---
description: Fetch latest FRED data, rebuild the series through the last complete month, re-render charts
allowed-tools: Bash(scripts/rebuild.sh)
---
Run `scripts/rebuild.sh` from the repo root (exactly that command). It runs fetch → build → plot
and stops at the first failing step.

If it fails, report the failing step (the last `== [n/3]` line) and the error text, then stop.
Do not edit data, code, or `build_range.json` to work around it — a build failure saying the end
month "isn't fully posted yet" just means FRED hasn't caught up (retry tomorrow).

If it succeeds, summarize briefly:
- fetch: each series' new last date and rows added
- build: the window (start → end month), rows, and per-fund tr_idx end + CAGR
- files written: the root CSVs/PNGs and the `output/` snapshot stamp

Do not edit docs and do not commit.
