from neo_api_client.exceptions import ApiValueError
from neo_api_client.settings import exchange_segment as _exchange_segment_map
from neo_api_client.settings import (
    exchange_segment_allowed_values,
    margin_exchange_segment_allowed_values,
    margin_order_type_allowed_values,
    order_type_allowed_values,
    place_order_product_allowed_values,
    price_required_order_types,
    validity_allowed_by_segment,
    validity_allowed_default,
)


def _require_non_blank(value, name):
    """Ensure a mandatory parameter is a non-empty, non-whitespace string."""
    if not isinstance(value, str):
        raise ApiValueError(f"{name} must be a string.")
    if not value.strip():
        raise ApiValueError(f"{name} is mandatory and cannot be blank.")


def _require_numeric(value, name):
    """Ensure a string parameter represents a valid (non-negative) number."""
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ApiValueError(f"{name} must be a valid number, got {value!r}.") from exc
    if parsed < 0:
        raise ApiValueError(f"{name} cannot be negative.")


def _require_positive_int(value, name):
    """Ensure a string parameter represents an integer greater than zero."""
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ApiValueError(f"{name} must be a valid integer, got {value!r}.") from exc
    if parsed <= 0:
        raise ApiValueError(f"{name} must be greater than zero.")


def _require_non_negative_int(value, name):
    """Ensure a string parameter represents an integer of zero or more."""
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ApiValueError(f"{name} must be a valid integer, got {value!r}.") from exc
    if parsed < 0:
        raise ApiValueError(f"{name} cannot be negative.")


def _require_positive_price_for_order_type(price, order_type):
    """Reject a zero price for order types that need a real limit price.

    MKT/SL-M orders execute at the prevailing market price, so price=0 is
    valid there. L/SL orders need an actual limit price — leaving price at
    0 has been observed to make the exchange silently substitute a default
    price instead of rejecting the order.

    ``order_type`` must already be one of the exact canonical codes (checked
    by the caller before this runs), so no alias resolution is needed here.
    """
    if order_type in price_required_order_types and float(price) <= 0:
        raise ApiValueError(f"price must be greater than zero for order_type '{order_type}'.")


def _require_valid_validity(validity, exchange_segment):
    """Validate order validity against the allowed set for the exchange segment.

    Most segments allow DAY and IOC; MCX F&O (``mcx_fo``) allows only DAY. The
    segment is normalized via the alias map, so ``NFO``/``nse_fo`` etc. all
    resolve to the same rule. Segments not explicitly configured fall back to
    the default set (DAY, IOC).
    """
    _require_non_blank(validity, "validity")
    # Normalize the (possibly aliased) segment to its canonical form.
    canonical = _exchange_segment_map.get(exchange_segment, exchange_segment)
    allowed = validity_allowed_by_segment.get(canonical, validity_allowed_default)
    if validity not in allowed:
        raise ApiValueError(
            f"Invalid validity '{validity}' for exchange segment "
            f"'{exchange_segment}'. Allowed values are {', '.join(allowed)}."
        )


def validate_configuration(consumer_key, consumer_secret):
    if not consumer_key:
        raise ApiValueError(
            "Please provide the Consumer Key parameter while creating NeoTradeAPI object. Without Consumer Key "
            "the API cannot be accessed."
        )
    if not consumer_secret:
        raise ApiValueError(
            "Please provide the Consumer Secret parameter while creating NeoTradeAPI object. Without Consumer "
            "Secret the API cannot be accessed."
        )


def place_order_validation(
    exchange_segment,
    product,
    price,
    order_type,
    quantity,
    validity,
    trading_symbol,
    transaction_type,
    amo=None,
    disclosed_quantity=None,
    trigger_price=None,
):
    # Exchange Segment validation (mandatory, non-blank). Only the exact
    # canonical codes are accepted — generic aliases (e.g. "NSE", "BSE") are
    # rejected, not resolved, since they're ambiguous about which specific
    # segment (cash vs. F&O) the order applies to.
    _require_non_blank(exchange_segment, "exchange_segment")
    if exchange_segment not in exchange_segment_allowed_values:
        raise ApiValueError(
            "Invalid exchange segment. Allowed values are nse_cm, bse_cm, nse_fo, bse_fo, mcx_fo."
        )

    # Product validation (mandatory, non-blank). Place order accepts only
    # the exact canonical codes CNC, NRML, MIS, MTF — aliases (e.g. "Normal",
    # "Cash and Carry", "cnc", "Intraday") are rejected, not resolved.
    _require_non_blank(product, "product")
    if product not in place_order_product_allowed_values:
        raise ApiValueError("Invalid product. Allowed values are CNC, NRML, MIS, MTF.")

    # Price validation (mandatory, non-blank numeric string)
    _require_non_blank(price, "price")
    _require_numeric(price, "price")

    # Order type validation (mandatory, non-blank). Only the exact canonical
    # codes are accepted — aliases (e.g. "Limit", "Market") and multi-leg
    # types (SP/2L/3L) are rejected, not resolved.
    _require_non_blank(order_type, "order_type")
    if order_type not in order_type_allowed_values:
        raise ApiValueError("Invalid order type. Allowed values are L, MKT, SL, SL-M.")

    # L/SL orders need a real limit price; MKT/SL-M may legitimately use 0.
    _require_positive_price_for_order_type(price, order_type)

    # Quantity validation (mandatory, non-blank positive integer string)
    _require_non_blank(quantity, "quantity")
    _require_positive_int(quantity, "quantity")

    # Validity validation (mandatory, non-blank, per-exchange-segment allowed set)
    _require_valid_validity(validity, exchange_segment)

    # Trading symbol validation (mandatory, non-blank)
    _require_non_blank(trading_symbol, "trading_symbol")

    # Transaction type validation (mandatory, non-blank)
    _require_non_blank(transaction_type, "transaction_type")
    if transaction_type not in ["B", "S", "Buy", "Sell"]:
        raise ApiValueError("Invalid transaction type. Allowed values are B or Buy, S or Sell.")

    # AMO validation (mandatory field with a default; must be non-blank if given)
    if amo is not None:
        _require_non_blank(amo, "amo")

    # Disclosed Quantity validation (must be non-blank if given)
    if disclosed_quantity is not None:
        _require_non_blank(disclosed_quantity, "disclosed_quantity")
        _require_non_negative_int(disclosed_quantity, "disclosed_quantity")

    # trigger_price validation (optional; must be numeric if given)
    if trigger_price is not None:
        _require_non_blank(trigger_price, "trigger_price")
        _require_numeric(trigger_price, "trigger_price")


def cancel_order_validation(order_id, amo=None):
    # order_id is mandatory (sent as "on"); must be a non-blank string.
    _require_non_blank(order_id, "order_id")

    # AMO is optional here but, when supplied, must be a non-blank string.
    if amo is not None:
        _require_non_blank(amo, "amo")


def modify_order_validation(
    order_id,
    price,
    order_type,
    quantity,
    validity,
    trigger_price=None,
    disclosed_quantity=None,
    amo=None,
):
    """Validate mandatory modify-order inputs before the request is built.

    Rejects blank/invalid values for the fields the API requires:
    order_id (no), price (pr), order_type (pt), quantity (qt), validity (vd),
    and the numeric optionals when supplied.

    modify_order has no exchange_segment parameter, so validity is always
    checked against the default allowed set (DAY, IOC).
    """
    # order_id (mandatory, non-blank)
    _require_non_blank(order_id, "order_id")

    # Price (mandatory, non-blank numeric string)
    _require_non_blank(price, "price")
    _require_numeric(price, "price")

    # Order type (mandatory, non-blank, from the allowed set). Only the exact
    # canonical codes are accepted — aliases (e.g. "Limit", "Market") and
    # multi-leg types (SP/2L/3L) are rejected, not resolved.
    _require_non_blank(order_type, "order_type")
    if order_type not in order_type_allowed_values:
        raise ApiValueError("Invalid order type. Allowed values are L, MKT, SL, SL-M.")

    # L/SL orders need a real limit price; MKT/SL-M may legitimately use 0.
    _require_positive_price_for_order_type(price, order_type)

    # Quantity (mandatory, non-blank positive integer string)
    _require_non_blank(quantity, "quantity")
    _require_positive_int(quantity, "quantity")

    # Validity (mandatory, non-blank). modify_order has no exchange_segment,
    # so the default allowed set (DAY, IOC) always applies.
    _require_valid_validity(validity, None)

    # trigger_price (optional; must be a non-negative number when supplied)
    if trigger_price is not None:
        _require_non_blank(trigger_price, "trigger_price")
        _require_numeric(trigger_price, "trigger_price")

    # disclosed_quantity (optional; must be a non-negative integer when supplied)
    if disclosed_quantity is not None:
        _require_non_blank(disclosed_quantity, "disclosed_quantity")
        _require_non_negative_int(disclosed_quantity, "disclosed_quantity")

    # amo (optional; must be non-blank when supplied)
    if amo is not None:
        _require_non_blank(amo, "amo")


def order_history_validation(order_id):
    if not isinstance(order_id, str):
        raise ValueError("order_id parameter must be a non-empty string")


def margin_validation(
    exchange_segment,
    price,
    order_type,
    product,
    quantity,
    instrument_token,
    transaction_type,
    broker_name,
    branch_id,
    trigger_price=None,
):
    # Exchange Segment validation (mandatory). Margin ("exSeg") accepts only
    # the exact canonical codes nse_cm, bse_cm, nse_fo, bse_fo, mcx_fo —
    # aliases (e.g. "NSE", "MCX") are rejected, not resolved.
    _require_non_blank(exchange_segment, "exchange_segment")
    if exchange_segment not in margin_exchange_segment_allowed_values:
        raise ApiValueError(
            "Invalid exchange segment. Allowed values are nse_cm, bse_cm, nse_fo, bse_fo, mcx_fo."
        )

    # Product validation (mandatory). Margin ("prod") accepts only the exact
    # canonical codes CNC, NRML, MIS, MTF — aliases are rejected, not resolved.
    _require_non_blank(product, "product")
    if product not in place_order_product_allowed_values:
        raise ApiValueError("Invalid product. Allowed values are CNC, NRML, MIS, MTF.")

    # Price validation (mandatory). Margin ("prc") may be zero or a positive number.
    _require_non_blank(price, "price")
    _require_numeric(price, "price")

    # Order type validation (mandatory). Margin ("prcTp") accepts only the
    # exact canonical codes L, MKT, SL, SL-M — aliases (e.g. "Limit", "Market")
    # are rejected, not resolved.
    _require_non_blank(order_type, "order_type")
    if order_type not in margin_order_type_allowed_values:
        raise ApiValueError("Invalid order type. Allowed values are L, MKT, SL, SL-M.")

    # Quantity validation (mandatory). Margin ("qty") must be a non-zero positive value.
    _require_non_blank(quantity, "quantity")
    _require_positive_int(quantity, "quantity")

    # Instrument token validation (mandatory). Margin ("tok") must be a valid
    # (positive integer) instrument token.
    _require_non_blank(instrument_token, "instrument_token")
    _require_positive_int(instrument_token, "instrument_token")

    # Transaction type validation (mandatory). Margin ("trnsTp") accepts only B, S.
    _require_non_blank(transaction_type, "transaction_type")
    if transaction_type not in ["B", "S"]:
        raise ApiValueError("Invalid transaction type. Allowed values are B, S.")

    # Broker name validation (mandatory). Margin ("brkName") must be a non-blank string.
    _require_non_blank(broker_name, "broker_name")

    # Branch id validation (mandatory). Margin ("brnchId") must be a non-blank string.
    _require_non_blank(branch_id, "branch_id")

    # trigger_price validation
    if trigger_price is not None and not isinstance(trigger_price, str):
        raise ApiValueError("trigger_price must be a string.")
