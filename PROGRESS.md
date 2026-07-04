# PROGRESS

Session handoff for this project. Written by `/wrapup`; auto-loaded into context at session start.

## What we did
- **Four** synthetic **0% TER** money-market fund series, monthly **Jan-1972 → Jun-2026** (654 rows):
  - `mmf_0_90dtm.csv` — rolls 13-week bills (~45d avg life)
  - `mmf_0_30dtm.csv` — rolls 4-week bills (~15d avg life)
  - `mmf_0dtm.csv` — **canonical overnight cash = secured Treasury repo (SOFR)**; flat NAV; the *holdable* one (a government MMF tracks it)
  - `mmf_0dtm_fed_funds.csv` — effective fed funds (unsecured interbank); **benchmark only**; flat NAV
- Bill model: FRED **daily** discount → bond-equivalent yield; income = trailing ladder-carry avg; price = month-end MtM on avg-life duration. Two share classes: `price_idx` (distributing, =100 @1972), `tr_idx` (accumulating, =100 @Aug-2002); `tr_ret = price_ret + coupon`.
- Cash model: overnight add-on rate at tenor 1 (→ ×365/360 conversion), `max_dtm 0` → zero duration → flat NAV=100. SOFR real **2018-04+**, proxied before as fed funds − mean spread (**~0.3 bp**).
- Timing (confirmed to user): row `YYYYMM` is **as-of month-end**; `price_idx` = last-trading-day mark; coupon = income over the month **paid at month-end** (rate = month-avg yield ÷12); no look-ahead.
- Key findings: cash yields **above** the bills (~5.0% vs 4.5–4.6%) = T-bill safety premium; SOFR ≈ fed funds (+0.3 bp; **Sept-2019 repo spike +23 bp**); 0–90 price swings **3.01×** wider than 0–30 (= duration ratio 45/15).
- 0–30 **pre-2001-07 proxied** (no 4-week bills before Jul-2001; ~13.3 bp RMSE); documented caution.
- Charts (`scripts/plot_mmf.py`, matplotlib in `.venv`): two 3-pane shared-x figures — `mmf_30-90DTM_compare.png` (bills) and `mmf_0dtm_compare.png` (fed funds vs SOFR). (Renamed from the single `mmf_chart.png`.)
- `output/` snapshots timestamped `YYYYMMDD_HHMM_*` (stamp fetched right before writing).
- Validations: discount→BEY vs FRED `DGS3MO` (mean −0.9 bp); 1M–3M spread 5.6 bp; CAGR 0–90 4.63%, 0–30 4.51%.
- Docs rewritten/updated: `README.md`, `MMF_SUMMARY.md` (SOFR marked canonical cash), `docs/mmf_methodology.md`. CSVs emit **LF**. Config: allowed `curl`, `head`, `cd`.

## Current state
- Canonical latest at repo root: `mmf_0_90dtm.csv`, `mmf_0_30dtm.csv`, `mmf_0dtm.csv` (SOFR), `mmf_0dtm_fed_funds.csv`; charts `mmf_30-90DTM_compare.png`, `mmf_0dtm_compare.png`.
- `output/`: coherent timestamped snapshot set (latest `20260704_1356_*`).
- Inputs `data/`: `DTB3`, `DTB4WK`, `DFF`, `SOFR` (+ legacy `TB3MS`, unused).
- Scripts: `build_mmf.py` (pure Python, timestamped output), `plot_mmf.py` (matplotlib/`.venv`, one parameterized renderer → both charts).
- All the above committed by this wrapup and pushed to `origin/main`.
- LSEG/Datastream override hook (`data/lseg_<key>_tr.csv`) exists but unused (connector needs interactive OAuth).

## Next steps
- Optional regime stress check: decompose carry vs MtM through 1973-74, 1980-81, 2008, 2022.
- Wire a genuine LSEG TR index once authorized (or drop an export into `data/lseg_*_tr.csv`).
- Monthly refresh: re-fetch FRED (`DTB3 DTB4WK DFF SOFR`), rerun `build_mmf.py` + `plot_mmf.py`.
- Add more buckets (e.g. 0–180 DTM) via the `FUNDS` table.

## Open questions
- Keep or drop legacy `data/TB3MS.csv` (superseded by daily `DTB3`)?
- Do downstream consumers need the 0–30 series pre-2001 given the proxy caveat — or start it at 2001-07 for relative-value work?
