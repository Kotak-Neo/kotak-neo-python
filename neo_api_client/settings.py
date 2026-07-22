"""
Add the settings related information in the given file
"""

UAT_URL = {
    "place_order": "quick/order/rule/ms/place",
    "cancel_order": "quick/order/cancel",
    "modify_order": "quick/order/vr/modify",
    "order_history": "quick/order/history",
    "order_book": "quick/user/orders",
    "trade_report": "quick/user/trades",
    "positions": "quick/user/positions",
    "holdings": "portfolio/v1/holdings",
    "margin": "quick/user/check-margin",
    "scrip_master": "script-details/1.0/masterscrip/file-paths",
    "limits": "quick/user/limits",
    "logout": "api/1.0/logout",
    "totp_login": "api/1.0/login/v6/totp/login",
    "totp_validate": "api/1.0/login/v6/totp/validate",
    "get_client_ip": "login/1.0/get-client-ip",
    "quotes_neo_symbol": "script-details/1.0/quotes/neosymbol/{neo_symbols}/{quote_type}",
}

PROD_URL = {
    "place_order": "quick/order/rule/ms/place",
    "cancel_order": "quick/order/cancel",
    "modify_order": "quick/order/vr/modify",
    "order_history": "quick/order/history",
    "order_book": "quick/user/orders",
    "trade_report": "quick/user/trades",
    "positions": "quick/user/positions",
    "holdings": "portfolio/v1/holdings",
    "margin": "quick/user/check-margin",
    "scrip_master": "script-details/1.0/masterscrip/file-paths",
    "limits": "quick/user/limits",
    "logout": "apim/login/2.0/logout",
    "totp_login": "login/1.0/tradeApiLogin",
    "totp_validate": "login/1.0/tradeApiValidate",
    "get_client_ip": "login/1.0/get-client-ip",
    "quotes_neo_symbol": "/script-details/1.0/quotes/neosymbol/{neo_symbols}/{quote_type}",
}

# Exchange segments accepted by place order. Only these exact canonical
# codes are accepted — generic aliases (e.g. "NSE", "BSE") are rejected, not
# resolved, since they're ambiguous about which specific segment (cash vs.
# F&O) the order applies to; resolving them silently could route an order to
# the wrong segment (e.g. "BSE" always resolving to bse_cm even when the
# caller meant bse_fo).
exchange_segment_allowed_values = [
    "nse_cm",
    "bse_cm",
    "nse_fo",
    "bse_fo",
    "mcx_fo",
]

product_allowed_values = [
    "NRML",
    "CNC",
    "MIS",
    "INTRADAY",
    "CO",
    "BO",
    "Normal",
    "Cash and Carry",
    "Cover Order",
    "Bracket Order",
    "MTF",
]

# Product types accepted by the place-order (and margin) API. Only these
# exact canonical codes are accepted — aliases (e.g. "Normal", "Cash and
# Carry") are rejected, not resolved.
place_order_product_allowed_values = ["CNC", "NRML", "MIS", "MTF"]

# Exchange segments accepted by the check-margin API. Only these exact
# canonical codes are accepted — aliases (e.g. "NSE", "MCX") are rejected, not
# resolved.
margin_exchange_segment_allowed_values = ["bse_cm", "nse_cm", "nse_fo", "bse_fo", "mcx_fo"]

# Order types accepted by the check-margin API. Only these exact canonical
# codes are accepted — aliases (e.g. "Limit", "Market") are rejected, not
# resolved.
margin_order_type_allowed_values = ["L", "MKT", "SL", "SL-M"]

# Order types accepted by place/modify order. Only these exact canonical
# codes are accepted — aliases (e.g. "Limit", "Market") and multi-leg types
# (SP/2L/3L) are rejected, not resolved.
order_type_allowed_values = [
    "L",
    "MKT",
    "SL",
    "SL-M",
]

exchange_segment = {
    "nse_cm": "nse_cm",
    "NSE": "nse_cm",
    "nse": "nse_cm",
    "BSE": "bse_cm",
    "bse": "bse_cm",
    "bse_cm": "bse_cm",
    "NFO": "nse_fo",
    "nse_fo": "nse_fo",
    "nfo": "nse_fo",
    "BFO": "bse_fo",
    "bse_fo": "bse_fo",
    "bfo": "bse_fo",
    "MCX": "mcx_fo",
    "mcx": "mcx_fo",
    "mcx_fo": "mcx_fo",
}

product = {
    "Normal": "NRML",
    "NRML": "NRML",
    "CNC": "CNC",
    "cnc": "CNC",
    "Cash and Carry": "CNC",
    "MIS": "MIS",
    "mis": "MIS",
    "INTRADAY": "INTRADAY",
    "intraday": "INTRADAY",
    "Cover Order": "CO",
    "co": "CO",
    "CO": "CO",
    "BO": "BO",
    "Bracket Order": "BO",
    "bo": "BO",
    "mtf": "MTF",
    "MTF": "MTF",
}

order_type = {
    "Limit": "L",
    "L": "L",
    "l": "L",
    "MKT": "MKT",
    "mkt": "MKT",
    "Market": "MKT",
    "sl": "SL",
    "SL": "SL",
    "Stop loss limit": "SL",
    "Stop loss market": "SL-M",
    "SL-M": "SL-M",
    "sl-m": "SL-M",
    "Spread": "SP",
    "SP": "SP",
    "sp": "SP",
    "2L": "2L",
    "2l": "2L",
    "Two Leg": "2L",
    "3L": "3L",
    "3l": "3L",
    "Three leg": "3L",
}

# Order types (canonical codes) that don't use a trigger price — a trigger is
# only meaningful for stop-loss variants (SL/SL-M). For these, the REST API
# still requires the "tp" field to be present, but the value doesn't matter,
# so the SDK sends "0" and doesn't require the caller to supply it.
NO_TRIGGER_ORDER_TYPES = {"L", "MKT"}

# Response "stCode" for a modify/cancel request rejected because the order is
# already complete, e.g. {"stCode": 1021, "errMsg": "order is completed", ...}.
ORDER_ALREADY_COMPLETE_ST_CODE = 1021

# Order types (canonical codes) that need a real, strictly-positive limit
# price. MKT and SL-M orders execute at the prevailing market price, so
# price=0 is valid there; L and SL orders need an actual limit price —
# sending price=0 (or blank) has been observed to make the exchange
# silently substitute a default price (e.g. 1) instead of rejecting the
# order, resulting in an unintended fill at a nonsense price.
price_required_order_types = ["L", "SL"]

# Allowed order-validity values per (canonical) exchange segment, used by place
# and modify order validation. Keyed by the normalized segment name (the value
# side of the `exchange_segment` map above). Segments not listed fall back to
# the default set below.
validity_allowed_by_segment = {
    "nse_cm": ["DAY", "IOC"],
    "bse_cm": ["DAY", "IOC"],
    "nse_fo": ["DAY", "IOC"],
    "bse_fo": ["DAY", "IOC"],
    "mcx_fo": ["DAY"],
}
# Default validity set for any segment not explicitly listed above.
validity_allowed_default = ["DAY", "IOC"]

stock_key_mapping = {
    "ltt": "last_traded_time",
    "v": "volume",
    "ltp": "last_traded_price",
    "ltq": "last_traded_quantity",
    "tbq": "total_buy_quantity",
    "tsq": "total_sell_quantity",
    "bp": "buy_price",
    "sp": "sell_price",
    "bq": "buy_quantity",
    "sq": "sell_quantity",
    "ap": "average_price",
    "oi": "open_interest",
    "lo": "low",
    "h": "high",
    "lcl": "lower_circuit_limit",
    "ucl": "upper_circuit_limit",
    "yh": "52week_high",
    "yl": "52week_low",
    "op": "open",
    "c": "close",
    "mul": "multiplier",
    "prec": "precision",
    "cng": "change",
    "nc": "net_change_percentage",
    "to": "total_traded_value",
    "tk": "instrument_token",
    "e": "exchange_segment",
    "ts": "trading_symbol",
    "request_type": "request_type",
}

index_key_mapping = {
    "iv": "last_traded_price",
    "ic": "prev_day_close",
    "tvalue": "timestamp",
    "highPrice": "high_price",
    "lowPrice": "low_price",
    "openingPrice": "open",
    "mul": "multiplier",
    "prec": "precision",
    "cng": "change",
    "nc": "net_change_percentage",
    "tk": "instrument_token",
    "e": "exchange_segment",
}

MarketDepthResp = {"depth": {}}
MarketDepthResp["depth"]["buy"] = [
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
]
MarketDepthResp["depth"]["sell"] = [
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
    {"price": "", "quantity": "", "orders": ""},
]

ReqTypeValues = {
    "CONNECTION": "cn",
    "SCRIP_SUBS": "mws",
    "SCRIP_UNSUBS": "mwu",
    "INDEX_SUBS": "ifs",
    "INDEX_UNSUBS": "ifu",
    "DEPTH_SUBS": "dps",
    "DEPTH_UNSUBS": "dpu",
    "CHANNEL_RESUME": "cr",
    "CHANNEL_PAUSE": "cp",
    "SNAP_MW": "mwsp",
    "SNAP_DP": "dpsp",
    "SNAP_IF": "ifsp",
    "OPC_SUBS": "opc",
    "THROTTLING_INTERVAL": "ti",
    "STR": "str",
    "FORCE_CONNECTION": "fcn",
}


# live_fin_key = "neotradeapi"

market_protection = 0
QuotesChannel = 1

help_functions = {
    1: 'help("place_order")',
    2: 'help("modify_order")',
    3: 'help("holdings")',
    4: 'help("positions")',
    5: 'help("limits")',
    6: 'help("trade_report")',
    7: 'help("margin_required")',
    8: 'help("cancel_order")',
    9: 'help("order_history")',
    10: 'help("scrip_master")',
    11: 'help("quotes")',
    12: 'help("socket")',
    13: 'help("search_scrip")',
    14: 'help("order_report")',
    15: 'help("subscribe_to_orderfeed")',
    16: "help()",
}

ORDER_SOURCE = "NEOTRADEAPI"
