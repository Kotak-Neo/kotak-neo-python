import httpx

from neo_api_client.api_client import ApiClient
from neo_api_client.utils.neo_utility import NeoUtility


def test_user_agent():
    config = NeoUtility(host="prod")

    client = ApiClient(config)

    assert client.user_agent == "NeoTradeApi-python/1.0.0/python"


def test_set_default_header():
    config = NeoUtility(host="prod")

    client = ApiClient(config)

    client.set_default_header("test", "value")

    assert client.default_headers["test"] == "value"


def test_init_with_header_name_seeds_default_headers():
    """Passing header_name/header_value populates default_headers at init."""
    config = NeoUtility(host="prod")

    client = ApiClient(config, header_name="X-Custom", header_value="hello")

    assert client.default_headers["X-Custom"] == "hello"


def test_init_with_transport_reaches_underlying_session():
    """transport= is threaded through to the REST client's httpx.Client."""
    config = NeoUtility(host="prod")
    custom_transport = httpx.HTTPTransport()

    client = ApiClient(config, transport=custom_transport)

    assert client.rest_client.session._transport is custom_transport


def test_init_with_limits_reaches_underlying_session():
    """limits= is threaded through to the REST client's httpx.Client."""
    config = NeoUtility(host="prod")
    custom_limits = httpx.Limits(max_connections=7, max_keepalive_connections=3)

    client = ApiClient(config, limits=custom_limits)

    assert client.rest_client.session._transport._pool._max_connections == 7


def test_init_with_http2_false_reaches_underlying_session():
    """http2=False is threaded through to the REST client's httpx.Client."""
    config = NeoUtility(host="prod")

    client = ApiClient(config, http2=False)

    assert client.rest_client.session._transport._pool._http2 is False


def test_init_with_timeout_reaches_underlying_session():
    """timeout= is threaded through to the REST client's httpx.Client."""
    config = NeoUtility(host="prod")

    client = ApiClient(config, timeout=45)

    assert client.rest_client.session.timeout.connect == 45
