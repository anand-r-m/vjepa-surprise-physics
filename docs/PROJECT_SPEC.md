# PROJECT_SPEC — Is latent surprise about physics?

Source of truth for the science. Full scope is required: every model, edit, strength, seed, ablation and dataset below is in. Target venue: ESCI 2027, submission Oct 15, 2026. If code, a brief, or a draft disagrees with this file, this file wins (or the lead updates it and logs why in `state/DECISIONS.md`).

Working title: *Impossible or Just Unexpected? Testing What Latent World Models' Surprise Detects*

## 1. Hypotheses

The violation-of-expectation (VoE) protocol scores a model as "understanding" a physical principle if its surprise (prediction error in representation space) is higher on the impossible video of a matched pair than on the possible one (Garrido et al., arXiv 2502.11831). If that surprise tracks physical impossibility, then:

- **H1 Invariance.** Applying the same physically neutral edit to both videos of a pair leaves the pairwise verdict unchanged. *Measured by* flip rate and pairwise accuracy under each edit vs. clean.
- **H2 Specificity.** Real violations raise surprise more than physically possible but abrupt events of matched pixel magnitude, and V-JEPA separates them better than a frame-difference baseline. *Measured by* specificity AUROC and its difference from the baseline's AUROC.
- **H3 Sensitivity (positive control).** Edits that create violations raise surprise. *Measured by* the fraction of videos whose surprise increases.

H3 validates the pipeline. H2 is the paper's main contribution. H1 is secondary.

## 2. Models

| ID | Model | Source | Role |
|---|---|---|---|
| M1 | V-JEPA ViT-L (Garrido et al. checkpoint) | github.com/facebookresearch/jepa-intuitive-physics (+ github.com/facebookresearch/jepa) | Primary; reproduces published numbers |
| M2 | V-JEPA 2 ViT-L | HF `facebook/vjepa2-vitl-fpc64-256` / github.com/facebookresearch/vjepa2 | Second latent model |
| M3 | VideoMAEv2 | supported in the jepa-intuitive-physics repo | Pixel-reconstruction contrast |
| M0r | M1 with random init | same code, untrained weights | Control: should be ≈ chance |
| B1 | Frame-difference surprise | ours | Trivial baseline: surprise_t = mean |f_t − f_{t−1}| |
| B2 | Copy-last-frame error | ours | Trivial baseline: pixel error of predicting f_t = f_{t−1} over the predicted window |

**Surprise computation:** reuse the jepa-intuitive-physics implementation exactly (context of M frames predicts representations of the next N frames; surprise = L1 distance between predicted and observed target representations, per timestep). Before using M2 via HF, confirm the HF class exposes the predictor with context/target masks; if not, use the official vjepa2 repo. Do not reimplement the M1 surprise metric from scratch.

**Aggregation:** primary = max surprise over time (Garrido et al. report max works better outside matched pairs); also report mean (ablation A1).

## 3. Data

| Split | Use | Notes |
|---|---|---|
| IntPhys (2019) dev split | Main evaluation for H1, H2, H3 | Public labels; V-JEPA ≈ 98% published, so there is headroom to fall. Confirm exact size on download and record it. |
| IntPhys 2 Debug (60 videos) | P1 sanity + P3 calibration of edit strengths **only** | HF `facebook/IntPhys2`, split Debug. Never report it as evaluation. |
| IntPhys 2 Main (1,012 videos) | Optional secondary check of H2 in harder scenes | Models are near chance here, so **do not** run H1 on it. |

IntPhys 2 is CC BY-NC 4.0, evaluation use only. Record dataset versions and file hashes in `results/DATA_MANIFEST.json`.

## 4. Edits (frozen in P3)

All edits are deterministic functions `edit(frames, params, seed) -> frames`, applied before the model's own preprocessing. Strengths: three levels (low/mid/high) per edit, chosen in P3 on the Debug split so that "high" is clearly visible but scenes remain recognisable.

**E-invariance (applied identically to both videos of a pair):** brightness/colour shift · Gaussian blur · JPEG re-compression · additive Gaussian noise · centre crop + resize (zoom) · horizontal flip · frame-rate halving (drop every other frame, keep clip length by sampling).

**E-specificity (applied to possible videos only, inserted at a time t*):** lighting step (global brightness change that persists) · camera jolt (crop window shifts by k px and stays) · sudden zoom (crop scale changes and stays). t* = the violation timestamp of the matched impossible video if available in metadata; otherwise uniformly in the middle 50% of the clip (seeded).

**Magnitude matching (critical for H2):** for each violation, compute its pixel-change magnitude at the event, |Δ|_viol = mean |impossible − possible| over the frames after the event. Scale each abrupt edit's strength so its |Δ| distribution matches the violations' (target: medians within 10%; report both distributions). Without this, the "of course unpredictable things are surprising" objection wins.

**E-positive (should create violations):** vertical flip of the whole clip (objects fall upward) · time reversal of possible clips.

## 5. Metrics and statistics

- **Pairwise accuracy** = fraction of pairs where surprise(impossible) > surprise(possible). **Flip rate** = fraction of pairs whose verdict differs from the clean verdict. Paired McNemar test vs clean; Holm correction across edits.
- **Specificity AUROC** = P(Δ_viol > Δ_abrupt), where Δ_viol = S(impossible) − S(possible) and Δ_abrupt = S(possible + abrupt edit) − S(possible). Bootstrap 95% CI (10,000 resamples over scenes/pairs). Report AUROC for M1, M2, M3, B1, B2, and the paired difference M1 − B1 with CI.
- **Positive-control detection** = fraction of videos with S(edited) > S(original); binomial 95% CI.
- **Seeds:** inference is deterministic; randomness is in edit timing/params. Use 3 seeds; report mean ± sd across seeds and CIs from bootstrap.
- **Meaningful effects (pre-registered):** H1 violated if accuracy drops ≥ 5 points or flip rate ≥ 10% with Holm-adjusted p < 0.05. H2 supports "surprise is specific" if AUROC_M1 ≥ 0.80 **and** the CI of AUROC_M1 − AUROC_B1 excludes 0 in M1's favour; supports "not specific" if AUROC_M1 ≤ 0.65 or its CI overlaps B1's.

## 6. Ablations (keep to these three)

- **A1** Aggregation: max vs mean surprise.
- **A2** Context length: 3 values bracketing the Garrido default.
- **A3** Dose-response: low/mid/high strength for every edit (comes free from §4).

## 7. Expected outputs (what "done" looks like)

| ID | Content | Shape |
|---|---|---|
| F0 | Method schematic (page 1) | VoE pair → surprise curve; the three tests side by side. For a broad audience. |
| T1 | Reproduction | Rows: M1, M2, M3, M0r, B1, B2. Cols: IntPhys dev pairwise acc (ours) · published value where one exists. |
| T2 | Invariance | Rows: edits × strength. Cols per model: acc · Δacc · flip rate · Holm p. |
| T3 | Positive controls | Rows: vflip, reversal. Cols per model: detection rate [95% CI]. |
| T4 | Ablations | A1 and A2 effects on clean acc and specificity AUROC. |
| F1 | Invariance | Grouped bars: flip rate per edit (high strength), one group per model. |
| F2 | Specificity (headline) | Left: distributions of Δ_viol vs Δ_abrupt for M1 and B1. Right: AUROC with CIs for all models/baselines. |
| F3 | Dose-response | Flip rate (H1 edits) and AUROC (H2 edits) vs strength. |
| F4 | Example surprise curves | 2–3 clips: clean possible, impossible, possible + abrupt event, with event time marked. |

## 8. Sanity expectations (if these fail, suspect a bug before believing a result)

- M1 clean IntPhys dev acc ≈ published (≥ 90%). M0r ≈ 50%. B1, B2 ≈ 50% on clean pairs (IntPhys pairs are pixel-matched, so frame-diff should not solve them).
- Identity edit (strength 0) gives flip rate exactly 0.
- Applying an invariance edit to both videos must use identical params and seed for both members of a pair (unit-tested).
- Surprise values are finite and on the same scale as the released raw surprise files.

## 9. Kill / stop criteria

- **G1 fails** (M1 < 90% on clean dev after 3 logged debugging attempts) → escalate to human.
- **G2 fails** (positive controls < 80% detection for M1) → pipeline suspect; do not interpret H1/H2 until fixed.
- **Not a kill:** M1 is invariant *and* clearly more specific than B1. That's a positive result ("evidence the JEPA abstraction claim holds in this setting"). Frame the paper around whatever the data says.

## 10. Output data layout

```
results/
  DATA_MANIFEST.json            dataset versions, file hashes, split sizes
  runs/<run_id>/
    meta.json                   git hash, model, dataset, edit, strength, seed, config path, kaggle kernel version, start/end time
    surprise.npz                per-video per-timestep surprise arrays + video ids
    log.txt
  analysis/                     coder's metric outputs (CSV/JSON) + figures
  VERIFIED.json                 written ONLY by verifier: headline numbers that passed independent recomputation
```

`run_id` format: `<phase>_<model>_<dataset>_<edit>-<strength>_s<seed>`, e.g. `P4_M1_ipdev_blur-high_s1`.

## Amendments A1 (2026-10-06, pre-freeze; from `reviews/P0_spec_review.md`, logged in DECISIONS)

Binding text for the P3 pre-registration. Where it conflicts with §§2–9 above, this section wins. Nothing in scope is dropped. Full wording is in the review's §2 (B1–B11) and §3 (MJ1–MJ12); the summary:

- **A1.1 Protocol (B1).** M1 uses the released IntPhys config verbatim (frame skip, window, C set, min over C, start stride 2); no re-selection on dev. G1/T1 use the aggregation behind the published 98% (expected: average). H1 primary = average; H2/H3 primary = max; A1 = the other. A2 = fixed C values vs default min-over-C, from stored S[t,C] (no new runs).
- **A1.2 Pairs (B2).** Pairing rule as released code; n_pairs 180, 90 quadruplet clusters (30/block); tie if |ΔS| ≤ 1e-4 counts 0.5. B1 ≈ 50% sanity relaxed.
- **A1.3 Event time (B3).** IntPhys dev has no event times. t*_on = first visible pixel divergence between a possible video and its prefix-sharing impossible partner; t*_off for dynamic-2; uniform fallback only if none, count logged.
- **A1.4 Matching (B4, MJ3).** Per-pair, pixel-only, at model input resolution; mid = 1×, low = 0.5×, high = 2× of the matched strength; achieved ratio reported. Strength levels for invariance edits by SSIM 0.95/0.85/0.70 on Debug.
- **A1.5 New edit (B5).** Local lighting step (spotlight matched in location/area to the violation), in the specificity family.
- **A1.6 Reference (B6).** Jolt/zoom on a base window applied to all frames; Δ_abrupt relative to the unshifted base-window video.
- **A1.7 H2 estimand and rule (B7, B8).** Mann–Whitney AUROC at mid strength pooled over types (per seed, then averaged), foil accuracy secondary, scene-cluster bootstrap stratified by block with all models on the same draw; exhaustive outcome table (Specific / Specific except type k / Separable but not beyond baseline / Partial / Not specific / Reversed). M1 and M2 must agree for claims about latent models in general.
- **A1.8 H1 (B9).** ±1 LSB dither noise floor; confirmatory family = 7 edits at high strength, Holm within model; flip-rate test vs floor; equivalence criterion for "invariant"; eligible models need clean acc ≥ 80%; cluster-bootstrap check.
- **A1.9 Frame-rate halving (B10).** Doubled native-frame stride, matched-window fallback; frame duplication prohibited.
- **A1.10 H3 and G2 (B11).** hflip-referenced and M0r-referenced detection; pairwise accuracy on flipped/reversed pairs; G2 = vflip detection ≥ 80% and M1 > M0r; reversal reported (≥ 50% expected), not gating alone. H3 is a sensitivity check, not evidence of physics understanding.
- **A1.11 Baselines and hygiene (MJ1, MJ2, MJ6, MJ9).** Add B3 = encoder-change baseline and M0r AUROC; baselines on the same preprocessed frames/stride as M1; seeds drive only genuinely random nuisance parameters (deterministic edits run once, frame-hash verified); no edited-dev runs or per-pair dev outputs viewed before the analysis text is frozen.
- **A1.12 Reporting (MJ4, MJ5, MJ7, MJ11, MJ12).** Exclude pairs whose crop removes the violation from confirmatory H1 (count reported); stratify by visible/occluded and block (descriptive); M3 descriptive only; discussion must not say "physics-specific" without "relative to these abrupt-event types".
- **Compute.** Critic estimates 50–180 GPU-h (vs 10–20 in COMPUTE.md). Time one condition in P2 and re-project on Oct 8.
