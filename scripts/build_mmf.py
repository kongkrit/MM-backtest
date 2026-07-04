#!/usr/bin/env python3
"""
Build synthetic monthly series for 0% TER money-market funds that hold
0-N DTM (days-to-maturity) U.S. Treasury bills, from January 1972.

Emits, for each fund in the FUNDS table below, TWO copies:
    <repo-root>/mmf_<key>.csv                 canonical latest series (consumers read this)
    output/<YYYYMMDD_HHMM>_mmf_<key>.csv       timestamped build-history snapshot
                                              (stamp captured right before writing)
so the repo root always holds the current series while output/ accumulates the
timestamped history of past builds.  Funds:
    mmf_0_90dtm  0-90 DTM  (buys 13-week bills, avg life ~45d)
    mmf_0_30dtm  0-30 DTM  (buys  4-week bills, avg life ~15d)
    mmf_0dtm            CANONICAL cash: secured Treasury repo, SOFR (2018+; proxied
                        before; flat NAV) — what a government MMF earns / you can hold
    mmf_0dtm_fed_funds  effective fed funds (unsecured, interbank) — BENCHMARK only

Columns (identical schema for every fund):
    yyyymm, price_idx, coupon_rate_monthly, coupon_rate_annual, tr_idx

==========================================================================
PORTFOLIO MODEL
==========================================================================
A "0-N DTM" fund buys the bill of tenor ~N days at auction and holds it to
maturity, so the steady-state book is a ladder with remaining lives spread
uniformly over 0-N days:
    * average remaining life = N/2 days           -> mark-to-market duration
    * bills were purchased over the trailing ~N days, each locked at the
      N-day yield prevailing then
      -> income earned = trailing average of the N-day yield (lags the market)

Two share classes off the SAME book, linked by the exact identity
      tr_return[t] = price_return[t] + coupon_rate_monthly[t] :
    price_idx  distributing NAV (coupons removed, marks to market), 100 @ 1972
    tr_idx     accumulating    (coupons reinvested), 100 @ the Aug-2002 splice

==========================================================================
INPUTS  (public FRED daily discount rates, %, converted to bond-equivalent)
==========================================================================
  data/DTB3.csv     3-month (13-week) bill, 1954->        -> 0-90 fund, all history
  data/DTB4WK.csv   4-week bill, 2001-07->                -> 0-30 fund, 2001-07+
  data/SOFR.csv     secured overnight financing rate (repo), 2018-04-> -> 0dtm
                    (CANONICAL cash; pre-2018 proxied as fed funds - mean spread, ~0 bp)
  data/DFF.csv      effective fed funds (overnight), 1954-> -> 0dtm_fed_funds (benchmark;
                    add-on rate; also the pre-2018 proxy base for 0dtm/SOFR)

PRE-2001 PROXY (0-30 fund only)
-------------------------------
The Treasury did not auction 4-week bills before Jul-2001, so no 1-month
series exists for 1972..2001-06.  There the 4-week DISCOUNT rate is proxied as
    d_4wk(t) = d_3mo(t) - mean(d_3mo - d_4wk over the 2001-07+ overlap)
(the month-average and month-end spreads are measured and applied separately).

Consequence, documented in docs/mmf_methodology.md: pre-2001 the 0-30 fund is
the SAME 3-month rate signal run through genuine 0-30 conventions (shorter
1-month income-smoothing window + 28-day yield conversion).  It is therefore
meaningfully lower-yielding and more responsive than the 0-90 fund
(cumulatively ~ -4.3% of carry over 1972-2001) but carries little information
INDEPENDENT of it: the real 1M-3M spread volatility (+/-35..93 bp post-2001)
is flattened to a constant.  Treat pre-200107 0-30 vs 0-90 month-to-month
divergences as structural-model output, not observed market data.

Optional override (any fund): drop data/lseg_<key>_tr.csv (yyyymm,value) to
replace that fund's tr_idx with a genuine external total-return index.
"""

import csv
import math
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")            # repo root: canonical latest series
DATA = os.path.join(HERE, "..", "data")
OUTD = os.path.join(HERE, "..", "output")  # build-history snapshots

START_YM  = 197201
SPLICE_YM = 200208
MIN_OBS   = 10          # drop a trailing partial month
DAYS_360  = 360.0
DAYS_365  = 365.0

# key, tenor (days of the purchased bill), max DTM (bucket width)
FUNDS = [
    {"key": "0_90dtm", "tenor": 91, "max_dtm": 90},
    {"key": "0_30dtm", "tenor": 28, "max_dtm": 30},
    # 0dtm = CANONICAL overnight "cash": secured Treasury repo (SOFR). This is
    # what a government/Treasury money-market fund actually earns and what you can
    # hold in a brokerage account. Real data 2018-04+; before that proxied as
    # fed funds minus the mean fed-funds - SOFR spread (~0 bp). tenor 1 makes
    # investment_yield() collapse to the x365/360 (actual/360->actual/365)
    # conversion; max_dtm 0 => zero duration => flat NAV (=100).
    {"key": "0dtm", "tenor": 1, "max_dtm": 0},
    # 0dtm_fed_funds = effective fed funds (UNSECURED, interbank). BENCHMARK ONLY
    # — not directly holdable at retail. Same flat-NAV cash mechanics.
    {"key": "0dtm_fed_funds", "tenor": 1, "max_dtm": 0},
]


def investment_yield(d, tenor):
    """Discount rate (decimal) -> bond-equivalent yield (decimal) for a
    `tenor`-day bill.  Uplift = 365/360 with the exact price-based convexity."""
    return d * (DAYS_365 / DAYS_360) / (1.0 - d * tenor / DAYS_360)


def load_daily(path):
    """Daily FRED discount CSV -> {yyyymm: (avg_decimal, eom_decimal)}."""
    agg = {}
    with open(path, newline="") as fh:
        for rec in csv.DictReader(fh):
            date = rec["observation_date"]
            col = next(k for k in rec if k != "observation_date")
            val = rec[col]
            if val in (".", "", None):
                continue
            ym = int(date[:4]) * 100 + int(date[5:7])
            v = float(val) / 100.0
            a = agg.setdefault(ym, [0.0, 0, "", 0.0])
            a[0] += v
            a[1] += 1
            if date > a[2]:
                a[2], a[3] = date, v
    return {ym: (s / n, last) for ym, (s, n, _dt, last) in agg.items()
            if n >= MIN_OBS}


def proxy_short_discount(d3, d1):
    """Full-history 4-week discount {ym:(avg,eom)}: real DTB4WK where it exists,
    else 3-month minus the mean overlap discount spread.  Returns (series, note)."""
    ov = sorted(set(d3) & set(d1))
    da = sum(d3[m][0] - d1[m][0] for m in ov) / len(ov)
    de = sum(d3[m][1] - d1[m][1] for m in ov) / len(ov)
    out, proxied = {}, 0
    for m, (a3, e3) in d3.items():
        if m in d1:
            out[m] = d1[m]
        else:
            out[m] = (a3 - da, e3 - de)
            proxied += 1
    se = sum((investment_yield(d3[m][0] - da, 28)
              - investment_yield(d1[m][0], 28)) ** 2 for m in ov)
    note = {"spread_avg_bp": da * 1e4, "spread_eom_bp": de * 1e4,
            "overlap": (ov[0], ov[-1]), "proxied": proxied,
            "rmse_bp": math.sqrt(se / len(ov)) * 1e4}
    return out, note


def proxy_overnight(base, target):
    """Full-history overnight add-on rate {ym:(avg,eom)}: real `target` (e.g.
    SOFR, secured) where it exists, else `base` (fed funds) minus the mean
    base-target overlap spread.  Same shape as proxy_short_discount; used for
    the canonical secured-overnight (0dtm) series whose real data starts 2018-04."""
    ov = sorted(set(base) & set(target))
    da = sum(base[m][0] - target[m][0] for m in ov) / len(ov)
    de = sum(base[m][1] - target[m][1] for m in ov) / len(ov)
    out, proxied = {}, 0
    for m, (a, e) in base.items():
        if m in target:
            out[m] = target[m]
        else:
            out[m] = (a - da, e - de)
            proxied += 1
    note = {"spread_avg_bp": da * 1e4, "overlap": (ov[0], ov[-1]), "proxied": proxied}
    return out, note


def load_override(key):
    path = os.path.join(DATA, f"lseg_{key}_tr.csv")
    if not os.path.exists(path):
        return None
    s = {}
    for rec in csv.DictReader(open(path, newline="")):
        cols = list(rec.values())
        s[int(rec.get("yyyymm", cols[0]))] = float(rec.get("value", cols[1]))
    return s or None


def build_fund(disc, tenor, max_dtm, key):
    months = sorted(m for m in disc if m >= START_YM)
    y_avg = {m: investment_yield(disc[m][0], tenor) for m in months}
    y_eom = {m: investment_yield(disc[m][1], tenor) for m in months}
    d_mod = (max_dtm / 2.0) / DAYS_365                 # avg-life duration (yr)
    ladder = max(1, round(max_dtm / 30.0))             # trailing purchase window

    out = []
    price_idx, tr_raw, prev_eom = 100.0, 1.0, None
    for i, m in enumerate(months):
        win = [y_avg[months[j]] for j in range(max(0, i - ladder + 1), i + 1)]
        y_earn = sum(win) / len(win)
        coupon_m = y_earn / 12.0
        price_ret = 0.0 if prev_eom is None else -d_mod * (y_eom[m] - prev_eom)
        price_idx *= (1.0 + price_ret)
        tr_raw *= (1.0 + coupon_m + price_ret)
        out.append({"yyyymm": m, "price_idx": price_idx,
                    "coupon_rate_monthly": coupon_m, "coupon_rate_annual": y_earn,
                    "tr_raw": tr_raw})
        prev_eom = y_eom[m]

    base = next(r["tr_raw"] for r in out if r["yyyymm"] == SPLICE_YM)
    for r in out:
        r["tr_idx"] = r["tr_raw"] / base * 100.0

    override = load_override(key)
    if override:
        ob = override[SPLICE_YM]
        for r in out:
            if r["yyyymm"] in override:
                r["tr_idx"] = override[r["yyyymm"]] / ob * 100.0
        print(f"  [{key}] external TR override applied")
    return out


def write(out, path):
    cols = ["yyyymm", "price_idx", "coupon_rate_monthly",
            "coupon_rate_annual", "tr_idx"]
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")   # LF, per repo .gitattributes
        w.writerow(cols)
        for r in out:
            w.writerow([r["yyyymm"], f"{r['price_idx']:.4f}",
                        f"{r['coupon_rate_monthly']:.8f}",
                        f"{r['coupon_rate_annual']:.8f}", f"{r['tr_idx']:.6f}"])


if __name__ == "__main__":
    d3 = load_daily(os.path.join(DATA, "DTB3.csv"))
    d1_real = load_daily(os.path.join(DATA, "DTB4WK.csv"))
    d1_full, note = proxy_short_discount(d3, d1_real)
    dff = load_daily(os.path.join(DATA, "DFF.csv"))   # overnight cash (fed funds)
    sofr = load_daily(os.path.join(DATA, "SOFR.csv"))  # secured overnight repo
    sofr_full, snote = proxy_overnight(dff, sofr)
    disc_by_key = {"0_90dtm": d3, "0_30dtm": d1_full,
                   "0dtm": sofr_full, "0dtm_fed_funds": dff}

    print(f"4-week proxy: spread avg={note['spread_avg_bp']:.1f}bp "
          f"eom={note['spread_eom_bp']:.1f}bp; real {note['overlap'][0]}-"
          f"{note['overlap'][1]}, {note['proxied']} months proxied pre-2001 "
          f"(overlap RMSE {note['rmse_bp']:.1f}bp)")
    print(f"SOFR proxy: fed funds - SOFR spread {snote['spread_avg_bp']:.1f}bp; "
          f"real {snote['overlap'][0]}-{snote['overlap'][1]}, "
          f"{snote['proxied']} months proxied pre-2018")
    results = [(f, build_fund(disc_by_key[f["key"]], f["tenor"], f["max_dtm"], f["key"]))
               for f in FUNDS]
    stamp = datetime.now().strftime("%Y%m%d_%H%M")   # fetched right before writing
    for f, out in results:
        write(out, os.path.join(ROOT, f"mmf_{f['key']}.csv"))          # canonical latest
        write(out, os.path.join(OUTD, f"{stamp}_mmf_{f['key']}.csv"))  # timestamped history
        a, z = out[0], out[-1]
        yrs = len(out) / 12.0
        print(f"mmf_{f['key']}: {len(out)} rows {a['yyyymm']}-{z['yyyymm']}  "
              f"tr {a['tr_idx']:.2f}->{z['tr_idx']:.2f}  "
              f"CAGR {(z['tr_idx']/a['tr_idx'])**(1/yrs)*100-100:.3f}%  "
              f"price[{min(r['price_idx'] for r in out):.2f},"
              f"{max(r['price_idx'] for r in out):.2f}]")
    print(f"build stamp: {stamp}")
