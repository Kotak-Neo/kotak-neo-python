import contextlib
import json
import re
import uuid
from contextvars import ContextVar
from typing import Any

import httpx

from neo_api_client.exceptions import ApiException

try:
    from neo_api_client import __version__
except ImportError:  # pragma: no cover - fallback when version metadata is unavailable
    __version__ = "unknown"

try:
    from neo_api_client.logger import get_logger, set_environment
    from neo_api_client.rate_limiter import get_rate_limiter

    _ENHANCED_FEATURES = True
except ImportError:  # pragma: no cover - fallback when optional deps are unavailable
    _ENHANCED_FEATURES = False

DEFAULT_TIMEOUT = 30
DEFAULT_POOL_CONNECTIONS = 10
DEFAULT_POOL_MAXSIZE = 20

# Response bodies larger than this get a size-only summary plus a short
# preview in the log (e.g. scrip master downloads, option chains, candle
# arrays), so a single large response can't blow up the rotating log file.
# This only affects what's written to the log -- the body returned to the
# caller (and raised in ApiException) is never truncated.
MAX_LOGGED_BODY_BYTES = 4096

# How much of a truncated body's raw text to keep as a "preview" -- enough to
# see an error envelope's leading fields (e.g. {"status": "ERROR", "fault":
# ...) even when the full body is too big to log in full.
TRUNCATED_BODY_PREVIEW_CHARS = 1000

# Context variable for request correlation
correlation_id_context: ContextVar[str | None] = ContextVar("correlation_id", default=None)

if _ENHANCED_FEATURES:  # pragma: no cover - always true in a valid install
    logger = get_logger(__name__)


class RESTClientObject:
    """Enhanced REST API Client with enterprise features."""

    def __init__(
        self,
        configuration,
        enable_rate_limiting: bool = False,
        raise_on_error: bool = False,
        transport: httpx.BaseTransport | None = None,
        limits: httpx.Limits | None = None,
        http2: bool = True,
        timeout: float | None = None,
    ):
        """
        Initialize the API client.

        Parameters
        ----------
        configuration : dict
            SDK configuration.
        enable_rate_limiting : bool, optional
            Enable rate limiting (default: False for backward compatibility)
        raise_on_error : bool, optional
            Raise exception on HTTP error status codes (400+) (default: False for backward compatibility)
        transport : httpx.BaseTransport, optional
            Custom transport for the underlying httpx.Client -- the migration
            hook for deployment architectures that need a corporate proxy,
            mTLS, custom connection pooling, or request/response
            instrumentation (the httpx equivalent of mounting a custom
            `requests.adapters.HTTPAdapter`). Defaults to httpx's standard
            transport when not given. Overrides `http2` for connections made
            through it, since a custom transport owns its own protocol
            negotiation.
        limits : httpx.Limits, optional
            Custom connection pool limits. Ignored if `transport` is given,
            since a custom transport owns its own pooling. Defaults to
            max_connections=20, max_keepalive_connections=10 when not given.
        http2 : bool, optional
            Whether to negotiate HTTP/2 (with automatic HTTP/1.1 fallback)
            on the default transport. Default: True. Ignored if `transport`
            is given.
        timeout : float, optional
            Default request timeout in seconds for the underlying httpx.Client.
            Individual calls to `request(..., timeout=...)` still override this
            per-call. Default: 30 seconds when not given.
        """
        self.configuration = configuration
        self._transport = transport
        self._limits = limits
        self._http2 = http2
        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self.session = self._create_session()
        self.rate_limiter = None
        self.raise_on_error = raise_on_error

        if _ENHANCED_FEATURES:
            host = str(getattr(configuration, "host", "") or "").strip().lower()
            if host:
                set_environment(host)

        if _ENHANCED_FEATURES and enable_rate_limiting:
            self.rate_limiter = get_rate_limiter()
            logger.debug(
                "rest_client_initialized",
                rate_limiting=enable_rate_limiting,
                timeout=self._timeout,
            )

    def _create_session(self) -> httpx.Client:
        """
        Create an HTTP/2-capable client with connection pooling.

        The Kotak endpoints negotiate HTTP/2 via ALPN, so ``http2=True`` upgrades
        eligible ``https`` connections automatically (falling back to HTTP/1.1
        when a server doesn't offer h2).

        Returns
        -------
        httpx.Client
            Configured HTTP/2 client.
        """
        limits = self._limits or httpx.Limits(
            max_connections=DEFAULT_POOL_MAXSIZE,
            max_keepalive_connections=DEFAULT_POOL_CONNECTIONS,
        )

        return httpx.Client(
            http2=self._http2,
            limits=limits,
            transport=self._transport,
            timeout=self._timeout,
            follow_redirects=True,
            headers={
                "User-Agent": f"NeoSDK-Python/{__version__}",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
        )

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        return str(uuid.uuid4())

    def _sanitize_url_for_logging(self, url: str) -> str:
        """Remove sensitive data from URL for logging."""
        sensitive_params = ["token", "password", "secret", "key", "sid", "auth"]
        for param in sensitive_params:
            url = re.sub(rf"({param})=[^&]*", r"\1=***", url, flags=re.IGNORECASE)
        return url

    def _parse_response_body(self, response: httpx.Response) -> Any:
        """Parse a response body as JSON, falling back to raw text."""
        try:
            return response.json()
        except Exception:
            return response.text

    def _response_body_for_logging(self, response: httpx.Response) -> Any:
        """Size-capped representation of a response body, safe to write to
        the log file. Sensitive fields are censored downstream by the shared
        structlog processor (`censor_sensitive_data`)."""
        if len(response.content) > MAX_LOGGED_BODY_BYTES:
            return {
                "truncated": True,
                "size_bytes": len(response.content),
                "preview": response.text[:TRUNCATED_BODY_PREVIEW_CHARS],
            }
        return self._parse_response_body(response)

    def request(
        self,
        method: str,
        url: str,
        query_params: dict | None = None,
        headers: dict | None = None,
        body: Any | None = None,
        timeout: int | None = None,
    ):
        """
        Make an HTTP request with optional retry, rate limiting, and tracing.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, etc.)
        url : str
            Request URL
        query_params : dict, optional
            Query parameters
        headers : dict, optional
            Request headers
        body : any, optional
            Request body
        timeout : int, optional
            Request timeout in seconds

        Returns
        -------
        httpx.Response
            Response object

        Raises
        ------
        ApiException
            On API errors
        """
        method = method.upper()

        if method not in {
            "GET",
            "HEAD",
            "DELETE",
            "POST",
            "PUT",
            "PATCH",
            "OPTIONS",
        }:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Apply rate limiting if enabled
        if _ENHANCED_FEATURES and self.rate_limiter:
            try:
                self.rate_limiter.acquire(timeout=30.0)
            except TimeoutError as e:
                if hasattr(self, "_sanitize_url_for_logging"):
                    logger.error("rate_limit_timeout", url=self._sanitize_url_for_logging(url))
                raise ApiException(
                    status=429,
                    reason="Rate limit exceeded",
                ) from e

        # Generate request ID for tracing (if enhanced features available)
        request_id = None
        if _ENHANCED_FEATURES:
            request_id = self._generate_request_id()
            correlation_id_context.set(request_id)

        # Drop headers with None values. requests silently omitted them, but
        # httpx raises on a None value, so filter them to preserve behavior.
        headers = {k: v for k, v in (headers or {}).items() if v is not None}
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        # SDK developers only: in the internal UAT environment, attach an
        # optional X-Forwarded-For header (from NEO_UAT_X_FORWARDED_FOR).
        # Never applied in production.
        host = str(getattr(self.configuration, "host", "") or "").lower().strip()
        xff = getattr(self.configuration, "uat_x_forwarded_for", None)
        if host == "uat" and xff and "X-Forwarded-For" not in headers:
            headers["X-Forwarded-For"] = xff

        # Add tracing headers if enhanced features available
        if _ENHANCED_FEATURES and request_id:
            headers["X-Request-ID"] = request_id
            if hasattr(self.configuration, "consumer_key") and self.configuration.consumer_key:
                headers["X-Client-ID"] = self.configuration.consumer_key[:8] + "***"

        try:
            content_type = headers.get("Content-Type", "")

            request_kwargs = {
                "url": url,
                "headers": headers,
                "params": query_params,
                "timeout": timeout or self._timeout,
            }

            if method in {"POST", "PUT", "PATCH", "DELETE"}:
                if re.search("json", content_type, re.IGNORECASE):
                    # Raw JSON body: send as content so httpx doesn't re-encode it.
                    if body is not None:
                        request_kwargs["content"] = json.dumps(body)

                elif re.search(
                    "x-www-form-urlencoded",
                    content_type,
                    re.IGNORECASE,
                ):
                    # Form-encoded body under the jData key (Kotak convention).
                    request_kwargs["data"] = {"jData": json.dumps(body)} if body is not None else {}

                else:
                    raise ApiException(
                        status=0,
                        reason="Invalid Content-Type in header parameters",
                    )

            response = self.session.request(
                method,
                **request_kwargs,
            )

            # One log line per request, written once the outcome is known --
            # carries the request context (method/url/body) that used to be
            # logged separately as "api_request_start", so the request and
            # its result are never split across two writes. Error responses
            # (status >= 400) are always logged (for monitoring), independent
            # of raise_on_error, which only controls whether they also raise.
            if _ENHANCED_FEATURES and request_id:
                is_error = response.status_code >= 400
                (logger.error if is_error else logger.info)(
                    "api_error_response" if is_error else "api_request_success",
                    request_id=request_id,
                    method=method,
                    url=self._sanitize_url_for_logging(url),
                    query_params=query_params,
                    body=body,
                    status_code=response.status_code,
                    reason=response.reason_phrase if is_error else None,
                    response_body=self._response_body_for_logging(response),
                )

            if response.status_code >= 400 and _ENHANCED_FEATURES and self.raise_on_error:
                raise ApiException(
                    status=response.status_code,
                    reason=response.reason_phrase,
                    body=self._parse_response_body(response),
                )

            return response

        except httpx.TimeoutException as exc:
            if _ENHANCED_FEATURES and request_id:
                logger.error(
                    "api_request_timeout",
                    request_id=request_id,
                    method=method,
                    url=self._sanitize_url_for_logging(url),
                    query_params=query_params,
                    body=body,
                    timeout=timeout or self._timeout,
                )
            raise ApiException(
                status=0,
                reason=f"Request timeout after {timeout or self._timeout} seconds",
            ) from exc

        except httpx.ConnectError as exc:
            if _ENHANCED_FEATURES and request_id:
                logger.error(
                    "api_request_connection_error",
                    request_id=request_id,
                    method=method,
                    url=self._sanitize_url_for_logging(url),
                    query_params=query_params,
                    body=body,
                )
            raise ApiException(
                status=0,
                reason="Unable to connect to server",
            ) from exc

        except httpx.HTTPError as exc:
            if _ENHANCED_FEATURES and request_id:
                logger.error(
                    "api_request_failed",
                    request_id=request_id,
                    method=method,
                    url=self._sanitize_url_for_logging(url),
                    query_params=query_params,
                    body=body,
                    error=str(exc),
                    exc_info=True,
                )
            raise ApiException(
                status=0,
                reason=str(exc),
            ) from exc

    def get_rate_limit_status(self) -> dict | None:
        """
        Get current rate limit status.

        Returns
        -------
        dict or None
            Dictionary with rate limit status or None if rate limiting disabled
        """
        if _ENHANCED_FEATURES and self.rate_limiter:
            return self.rate_limiter.get_status()
        return None

    def close(self) -> None:
        """Close underlying HTTP session and release resources."""
        if self.session:
            # Best-effort close log; it must never mask the session.close() below.
            try:
                if _ENHANCED_FEATURES:
                    logger.debug("rest_client_closing")
            except Exception:  # nosec B110
                pass
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()

    def __del__(self):
        """Cleanup on garbage collection."""
        with contextlib.suppress(BaseException):
            self.close()
