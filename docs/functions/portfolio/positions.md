# **Positions**
Gets positions

```python
client.positions()
```

### Example

```python
from neo_api_client import NeoAPI


# First initialize session and generate session token
client = NeoAPI(environment="prod", access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp="")
client.totp_validate(mpin="")

try:
    client.positions()
except Exception as e:
    print("Exception when calling PositionsApi->positions: %s\n" % e)
```

### Return type

**object**

### Sample response

`netQty`/`averagePrice`/`positionPnl`/`mtmPnl`/`pnlCalculationError` (last 5
fields) are added by `positions()` itself — everything above them, including
`ltp`, is the raw broker response. This example is a fresh fill today (no
carry-forward: `cfBuyQty`/`cfSellQty` are both `0`), so `averagePrice` is
simply `buyAmt / flBuyQty` here (475200 / 225); a carry-forward position
would factor in Holdings' `averagePrice` instead — see
[Positions Calculations](#positions-calculations--computed-automatically) below.

`ltp` is used directly for `positionPnl`/`mtmPnl` — no separate `quotes()`
call is needed unless a position is missing it.

```json
{
    "stat": "ok",
    "stCode": 200,
    "data": [
        {
            "actId": "ABCXYZ61",
            "brdLtQty": 225,
            "cfBuyAmt": "0.00",
            "cfSellAmt": "0.00",
            "cfBuyQty": "0",
            "cfSellQty": "0",
            "exSeg": "nse_fo",
            "buyAmt": "475200.00",
            "sellAmt": "0.00",
            "flBuyQty": "225",
            "flSellQty": "0",
            "prod": "NRML",
            "series": "XX",
            "tok": "61304",
            "trdSym": "TCS26JULFUT",
            "optTp": "XX",
            "stkPrc": "0.00",
            "type": "FUTSTK",
            "sym": "TCS",
            "sqrFlg": "Y",
            "posFlg": "true",
            "lotSz": "225",
            "multiplier": "1",
            "precision": "2",
            "prcNum": "1",
            "prcDen": "1",
            "hsUpTm": "2026/07/24 12:57:46",
            "expDt": "28 Jul, 2026",
            "exp": "1785196800",
            "genNum": "1",
            "genDen": "1",
            "dscQty": "",
            "upldPrc": "0.00",
            "updRecvTm": 1784878066658915084,
            "ltp": "2117.00",
            "netQty": 225,
            "averagePrice": 2112.0,
            "positionPnl": 1125.0,
            "mtmPnl": 1125.0,
            "pnlCalculationError": null
        }
    ]
}

```

### Positions Calculations — computed automatically

`positions()` adds `netQty`, `averagePrice`, `positionPnl`, `mtmPnl`, and
`pnlCalculationError` to every position dict in the response, in addition to
all the raw fields above. You don't need to compute these yourself.

| Field | Meaning |
|---|---|
| `netQty` | Net quantity — see §5 below |
| `averagePrice` | Correct average price — see §7 below |
| `positionPnl` | Position P&L (§9) |
| `mtmPnl` | MTM/Day P&L (§10) |
| `pnlCalculationError` | `None` when the three fields above were computed successfully; otherwise a string explaining why (e.g. no matching Holdings entry for an equity carry-forward position, or LTP was unavailable) — in that case the affected field(s) are `None`, **never** a silently wrong number like `averagePrice = LTP`. |

> **Why this matters:** for a carry-forward position with no fills today,
> naively computing average price from the raw fields above alone (e.g.
> using `upldPrc`, or `cfBuyAmt`/`cfSellAmt` as if they were the acquisition
> cost) gives **average = LTP** and **P&L = 0**, because those fields don't
> carry equity's true carry-forward cost basis. The Kotak Neo app shows the
> correct, non-zero average/P&L for the same position by pulling the real
> cost basis from [Holdings](holdings.md). `positions()` does the same: it
> pulls `averagePrice` from Holdings (matched by
> `positions.tok == holdings.exchangeIdentifier`), not just the
> closing-price shortcut.

To do this, `positions()` needs holdings data available on every call,
regardless of what the response turns out to contain, so it isn't fetched
lazily or skipped for F&O-only accounts. First it checks whether holdings
has already been fetched **today** — by an earlier `positions()` call, or by
you calling `holdings()` directly, from this process or an earlier run of
it — and reuses that cached result if so; otherwise it fetches holdings
itself (one network call) before continuing. Either way, this internal use
never costs more than one network call per calendar day. A direct call to
`holdings()` is different: it's a live read and always hits the network,
regardless of what's cached — see
[Holdings](holdings.md#always-a-live-call--and-what-it-feeds-internally-into-positions)
for the full distinction. A failed fetch isn't cached, so the next call that
needs holdings retries rather than locking in "no holdings" for the rest of
the day.

> **Note:** the cache is persisted to disk (default location
> `~/.kotak_neo/holdings_cache`, overridable via `NEO_HOLDINGS_CACHE_DIR`,
> scoped per account/UCC), not just held in memory — so it survives across
> separate runs of the same script the same day, not only repeat calls
> within one long-lived process.

For current LTP, `positions()` (`portfolio/v2/positions`) returns its own
`ltp` field per position (see the sample response above), which is used
directly — no extra call needed in the common case. `quotes()` is only used
as a fresh, per-call fallback batch for any position where `ltp` is missing
or unparseable (e.g. an older backend response), batched across all such
positions in as few calls as possible.

The rest of this section is the calculation `positions()` performs — useful
if you want to verify a number, understand an edge case, or reimplement this
against another language/client that doesn't do it for you.

#### 1. Two P&Ls

| P&L | What it tells you | Reference price |
|---|---|---|
| **Position P&L** | Total profit since you entered the position | Actual average price |
| **MTM P&L (Day P&L)** | Profit for today only | Previous close |

The rest of §2–§9 covers **Position P&L** in full. **MTM P&L** uses the same
steps with one field changed — given as a short block at the end (§10).

#### 2. Data sources

##### Positions API — today's activity and carry-forward quantity

| Field | Meaning |
|---|---|
| `tok` | Instrument token (used to match with Holdings) |
| `cfBuyQty` | Carry-forward buy quantity (from previous days) |
| `cfSellQty` | Carry-forward sell quantity (from previous days) |
| `flBuyQty` | Today's ("fresh") buy quantity |
| `flSellQty` | Today's sell quantity |
| `buyAmt` | Today's buy amount (fresh fills only) |
| `sellAmt` | Today's sell amount (fresh fills only) |
| `cfBuyAmt` | Carry-forward buy amount **valued at previous close** — used for MTM P&L (§10) |
| `cfSellAmt` | Carry-forward sell amount **valued at previous close** — used for MTM P&L (§10) |
| `multiplier`, `genNum`, `genDen`, `prcNum`, `prcDen` | Unit-scaling factors (see §4) |
| `precision` | Decimal places for the final average price |
| `ltp` | Current last-traded price — used directly for P&L (see §9/§10); `quotes()` is only a fallback if this is missing |

See the sample response above for these fields in context.

##### Holdings API — actual cost of equity carry-forward

| Field | Meaning |
|---|---|
| `exchangeIdentifier` | Instrument identifier (used to match with Positions) |
| `averagePrice` | **Actual average purchase price** of the holding |

> **Match on `exchangeIdentifier`, not `instrumentToken`.** Holdings has both
> fields, and they are *not* the same value — `instrumentToken` is a different
> identifier for the holding record itself. The matching key for this
> calculation is specifically `exchangeIdentifier`, which lines up with
> `positions.tok` (see [Holdings](holdings.md)'s sample response).
>
> `averagePrice` is what you actually paid — it gives the correct **Position
> P&L** for equity carry-forward. The Holdings API is **equity/demat only**;
> F&O carry-forward is handled in §8.

#### 3. Matching a position to its holding

A carry-forward position and its holding are linked by token:

```
positions.tok  ==  holdings.exchangeIdentifier
```

Match this **per instrument, before** using `averagePrice`, because a single position can
contain **both** carry-forward quantity **and** quantity traded today.

#### 4. The scaling factor (NF)

The API stores amounts in a scaled form. To convert between amounts and real rupee
prices we use a single scaling factor:

```
NF = multiplier × (genNum / genDen) × (prcNum / prcDen)
```

- **Equity:** `NF = 1`. Amounts are already in plain rupees, so NF can be ignored.
- **F&O:** `NF` handles the lot/price unit conversion.

Because `averagePrice` exists **only for equity**, wherever `averagePrice` appears below, `NF = 1`.

#### 5. Quantity

```
Total Buy Qty   = cfBuyQty  + flBuyQty
Total Sell Qty  = cfSellQty + flSellQty

Carry Fwd Qty   = cfBuyQty  - cfSellQty          (positive = long CF, negative = short CF)

Net Qty         = Total Buy Qty - Total Sell Qty
```

`Net Qty` sign tells you the current position:
`> 0` long · `< 0` short · `= 0` flat.

#### 6. Amounts

An amount has a **today part** and a **carry-forward part**.

**Today's amounts**

```
buyAmt      = today's buy amount   (fresh fills)
sellAmt     = today's sell amount  (fresh fills)
```

**Carry-forward amount (at actual cost)**

Value the carry-forward leg at its actual cost using `averagePrice`. The sign of the
carry-forward quantity decides which side it lands on:

```
Carry Fwd Qty = cfBuyQty - cfSellQty

If Carry Fwd Qty > 0 (long CF, e.g. equity):
    CF Buy Amt  = averagePrice × Carry Fwd Qty
    CF Sell Amt = 0

If Carry Fwd Qty < 0 (short CF, F&O — see §8):
    CF Sell Amt = averagePrice × |Carry Fwd Qty|
    CF Buy Amt  = 0
```

**Combine**

```
Total Buy Amt   = buyAmt  + CF Buy Amt
Total Sell Amt  = sellAmt + CF Sell Amt
```

#### 7. Average price

The average price of the **active** position:

```
Buy Avg Price  = Total Buy Amt  / (Total Buy Qty  × NF)
Sell Avg Price = Total Sell Amt / (Total Sell Qty × NF)

Average Price =
    Net Qty > 0  →  Buy Avg Price
    Net Qty < 0  →  Sell Avg Price
    Net Qty = 0  →  0
```

Round to `precision` decimal places.

**Why buy-side for a long, sell-side for a short:** for a long position the average is
about *what you paid to build it*, so only buys matter — selling part of it reduces the
quantity but does not change what the remaining shares cost. The reverse holds for a
short.

#### 8. F&O carry-forward (no Holdings `averagePrice`)

The Holdings API is equity-only, so **F&O carry-forward has no `averagePrice`**. F&O is settled
against the daily settlement price — overnight profit is booked each day — so the
correct reference for a carried F&O leg is the **previous close**, which is exactly what
`cfBuyAmt` / `cfSellAmt` contain.

So the carry-forward cost source depends on segment:

| Segment | Carry-forward cost source |
|---|---|
| Equity | `averagePrice` from Holdings API |
| F&O | `cfBuyAmt` / `cfSellAmt` from Positions API (previous close) |

*(A true cost basis for F&O would require rebuilding the entry price from trade history;
previous close is the defensible default and the only value the API exposes. A
consequence: for an F&O carry-forward, Position P&L and MTM P&L are the same number.)*

#### 9. Position P&L

```
Position P&L =
    (Total Sell Amt - Total Buy Amt)
    + (Net Qty × LTP × NF)
```

The first bracket is realized value (sells minus buys); the second values the open
quantity at the current LTP. Together they give **total profit since entry**
(realized + unrealized).

#### 10. MTM P&L (today's profit only)

Same formula as Position P&L, with **one change**: value **every** carry-forward leg at
**previous close** (`cfBuyAmt` / `cfSellAmt`) instead of `averagePrice`.

```
Total Buy Amt  = buyAmt  + cfBuyAmt
Total Sell Amt = sellAmt + cfSellAmt

MTM P&L = (Total Sell Amt - Total Buy Amt) + (Net Qty × LTP × NF)
```

*(For F&O this equals Position P&L, since F&O carry-forward already uses previous
close.)*

#### 11. Quick reference

| Step | Formula |
|---|---|
| Net Qty | `(cfBuyQty + flBuyQty) - (cfSellQty + flSellQty)` |
| CF cost (equity) | `averagePrice × (cfBuyQty - cfSellQty)` |
| Total Buy Amt | `buyAmt + CF Buy Amt` |
| Total Sell Amt | `sellAmt + CF Sell Amt` |
| Average Price | Buy Avg if long, Sell Avg if short, else 0 |
| Position P&L | `(Total Sell Amt - Total Buy Amt) + Net Qty × LTP × NF` |
| MTM P&L | same, but carry-forward valued at `cfBuyAmt` / `cfSellAmt` |

Implementation, if you want to trace the actual code: `neo_api_client/utils/positions_pnl.py`
(`compute_position_metrics()`) for the calculation itself, and
`NeoAPI.positions()`/`NeoAPI._enrich_positions_with_pnl()` in
`neo_api_client/neo_api.py` for the orchestration (holdings caching, LTP batching).

### HTTP request headers

 - **Endpoint**: `portfolio/v2/positions`
 - **Accept**: application/json


### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Gets the Positoin data for a client account  |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |
