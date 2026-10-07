# MMF series — consumer summary

Synthetic **0% TER** (no fee drag) money-market fund series: two rolling **T-bill**
ladders and two **overnight-cash** funds. Monthly, from **Jan 1970** (`start_month`
in `build_range.json` at the repo root, the single source of truth) through the
**last complete calendar month before the build date**; every fund has the same
row count.

## Files

Read these from the **repo root** — they are always the latest series:

| File | What it is |
|---|---|
| `mmf_0_90dtm.csv` | Rolling **0–90 DTM** T-bills (13-week bills, ~45-day average life). The general "T-bill cash" proxy. |
| `mmf_0_30dtm.csv` | Rolling **0–30 DTM** T-bills (4-week bills, ~15-day average life). Shorter, steadier. |
| `mmf_0dtm.csv` | **Canonical overnight cash** — secured Treasury repo (**SOFR**). Flat NAV. **This is the holdable one** (a government money-market fund tracks it). |
| `mmf_0dtm_fed_funds.csv` | Overnight **fed funds** (unsecured, interbank). **Benchmark only** — not directly holdable at retail. |

All four share the same columns and date grid, so they align row-for-row.

## Which cash fund to use

Use **`mmf_0dtm`** (SOFR). It is the secured overnight Treasury-repo rate — what a
government / Treasury money-market fund (VMFXX, SPAXX, VUSXX, SGOV-style) actually
earns, i.e. the cash you can buy and hold in a brokerage account.
`mmf_0dtm_fed_funds` is the *unsecured interbank* rate: a reference benchmark you
cannot directly hold. The two differ by only **~0.3 bp** on average (see the
overnight note below), so this choice is about correctness, not magnitude.

## Columns

| Column | Meaning |
|---|---|
| `yyyymm` | Month key, integer (e.g. `197001` = Jan 1970). |
| `price_idx` | Price/NAV index of the **distributing** class (coupons paid out). **= 100 in the 197001 row** (see **First row** below). Bills wiggle with yields; the cash funds are **flat 100** (zero duration). |
| `coupon_rate_monthly` | Monthly coupon as a fraction of NAV (decimal) — cash a distributing holder receives for that month. |
| `coupon_rate_annual` | `coupon_rate_monthly × 12` (simple annualized, not compounded). |
| `tr_idx` | Total-return index — **accumulating** (coupons reinvested). **= 100 in the 197001 row** (see **First row** below). |

**Timing.** Row `YYYYMM` is *as of month-end*. `price_idx` is the NAV mark at the
last trading day; `coupon_rate_*` is the income earned over the month and **paid at
month-end**. So the monthly total return booked at month-end is
`coupon_rate_monthly + price change = tr_idx[m] / tr_idx[m−1] − 1` — no look-ahead.
(The coupon *rate* is the month-average yield ÷12; the end-of-month yield is used
only for the price mark.)

**First row.** `197001` is the starting point: both indices are 100 there, and they
don't include January 1970's return. `price_idx` is also 100 at the *beginning* of
January: the build sets the first month's price change to 0, so the NAV starts and
ends January at 100. Read `tr_idx` = 100 as the level at the end of January
(start of February), so the first monthly return is `tr_idx[197002] / 100 − 1`
(February 1970). The 197001 `coupon_rate_*` values still show January's coupon,
but it isn't compounded into `tr_idx`.

For **0–90 DTM only**, the first two coupons average fewer months of bills than
the model's 3, because the build starts at 197001. The 197001 coupon uses only January's
yield (0.00678 vs 0.00658 with the full 3-month average). The 197002 coupon uses
January–February (0.00646 vs 0.00655), and it *is* in `tr_idx`, so every later 0–90
`tr_idx` is about 0.009% low. The 0–30 and overnight funds average only the
current month, so they're unaffected.

## At a glance

*As of the Sep-2026 build (197001 → 202609, 681 rows; CAGR over the 680 months of
return, Feb-1970 on).*

| Fund | tr_idx 1970 → 2026 | TR CAGR | price_idx |
|---|---|---|---|
| 0–90 DTM (bills) | 100.00 → 1332.35 | 4.68% | 98.98 – 101.00 |
| 0–30 DTM (bills) | 100.00 → 1241.84 | 4.55% | 99.67 – 100.33 |
| **0DTM cash — SOFR** (`mmf_0dtm`) | 100.00 → 1630.43 | **5.05%** | flat 100 |
| 0DTM fed funds (benchmark) | 100.00 → 1632.84 | 5.05% | flat 100 |

Among the **bills**, shorter = a bit less yield and a steadier NAV. The
**overnight-cash** funds yield *more* than the bills (see the note below) — the
T-bill safety premium, not an error.

## Charts

Two comparison charts (repo root), each three shared-axis panes — price index
(semilog), annual coupon rate, monthly coupon delta:

- `mmf_30-90DTM_compare.png` — 0–30 vs 0–90 DTM bills
- `mmf_0dtm_compare.png` — fed funds vs SOFR overnight cash (flat NAV; the delta pane shows the Sept-2019 repo spike)

`output/` holds **timestamped build-history snapshots** (`YYYYMMDD_HHMM_mmf_<fund>.csv`
and `..._*_compare.png`), stamped when the build ran. For current data, always read
the files at the repo root.

## ⚠️ Caution 1 — the 0–30 DTM series through July 2001

4-week Treasury bills did not exist before the Treasury began auctioning them in
**July 2001**. For **1970 → July 2001** the 0–30 series is **modeled from 3-month
bill data**, not observed 1-month bills (July 2001 itself has a single 4-week quote,
on the 31st — too few days for a monthly average).

- **From 2001-08 onward:** fully real — use freely, including the 0–30 vs 0–90 difference.
- **Through 2001-07:** the 0–30 fund is the 0–90 rate signal re-expressed with
  shorter-maturity behavior. Its **level and long-run return are reliable**, but its
  **month-to-month difference from 0–90 is a modeling artifact** (the true
  1M-vs-3M spread is assumed constant). Don't build 0–30-vs-0–90 spread/relative-value
  signals on that window; use 0–90 alone there, or start at 2001-08.

The 0–90 fund has **no such caveat** — real 3-month bill data across the full 1970+ history.

## ⚠️ Caution 2 — the overnight "cash" funds

`mmf_0dtm` (SOFR) and `mmf_0dtm_fed_funds` are overnight cash with a **flat NAV
(=100)** — zero duration, so all return is coupon.

- **They yield *above* the bills** (CAGR ~5.0% vs 4.5–4.7%). That's the T-bill
  safety/liquidity premium — Treasuries yield less than equally-short cash — not a
  bug. Overnight cash is **not** a lower-yielding "shorter tier" than the bills.
- **SOFR ≈ fed funds:** mean gap **+0.3 bp** over 2018-04+ (their real overlap); the
  real signal is repo-stress months — e.g. **Sept-2019, SOFR +23 bp over fed funds**.
- **`mmf_0dtm` (SOFR) is real only from 2018-04.** Before that it is proxied as fed
  funds minus the ~0 bp spread, so pre-2018 it ≈ `mmf_0dtm_fed_funds`. Don't read
  pre-2018 secured-vs-unsecured differences.

---
Full model details: `docs/mmf_methodology.md`.
