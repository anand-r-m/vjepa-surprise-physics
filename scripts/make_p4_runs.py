"""Generate the P4 kernel groups for M1 (and M0r controls) from the A1 condition list.
Counts must match notes/GPU_PROJECTION.md: 34 full (360-video) + 31 half (180 possible) M1
conditions + 7 half M0r conditions. Deterministic edits are generated once (seed 1);
seeded edits x3 seeds. Writes kaggle/<group>/{runs.json,kernel-metadata.json}; never pushes.

Strength tables come from configs/edit_params.yaml (bundled by build_kernel.py): copy the FROZEN
values there before building. Specificity groups read kaggle/<group>/matches.json (produced by
scripts/make_matched_strengths.py AFTER freeze) which build_kernel.py bundles."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S_M2 = 5.22              # M2 fp16 2 GPUs, results/raw/p2_m2/results/P2M_M2_dev12_fp16_2gpu_s1/meta.json
S_PER_VIDEO = 2.54        # M1 fp16, 2 GPUs, results/raw/p2_det2/.../P2D2_M1_dev12_fp16_2gpu_A_s1/meta.json
S_IP2 = 2.73             # M1 fp16, IntPhys 2 mp4 loader, 5.46 s/video on 1 GPU (P2D_M1_ip2dbg_fp16_clean_s1/meta.json, wall incl. decode) / 2 GPUs (dev: 5.17 vs 2.54)
N_IP2_MAIN = 1012        # 506 pairs (data/intphys2/extracted/Main/metadata.csv)
MATCHES = "/kaggle/working/code/matches.json"
LEVELS = ("low", "mid", "high")
SEEDS = (1, 2, 3)
BASE = dict(dataset="ipdev", frame_step=2, precision="fp16", n_gpus=2)


def run(rid, model, edit, seed, members, feats=False, **kw):
    r = dict(run_id=rid, model=model, edit=edit, seed=seed, members=members, baselines=True,
             store_feats=feats, **BASE)
    r.update(kw)
    return r


def rid(model, name, tag, seed):
    return f"P4_{model}_ipdev_{name}-{tag}_s{seed}"


def inv(name, strengths=LEVELS, seeds=(1,)):
    return [run(rid("M1", name, st, s), "M1", dict(name=name, strength=st), s, "all") for st in strengths for s in seeds]


def spec(model, kind, levels, seeds):
    return [run(rid(model, kind, lv, s), model, dict(name=kind, level=lv, matches=MATCHES), s, "possible", feats=True)
            for lv in levels for s in seeds]


def clean_groups():
    c = dict(dataset="ipdev", frame_step=2, edit=None, seed=1, members="all", baselines=True, store_feats=True,
             precision="fp16", n_gpus=2)
    g = {}
    g["p4_clean_m1"] = ([dict(run_id="P4_M1_ipdev_clean_s1", model="M1", **c),
                         dict(c, run_id="P4_M1_ipdev_clean-skip4_s1", model="M1", frame_step=4)]
                        + [dict(c, run_id=f"P4_M0r_ipdev_clean-init{i}_s1", model="M0r", init_seed=i, baselines=False, store_feats=False)
                           for i in range(3)])
    g["p4_clean_m2"] = [dict(run_id="P4_M2_ipdev_clean_s1", model="M2", **c)]
    # Q10 B (2026-10-08): M2 rerun with predictor mask_index=0 (now the wrapper default). The run above stays as a documented wrapper deviation.
    g["p4_clean_m2_mi0"] = [dict(run_id="P4_M2_ipdev_clean-mi0_s1", model="M2", **c)]
    return g


def groups():
    g = {}
    g["g2_controls"] = (
        [run(rid("M1", "vflip", "high", 1), "M1", dict(name="vflip", strength="high"), 1, "all", feats=True),
         run(rid("M1", "time_reversal", "high", 1), "M1", dict(name="time_reversal", strength="high"), 1, "all", feats=True),
         run(rid("M1", "hflip", "high", 1), "M1", dict(name="hflip", strength="high"), 1, "all", feats=True)]
        + [run(rid("M0r", n, "high", 1), "M0r", dict(name=n, strength="high"), 1, "possible", init_seed=0, baselines=False)
           for n in ("vflip", "time_reversal")])
    g["h2_spec_a"] = (spec("M1", "lighting_global", LEVELS, SEEDS) + spec("M1", "lighting_local", LEVELS, SEEDS))
    g["h2_spec_b"] = (spec("M1", "jolt_base", LEVELS, SEEDS) + spec("M1", "zoom_base", LEVELS, (1,))
                      + [run(rid("M1", "base_ref", "ref", 1), "M1", dict(name="base_ref"), 1, "possible", feats=True)]
                      + [dict(r, init_seed=0, baselines=False) for r in
                         spec("M0r", "lighting_global", ("mid",), (1,)) + spec("M0r", "lighting_local", ("mid",), (1,))
                         + spec("M0r", "jolt_base", ("mid",), (1,)) + spec("M0r", "zoom_base", ("mid",), (1,))]
                      + [run(rid("M0r", "base_ref", "ref", 1), "M0r", dict(name="base_ref"), 1, "possible", init_seed=0, baselines=False)])
    g["h1_inv_a"] = inv("brightness", LEVELS, SEEDS) + [run(rid("M1", "fps_halve", "high", 1), "M1", dict(name="halve"), 1, "all")]
    g["h1_inv_b"] = inv("noise", LEVELS, SEEDS) + [run(rid("M1", "dither", "on", s), "M1", dict(name="dither"), s, "all") for s in SEEDS]
    g["h1_inv_c"] = inv("blur") + inv("jpeg") + inv("zoom")
    return g


M2_CAP_H = 3.3           # per-kernel GPU-hour cap used for M1 groups (test_counts_match_projection)


def chunk(prefix, runs, cap=M2_CAP_H):
    """Greedy split of an ordered M2 run list into groups <= cap GPU-hours (5.22 s/video), named prefix_a, prefix_b, ..."""
    out, cur, h = [], [], 0.0
    for r in runs:
        d = n_videos(r) * S_M2 / 3600
        if cur and h + d > cap:
            out.append(cur); cur, h = [], 0.0
        cur.append(r); h += d
    if cur:
        out.append(cur)
    return {f"{prefix}_{chr(97 + i)}": c for i, c in enumerate(out)}


def m2(name, edit, seed, members, tag, feats=False):
    return run(rid("M2", name, tag, seed), "M2", edit, seed, members, feats=feats)


def m2_inv(name, strengths, seeds):
    return [m2(name, dict(name=name, strength=st), s, "all", st) for st in strengths for s in seeds]


def m2_groups():
    """M2 edited groups (prereg s8 tiers 2 and 3), GATED: run only if M2 clean (mask_index 0, P4_M2_ipdev_clean-mi0_s1)
    is H1-eligible (>= 80% tie-half, s6). Mirrors the M1 groups. Tier 2 (confirmatory): 7 invariance edits at high
    (brightness/noise x3 seeds, blur, jpeg, zoom, hflip, fps_halve + its skip-4 clean reference), dither x3, H2 mid for
    4 types (+ base_ref), vflip, reversal. Tier 3 (dose-response): low/mid invariance, low/high spec; seed 1 groups (_s1)
    separate from seed 2-3 groups (_s23) so that, if quota is short, seeds 2-3 go to the Colab overflow first (s8)."""
    g = {}
    g["m2_g2_controls"] = [m2(n, dict(name=n, strength="high"), 1, "all", "high", feats=True) for n in ("vflip", "time_reversal", "hflip")]
    g["m2_h2_spec_a"] = (spec("M2", "lighting_global", ("mid",), SEEDS) + spec("M2", "lighting_local", ("mid",), SEEDS))
    g["m2_h2_spec_b"] = (spec("M2", "jolt_base", ("mid",), SEEDS) + spec("M2", "zoom_base", ("mid",), (1,))
                         + [run(rid("M2", "base_ref", "ref", 1), "M2", dict(name="base_ref"), 1, "possible", feats=True)])
    g["m2_h1_inv_a"] = m2_inv("brightness", ("high",), SEEDS) + [
        m2("fps_halve", dict(name="halve"), 1, "all", "high"),
        # skip-4 clean M2 reference for the halving contrast (s3: reference = clean run at skip 4); mirrors M1's p4_clean_m1 run
        dict(run("P4_M2_ipdev_clean-skip4_s1", "M2", None, 1, "all", feats=True), frame_step=4)]
    g["m2_h1_inv_b"] = m2_inv("noise", ("high",), SEEDS) + [m2("dither", dict(name="dither"), s, "all", "on") for s in SEEDS]
    g["m2_h1_inv_c"] = m2_inv("blur", ("high",), (1,)) + m2_inv("jpeg", ("high",), (1,)) + m2_inv("zoom", ("high",), (1,))
    # tier 3: dose-response
    for tag, seeds in (("s1", (1,)), ("s23", (2, 3))):
        inv_runs = []
        for name in ("brightness", "noise", "blur", "jpeg", "zoom"):
            if name in SEEDED_INV_NAMES:
                inv_runs += m2_inv(name, ("low", "mid"), seeds)
            elif tag == "s1":                    # deterministic edits: seed 1 only
                inv_runs += m2_inv(name, ("low", "mid"), (1,))
        spec_runs = []
        for kind in ("lighting_global", "lighting_local", "jolt_base", "zoom_base"):
            if kind == "zoom_base":
                if tag == "s1":
                    spec_runs += spec("M2", kind, ("low", "high"), (1,))
            else:
                spec_runs += spec("M2", kind, ("low", "high"), seeds)
        g.update(chunk(f"m2_dose_inv_{tag}", inv_runs))
        g.update(chunk(f"m2_dose_spec_{tag}", spec_runs))
    return g


SEEDED_INV_NAMES = ("brightness", "noise")


def ip2main_groups():
    """IntPhys 2 Main, M1 only, clean (prereg s8: 'M1 clean accuracy (descriptive)'; no edit, no H2, no M0r/M2 on Main).
    Dataset support is kaggle/ip2main/ip2main_lib.py (bundled only into ip2main_* groups)."""
    return {"ip2main_clean_m1": [dict(run_id="P4_M1_ip2main_clean_s1", model="M1", dataset="ip2main", frame_step=2, edit=None,
                                      seed=1, members="all", baselines=True, store_feats=True, precision="fp16", n_gpus=2)]}


def n_videos(r):
    if r["dataset"] == "ip2main":
        return N_IP2_MAIN if r["members"] == "all" else N_IP2_MAIN // 2
    return 360 if r["members"] == "all" else 180


def sec_per_video(r):
    return S_IP2 if r["dataset"] == "ip2main" else (S_M2 if r["model"] == "M2" else S_PER_VIDEO)


def summarize(g):
    out = {}
    for name, rs in g.items():
        full = sum(1 for r in rs if r["members"] == "all")
        half = len(rs) - full
        h = sum(n_videos(r) * sec_per_video(r) for r in rs) / 3600
        out[name] = dict(runs=len(rs), full=full, half=half, hours=round(h, 2))
    return out


def write(g):
    for name, rs in g.items():
        ip2 = all(r["dataset"] == "ip2main" for r in rs)
        d = ROOT / "kaggle" / name
        d.mkdir(parents=True, exist_ok=True)
        cfg = dict(group=name, ip2_dataset="intphys2", runs=rs) if ip2 else dict(group=name, dev_dataset="intphys-dev-npz", runs=rs)
        (d / "runs.json").write_text(json.dumps(cfg, indent=1))
        meta = json.loads((ROOT / "kaggle" / "p2_bench" / "kernel-metadata.json").read_text())
        meta["id"] = f"anandrodriguezmenon/vjepa-p4-{name.replace('_', '-')}"
        meta["title"] = f"vjepa-p4-{name.replace('_', '-')}"
        if ip2:
            meta["dataset_sources"] = ["anandrodriguezmenon/intphys2"]       # Main/ is already in this private dataset (1012 videos + metadata.csv)
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
        if any(isinstance(r.get("edit"), dict) and "matches" in r["edit"] for r in rs):
            # M2 spec groups reuse the SAME post-freeze matches.json as the M1 spec groups (matching is at M1 input resolution, prereg s4)
            (d / "matches.json").write_bytes((ROOT / "kaggle" / "h2_spec_a" / "matches.json").read_bytes())


if __name__ == "__main__":
    if sys.argv[1:] == ["ip2main"]:          # writes ONLY the ip2main groups; the frozen groups' files are not regenerated
        g = ip2main_groups()
        write(g)
        for k, v in summarize(g).items():
            print(k, v)
        sys.exit(0)
    g = groups()
    g.update(clean_groups())
    g.update(m2_groups())
    write(g)
    s = summarize(g)
    tot = lambda k: sum(v[k] for v in s.values())
    for k, v in s.items():
        print(k, v)
    print("TOTAL", dict(runs=tot("runs"), full=tot("full"), half=tot("half"), hours=round(tot("hours"), 2)))
