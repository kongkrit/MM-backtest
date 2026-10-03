#!/usr/bin/env python3
"""
Refresh the FRED daily inputs in data/ to the latest published observations.

Downloads the FULL history of each series the builder reads (SERIES below) from
FRED's public CSV endpoint (no API key), validates every download, and only
then replaces data/<ID>.csv — all-or-nothing, so data/ is never left holding a
mix of old and new vintages.  Re-downloading full history (files are <0.5 MB)
also picks up FRED's revisions to past observations.

A download is refused (exit 1, data/ untouched) if:
    the header isn't  observation_date,<ID>
    any row isn't (ISO date, number-or-blank), or dates aren't strictly rising
    its first date differs from the existing file   (truncated history)
    its last date or row count goes backwards        (stale / partial response)

Reports, per series:
    <ID>  old_last -> new_last  (+N rows, K revised)
where "revised" counts dates in the existing file whose value changed (or that
FRED no longer lists).

The fetcher does not pick the build end month: build_mmf.py's coverage gate
does (last complete month before today, which must be fully posted).

Pure stdlib:  python3 scripts/fetch_fred.py
"""

import csv
import io
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

SERIES = ("DTB3", "DTB4WK", "DFF", "SOFR")   # the inputs scripts/build_mmf.py reads
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
USER_AGENT = "MM-backtest/fetch_fred.py (python-urllib)"
TIMEOUT = 60      # seconds per attempt
ATTEMPTS = 3      # backoff 2 s, 4 s between attempts
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def download(sid):
    req = urllib.request.Request(URL.format(sid), headers={"User-Agent": USER_AGENT})
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode("utf-8")
        except OSError as e:   # URLError / HTTPError / timeouts are all OSError
            if attempt == ATTEMPTS:
                raise OSError(f"download failed after {ATTEMPTS} attempts: {e}") from e
            time.sleep(2 ** attempt)


def parse(text, sid, source):
    """FRED CSV text -> [(date, value)]; raises ValueError on malformed content.
    value is the raw string ('' = FRED missing, e.g. a holiday)."""
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or rows[0] != ["observation_date", sid]:
        raise ValueError(f"unexpected header in {source}: {rows[0] if rows else '(empty)'}")
    out = []
    for n, r in enumerate(rows[1:], start=2):
        if len(r) != 2 or not ISO_DATE.match(r[0]):
            raise ValueError(f"malformed row {n} in {source}: {r}")
        if r[1] not in ("", "."):
            try:
                float(r[1])
            except ValueError:
                raise ValueError(f"non-numeric value on row {n} in {source}: {r}")
        if out and r[0] <= out[-1][0]:
            raise ValueError(f"dates not strictly rising at row {n} in {source}: {r[0]}")
        out.append((r[0], r[1]))
    if not out:
        raise ValueError(f"no observations in {source}")
    return out


def same(a, b):
    """Equal observations: both missing, or numerically equal ('3.6' == '3.60')."""
    miss_a, miss_b = a in ("", "."), b in ("", ".")
    if miss_a or miss_b:
        return miss_a and miss_b
    return float(a) == float(b)


def check(old, new):
    """Validate `new` against the existing file's rows; return (added, revised)."""
    if not old:
        return len(new), 0
    if new[0][0] != old[0][0]:
        raise ValueError(f"first date changed {old[0][0]} -> {new[0][0]} (truncated history?)")
    if new[-1][0] < old[-1][0]:
        raise ValueError(f"last date went backwards {old[-1][0]} -> {new[-1][0]}")
    if len(new) < len(old):
        raise ValueError(f"row count went backwards {len(old)} -> {len(new)}")
    fresh = dict(new)
    revised = sum(1 for d, v in old if d not in fresh or not same(v, fresh[d]))
    return len(new) - len(old), revised


if __name__ == "__main__":
    staged, errors = [], []
    for sid in SERIES:
        path = os.path.join(DATA, f"{sid}.csv")
        try:
            old = []
            if os.path.exists(path):
                with open(path, newline="") as fh:
                    old = parse(fh.read(), sid, path)
            new = parse(download(sid), sid, URL.format(sid))
            added, revised = check(old, new)
            staged.append((sid, path, new))
            print(f"{sid:<7} {old[-1][0] if old else '(none)':>10} -> {new[-1][0]}  "
                  f"(+{added} rows, {revised} revised)")
        except (OSError, ValueError) as e:
            errors.append(f"  {sid}: {e}")
    if errors:
        sys.exit("FRED fetch failed; data/ left untouched:\n" + "\n".join(errors))

    tmps = []
    try:
        for sid, path, rows in staged:   # write every temp first ...
            tmp = os.path.join(DATA, f".{sid}.csv.tmp")
            tmps.append(tmp)
            with open(tmp, "w", newline="") as fh:   # LF, per repo .gitattributes
                fh.write(f"observation_date,{sid}\n")
                fh.writelines(f"{d},{v}\n" for d, v in rows)
        for (sid, path, _rows), tmp in zip(staged, tmps):   # ... then swap them in
            os.replace(tmp, path)
    finally:
        for tmp in tmps:
            if os.path.exists(tmp):
                os.remove(tmp)
    print(f"updated data/: {', '.join(SERIES)}")
