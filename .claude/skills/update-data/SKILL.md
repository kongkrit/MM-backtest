---
name: update-data
description: Fetch the latest FRED data, rebuild the series through the last complete month, re-render the charts, and refresh the build figures in MMF_SUMMARY.md. Use when asked to update or refresh the data.
allowed-tools: Bash(scripts/rebuild.sh)
---
Run `scripts/rebuild.sh` from the repo root (exactly that command). It runs fetch → build → plot
and stops at the first failing step.

If it fails, report the failing step (the last `== [n/3]` line) and the error text, then stop.
Do not edit data, code, docs, or `build_range.json` to work around it — a build failure saying the end
month "isn't fully posted yet" just means FRED hasn't caught up (retry tomorrow).

If it succeeds, update the build figures in `MMF_SUMMARY.md` from the build's printed lines so the doc
matches the new CSVs. Keep the existing wording and formatting; change only these values
(`<Mon-YYYY>` is the end month, e.g. `202610` → `Oct-2026`):
- **At a glance** italic line: the `<Mon-YYYY>` build, start → end month, rows, and months of return
  (= rows − 1).
- **At a glance** table: the header's end month (`tr_idx Dec-1969 → <Mon-YYYY>`) and, per fund, the
  tr_idx end (2 dp), CAGR (rounded to 2 dp) and bill price range (2 dp; cash stays "flat 100").
- **Caution 2** SOFR bullet: `SOFR averages **<x> bp below** fed funds`, where x is the `spread avg`
  on the `SOFR proxy` line (fed funds minus SOFR; write "above" if it is negative).

Leave every other doc alone (the `docs/mmf_methodology.md` figures are refreshed by hand) and do not
commit.

Then summarize briefly:
- fetch: each series' new last date and rows added
- build: the window (start → end month), rows, and per-fund tr_idx end + CAGR
- files written: the root CSVs/PNGs, the `output/` snapshot stamp, and MMF_SUMMARY's new as-of month
