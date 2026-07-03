# MM-backtest

Synthetic monthly **total-return and price series for 0% TER money-market funds**
holding short-dated U.S. Treasury bills, from **January 1972**. Built from public
Federal Reserve (FRED) daily bill rates — no paid data feed required.

## The series

Canonical latest files live at the repo root; both are monthly, share one date
grid, and align row-for-row:

| File | Fund | Buys | Avg life |
|---|---|---|---|
| [`mmf_0_90dtm.csv`](mmf_0_90dtm.csv) | 0–90 DTM T-bills | 13-week bills | ~45 days |
| [`mmf_0_30dtm.csv`](mmf_0_30dtm.csv) | 0–30 DTM T-bills | 4-week bills | ~15 days |

Columns: `yyyymm`, `price_idx` (distributing NAV, =100 @ Jan-1972), `coupon_rate_monthly`,
`coupon_rate_annual` (=`coupon_rate_monthly × 12`), `tr_idx` (accumulating, =100 @ Aug-2002 splice).
`price_idx` and `tr_idx` are two share classes of the same portfolio (`tr_return = price_return + coupon`).

> [!WARNING]
> The **0–30 fund before July 2001 is proxied** — 4-week bills didn't exist then.
> Its level and long-run return are reliable, but its month-to-month difference
> from the 0–90 fund pre-2001-07 is a modeling artifact, not observed data. Don't
> build 0–30-vs-0–90 spread/relative-value signals on that window. See
> [`MMF_SUMMARY.md`](MMF_SUMMARY.md).

## Documentation

- [`MMF_SUMMARY.md`](MMF_SUMMARY.md) — consumer summary: **what** the files are and the 0–30 caution.
- [`docs/mmf_methodology.md`](docs/mmf_methodology.md) — full **how**: model, data, validations.

## Regenerate

```bash
# refetch FRED inputs (optional — already in data/)
for id in DTB3 DTB4WK DFF; do
  curl -sSL "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$id" -o data/$id.csv
done
python3 scripts/build_mmf.py
```

The builder writes the canonical CSVs to the repo root and an archived,
vintage-stamped snapshot to `output/mmf_<fund>_<lastmonth>.csv` (build history).
Add a maturity bucket by appending `{key, tenor, max_dtm}` to the `FUNDS` table
in [`scripts/build_mmf.py`](scripts/build_mmf.py). Pure Python 3 — no dependencies.

## Repo layout

| Path | Purpose |
|---|---|
| `mmf_0_90dtm.csv`, `mmf_0_30dtm.csv` | Canonical latest series (repo root). |
| `scripts/build_mmf.py` | Single builder for all funds. |
| `data/` | Raw FRED inputs (`DTB3`, `DTB4WK`, `DFF`). |
| `output/` | Versioned build-history snapshots. |
| `docs/`, `MMF_SUMMARY.md` | Methodology and consumer summary. |
| `PROGRESS.md` | Session handoff (printed into context at startup). |

**External TR override:** drop `data/lseg_<key>_tr.csv` (`yyyymm,value`) to replace a
fund's `tr_idx` with a genuine index (e.g. LSEG/Datastream); the FRED build still
supplies the price/coupon columns.

## Development setup (Debian)

Targets **Debian 13 (trixie)**. `docker` is assumed already installed.

Install the base toolchain:

```bash
sudo apt install -y git gh python3 python3-venv python3-pip python3-dev build-essential curl jq
```

| Package | Purpose |
|---|---|
| `git` | Version control. |
| `gh` | GitHub CLI — clone, push, PRs, releases. |
| `python3` | Interpreter (the builder is pure Python 3, no third-party deps). |
| `python3-venv` | Virtual environments — required on Debian 13 (see below). |
| `python3-pip` | Installs Python dependencies (most ship as prebuilt wheels). |
| `python3-dev` | C headers for dependencies built from source. |
| `build-essential` | C/C++ compiler + make, for the same source builds. |
| `curl` | Fetching FRED data over HTTP. |
| `jq` | Command-line JSON processor. |

### Installing more tools

Passwordless `sudo` is available; install extra system tooling when a task needs it:

```bash
sudo apt update                 # refresh the package index if a package isn't found
sudo apt install -y <package>   # e.g. ripgrep, sqlite3
```

Use `apt` for system-level tools; keep any Python dependencies in a project venv
rather than installing them system-wide. Record lasting dependencies in the base
toolchain list above so they stay reproducible.

### Python: Debian 13 is externally managed (PEP 668)

A system-wide `pip install` is blocked. Use a virtual environment per project:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt      # or: pip install -e ".[dev]"
```

(The current builder needs no packages; a venv is only needed if you add analysis deps.)

### Not required

- **node / npm** — not used; serve static content with `python3 -m http.server`.
- **.NET SDK** — no .NET projects.

## License

See [LICENSE](LICENSE).
