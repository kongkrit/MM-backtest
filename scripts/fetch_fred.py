#!/usr/bin/env python3
"""
Refresh data/ with the full history of every FRED input the builder reads.

Full history each run: the files are small (<0.5 MB) and this also picks up any
FRED revisions, which then show in `git diff data/`.  FRED's CSV is saved as
received (it already matches our files byte for byte).  Every download is
checked before any file is written, so a failed run leaves data/ unchanged.

    python3 scripts/fetch_fred.py
"""

import os
import sys
import urllib.request

from build_mmf import DATA, SERIES

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

if __name__ == "__main__":
    fresh = {}
    for sid in SERIES:
        with open(os.path.join(DATA, f"{sid}.csv")) as fh:
            old = fh.read().splitlines()
        with urllib.request.urlopen(URL + sid, timeout=60) as resp:
            text = resp.read().decode()
        new = text.splitlines()
        # An error page or a cut-off download must not replace good data.
        if not text.startswith(f"observation_date,{sid}\n") or len(new) < len(old):
            sys.exit(f"{sid}: unexpected download ({len(new)} lines, was {len(old)}); "
                     "data/ unchanged")
        fresh[sid] = text
        print(f"{sid:<7} {old[-1][:10]} -> {new[-1][:10]}  (+{len(new) - len(old)} rows)")

    for sid, text in fresh.items():
        with open(os.path.join(DATA, f"{sid}.csv"), "w") as fh:
            fh.write(text)
