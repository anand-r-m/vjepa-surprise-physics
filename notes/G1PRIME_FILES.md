# G1' file list for the verifier (data paths only; no coder code)

IntPhys 2 Debug scene 0 (SceneIndex `0`), 4 videos under `data/intphys2/extracted/Debug/`:
- `Videos/083861b17a8b3f4bef7e3aaad0b960318a5ea19ca98258fe2bfd700d11343e3d.mp4` (1_Possible)
- `Videos/56c044c79b791ff1d2eae592c3af1914772d79a23c9603dcaf9a983717c5c47c.mp4` (1_Impossible)
- `Videos/4b2779c2649b64094af506b8783525387c2f7cd52dd8f5974330500866a5045e.mp4` (2_Impossible)
- `Videos/66a6de26327fe7661ac4fec04da96d0710d2177afad8babdc0dd27e71b19db1e.mp4` (2_Possible)

Metadata: `data/intphys2/extracted/Debug/metadata.csv` (rows with SceneIndex = 0).
Reference tensor from the released dataloader (float32, shape [3 channels, 49 frames, 224, 224]) for the first video (`1_Possible`): `results/analysis/g1prime/released_tensor_scene0_video1.npy`. SHA-256 of all four released tensors (raw float32 bytes, C-order) are in `results/analysis/g1prime/g1prime_iii.json` (`sha256_released`).
Input spec to reproduce independently: decode the mp4 (RGB), keep every 4th frame, first 100 frames kept; then the released protocol: frames 0,2,...,96 (49 frames, skip 2), bilinear resize to 224x224 (align_corners=False, no antialias), ImageNet mean/std on the 0-255 scale.
Released code to compare against: `external/jepa-intuitive-physics/evaluation_code/evals/intuitive_physics/intphys_dataset.py` (IntPhysDataset) and `src/utils/transforms.py` (make_transforms), pinned commit `302a2e821d908b4a8667e0c0e48fe733e43c9156`.
Dev (G1' attempt-1 clean runs) files: `results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz`, `results/raw/p2_vith/results/P2H_M1H_ipdev_clean_s1/surprise.npz`; released references `verify/released_dev_accuracy.json`.
