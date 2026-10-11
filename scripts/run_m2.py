"""M2 DESCRIPTIVE analysis (M2 is H1-ineligible: clean 60.8% < 80%): the frozen H1 / H2 / H3 stages applied to M2 exactly as to M1.

New script; calls the frozen driver (scripts/run_analysis.py, unmodified) for clean/h1/h2 and its h3_stage function for H3
(the driver's main() only dispatches H3 for M1). Meta check runs first inside RA.main (abort = exception).

  python scripts/run_m2.py --runs <dir of run symlinks> --out results/analysis/m2 --matches kaggle/h2_spec_a/matches.json \
         --retention results/analysis/h1/retention.json
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_analysis as RA                     # frozen driver (unmodified)

VARIANTS = (("", "tiehalf", 1.0), ("strict", "strict", 1.0), ("exactties", "tiehalf", 0.0))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", default="results/analysis/m2")
    ap.add_argument("--matches", default="kaggle/h2_spec_a/matches.json")
    ap.add_argument("--retention", default="results/analysis/h1/retention.json")
    ap.add_argument("--n-boot", type=int, default=10000)
    a = ap.parse_args(argv)
    for sub, tie_mode, ts in VARIANTS:
        out = Path(a.out) / sub
        args = ["--runs", a.runs, "--out", str(out), "--matches", a.matches, "--retention", a.retention, "--models", "M2",
                "--stages", "clean", "h1", "h2", "--n-boot", str(a.n_boot), "--tie-mode", tie_mode, "--tau-scale", str(ts)]
        RA.main(args)                                            # meta check first; raises on mismatch
        R = RA.Runs(a.runs)
        _, clean, _ = RA.clean_stage(R, ["M2"], out, a.n_boot)
        RA.h3_stage(R, "M2", clean["M2"], R.need(R.clean_id("M0r", "init0")), out, a.n_boot, RA.make_var("h3", "primary", None, tie_mode, ts))


if __name__ == "__main__":
    main()
