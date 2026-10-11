"""Independent G2 control recompute: own numpy flip/reverse of decoded PNG frames, released eval code, CPU fp32."""
import sys, os, json, time
import numpy as np, torch, torch.nn.functional as F
from einops import rearrange
from PIL import Image
ROOT = "/home/anand-r-m/Research & Dev/Vjepa"; EC = ROOT + "/external/jepa-intuitive-physics/evaluation_code"
sys.path.insert(0, EC)
from src.utils.transforms import make_transforms
from src.masks.utils import apply_masks
from evals.intuitive_physics.utils import get_time_masks
import evals.intuitive_physics.eval as released
torch.set_num_threads(6)
dev = torch.device("cpu")
enc, tgt, pred = released.init_model(device=dev, pretrained=ROOT + "/scratch_data/vitl16.pth.tar", model_name="vit_large", patch_size=16,
    crop_size=224, frames_per_clip=16, tubelet_size=2, is_causal=False, pred_is_causal=False, pred_depth=12, uniform_power=True,
    enc_checkpoint_key="encoder", pred_checkpoint_key="predictor", use_SiLU=False, wide_SiLU=False, use_sdpa=True)
for m in (enc, tgt, pred):
    m.eval()
    for p in m.parameters(): p.requires_grad = False
tf = make_transforms(random_horizontal_flip=False, random_resize_aspect_ratio=[1., 1.], random_resize_scale=[1., 1.], reprob=0., auto_augment=False, motion_shift=False, crop_size=224)
CTX = [2, 4, 6, 8, 10]
WIN = [0, 5, 10, 16]  # window subset for CPU budget (full 17-window run done separately for O1/01/2 vflip)
def surprise(clip, nwin=17):
    pieces = clip[None].unfold(2, 16, 2).permute(0, 2, -1, 1, 3, 4).contiguous().flatten(0, 1)
    pieces = rearrange(pieces, "b t c h w -> b c t h w").contiguous()[WIN]
    out = []
    for s in range(0, pieces.shape[0], 6):
        pc = pieces[s:s + 6]; B = pc.shape[0]; per = []
        for L in CTX:
            m, m_, fm = get_time_masks(L, spatial_size=(16, 16), temporal_dim=16, as_bool=False)
            m, m_, fm = [x.unsqueeze(0).repeat(B, 1) for x in (m, m_, fm)]
            h = tgt(pc, [fm])[0]; h = F.layer_norm(h, (h.size(-1),)); t = apply_masks(h, [m_], concat=False)
            c = enc(pc, [m]); p = pred(c, t, [m], [m_])
            per.append(F.l1_loss(p[0].float(), t[0].float(), reduction="none").mean((1, 2)))
        out.append(torch.stack(per, 1))
    return torch.cat(out).numpy()
def load_native(v):
    d = f"{ROOT}/data/intphys_dev/extracted/dev/{v}/scene"
    return np.stack([np.array(Image.open(f"{d}/{n}")) for n in sorted(os.listdir(d))])  # [100,H,W,3] uint8
jobs = [("vflip", v) for v in ["O1/01/1", "O2/05/4", "O3/10/3"]] + \
       [("rev_native", v) for v in ["O1/01/2", "O2/05/4"]] + [("rev_sampled", v) for v in ["O1/01/2"]]
jobs = [j for j in jobs if (len(sys.argv) < 2 or j[0] in sys.argv[1:])]
EDIT = {"vflip": "vflip-high", "rev_native": "time_reversal-high", "rev_sampled": "time_reversal-high"}
ids = list(np.load(ROOT + "/results/raw/p4_clean_m1/results/P4_M1_ipdev_clean_s1/surprise.npz", allow_pickle=True)["video_ids"])
res = []
for edit, v in jobs:
    t0 = time.time(); fr = load_native(v)
    if edit == "vflip": sel = np.flip(fr, axis=1)[0:98:2]          # flip rows (H axis) of every native frame, then released sampling
    elif edit == "rev_native": sel = fr[::-1][0:98:2]               # reverse the 100 native frames, then sample
    else: sel = fr[0:98:2][::-1]                                    # sample, then reverse the 49 sampled frames
    sel = np.ascontiguousarray(sel).astype(np.float32)
    S = surprise(tf(sel))
    st = np.load(f"{ROOT}/results/raw/g2_controls/results/P4_M1_ipdev_{EDIT[edit]}_s1/surprise.npz", allow_pickle=True)["S"][ids.index(v)]
    st = st[WIN]; d = np.abs(S - st)
    r = dict(edit=edit, vid=v, max_abs=float(d.max()), mean_abs=float(d.mean()), indep_fullmax=float(S.min(1).max()), stored_fullmax=float(st.min(1).max()), S=S.tolist())
    res.append(r); print(edit, v, "max|d|", d.max(), "mean", d.mean(), "fullmax indep/stored", r["indep_fullmax"], r["stored_fullmax"], "sec", time.time() - t0, flush=True)
    json.dump(res, open(ROOT + f"/verify/g2_independent_sub_{'_'.join(sys.argv[1:]) or 'all'}.json", "w"))
