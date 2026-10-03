# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

**MM-backtest** builds synthetic monthly **price and total-return series for 0% TER money-market funds** —
two rolling T-bill ladders (0–90 and 0–30 DTM) and two overnight-cash funds (SOFR, canonical; fed funds,
benchmark) — from public FRED daily rates, Jan 1970 through the last complete month. Consumers read the
canonical CSVs at the repo root; [MMF_SUMMARY.md](MMF_SUMMARY.md) explains *what* they are,
[docs/mmf_methodology.md](docs/mmf_methodology.md) explains *how*.

## Repository layout

- `mmf_0_90dtm.csv`, `mmf_0_30dtm.csv`, `mmf_0dtm.csv`, `mmf_0dtm_fed_funds.csv` — canonical latest series
  (identical schema: `yyyymm, price_idx, coupon_rate_monthly, coupon_rate_annual, tr_idx`; both indices
  = 100 @ the build-window start).
- `mmf_30-90DTM_compare.png`, `mmf_0dtm_compare.png` — canonical latest 3-pane comparison charts.
- `build_range.json` — `start_month` only (single source of truth for the start; there is no end setting).
- `scripts/fetch_fred.py` — refreshes `data/` from FRED (all-or-nothing, validated; stdlib only).
- `scripts/build_mmf.py` — series builder (stdlib only); `FUNDS` table defines the buckets.
- `scripts/plot_mmf.py` — chart renderer (matplotlib, from `.venv`).
- `scripts/rebuild.sh` — fetch → build → plot in one go.
- `data/` — raw FRED daily inputs `DTB3`, `DTB4WK`, `DFF`, `SOFR` (legacy `TB3MS` is unused and not refreshed).
- `output/` — timestamped build-history snapshots `YYYYMMDD_HHMM_*` (every build adds 6 files).
- `README.md`, `MMF_SUMMARY.md`, `docs/mmf_methodology.md` — overview, consumer summary, methodology.
- `.claude/settings.json` — committed Claude Code settings (`model: opus`, `effortLevel: xhigh`, permissions,
  `SessionStart` hook). Personal overrides go in `.claude/settings.local.json` (gitignored).
- `.claude/commands/wrapup.md` — `/wrapup`: writes the session handoff to `PROGRESS.md`, then stages and commits.
- `.claude/commands/rebuild.md` — `/rebuild`: runs `scripts/rebuild.sh` and summarizes the result (no doc edits, no commit).
- `PROGRESS.md` — session handoff; printed into context at session start by the `SessionStart` hook.
- `.gitignore`, `.gitattributes`, `LICENSE` — repo hygiene (see Conventions).

## Build and run

- `scripts/rebuild.sh` (or `/rebuild`) — fetch FRED → build series → render charts, through the last complete
  calendar month before today. Stops at the first failing stage.
- Stages individually: `python3 scripts/fetch_fred.py`, `python3 scripts/build_mmf.py`,
  `.venv/bin/python3 scripts/plot_mmf.py`.
- The builder **fails, writing nothing**, if any input doesn't fully cover the end month (it needs an
  observation dated after it). On the 1st–2nd of a month that usually means FRED hasn't posted yet — rerun
  later; never work around it by editing data, code, or `build_range.json`.
- **Permissions:** `scripts/rebuild.sh` is deliberately **not** in the `.claude/settings.json` allow list.
  It runs without a prompt only inside `/rebuild` (via that command's `allowed-tools`); anywhere else it must
  prompt. Do not add it to the allow list.
- No test suite. Verify a build by its printed summary (window, rows, tr_idx/CAGR, proxy spreads), by
  `git diff` on the CSVs (the 0–90 and fed-funds series should only append; the proxied 0–30 and SOFR
  series shift slightly when the overlap spreads move), and by viewing both `*_compare.png` charts.

## Data and modelling rules

- **No magic dates.** The start comes only from `build_range.json`; the end is computed. The only date
  literals in code are real-world data-availability facts: the proxy-transition markers in `plot_mmf.py`
  (0–30 real from **2001-08** — Jul-2001 has a single DTB4WK quote, below `MIN_OBS`; SOFR real from
  **2018-04**).
- Proxied spans: 0–30 DTM through 2001-07 (3-month bill minus the mean overlap spread); SOFR before 2018-04
  (fed funds minus the mean overlap spread). Their month-to-month differences vs the parent series are
  model output, not observed data.
- `fetch_fred.py` and `build_mmf.py` stay **pure stdlib**; matplotlib is only for `plot_mmf.py`.
- Doc statistics (MMF_SUMMARY table, methodology figures) are labelled **"as of the <Mon-YYYY> build"** and
  are refreshed by hand, not by `/rebuild`. When refreshing one, first reproduce the old value from the
  previous build's CSVs to confirm the method, then recompute.
- Optional external TR override: `data/lseg_<key>_tr.csv` (`yyyymm,value`) replaces that fund's `tr_idx`.

## Conventions

- Line endings are LF across the repo (enforced by `.gitattributes`); the scripts write CSVs with LF. Do not introduce CRLF.
- When adding a new language or toolchain, extend `.gitignore` and `.gitattributes` rather than creating parallel ignore files.
- Respect the project [LICENSE](LICENSE) when adding dependencies.

## Development environment

- Target OS is **Debian 13 (trixie)**. Base tooling is installed via `apt` — `git`, `gh`, `python3`, `python3-venv`,
  `python3-pip`, `python3-dev`, `build-essential`, `curl`, `jq` (see the [README](README.md#development-setup-debian)).
- **You may install additional system tools yourself** with `sudo apt install -y <package>` (`sudo apt update`
  first if a package isn't found). Keep Python dependencies in the project venv, not system packages. Record
  anything the project will keep relying on in the [README](README.md#development-setup-debian).
- **Debian 13 is externally managed (PEP 668): never run a system-wide `pip install`.** The only Python
  dependency is matplotlib, for the charts:

  ```bash
  python3 -m venv .venv && .venv/bin/python3 -m pip install matplotlib
  ```
- `node`/`npm` and the .NET SDK are not used.

## Notes

- Keep this file current when build/run commands, inputs, or outputs change.
