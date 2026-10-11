"""F0: method schematic (no numbers). Run: python -m vjepa_study.figures.f0_schematic"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

C_POS, C_IMP, C_ABR, C_ED = "#4C72B0", "#C44E52", "#DD8452", "#55A868"


def _clip(ax, x, y, label, color, w=0.26, h=0.14):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", fc="white", ec=color, lw=2))
    for i in range(4):
        ax.add_patch(plt.Rectangle((x + 0.015 + i * w / 4.2, y + 0.03), w / 5, h - 0.06, fc=color, alpha=0.25, ec=color, lw=0.6))
    ax.text(x + w / 2, y + h + 0.025, label, ha="center", va="bottom", fontsize=8.5, color=color)


def _curve(ax, x0, y0, w, h, ys, color, label=None, ls="-"):
    t = np.linspace(0, 1, len(ys))
    ax.plot(x0 + t * w, y0 + np.asarray(ys) * h, color=color, lw=2, ls=ls, label=label)


def _panel(ax, title, question):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.97, title, ha="center", va="top", fontsize=12, fontweight="bold")
    ax.text(0.5, 0.905, question, ha="center", va="top", fontsize=9, style="italic", wrap=True)


def _axes_box(ax, x0, y0, w, h):
    ax.plot([x0, x0, x0 + w], [y0 + h, y0, y0], color="black", lw=1)
    ax.text(x0 + w / 2, y0 - 0.045, "time", ha="center", va="top", fontsize=8)
    ax.text(x0 - 0.03, y0 + h / 2, "surprise", ha="right", va="center", fontsize=8, rotation=90)


def build(out="paper/figures/f0_schematic.pdf"):
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.6))
    base = np.array([.18, .2, .18, .22, .2, .19, .21, .2, .19, .2])
    spike = base.copy(); spike[5:8] += [.55, .45, .3]
    x0, y0, w, h = 0.16, 0.12, 0.74, 0.28

    # 1 invariance
    ax = axs[0]; _panel(ax, "1  Invariance", "Does a harmless change to the video\nchange which one looks impossible?")
    _clip(ax, 0.06, 0.52, "possible", C_POS); _clip(ax, 0.38, 0.52, "impossible", C_IMP)
    ax.text(0.78, 0.59, "+ same blur, noise,\nbrightness, ... on both", fontsize=8, ha="left", va="center", color=C_ED)
    _axes_box(ax, x0, y0, w, h)
    _curve(ax, x0, y0, w, h, base, C_POS, "possible"); _curve(ax, x0, y0, w, h, spike, C_IMP, "impossible")
    _curve(ax, x0, y0, w, h, base * 1.15, C_POS, ls="--"); _curve(ax, x0, y0, w, h, spike * 1.1, C_IMP, ls="--")
    ax.text(0.5, 0.02, "same verdict before (solid) and after (dashed)?", ha="center", fontsize=8.5)

    # 2 specificity
    ax = axs[1]; _panel(ax, "2  Specificity", "Is surprise about impossible physics,\nor about any sudden change?")
    _clip(ax, 0.06, 0.52, "impossible event", C_IMP); _clip(ax, 0.38, 0.52, "possible + abrupt\n(light flash, camera jolt)", C_ABR)
    ax.text(0.7, 0.59, "matched pixel\nchange size", fontsize=8, ha="left", va="center")
    _axes_box(ax, x0, y0, w, h)
    _curve(ax, x0, y0, w, h, spike, C_IMP, "violation"); _curve(ax, x0, y0, w, h, base + np.r_[np.zeros(5), [.4, .3, .15, .1, .05]], C_ABR, "abrupt, possible")
    ax.text(0.5, 0.02, "does the model tell them apart?", ha="center", fontsize=8.5)

    # 3 positive controls
    ax = axs[2]; _panel(ax, "3  Positive controls", "If we make the physics impossible,\ndoes surprise go up?")
    _clip(ax, 0.06, 0.52, "original", C_POS); _clip(ax, 0.38, 0.52, "upside-down /\nplayed backwards", C_IMP)
    _axes_box(ax, x0, y0, w, h)
    _curve(ax, x0, y0, w, h, base, C_POS, "original"); _curve(ax, x0, y0, w, h, base * 2.1, C_IMP, "edited")
    ax.text(0.5, 0.02, "checks that the pipeline can see violations", ha="center", fontsize=8.5)

    for a in axs:
        a.legend(loc="upper left", bbox_to_anchor=(0.14, 0.43), fontsize=7.5, frameon=False)
    fig.suptitle("Violation-of-expectation: a model is 'surprised' by impossible videos. What is that surprise tracking?", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out); plt.close(fig)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "paper/figures/f0_schematic.pdf"))
