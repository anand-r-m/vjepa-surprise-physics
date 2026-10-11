"""Numeric tokens added to paper/sections + paper/tables since 4762182, matched against VERIFIED.json values (any key)."""
import re, subprocess, json, collections, glob, os
from decimal import Decimal, ROUND_HALF_UP
V = json.load(open('results/VERIFIED.json'))['entries']
def nums(o, out):
    if isinstance(o, bool) or o is None: return
    if isinstance(o, (int, float)): out.append(float(o))
    elif isinstance(o, (list, tuple)): [nums(x, out) for x in o]
    elif isinstance(o, dict): [nums(x, out) for x in o.values()]
vals = []; keyof = collections.defaultdict(set)
for e in V:
    t = []; nums(e.get('value'), t); nums(e.get('ci'), t); nums(e.get('alt'), t)
    for x in t:
        for sc in (1, 100):
            vals.append((x * sc, e['key']))
    for m in re.finditer(r'\d+(?:\.\d+)?', str(e.get('display', ''))): vals.append((float(m.group()), e['key']))
    for m in re.finditer(r'\d+(?:\.\d+)?', str(e.get('note', ''))): vals.append((float(m.group()), e['key'] + ' [note]'))
def keys_for(tok):
    x = float(tok); d = len(tok.split('.')[1]) if '.' in tok else 0
    q = Decimal(1).scaleb(-d); hit = set()
    for v, k in vals:
        if Decimal(repr(v)).quantize(q, rounding=ROUND_HALF_UP) == Decimal(tok) or abs(v - x) < 1e-9: hit.add(k)
    return hit
def toks(t):
    s = re.sub(r'\\(cite[a-z]*|ref|label|eqref|input|includegraphics|bibliography\w*)\{[^}]*\}', ' ', t)
    s = re.sub(r'\\(begin|end|usepackage|documentclass|setlength|renewcommand|newcommand)\{?[^}\n]*\}?', ' ', s)
    return collections.Counter(re.findall(r'(?<![\w.])\d+(?:\.\d+)?', s))
files = sorted(glob.glob('paper/sections/*.tex') + glob.glob('paper/tables/*.tex'))
rep = []
for f in files:
    try: old = subprocess.check_output(['git', 'show', f'4762182:{f}'], text=True, stderr=subprocess.DEVNULL)
    except Exception: old = ''
    new = open(f).read()
    if old == new: continue
    a = toks(new) - toks(old)
    for tk, n in sorted(a.items()):
        ks = keys_for(tk)
        # context
        m = re.search(r'.{0,60}(?<![\w.])' + re.escape(tk) + r'(?![\d]).{0,40}', new.replace('\n', ' '))
        rep.append((f, tk, n, sorted(ks)[:4], m.group(0) if m else ''))
json.dump(rep, open(os.path.expanduser('~/.cache/tmp/p10_tokens.json'), 'w'))
print(len(rep), 'added tokens;', sum(1 for r in rep if not r[3]), 'with no VERIFIED match')
for r in rep:
    if not r[3]: print(r[0].replace('paper/', ''), r[1], 'x%d' % r[2], '|', r[4])
