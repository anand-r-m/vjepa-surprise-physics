"""Kernel entry body (appended to the bundle header by kaggle/build_kernel.py).
Runs inside Kaggle: pinned pip installs, checkpoint download + hash, then run_lib.main."""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CODE = Path(os.environ.get("VJEPA_CODE", "/kaggle/working/code"))
OUT = Path(os.environ.get("VJEPA_OUT", "/kaggle/working/results"))
CKPT_DIR = Path("/tmp/ckpt")   # NOT /kaggle/working: everything there is returned as kernel output

sys.path[:0] = [str(CODE / "src"), str(CODE / "kaggle" / "common")]
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
os.environ["VJEPA_EDIT_PARAMS"] = str(CODE / "configs" / "edit_params.yaml")

PIP = ["einops==0.8.1", "beartype==0.21.0"]      # pinned; torch/timm/numpy/scipy/sklearn come from the image
URLS = {
    "M1": "https://dl.fbaipublicfiles.com/jepa/vitl16/vitl16.pth.tar",
    "M2": "https://dl.fbaipublicfiles.com/vjepa2/vitl.pt",
    "M1H": "https://dl.fbaipublicfiles.com/jepa/vith16/vith16.pth.tar",   # public original V-JEPA ViT-H/16 (diagnostic)
}


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "kernel_log.txt", "a") as fh:
        fh.write(s + "\n")


def resolve_dataset(slug):
    root = Path("/kaggle/input")
    log("ls /kaggle/input:", sorted(p.name for p in root.iterdir()) if root.exists() else "missing")
    for c in (root / slug, root / "datasets" / "anandrodriguezmenon" / slug):
        if c.exists():
            return str(c)
    hits = [p for p in root.rglob(slug) if p.is_dir()]
    return str(hits[0]) if hits else None


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        t = time.time()
        log("downloading", url)
        urllib.request.urlretrieve(url, dest)
        log(f"downloaded {dest.stat().st_size/1e9:.2f} GB in {time.time()-t:.0f}s")
    return dest


def main():
    t0 = time.time()
    log("kernel start", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *PIP], capture_output=True, text=True)
    log("pip install rc", r.returncode, r.stderr[-300:])
    cfg_path = CODE / "runs.json"
    cfg = json.load(open(cfg_path))
    cfg["dev_path"] = resolve_dataset(cfg.get("dev_dataset", "intphys-dev"))
    cfg["ip2_path"] = resolve_dataset(cfg.get("ip2_dataset", "intphys2"))
    log("dataset paths", cfg["dev_path"], cfg["ip2_path"])
    resolved = OUT.parent / "runs_resolved.json"
    resolved.write_text(json.dumps(cfg))
    import run_lib
    from vjepa_study.models.m1_vjepa import M1VJEPA
    from vjepa_study.models.m0r import M0r
    ckpt_info = {}

    def build_model(name, run):
        """Return a list of wrappers, one per GPU (run['n_gpus'], default 1)."""
        import torch
        n = min(run.get("n_gpus", 1), max(torch.cuda.device_count(), 1))
        prec = run.get("precision", "fp16")   # released config = fp16 autocast; fp32 only on request
        out = []
        for g in range(n):
            dev = f"cuda:{g}" if torch.cuda.is_available() else "cpu"
            if name in ("M1", "M1H"):
                arch = "vit_large" if name == "M1" else "vit_huge"
                p = download(URLS[name], CKPT_DIR / Path(URLS[name]).name)
                if name not in ckpt_info:
                    ckpt_info[name] = dict(url=URLS[name], bytes=p.stat().st_size, sha256=run_lib.sha256_file(p))
                m = M1VJEPA(ckpt_path=str(p), model_name=arch, resolution=224, repo_root=CODE,
                            device=dev, precision=prec)
                m.info.update(ckpt_info[name])
            elif name == "M0r":
                m = M0r(init_seed=run.get("init_seed", 0), model_name="vit_large", resolution=224,
                        repo_root=CODE, device=dev, precision=prec)
                m.info["note"] = "random init, released init_model with empty checkpoint"
            elif name == "M2":
                from vjepa_study.models.m2_vjepa2 import M2VJEPA2
                p = download(URLS["M2"], CKPT_DIR / "vitl.pt")
                if "M2" not in ckpt_info:
                    ckpt_info["M2"] = dict(url=URLS["M2"], bytes=p.stat().st_size, sha256=run_lib.sha256_file(p))
                m = M2VJEPA2(ckpt_path=str(p), repo_root=CODE, device=dev, precision=prec)
                m.info = dict(ckpt_info["M2"], resolution=m.res, precision=prec, mask_index=m.mask_index, load_msgs={k: [len(v.missing_keys), len(v.unexpected_keys)] for k, v in m.load_msgs.items()})
            else:
                raise NotImplementedError(name)
            out.append(m)
        return out

    bundle = json.load(open(CODE / "BUNDLE_INFO.json"))
    st = run_lib.main(str(resolved), OUT, build_model=build_model, bundle_info=bundle, log=log)
    log("status", json.dumps(st))
    log(f"kernel total {time.time()-t0:.0f}s")


main()
