from neo_api_client.exceptions import ApiValueError
from neo_api_client.settings import (
    exchange_limits,
    exchange_segment_allowed_values,
    order_type_allowed_values,
    product_allowed_values,
    product_limits,
    segment_limits,
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
    market_protection=None,
    pf=None,
    trigger_price=None,
    tag=None,
):
    # Exchange Segment validation (mandatory, non-blank)
    _require_non_blank(exchange_segment, "exchange_segment")
    if exchange_segment not in exchange_segment_allowed_values:
        raise ApiValueError(
            "Invalid exchange segment. Allowed values are NSE or nse_cm, BSE or bse_cm, NFO or nse_fo, "
            "BFO or bse_fo, CDS or cde_fo, BCD or bcs_fo."
        )

    # Product validation (mandatory, non-blank)
    _require_non_blank(product, "product")
    if product not in product_allowed_values:
        raise ApiValueError(
            "Invalid product. Allowed values are  NRML or Normal, CNC or Cash and Carry, MIS, "
            "INTRADAY, CO or Cover order, BO or Bracket Order."
        )

    # Price validation (mandatory, non-blank numeric string)
    _require_non_blank(price, "price")
    _require_numeric(price, "price")

    # Order type validation (mandatory, non-blank)
    _require_non_blank(order_type, "order_type")
    if order_type not in order_type_allowed_values:
        raise ApiValueError(
            "Invalid order type. Allowed values are L or Limit, MKT or Market, SL or Stop loss limit,"
            "SL-M or Stop loss market, SP or Spread, 2L or Tow leg, 3L or Three Leg."
        )

    # Quantity validation (mandatory, non-blank positive integer string)
    _require_non_blank(quantity, "quantity")
    _require_positive_int(quantity, "quantity")

    # Validity validation (mandatory, non-blank)
    _require_non_blank(validity, "validity")
    if validity not in ["DAY", "IOC"]:
        raise ApiValueError("Invalid validity. Allowed values are DAY, IOC.")

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

    # Market_protection validation (must be non-blank if given)
    if market_protection is not None:
        _require_non_blank(market_protection, "market_protection")

    # pf validation (must be non-blank if given)
    if pf is not None:
        _require_non_blank(pf, "pf")

    # trigger_price validation (optional; must be numeric if given)
    if trigger_price is not None:
        _require_non_blank(trigger_price, "trigger_price")
        _require_numeric(trigger_price, "trigger_price")

    # Tag validation (optional; only a type constraint)
    if tag is not None and not isinstance(tag, str):
        raise ApiValueError("tag must be a string.")


def cancel_order_validation(order_id, amo=None):
    if not isinstance(order_id, str) or not bool(order_id.strip()):
        raise ValueError("order_id parameter must be a non-empty string")

    # AMO validation
    if amo is not None and not isinstance(amo, str):
        raise ApiValueError("AMO must be a string.")


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
    trigger_price=None,
):
    # Exchange Segment validation
    if not isinstance(exchange_segment, str):
        raise ApiValueError("Exchange segment must be a string.")
    if exchange_segment not in exchange_segment_allowed_values:
        raise ApiValueError(
            "Invalid exchange segment. Allowed values are NSE or nse_cm, BSE or bse_cm, NFO or nse_fo, "
            "BFO or bse_fo, CDS or cde_fo, BCD or bcs_fo."
        )

    # Product validation
    if not isinstance(product, str):
        raise ApiValueError("Product must be a string.")
    if product not in product_allowed_values:
        raise ApiValueError(
            "Invalid product. Allowed values are  NRML or Normal, CNC or Cash and Carry, MIS, "
            "INTRADAY, CO or Cover order, BO or Bracket Order."
        )

    # Price validation
    if not isinstance(price, str):
        raise ApiValueError("Price must be a string.")

    # Order type validation
    if not isinstance(order_type, str):
        raise ApiValueError("Order type must be a string.")
    if order_type not in order_type_allowed_values:
        raise ApiValueError(
            "Invalid order type. Allowed values are L or Limit, MKT or Market, SL or Stop loss limit,"
            "SL-M or Stop loss market, SP or Spread, 2L or Tow leg, 3L or Three Leg."
        )

    # Quantity validation
    if not isinstance(quantity, str):
        raise ApiValueError("Quantity must be an string.")

    # Instrument_token validation
    if not isinstance(instrument_token, str):
        raise ApiValueError("Instrument token must be a string.")

    # Transaction type validation
    if not isinstance(transaction_type, str):
        raise ApiValueError("Transaction type must be a string.")
    if transaction_type not in ["B", "S", "Buy", "Sell", "sell", "buy"]:
        raise ApiValueError("Invalid transaction type. Allowed values are B or Buy, S or Sell.")

    # trigger_price validation
    if trigger_price is not None and not isinstance(trigger_price, str):
        raise ApiValueError("trigger_price must be a string.")


def limits_validation(segment, exchange, product):
    #  Segment validation
    if not isinstance(segment, str):
        raise ApiValueError("Segment must be a string.")
    if segment not in segment_limits:
        raise ApiValueError("Invalid segment. Allowed values are CASH, CUR, FO, ALL")

    #  Exchange validation
    if not isinstance(exchange, str):
        raise ApiValueError("Exchange must be a string.")
    if exchange not in exchange_limits:
        raise ApiValueError("Invalid Exchange. Allowed values are NSE, BSE, ALL")

    #  Product validation
    if not isinstance(product, str):
        raise ApiValueError("Product must be a string.")
    if product not in product_limits:
        raise ApiValueError("Invalid Product. Allowed values are CNC, MIS, NRML, ALL")
