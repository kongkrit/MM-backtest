#!/usr/bin/env python3
"""
Render the comparison charts (one per entry in CHARTS), each a 3-pane figure on
a shared time axis:

    pane 1   price_idx, SEMILOG y            (both funds)
    pane 2   coupon_rate_annual, LINEAR y    (both funds)
    pane 3   monthly coupon delta, LINEAR y  = coupon_monthly(A) - coupon_monthly(B),
             in bp of NAV; blue where A pays more, red where B pays more.

Charts produced:
    mmf_30-90DTM_compare.png   0-90 vs 0-30 DTM T-bill funds
    mmf_0dtm_compare.png       fed-funds vs SOFR overnight-cash funds (price pane
                               is flat 100 — cash has zero duration)

Reads the canonical CSVs at the repo root; for each chart writes:
    <repo-root>/<name>.png                  canonical latest
    output/<YYYYMMDD_HHMM>_<name>.png        timestamped build-history snapshot
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
CA = "#2a78d6"    # blue  — slot 1  -> fund A
CB = "#1baf7a"    # aqua  — slot 2  -> fund B
CRED = "#e34948"  # red   — slot 6  -> diverging pole (B pays more)

CHARTS = [
    {
        "name": "mmf_30-90DTM_compare",
        "A": ("0_90dtm", "0–90 DTM"), "B": ("0_30dtm", "0–30 DTM"),
        "split": datetime(2001, 8, 1), "split_note": "0–30 DTM: proxied ← | → observed",
        "titles": ("Money-market fund price index — 0–30 vs 0–90 DTM",
                   "Annual coupon rate — 0–30 vs 0–90 DTM",
                   "Monthly coupon delta — 0–90 minus 0–30"),
        "delta_ylabel": "Monthly coupon Δ\n0–90 − 0–30 (bp of NAV)",
        "delta_more": ("0–90 pays more", "0–30 pays more"),
        "caption": ("0% TER, rolling T-bill ladders. Source: FRED daily T-bill "
                    "rates (DTB3, DTB4WK). 0–30 DTM proxied through Jul-2001 — "
                    "see MMF_SUMMARY.md."),
    },
    {
        "name": "mmf_0dtm_compare",
        "A": ("0dtm_fed_funds", "fed funds (benchmark)"), "B": ("0dtm", "SOFR — 0DTM cash"),
        "split": datetime(2018, 4, 1), "split_note": "SOFR: proxied ← | → observed",
        "titles": ("Overnight cash NAV — fed funds vs SOFR  (flat: zero duration)",
                   "Annual coupon rate — fed funds vs SOFR",
                   "Monthly coupon delta — fed funds minus SOFR"),
        "delta_ylabel": "Monthly coupon Δ\nfed funds − SOFR (bp of NAV)",
        "delta_more": ("fed funds pays more", "SOFR pays more"),
        "caption": ("0% TER overnight cash, flat NAV. Source: FRED DFF (fed "
                    "funds), SOFR. SOFR proxied before Apr-2018 — see "
                    "MMF_SUMMARY.md."),
    },
]


def load(key):
    rows = list(csv.DictReader(open(os.path.join(ROOT, f"mmf_{key}.csv"))))
    x = [datetime(int(r["yyyymm"]) // 100, int(r["yyyymm"]) % 100, 1) for r in rows]
    price = [float(r["price_idx"]) for r in rows]
    coupon_a = [float(r["coupon_rate_annual"]) * 100.0 for r in rows]   # percent
    coupon_m = [float(r["coupon_rate_monthly"]) for r in rows]          # fraction
    return x, price, coupon_a, coupon_m


def price_window(*series):
    """Data-derived y-window + ticks for the price pane — no hardcoded limits.
    Tight to the data (12% margin) but at least ±0.5 around the midpoint so a
    flat, zero-duration cash NAV still reads as flat-at-100. Ticks on a clean
    0.5 grid inside the window."""
    lo = min(min(s) for s in series)
    hi = max(max(s) for s in series)
    mid = (lo + hi) / 2.0
    half = max((hi - lo) / 2.0 * 1.12, 0.5)
    ylo, yhi = mid - half, mid + half
    ticks = list(np.arange(np.ceil(ylo / 0.5) * 0.5, yhi + 1e-9, 0.5))
    return ylo, yhi, ticks


def build_fig(cfg):
    (kA, lA), (kB, lB) = cfg["A"], cfg["B"]
    x, pA, caA, cmA = load(kA)
    _, pB, caB, cmB = load(kB)
    delta_bp = np.array([(a - b) * 1e4 for a, b in zip(cmA, cmB)])
    split = cfg["split"]
    ylo, yhi, price_yticks = price_window(pA, pB)
    note_y = ylo + 0.03 * (yhi - ylo)   # bottom of the pane, clear of the lines

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, sharex=True, figsize=(11, 11.6),
        gridspec_kw={"hspace": 0.17, "height_ratios": [1.05, 1.05, 0.8]})

    # pane 1: price index, semilog
    ax1.set_yscale("log")
    ax1.plot(x, pA, color=CA, lw=1.8, label=lA)
    ax1.plot(x, pB, color=CB, lw=1.8, label=lB)
    ax1.set_ylim(ylo, yhi)
    ax1.set_yticks(price_yticks)
    ax1.yaxis.set_major_formatter(ScalarFormatter())
    ax1.yaxis.set_minor_formatter(NullFormatter())
    ax1.minorticks_off()
    ax1.set_ylabel(f"Price / NAV index\n(=100 @ {x[0].year}, log scale)")
    ax1.set_title(cfg["titles"][0], loc="left", color=INK, fontsize=12.5,
                  fontweight="bold", pad=8)
    ax1.legend(frameon=False, loc="upper left", labelcolor=INK2)
    ax1.text(split, note_y, "  " + cfg["split_note"], color=MUTED,
             fontsize=8.5, va="bottom", ha="left")

    # pane 2: annual coupon rate, linear
    ax2.plot(x, caA, color=CA, lw=1.8, label=lA)
    ax2.plot(x, caB, color=CB, lw=1.8, label=lB)
    ax2.set_ylim(0, None)
    ax2.set_ylabel("Coupon rate, annual (%)")
    ax2.set_title(cfg["titles"][1], loc="left", color=INK, fontsize=12.5,
                  fontweight="bold", pad=8)
    ax2.legend(frameon=False, loc="upper right", labelcolor=INK2)

    # pane 3: monthly coupon delta (A - B), diverging
    ax3.axhline(0, color=AXIS, lw=0.8)
    ax3.fill_between(x, 0, delta_bp, where=delta_bp >= 0, interpolate=True,
                     color=CA, alpha=0.55, linewidth=0)
    ax3.fill_between(x, 0, delta_bp, where=delta_bp <= 0, interpolate=True,
                     color=CRED, alpha=0.55, linewidth=0)
    ax3.plot(x, delta_bp, color=INK2, lw=0.7)
    ax3.set_ylabel(cfg["delta_ylabel"])
    ax3.set_xlabel("Year")
    ax3.set_title(cfg["titles"][2], loc="left", color=INK, fontsize=12.5,
                  fontweight="bold", pad=8)
    ax3.legend(handles=[Patch(color=CA, alpha=0.55, label=cfg["delta_more"][0]),
                        Patch(color=CRED, alpha=0.55, label=cfg["delta_more"][1])],
               frameon=False, loc="upper right", labelcolor=INK2, ncol=2, fontsize=8.5)

    # shared x + proxy marker on every pane
    ax3.xaxis.set_major_locator(YearLocator(5))
    ax3.xaxis.set_major_formatter(DateFormatter("%Y"))
    for ax in (ax1, ax2, ax3):
        ax.axvline(split, color=MUTED, ls=(0, (4, 3)), lw=0.9, alpha=0.7)
        ax.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(AXIS)
        ax.tick_params(colors=MUTED)

    fig.text(0.008, 0.006, cfg["caption"], color=MUTED, fontsize=8)
    return fig


if __name__ == "__main__":
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "font.family": "sans-serif", "font.size": 10,
    })
    figs = [(cfg, build_fig(cfg)) for cfg in CHARTS]
    stamp = datetime.now().strftime("%Y%m%d_%H%M")   # fetched right before writing
    for cfg, fig in figs:
        for path in (os.path.join(ROOT, f"{cfg['name']}.png"),
                     os.path.join(OUTD, f"{stamp}_{cfg['name']}.png")):
            fig.savefig(path, dpi=140, facecolor=SURFACE, bbox_inches="tight")
        print(f"wrote {cfg['name']}.png (+ output/{stamp}_{cfg['name']}.png)")
