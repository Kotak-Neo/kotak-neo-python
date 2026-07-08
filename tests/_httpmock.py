"""A small ``requests_mock``-compatible shim backed by ``respx``.

The SDK's HTTP transport moved from ``requests`` to ``httpx`` (for HTTP/2), so
``requests_mock`` no longer intercepts anything. This shim presents the subset
of the ``requests_mock`` API the test-suite relies on — ``.get/.post/.put/
.delete(url, json=, text=, status_code=, reason=)`` plus ``.last_request`` —
on top of ``respx``, so the existing tests keep working with minimal edits.
"""

import json as _json

import httpx
import respx


class _RecordedRequest:
    """A ``requests_mock``-style view over a recorded ``httpx.Request``."""

    def __init__(self, request: httpx.Request):
        self._request = request

    @property
    def headers(self):
        return self._request.headers

    @property
    def url(self):
        return str(self._request.url)

    @property
    def text(self):
        return self._request.content.decode("utf-8", errors="replace")

    @property
    def json(self):
        return _json.loads(self._request.content or b"null")

    @property
    def query(self):
        return dict(self._request.url.params)


class RespxMock:
    """Mimics the subset of ``requests_mock.Mocker`` used by the test-suite."""

    def __init__(self):
        # assert_all_called=False: tests may register routes they don't hit.
        self._router = respx.MockRouter(assert_all_called=False)
        # Requests recorded before the router resets, so `last_request` /
        # `request_history` remain readable after the `with` block exits (respx
        # clears its own call log on stop, but requests_mock keeps history).
        self._recorded = []

    # ---- context-manager form: ``with RespxMock() as m:`` -------------------

    def __enter__(self):
        self._router.start()
        return self

    def __exit__(self, *exc):
        self._snapshot()
        self._router.stop(quiet=True)
        return False

    # ---- fixture form: started/stopped by the pytest fixture ----------------

    def start(self):
        self._router.start()

    def stop(self):
        self._snapshot()
        self._router.stop(quiet=True)

    def _snapshot(self):
        """Preserve recorded requests before respx resets its call log."""
        self._recorded = [call.request for call in self._router.calls]

    # ---- route registration -------------------------------------------------

    def _register(
        self,
        method,
        url,
        *,
        json=None,
        text=None,
        status_code=200,
        reason=None,
        content=None,
        exc=None,
    ):
        # Match on scheme://host/path only, ignoring the query string — this
        # mirrors requests_mock's default (query params don't affect matching).
        parsed = httpx.URL(url)
        base = str(parsed.copy_with(query=None, fragment=None))
        route = self._router.route(method=method, url=base)

        if exc is not None:
            # A bare Exception isn't an httpx transport error; the SDK's generic
            # handler wraps httpx.HTTPError, so raise that to exercise it.
            side_effect = exc if isinstance(exc, BaseException) else exc()
            if not isinstance(side_effect, httpx.HTTPError):
                side_effect = httpx.HTTPError(str(side_effect))
            route.mock(side_effect=side_effect)
            return route

        response_kwargs = {}
        if json is not None:
            response_kwargs["json"] = json
        if text is not None:
            response_kwargs["text"] = text
        if content is not None:
            response_kwargs["content"] = content
        if reason is not None:
            # httpx derives reason_phrase from the status code unless overridden.
            response_kwargs["extensions"] = {"reason_phrase": reason.encode("ascii")}

        route.mock(return_value=httpx.Response(status_code, **response_kwargs))
        return route

    def get(self, url, **kwargs):
        return self._register("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._register("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self._register("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._register("DELETE", url, **kwargs)

    def patch(self, url, **kwargs):
        return self._register("PATCH", url, **kwargs)

    def options(self, url, **kwargs):
        return self._register("OPTIONS", url, **kwargs)

    def head(self, url, **kwargs):
        return self._register("HEAD", url, **kwargs)

    # ---- introspection ------------------------------------------------------

    def _requests(self):
        """Recorded httpx.Request objects (live if active, else the snapshot)."""
        live = [call.request for call in self._router.calls]
        return live or self._recorded

    @property
    def last_request(self):
        requests = self._requests()
        if not requests:
            return None
        return _RecordedRequest(requests[-1])

    @property
    def request_history(self):
        return [_RecordedRequest(req) for req in self._requests()]

    @property
    def call_count(self):
        return len(self._requests())

    @property
    def called(self):
        return len(self._requests()) > 0


def Mocker():
    """``requests_mock.Mocker()``-compatible factory returning a respx-backed mock."""
    return RespxMock()
