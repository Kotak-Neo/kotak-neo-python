# Using the Async Feeds from a Synchronous, Multi-Process App

A production pattern for consuming the `async`/`await` SFeed and order/position
feeds (`create_websocket()` / `create_order_feed()`) from an application that
is itself synchronous and runs as multiple worker processes — e.g. Django/Flask
behind gunicorn/uWSGI sync workers, or Celery workers.

## Table of Contents
- [Why this needs a pattern at all](#why-this-needs-a-pattern-at-all)
- [The bridge: background thread + thread-safe queue](#the-bridge-background-thread--thread-safe-queue)
- [Using it from gunicorn (sync workers)](#using-it-from-gunicorn-sync-workers)
- [Using it from Celery](#using-it-from-celery)
- [Multi-process considerations](#multi-process-considerations)
- [When you don't need this](#when-you-dont-need-this)

## Why this needs a pattern at all

The legacy SDK's WebSocket client was callback-based and ran its own
background thread internally (`on_message`/`on_error`/etc. fired from a
thread the library created for you) — trivial to bolt onto a synchronous,
multi-process app, since you never touched asyncio at all.

The current SFeed/order-feed clients are `async`/`await` — they need a
running asyncio event loop. A sync web worker or Celery task doesn't have
one (and shouldn't become asyncio-native just to consume a feed). The
pattern below reproduces the *old* thread-based experience on top of the
*new* async client: one background thread per process owns the event loop
and the WebSocket connection; your synchronous code talks to it through a
thread-safe queue and `asyncio.run_coroutine_threadsafe(...)`.

## The bridge: background thread + thread-safe queue

```python
import asyncio
import contextlib
import queue
import threading


class SyncFeedBridge:
    """Bridges an async SFeed/order-feed client into synchronous code.

    Construct exactly ONE instance per worker PROCESS (see the gunicorn/Celery
    sections below for where) -- never share one instance's background
    thread/event loop across processes (impossible anyway, since processes
    don't share memory), and don't construct a new one per request/task.
    """

    def __init__(self, client, tokens, queue_maxsize=10_000, startup_timeout=15):
        self._client = client
        self._tokens = tokens
        self.messages = queue.Queue(maxsize=queue_maxsize)
        self._loop = None
        self._ws = None
        self._ready = threading.Event()
        self._error = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=startup_timeout):
            raise TimeoutError("SFeed connection did not become ready in time")
        if self._error:
            raise self._error

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        except Exception as exc:  # surfaced to the constructing thread below
            self._error = exc
            self._ready.set()

    async def _main(self):
        async with self._client.create_websocket() as ws:
            self._ws = ws
            await ws.subscribe_scrips(self._tokens)
            self._ready.set()
            async for message in ws:
                self.messages.put(message)

    def get(self, timeout=None):
        """Blocking, synchronous read of the next message -- call this from
        your sync request handler / task."""
        return self.messages.get(timeout=timeout)

    def subscribe(self, tokens, timeout=5):
        """Synchronously call the async client's subscribe_scrips() from sync code."""
        future = asyncio.run_coroutine_threadsafe(self._ws.subscribe_scrips(tokens), self._loop)
        return future.result(timeout=timeout)

    def close(self, timeout=5):
        if self._loop and self._ws:
            future = asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
            with contextlib.suppress(Exception):
                future.result(timeout=timeout)
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=timeout)
```

Adapt `_main()`/`subscribe()` for the order/position feed (`create_order_feed()`)
the same way — it has no subscribe step, so `_main()` just connects and reads.

## Using it from gunicorn (sync workers)

Build the bridge in gunicorn's `post_fork` hook, **not** at module import time
or before forking. asyncio event loops and open sockets are not fork-safe —
creating the bridge in the master process and letting workers inherit it via
fork produces a broken, shared connection. Each worker must open its own.

```python
# gunicorn.conf.py
from neo_api_client import NeoAPI
from myapp.feed import SyncFeedBridge, LTP_TOKENS


def post_fork(server, worker):
    client = NeoAPI(consumer_key="...", environment="prod")
    client.totp_login(mobile_number="...", ucc="...", totp="...")
    client.totp_validate(mpin="...")
    worker.feed = SyncFeedBridge(client, LTP_TOKENS)


def worker_exit(server, worker):
    if hasattr(worker, "feed"):
        worker.feed.close()
```

Your view/handler code then reads synchronously:

```python
def quote_view(request):
    message = request.app_worker.feed.get(timeout=1)
    ...
```

## Using it from Celery

Use the `worker_process_init` signal, which fires once per worker process
after it forks — same fork-safety reasoning as gunicorn's `post_fork`.

```python
from celery.signals import worker_process_init, worker_process_shutdown

_bridge = None


@worker_process_init.connect
def start_feed(**kwargs):
    global _bridge
    client = NeoAPI(consumer_key="...", environment="prod")
    client.totp_login(mobile_number="...", ucc="...", totp="...")
    client.totp_validate(mpin="...")
    _bridge = SyncFeedBridge(client, LTP_TOKENS)


@worker_process_shutdown.connect
def stop_feed(**kwargs):
    if _bridge:
        _bridge.close()
```

A Celery task then just calls `_bridge.get(timeout=...)` like any other
synchronous call — no `async`/`await` anywhere in task code.

## Multi-process considerations

- **One WebSocket connection per process, not per request/task.** Each
  process gets its own bridge instance and its own live connection to the
  feed. With N worker processes you'll have N independent subscriptions to
  the same tokens — that's expected (each process needs its own feed), but
  size your worker count with that in mind if the feed enforces a per-account
  connection limit.
- **Never construct before fork.** See the gunicorn/Celery sections above —
  build the bridge in a post-fork hook, never at module import time in code
  that gunicorn/Celery loads before forking workers.
- **The queue is the only thing crossing the thread boundary safely.**
  Everything else (the `SFeedWebSocket` instance, its event loop) belongs to
  the bridge's background thread; don't reach into `bridge._ws` from your
  sync code except through the `subscribe()`-style wrapper methods shown
  above, which marshal the call onto the event loop's thread via
  `asyncio.run_coroutine_threadsafe`.

## When you don't need this

If your application is already asyncio-native (FastAPI, an asyncio-based
worker, a standalone script), just `await` the client directly as shown in
the [SFeed WebSocket Guide](websocket.md) — this bridge exists specifically
for synchronous, multi-process deployments that can't (or don't want to)
become asyncio-native.

## Getting Help

- **Issues:** https://github.com/Kotak-Neo/kotak-neo-python/issues
- **Email:** support@kotakneo.com
