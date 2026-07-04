# MMF series — consumer summary

Two synthetic **0% TER** (no fee drag) money-market fund series holding
short-dated U.S. Treasury bills. Monthly, **Jan 1972 → Jun 2026** (654 rows
each; extends as new months are added).

## Files

Read these two from the **repo root** — they are always the latest series:

| File | What it is |
|---|---|
| `mmf_0_90dtm.csv` | Fund holding **0–90 DTM** T-bills (13-week bills, ~45-day average life). The general "T-bill cash" proxy. |
| `mmf_0_30dtm.csv` | Fund holding **0–30 DTM** T-bills (4-week bills, ~15-day average life). Shorter, lower-yielding, less rate-sensitive. |

Both files share the same columns and date grid, so they align row-for-row.

A comparison chart is at `mmf_chart.png` (repo root): three shared-axis panes —
price index (semilog), annual coupon rate, and the monthly coupon delta
(0–90 − 0–30, bp of NAV) — for 0–30 vs 0–90.

`output/` holds **timestamped build-history snapshots** named
`YYYYMMDD_HHMM_mmf_<fund>.csv` (and `..._mmf_chart.png`), stamped when the build
ran. Use these only to reproduce or compare past builds — for current data,
always read the two files at the repo root.

## Columns

| Column | Meaning |
|---|---|
| `yyyymm` | Month key, integer (e.g. `200208` = Aug 2002). |
| `price_idx` | Price/NAV index — the mark of a **distributing** fund (coupons paid out). **= 100 at Jan-1972.** Cyclical: rises when yields fall, falls when they rise. Stays near 100 (tiny duration). |
| `coupon_rate_monthly` | Monthly coupon as a fraction of NAV (decimal) — cash a distributing holder receives that month. Smoothed, not lumpy. |
| `coupon_rate_annual` | `coupon_rate_monthly × 12` (simple annualized, not compounded). |
| `tr_idx` | Total-return index — **accumulating** (coupons reinvested). **= 100 at the Aug-2002 splice.** Compounds steadily upward. |

`price_idx` and `tr_idx` are two share classes of the **same** portfolio:
total return = price change + coupon.

## At a glance

| | 0–90 DTM | 0–30 DTM |
|---|---|---|
| tr_idx Jan-1972 → Jun-2026 | 12.82 → 150.75 | 13.44 → 148.75 |
| Full-period total-return CAGR | 4.63% | 4.51% |
| price_idx range | 98.41 – 100.41 | 99.49 – 100.14 |

The 0–30 fund earns a bit less (shorter, safer paper) and its NAV barely moves.

## ⚠️ Caution — the 0–30 DTM series before July 2001

4-week Treasury bills did not exist before the Treasury began auctioning them
in **July 2001**. For **1972 → June 2001** the 0–30 series is therefore
**modeled from 3-month bill data**, not built from observed 1-month bills.

What that means for you:

- **From 2001-07 onward:** fully real — use freely, including the 0–30 vs 0–90
  difference.
- **Before 2001-07:** the 0–30 fund is essentially the 0–90 rate signal
  re-expressed with shorter-maturity behavior. Its **level and long-run return
  are reliable** (it correctly earns modestly less than 0–90). But its
  **month-to-month difference from the 0–90 fund is a modeling artifact**, not
  observed market data — the true 1-month-vs-3-month spread is assumed constant.
- **Do not** build spread trades, relative-value signals, or "0–30 minus 0–90"
  analytics on the **pre-2001-07** window. Use the 0–90 fund alone there, or
  start such work at 2001-07.

The 0–90 fund has **no such caveat** — it is real 3-month bill data across the
full 1972+ history.

---
Full model details: `docs/mmf_methodology.md`.
