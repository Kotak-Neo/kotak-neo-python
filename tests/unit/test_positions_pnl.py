"""Unit tests for the positions() P&L calculation (docs/functions/portfolio/positions.md)."""

from neo_api_client.utils.positions_pnl import (
    compute_position_metrics,
    is_derivatives_segment,
    parse_amount,
)


def _position(**overrides):
    base = {
        "exSeg": "nse_cm",
        "cfBuyQty": "0",
        "cfSellQty": "0",
        "flBuyQty": "0",
        "flSellQty": "0",
        "buyAmt": "0.00",
        "sellAmt": "0.00",
        "cfBuyAmt": "0.00",
        "cfSellAmt": "0.00",
        "multiplier": "1",
        "genNum": "1",
        "genDen": "1",
        "prcNum": "1",
        "prcDen": "1",
        "precision": "2",
    }
    base.update(overrides)
    return base


def test_parse_amount_handles_strings_blank_and_none():
    assert parse_amount("1.50") == 1.50
    assert parse_amount("") == 0.0
    assert parse_amount(None) == 0.0
    assert parse_amount("not-a-number") == 0.0
    assert parse_amount(5) == 5.0


def test_is_derivatives_segment():
    assert is_derivatives_segment("nse_fo") is True
    assert is_derivatives_segment("bse_fo") is True
    assert is_derivatives_segment("mcx_fo") is True
    assert is_derivatives_segment("nse_cm") is False
    assert is_derivatives_segment("bse_cm") is False
    assert is_derivatives_segment(None) is False


def test_equity_carry_forward_long_no_fills_today_uses_holdings_cost():
    """The bug this exists to fix: a carry-forward position with no fills
    today must get average = actual holding cost, not average = LTP, and a
    non-zero Position P&L, not 0."""
    position = _position(cfBuyQty="10", cfSellQty="0")
    holding = {"exchangeIdentifier": "61304", "averagePrice": 100.0}

    result = compute_position_metrics(position, holding, ltp=120.0)

    assert result["netQty"] == 10.0
    assert result["averagePrice"] == 100.0  # not 120.0 (LTP)
    assert result["positionPnl"] == 200.0  # not 0.0
    assert result["pnlCalculationError"] is None


def test_equity_carry_forward_without_matching_holding_reports_error_not_wrong_number():
    """No matching Holdings entry -> report it explicitly, never silently
    fall back to average=LTP/P&L=0."""
    position = _position(cfBuyQty="10", cfSellQty="0")

    result = compute_position_metrics(position, holding=None, ltp=120.0)

    assert result["averagePrice"] is None
    assert result["positionPnl"] is None
    assert result["mtmPnl"] is None
    assert "No matching Holdings entry" in result["pnlCalculationError"]


def test_equity_carry_forward_short():
    position = _position(cfBuyQty="0", cfSellQty="10")
    holding = {"averagePrice": 50.0}

    result = compute_position_metrics(position, holding, ltp=40.0)

    assert result["netQty"] == -10.0
    assert result["averagePrice"] == 50.0
    # Realized/unrealized: sold at 50 (500 total), now valued at 40 -> profit.
    assert result["positionPnl"] == 100.0


def test_flat_position_bought_and_sold_same_qty_today():
    position = _position(flBuyQty="5", flSellQty="5", buyAmt="500.00", sellAmt="520.00")

    result = compute_position_metrics(position, holding=None, ltp=105.0)

    assert result["netQty"] == 0.0
    assert result["averagePrice"] == 0.0
    assert result["positionPnl"] == 20.0
    assert result["pnlCalculationError"] is None


def test_fo_short_carry_forward_uses_cfsellamt_not_holdings():
    """F&O carry-forward never needs (or has) a Holdings entry -- previous
    close (cfSellAmt) is the cost basis."""
    position = _position(exSeg="nse_fo", cfBuyQty="0", cfSellQty="5", cfSellAmt="5000.00")

    result = compute_position_metrics(position, holding=None, ltp=950.0)

    assert result["netQty"] == -5.0
    assert result["averagePrice"] == 1000.0  # 5000 / 5
    assert result["pnlCalculationError"] is None
    # F&O carry-forward: Position P&L and MTM P&L must be equal (§8/§10).
    assert result["positionPnl"] == result["mtmPnl"]


def test_fo_long_carry_forward_uses_cfbuyamt():
    position = _position(exSeg="nse_fo", cfBuyQty="5", cfSellQty="0", cfBuyAmt="4500.00")

    result = compute_position_metrics(position, holding=None, ltp=920.0)

    assert result["netQty"] == 5.0
    assert result["averagePrice"] == 900.0  # 4500 / 5
    assert result["positionPnl"] == result["mtmPnl"]


def test_missing_ltp_reports_error_but_still_computes_average_price():
    """Average price doesn't need LTP -- only P&L does. A missing LTP should
    not also blank out the average."""
    position = _position(cfBuyQty="10", cfSellQty="0")
    holding = {"averagePrice": 100.0}

    result = compute_position_metrics(position, holding, ltp=None)

    assert result["averagePrice"] == 100.0
    assert result["positionPnl"] is None
    assert result["mtmPnl"] is None
    assert "LTP unavailable" in result["pnlCalculationError"]


def test_precision_field_controls_rounding():
    position = _position(cfBuyQty="3", cfSellQty="0", precision="4")
    holding = {"averagePrice": 33.333333}

    result = compute_position_metrics(position, holding, ltp=40.0)

    assert result["averagePrice"] == round(33.333333, 4)


def test_nf_scaling_factor_applied_for_derivatives():
    """multiplier/genNum/genDen/prcNum/prcDen combine into NF, scaling both
    average price and P&L (equity's NF is 1, so this only shows up for F&O)."""
    position = _position(
        exSeg="nse_fo",
        cfBuyQty="0",
        cfSellQty="2",
        cfSellAmt="1000.00",
        multiplier="10",
    )

    result = compute_position_metrics(position, holding=None, ltp=45.0)

    # Sell Avg Price = 1000 / (2 * NF=10) = 50.
    assert result["averagePrice"] == 50.0
