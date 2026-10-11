# expl preamble: runs between the bundle header (extraction) and the unchanged kernel_main body.
import os as _os
import sys as _sys
_C = _os.environ.get("VJEPA_CODE", "/kaggle/working/code")
_sys.path[:0] = [_C + "/src", _C + "/kaggle/common", _C + "/kaggle/expl"]
import run_lib as _run_lib
import expl_lib as _expl_lib
_expl_lib.install(_run_lib)
