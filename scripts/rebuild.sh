#!/usr/bin/env bash
# Fetch the FRED inputs, rebuild the series, re-render the charts, through the
# last complete month before today.  `set -e` stops at the first failing step,
# so the last "==" line printed names the step that failed.
set -e
cd "$(dirname "$0")/.."
echo "== [1/3] fetch"; python3 scripts/fetch_fred.py
echo "== [2/3] build"; python3 scripts/build_mmf.py
echo "== [3/3] plot";  .venv/bin/python3 scripts/plot_mmf.py
