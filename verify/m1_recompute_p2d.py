"""Independent recompute of M1 surprise S[window, C] with the RELEASED eval code (external/jepa-intuitive-physics)."""
import sys, os, json, argparse, time
import numpy as np, cv2, torch, torch.nn.functional as F
from einops import rearrange
ROOT = "/home/anand-r-m/Research & Dev/Vjepa"
EC = ROOT + "/external/jepa-intuitive-physics/evaluation_code"
sys.path.insert(0, EC)
from src.utils.transforms import make_transforms
from src.masks.utils import apply_masks
from evals.intuitive_physics.utils import get_time_masks
import evals.intuitive_physics.eval as released   # init_model, load_pretrained

ap = argparse.ArgumentParser()
ap.add_argument("--vids", nargs="+", type=int, default=[0, 1])      # indices into stored video_ids
ap.add_argument("--temporal", default="A")  # A: first 100 native frames; B: every 4th of first 400 (100 frames); C: every 4th frame of first 100 (25)
ap.add_argument("--spatial", default="direct")  # direct: 512->224 by released transform; area288: cv2 INTER_AREA 512->288 first
ap.add_argument("--dev", nargs="*", default=None)  # dev video ids like O1/01/2: compare with p2_clean fp32 run (released PNG loader)
ap.add_argument("--nwin", type=int, default=17)
ap.add_argument("--precision", default="fp32")
ap.add_argument("--out", default=ROOT + "/verify/m1_surprise_recompute.json")
ap.add_argument("--ckpt", default=ROOT + "/scratch_data/vitl16.pth.tar")
a = ap.parse_args()
torch.set_num_threads(6)
dev = torch.device("cpu")
stored = np.load(ROOT + "/results/raw/p2_det/results/P2D_M1_ip2dbg_fp32_clean_s1/surprise.npz", allow_pickle=True)

def load_frames(path, temporal, spatial):
    cap = cv2.VideoCapture(path); fr = []
    n = {"A": 100, "B": 400, "C": 100}[temporal]
    while len(fr) < n:
        ok, f = cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    if temporal in ("B", "C"): fr = fr[::4]
    if spatial == "area288": fr = [cv2.resize(f, (288, 288), interpolation=cv2.INTER_AREA) for f in fr]
    return np.stack(fr)

# released model construction (config = default_intphys.yaml values, vit_large non-rope checkpoint)
encoder, target_encoder, predictor = released.init_model(
    device=dev, pretrained=a.ckpt, model_name="vit_large", patch_size=16, crop_size=224, frames_per_clip=16,
    tubelet_size=2, is_causal=False, pred_is_causal=False, pred_depth=12, uniform_power=True,
    enc_checkpoint_key="encoder", pred_checkpoint_key="predictor", use_SiLU=False, wide_SiLU=False, use_sdpa=True)
for m in (encoder, target_encoder, predictor):
    m.eval()
    for p in m.parameters(): p.requires_grad = False
transform = make_transforms(random_horizontal_flip=False, random_resize_aspect_ratio=[1., 1.], random_resize_scale=[1., 1.],
                            reprob=0., auto_augment=False, motion_shift=False, crop_size=224)
CTX = [2, 4, 6, 8, 10]

def surprise(clip, nwin):  # clip [C,T,H,W] float normalised, sampled frames (already skip 2)
    pieces = clip[None].unfold(2, 16, 2).permute(0, 2, -1, 1, 3, 4).contiguous().flatten(0, 1)  # [W,16,C,H,W]
    pieces = rearrange(pieces, "b t c h w -> b c t h w").contiguous()[:nwin]
    out = []
    for s in range(0, pieces.shape[0], 6):
        pc = pieces[s:s + 6]; B = pc.shape[0]; per = []
        for L in CTX:
            m, m_, full_m = get_time_masks(L, spatial_size=(16, 16), temporal_dim=16, as_bool=False)
            m, m_, full_m = [x.unsqueeze(0).repeat(B, 1) for x in (m, m_, full_m)]
            with torch.autocast("cpu", dtype=torch.bfloat16, enabled=(a.precision == "bf16")):
                h = target_encoder(pc, [full_m])[0]
                h = F.layer_norm(h, (h.size(-1),))
                targets = apply_masks(h, [m_], concat=False)
                context = encoder(pc, [m])
                preds = predictor(context, targets, [m], [m_])
            per.append(F.l1_loss(preds[0].float(), targets[0].float(), reduction="none").mean((1, 2)))
        out.append(torch.stack(per, 1))  # [B, 5]
    return torch.cat(out).numpy()  # [W,5]

res = {"args": vars(a), "videos": []}
if a.dev:
    from PIL import Image
    zd = np.load(ROOT + "/results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz", allow_pickle=True)
    ids = list(zd["video_ids"])
    for v in a.dev:
        t0 = time.time(); d = f"{ROOT}/data/intphys_dev/extracted/dev/{v.split('/')[0]}/{v.split('/')[1]}/{v.split('/')[2]}/scene"
        names = sorted(os.listdir(d))[0:98:2]          # released IntPhysDataset: frames_all[0:length_clip:frame_step]
        sel = np.stack([np.array(Image.open(f"{d}/{n}")) for n in names]).astype(np.float32)
        S = surprise(transform(sel), a.nwin); ref = zd["S"][ids.index(v)][:a.nwin]; dd = np.abs(S - ref)
        res["videos"].append({"video_id": v, "n_sampled": len(names), "S": S.tolist(), "stored": ref.tolist(), "absdiff_WxC": dd.tolist(),
                              "max_absdiff": float(dd.max()), "mean_absdiff": float(dd.mean()), "sec": time.time() - t0})
        print(v, "max|dS|", dd.max(), "mean", dd.mean(), flush=True)
    json.dump(res, open(a.out, "w"), indent=1); sys.exit(0)
for vi in a.vids:
    vid = str(stored["video_ids"][vi]); t0 = time.time()
    fr = load_frames(f"{ROOT}/data/intphys2/extracted/Debug/Videos/{vid}.mp4", a.temporal, a.spatial)
    # released extract_losses: clip_len = 99//frame_step = 49 sampled frames at skip 2, start 0 -> 17 windows
    sel = fr[0:98:2][:49]
    clip = transform(sel)  # [C,T,H,W]
    S = surprise(clip, a.nwin)
    ref = stored["S"][vi][:a.nwin]  # stored layout [window, C]
    d = np.abs(S - ref)
    res["videos"].append({"video_id": vid, "frames_decoded": int(len(fr)), "n_sampled": int(len(sel)), "S": S.tolist(), "stored": ref.tolist(),
                          "absdiff_WxC": d.tolist(), "max_absdiff": float(d.max()), "max_absdiff_per_C": d.max(0).tolist(),
                          "mean_absdiff": float(d.mean()), "min_over_C_mean_agg_diff": float(abs(S.min(1).mean() - ref.min(1).mean())),
                          "sec": time.time() - t0})
    print(vid[:8], "nwin", a.nwin, "max|dS|", d.max(), "mean|dS|", d.mean(), flush=True)
json.dump(res, open(a.out, "w"), indent=1)
