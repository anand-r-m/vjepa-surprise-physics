"""Build kaggle/<group>/run.py = self-contained bundle header + kernel_main body.
Usage: python kaggle/build_kernel.py <group>
The bundle (src/vjepa_study, kaggle/common, configs, minimal external code, runs.json) is
embedded as base64 tar.gz so no extra dataset or git access is needed inside the kernel."""
import base64
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = ("__pycache__", ".pyc", ".git/", "data_intphys.tar.gz", "figures.ipynb", ".github")


def add(tf, rel):
    p = ROOT / rel
    for f in ([p] if p.is_file() else sorted(p.rglob("*"))):
        r = str(f.relative_to(ROOT))
        if f.is_file() and not any(x in r for x in EXCLUDE):
            tf.add(f, arcname=r)


def dirty_paths():
    """Porcelain entries other than the build products kaggle/<group>/run.py (tracked outputs of this script: earlier
    builds in the same pass would otherwise mark every later bundle dirty although run.py is in no bundle)."""
    out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    return [l for l in out if not (l[3:].startswith("kaggle/") and l.endswith("/run.py"))]


def main(group):
    gdir = ROOT / "kaggle" / group
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        add(tf, "src/vjepa_study")
        add(tf, "kaggle/common")
        add(tf, "configs/edit_params.yaml")
        add(tf, "external/jepa-intuitive-physics/evaluation_code")
        add(tf, "external/vjepa2/src")
        add(tf, "external/vjepa2/evals/hub")
        if group.startswith("ip2main"):             # IntPhys 2 Main support lives in its own module, bundled only here (prereg s1 same-code-path)
            add(tf, "kaggle/ip2main")
        if group.startswith("expl"):                # EXPLORATORY post-freeze edits (halve_hold) live in their own module, bundled only here
            add(tf, "kaggle/expl")
        tf.add(gdir / "runs.json", arcname="runs.json")
        if (gdir / "matches.json").exists():       # per-pair matched strengths (post-freeze, make_matched_strengths.py)
            tf.add(gdir / "matches.json", arcname="matches.json")
        git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        ext = lambda n: subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT / "external" / n, capture_output=True, text=True).stdout.strip()
        info = dict(group=group, repo_head=git("rev-parse", "HEAD"), repo_dirty=bool(dirty_paths()),
                    external={n: ext(n) for n in ("jepa-intuitive-physics", "vjepa2", "jepa")})
        b = json.dumps(info).encode()
        ti = tarfile.TarInfo("BUNDLE_INFO.json"); ti.size = len(b)
        tf.addfile(ti, io.BytesIO(b))
    b64 = base64.b64encode(buf.getvalue()).decode()
    header = (
        "import base64, io, os, tarfile\n"
        f"_B = '{b64}'\n"
        "os.makedirs('/kaggle/working/code', exist_ok=True)\n"
        "tarfile.open(fileobj=io.BytesIO(base64.b64decode(_B)), mode='r:gz').extractall('/kaggle/working/code')\n"
        "del _B\n"
    )
    if group.startswith("expl"):
        header += (ROOT / "kaggle" / "expl" / "preamble.py").read_text()
    if group.startswith("ip2main"):
        header += (ROOT / "kaggle" / "ip2main" / "preamble.py").read_text()
    body = (ROOT / "kaggle" / "common" / "kernel_main.py").read_text()
    out = gdir / "run.py"
    out.write_text(header + body)
    print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB), bundle {info}")


if __name__ == "__main__":
    main(sys.argv[1])
