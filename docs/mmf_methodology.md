# Money-market fund series — methodology

Synthetic monthly total-return and price series for **0% TER** money-market
funds holding short-dated U.S. Treasuries / cash, from `start_month` in
[`build_range.json`](../build_range.json) (**December 1969**, the base row; returns
start January 1970) through the **last complete calendar month before the build
date** (inclusive `YYYYMM`; a build run on 2026-10-03 ends at 202609). The builder
fails, writing nothing, if any input doesn't yet fully cover that end month. Figures
quoted below are **as of the Sep-2026 build** (196912 → 202609, 682 rows). Built by
[`scripts/build_mmf.py`](../scripts/build_mmf.py).

## Funds

| File | Bucket | Rate | Avg life | MtM duration | Income window |
|---|---|---|---|---|---|
| [`mmf_0_90dtm.csv`](../mmf_0_90dtm.csv) | 0–90 DTM | 13-week bill | ~45 d | 45/365 yr | trailing 3 mo |
| [`mmf_0_30dtm.csv`](../mmf_0_30dtm.csv) | 0–30 DTM | 4-week bill | ~15 d | 15/365 yr | trailing 1 mo |
| [`mmf_0dtm.csv`](../mmf_0dtm.csv) | overnight | SOFR (secured, **canonical**) | ~0 | 0 (flat NAV) | current mo |
| [`mmf_0dtm_fed_funds.csv`](../mmf_0dtm_fed_funds.csv) | overnight | effective fed funds (benchmark) | ~0 | 0 (flat NAV) | current mo |

**Overnight funds** (`0dtm`, `0dtm_fed_funds`): zero-duration cash. The rate is an
add-on (actual/360) fed through the same `investment_yield()` at tenor 1, which
collapses to the ×365/360 actual-365 conversion; `max_dtm 0` → duration 0 → flat
`price_idx`=100, so all return is coupon. **`0dtm` is canonical**: it uses **SOFR**
(secured Treasury repo) — what a government MMF earns and what you can hold — real
from 2018-04 and proxied before as fed funds minus the mean fed-funds − SOFR spread
(**~0.3 bp**, so pre-2018 ≈ `0dtm_fed_funds`). `0dtm_fed_funds` uses **effective
fed funds** (unsecured, interbank, 1954+) as a reference benchmark. Both yield
**above** the bill funds
(CAGR ~5.0% vs 4.5–4.7%) — the T-bill safety/liquidity premium, a full-history
average dominated by the 1970s-80s (in 2018+ all four sit within a few bp).

Canonical latest series live at the **repo root**. Each build also writes a
**timestamped** snapshot `output/<YYYYMMDD_HHMM>_mmf_<fund>.csv` (stamp taken at
write time) so `output/` accumulates build history. `scripts/plot_mmf.py`
renders two 3-pane comparison charts (price index semilog, annual coupon, monthly
coupon delta) — `mmf_30-90DTM_compare.png` (0–30 vs 0–90 bills) and
`mmf_0dtm_compare.png` (fed funds vs SOFR cash) — with the same root/`output/`
timestamping; it needs matplotlib (`.venv`).

## Columns

| Column | Meaning |
|---|---|
| `yyyymm` | Month key, integer (e.g. `197001` = Jan 1970). |
| `price_idx` | Price / NAV index of the **distributing** class (coupons paid out, NAV marks to market). = 100 in the base row (Dec-1969). Cyclical: rises when yields fall, falls when they rise. |
| `coupon_rate_monthly` | Monthly coupon as a fraction of NAV (decimal) — cash a distributing holder receives that month. Smoothed to a level rate. |
| `coupon_rate_annual` | `coupon_rate_monthly × 12` (simple, not compounded). |
| `tr_idx` | Total-return index of the **accumulating** class (coupons reinvested). = 100 in the same base row (Dec-1969). |

The two classes describe one portfolio and are linked by the exact identity
`tr_return[t] = price_return[t] + coupon_rate_monthly[t]`.

## Model

A "0–N DTM" fund buys the ~N-day bill at auction and holds it to maturity, so
the book is a ladder of remaining lives spread uniformly over 0–N days.

1. **Yield.** FRED quotes bills on a **discount basis**; convert to the
   bond-equivalent (investment) yield actually earned:
   `y = d · (365/360) / (1 − d · tenor/360)` (decimal). Uplift reaches ~+0.8%
   at the 1981 peak for the 13-week bill.
2. **Income (carry).** The book holds bills bought over the trailing ~N days,
   each locked at the N-day yield prevailing then, so
   `coupon_rate_annual = trailing-average(y_month_avg)` — smooth, and it *lags*
   the market like a real money-fund distribution yield.
   `coupon_rate_monthly = coupon_rate_annual / 12`.
3. **Mark-to-market.** `price_return[t] = −(avg_life/365) · (y_eom[t] − y_eom[t−1])`
   using **month-end** yields; `price_idx` compounds it.
4. **Total return.** `tr_idx` compounds `coupon_rate_monthly + price_return`.

Each fund runs over **all** FRED history (back to 1954), and only then is the
window kept, so even its first rows hold a full ladder of real earlier bills. Both
indices are then rebased to 100 at the window's first row (the base, `start_month`);
every later row's change is that month's real return.

Month-average yields drive income; month-end yields drive the MtM — separated
using the **daily** FRED series.

## Data sources (public, FRED)

| Series | Use | Coverage |
|---|---|---|
| `DTB3` — 3-month bill, discount basis, daily | 0–90 fund yield (all history) | 1954→ |
| `DTB4WK` — 4-week bill, discount basis, daily | 0–30 fund yield | **2001-07→** |
| `SOFR` — secured overnight financing rate, daily | 0dtm (canonical cash) | **2018-04→** |
| `DFF` — effective fed funds, daily | 0dtm_fed_funds (benchmark); SOFR proxy base | 1954→ |

Fetch pattern: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>`.
These come from the Federal Reserve H.15 release — the official secondary-market
bill rates, essentially never revised.

## ⚠️ Pre-2001 proxy — READ THIS for the 0–30 fund

The Treasury did not auction 4-week bills before **July 2001**, so no 1-month
series exists before **2001-07**, and July 2001 has a single daily quote
(2001-07-31) — below the 10-observation monthly minimum. The proxy therefore covers
**1969-12 → 2001-07** in the window (380 of the 682 rows). There the 4-week
*discount* rate is proxied as the 3-month discount minus the mean overlap
spread (month-average and month-end handled separately):

- mean 3M−4W discount spread: **avg 5.6 bp, eom 5.3 bp**
- proxy accuracy vs the real 4-week bill over the 2001-08+ overlap: **13.2 bp RMSE**

**What this means.** Pre-2001 the 0–30 fund is the *same 3-month rate signal*
run through genuine 0–30 conventions (shorter 1-month income window + 28-day
yield conversion). It is therefore legitimately **lower-yielding and more
responsive** than the 0–90 fund — but it carries little information
*independent* of it, because the real 1M–3M spread volatility (which swings
−35…+93 bp post-2001) is flattened to a constant 5.6 bp.

- Cumulative carry drag, Dec-1969 → Jun-2001: **0–30 earns ~−5.3%** vs 0–90.
- Month-to-month 0–30 vs 0–90 gap: pre-2001 **−159…+423 bp** (structural, on a
  proxied signal, largest during the 1980–81 rate rollercoaster); post-2001
  **−35…+93 bp** (fully observed).

**Do not** read month-to-month 0–30/0–90 divergences through 2001-07 as observed
market behaviour. From 2001-08 onward every point is a real 4-week bill.

## Validations

| Check | Result |
|---|---|
| discount→bond-equivalent conversion vs FRED `DGS3MO` (independent investment-basis 3-mo CMT), 541 mo | mean −0.9 bp, stdev 2.2 bp |
| single-tenor proxy for the bucket (3M vs 1M spread, 2001+) | avg 5.6 bp |
| full-period TR CAGR vs known long-run T-bill returns | 0–90 4.68%, 0–30 4.55% (in band) |

## Regenerate

```bash
scripts/rebuild.sh                      # all three steps below (or /rebuild in Claude Code)

python3 scripts/fetch_fred.py           # refresh FRED inputs in data/ (pure Python)
python3 scripts/build_mmf.py            # series CSVs (pure Python)
.venv/bin/python3 scripts/plot_mmf.py   # comparison charts (needs matplotlib)
```

Add a fund by appending `{key, tenor, max_dtm}` to `FUNDS` in the script.
