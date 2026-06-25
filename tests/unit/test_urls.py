"""Tests for URL utilities."""

from neo_api_client.utils.urls import (
    BASE_URL,
    ORDER_FEED_URL,
    PROD_BASE_URL,
    UAT_BASE_URL,
    WEBSOCKET_URL,
)


def test_prod_base_url():
    """Test production base URL."""
    assert PROD_BASE_URL is not None
    assert "kotaksecurities" in PROD_BASE_URL


def test_uat_base_url():
    """Test UAT base URL."""
    assert UAT_BASE_URL is not None
    assert "kotaksecurities" in UAT_BASE_URL


def test_urls_are_different():
    """Test that prod and UAT URLs are different."""
    assert PROD_BASE_URL != UAT_BASE_URL


def test_websocket_url():
    """Test websocket URL."""
    assert WEBSOCKET_URL is not None
    assert "wss://" in WEBSOCKET_URL


def test_order_feed_url():
    """Test order feed URL."""
    assert ORDER_FEED_URL is not None
    assert "wss://" in ORDER_FEED_URL


def test_base_url():
    """Test base URL."""
    assert BASE_URL is not None
    assert "https://" in BASE_URL
