# Is latent surprise about physics? V-JEPA / V-JEPA 2 on IntPhys

Code, pre-registration, analysis outputs and verification scripts for the ESCI 2027 submission.

## Contents
- `src/`, `scripts/`, `tests/`, `configs/`: edits, model wrappers (V-JEPA, V-JEPA 2, baselines), analysis, figure scripts, unit tests. Install with `pip install -e .`.
- `docs/PREREGISTRATION.md`: the frozen pre-registration (v3.3.2); `docs/PROJECT_SPEC.md`: the specification.
- `kaggle/`: kernel sources and run lists (`runs.json`, `matches.json`) used for every GPU run. Dataset folders are not included.
- `results/analysis/`: analysis outputs; `results/VERIFIED.json`: independently recomputed numbers that the paper uses.
- `results/raw/`: per-run `meta.json` and logs only.
- `verify/`: the independent verifier's recomputation scripts and audit notes. `notes/`: result write-ups.
- `paper/`: LaTeX sources, number-trace table, figure scripts' outputs.

## Not included
- Model weights (V-JEPA ViT-L/16, V-JEPA 2 ViT-L, ViT-H): download from the official Meta releases.
- IntPhys dev-set videos (licence restricts redistribution): obtain from the IntPhys authors.
- Raw per-video surprise arrays (`surprise.npz`, about 4.4 GB). They are available on request and can be mirrored on an archive such as Zenodo.

## Provenance
The pre-registration was frozen at commit `ee63aee` (tag `prereg-frozen`) in the original development repository. That history is not published here, because it contains a large checkpoint file. This folder is a snapshot of the final state. Commit hashes quoted in `results/` and the paper refer to that development repository.

## Licence
Add a licence file of your choice before publishing.

Note: the frozen `docs/PREREGISTRATION.md` is reproduced unchanged and so refers to project-management files (`state/`, `reviews/`) that are not part of this release.
