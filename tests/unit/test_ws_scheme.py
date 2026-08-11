"""Unit tests for the shared http(s) -> ws(s) URL scheme helper."""

from neo_api_client.utils.ws_scheme import to_websocket_scheme


def test_https_becomes_wss():
    assert to_websocket_scheme("https://sfeed.kotaksecurities.com/wsfeed") == (
        "wss://sfeed.kotaksecurities.com/wsfeed"
    )


def test_http_becomes_ws():
    assert to_websocket_scheme("http://fake/feed") == "ws://fake/feed"


def test_wss_left_unchanged():
    assert to_websocket_scheme("wss://fake/feed") == "wss://fake/feed"


def test_ws_left_unchanged():
    assert to_websocket_scheme("ws://fake/feed") == "ws://fake/feed"


def test_query_string_preserved():
    assert to_websocket_scheme("https://fake/feed?a=1&b=2") == "wss://fake/feed?a=1&b=2"
