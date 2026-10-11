"""Pack IntPhys dev scene PNGs into one compressed npz per video (360 files) so a Kaggle
dataset has few large files instead of ~150k small ones (the PNG-tree dataset hung the
kernel mount). Output name: <block>_<scene>_<k>.npz with frames uint8 (T,H,W,3), is_possible."""
import sys
from pathlib import Path
import numpy as np
from vjepa_study import data

src = Path(sys.argv[1]); dst = Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
for block, scene in data.list_dev_scenes(src):
    for k in (1, 2, 3, 4):
        out = dst / f"{block}_{scene}_{k}.npz"
        if out.exists():
            continue
        d = src / block / scene / str(k)
        np.savez_compressed(out, frames=data.load_png_sequence(d / "scene"), is_possible=np.array(data._read_status(d)))
print("done", len(list(dst.glob("*.npz"))))
