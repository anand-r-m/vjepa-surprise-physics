"""Model wrappers. Each exposes ``surprise(frames_uint8, ...) -> dict`` with
  S            float32 (n_windows, n_ctx)   released-protocol surprise per window and context length
  target_feats float16 (n_windows, n_tub, D) spatially pooled, layer-normed target features per tubelet
  idx          native frame indices used
Min over C and mean/max over windows are applied downstream (analysis.metrics.aggregate_S).
"""
