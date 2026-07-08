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
