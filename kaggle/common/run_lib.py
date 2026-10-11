"""Kaggle job pattern (docs/COMPUTE.md): runs.json -> per-run folders with surprise.npz,
meta.json, log.txt; skip-if-exists checkpointing; everything pinned in meta.json.

Run config (one dict in runs.json["runs"]):
  run_id, model ("M1"|"M0r"|"M2"|"M3"), dataset ("ipdev"|"ip2debug"),
  subset: {"scenes": ["O1/01", ...]} | {"every": k, "n": n} (ip2 pairs) | omitted = all,
  members: "all" | "possible", frame_step (default 2), seed (default 1),
  edit: null | {"name": <edits.EDIT_FUNCS name | "dither" | "halve" | "base_ref" |
                 lighting_global|lighting_local|jolt_base|zoom_base>, "strength": low|mid|high (registry
                 edits) | "level": low|mid|high + "matches": path (matched edits)},
  baselines: true (B1/B2/B3 stored next to the model's S), store_feats: true.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import platform
import subprocess
import queue
import sys
import threading
import time
import traceback
from pathlib import Path

import numpy as np

from vjepa_study import amend, data, edits, schema
from vjepa_study.analysis import baselines as bl

CTX = (2, 4, 6, 8, 10)


# ------------------------------------------------------------------ environment / data
def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # noqa
        return f"ERR {e}"


def env_info(bundle_info=None):
    info = dict(python=sys.version.split()[0], platform=platform.platform(), bundle=bundle_info or {})
    try:
        import torch
        info.update(torch=torch.__version__, cuda=torch.version.cuda, cuda_available=torch.cuda.is_available())
        if torch.cuda.is_available():
            info["gpus"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    except Exception as e:  # noqa
        info["torch_error"] = str(e)
    for pkg in ("numpy", "opencv-python-headless", "timm", "einops", "scipy", "transformers"):
        info[pkg] = sh(f"{sys.executable} -m pip show {pkg} 2>/dev/null | grep -i '^version' | cut -d' ' -f2")
    return info


def sha256_file(path, block=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ensure_dev(input_root, work, scenes=None):
    """Return path of the extracted `dev` dir. Accepts an extracted tree or dev.tar.gz
    (extracts only scene/ PNGs and status.json, optionally only for `scenes`)."""
    input_root, work = Path(input_root), Path(work)
    if data.is_npz_root(input_root):
        return input_root
    for cand in (input_root / "dev", input_root / "extracted" / "dev"):
        if (cand / "O1").exists():
            return cand
    tars = list(input_root.rglob("dev.tar.gz")) or list(input_root.rglob("*.tar.gz"))
    if not tars:
        raise FileNotFoundError(f"no IntPhys dev under {input_root}")
    dest = work / "intphys_dev"
    tag = "all" if scenes is None else hashlib.md5(",".join(sorted(scenes)).encode()).hexdigest()
    marker = dest / f".done_{tag}"
    if not marker.exists():
        dest.mkdir(parents=True, exist_ok=True)
        pats = ["dev/*/*/*/scene/*.png", "dev/*/*/*/status.json"] if scenes is None else \
            [f"dev/{sc}/*/{x}" for sc in scenes for x in ("scene/*.png", "status.json")]
        cmd = ["tar", "xzf", str(tars[0]), "-C", str(dest), "--wildcards", *pats]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"tar failed: {r.stderr[-500:]}")
        marker.write_text("ok")
    return dest / "dev"


def verify_dev_npz(root, scenes=None, n_blocks=3, n_scenes=30, min_bytes=500_000, log=print):
    """Fail fast (clear message) unless every <block>_<scene>_<k>.npz exists with plausible size
    and a few random files load with 100x288x288x3 uint8 frames."""
    root = Path(root)
    want = [(f"O{b}", f"{s:02d}") for b in range(1, n_blocks + 1) for s in range(1, n_scenes + 1)]
    if scenes is not None:
        want = [tuple(x.split("/")) for x in scenes]
    missing, small = [], []
    for b, sc in want:
        for k in (1, 2, 3, 4):
            f = root / f"{b}_{sc}_{k}.npz"
            if not f.exists():
                missing.append(f.name)
            elif f.stat().st_size < min_bytes:
                small.append(f.name)
    if missing or small:
        raise FileNotFoundError(f"intphys-dev-npz incomplete under {root}: {len(missing)} missing "
                                f"(e.g. {missing[:5]}), {len(small)} too small (e.g. {small[:5]})")
    rng = np.random.default_rng(0)
    for i in rng.choice(len(want) * 4, size=min(3, len(want) * 4), replace=False):
        b, sc = want[i // 4]
        with np.load(root / f"{b}_{sc}_{i % 4 + 1}.npz") as z:
            fr = z["frames"]
            assert fr.dtype == np.uint8 and fr.ndim == 4 and fr.shape[1:] == (288, 288, 3), fr.shape
    log(f"verify_dev_npz OK: {len(want) * 4} files under {root}")


def find_ip2(input_root):
    input_root = Path(input_root)
    for cand in (input_root / "Debug", input_root / "extracted" / "Debug"):
        if cand.exists():
            return cand.parent
    hits = list(input_root.rglob("metadata.csv"))
    if hits:
        return hits[0].parent.parent
    raise FileNotFoundError(f"no IntPhys2 under {input_root}")


# ------------------------------------------------------------------ items
def iter_items(run, dev_root=None, ip2_root=None):
    """Yield dict(video_id,label(1=impossible),pair_id,scene_id,block,frames) for a run."""
    fs = run.get("frame_step", 2)
    members = run.get("members", "all")
    sub = run.get("subset") or {}
    if run["dataset"] == "ipdev":
        scenes = [tuple(s.split("/")) for s in sub["scenes"]] if "scenes" in sub else data.list_dev_scenes(dev_root)
        for block, scene in scenes:
            f4, lab, ids = data.load_dev_quadruplet(dev_root, block, scene)
            for k, (ip, ii) in enumerate(data.make_pairs(f4, lab, fs)):
                pid = f"{block}/{scene}/p{k}"
                for idx, label in ((ip, 0), (ii, 1)):
                    if members == "possible" and label == 1:
                        continue
                    yield dict(video_id=ids[idx], label=label, pair_id=pid, scene_id=f"{block}/{scene}",
                               block=block, frames=f4[idx])
    elif run["dataset"] == "ip2debug":
        split = Path(ip2_root) / "Debug"
        pairs = data.ip2_pairs(split)
        pairs = pairs[:: sub.get("every", 1)][: sub.get("n", len(pairs))]
        for pos, imp, scene, k in pairs:
            for row, label in ((pos, 0), (imp, 1)):
                if members == "possible" and label == 1:
                    continue
                fr = data.load_ip2_video(split, row, max_frames=100, stride=4)   # 60 fps -> 15 fps, 100 frames
                yield dict(video_id=row["name"], label=label, pair_id=f"ip2/{scene}/{k}", scene_id=f"ip2/{scene}",
                           block="IP2", frames=fr)
    else:
        raise KeyError(run["dataset"])


def apply_run_edit(item, edit, seed, matches=None):
    """Return (frames, frame_step_multiplier). Edits are applied to both pair members with the
    same seed (identical params, PROJECT_SPEC section 8)."""
    f = item["frames"]
    if not edit:
        return f, 1
    n = edit["name"]
    if n == "halve":
        return f, 2
    if n == "dither":
        return amend.dither(f, dict(amount=1.0), seed), 1
    if n == "base_ref":
        return amend.base_ref(f), 1
    if n in amend.KINDS:
        pm = matches["pairs"][item["pair_id"]] if "pairs" in matches else matches[item["pair_id"]]
        m = pm[n] if "levels" in pm[n] else pm[n][str(seed)]       # seeded kinds are matched per seed
        ev = pm["event"]
        ed, _ = amend.apply_matched(n, f, m, edit["level"], seed, ev["t_on"], ev["t_off"])
        return ed, 1
    p = edits.params_for(n, edit["strength"])
    return edits.EDIT_FUNCS[n](f, p, seed), 1


def _is_det(name):
    try:
        return amend.is_deterministic(name)
    except KeyError:
        return False


# ------------------------------------------------------------------ one run
def run_one(run, model, out_root, dev_root=None, ip2_root=None, log=print, base_meta=None):
    out = Path(out_root) / run["run_id"]
    if (out / "surprise.npz").exists():
        log(f"[skip] {run['run_id']} exists")
        return "skipped"
    out.mkdir(parents=True, exist_ok=True)
    lines = []

    def L(*a):
        s = " ".join(str(x) for x in a)
        lines.append(s)
        log(s)
        (out / "log.txt").write_text("\n".join(lines) + "\n")

    seed = run.get("seed", 1)
    edit = run.get("edit")
    # deterministic edits are run once (seed 1); other seeds are recorded as identical by construction
    if edit and seed != 1 and _is_det(edit["name"]):
        ref_id = run.get("alias_of", run["run_id"].rsplit("_s", 1)[0] + "_s1")
        (out / "meta.json").write_text(json.dumps(dict(run=run, status="identical_by_construction", of=ref_id), indent=1))
        L(f"{run['run_id']}: deterministic edit {edit['name']} identical to {ref_id}; not recomputed")
        return "alias"
    matches = json.load(open(run["edit"]["matches"])) if edit and edit.get("matches") else None
    t0 = time.time()
    fs0 = run.get("frame_step", 2)
    models = list(model) if isinstance(model, (list, tuple)) else [model]
    lock = threading.Lock()
    state = dict(n_done=0, t_model=0.0)

    def proc(item, mdl):
        frames, mult = apply_run_edit(item, edit, seed, matches)
        tm = time.time()
        r = mdl.surprise(frames, frame_step=fs0 * mult, ctx=CTX)
        dt = time.time() - tm
        S = r["S"]
        if not np.isfinite(S).all():
            raise FloatingPointError(f"non-finite surprise in {item['video_id']}")
        out = dict(S=S, feats=r.get("target_feats"), item={k: v for k, v in item.items() if k != "frames"},
                   hash=amend.frame_hash(frames), B={})
        if run.get("baselines", True):
            sub = amend.to_model_res(frames[r["idx"]], getattr(mdl, "res", 224))   # baselines see the model's own preprocessed frames (MJ2)
            out["B"]["B1"] = bl.b1_windows(sub, CTX)
            out["B"]["B2"] = bl.b2_windows(sub, CTX)
            if r.get("target_feats") is not None:
                out["B"]["B3"] = bl.b3_windows(r["target_feats"].astype(np.float32), CTX)
        with lock:
            state["n_done"] += 1
            state["t_model"] += dt
            L(f"[{state['n_done']}] {item['video_id']} dev={getattr(mdl, 'device', '')} windows={S.shape[0]} "
              f"S[min,mean,max]=({S.min():.4f},{S.mean():.4f},{S.max():.4f}) elapsed={time.time()-t0:.1f}s")
        return out

    results, errors = {}, []
    # FIXED video->GPU assignment (item i -> worker i % n_gpus): deterministic, so a re-run puts
    # every video on the same device with the same batch composition.
    nw = len(models)
    qs = [queue.Queue(maxsize=2) for _ in range(nw)]

    def worker(mdl, qq):
        while True:
            got = qq.get()
            if got is None:
                return
            i, item = got
            try:
                results[i] = proc(item, mdl)
            except Exception:
                errors.append(traceback.format_exc())
    threads = [threading.Thread(target=worker, args=(m, qq), daemon=True) for m, qq in zip(models, qs)]
    for t in threads:
        t.start()
    n = 0
    for i, item in enumerate(iter_items(run, dev_root, ip2_root)):
        if errors:
            break
        qs[i % nw].put((i, item))
        n += 1
    for qq in qs:
        qq.put(None)
    for t in threads:
        t.join()
    if errors:
        raise RuntimeError(errors[0])
    order = [results[i] for i in range(n)]
    t_model = state["t_model"]
    ids = [o["item"]["video_id"] for o in order]; labels = [o["item"]["label"] for o in order]
    pairs = [o["item"]["pair_id"] for o in order]; scenes = [o["item"]["scene_id"] for o in order]
    blocks = [o["item"]["block"] for o in order]; hashes = [o["hash"] for o in order]
    S_list = [o["S"] for o in order]; F_list = [o["feats"] for o in order]
    B = {k: [o["B"][k] for o in order if k in o["B"]] for k in ("B1", "B2", "B3")}
    bsel = {k: v for k, v in B.items() if len(v) == n}
    schema.save_run(out / "surprise.npz", ids, S_list, F_list if run.get("store_feats", True) else None, CTX,
                    baselines=bsel, label=np.array(labels), pair_id=np.array(pairs), scene_id=np.array(scenes),
                    block=np.array(blocks), video_hash=np.array(hashes))
    wall = time.time() - t0
    meta = dict(run=run, status="done", n_videos=n, n_gpus=len(models), precision=run.get('precision', 'fp16'), device_assignment='i % n_gpus', wall_s=wall, model_s=t_model,
                sec_per_video=wall / max(n, 1), model_sec_per_video=t_model / max(n, 1),   # wall-clock per video (all GPUs) / summed GPU-seconds per video
                
                start_utc=datetime.datetime.utcfromtimestamp(t0).isoformat() + "Z",
                end_utc=datetime.datetime.utcnow().isoformat() + "Z", **(base_meta or {}))
    (out / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
    L(f"done {run['run_id']} n={n} wall={wall:.1f}s model={t_model:.1f}s")
    return "done"


# ------------------------------------------------------------------ driver
def main(runs_json, out_root, input_root="/kaggle/input", work="/kaggle/working", build_model=None,
         bundle_info=None, log=print):
    """build_model(model_name, run) -> wrapper (cached per model name by this driver)."""
    cfg = json.load(open(runs_json))
    runs = cfg["runs"]
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    env = env_info(bundle_info)
    (out_root / "env.json").write_text(json.dumps(dict(env=env, kernel_cfg={k: v for k, v in cfg.items() if k != "runs"}), indent=1))
    scenes = sorted({s for r in runs if r["dataset"] == "ipdev" for s in (r.get("subset") or {}).get("scenes", ["__all__"])})
    dev_root = ip2_root = None
    if any(r["dataset"] == "ipdev" for r in runs):
        dev_root = ensure_dev(Path(cfg.get("dev_path") or Path(input_root) / cfg.get("dev_dataset", "intphys-dev")), work,
                              None if "__all__" in scenes else scenes)
    if dev_root is not None and data.is_npz_root(dev_root):
        verify_dev_npz(dev_root, None if "__all__" in scenes else scenes, log=log)
    if any(r["dataset"] == "ip2debug" for r in runs):
        ip2_root = find_ip2(Path(cfg.get("ip2_path") or Path(input_root) / cfg.get("ip2_dataset", "intphys2")))
    cache, status = {}, {}
    for run in runs:
        try:
            key = (run["model"], run.get("init_seed"), run.get("precision", "fp16"), run.get("n_gpus", 1))
            if key not in cache:
                cache.clear()                      # keep one model set resident (GPU memory)
                try:
                    import torch, gc
                    gc.collect(); torch.cuda.empty_cache()
                except Exception:
                    pass
                t = time.time()
                cache[key] = build_model(run["model"], run)       # -> list of wrappers, one per GPU
                log(f"model {key} built in {time.time()-t:.1f}s")
            ms = cache[key]
            base_meta = dict(env=env, model_info=[getattr(m, "info", {}) for m in ms])
            status[run["run_id"]] = run_one(run, ms, out_root, dev_root, ip2_root, log, base_meta)
        except Exception:
            status[run["run_id"]] = "FAILED"
            tb = traceback.format_exc()
            log(tb)
            d = out_root / run["run_id"]
            d.mkdir(parents=True, exist_ok=True)
            (d / "error.txt").write_text(tb)
    (out_root / "status.json").write_text(json.dumps(status, indent=1))
    return status
