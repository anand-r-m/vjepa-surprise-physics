"""Independent recomputation of released-model IntPhys dev pairwise accuracy from raw surprises.
numpy/scipy only for analysis; PIL used only to decode PNGs for the pixel pairing rule; zip+pickle parsed by hand
(no torch). Raw data: external/jepa-intuitive-physics/data_intphys.tar.gz (extracted to $RAW_DIR)."""
import os, sys, json, glob, pickle, zipfile, tarfile, collections
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAR = f"{ROOT}/external/jepa-intuitive-physics/data_intphys.tar.gz"
RAW = os.environ.get("RAW_DIR", f"{ROOT}/scratch_data/verify_released_raw")
DEV = f"{ROOT}/data/intphys_dev/extracted/dev"
BLOCKS = ["O1", "O2", "O3"]

def extract():
    if os.path.isdir(f"{RAW}/data_intphys"): return
    os.makedirs(RAW, exist_ok=True)
    with tarfile.open(TAR) as t:
        for m in t:
            b = os.path.basename(m.name)
            if b.startswith("._") or b == ".DS_Store": continue
            if "/intphys/" in m.name or m.isdir():
                t.extract(m, RAW)

# ---- minimal torch .pth reader (numpy only)
class _Storage:
    def __init__(self, dtype): self.dtype = dtype; self.arr = None
_DT = {"FloatStorage": np.float32, "DoubleStorage": np.float64, "LongStorage": np.int64, "HalfStorage": np.float16, "IntStorage": np.int32, "BoolStorage": np.bool_}
def load_pth(path):
    z = zipfile.ZipFile(path); names = z.namelist()
    pk = [n for n in names if n.endswith("data.pkl")][0]; pre = pk[:-len("data.pkl")]
    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if name in _DT: return name
            if name == "_rebuild_tensor_v2":
                def rb(st, off, size, stride, *a):
                    arr = np.frombuffer(z.read(f"{pre}data/{st[0]}"), dtype=st[1])
                    return np.lib.stride_tricks.as_strided(arr[off:], shape=tuple(size), strides=tuple(s*arr.itemsize for s in stride)).copy()
                return rb
            if name == "OrderedDict": return collections.OrderedDict
            return super().find_class(mod, name)
        def persistent_load(self, pid):
            return (pid[2], _DT[pid[1]])  # (key, dtype)
    return U(z.open(pk)).load()

def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z*z/n; c = (p + z*z/(2*n)) / d; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return [float(c-h), float(c+h)]

def load_dev():
    """Return {block: [(scene, labels[4], bps[3], matches)]}, plus counts."""
    out = {}
    for b in BLOCKS:
        scenes = sorted(os.listdir(f"{DEV}/{b}")); rows = []
        for s in scenes:
            labs, vids = [], []
            for v in [1, 2, 3, 4]:
                labs.append(bool(json.load(open(f"{DEV}/{b}/{s}/{v}/status.json"))["header"]["is_possible"]))
            fr = sorted(os.listdir(f"{DEV}/{b}/{s}/1/scene"))[0:98:2]  # frame_step 2, 49 frames (num_frames=99//2, clip len 98>90 -> start 0)
            T = len(fr)
            def load(v): return np.stack([np.asarray(Image.open(f"{DEV}/{b}/{s}/{v}/scene/{f}")).astype(np.int32) for f in fr])
            V = [load(v) for v in [1, 2, 3, 4]]
            bps = []
            for k in (1, 2, 3):
                d = (V[0] - V[k]).reshape(T, -1).sum(1)   # same quantity as released: sum over C,H,W per frame
                nz = np.nonzero(d != 0)[0]
                bps.append(int(nz[0]) if len(nz) else T)
            a = int(np.argmax(bps))
            matches = [[0,1],[2,3]] if a == 0 else ([[0,2],[1,3]] if a == 1 else [[0,3],[1,2]])
            rows.append(dict(scene=s, labels=labs, bps=bps, matches=matches, T=T))
        out[b] = rows
    return out

def pair_accuracy(losses, labels, tol=1e-4):
    """losses [N,5,W]; rows 2i,2i+1 form pair i (one possible, one impossible)."""
    f = losses.min(1)   # min over context lengths -> [N, W]
    res = {}
    for agg, fn in (("mean", lambda x: x.mean(1)), ("max", lambda x: x.max(1))):
        s = fn(f)
        P, I = [], []
        for i in range(0, len(s), 2):
            a, b = i, i+1
            p, q = (a, b) if labels[a] == 1 else (b, a)
            assert labels[p] == 1 and labels[q] == 0
            P.append(s[p]); I.append(s[q])
        P = np.array(P); I = np.array(I); dlt = I - P
        strict = (P < I)
        res[agg] = dict(strict=strict, tie=np.abs(dlt) <= tol)
    return res

def main():
    extract()
    dev = load_dev()
    n_vid = sum(len(r)*4 for r in dev.values()); n_quad = sum(len(r) for r in dev.values())
    n_possible = sum(sum(r["labels"]) for rows in dev.values() for r in rows)
    bad_q = [(b, r["scene"]) for b, rows in dev.items() for r in rows if sum(r["labels"]) != 2]
    # pair validity under the pixel rule: each matched pair must contain one possible, one impossible
    pair_bad = [(b, r["scene"]) for b, rows in dev.items() for r in rows for m in r["matches"] if sum(r["labels"][i] for i in m) != 1]
    fallback = [(b, r["scene"], r["bps"]) for b, rows in dev.items() for r in rows if max(r["bps"]) >= r["T"]]
    ties_bp = [(b, r["scene"], r["bps"]) for b, rows in dev.items() for r in rows if sorted(r["bps"])[-1] == sorted(r["bps"])[-2]]
    struct = dict(n_videos=n_vid, n_quadruplets=n_quad, n_pairs=2*n_quad, n_possible_videos=int(n_possible),
                  per_block_quadruplets={b: len(r) for b, r in dev.items()},
                  quadruplets_not_2_possible=bad_q, pixel_pairs_not_1p1i=pair_bad,
                  quads_with_no_pixel_divergence_fallback=fallback, quads_with_tied_top_breakpoint=ties_bp)

    models = ["vit-l-rope-vm2m", "vit-l-rope-howto", "vit-h-rope-vm2m", "videomaev2_g"] + [f"vit-l-rope-random-{i}" for i in range(20)]
    results = {}; label_check = {}
    for m in models:
        per = {}
        for b in BLOCKS:
            d = load_pth(f"{RAW}/data_intphys/{m}/intphys/raw_surprises/{b}_16frames.pth")
            L = d["losses"].astype(np.float32); lab = d["labels"]
            assert d["context_lengths"] == [2,4,6,8,10] and d["frame_step"] == 2, (m, b)
            assert L.shape == (120, 5, 17) and np.isfinite(L).all(), (m, b, L.shape)
            per[b] = (pair_accuracy(L, lab), lab)
            # label-sequence check: rows within each quadruplet pair-block follow released rule, scene order is rank-interleaved (world 6)
            ws_ok = []
            for W in (1, 2, 3, 5, 6, 10, 15, 30):
                exp = []
                for r in range(W):
                    for si in range(r, 30, W):
                        sc = dev[b][si]
                        for mt in sc["matches"]:
                            exp += [int(sc["labels"][i]) for i in mt]
                if np.array_equal(np.array(exp), lab.astype(int)): ws_ok.append(W)
            lab4 = [tuple(int(x) for x in lab[i:i+4]) for i in range(0, 120, 4)]
            exp4 = [tuple(int(sc["labels"][i]) for mt in sc["matches"] for i in mt) for sc in dev[b]]
            label_check.setdefault(m, {})[b] = dict(world_sizes=ws_ok, quad_label_multiset_equal=sorted(lab4) == sorted(exp4))
        results[m] = {}
        for agg in ("mean", "max"):
            rec = {}
            allk = alln = allt = 0; allhalf = 0.0
            for b in BLOCKS:
                st = per[b][0][agg]["strict"]; tie = per[b][0][agg]["tie"]
                k, n = int(st.sum()), len(st)
                # tie-aware: |dS|<=1e-4 counts 0.5, otherwise strict
                score = float(np.where(tie, 0.5, st).sum())
                rec[b] = dict(n_pairs=n, k_correct_strict=k, acc_strict=k/n, wilson95=wilson(k, n), n_ties_tol=int(tie.sum()), acc_tie_half=score/n)
                allk += k; alln += n; allt += int(tie.sum()); allhalf += score
            rec["overall"] = dict(n_pairs=alln, k_correct_strict=allk, acc_strict=allk/alln, wilson95=wilson(allk, alln), n_ties_tol=allt, acc_tie_half=allhalf/alln)
            results[m][agg] = rec
    # random-control summary
    rnd = [m for m in models if "random" in m]
    summ = {}
    for agg in ("mean", "max"):
        accs = np.array([results[m][agg]["overall"]["acc_strict"] for m in rnd])
        summ[agg] = dict(n_models=len(rnd), mean_acc=float(accs.mean()), min=float(accs.min()), max=float(accs.max()), sd=float(accs.std(ddof=1)))
    # cross-check vs released performance.csv "Filtered" rows
    cmp = {}
    for m in models:
        rows = [l.strip().split(";") for l in open(f"{RAW}/data_intphys/{m}/intphys/performance.csv")]
        hdr = rows[0]; ia, ix = hdr.index("Relative Accuracy (avg)"), hdr.index("Relative Accuracy (max)")
        f = {r[0]: (float(r[ia]), float(r[ix])) for r in rows[1:] if r[1] == "Filtered"}
        cmp[m] = {b: dict(csv_mean=f[b][0], csv_max=f[b][1], mine_mean=100*results[m]["mean"][b]["acc_strict"], mine_max=100*results[m]["max"][b]["acc_strict"]) for b in BLOCKS}
    maxdiff = max(abs(v[f"csv_{a}"] - v[f"mine_{a}"]) for m in cmp for v in cmp[m].values() for a in ("mean", "max"))
    out = dict(structure=struct, label_order_reproduced_by_pixel_rule_for_world_sizes=label_check, results=results, random_control_summary=summ,
               csv_crosscheck=cmp, csv_crosscheck_max_abs_diff_pct=maxdiff,
               rule=("pairs = released rule: bp_k=first sampled frame (every 2nd of first 98, 49 frames) where video1 differs from video k+1; "
                     "argmax(bps) selects matching [[0,1],[2,3]]/[[0,2],[1,3]]/[[0,3],[1,2]]; surprise rows are stored per pair as consecutive rows; "
                     "correct iff S(possible) < S(impossible) strictly; S = agg_over_17_windows(min_over_5_contexts)"))
    json.dump(out, open(f"{ROOT}/verify/released_dev_accuracy.json", "w"), indent=1)
    print(json.dumps(struct, indent=1)); print("label check", {m: (sorted({tuple(v["world_sizes"]) for v in x.values()}), all(v["quad_label_multiset_equal"] for v in x.values())) for m, x in label_check.items()})
    print("csv diffs>1e-3:", [(m, b, a) for m, v in cmp.items() for b, x in v.items() for a in ("mean","max") if abs(x["csv_"+a]-x["mine_"+a]) > 1e-3] if False else "")
    for m in models[:4] + ["vit-l-rope-random-0"]:
        for agg in ("mean", "max"):
            r = results[m][agg]
            print(m, agg, {b: (round(100*r[b]["acc_strict"], 2), r[b]["n_pairs"]) for b in r}, "CI", [round(100*x, 1) for x in r["overall"]["wilson95"]])
    print(summ); print("max abs diff vs csv", maxdiff); print("csv diffs", [(m, b, a, v[f"csv_{a}"], round(v[f"mine_{a}"],2)) for m, c in cmp.items() for b, v in c.items() for a in ("mean","max") if abs(v[f"csv_{a}"]-v[f"mine_{a}"]) > 1e-3])
if __name__ == "__main__": main()

def write_md():
    d = json.load(open(f"{ROOT}/verify/released_dev_accuracy.json")); R = d["results"]; S = d["structure"]
    L = ["# Released-surprise IntPhys dev pairwise accuracy (independent recomputation)", "",
         f"Structure: {S['n_videos']} videos, {S['n_quadruplets']} quadruplets ({S['per_block_quadruplets']}), {S['n_pairs']} pairs; {S['n_possible_videos']} possible videos.", "",
         "Rule: " + d["rule"], "", "Accuracy % (strict S(possible) < S(impossible)), n=60 pairs per block, 180 overall; Wilson 95% CI on overall.", "",
         "| model | agg | O1 | O2 | O3 | overall (k/n) | Wilson 95% |", "|---|---|---|---|---|---|---|"]
    names = ["vit-l-rope-vm2m", "vit-l-rope-howto", "vit-h-rope-vm2m", "videomaev2_g"] + [f"vit-l-rope-random-{i}" for i in range(20)]
    for m in names:
        for a in ("mean", "max"):
            r = R[m][a]; o = r["overall"]
            L.append(f"| {m} | {a} | " + " | ".join(f"{100*r[b]['acc_strict']:.2f}" for b in BLOCKS) + f" | {100*o['acc_strict']:.2f} ({o['k_correct_strict']}/{o['n_pairs']}) | [{100*o['wilson95'][0]:.1f}, {100*o['wilson95'][1]:.1f}] |")
    L += ["", "Random-init ViT-L controls (20 seeds), overall acc: " + json.dumps(d["random_control_summary"]), "",
          f"Cross-check vs released performance.csv 'Filtered' rows: max abs diff {d['csv_crosscheck_max_abs_diff_pct']:.3f} points (only near-tie random-init mean cases differ, float32 summation order)."]
    open(f"{ROOT}/verify/released_dev_accuracy.md", "w").write("\n".join(L) + "\n")
write_md()
