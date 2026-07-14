"""Shared "is this order still modifiable/cancellable" check.

Once an order reaches a terminal state (complete, traded, rejected,
cancelled) it can no longer be modified or cancelled. This looks the order up
in the order book and returns a structured, HTTP-style error when it's
already terminal, so callers reject the request client-side instead of
sending a modify/cancel that the exchange would just reject anyway.
"""

import neo_api_client
from neo_api_client.settings import TERMINAL_ORDER_STATUSES


def check_order_not_terminal(api_client, order_id):
    """Look up ``order_id`` in the order book.

    Returns a ``(item, error)`` tuple:

    - ``error`` is a structured 409 error dict if the order is in a terminal
      state; otherwise ``None`` — the caller should proceed.
    - ``item`` is the matching order-book entry (useful for callers that also
      need to read other fields from it), or ``None`` if the order wasn't
      found. "Not found" is intentionally treated as "proceed" (``error`` is
      ``None``) rather than blocking the request — we only block when we can
      positively confirm the order is terminal.

    Raises whatever the order-book lookup itself raises (e.g. a network or
    API error) — callers that can safely proceed without this information
    (cancel, quick-modify, which already have every field they need) should
    catch that and treat it as "proceed"; callers that need ``item`` to fill
    in missing fields (the order-id-only modify path) should let it
    propagate, since they can't safely proceed without it either way.
    """
    order_book_resp = neo_api_client.OrderReportAPI(api_client).ordered_books()

    if not isinstance(order_book_resp, dict) or "data" not in order_book_resp:
        return None, None

    for item in order_book_resp["data"]:
        if item.get("nOrdNo") == str(order_id).strip():
            status = item.get("ordSt")
            if status in TERMINAL_ORDER_STATUSES:
                return item, {
                    "status_code": 409,
                    "Error": f"Order {order_id} is already '{status}' and can no "
                    "longer be modified or cancelled.",
                    "ordSt": status,
                    "Reason": item.get("rejRsn"),
                    "nOrdNo": order_id,
                }
            return item, None

    return None, None
