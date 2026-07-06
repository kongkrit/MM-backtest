# PROGRESS

Session handoff for this project. Written by `/wrapup`; auto-loaded into context at session start.

## What we did
- **Made the build window a single source of truth** in new `build_range.json` (repo root):
  `{ "start_month": 197001, "end_month": 202605 }` (inclusive `YYYYMM`). Removed every magic start/end
  date from the scripts.
- **Step 0 (data check):** confirmed enough data for 1970-01 → 2026-05. DTB3 (1954+) and DFF (1954+)
  have real data at both ends (≥20 obs/mo); DTB4WK (0–30) and SOFR (0dtm) use the **same existing proxy**
  before 2001-07 / 2018-04 — extending start from 1972 to 1970 just adds 24 fully-covered months.
- **`build_mmf.py`:** deleted `START_YM=197201`; now `START_YM, END_YM = load_build_range()`. Month filter
  is `START_YM <= m <= END_YM` (previously `>= START_YM` with **no end cap** → implicitly ran to the last
  full data month, 202606).
- **Removed the last magic date — `SPLICE_YM=200208`.** `tr_idx` now bases at **100 @ the build-window
  start** (`out[0]`), the same anchor as `price_idx` — both = 100 @ 197001. CAGRs unchanged (ratio-based);
  only the tr_idx *level* rescaled. External-override path now rebases to its own earliest month.
- **Proxy-transition markers kept** (`datetime(2001,7,1)`, `datetime(2018,4,1)` in `plot_mmf.py`) — these
  are real-world data-availability facts (DTB4WK / SOFR start), not magic build-range dates.
- **`plot_mmf.py`:** price-pane y-window is now **data-derived** (`price_window()`: 12% margin, floored at
  ±0.5 so flat cash NAV still reads flat-at-100; ticks on a 0.5 grid). Removed hardcoded
  `price_ylim`/`price_yticks`. Axis label is `=100 @ {x[0].year}` (renders "1970").
- **Docs updated** to match (README, MMF_SUMMARY, docs/mmf_methodology): 1972→1970, Jun-2026→May-2026,
  654→677 rows, tr_idx base "Aug-2002 splice"→"build-window start", proxied 0–30 count 378 of 677,
  carry-drag 1970→2001 ≈ **−5.2%** (was ~−4.3% over 1972→2001), CAGRs 0–90 **4.67%** / 0–30 **4.54%**.
  Added `build_range.json` to the README repo-layout table.

## Current state
- All four series rebuilt: **197001 → 202605, 677 rows each**; `tr_idx` = 100.00 @ 197001.
  tr end: 0–90 1316.39, 0–30 1226.84, 0dtm(SOFR) 1610.30, 0dtm_ff 1612.81.
  price range: 0–90 [98.98,101.00], 0–30 [99.67,100.33], cash flat 100.
- Charts regenerated with data-derived windows (no clipping): `mmf_30-90DTM_compare.png`,
  `mmf_0dtm_compare.png`.
- `output/`: latest coherent snapshot set `20260706_1303_*` (CSVs) + `20260706_1304_*` (PNGs); stale
  intermediate iteration snapshots removed.
- Both scripts compile; no magic date/window literals remain (only `build_range.json`, the real-world
  2001-07/2018-04 proxy markers, and `MIN_OBS=10`).
- Inputs `data/` unchanged: `DTB3`, `DTB4WK`, `DFF`, `SOFR` (+ legacy `TB3MS`, unused).
- LSEG/Datastream override hook (`data/lseg_<key>_tr.csv`) exists but unused (connector needs interactive OAuth).

## Next steps
- Monthly refresh: re-fetch FRED (`DTB3 DTB4WK DFF SOFR`), bump `end_month` in `build_range.json`,
  rerun `build_mmf.py` + `plot_mmf.py`.
- Optional regime stress check: decompose carry vs MtM through 1973-74, 1980-81, 2008, 2022 (history now
  starts 1970, so this covers the full early-70s runup).
- Wire a genuine LSEG TR index once authorized (or drop an export into `data/lseg_*_tr.csv`) — override
  now rebases to its own earliest month.
- Add more buckets (e.g. 0–180 DTM) via the `FUNDS` table.

## Open questions
- Keep or drop legacy `data/TB3MS.csv` (superseded by daily `DTB3`)?
- Do downstream consumers need the 0–30 series pre-2001 given the proxy caveat — or start it at 2001-07
  for relative-value work?
- Should `output/` snapshots keep accumulating in-repo, or move to gitignored build-history?
