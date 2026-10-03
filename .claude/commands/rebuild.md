---
description: Fetch latest FRED data, rebuild the series through the last complete month, re-render charts
allowed-tools: Bash(scripts/rebuild.sh)
---
Run `scripts/rebuild.sh` from the repo root (exactly that command). It runs fetch → build → plot
and stops at the first failing stage.

If it fails, report the failing stage (the `== [n/3]` line before the error) and the error text,
then stop. Do not edit data, code, or `build_range.json` to work around it — a build coverage-gate
failure just means FRED hasn't fully posted the end month yet (rerun later).

If it succeeds, summarize briefly:
- fetch: each series' new last date, rows added, and revised values (call out any revisions)
- build: the window (start → end month), rows, and per-fund tr_idx end + CAGR
- files written: the root CSVs/PNGs and the `output/` snapshot stamp

Do not edit docs and do not commit.
