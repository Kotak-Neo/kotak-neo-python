"""Average price / P&L calculation for positions(), per
docs/functions/portfolio/positions.md.

positions() alone can't correctly value a carry-forward position -- equity's
true carry-forward cost basis lives in holdings() (`averagePrice`, matched by
`positions.tok == holdings.exchangeIdentifier`), not in anything the
Positions API itself returns. This module is the pure calculation; the
orchestration (fetching/caching holdings(), fetching LTP via quotes(), and
merging results into each position dict) lives in NeoAPI.positions().
"""

from __future__ import annotations

from typing import Any


def parse_amount(value: Any) -> float:
    """Best-effort numeric parse. API numeric fields are strings (and
    sometimes blank/None); treat anything unparseable as 0 rather than
    raising, since a single bad field shouldn't break the whole calculation."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def is_derivatives_segment(exchange_segment: Any) -> bool:
    """F&O/derivatives segments (nse_fo, bse_fo, mcx_fo, ...) carry their own
    carry-forward cost basis (cfBuyAmt/cfSellAmt, valued at previous close);
    equity/cash segments need Holdings' averagePrice instead -- the Holdings
    API is equity-only. See docs/functions/portfolio/positions.md §8."""
    return isinstance(exchange_segment, str) and exchange_segment.lower().endswith("_fo")


def compute_position_metrics(
    position: dict[str, Any],
    holding: dict[str, Any] | None,
    ltp: float | None,
) -> dict[str, Any]:
    """Compute netQty, averagePrice, positionPnl, and mtmPnl for one position.

    Implements docs/functions/portfolio/positions.md end to end. `holding` is the
    Holdings-API entry matching this position (`exchangeIdentifier` ==
    `position["tok"]`), or None if there isn't one -- fine unless this
    position has equity carry-forward quantity, in which case average
    price/P&L can't be computed without it (reported via
    `pnlCalculationError`, not a wrong answer like average=LTP).
    """
    cf_buy_qty = parse_amount(position.get("cfBuyQty"))
    cf_sell_qty = parse_amount(position.get("cfSellQty"))
    fl_buy_qty = parse_amount(position.get("flBuyQty"))
    fl_sell_qty = parse_amount(position.get("flSellQty"))

    total_buy_qty = cf_buy_qty + fl_buy_qty
    total_sell_qty = cf_sell_qty + fl_sell_qty
    net_qty = total_buy_qty - total_sell_qty
    carry_fwd_qty = cf_buy_qty - cf_sell_qty

    result: dict[str, Any] = {
        "netQty": net_qty,
        "averagePrice": None,
        "positionPnl": None,
        "mtmPnl": None,
        "pnlCalculationError": None,
    }

    derivatives = is_derivatives_segment(position.get("exSeg"))

    # Carry-forward leg, valued at *actual* cost (for Position P&L only --
    # MTM P&L below always uses previous close regardless of segment).
    cf_buy_amt = 0.0
    cf_sell_amt = 0.0
    if carry_fwd_qty != 0:
        if derivatives:
            # F&O: no Holdings averagePrice exists -- previous close
            # (cfBuyAmt/cfSellAmt) is the only cost basis the API exposes.
            if carry_fwd_qty > 0:
                cf_buy_amt = parse_amount(position.get("cfBuyAmt"))
            else:
                cf_sell_amt = parse_amount(position.get("cfSellAmt"))
        else:
            if holding is None:
                result["pnlCalculationError"] = (
                    "No matching Holdings entry for this equity carry-forward "
                    "position (positions.tok not found in "
                    "holdings.exchangeIdentifier) -- cannot compute average "
                    "price/P&L without the actual cost."
                )
                return result
            avg_price = parse_amount(holding.get("averagePrice"))
            if carry_fwd_qty > 0:
                cf_buy_amt = avg_price * carry_fwd_qty
            else:
                cf_sell_amt = avg_price * abs(carry_fwd_qty)

    buy_amt = parse_amount(position.get("buyAmt"))
    sell_amt = parse_amount(position.get("sellAmt"))
    total_buy_amt = buy_amt + cf_buy_amt
    total_sell_amt = sell_amt + cf_sell_amt

    multiplier = parse_amount(position.get("multiplier")) or 1.0
    gen_num = parse_amount(position.get("genNum")) or 1.0
    gen_den = parse_amount(position.get("genDen")) or 1.0
    prc_num = parse_amount(position.get("prcNum")) or 1.0
    prc_den = parse_amount(position.get("prcDen")) or 1.0
    nf = multiplier * (gen_num / gen_den) * (prc_num / prc_den) or 1.0

    precision = int(parse_amount(position.get("precision")) or 2)

    if net_qty > 0 and total_buy_qty:
        average_price = total_buy_amt / (total_buy_qty * nf)
    elif net_qty < 0 and total_sell_qty:
        average_price = total_sell_amt / (total_sell_qty * nf)
    else:
        average_price = 0.0
    result["averagePrice"] = round(average_price, precision)

    if ltp is None:
        result["pnlCalculationError"] = "LTP unavailable -- cannot compute P&L."
        return result

    result["positionPnl"] = round(
        (total_sell_amt - total_buy_amt) + (net_qty * ltp * nf), precision
    )

    # MTM P&L: identical formula, but EVERY carry-forward leg (equity or F&O)
    # is valued at previous close (cfBuyAmt/cfSellAmt) instead of actual cost.
    mtm_total_buy_amt = buy_amt + parse_amount(position.get("cfBuyAmt"))
    mtm_total_sell_amt = sell_amt + parse_amount(position.get("cfSellAmt"))
    result["mtmPnl"] = round(
        (mtm_total_sell_amt - mtm_total_buy_amt) + (net_qty * ltp * nf), precision
    )

    return result
