# PROGRESS

Session handoff for this project. Written by `/wrapup`; auto-loaded into context at session start.

## What we did (2026-10-03)
- **Retired `end_month`.** `build_range.json` is now just `{ "start_month": 197001 }`. The end is computed:
  `load_build_range(today=None)` in `build_mmf.py` returns the **last complete calendar month before
  today** (run 2026-10-03 → 202609; January wraps to the prior December).
- **Coverage gate (fail loudly).** `require_coverage()` runs after the 4 inputs load, before any build or
  write. Each of `DTB3 DTB4WK DFF SOFR` must have ≥ `MIN_OBS` obs in END_YM **and** an observation dated
  after END_YM (proves the month-end value is posted). Otherwise it exits 1, names each short series with
  its last obs date, and writes nothing. `load_daily()` now returns `(monthly, last_obs_date)`.
- **New `scripts/fetch_fred.py`** (stdlib only). Full-history download of `DTB3 DTB4WK DFF SOFR` from
  `fredgraph.csv` (UA set, 60 s timeout, 3 attempts with backoff). **All-or-nothing**: validates all 4
  (header, ISO dates strictly rising, numeric-or-blank values, same first date, last date / row count
  never go backwards), then writes temp files and `os.replace`s them in. Reports
  `old_last -> new_last (+N rows, K revised)`. Writes FRED's exact format (LF, blank = missing), so
  `git diff data/` shows only real changes. Legacy `TB3MS` is not fetched.
- **Refreshed data and outputs through 202609.** Fetch: +66/+66/+92/+66 rows, 0 revisions, all inputs end
  2026-10-01. Rebuilt the 4 CSVs and 2 charts. 0–90 and fed funds were pure appends (+4 rows). 0–30 and
  0dtm changed on every row (max 0.056 bp coupon, 0.017% tr_idx) because the proxy overlap-mean spreads
  shifted with 4 more months, and tr_idx compounds from 1970. This is expected.
- **Fixed a pre-existing off-by-one: July 2001 is proxied.** DTB4WK has one Jul-2001 quote (2001-07-31,
  below `MIN_OBS`), so the 0–30 proxy covers **1970-01 → 2001-07 (379 of 681 months)** and real data starts
  **2001-08**. Updated docs, the `build_mmf.py` docstring, and `plot_mmf.py` (split marker
  `datetime(2001, 8, 1)`, caption "proxied through Jul-2001").
- **Docs:** README / MMF_SUMMARY / methodology describe the end-month rule instead of a fixed date. Stats
  are labelled **"as of the Sep-2026 build"**. Every figure was re-derived after first reproducing the old
  value with the same method (carry drag = tr_idx ratio through 2001-06; gaps = 0–90 − 0–30 annual coupon;
  DGS3MO check = month-avg BEY vs DGS3MO, fetched to scratch only). Changes: RMSE 13.3→13.2 bp, pre-2001
  gap max +422→+423 bp, DGS3MO 538→541 mo, cash CAGRs 5.05%→5.04%.
- **New `rebuild` command.** `scripts/rebuild.sh` (executable): venv check first, then `[1/3] fetch →
  [2/3] build → [3/3] plot`, `set -euo pipefail` plus an ERR trap that names the failed stage.
  `.claude/commands/rebuild.md` (`/rebuild`) runs it and summarizes the result. It never edits docs or
  commits. README, methodology and CLAUDE.md ("Build and run" section) document both.
- Deleted the in-between step-2 snapshot set `output/20261003_1125_*`.
- **Decided: `scripts/rebuild.sh` stays out of every allow list.** It runs prompt-free only inside
  `/rebuild` (command `allowed-tools`); anywhere else it prompts. Recorded in CLAUDE.md.
- **Rewrote CLAUDE.md for MM-backtest** (was template boilerplate). It now has a project description, a
  full layout, Build and run (with the permission rule), Data and modelling rules (no magic dates, proxy
  spans, stdlib-only fetch/build, "as of" doc stats), and an accurate venv command (`pip install matplotlib`).
  Dropped two stale template lines: `requirements.txt` (doesn't exist) and a README QEMU/buildx
  pointer (no such section).
- **Moved the proxy-transition note to the bottom of the price pane** (same x, at the split line).
  `plot_mmf.py`: `note_y = ylo + 3%`, `va="bottom"`. On the 30–90 chart it had overlapped the 0–90 line's
  101.0 plateau (~2009–2015). It applies to both charts (shared `build_fig`). Re-rendered the PNGs and
  deleted the superseded `output/20261003_1131_*.png`.

## Current state
- **Nothing committed yet.** Working tree: modified scripts/docs/data/outputs. New, untracked:
  `scripts/fetch_fred.py`, `scripts/rebuild.sh`, `.claude/commands/rebuild.md`, `output/20261003_1131_*.csv`,
  `output/20261003_1213_*.png`.
- All four series: **197001 → 202609, 681 rows each**; `tr_idx` = 100.000000 @ 197001.
  tr end / CAGR: 0–90 1332.35 / 4.67%, 0–30 1241.84 / 4.54%, 0dtm (SOFR) 1630.43 / 5.04%,
  0dtm_ff 1632.84 / 5.04%. Price range: 0–90 [98.98,101.00], 0–30 [99.67,100.33], cash flat 100.
- Proxy spreads (Sep-2026 build): 3M−4W avg 5.6 / eom 5.3 bp, RMSE 13.2 bp. Fed funds − SOFR 0.3 bp.
- `output/` latest coherent set: `20261003_1131_*` CSVs (made by `/rebuild`; byte-identical to the step-2
  build) + `20261003_1213_*` PNGs (bottom-placed note). Older sets `20260704_1356_*` and
  `20260706_1303/1304_*` kept.
- Verified:
  - end-month rule for 4 dates incl. the January wrap;
  - gate fails on stale data and passes once data covers the month;
  - fetcher refuses bad downloads and dead-network runs, and leaves `data/` untouched (checksummed);
  - fetcher rerun is idempotent;
  - `rebuild.sh` stops at the venv check and at a failed fetch (scratch copy), and the real `/rebuild`
    run passed.
- `data/TB3MS.csv` is now stale (ends 2026-06) since the fetcher skips it. It is unused by the build.
- LSEG/Datastream override hook (`data/lseg_<key>_tr.csv`) exists but unused (connector needs interactive OAuth).

## Next steps
- Commit this session's work (scripts, docs, data, outputs, `/rebuild`).
- Monthly refresh is now just `scripts/rebuild.sh` (or `/rebuild`) any time after FRED posts the prior
  month's last day. On the 1st–2nd of a month the gate may fail; rerun a day later. Doc stats stay
  "as of Sep-2026" until refreshed by hand.
- Optional regime stress check: decompose carry vs MtM through 1973-74, 1980-81, 2008, 2022.
- Wire a genuine LSEG TR index once authorized (or drop an export into `data/lseg_*_tr.csv`).
- Add more buckets (e.g. 0–180 DTM) via the `FUNDS` table (and the fetcher's `SERIES` if new inputs).

## Open questions
- Keep or drop legacy `data/TB3MS.csv` (superseded by daily `DTB3`, no longer refreshed)?
- Do downstream consumers need the 0–30 series pre-2001 given the proxy caveat — or start it at 2001-08
  for relative-value work?
- Should `output/` snapshots keep accumulating in-repo (every `/rebuild` adds 6 files), or move to
  gitignored build-history?
