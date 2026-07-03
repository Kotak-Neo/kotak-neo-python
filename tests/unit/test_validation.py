"""Unit tests for request data validation."""

import pytest

from neo_api_client.exceptions import ApiValueError
from neo_api_client.req_data_validation import (
    cancel_order_validation,
    limits_validation,
    margin_validation,
    order_history_validation,
    place_order_validation,
    validate_configuration,
)

# ---- validate_configuration -------------------------------------------------


def test_validate_configuration_ok():
    validate_configuration(consumer_key="key", consumer_secret="secret")


def test_validate_configuration_missing_key():
    with pytest.raises(ApiValueError):
        validate_configuration(consumer_key="", consumer_secret="secret")


def test_validate_configuration_missing_secret():
    with pytest.raises(ApiValueError):
        validate_configuration(consumer_key="key", consumer_secret="")


# ---- place_order_validation -------------------------------------------------


def _valid_place_kwargs(**overrides):
    kwargs = {
        "exchange_segment": "nse_cm",
        "product": "CNC",
        "price": "100.00",
        "order_type": "L",
        "quantity": "1",
        "validity": "DAY",
        "trading_symbol": "RELIANCE-EQ",
        "transaction_type": "B",
    }
    kwargs.update(overrides)
    return kwargs


def test_place_order_validation_ok():
    # Should not raise
    place_order_validation(**_valid_place_kwargs())


def test_place_order_validation_optional_fields_ok():
    place_order_validation(
        **_valid_place_kwargs(),
        amo="NO",
        disclosed_quantity="0",
        market_protection="0",
        pf="N",
        trigger_price="0",
        tag="my-tag",
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("exchange_segment", 123),
        ("product", 123),
        ("price", 100),
        ("order_type", 123),
        ("quantity", 1),
        ("validity", 123),
        ("trading_symbol", 123),
        ("transaction_type", 123),
    ],
)
def test_place_order_validation_type_errors(field, value):
    with pytest.raises(ApiValueError):
        place_order_validation(**_valid_place_kwargs(**{field: value}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("exchange_segment", "INVALID"),
        ("product", "INVALID"),
        ("order_type", "INVALID"),
        ("validity", "GTC"),
        ("transaction_type", "X"),
    ],
)
def test_place_order_validation_value_errors(field, value):
    with pytest.raises(ApiValueError):
        place_order_validation(**_valid_place_kwargs(**{field: value}))


@pytest.mark.parametrize(
    "field",
    ["amo", "disclosed_quantity", "market_protection", "pf", "trigger_price", "tag"],
)
def test_place_order_validation_optional_type_errors(field):
    with pytest.raises(ApiValueError):
        place_order_validation(**_valid_place_kwargs(), **{field: 123})


# ---- cancel_order_validation ------------------------------------------------


def test_cancel_order_validation_ok():
    cancel_order_validation(order_id="12345")


def test_cancel_order_validation_empty():
    with pytest.raises(ValueError):
        cancel_order_validation(order_id="   ")


def test_cancel_order_validation_non_string():
    with pytest.raises(ValueError):
        cancel_order_validation(order_id=12345)


def test_cancel_order_validation_bad_amo():
    with pytest.raises(ApiValueError):
        cancel_order_validation(order_id="12345", amo=1)


# ---- order_history_validation -----------------------------------------------


def test_order_history_validation_ok():
    order_history_validation(order_id="12345")


def test_order_history_validation_non_string():
    with pytest.raises(ValueError):
        order_history_validation(order_id=12345)


# ---- margin_validation ------------------------------------------------------


def _valid_margin_kwargs(**overrides):
    kwargs = {
        "exchange_segment": "nse_cm",
        "price": "100.00",
        "order_type": "L",
        "product": "CNC",
        "quantity": "1",
        "instrument_token": "11536",
        "transaction_type": "B",
    }
    kwargs.update(overrides)
    return kwargs


def test_margin_validation_ok():
    margin_validation(**_valid_margin_kwargs())


@pytest.mark.parametrize(
    "field,value",
    [
        ("exchange_segment", "INVALID"),
        ("product", "INVALID"),
        ("order_type", "INVALID"),
        ("transaction_type", "X"),
    ],
)
def test_margin_validation_value_errors(field, value):
    with pytest.raises(ApiValueError):
        margin_validation(**_valid_margin_kwargs(**{field: value}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("exchange_segment", 1),
        ("product", 1),
        ("price", 1),
        ("order_type", 1),
        ("quantity", 1),
        ("instrument_token", 1),
        ("transaction_type", 1),
    ],
)
def test_margin_validation_type_errors(field, value):
    with pytest.raises(ApiValueError):
        margin_validation(**_valid_margin_kwargs(**{field: value}))


def test_margin_validation_bad_trigger_price():
    with pytest.raises(ApiValueError):
        margin_validation(**_valid_margin_kwargs(), trigger_price=100)


# ---- limits_validation ------------------------------------------------------


def test_limits_validation_ok():
    limits_validation(segment="ALL", exchange="ALL", product="ALL")


@pytest.mark.parametrize(
    "segment,exchange,product",
    [
        ("INVALID", "ALL", "ALL"),
        ("ALL", "INVALID", "ALL"),
        ("ALL", "ALL", "INVALID"),
    ],
)
def test_limits_validation_value_errors(segment, exchange, product):
    with pytest.raises(ApiValueError):
        limits_validation(segment=segment, exchange=exchange, product=product)


@pytest.mark.parametrize(
    "segment,exchange,product",
    [
        (1, "ALL", "ALL"),
        ("ALL", 1, "ALL"),
        ("ALL", "ALL", 1),
    ],
)
def test_limits_validation_type_errors(segment, exchange, product):
    with pytest.raises(ApiValueError):
        limits_validation(segment=segment, exchange=exchange, product=product)
