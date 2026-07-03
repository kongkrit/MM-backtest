# PROGRESS

Session handoff for this project. Written by `/wrapup`; auto-loaded into context at session start.

## What we did
- Built synthetic **0% TER Treasury-bill money-market fund** series, monthly **Jan-1972 → Jun-2026** (654 rows):
  - `mmf_0_90dtm.csv` (0–90 DTM, 13-week bills, ~45d avg life)
  - `mmf_0_30dtm.csv` (0–30 DTM, 4-week bills, ~15d avg life)
- Model: FRED **daily** bill discount rates → bond-equivalent yield; income = trailing ladder-carry average (lags market); price = month-end mark-to-market on avg-life duration. Two share classes off one book: `price_idx` (distributing, =100 @1972), `tr_idx` (accumulating, =100 @Aug-2002 splice); linked by `tr_ret = price_ret + coupon`.
- **0–30 pre-2001-07 is a documented proxy** (4-week bills didn't exist before Jul-2001): 4wk discount = 3mo − mean spread (5.6bp), ~13.3bp RMSE. Option A chosen: full history w/ proxy; caution surfaced to consumers.
- Validations: discount→BEY vs FRED `DGS3MO` (mean −0.9bp, stdev 2.2bp); 1M–3M spread 5.6bp; CAGR 0–90 **4.63%**, 0–30 **4.51%** (in band vs known T-bill returns).
- Layout: single builder `scripts/build_mmf.py`; canonical CSVs at **repo root**; `output/` = versioned build-history snapshots (`mmf_<fund>_<vintage>.csv`). CSVs emit **LF** (repo convention).
- Docs: `MMF_SUMMARY.md` (consumer WHAT + 0–30 caution), `docs/mmf_methodology.md` (full HOW).
- Config: allowed `curl` in `.claude/settings.json`. Committed as `69013c8` (identity kongkrit <kongkrit@gmail.com>).

## Current state
- Working tree clean; all deliverables committed on `main`.
- Inputs in `data/`: `DTB3.csv`, `DTB4WK.csv`, `DFF.csv` (+ legacy `TB3MS.csv`, unused by current builder).
- LSEG/Datastream override hook exists (`data/lseg_<key>_tr.csv` auto-overrides `tr_idx`) but is **unused** — the `lseg` MCP connector needs interactive OAuth and was unreachable this session.

## Next steps
- Optional regime stress check: decompose carry vs MtM through 1973-74, 1980-81, 2008, 2022.
- Wire a genuine LSEG 0–90 TR index once the connector is authorized (or drop an export into `data/lseg_*_tr.csv`).
- Monthly refresh: re-fetch FRED series, rerun `scripts/build_mmf.py` (new vintage snapshot auto-created).
- Add more buckets (e.g. 0–180 DTM) by appending to the `FUNDS` table in the builder.

## Open questions
- Keep or drop legacy `data/TB3MS.csv` (superseded by daily `DTB3`)?
- Do downstream consumers need the 0–30 series pre-2001 at all, given the proxy caveat — or start it at 2001-07 for relative-value work?
