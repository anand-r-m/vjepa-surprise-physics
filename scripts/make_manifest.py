"""Build results/DATA_MANIFEST.json: archive hashes, per-split file counts, per-file sha256.

Usage: .venv/bin/python scripts/make_manifest.py
"""
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "DATA_MANIFEST.json"


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def tree(root):
    files = {}
    total = 0
    exts = Counter()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(root))
            files[rel] = {"bytes": p.stat().st_size, "sha256": digest(p, "sha256")}
            total += p.stat().st_size
            exts[p.suffix.lower()] += 1
    return {"n_files": len(files), "total_bytes": total, "by_ext": dict(exts), "files": files}


def main():
    m = json.loads(OUT.read_text()) if OUT.exists() else {}
    ip2 = ROOT / "data" / "intphys2"
    dev = ROOT / "data" / "intphys_dev"
    if (ip2 / "IntPhys2.zip").exists():
        e = m.setdefault("intphys2", {})
        e.update({
            "source": "https://dl.fbaipublicfiles.com/IntPhys2/IntPhys2.zip (HF facebook/IntPhys2)",
            "license": "CC BY-NC 4.0, evaluation use only, do not redistribute (private Kaggle dataset only)",
            "archive": {"name": "IntPhys2.zip", "bytes": (ip2 / "IntPhys2.zip").stat().st_size,
                        "sha256": digest(ip2 / "IntPhys2.zip", "sha256")},
        })
        ex = ip2 / "extracted"
        if ex.exists():
            e["tree"] = tree(ex)
            e["splits"] = {}
            for split in ("Debug", "Main", "HeldOut"):
                for d in ex.rglob(split):
                    if d.is_dir():
                        e["splits"][split] = sum(1 for p in d.rglob("*.mp4"))
    if (dev / "dev.tar.gz").exists():
        e = m.setdefault("intphys_dev", {})
        e.update({
            "source": "https://download-intphys.cognitive-ml.fr/dev.tar.gz",
            "license": "CC BY 4.0",
            "published_md5": "6a72715007f2f3b0e9546bfa8d8fc39b",
            "archive": {"name": "dev.tar.gz", "bytes": (dev / "dev.tar.gz").stat().st_size,
                        "md5": digest(dev / "dev.tar.gz", "md5"),
                        "sha256": digest(dev / "dev.tar.gz", "sha256")},
        })
        ex = dev / "extracted"
        if ex.exists():
            e["tree"] = tree(ex)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(m, indent=1))
    print("wrote", OUT, {k: v.get("tree", {}).get("n_files") for k, v in m.items()})


if __name__ == "__main__":
    sys.exit(main())
