"""Tests for settings module."""

from neo_api_client import settings


def test_settings_exchange_segment():
    """Test exchange segment settings."""
    assert "nse_cm" in settings.exchange_segment
    assert settings.exchange_segment["nse_cm"] == "nse_cm"


def test_settings_product():
    """Test product settings."""
    assert "CNC" in settings.product
    assert settings.product["CNC"] == "CNC"


def test_settings_order_type():
    """Test order type settings."""
    assert "L" in settings.order_type
    assert settings.order_type["L"] == "L"


def test_settings_segment_limits():
    """Test segment limits."""
    assert "CASH" in settings.segment_limits
    assert "FO" in settings.segment_limits


def test_settings_exchange_limits():
    """Test exchange limits."""
    assert "NSE" in settings.exchange_limits
    assert "BSE" in settings.exchange_limits
