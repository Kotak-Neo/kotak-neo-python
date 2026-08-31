import httpx

from neo_api_client import rest


class ApiClient:
    """
    :param configuration: .Configuration object for this client
    :param header_name: a header to pass when making calls to the API.
    param header_value: a header value to pass when making calls to
        the API.
    :param transport: custom httpx.BaseTransport for the underlying REST
        client (e.g. corporate proxy, mTLS, custom pooling, instrumentation).
    :param limits: custom httpx.Limits for the underlying REST client's
        connection pool. Ignored if `transport` is given.
    :param http2: whether to negotiate HTTP/2 (with automatic HTTP/1.1
        fallback) on the default transport. Default: True. Ignored if
        `transport` is given.
    :param timeout: default request timeout in seconds for the underlying
        REST client. Default: 30 seconds when not given.
    """

    def __init__(
        self,
        configuration,
        header_name=None,
        header_value=None,
        transport: httpx.BaseTransport | None = None,
        limits: httpx.Limits | None = None,
        http2: bool = True,
        timeout: float | None = None,
    ):
        self.configuration = configuration
        self.rest_client = rest.RESTClientObject(
            configuration, transport=transport, limits=limits, http2=http2, timeout=timeout
        )
        self.default_headers = {}
        if header_name is not None:
            self.default_headers[header_name] = header_value
        self.user_agent = "NeoTradeApi-python/1.0.0/python"

    @property
    def user_agent(self):
        """User agent for this API client"""
        return self.default_headers["User-Agent"]

    @user_agent.setter
    def user_agent(self, value):
        self.default_headers["User-Agent"] = value

    def set_default_header(self, header_name, header_value):
        self.default_headers[header_name] = header_value
