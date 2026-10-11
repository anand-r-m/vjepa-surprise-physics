"""Shared helpers for the paper table/figure scripts (scripts/figs/*.py).

Rules enforced here:
 * numbers in table cells / plot annotations come from results/VERIFIED.json via V()/val()/ci(); every key touched
   is recorded and written to the item's sidecar JSON, with its status (verified / mismatch / info-only / pending);
 * keys that do not exist are recorded as missing and rendered as a 'pending' marker, never invented;
 * per-pair / per-video plotted data come from results/raw (via a symlink runs dir) or results/analysis json files,
   and the script records every input file it opened (I()).
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "paper" / "tables"
FIGS = ROOT / "paper" / "figures"
RUNS_DIR = Path(os.path.expanduser("~/.cache/claude-tmp/figs_runs"))   # symlinks to results/raw/*/results/P*

# Okabe-Ito (colourblind safe). Greyscale legibility is carried by hatch / marker / linestyle, never by hue alone.
C = dict(M1="#0072B2", M2="#D55E00", M0r="#6b7280", B1="#E69F00", B2="#009E73", B3="#CC79A7", ink="#222222", grid="#d9d9d9")
HATCH = dict(M1="", M2="//", B1="xx", B2="..", M0r="\\\\", B3="--")
MARK = dict(M1="o", M2="s", B1="^", B2="D", M0r="v", B3="P")
LS = dict(M1="-", M2="--", B1=":", B2="-.", M0r=(0, (1, 1)))
NAME = dict(M1="V-JEPA ViT-L (M1)", M2="V-JEPA 2 (M2, descr.)", B1="Frame-diff (B1)", B2="Copy-last (B2)",
            M0r="Random init (M0r)", B3="Target-feat. (B3)")

_V = None
_used: dict = {}
_missing: set = set()
_inputs: set = set()


def verified() -> dict:
    global _V
    if _V is None:
        d = json.loads((ROOT / "results" / "VERIFIED.json").read_text())
        _V = {}
        for e in d["entries"]:
            _V.setdefault(e["key"], e)
        _inputs.add("results/VERIFIED.json")
    return _V


def V(key):
    """Entry for key, or None (recorded as missing). Records usage."""
    e = verified().get(key)
    if e is None:
        _missing.add(key)
        return None
    _used[key] = e["status"]
    return e


def has(key) -> bool:
    e = verified().get(key)
    return e is not None and e.get("value") is not None and e["status"] != "pending"


def val(key):
    e = V(key)
    if e is None or e.get("value") is None or e["status"] == "pending":
        return None
    return e["value"]


def ci(key, ckey=None):
    """95% CI: entry['ci'], else the value of `ckey` (a separate *_ci key holding a list)."""
    e = V(key)
    if e is not None and e.get("ci"):
        return e["ci"]
    if ckey:
        v = val(ckey)
        return v if isinstance(v, list) else None
    return None


def status(key):
    e = verified().get(key)
    return None if e is None else e["status"]


def I(path):
    """Record an input file (relative to repo) and return its absolute Path."""
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    _inputs.add(str(p.relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p))
    return p


def jload(path):
    return json.loads(I(path).read_text())


def write_sidecar(item, script, outputs, extra=None):
    out = dict(item=item, script=script, outputs=outputs, generated=datetime.date.today().isoformat(),
               verified_keys_used={k: _used[k] for k in sorted(_used)},
               verified_keys_missing=sorted(_missing), input_files=sorted(_inputs))
    if extra:
        out.update(extra)
    p = ROOT / (outputs[0] if isinstance(outputs, list) else outputs)
    p = p.with_suffix(".json") if p.suffix != ".json" else p
    p.write_text(json.dumps(out, indent=1))
    return p


# ------------------------------------------------------------------ LaTeX cell formatting
PEND = r"\textit{pend.}"


def rhu(v, nd):
    """Round half up (away from zero on the stored decimal value) to nd decimals; one rule for the whole paper."""
    from decimal import Decimal, ROUND_HALF_UP
    return Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-nd), ROUND_HALF_UP)


def f(v, nd=1, signed=False):
    if v is None:
        return PEND
    q = rhu(v, nd)
    s = f"{q:+f}" if signed else f"{q:f}"
    return s.replace("-", "$-$")


def fci(v, c, nd=1, signed=False):
    if v is None:
        return PEND
    if not c:
        return f(v, nd, signed)
    return f"{f(v, nd, signed)} [{f(c[0], nd)}, {f(c[1], nd)}]"


def fp(p):
    if p is None:
        return PEND
    if p < 0.001:
        return "$<$0.001"
    return f"{p:.3f}" if p < 0.1 else f"{p:.2f}"


def write_tex(name, text):
    TABLES.mkdir(parents=True, exist_ok=True)
    p = TABLES / name
    p.write_text(text)
    return p


# ------------------------------------------------------------------ matplotlib setup
def mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5, "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#555555", "axes.linewidth": 0.6, "axes.grid": True, "grid.color": C["grid"], "grid.linewidth": 0.4,
        "axes.axisbelow": True, "lines.linewidth": 1.2, "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
    return plt


def pending_note(ax, text="pending", **kw):
    ax.text(0.5, 0.5, text, transform=ax.transAxes, ha="center", va="center", fontsize=8, color="#555555",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", ls="--"), **kw)


# ------------------------------------------------------------------ per-pair H2 arrays (frozen driver functions on the raw runs)
def h2_arrays(models=("M1",), level="mid"):
    """Return {name: dict(dv, da{type:(seeds,pairs)}, tau, s_clean_med)} for the event-aligned max primary variant.
    Mirrors scripts/run_analysis.h2_stage (frozen) so the plotted arrays are the analysed ones. Inputs: results/raw via RUNS_DIR."""
    import sys
    import numpy as np
    sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
    import run_analysis as RA
    from vjepa_study.analysis import prereg as P
    R = RA.Runs(RUNS_DIR)
    mp = I("kaggle/h2_spec_a/matches.json")
    matches = json.loads(mp.read_text())
    clean = {m: R.need(R.clean_id(m)) for m in models}
    _inputs.add("results/raw/*/results/P4_<M>_ipdev_clean*/surprise.npz, ..._<edit>-mid_s<k>/surprise.npz (via symlink dir)")
    px = P.pair_index(clean[models[0]])
    t_on, late = RA.event_times(matches, px["pair_ids"])
    keep = ~late
    tv_of = lambda d, p: P._per_video_t(d, p, t_on)
    out = {}
    for m in models:
        dc = clean[m]
        for key, name in [("S", m)] + [(b, b) for b in ("B1", "B2", "B3") if b in dc and m == models[0]]:
            tau = P.tau_m(P.video_scores(dc, key, "max", None, None))
            vs = lambda d, p: P.video_scores(d, key, "max", tv_of(d, p), None)
            s_clean = vs(dc, px)
            s_pos, s_imp = s_clean[px["pos"]], s_clean[px["imp"]]
            da = {}
            for t in RA.SPEC_TYPES:
                rows = []
                for s in ((1, 2, 3) if t in RA.SEEDED else (1,)):
                    de = R.need(R.id(m, t, level, s)); pe = P.pair_index(de)
                    se = vs(de, pe)[pe["pos"]]
                    if t in ("jolt_base", "zoom_base"):
                        dr = R.need(R.id(m, "base_ref", "ref", 1)); pr = P.pair_index(dr)
                        sr = vs(dr, pr)[pr["pos"]]
                    else:
                        sr = s_pos
                    rows.append(se - sr)
                da[t] = np.stack(rows)[:, keep]
            out[name] = dict(dv=(s_imp - s_pos)[keep], da=da, tau=tau, med=float(np.median(P.video_scores(dc, key, "max", None, None))),
                             pair_ids=px["pair_ids"][keep], block=px["block"][keep], s_pos=s_pos[keep], s_imp=s_imp[keep])
    return out
