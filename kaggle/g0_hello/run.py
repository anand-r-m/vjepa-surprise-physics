"""G0 hello kernel: report torch/CUDA/GPU, do a small GPU matmul, write results/g0/."""
import json, os, platform, subprocess, sys, time, datetime

OUT = "/kaggle/working/results/g0"
os.makedirs(OUT, exist_ok=True)
lines = []
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    lines.append(s)

t0 = time.time()
start = datetime.datetime.utcnow().isoformat() + "Z"
meta = {"start_utc": start, "python": sys.version, "platform": platform.platform()}
try:
    nv = subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout
except Exception as e:  # noqa
    nv = f"nvidia-smi failed: {e}"
log(nv)
meta["nvidia_smi"] = nv
try:
    import torch
    meta["torch"] = torch.__version__
    meta["cuda_available"] = torch.cuda.is_available()
    meta["cuda_version"] = torch.version.cuda
    log("torch", torch.__version__, "cuda_available", torch.cuda.is_available())
    if torch.cuda.is_available():
        meta["device_name"] = torch.cuda.get_device_name(0)
        meta["device_count"] = torch.cuda.device_count()
        log("device", meta["device_name"], "count", meta["device_count"])
        a = torch.randn(2048, 2048, device="cuda"); b = torch.randn(2048, 2048, device="cuda")
        torch.cuda.synchronize(); t1 = time.time()
        c = a @ b
        torch.cuda.synchronize()
        meta["matmul_2048_seconds"] = time.time() - t1
        meta["matmul_checksum"] = float(c.sum().item())
        meta["matmul_finite"] = bool(torch.isfinite(c).all().item())
        log("matmul ok", meta["matmul_2048_seconds"], meta["matmul_finite"])
except Exception as e:
    meta["error"] = repr(e)
    log("ERROR", repr(e))
meta["wall_seconds"] = time.time() - t0
meta["end_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
with open(f"{OUT}/meta.json", "w") as f:
    json.dump(meta, f, indent=2)
with open(f"{OUT}/log.txt", "w") as f:
    f.write("\n".join(lines) + "\n")
log("done")
