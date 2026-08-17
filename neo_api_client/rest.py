import contextlib
import json
import re
import time
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
    from neo_api_client.logger import get_logger
    from neo_api_client.rate_limiter import get_rate_limiter

    _ENHANCED_FEATURES = True
except ImportError:  # pragma: no cover - fallback when optional deps are unavailable
    _ENHANCED_FEATURES = False

DEFAULT_TIMEOUT = 30
DEFAULT_POOL_CONNECTIONS = 10
DEFAULT_POOL_MAXSIZE = 20

# Context variable for request correlation
correlation_id_context: ContextVar[str | None] = ContextVar("correlation_id", default=None)

if _ENHANCED_FEATURES:  # pragma: no cover - always true in a valid install
    logger = get_logger(__name__)


class RESTClientObject:
    """Enhanced REST API Client with enterprise features."""

    def __init__(
        self, configuration, enable_rate_limiting: bool = False, raise_on_error: bool = False
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
        """
        self.configuration = configuration
        self.session = self._create_session()
        self.rate_limiter = None
        self.raise_on_error = raise_on_error

        if _ENHANCED_FEATURES and enable_rate_limiting:
            self.rate_limiter = get_rate_limiter()
            logger.debug(
                "rest_client_initialized",
                rate_limiting=enable_rate_limiting,
                timeout=DEFAULT_TIMEOUT,
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
        limits = httpx.Limits(
            max_connections=DEFAULT_POOL_MAXSIZE,
            max_keepalive_connections=DEFAULT_POOL_CONNECTIONS,
        )

        return httpx.Client(
            http2=True,
            limits=limits,
            timeout=DEFAULT_TIMEOUT,
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
        start_time = None
        if _ENHANCED_FEATURES:
            request_id = self._generate_request_id()
            correlation_id_context.set(request_id)
            start_time = time.time()

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

            logger.debug(
                "api_request_start",
                request_id=request_id,
                method=method,
                url=self._sanitize_url_for_logging(url),
            )

        try:
            content_type = headers.get("Content-Type", "")

            request_kwargs = {
                "url": url,
                "headers": headers,
                "params": query_params,
                "timeout": timeout or DEFAULT_TIMEOUT,
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

            # Log success if enhanced features available
            if _ENHANCED_FEATURES and request_id and start_time:
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(
                    "api_request_success",
                    request_id=request_id,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                )

            # Check for error status codes (only if raise_on_error is enabled)
            if response.status_code >= 400 and _ENHANCED_FEATURES and self.raise_on_error:
                self._handle_error_response(response, request_id)

            return response

        except httpx.TimeoutException as exc:
            if _ENHANCED_FEATURES and request_id and start_time:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "api_request_timeout",
                    request_id=request_id,
                    timeout=timeout or DEFAULT_TIMEOUT,
                    duration_ms=round(duration_ms, 2),
                )
            raise ApiException(
                status=0,
                reason=f"Request timeout after {timeout or DEFAULT_TIMEOUT} seconds",
            ) from exc

        except httpx.ConnectError as exc:
            if _ENHANCED_FEATURES and request_id and start_time:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "api_request_connection_error",
                    request_id=request_id,
                    duration_ms=round(duration_ms, 2),
                )
            raise ApiException(
                status=0,
                reason="Unable to connect to server",
            ) from exc

        except httpx.HTTPError as exc:
            if _ENHANCED_FEATURES and request_id and start_time:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "api_request_failed",
                    request_id=request_id,
                    error=str(exc),
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )
            raise ApiException(
                status=0,
                reason=str(exc),
            ) from exc

    def _handle_error_response(self, response: httpx.Response, request_id: str | None) -> None:
        """
        Handle error responses and raise appropriate exceptions.

        Parameters
        ----------
        response : httpx.Response
            HTTP response object
        request_id : str, optional
            Request correlation ID

        Raises
        ------
        ApiException
            With details about the error
        """
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        if _ENHANCED_FEATURES:
            logger.error(
                "api_error_response",
                request_id=request_id,
                status_code=response.status_code,
                reason=response.reason_phrase,
            )

        raise ApiException(
            status=response.status_code,
            reason=response.reason_phrase,
            body=error_body,
        )

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
