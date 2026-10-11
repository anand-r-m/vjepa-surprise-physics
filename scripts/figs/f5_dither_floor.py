"""F5 (EXPLORATORY, post-hoc) dither noise floor: copies the figure already produced by scripts/fig_dither_floor.py into paper/figures/.
The source figure needs the raw runs; regenerate it with scripts/fig_dither_floor.py. -> paper/figures/f5_dither_floor_EXPLORATORY.pdf"""
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

src = I("figures/dither_floor_EXPLORATORY_post-hoc.pdf")
I("results/analysis/h1/dither_floor_EXPLORATORY.json")
dst = FIGS / "f5_dither_floor_EXPLORATORY.pdf"
shutil.copyfile(src, dst)
write_sidecar("F5", "scripts/figs/f5_dither_floor.py", ["paper/figures/f5_dither_floor_EXPLORATORY.pdf"],
              extra=dict(notes=["Copy of figures/dither_floor_EXPLORATORY_post-hoc.pdf (scripts/fig_dither_floor.py); no VERIFIED keys; numbers in the figure come from results/analysis/h1/dither_floor_EXPLORATORY.json",
                                "Not re-styled: greyscale legibility not re-checked by this script"]))
