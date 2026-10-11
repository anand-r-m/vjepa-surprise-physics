"""Appends P10 (exploratory splice analyses) entries to results/VERIFIED.json from verify/p10_recompute.json (verifier code)."""
import json, datetime
V = json.load(open('verify/p10_recompute.json')); D = json.load(open('results/VERIFIED.json')); E = D['entries']; have = {e['key'] for e in E}
SRC = ['P4_M1_ipdev_clean_s1', 'kaggle/datasets/intphys-dev-npz']
def add(key, value, ci=None, unit=None, note='', src=None, tol='0.1 pp', status='verified', cmp=None):
    assert key not in have, key; have.add(key)
    d = dict(key=key, value=value, ci=ci, unit=unit, sources=src or SRC, tolerance=tol, status=status, exploratory=True, note='EXPLORATORY (post-hoc, not preregistered). ' + note)
    if cmp: d['compared_with'] = cmp
    E.append(d)
r2 = lambda x: round(x, 2); r3 = lambda x: round(x, 3)
C = 'verify/p10_compare.md'
S = V['splice']
add('expl.splice.n_single', S['n_single'], unit='videos', tol='exact', note='Impossible dev videos that are a single splice (prefix of one possible partner + suffix of the other), exact pixel equality at same frame index. 40 per block.', cmp=C)
add('expl.splice.n_double', S['n_double'], unit='videos', tol='exact', note='Double splice (a-b-a, two switches). 20 per block.', cmp=C)
add('expl.splice.n_nonsplice', S['n_other'], unit='videos', tol='exact', note='Impossible dev videos not fully matched by frames of the two possible partners: 0 of 180; 0 unmatched frames over 18,000. Supports the claim that each impossible dev video is a splice (90/90 quadruplets).', cmp=C)
add('expl.splice.quads_ok', S['quad']['n_quads_2pos_2imp'], unit='quadruplets', tol='exact', note='Quadruplets with 2 possible + 2 impossible videos, each impossible video using both possibles: %d/90.' % S['quad']['n_imp_both_sources'] , cmp=C)
add('expl.splice.switch1_median', S['switch1_median'], ci=[S['switch1_min'], S['switch1_max']], unit='native frame', tol='exact', note='First switch frame (native index 0..99) over 180 impossible videos: median, [min, max]; single median %.1f, double median %.1f. ci field holds the range, not a CI.' % (S['switch1_median_single'], S['switch1_median_double']), cmp=C)
add('expl.splice.switch2_median', S['switch2_median'], ci=[S['switch2_min'], S['switch2_max']], unit='native frame', tol='exact', note='Second switch frame over the 60 double splices: median, [min, max] (range, not a CI).', cmp=C)
for k, nm in (('M1', 'M1 fp16'), ('B1', 'B1'), ('B2', 'B2')):
    c = V['clean'][k]
    add(f'expl.splice.clean_tiehalf.{k}', r2(c['tiehalf']), unit='%', note=f'{nm} clean accuracy, tie-half, mean agg, tau={c["tau"]:.4g}, strict {c["strict"]:.2f}, ties {c["n_ties"]}.', cmp=C)
for k in ('B2', 'B1'):
    s = V['spearman'][k]
    add(f'expl.splice.spearman.M1_{k}', r3(s['rho']), ci=[r3(x) for x in s['ci']], unit='rho', tol='0.005 (CI 0.01)', note=f'Spearman of per-pair margins S_imp - S_pos, M1 fp16 vs {k}, 180 pairs; 10,000 scene-cluster bootstrap seed 20261015.', cmp=C)
    b = V['by_baseline'][k]
    add(f'expl.splice.m1acc_right.{k}', r2(b['m1_acc_right']), ci=[r2(x) for x in b['m1_acc_right_ci']], unit='%', note=f'M1 tie-half accuracy on pairs where {k} is right (margin > tau_{k}); n={b["n_right"]}.', cmp=C)
    add(f'expl.splice.m1acc_wrong.{k}', r2(b['m1_acc_wrong']), ci=[r2(x) for x in b['m1_acc_wrong_ci']], unit='%', note=f'M1 tie-half accuracy on pairs where {k} is wrong (margin < -tau_{k}); n={b["n_wrong"]}; {k} ties n={b["n_tie"]}.', cmp=C)
    add(f'expl.splice.m1acc_diff.{k}', r2(b['diff_pp']), ci=[r2(x) for x in b['diff_ci']], unit='pp', note=f'Right minus wrong, M1 accuracy, split by {k} correctness (association, not causal).', cmp=C)
for cl in ('single', 'double'):
    for k in ('M1', 'B1', 'B2'):
        g = V['by_class'][cl][k]
        add(f'expl.splice.{cl}.{k}', r2(g['acc']), ci=[r2(x) for x in g['ci']], unit='%', note=f'{k} tie-half accuracy on {cl}-splice pairs, n={V["by_class"][cl]["n"]}; strict {g["strict"]:.2f}.', cmp=C)
for k in ('M1', 'B1', 'B2'):
    g = V['by_class']['diff_single_minus_double'][k]
    add(f'expl.splice.single_minus_double.{k}', r2(g['diff_pp']), ci=[r2(x) for x in g['ci']], unit='pp', note=f'{k}: single minus double splice accuracy.', cmp=C)
for t in ('early', 'mid', 'late'):
    g = V['by_position']['terciles'][t]
    for k in ('M1', 'B1', 'B2'):
        add(f'expl.splice.tercile.{t}.{k}', r2(g[k]['acc']), ci=[r2(x) for x in g[k]['ci']], unit='%', note=f'{k} tie-half accuracy, {t} tercile of first switch frame {g["switch_range"]}; n=60 pairs; cutoffs {V["by_position"]["cutoffs"][0]:.2f}, {V["by_position"]["cutoffs"][1]:.2f}.', cmp=C)
pv = V['peak_window_native_any_switch']
for k, nm in (('surprise', 'M1'), ('B1', 'B1'), ('B2', 'B2')):
    add(f'expl.splice.peak_covers.{nm}', r2(pv[f'imp_{k}']['rate']), unit='%', note=f'Impossible videos whose peak window (max windowed score, min over C) covers a switch frame, native-frame containment 4w <= s <= 4w+30 for either switch; uniform-window chance {pv[f"imp_{k}"]["chance"]:.1f}%. Possible-partner control {pv[f"pos_{k}"]["rate"]:.1f}%. Sampled-frame-aligned first-switch-only variant: {V["peak_window"][k]["first_switch_rate"]:.1f}% (chance {V["peak_window"][k]["chance_uniform_first"]:.1f}%).', cmp=C)
for ed in ('vflip', 'hflip', 'time_reversal'):
    m = V['edits_pairwise'][f'{ed}_mean']['strict']; mm = V['edits_pairwise'][f'{ed}_max']['strict']
    n = 'M1 reversal run holds both classes (360 videos).' if ed == 'time_reversal' else ''
    add(f'expl.splice.edit.{ed}.counts', [m['correct_both'], m['lost'], m['gained'], m['wrong_both']], unit='pairs [both correct, lost, gained, both wrong]', tol='exact', note=f'M1 pairwise correctness clean vs {ed}, mean agg, strict d>0, 180 pairs. {n} Max-agg: lost {mm["lost"]}, gained {mm["gained"]}, p={mm["mcnemar_p"]:.3f}.', cmp=C)
    add(f'expl.splice.edit.{ed}.mcnemar_p', r3(m['mcnemar_p']), unit='p', tol='0.001', note=f'Exact two-sided McNemar, mean agg, strict; tie-half-binary version p={V["edits_pairwise"][ed+"_mean"]["tiehalf_binary_credit_gt_half"]["mcnemar_p"]:.3f}; uncorrected for multiplicity.', cmp=C)
sv = V['vflip_shift_M1']['possible180']
add('expl.vflip.m1_frac_neg_possible', r2(sv['frac_neg']), unit='%', note=f'Share of the 180 possible videos with full-clip max S(vflip) - S(clean) < 0 for M1 ({sv["n_neg"]}/180); positive {sv["n_pos"]}; above tau {sv["n_up_gt_tau"]}, ties {sv["n_tie"]}; sign test p={sv["sign_p"]:.1e}. All 360 videos: {V["vflip_shift_M1"]["all360"]["frac_neg"]:.2f}% negative.', cmp=C)
mv = V['vflip_shift_M0r_init0']
add('expl.vflip.m0r_frac_pos_possible', r2(mv['frac_pos']), unit='%', note=f'M0r init0, 180 possible videos, full-clip max, paired: positive in {mv["n_pos"]}/180 (above tau {mv["n_up_gt_tau"]}, ties {mv["n_tie"]}); tie-half detection {mv["detect_tiehalf"]:.2f}; sign test p={mv["sign_p"]:.1e}. M0r reversal/vflip runs contain possible videos only (no pairwise accuracy).', src=['P4_M0r_ipdev_vflip-high_s1', 'P4_M0r_ipdev_clean-init0_s1'], cmp=C)
add('expl.released.vith_vm2m_dev_acc', 96.67, unit='%', tol='0.1 pp', src=['scratch_data/verify_released_raw (released surprise files)'], note='Recomputed from the released raw surprise files (rerun 2026-10-11, outputs identical): vit-h-rope-vm2m mean agg 174/180, Wilson 92.9 to 98.5. See verify/released_dev_accuracy.md.', status='verified', cmp='verify/released_dev_accuracy.md')
add('expl.released.vitl_vm2m_dev_acc', 89.44, unit='%', tol='0.1 pp', src=['scratch_data/verify_released_raw (released surprise files)'], note='vit-l-rope-vm2m mean agg 161/180, Wilson 84.1 to 93.1.', status='verified', cmp='verify/released_dev_accuracy.md')
for e in E[-len([k for k in have if k.startswith('expl.splice') or k.startswith('expl.vflip') or k.startswith('expl.released')]):]: pass
D['generated'] = datetime.date.today().isoformat(); D['generator'] += ' + verify/p10_make_verified.py (P10: exploratory splice analyses; values from verify/p10_recompute.json)'
json.dump(D, open('results/VERIFIED.json', 'w'), indent=1)
print(len(E))
