#!/usr/bin/env python3
"""
Build synthetic monthly series for 0% TER money-market funds (FUNDS below) from
the daily FRED rates in data/.  Full model, inputs and proxies:
docs/mmf_methodology.md.

Window: start_month in build_range.json through the last complete calendar
month before today.  Exits, writing nothing, if any input doesn't fully cover
that month yet.

Model in brief: a "0-N DTM" fund (DTM = days to maturity) holds a ladder of
bills bought over the last ~N days.  It therefore earns the trailing average of
the N-day yield, and its NAV moves against month-end yield changes in proportion
to the ladder's average remaining life, N/2 days.  Two share classes of one book:
    price_idx  distributing (coupons paid out), 100 at the window start
    tr_idx     accumulating (coupons reinvested), 100 at the window start

Writes, per fund (columns: yyyymm, price_idx, coupon_rate_monthly,
coupon_rate_annual, tr_idx):
    mmf_<key>.csv                          canonical latest (repo root)
    output/<YYYYMMDD_HHMM>_mmf_<key>.csv   timestamped build-history snapshot
"""

import csv
import json
import math
import os
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                  # repo root: canonical latest outputs
DATA = os.path.join(ROOT, "data")
OUTD = os.path.join(ROOT, "output")           # timestamped build-history snapshots
STAMP = "%Y%m%d_%H%M"                         # snapshot filename prefix
SERIES = ("DTB3", "DTB4WK", "DFF", "SOFR")    # FRED inputs, read from data/<ID>.csv
MIN_OBS = 10                                  # fewer daily quotes = partial month, dropped


def load_build_range():
    """Inclusive (start_ym, end_ym) as YYYYMM ints."""
    with open(os.path.join(ROOT, "build_range.json")) as fh:
        start = int(json.load(fh)["start_month"])
    last_month = date.today().replace(day=1) - timedelta(days=1)   # 2026-10-03 -> 2026-09-30
    return start, last_month.year * 100 + last_month.month


START_YM, END_YM = load_build_range()

# tenor = days of the bill bought; max_dtm = longest remaining life held.  The
# overnight funds use tenor 1, which reduces investment_yield() to the 365/360
# day-count conversion, and max_dtm 0: zero duration, so the NAV stays at 100.
FUNDS = [
    {"key": "0_90dtm", "tenor": 91, "max_dtm": 90},
    {"key": "0_30dtm", "tenor": 28, "max_dtm": 30},
    {"key": "0dtm", "tenor": 1, "max_dtm": 0},             # SOFR: canonical, holdable cash
    {"key": "0dtm_fed_funds", "tenor": 1, "max_dtm": 0},   # fed funds: benchmark only
]


def investment_yield(d, tenor):
    """Discount rate -> bond-equivalent yield (both decimal) for a `tenor`-day bill.
    Bills are quoted as a discount from face value per 360 days; the yield
    actually earned is on the lower price paid, per 365 days.
    E.g. a 5.00% discount on a 91-day bill -> 5.13% yield."""
    return d * (365 / 360) / (1 - d * tenor / 360)


def load_daily(path):
    """Daily FRED rate CSV (percent) -> {yyyymm: (month_avg, month_end)}, decimal.
    Exits if END_YM isn't fully posted: FRED adds each day's rate about a
    business day late, so END_YM counts as complete only once a later day is in."""
    by_month = {}
    with open(path, newline="") as fh:
        for day, rate in list(csv.reader(fh))[1:]:
            if rate:                                  # blank = no quote that day
                ym = int(day[:4]) * 100 + int(day[5:7])
                by_month.setdefault(ym, []).append(float(rate) / 100.0)
    if max(by_month) <= END_YM or len(by_month.get(END_YM, [])) < MIN_OBS:
        sys.exit(f"{os.path.basename(path)}: {END_YM} isn't fully posted yet; run "
                 "scripts/fetch_fred.py or retry tomorrow. Nothing was written.")
    return {ym: (sum(v) / len(v), v[-1]) for ym, v in by_month.items()
            if len(v) >= MIN_OBS}


def proxy_fill(base, real, tenor):
    """Fill the months `real` lacks with `base` minus their mean spread over the
    months both have (month-average and month-end spreads separately).
    Returns (filled series, note); note's RMSE compares proxy and real yields
    over that overlap."""
    overlap = sorted(set(base) & set(real))
    s_avg = sum(base[m][0] - real[m][0] for m in overlap) / len(overlap)
    s_eom = sum(base[m][1] - real[m][1] for m in overlap) / len(overlap)
    filled = {m: real.get(m, (a - s_avg, e - s_eom)) for m, (a, e) in base.items()}
    se = sum((investment_yield(base[m][0] - s_avg, tenor)
              - investment_yield(real[m][0], tenor)) ** 2 for m in overlap)
    note = {"first_real": overlap[0], "avg_bp": s_avg * 1e4, "eom_bp": s_eom * 1e4,
            "rmse_bp": math.sqrt(se / len(overlap)) * 1e4,
            "proxied": sum(START_YM <= m <= END_YM for m in set(base) - set(real))}
    return filled, note


def build_fund(rates, tenor, max_dtm):
    """Monthly rows for one fund from its {yyyymm: (avg, eom)} discount rates.
    Runs over all history, not just the window, so the first window rows hold a
    full ladder of real earlier bills; then keeps the window and rebases both
    indices to 100 at its first row (the base: returns start the month after)."""
    months = sorted(m for m in rates if m <= END_YM)
    y_avg = [investment_yield(rates[m][0], tenor) for m in months]
    y_eom = [investment_yield(rates[m][1], tenor) for m in months]
    duration = (max_dtm / 2.0) / 365.0        # average remaining life, years
    ladder = max(1, round(max_dtm / 30.0))    # months of purchases still held

    out = []
    price, tr = 1.0, 1.0
    for i, m in enumerate(months):
        held = y_avg[max(0, i - ladder + 1): i + 1]   # yields locked in by bills still held
        coupon_a = sum(held) / len(held)
        coupon_m = coupon_a / 12.0
        price_ret = -duration * (y_eom[i] - y_eom[i - 1]) if i else 0.0
        price *= (1.0 + price_ret)
        tr *= (1.0 + coupon_m + price_ret)
        if m >= START_YM:
            out.append({"yyyymm": m, "price": price, "coupon_rate_monthly": coupon_m,
                        "coupon_rate_annual": coupon_a, "tr": tr})
    for r in out:
        r["price_idx"] = r["price"] / out[0]["price"] * 100.0
        r["tr_idx"] = r["tr"] / out[0]["tr"] * 100.0
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
    d3, d1_real, dff, sofr_real = (load_daily(os.path.join(DATA, f"{s}.csv")) for s in SERIES)
    d1, note_1m = proxy_fill(d3, d1_real, 28)        # 4-week bill from the 3-month bill
    sofr, note_sofr = proxy_fill(dff, sofr_real, 1)  # SOFR from fed funds
    for name, n in (("4-week bill", note_1m), ("SOFR", note_sofr)):
        print(f"{name} proxy: real from {n['first_real']}, {n['proxied']} window months proxied; "
              f"spread avg {n['avg_bp']:.1f}bp eom {n['eom_bp']:.1f}bp, RMSE {n['rmse_bp']:.1f}bp")

    rates = {"0_90dtm": d3, "0_30dtm": d1, "0dtm": sofr, "0dtm_fed_funds": dff}
    stamp = datetime.now().strftime(STAMP)
    for f in FUNDS:
        out = build_fund(rates[f["key"]], f["tenor"], f["max_dtm"])
        write(out, os.path.join(ROOT, f"mmf_{f['key']}.csv"))
        write(out, os.path.join(OUTD, f"{stamp}_mmf_{f['key']}.csv"))
        a, z = out[0], out[-1]    # a is the 100 base: len(out) - 1 months of return follow
        print(f"mmf_{f['key']}: {len(out)} rows {a['yyyymm']}-{z['yyyymm']}  "
              f"tr {a['tr_idx']:.2f}->{z['tr_idx']:.2f}  "
              f"CAGR {(z['tr_idx'] / a['tr_idx']) ** (12 / (len(out) - 1)) * 100 - 100:.3f}%  "
              f"price[{min(r['price_idx'] for r in out):.2f},"
              f"{max(r['price_idx'] for r in out):.2f}]")
    print(f"build stamp: {stamp}")
