# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

**MM-backtest** builds synthetic monthly **price and total-return series for 0% TER money-market funds** —
two rolling T-bill ladders (0–90 and 0–30 DTM) and two overnight-cash funds (SOFR, canonical; fed funds,
benchmark) — from public FRED daily rates, from a Dec 1969 base row (both indices 100; returns start
Jan 1970) through the last complete month. Each fund is computed over all FRED history before the window
is cut, so no row is a warm-up. Consumers read the
canonical CSVs at the repo root; [MMF_SUMMARY.md](MMF_SUMMARY.md) explains *what* they are,
[docs/mmf_methodology.md](docs/mmf_methodology.md) explains *how*.

## Code principles — IMPORTANT

**All code MUST be SIMPLE, MINIMAL, EASY TO UNDERSTAND, and DRY.** These rules come before cleverness, speculative flexibility, and personal style.

- **Simple:** use the most straightforward approach that works. No clever tricks, premature abstraction, or premature optimization.
- **Minimal:** write only what the task needs. No speculative features, unused options, or "just in case" code. Fewer lines, files, and dependencies win. Delete dead code.
- **Easy to understand:** a newcomer should follow it on first read. Clear names, small functions, shallow nesting, obvious control flow.
- **DRY:** one source of truth for each piece of logic, data, and config. Search for existing code to reuse before writing new code; never copy-paste logic. Extract it once instead.
- **When in doubt, choose the simpler option.** Before finishing, re-read your diff and cut anything that isn't needed.

## How to explain things

These rules apply to explanations to the user and to code comments, not to commit messages.

For code comments:
- Explain why and the mechanism; don't restate what the code plainly does.
- Define a term once, at its first use in the file.
- Add a worked numeric example only for non-obvious math (scaling, units, bit layouts).
- Keep comments as short as the point allows; "Simple", "Minimal", "Easy to understand", and "DRY" still applies.

Audience: someone with a BS in EE who remembers the fundamentals (circuits, signals, calculus, basic probability and statistics) but not every formula or every field's jargon. Write for a sharp engineer outside the specialty.

Goal: as simple as possible, without saying anything false.

1. Start with the plain-language answer in 1-2 sentences, then the reasoning.
2. Explain the mechanism (what causes what) in words before any math.
3. Define each technical term the first time it appears, in a short phrase. Introduce as few new terms as possible.
4. Use an equation only when it makes the point clearer than words. If you use one, define every symbol and show one worked example with real numbers.
5. Prefer a concrete numeric example over abstract notation.
6. Use an analogy (EE analogies are welcome) only if it maps accurately, and say where it breaks down.
7. When you simplify, say what you left out and when it would matter.
8. No handwaving: back each claim with a reason, a number, or a source. If the answer depends on something, say what. If unsure, say so.
9. Before sending, check: could I follow this on the first read without looking anything up? If not, rewrite it.

## Repository layout

- `mmf_0_90dtm.csv`, `mmf_0_30dtm.csv`, `mmf_0dtm.csv`, `mmf_0dtm_fed_funds.csv` — canonical latest series
  (identical schema: `yyyymm, price_idx, coupon_rate_monthly, coupon_rate_annual, tr_idx`; both indices
  = 100 @ the build-window start).
- `mmf_30-90DTM_compare.png`, `mmf_0dtm_compare.png` — canonical latest 3-pane comparison charts.
- `build_range.json` — `start_month` only (single source of truth for the start; there is no end setting).
- `scripts/fetch_fred.py` — refreshes `data/` from FRED; writes only if every download has the right header and no fewer rows (stdlib only).
- `scripts/build_mmf.py` — series builder (stdlib only); `FUNDS` table defines the buckets.
- `scripts/plot_mmf.py` — chart renderer (matplotlib, from `.venv`).
- `scripts/rebuild.sh` — fetch → build → plot in one go.
- `data/` — raw FRED daily inputs `DTB3`, `DTB4WK`, `DFF`, `SOFR` (the list lives in `SERIES` in `build_mmf.py`).
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
  calendar month before today. Stops at the first failing step.
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
- `build_mmf.py` is the single source of truth for paths (`ROOT`, `DATA`, `OUTD`), the snapshot stamp
  format (`STAMP`), and the input list (`SERIES`); `fetch_fred.py` and `plot_mmf.py` import them.
- Doc statistics (MMF_SUMMARY table, methodology figures) are labelled **"as of the <Mon-YYYY> build"** and
  are refreshed by hand, not by `/rebuild`. When refreshing one, first reproduce the old value from the
  previous build's CSVs to confirm the method, then recompute.

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
