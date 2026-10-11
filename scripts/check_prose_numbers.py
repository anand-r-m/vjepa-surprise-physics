#!/usr/bin/env python3
"""Compare numeric tokens, \\cite keys, \\ref/\\label keys, macros and CHECK/TODO/NEED markers
of paper prose before/after editing.
  snapshot: python3 scripts/check_prose_numbers.py snapshot [out.json]   (default scripts/prose_baseline.json)
  check:    python3 scripts/check_prose_numbers.py check [baseline.json]
  head:     python3 scripts/check_prose_numbers.py check-git [rev]       (baseline = files at git rev)
Exit 1 on any multiset difference."""
import re, sys, json, subprocess, pathlib
from collections import Counter
root = pathlib.Path(__file__).resolve().parent.parent
FILES = ["abstract","01_introduction","02_related_work","03_method","04_results","05_discussion","06_supplement"]
def feats(t):
    c = Counter()
    for m in re.finditer(r'\\(cite[a-z]*)\{([^}]*)\}', t):
        for k in m.group(2).split(','): c['cite:'+k.strip()] += 1
    for m in re.finditer(r'\\(ref|label|eqref)\{([^}]*)\}', t): c[m.group(1)+':'+m.group(2)] += 1
    for m in re.finditer(r'\\(num|chk|need|prereg)\b', t): c['macro:'+m.group(1)] += 1
    for m in re.finditer(r'TBD:[\w.\-]+|\[CHECK|\[NEED NUMBER|TODO|\[AUTHOR|\[AI-USE', t): c['mark:'+m.group(0)] += 1
    for m in re.finditer(r'Table~S\d|Fig\.~S\d|Section~S-[IVX]+|Section~[IVX]+-[A-Z]|Supplement Section~S-[IVX]+', t): c['xref:'+m.group(0)] += 1
    # numeric tokens, including digits glued to letters/macros; ignore digits inside cite/ref/label args already counted
    s = re.sub(r'\\(cite[a-z]*|ref|label|eqref|input|includegraphics)\{[^}]*\}', ' ', t)
    s = re.sub(r'\\texttt\{[^}]*\}', lambda m: m.group(0), s)
    for m in re.finditer(r'\d+(?:\.\d+)?', s): c['num:'+m.group(0)] += 1
    return c
def load_dir(rev=None):
    out = {}
    for f in FILES:
        p = f"paper/sections/{f}.tex"
        if rev: t = subprocess.check_output(["git","show",f"{rev}:{p}"], cwd=root, text=True)
        else: t = (root/p).read_text()
        out[f] = dict(feats(t))
    return out
def cmp(a, b):
    bad = 0
    for f in FILES:
        A, B = Counter(a[f]), Counter(b[f])
        for k in sorted(set(A)|set(B)):
            if A[k] != B[k]:
                bad += 1; print(f"DIFF {f}: {k}  before={A[k]} after={B[k]}")
    print("ZERO DIFFERENCES" if not bad else f"{bad} difference(s)")
    return bad
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "snapshot":
        p = pathlib.Path(sys.argv[2] if len(sys.argv)>2 else root/"scripts/prose_baseline.json")
        json.dump(load_dir(), open(p,"w"), indent=1, sort_keys=True); print("wrote", p)
    elif mode == "check-git":
        sys.exit(1 if cmp(load_dir(sys.argv[2] if len(sys.argv)>2 else "HEAD"), load_dir()) else 0)
    else:
        p = pathlib.Path(sys.argv[2] if len(sys.argv)>2 else root/"scripts/prose_baseline.json")
        sys.exit(1 if cmp(json.load(open(p)), load_dir()) else 0)
