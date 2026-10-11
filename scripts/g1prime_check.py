"""G1' (iii): bitwise equality between our loader's input tensor and the output of the RELEASED
IntPhysDataset + make_transforms, on IntPhys 2 Debug scene 0 (4 videos). Debug mp4 is decoded with
our cv2 loader (every 4th frame, first 100), written losslessly as the released PNG layout, then the
released dataset class samples/transforms it. Reference tensor for (iv) is saved."""
import hashlib, json, shutil, sys, tempfile, warnings
from pathlib import Path
import cv2, numpy as np, torch
warnings.filterwarnings("ignore")
from vjepa_study import data
from vjepa_study.models import common

ROOT = Path(__file__).resolve().parents[1]
split = ROOT / "data/intphys2/extracted/Debug"
rows = [r for r in data.read_ip2_metadata(split) if r["SceneIndex"] == "0"]
assert len(rows) == 4
tmp = Path(tempfile.mkdtemp())
frames = []
for k, r in enumerate(rows, 1):
    fr = data.load_ip2_video(split, r, max_frames=100, stride=4)
    frames.append(fr)
    d = tmp / "S0" / str(k) / "scene"
    d.mkdir(parents=True)
    for i, f in enumerate(fr):
        cv2.imwrite(str(d / f"scene_{i+1:03d}.png"), f[..., ::-1])
    (tmp / "S0" / str(k) / "status.json").write_text(json.dumps({"header": {"is_possible": r["type"].endswith("Possible") and "Impossible" not in r["type"]}}))
common.use_repo(common.external_dir("jepa-intuitive-physics") / "evaluation_code")
from evals.intuitive_physics.intphys_dataset import IntPhysDataset
from src.utils.transforms import make_transforms
tf = make_transforms(random_horizontal_flip=False, random_resize_aspect_ratio=[1, 1], random_resize_scale=[1.0, 1.0],
                     reprob=0., auto_augment=False, motion_shift=False, crop_size=224)
ds = IntPhysDataset(str(tmp), frames_per_clip=99 // 2, frame_step=2, transform=tf)
buf, labels = ds[0]                                   # released: (4, C, T, H, W)
idx = data.sample_indices(len(frames[0]), 2)
out = dict(frames_shape=list(frames[0].shape), n_sampled=int(len(idx)), videos=[])
for k in range(4):
    mine = common.preprocess(frames[k][idx], 224).permute(1, 0, 2, 3)
    ref = buf[k]
    out["videos"].append(dict(file=rows[k]["file_name"], type=rows[k]["type"], bitwise_equal=bool(torch.equal(mine, ref)),
                              max_abs_diff=float((mine - ref).abs().max()), sha256_released=hashlib.sha256(ref.numpy().tobytes()).hexdigest(),
                              sha256_ours=hashlib.sha256(mine.numpy().tobytes()).hexdigest(), shape=list(ref.shape)))
np.save(ROOT / "results/analysis/g1prime/released_tensor_scene0_video1.npy", buf[0].numpy())
json.dump(out, open(ROOT / "results/analysis/g1prime/g1prime_iii.json", "w"), indent=1)
print(json.dumps(out, indent=1))
shutil.rmtree(tmp)
