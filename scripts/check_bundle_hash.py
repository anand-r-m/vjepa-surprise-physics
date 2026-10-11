"""Check that every kaggle/<group>/run.py bundle embeds configs/edit_params.yaml identical to the repo
file and to the sha256 recorded in notes/CALIBRATION.md. Run before any push.
Usage: python scripts/check_bundle_hash.py [group ...]   (default: the six edited P4 groups; legacy clean/P1/P2 bundles embed the old placeholder yaml but never read it)
Exit code 1 on any mismatch."""
import base64
import hashlib
import io
import re
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITED = ["g2_controls", "h1_inv_a", "h1_inv_b", "h1_inv_c", "h2_spec_a", "h2_spec_b"]
M2_EDITED = ["m2_g2_controls", "m2_h1_inv_a", "m2_h1_inv_b", "m2_h1_inv_c", "m2_h2_spec_a", "m2_h2_spec_b"]   # tier 2; pass m2_dose_* explicitly


def bundle_yaml(run_py: Path):
    m = re.search(r"^_B = '([A-Za-z0-9+/=]+)'", run_py.read_text(), re.M)
    if not m:
        return None
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(m.group(1))), mode="r:gz") as tf:
        try:
            return tf.extractfile("configs/edit_params.yaml").read()
        except KeyError:
            return None


def recorded_hash():
    m = re.findall(r"edit_params\.yaml sha256[^0-9a-f]*([0-9a-f]{64})", (ROOT / "notes" / "CALIBRATION.md").read_text())
    return m[-1] if m else None


def main(groups):
    repo = hashlib.sha256((ROOT / "configs" / "edit_params.yaml").read_bytes()).hexdigest()
    rec = recorded_hash()
    ok = True
    print(f"repo yaml {repo}\nrecorded  {rec}")
    if repo != rec:
        print("MISMATCH repo vs notes/CALIBRATION.md"); ok = False
    for g in groups or EDITED:
        y = bundle_yaml(ROOT / "kaggle" / g / "run.py")
        if y is None:
            print(f"{g}: no edit_params.yaml in bundle (clean group), skipped"); continue
        h = hashlib.sha256(y).hexdigest()
        good = h == repo == rec
        ok &= good
        print(f"{g}: {h[:16]} {'OK' if good else 'MISMATCH'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
