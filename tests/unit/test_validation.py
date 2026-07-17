"""Unit tests for request data validation."""

import pytest

from neo_api_client.exceptions import ApiValueError
from neo_api_client.req_data_validation import (
    cancel_order_validation,
    margin_validation,
    modify_order_validation,
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


@pytest.mark.parametrize("product", ["CNC", "NRML", "MIS", "MTF"])
def test_place_order_allowed_products(product):
    """Only the exact canonical codes CNC/NRML/MIS/MTF are accepted."""
    place_order_validation(**_valid_place_kwargs(product=product))


@pytest.mark.parametrize(
    "product",
    [
        "CO",
        "BO",
        "INTRADAY",
        "XYZ",
        # Aliases are rejected, not resolved — only the exact canonical
        # codes above are accepted.
        "Normal",
        "Cash and Carry",
        "cnc",
        "mis",
        "mtf",
        "Intraday",
    ],
)
def test_place_order_rejects_disallowed_products(product):
    """CO/BO/INTRADAY/unknown values and product aliases are all rejected."""
    with pytest.raises(ApiValueError, match="Allowed values are CNC, NRML, MIS, MTF"):
        place_order_validation(**_valid_place_kwargs(product=product))


def test_place_order_validation_optional_fields_ok():
    place_order_validation(
        **_valid_place_kwargs(),
        amo="NO",
        disclosed_quantity="0",
        trigger_price="0",
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
        # Currency derivatives (CDS/cde_fo) are no longer accepted for place order.
        ("exchange_segment", "CDS"),
        ("exchange_segment", "cds"),
        ("exchange_segment", "cde_fo"),
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
    ["amo", "disclosed_quantity", "trigger_price"],
)
def test_place_order_validation_optional_type_errors(field):
    with pytest.raises(ApiValueError):
        place_order_validation(**_valid_place_kwargs(), **{field: 123})


# ---- blank / empty mandatory parameters -------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "exchange_segment",
        "product",
        "price",
        "order_type",
        "quantity",
        "validity",
        "trading_symbol",
        "transaction_type",
    ],
)
@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_place_order_validation_blank_mandatory_fields(field, blank):
    """Every mandatory field must reject blank / whitespace-only values."""
    with pytest.raises(ApiValueError, match="cannot be blank|mandatory"):
        place_order_validation(**_valid_place_kwargs(**{field: blank}))


@pytest.mark.parametrize("field", ["amo", "disclosed_quantity"])
def test_place_order_validation_blank_optional_mandatory_fields(field):
    """am/dq carry defaults but must not be blank when explicitly passed."""
    with pytest.raises(ApiValueError, match="cannot be blank|mandatory"):
        place_order_validation(**_valid_place_kwargs(), **{field: ""})


@pytest.mark.parametrize("bad_price", ["abc", "1,000", "$5"])
def test_place_order_validation_non_numeric_price(bad_price):
    with pytest.raises(ApiValueError, match="valid number"):
        place_order_validation(**_valid_place_kwargs(price=bad_price))


def test_place_order_validation_negative_price():
    with pytest.raises(ApiValueError, match="negative"):
        place_order_validation(**_valid_place_kwargs(price="-1"))


@pytest.mark.parametrize("order_type", ["L", "Limit", "SL", "Stop loss limit"])
def test_place_order_validation_zero_price_rejected_for_limit_types(order_type):
    """L/SL orders need a real limit price; price=0 must be rejected rather
    than silently sent through (the exchange has been observed to substitute
    a nonsense default price instead of rejecting such orders)."""
    with pytest.raises(ApiValueError, match="greater than zero"):
        place_order_validation(**_valid_place_kwargs(order_type=order_type, price="0"))


@pytest.mark.parametrize("order_type", ["MKT", "Market", "SL-M", "Stop loss market"])
def test_place_order_validation_zero_price_allowed_for_market_types(order_type):
    """MKT/SL-M orders execute at the prevailing market price, so price=0 is valid."""
    place_order_validation(**_valid_place_kwargs(order_type=order_type, price="0"))


@pytest.mark.parametrize("bad_qty", ["abc", "1.5", "0", "-3"])
def test_place_order_validation_invalid_quantity(bad_qty):
    with pytest.raises(ApiValueError, match="integer|greater than zero"):
        place_order_validation(**_valid_place_kwargs(quantity=bad_qty))


def test_place_order_validation_negative_trigger_price():
    with pytest.raises(ApiValueError, match="negative|valid number"):
        place_order_validation(**_valid_place_kwargs(), trigger_price="-5")


@pytest.mark.parametrize("bad_dq", ["-1", "abc", "1.5"])
def test_place_order_validation_invalid_disclosed_quantity(bad_dq):
    with pytest.raises(ApiValueError, match="integer|negative"):
        place_order_validation(**_valid_place_kwargs(), disclosed_quantity=bad_dq)


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


def test_cancel_order_validation_blank_amo():
    with pytest.raises(ApiValueError, match="blank|mandatory"):
        cancel_order_validation(order_id="12345", amo="")


# ---- modify_order_validation ------------------------------------------------


def _valid_modify_kwargs(**overrides):
    kwargs = {
        "order_id": "260709000000058",
        "price": "1400",
        "order_type": "L",
        "quantity": "3",
        "validity": "DAY",
    }
    kwargs.update(overrides)
    return kwargs


def test_modify_order_validation_ok():
    # Should not raise
    modify_order_validation(**_valid_modify_kwargs())


def test_modify_order_validation_optional_fields_ok():
    modify_order_validation(
        **_valid_modify_kwargs(),
        trigger_price="0",
        disclosed_quantity="0",
        amo="NO",
    )


@pytest.mark.parametrize("field", ["order_id", "price", "order_type", "quantity", "validity"])
@pytest.mark.parametrize("blank", ["", "   ", None])
def test_modify_order_validation_blank_mandatory(field, blank):
    with pytest.raises(ApiValueError):
        modify_order_validation(**_valid_modify_kwargs(**{field: blank}))


@pytest.mark.parametrize("bad_price", ["abc", "-5"])
def test_modify_order_validation_bad_price(bad_price):
    with pytest.raises(ApiValueError, match="number|negative"):
        modify_order_validation(**_valid_modify_kwargs(price=bad_price))


@pytest.mark.parametrize("order_type", ["L", "SL"])
def test_modify_order_validation_zero_price_rejected_for_limit_types(order_type):
    """L/SL modifications need a real limit price; price=0 must be rejected."""
    with pytest.raises(ApiValueError, match="greater than zero"):
        modify_order_validation(**_valid_modify_kwargs(order_type=order_type, price="0"))


@pytest.mark.parametrize("order_type", ["MKT", "SL-M"])
def test_modify_order_validation_zero_price_allowed_for_market_types(order_type):
    """MKT/SL-M modifications execute at the prevailing market price, so price=0 is valid."""
    modify_order_validation(**_valid_modify_kwargs(order_type=order_type, price="0"))


@pytest.mark.parametrize("bad_qty", ["abc", "0", "-3", "1.5"])
def test_modify_order_validation_bad_quantity(bad_qty):
    with pytest.raises(ApiValueError, match="integer|greater than zero"):
        modify_order_validation(**_valid_modify_kwargs(quantity=bad_qty))


def test_modify_order_validation_bad_order_type():
    with pytest.raises(ApiValueError, match="order type"):
        modify_order_validation(**_valid_modify_kwargs(order_type="INVALID"))


def test_modify_order_validation_bad_validity():
    with pytest.raises(ApiValueError, match="validity"):
        modify_order_validation(**_valid_modify_kwargs(validity="GTC"))


def test_modify_order_validation_negative_trigger_price():
    with pytest.raises(ApiValueError, match="negative|number"):
        modify_order_validation(**_valid_modify_kwargs(), trigger_price="-1")


def test_modify_order_validation_bad_disclosed_quantity():
    with pytest.raises(ApiValueError, match="integer|negative"):
        modify_order_validation(**_valid_modify_kwargs(), disclosed_quantity="-1")


def test_modify_order_validation_blank_amo():
    with pytest.raises(ApiValueError, match="blank|mandatory"):
        modify_order_validation(**_valid_modify_kwargs(), amo="")


def test_modify_order_validation_product_not_supplied_ok():
    """product is optional for modify_order."""
    modify_order_validation(**_valid_modify_kwargs())


@pytest.mark.parametrize("product", ["CNC", "NRML", "MIS", "MTF"])
def test_modify_order_validation_allowed_products(product):
    """Only the exact canonical codes CNC/NRML/MIS/MTF are accepted."""
    modify_order_validation(**_valid_modify_kwargs(), product=product)


@pytest.mark.parametrize(
    "product",
    [
        "CO",
        "BO",
        "INTRADAY",
        "XYZ",
        # Aliases are rejected, not resolved.
        "Normal",
        "Cash and Carry",
        "cnc",
        "mis",
        "mtf",
        "Intraday",
    ],
)
def test_modify_order_validation_rejects_disallowed_products(product):
    with pytest.raises(ApiValueError, match="Allowed values are CNC, NRML, MIS, MTF"):
        modify_order_validation(**_valid_modify_kwargs(), product=product)


def test_modify_order_validation_blank_product():
    with pytest.raises(ApiValueError, match="blank|mandatory"):
        modify_order_validation(**_valid_modify_kwargs(), product="")


def test_modify_order_validation_rejects_unexpected_exchange_segment_kwarg():
    """exchange_segment is no longer a modify_order parameter."""
    with pytest.raises(TypeError):
        modify_order_validation(**_valid_modify_kwargs(), exchange_segment="nse_cm")


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
        "broker_name": "KOTAK",
        "branch_id": "1",
    }
    kwargs.update(overrides)
    return kwargs


def test_margin_validation_ok():
    margin_validation(**_valid_margin_kwargs())


@pytest.mark.parametrize(
    "field,value",
    [
        ("exchange_segment", "INVALID"),
        # Margin supports a narrower segment set than place order (modify
        # order has no exchange_segment parameter at all).
        ("exchange_segment", "cde_fo"),
        ("exchange_segment", "CDS"),
        ("exchange_segment", "BCD"),
        # Aliases are rejected, not resolved — "NSE"/"MCX" would resolve to
        # allowed canonical segments (nse_cm/mcx_fo), but only the exact
        # canonical string is accepted.
        ("exchange_segment", "NSE"),
        ("exchange_segment", "MCX"),
        ("exchange_segment", "nse"),
        ("product", "INVALID"),
        # Margin does not accept INTRADAY/CO/BO, unlike the general product list.
        ("product", "INTRADAY"),
        ("order_type", "INVALID"),
        # Margin does not accept SP/2L/3L, unlike the general order type list.
        ("order_type", "SP"),
        ("order_type", "2L"),
        # Aliases are rejected, not resolved — "Limit"/"Market" would resolve
        # to allowed canonical order types (L/MKT), but only the exact
        # canonical string is accepted.
        ("order_type", "Limit"),
        ("order_type", "Market"),
        ("transaction_type", "X"),
        # Margin no longer accepts the "Buy"/"Sell" aliases, only B/S.
        ("transaction_type", "Buy"),
        ("transaction_type", "Sell"),
        ("price", "-1"),
        ("quantity", "0"),
        ("quantity", "-1"),
        ("instrument_token", "0"),
        ("instrument_token", "-1"),
        ("instrument_token", "abc"),
        ("broker_name", ""),
        ("broker_name", "   "),
        ("branch_id", ""),
        ("branch_id", "   "),
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
        ("broker_name", 1),
        ("branch_id", 1),
    ],
)
def test_margin_validation_type_errors(field, value):
    with pytest.raises(ApiValueError):
        margin_validation(**_valid_margin_kwargs(**{field: value}))


def test_margin_validation_bad_trigger_price():
    with pytest.raises(ApiValueError):
        margin_validation(**_valid_margin_kwargs(), trigger_price=100)


def test_margin_validation_missing_broker_name():
    with pytest.raises(TypeError):
        margin_validation(**{k: v for k, v in _valid_margin_kwargs().items() if k != "broker_name"})


def test_margin_validation_missing_branch_id():
    with pytest.raises(TypeError):
        margin_validation(**{k: v for k, v in _valid_margin_kwargs().items() if k != "branch_id"})


# ---- per-exchange-segment order validity ------------------------------------


@pytest.mark.parametrize(
    "segment,validity",
    [
        ("nse_cm", "DAY"),
        ("nse_cm", "IOC"),
        ("bse_cm", "DAY"),
        ("bse_cm", "IOC"),
        ("nse_fo", "DAY"),
        ("nse_fo", "IOC"),
        ("bse_fo", "DAY"),
        ("bse_fo", "IOC"),
        ("mcx_fo", "DAY"),
    ],
)
def test_place_order_validity_allowed_per_segment(segment, validity):
    # Should not raise for the documented allowed combinations.
    place_order_validation(**_valid_place_kwargs(exchange_segment=segment, validity=validity))


def test_place_order_mcx_fo_rejects_ioc():
    """MCX F&O allows only DAY (not IOC)."""
    with pytest.raises(ApiValueError, match="Invalid validity 'IOC'.*mcx_fo"):
        place_order_validation(**_valid_place_kwargs(exchange_segment="mcx_fo", validity="IOC"))


@pytest.mark.parametrize("segment", ["nse_cm", "bse_cm", "nse_fo", "bse_fo", "mcx_fo"])
def test_place_order_rejects_unsupported_validity(segment):
    """GTC is never allowed on any segment."""
    with pytest.raises(ApiValueError, match="Invalid validity"):
        place_order_validation(**_valid_place_kwargs(exchange_segment=segment, validity="GTC"))


def test_place_order_validity_segment_alias_resolved():
    """NFO alias resolves to nse_fo -> IOC is allowed."""
    place_order_validation(**_valid_place_kwargs(exchange_segment="NFO", validity="IOC"))


def test_modify_order_validity_uses_default_set():
    """modify_order has no exchange_segment, so validity is always checked
    against the default allowed set (DAY, IOC) — IOC is allowed, GTC isn't."""
    modify_order_validation(**_valid_modify_kwargs(validity="IOC"))  # OK
    with pytest.raises(ApiValueError, match="Invalid validity"):
        modify_order_validation(**_valid_modify_kwargs(validity="GTC"))
