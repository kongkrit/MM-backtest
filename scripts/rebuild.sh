#!/usr/bin/env bash
# Rebuild everything through the last complete calendar month before today:
#   [1/3] fetch_fred.py  refresh the FRED inputs in data/ (all-or-nothing)
#   [2/3] build_mmf.py   series CSVs (repo root + output/ snapshot); fails, writing
#                        nothing, if any input doesn't yet fully cover the end month
#   [3/3] plot_mmf.py    comparison charts (repo root + output/ snapshot)
# Stops at the first failing stage, so later stages never run on a failed one.
#
# Usage:  scripts/rebuild.sh        (or /rebuild in Claude Code)
set -euo pipefail
cd "$(dirname "$0")/.."

PY_PLOT=.venv/bin/python3   # charting needs matplotlib; fetch + build are pure stdlib
if [[ ! -x $PY_PLOT ]]; then
    echo "rebuild: $PY_PLOT not found — create the venv first (see README):" >&2
    echo "  python3 -m venv .venv && .venv/bin/python3 -m pip install matplotlib" >&2
    exit 1
fi

stage=""
trap 'echo "== rebuild FAILED at $stage; later stages skipped" >&2' ERR

stage="[1/3] fetch"; echo "== $stage: FRED inputs"
python3 scripts/fetch_fred.py
stage="[2/3] build"; echo "== $stage: series CSVs"
python3 scripts/build_mmf.py
stage="[3/3] plot";  echo "== $stage: comparison charts"
"$PY_PLOT" scripts/plot_mmf.py
echo "== rebuild complete"
