# PROGRESS

Session handoff for this project. Written by `/wrapup`; auto-loaded into context at session start.

## What we did (2026-10-03)
- **Retired `end_month`.** `build_range.json` holds only `start_month` (now 196912; see 2026-10-07). `load_build_range()`
  computes the end as the **last complete calendar month before today**: the day before this month's 1st
  (run 2026-10-03 → 202609; January → prior December).
- **Coverage gate (fail loudly), inside `load_daily()`.** Each input must have ≥ `MIN_OBS` quotes in END_YM
  **and** a quote dated after it. FRED posts each day about a business day late, so this proves the month
  end is in. Otherwise the build exits naming the file and writes nothing.
- **New `scripts/fetch_fred.py`** (stdlib, ~40 lines). It downloads the full history of each `SERIES` and
  writes nothing unless every download starts with `observation_date,<ID>` and has ≥ the current row count.
  FRED's text is saved as received (byte-identical to our files). Prints `old_last -> new_last (+N rows)`.
  Revisions show in `git diff data/`.
- **Refreshed data and outputs through 202609.** Fetch: +66/+66/+92/+66 rows, no revisions, inputs end
  2026-10-01. 0–90 and fed funds were pure appends (+4 rows). 0–30 and 0dtm moved slightly on every row
  (max 0.056 bp coupon, 0.017% tr_idx): the proxy overlap-mean spreads shifted with 4 more months, and
  tr_idx compounds from 1970.
- **Fixed a pre-existing off-by-one: July 2001 is proxied.** DTB4WK has one Jul-2001 quote (below
  `MIN_OBS`), so the 0–30 proxy covers **1970-01 → 2001-07 (379 of 681 months)** and real data starts
  **2001-08**. Docs, chart split marker and caption updated.
- **Docs:** describe the end-month rule. Stats are labelled **"as of the Sep-2026 build"** and were
  re-derived after first reproducing the old values (carry drag = tr_idx ratio through 2001-06; gaps =
  0–90 − 0–30 annual coupon; DGS3MO check = month-avg yield vs DGS3MO, fetched to scratch only).
- **New `rebuild` command.** `scripts/rebuild.sh` runs `set -e` and `== [1/3] fetch`, `[2/3] build`,
  `[3/3] plot`; the last `==` line names a failed step. `/rebuild` (`.claude/commands/rebuild.md`) runs it
  and summarizes; it never edits docs or commits. **Decided:** `rebuild.sh` stays out of every allow
  list, so it only runs prompt-free inside `/rebuild` (recorded in CLAUDE.md).
- **CLAUDE.md** rewritten for MM-backtest. It now includes your verbatim **Code principles** (simple,
  minimal, easy to understand, DRY) and **How to explain things** sections.
- **Chart:** the proxy-transition note moved to the bottom of the price pane (it overlapped the 0–90
  line's 2009–2015 plateau).
- **Simplified the whole codebase to the code principles** (scripts 653 → ~370 lines). Outputs verified
  **byte-identical** (CSVs) and **pixel-identical** (PNGs).
  - `build_mmf.py` is the single source of `ROOT/DATA/OUTD`, `STAMP` and `SERIES`; the fetcher and plotter
    import them.
  - The two near-duplicate proxy functions became one `proxy_fill(base, real, tenor)`.
  - The 75-line docstring was cut to a summary that points to the methodology.
  - `load_daily()` collects quotes per month in a list.
  - Removed the `DAYS_*` constants, the `today=` test hook and `require_coverage()`.
  - Plot titles are styled once in a loop.
  - The fetcher lost its retries, custom User-Agent, row checks, revision count and temp files.
    `rebuild.sh` lost its venv check and ERR trap.
  - The build's proxy lines now count proxied months **inside the window** (379 / 579), not back to 1954.
- **Deleted dead code/data:** the unused LSEG override hook (`load_override`, docs sections) and
  `data/TB3MS.csv`.
- Deleted in-between `output/` snapshots, keeping one coherent set per state.

## What we did (2026-10-07)
- **Real 196912 base row for downstream** (who flagged `mmf_0_90dtm.csv` in particular).
  - `start_month` → **196912**. Both indices are 100 there (end of Dec 1969), so January 1970 now has a
    real return.
  - `build_fund()` runs each fund over **all** FRED history (from 1954) before cutting the window, then
    rebases both indices at the first row. This removed the 0–90 short-ladder warm-up: 197001/197002
    coupons were 0.00678/0.00646 (1–2 months averaged), now 0.00658/0.00655 (full 3 months), and later
    0–90 `tr_idx` was ~0.009% low.
  - Verified:
    - the 196912 0–90 coupon recomputed from raw DTB3 matches exactly (0.07595964);
    - coupons after the warm-up are unchanged;
    - month-to-month `tr_idx` returns are unchanged to ≤ 1.3e-8 (CSV rounding).
  - The chart's axis label now reads "=100 @ Dec 1969". The docs' "First row" note was rewritten, the
    warm-up caveat removed, and the stats refreshed.

## Current state
- Everything is committed and pushed to `origin/main` (the simplification pass is `baf1ba9`). Cleanup is
  done; downstream work consuming the root CSVs has started. It should re-read whole files after each
  rebuild, because the proxied 0–30 and SOFR history shifts slightly as the overlap spreads re-estimate.
- All four series: **196912 → 202609, 682 rows each**. Both indices = 100 @ 196912 (the base row);
  681 months of return from Jan 1970.
  tr end / CAGR: 0–90 1341.51 / 4.68%, 0–30 1250.16 / 4.55%, 0dtm (SOFR) 1642.80 / 5.06%,
  0dtm_ff 1645.23 / 5.06%. Price range: 0–90 [99.00,101.02], 0–30 [99.68,100.33], cash flat 100.
- Proxies (Sep-2026 build): 3M−4W spread avg 5.6 / eom 5.3 bp, RMSE 13.2 bp. Fed funds − SOFR 0.3 bp.
  0–30 proxied for 380 window rows (through 2001-07), SOFR for 580 (through 2018-03).
- `output/` latest set: `20261007_1839_*` (196912 base). Older sets kept: `20261003_1131/1213_*`
  (197001 base), `20260704_1356_*`, `20260706_1303/1304_*`.
- Verified after simplifying:
  - the end-month rule (incl. the January wrap);
  - the gate exits for 202610 and loads for 202609;
  - a dead-network fetch exits 1 with `data/` unchanged (checksummed);
  - the full `rebuild.sh` passes with identical outputs.

## Next steps
- Monthly refresh is `scripts/rebuild.sh` (or `/rebuild`) any time after FRED posts the prior month's
  last day. On the 1st–2nd of a month the gate may stop it; rerun a day later. Doc stats stay
  "as of Sep-2026" until refreshed by hand.
- Optional regime stress check: decompose carry vs MtM through 1973-74, 1980-81, 2008, 2022.
- Add more buckets (e.g. 0–180 DTM) via the `FUNDS` table (and `SERIES` if they need new inputs).

## Open questions
- Do downstream consumers need the 0–30 series pre-2001 given the proxy caveat — or start it at 2001-08
  for relative-value work?
- Should `output/` snapshots keep accumulating in-repo (every `/rebuild` adds 6 files), or move to
  gitignored build-history?
