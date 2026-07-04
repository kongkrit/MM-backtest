#!/usr/bin/env python3
"""
Render mmf_chart.png — a 3-pane comparison of the 0-30 vs 0-90 DTM rolling
Treasury-bill funds, all sharing one x-axis (time):

    pane 1   price_idx, SEMILOG y            (both funds)
    pane 2   coupon_rate_annual, LINEAR y    (both funds)
    pane 3   monthly coupon delta, LINEAR y  = coupon_monthly(0-90) - coupon_monthly(0-30),
             in basis points of NAV; blue where 0-90 pays more, red where 0-30 does.

Reads the canonical CSVs at the repo root; writes:
    <repo-root>/mmf_chart.png                 canonical latest chart
    output/<YYYYMMDD_HHMM>_mmf_chart.png       timestamped build-history snapshot
                                              (stamp captured right before writing)

Needs matplotlib (see .venv):  .venv/bin/python3 scripts/plot_mmf.py
Fund colours are dataviz categorical slots 1 (blue) & 2 (aqua); the delta uses
the diverging blue<->red pair about a gray zero — all colourblind-safe.
"""

import csv
import os
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter
from matplotlib.ticker import ScalarFormatter, NullFormatter
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUTD = os.path.join(HERE, "..", "output")

# dataviz reference palette (light surface) ---------------------------------
SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"
MUTED = "#898781"; GRID = "#e1e0d9"; AXIS = "#c3c2b7"
C90 = "#2a78d6"   # blue  — slot 1  -> 0-90 DTM
C30 = "#1baf7a"   # aqua  — slot 2  -> 0-30 DTM
CRED = "#e34948"  # red   — slot 6  -> diverging pole (0-30 pays more)
SPLIT = datetime(2001, 7, 1)   # 0-30 is proxied before this; observed after


def load(key):
    rows = list(csv.DictReader(open(os.path.join(ROOT, f"mmf_{key}.csv"))))
    x = [datetime(int(r["yyyymm"]) // 100, int(r["yyyymm"]) % 100, 1) for r in rows]
    price = [float(r["price_idx"]) for r in rows]
    coupon_a = [float(r["coupon_rate_annual"]) * 100.0 for r in rows]      # percent
    coupon_m = [float(r["coupon_rate_monthly"]) for r in rows]             # fraction
    return x, price, coupon_a, coupon_m


def main():
    x, p90, ca90, cm90 = load("0_90dtm")
    _, p30, ca30, cm30 = load("0_30dtm")
    delta_bp = np.array([(a - b) * 1e4 for a, b in zip(cm90, cm30)])  # monthly, bp of NAV

    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "font.family": "sans-serif", "font.size": 10,
    })
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, sharex=True, figsize=(11, 11.6),
        gridspec_kw={"hspace": 0.17, "height_ratios": [1.05, 1.05, 0.8]})

    # --- pane 1: price index, semilog ------------------------------------
    ax1.set_yscale("log")
    ax1.plot(x, p90, color=C90, lw=1.8, label="0–90 DTM")
    ax1.plot(x, p30, color=C30, lw=1.8, label="0–30 DTM")
    ax1.set_ylim(98.2, 100.7)
    ax1.set_yticks([98.5, 99, 99.5, 100, 100.5])
    ax1.yaxis.set_major_formatter(ScalarFormatter())
    ax1.yaxis.set_minor_formatter(NullFormatter())
    ax1.minorticks_off()
    ax1.set_ylabel("Price / NAV index\n(=100 @ 1972, log scale)")
    ax1.set_title("Money-market fund price index — 0–30 vs 0–90 DTM",
                  loc="left", color=INK, fontsize=12.5, fontweight="bold", pad=8)
    ax1.legend(frameon=False, loc="upper left", labelcolor=INK2)
    ax1.text(SPLIT, 100.62, "  0–30 DTM: proxied ← | → observed", color=MUTED,
             fontsize=8.5, va="top", ha="left")

    # --- pane 2: annual coupon rate, linear ------------------------------
    ax2.plot(x, ca90, color=C90, lw=1.8, label="0–90 DTM")
    ax2.plot(x, ca30, color=C30, lw=1.8, label="0–30 DTM")
    ax2.set_ylim(0, None)
    ax2.set_ylabel("Coupon rate, annual (%)")
    ax2.set_title("Annual coupon rate — 0–30 vs 0–90 DTM",
                  loc="left", color=INK, fontsize=12.5, fontweight="bold", pad=8)
    ax2.legend(frameon=False, loc="upper right", labelcolor=INK2)

    # --- pane 3: monthly coupon delta (0-90 - 0-30), linear, diverging ---
    ax3.axhline(0, color=AXIS, lw=0.8)
    ax3.fill_between(x, 0, delta_bp, where=delta_bp >= 0, interpolate=True,
                     color=C90, alpha=0.55, linewidth=0)
    ax3.fill_between(x, 0, delta_bp, where=delta_bp <= 0, interpolate=True,
                     color=CRED, alpha=0.55, linewidth=0)
    ax3.plot(x, delta_bp, color=INK2, lw=0.7)
    ax3.set_ylabel("Monthly coupon Δ\n0–90 − 0–30 (bp of NAV)")
    ax3.set_xlabel("Year")
    ax3.set_title("Monthly coupon delta — 0–90 minus 0–30",
                  loc="left", color=INK, fontsize=12.5, fontweight="bold", pad=8)
    ax3.legend(handles=[Patch(color=C90, alpha=0.55, label="0–90 pays more"),
                        Patch(color=CRED, alpha=0.55, label="0–30 pays more")],
               frameon=False, loc="upper right", labelcolor=INK2, ncol=2, fontsize=8.5)

    # --- shared x + proxy marker on every pane ---------------------------
    ax3.xaxis.set_major_locator(YearLocator(5))
    ax3.xaxis.set_major_formatter(DateFormatter("%Y"))
    for ax in (ax1, ax2, ax3):
        ax.axvline(SPLIT, color=MUTED, ls=(0, (4, 3)), lw=0.9, alpha=0.7)
        ax.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(AXIS)
        ax.tick_params(colors=MUTED)

    fig.text(0.008, 0.006,
             "0% TER, rolling T-bill ladders. Source: FRED daily T-bill rates "
             "(DTB3, DTB4WK). 0–30 DTM proxied before Jul-2001 — see MMF_SUMMARY.md.",
             color=MUTED, fontsize=8)

    stamp = datetime.now().strftime("%Y%m%d_%H%M")   # fetched right before writing
    for path in (os.path.join(ROOT, "mmf_chart.png"),
                 os.path.join(OUTD, f"{stamp}_mmf_chart.png")):
        fig.savefig(path, dpi=140, facecolor=SURFACE, bbox_inches="tight")
    print(f"wrote mmf_chart.png (+ output/{stamp}_mmf_chart.png)")


if __name__ == "__main__":
    main()
