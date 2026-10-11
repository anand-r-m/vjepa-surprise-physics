"""EXPLORATORY post-freeze kernel groups (human-approved Q11 onset-aligned specificity; human-requested corrected
frame-rate edit). Never touches the frozen groups' files. Writes kaggle/<group>/{runs.json,kernel-metadata.json}; the
onset group's matches.json is produced by scripts/make_onset_matches.py (not copied from h2_spec_*). Never pushes.

  expl_onset_spec : M1, mid strength, the four spec types, seeds as in the frozen mid runs (lighting_global x3,
                    lighting_local x3, jolt_base x3, zoom_base x1) = 10 half-size runs, members possible, matches =
                    onset-aligned kaggle/expl_onset_spec/matches.json. References are the EXISTING runs: clean
                    possible/impossible (P4_M1_ipdev_clean_s1) for lighting and Delta_viol, and the existing
                    P4_M1_ipdev_base_ref-ref_s1 for jolt/zoom (base_ref does not depend on the event time).
  expl_halve_hold : M1, halve_hold at high strength (on), seed 1, 360 videos; reference = existing clean skip-2 run.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCHES = "/kaggle/working/code/matches.json"
S_PER_VIDEO = 2.54        # M1 fp16, 2 GPUs (same constant as make_p4_runs)
HALF_RUN_H = 0.16         # measured: 32 M1 half-size spec runs, mean wall 0.159 h (0.145 to 0.165), results/raw/h2_spec_*/.../meta.json
FULL_RUN_H = 0.311        # measured: P4_M1_ipdev_clean_s1 (360 videos, same 17 windows as halve_hold), wall
BASE = dict(dataset="ipdev", frame_step=2, precision="fp16", n_gpus=2, model="M1", baselines=True)


def groups():
    onset = []
    for kind, seeds in (("lighting_global", (1, 2, 3)), ("lighting_local", (1, 2, 3)), ("jolt_base", (1, 2, 3)), ("zoom_base", (1,))):
        for s in seeds:
            onset.append(dict(run_id=f"EXPL_M1_ipdev_onset-{kind}-mid_s{s}", edit=dict(name=kind, level="mid", matches=MATCHES),
                              seed=s, members="possible", store_feats=True, **BASE))
    halve = [dict(run_id="EXPL_M1_ipdev_halve_hold-high_s1", edit=dict(name="halve_hold", strength="high"), seed=1,
                  members="all", store_feats=False, **BASE)]
    return {"expl_onset_spec": onset, "expl_halve_hold": halve}


def summarize(g):
    out = {}
    for name, rs in g.items():
        h = sum(HALF_RUN_H if r["members"] == "possible" else FULL_RUN_H for r in rs)
        out[name] = dict(runs=len(rs), half=sum(r["members"] == "possible" for r in rs), full=sum(r["members"] == "all" for r in rs),
                         hours=round(h, 2), model_only_hours=round(sum((180 if r["members"] == "possible" else 360) * S_PER_VIDEO for r in rs) / 3600, 2))
    return out


def write(g):
    for name, rs in g.items():
        d = ROOT / "kaggle" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "runs.json").write_text(json.dumps(dict(group=name, dev_dataset="intphys-dev-npz", runs=rs), indent=1))
        meta = json.loads((ROOT / "kaggle" / "p2_bench" / "kernel-metadata.json").read_text())
        meta["id"] = f"anandrodriguezmenon/vjepa-p4-{name.replace('_', '-')}"
        meta["title"] = f"vjepa-p4-{name.replace('_', '-')}"
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    g = groups()
    write(g)
    for k, v in summarize(g).items():
        print(k, v)
