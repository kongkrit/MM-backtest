# PROGRESS

Session handoff for this project. Written by `/wrapup`; auto-loaded into context at session start.

## What we did
- Built two synthetic **0% TER, rolling Treasury-bill fund** series, monthly **Jan-1972 → Jun-2026** (654 rows):
  - `mmf_0_90dtm.csv` (rolls 13-week bills, ~45d avg life)
  - `mmf_0_30dtm.csv` (rolls 4-week bills, ~15d avg life)
- Model: FRED **daily** bill discount rates → bond-equivalent yield; income = trailing ladder-carry average (lags market); price = month-end mark-to-market on avg-life duration. Two share classes off one book: `price_idx` (distributing, =100 @1972), `tr_idx` (accumulating, =100 @Aug-2002 splice); linked by `tr_ret = price_ret + coupon`.
- **0–30 pre-2001-07 is a documented proxy** (4-week bills didn't exist before Jul-2001): 4wk discount = 3mo − mean spread (5.6bp), ~13.3bp RMSE. Option A: full history w/ proxy; caution surfaced to consumers.
- **Chart:** `scripts/plot_mmf.py` → `mmf_chart.png`, a 3-pane shared-x figure — price index (semilog), annual coupon rate (linear), and monthly coupon delta 0–90 − 0–30 (bp of NAV, diverging blue/red). matplotlib in `.venv` (gitignored); core builder stays dependency-free.
- **Timestamped outputs:** `output/` snapshots now `YYYYMMDD_HHMM_mmf*.*` (CSVs + chart), stamp fetched right before writing; replaced the old vintage naming (old `*_202606.csv` snapshots removed).
- Sanity-checks (answered user): funds are near-identical in yield (post-2001 coupon gap mean **6.7 bp** — front bill curve is flat) but 0–90 price swings **3.01×** wider (= duration ratio 45/15); both correct, no bug.
- Validations: discount→BEY vs FRED `DGS3MO` (mean −0.9bp); 1M–3M spread 5.6bp; CAGR 0–90 **4.63%**, 0–30 **4.51%**.
- Docs: `README.md` (project overview + embedded chart), `MMF_SUMMARY.md` (consumer WHAT + 0–30 caution), `docs/mmf_methodology.md` (full HOW). CSVs emit **LF** (`.gitattributes`).
- Config: allowed `curl`, `head`, `cd` in `.claude/settings.json`.

## Current state
- Canonical latest at repo root: `mmf_0_90dtm.csv`, `mmf_0_30dtm.csv`, `mmf_chart.png`.
- `output/`: coherent timestamped snapshot set (latest `20260704_1013_*`).
- Scripts: `build_mmf.py` (pure Python, timestamped output), `plot_mmf.py` (matplotlib/`.venv`).
- Pushed through `e32dd7f` (README) on `origin/main`; this session's chart + timestamped-output work committed by this wrapup but **not yet pushed**.
- LSEG/Datastream override hook (`data/lseg_<key>_tr.csv`) exists but unused (connector needs interactive OAuth).

## Next steps
- `git push origin main` to publish this wrapup commit.
- Decide the coupon-delta basis: currently **monthly** coupon (bp of NAV); confirm vs annualized (12×) preference.
- Optional regime stress check: decompose carry vs MtM through 1973-74, 1980-81, 2008, 2022.
- Wire a genuine LSEG TR index once authorized (or drop an export into `data/lseg_*_tr.csv`).
- Monthly refresh: re-fetch FRED, rerun `build_mmf.py` + `plot_mmf.py` (new timestamped snapshots auto-created).
- Add more buckets (e.g. 0–180 DTM) via the `FUNDS` table.

## Open questions
- Keep or drop legacy `data/TB3MS.csv` (superseded by daily `DTB3`)?
- Do downstream consumers need the 0–30 series pre-2001 given the proxy caveat — or start it at 2001-07 for relative-value work?
