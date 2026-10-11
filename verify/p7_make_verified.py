"""Builds results/VERIFIED.json from verify/p7_recompute.json (verifier's own numbers) + comparison statuses (verify/_p7_rows.json)."""
import json, datetime
V = json.load(open('verify/p7_recompute.json')); ROWS = {r[0]: r for r in json.load(open('verify/_p7_rows.json'))}
E = []
def st(labels):
    if not labels: return 'info-only'
    out = []
    for l in labels:
        assert l in ROWS, l
        out.append(ROWS[l][5])
    return 'verified' if all(o == 'match' for o in out) else 'mismatch'
def add(key, value, labels=None, ci=None, src=None, tol=None, unit=None, note=None, exploratory=False, status=None, display=None, alt=None):
    d = dict(key=key, value=value, ci=ci, unit=unit, sources=src or [], tolerance=tol, status=status or st(labels), exploratory=exploratory)
    if display is not None: d['display'] = display
    if note: d['note'] = note
    if alt: d['alt'] = alt
    if labels: d['compared_with'] = 'results/analysis (labels in verify/p7_compare.md): ' + '; '.join(labels[:4]) + (' ...' if len(labels) > 4 else '')
    E.append(d)
pc = lambda x: round(100 * x, 2)
P4C = ['P4_M1_ipdev_clean_s1']; P2C = ['P2_M1_ipdev_clean_s1']
ca = V['clean_acc']
# ---------------- placeholders
add('g1_m1_clean_acc', pc(ca['M1_fp32_P2']['tiehalf']), ['P2 fp32 tie-half'], src=P2C, tol='0.1 pp', unit='%', display='81.7', note='Public V-JEPA ViT-L, fp32 P2 run, mean aggregation, tie-half with prereg tau_m (1.057e-4). Strict 80.6. Identical under the old fixed tau 1e-4.')
add('g1_vith_clean_acc', pc(ca['M1H_fp16_P2H']['tiehalf']), ['ViT-H strict'], src=['P2H_M1H_ipdev_clean_s1'], tol='0.1 pp', unit='%', display='88.3', status='mismatch',
    note='Prereg-tau (scale-relative tau_m = 1.195e-4) tie-half = 88.33 (159/180 credits); strict 87.8 (verified). The 88.1 quoted in PREREG s7 and results/analysis/p2_vith_g1.json is the SUPERSEDED fixed tau = 1e-4 figure (reproduced: 88.06). Lead/writer must pick one convention and state it; the verifier recommends 88.3 (prereg tau) or strict 87.8.', alt=dict(value=pc(ca['M1H_fp16_P2H']['tiehalf_fixed_tau1e4']), convention='fixed tau 1e-4 (superseded)', strict=pc(ca['M1H_fp16_P2H']['strict'])))
add('m1_fp16_clean_acc', pc(ca['M1_fp16_P4']['tiehalf']), ['M1 fp16 clean tie-half', 'M1 fp16 clean strict', 'M1 fp16 clean ties'], src=P4C, tol='0.1 pp', unit='%', display='80.8', note='tie-half; strict 81.1; 7 ties. verified against results/analysis/p4/clean.json.')
h3 = V['h3']['M1']
add('g2_vflip_det', pc(h3['vflip_a_ref_p']['det']), ['H3 M1 vflip (a)'], src=['P4_M1_ipdev_vflip-high_s1', P4C[0]], tol='0.1 pp', unit='%', display='21.1', note='full-clip max, tie-half, tau_m = 1.0875e-4 (2 ties); G2 NOT met')
add('g2_vflip_ci', [pc(h3['vflip_a_ref_p']['ci'][0]), pc(h3['vflip_a_ref_p']['ci'][1])], ['H3 M1 vflip (a)'], tol='1 pp (bootstrap)', unit='%', display='14.7 to 28.1', note='scene-cluster bootstrap, 10,000, seed 20261015; analysis file gives 14.7 to 28.3', ci=[pc(h3['vflip_a_ref_p']['ci'][0]), pc(h3['vflip_a_ref_p']['ci'][1])])
add('g2_rev_det', pc(h3['reversal_ref_p']['det']), ['H3 M1 reversal'], src=['P4_M1_ipdev_time_reversal-high_s1'], tol='0.1 pp', unit='%', display='60.8', ci=[pc(x) for x in h3['reversal_ref_p']['ci']])
add('g2_hflip_det', pc(h3['hflip_ref_p']['det']), ['M1 hflip detection'], src=['P4_M1_ipdev_hflip-high_s1'], tol='0.1 pp', unit='%', display='38.6', ci=[pc(x) for x in h3['hflip_ref_p']['ci']], note='detection of hflip vs clean (full-clip max); hflip is an invariance edit, so >50% would be unexpected')
add('g2_vflip_pair_acc', pc(h3['pairwise_acc_vflip']['tiehalf']), ['H3 M1 pairwise vflip tie-half'], src=['P4_M1_ipdev_vflip-high_s1'], tol='0.1 pp', unit='%', display='83.9', note='mean aggregation, tie-half with tau_mean; strict 82.2. Clean fp16 is 80.8.')
add('g2_m0r_vflip_det', pc(h3['M0r_vflip']['det']), ['M0r vflip detection'], src=['P4_M0r_ipdev_vflip-high_s1', 'P4_M0r_ipdev_clean-init0_s1'], tol='0.1 pp', unit='%', display='87.8', ci=[pc(x) for x in h3['M0r_vflip']['ci']], note='init0 only; M0r tau = 1.704e-4 (own full-clip-max median); 16 ties. The prereg expected about 50%.')
add('b2_clean_acc', pc(ca['B2_P2_fp32']['tiehalf']), ['P2 B2 strict'], src=P2C, tol='0.1 pp', unit='%', display='76.1', note='copy-last-context-frame; tie-half = strict = 76.1 under prereg tau (0 ties). results/analysis/p2_clean_g1.json tie-half 62.5 is the superseded fixed-tau figure (see p7_compare.md); strict agrees.')
d = V['paired_M1_minus_B2']
add('m1_minus_b2_diff', pc(d['fp16_P4']['diff']), ['T1 M1(fp16)-B2 diff'], src=P4C, tol='0.1 pp', unit='pp', display='4.7', note='fp16 M1 (80.8) minus B2 (76.1), paired tie-half; this is the pairing in results/analysis/p4/clean.json T1. The text pairs it with g1_m1_clean_acc (fp32, 81.7), for which the difference is 5.6 pp (CI 0.0 to 11.1): see m1_minus_b2_diff_fp32.')
add('m1_minus_b2_ci', [pc(x) for x in d['fp16_P4']['ci']], ['T1 CI lo', 'T1 CI hi'], tol='1 pp (bootstrap)', unit='pp', display='-1.1 to 10.6', ci=[pc(x) for x in d['fp16_P4']['ci']], note='includes zero. Analysis file: -1.1 to 10.3.')
add('m1_minus_b2_diff_fp32', pc(d['fp32_P2']['diff']), None, src=P2C, unit='pp', ci=[pc(x) for x in d['fp32_P2']['ci']], note='fp32 P2 M1 (81.7) minus B2; lower CI bound is exactly 0.0 (boundary), two-sided p 0.053. Verifier-only (no analysis counterpart).', status='info-only')
ev = V['h2_event_info']
add('h2_fallback_n', ev['n_fallback_stored'], None, src=['kaggle/h2_spec_a/matches.json'], tol='exact', unit='pairs', status='verified', note='stored meta n_fallback 178 and per-pair event.fallback flags agree; verifier pixel recompute (p6) gave 178 as well')
add('h2_pairs_n', ev['meta_n_pairs'], None, src=['kaggle/h2_spec_a/matches.json'], tol='exact', unit='pairs', status='verified')
add('h2_mi_median', round(ev['m_i_median_gray'], 3), None, src=['kaggle/h2_spec_a/matches.json'], tol='0.01', unit='grey levels of 255', display='0.33', note='median over 180 pairs of 255 x m_i (stored matched magnitude, mean |v-p| over the event window incl. fallback windows); IQR %s; max %.2f. Independently recomputed from dev pixels (D(t) mean |v-p| at 224 px, linear resize, mean over [t_on,t_off)): median %.4f, max abs deviation from stored m_i %.1e.' % ([round(x, 2) for x in ev['m_i_iqr_gray']], ev['m_i_max_gray'], ev['m_i_pixel_recompute_median_gray'], ev['m_i_pixel_vs_stored_max_abs_diff']), status='verified')
add('h2_lg_in_band', pc(ev['mid_ratio']['lighting_global']['frac_in_0p9_1p1']), None, src=['kaggle/h2_spec_a/matches.json'], tol='exact count', unit='%', display='50.0', status='info-only', note='NOT recomputed from pixels (needs the edit code); read from stored matches.json, agrees with its meta (0.5) and with the analysis notes. 270 of 540 (180 pairs x 3 seeds) mid-strength entries with achieved/target ratio in [0.9,1.1]; 12 entries have undefined ratio (m_i = 0) and count as out of band. Matches stored meta (0.5). Local lighting 96.7%, jolt 97.8%, zoom 97.8%.')
add('h2_entries_n', 180, None, src=['P4_M1_ipdev_lighting_global-mid_s{1,2,3}'], unit='entries', status='verified', note='180 pairs per seed (540 over 3 seeds); the no-op count is per seed and identical in the 3 seeds')
add('h2_lg_noop_n', V['lg_noop']['s1']['n_evmax_within_tau2'], ['lighting_global mid no-op (effect<=tau) seed 1', 'lighting_global mid no-op (effect<=tau) seed 2', 'lighting_global mid no-op (effect<=tau) seed 3'], src=['P4_M1_ipdev_lighting_global-mid_s1..3', 'P4_M1_ipdev_clean_s1'], tol='exact', unit='entries', display='84',
    note='definition: |S_event-aligned-max(edited) - S(clean)| <= tau_m (1.0875e-4); 84 of 180 in each seed. Of these, %d videos are bitwise identical to clean over all 17 windows (edit rounds to nothing); the remainder moved by less than tau.' % V['lg_noop']['s1']['n_bitwise_identical_to_clean'])
h2 = V['h2']['M1']
add('h2_A', round(h2['all']['A_point']['M'], 4), ['H2 M1 A'], src=['P4_M1_ipdev_{lighting_global,lighting_local,jolt_base,zoom_base}-mid_s1..3', 'P4_M1_ipdev_clean_s1', 'P4_M1_ipdev_base_ref-ref_s1'], tol='0.002', unit='AUROC', display='0.546', note='event-aligned max, stored matches t_on (178/180 fallback onset 48), tie-half, mean of 4 per-type AUROCs, seeds averaged')
add('h2_A_ci', [round(x, 4) for x in h2['all']['A_ci']['M']], ['H2 M1 A CI lo', 'H2 M1 A CI hi'], tol='0.01', ci=[round(x, 4) for x in h2['all']['A_ci']['M']], display='0.501 to 0.591')
add('h2_A_nolg', round(h2['no_lighting_global']['A_point']['M'], 4), ['H2 M1 A excl lighting_global'], tol='0.002', unit='AUROC', display='0.520')
add('h2_A_nolg_ci', [round(x, 4) for x in h2['no_lighting_global']['A_ci']['M']], ['H2 M1 A excl lg CI lo', 'H2 M1 A excl lg CI hi'], tol='0.01', ci=[round(x, 4) for x in h2['no_lighting_global']['A_ci']['M']], display='0.475 to 0.565')
add('h2_A0', round(h2['A0']['M']['A0'], 4), ['H2 M1 A0'], tol='0.001', unit='accuracy', display='0.722', ci=[round(x, 4) for x in h2['A0']['M']['ci']], note='clean tie-half accuracy under the event-aligned max aggregation; 22 ties; strict 0.667; precondition 0.85 not met')
add('h2_B1_A', round(h2['all']['A_point']['B1'], 4), ['H2 M1 A_B1'], tol='0.002', unit='AUROC', display='0.335')
add('h2_B2_A', round(h2['all']['A_point']['B2'], 4), ['H2 M1 A_B2'], tol='0.002', unit='AUROC', display='0.379')
add('h2_tau', float('%.5g' % h2['tau']['M']), ['H2 M1 tau'], tol='1e-9', unit='score units', display='1.09e-4', note='tau_m for H2/H3 = 2e-4 x median of 360 clean full-clip-max scores; B1 1.467e-6, B2 2.920e-6')
h1 = V['h1']['M1']
add('h1_f0', pc(h1['dither']['f0_all']), ['H1 M1 f0'], src=['P4_M1_ipdev_dither-on_s1..3', P4C[0]], tol='0.1 pp', unit='%', display='21.5', note='mean over 3 dither seeds of the fraction of the 180 pairs whose 3-way verdict class changes vs clean (tau_mean 1.057e-4)')
add('h1_f0_strict', pc(h1['dither']['f0_strict_all']), ['H1 M1 strict f0'], tol='0.1 pp', unit='%', display='15.6', note='strict convention: tau = 0, class = sign of the margin (exact ties counted as their own class; none occur). Binary right/wrong flip rate would be %.1f%%.' % pc(h1['dither']['flip_binary_correct']))
add('h1_jpeg_p_cluster', round(h1['stats']['jpeg']['holm_dacc'], 4), ['H1 M1 jpeg Holm-14 dAcc'], tol='Holm x MC error', unit='p', display='< 0.0001', note='tie-half, cluster-bootstrap dAcc, Holm-14; raw p < 1e-4 (0 of 10,000 draws). Strict convention: Holm-14 %.4f (analysis 0.0176; MC).' % h1['stats']['jpeg']['holm_dacc_strict'])
add('h1_jpeg_p_sign', round(h1['stats']['jpeg']['holm_sign'], 4), ['H1 M1 jpeg Holm-14 sign-fam sign'], tol='0.03', unit='p', display='0.018', note='tie-half, exact sign test, Holm over its own 14-p family (7 sign + 7 flip-vs-floor). IMPORTANT: under the tie-half convention both tests are Holm-significant (< .05), so they do NOT disagree on significance; the cluster/sign disagreement exists under the STRICT convention (cluster Holm-14 dAcc %.4f vs sign Holm-14 %.4f; analysis 0.0176 vs 0.1151). The text should say which convention it quotes.' % (h1['stats']['jpeg']['holm_dacc_strict'], h1['stats']['jpeg']['holm_sign_strict']))
add('h1_jpeg_p_cluster_strict', round(h1['stats']['jpeg']['holm_dacc_strict'], 4), ['H1 strict jpeg Holm-14 dAcc'], tol='Holm x MC error', unit='p', note='strict convention (tau = 0); analysis value 0.0176 (MC)')
add('h1_jpeg_p_sign_strict', round(h1['stats']['jpeg']['holm_sign_strict'], 4), ['H1 strict jpeg Holm-14 sign'], tol='0.03', unit='p', note='strict convention; analysis 0.1151')
add('h1_zoom_n', h1['stats']['zoom']['n_pairs'], ['H1 M1 zoom n'], tol='exact', unit='pairs', display='112', note='stored matches.json support_retention_crop >= 0.9 (crop 0.7); verifier pixel retention gives 110 (cm_win) - see p6')
add('h1_pairs_n', 180, None, src=P4C, tol='exact', unit='pairs', status='verified')
pv = V['precision']
add('prec_verdict_change', round(100 * pv['own_tau']['class_change_frac'], 2), ['prec verdicts changed (tie-half) n'], src=['P2_M1_ipdev_clean_s1', P4C[0]], tol='exact count', unit='%', display='2.8', note='5 of 180 pairs change 3-way verdict class (fp16 P4 vs fp32 P2, each at its own tau; same count at a common tau). Strict (tau=0): 1 of 180 (0.56%).')
add('prec_margin_noise_max', float('%.3g' % pv['max_abs_window_margin_diff']), None, src=['P2_M1_ipdev_clean_s1', P4C[0]], unit='score units', display='1.7e-3', status='info-only',
    note='DEFINITION CHOICE: max over pairs and windows of |(S_imp - S_pos)_fp16 - (...)_fp32| per window (min over C) = 1.69e-3; elementwise per-window score difference max 2.0e-3; per-(window,C) S max 2.65e-3; median per-window margin diff 5.4e-5, 99th pct 7.6e-4. The analysis file (precision_audit.json) reports only the pair-level (17-window-mean) margin difference max 5.51e-4 (verified, key prec_pair_margin_noise_max). The text says "per-window", so 1.7e-3 is the matching figure; lead to confirm.')
add('prec_pair_margin_noise_max', float('%.3g' % pv['max_abs_pair_mean_margin_diff']), ['prec max pair-margin diff'], unit='score units', tol='1e-7', display='5.5e-4', src=['P2_M1_ipdev_clean_s1', P4C[0]])
add('m2_old_acc', pc(ca['M2_mi1_old']['tiehalf']), ['M2 mi1 old clean tie-half'], src=['P4_M2_ipdev_clean_s1'], tol='0.1 pp', unit='%', display='46.9', note='mask_index 1; strict 46.7; 19 ties')
add('m2_new_acc', pc(ca['M2_mi0']['tiehalf']), ['M2 mi0 clean tie-half'], src=['P4_M2_ipdev_clean-mi0_s1'], tol='0.1 pp', unit='%', display='60.8', note='mask_index 0; strict 60.6; 17 ties; below the 80% H1 eligibility threshold')
# ---------------- structured: clean / baselines
def clean_row(key, c, src, lab=None, note=None, exploratory=False):
    add(key + '.tiehalf', pc(c['tiehalf']), lab, src=src, tol='0.1 pp', unit='%', note=note, status=None if lab else 'info-only')
    add(key + '.strict', pc(c['strict']), None, src=src, tol='0.1 pp', unit='%', status='info-only' if not lab else 'verified')
clean_row('clean.M1_fp16', ca['M1_fp16_P4'], P4C, ['M1 fp16 clean tie-half', 'M1 fp16 clean strict'])
clean_row('clean.M1_fp32', ca['M1_fp32_P2'], P2C, ['P2 fp32 tie-half'])
add('clean.M1_fp32.strict', pc(ca['M1_fp32_P2']['strict']), ['P2 fp32 strict'], src=P2C, unit='%', tol='0.1 pp')
add('clean.M1H_fp16.strict', pc(ca['M1H_fp16_P2H']['strict']), ['ViT-H strict'], src=['P2H_M1H_ipdev_clean_s1'], unit='%', tol='0.1 pp')
add('clean.B1_P2.tiehalf', pc(ca['B1_P2_fp32']['tiehalf']), None, src=P2C, unit='%', tol='0.1 pp', status='mismatch', note='prereg-tau tie-half 58.1 (reproduces PREREG s0); results/analysis/p2_clean_g1.json shows 50.0 under the superseded fixed tau; strict 57.2 agrees')
add('clean.B1_P2.strict', pc(ca['B1_P2_fp32']['strict']), ['P2 B1 strict'], src=P2C, unit='%', tol='0.1 pp')
add('clean.B2_P2.strict', pc(ca['B2_P2_fp32']['strict']), ['P2 B2 strict'], src=P2C, unit='%', tol='0.1 pp')
add('clean.B3_P2.tiehalf', pc(ca['B3_P2_fp32']['tiehalf']), None, src=P2C, unit='%', status='info-only')
add('clean.M2_mi0.strict', pc(ca['M2_mi0']['strict']), ['M2 mi0 clean strict'], src=['P4_M2_ipdev_clean-mi0_s1'], unit='%', tol='0.1 pp')
add('clean.M2_old.strict', pc(ca['M2_mi1_old']['strict']), ['M2 mi1 old strict'], src=['P4_M2_ipdev_clean_s1'], unit='%', tol='0.1 pp')
add('clean.M2_mi0.ties', ca['M2_mi0']['n_ties'], ['M2 mi0 ties'], unit='pairs', tol='exact', src=['P4_M2_ipdev_clean-mi0_s1'])
add('clean.M2_B2.tiehalf', pc(ca['B2_P4_fp16_M2']['tiehalf']), None, src=['P4_M2_ipdev_clean-mi0_s1'], unit='%', status='info-only', note='M2 run B2 array (native 256 px)')
# ---------------- H1 tables
for M in ('M1', 'M2'):
    for e, x in V['h1'][M]['stats'].items():
        L = lambda s: f'H1 {M} {e} {s}'
        src = [f'P4_{M}_ipdev_{e}-high_s*', f'P4_{M}_ipdev_clean_s1' if M == 'M1' else 'P4_M2_ipdev_clean-mi0_s1', f'P4_{M}_ipdev_dither-on_s1..3']
        add(f'h1.{M}.{e}.n', x['n_pairs'], [L('n')], src=src, tol='exact', unit='pairs')
        add(f'h1.{M}.{e}.dacc_pp', pc(x['dacc']), [L('dAcc')], ci=[pc(x['dacc_ci'][0]), pc(x['dacc_ci'][1])], src=src, tol='0.1 pp (CI 1 pp)', unit='pp')
        add(f'h1.{M}.{e}.flip_pct', pc(x['flip']), [L('flip')], src=src, tol='0.1 pp', unit='%')
        add(f'h1.{M}.{e}.flip_minus_f0_pp', pc(x['flip_minus_f0']), [L('flip-f0')], ci=[pc(x['flip_minus_f0_ci'][0]), pc(x['flip_minus_f0_ci'][1])], src=src, tol='0.1 pp', unit='pp')
        add(f'h1.{M}.{e}.holm14_dacc', round(x['holm_dacc'], 4), [L('Holm-14 dAcc')], src=src, tol='Holm x MC', unit='p')
        add(f'h1.{M}.{e}.holm14_flip', round(x['holm_flip'], 4), [L('Holm-14 flip')], src=src, tol='Holm x MC', unit='p')
        add(f'h1.{M}.{e}.p_sign', round(x['p_sign'], 5), [L('sign p')], src=src, tol='1e-5', unit='p')
    add(f'h1.{M}.f0_pct', pc(V['h1'][M]['dither']['f0_all']), [f'H1 {M} f0'], src=[f'P4_{M}_ipdev_dither-on_s1..3'], unit='%', tol='0.1 pp', note='M2 f0 is %.1f%% (descriptive; M2 not H1-eligible)' % pc(V['h1']['M2']['dither']['f0_all']) if M == 'M2' else None)
add('h1.M1.fps_halve.identical_to_skip4_clean', V['h1']['M1']['fps_halve_identical_to_skip4_clean'], None, src=['P4_M1_ipdev_fps_halve-high_s1', 'P4_M1_ipdev_clean-skip4_s1'], status='verified', note='bitwise-equal pair scores: dAcc = flip = 0 by construction (pre-registration design error); same for M2')
# ---------------- H2 / H3 (M1, M2) + CI
for M, tag in (('M1', 'H2 M1'), ('M2', 'H2 M2')):
    h = V['h2'][M]; s = h['all']
    for b in ('B1', 'B2'):
        add(f'h2.{M}.D_{b}', round(s['D'][b]['D'], 4), [f'{tag} D_{b}'], ci=[round(x, 4) for x in s['D'][b]['ci']], tol='0.002', unit='AUROC diff')
        add(f'h2.{M}.holm2_{b}', round(s['D'][b]['holm2'], 5), [f'{tag} Holm-2 {b}'], tol='MC', unit='p')
        add(f'h2.{M}.D_{b}.no_lg', round(h['no_lighting_global']['D'][b]['D'], 4), [f'{tag} D_{b} excl lg'], ci=[round(x, 4) for x in h['no_lighting_global']['D'][b]['ci']], tol='0.002', unit='AUROC diff')
    add(f'h2.{M}.A', round(s['A_point']['M'], 4), [f'{tag} A'], ci=[round(x, 4) for x in s['A_ci']['M']], tol='0.002', unit='AUROC')
    add(f'h2.{M}.A_nolg', round(h['no_lighting_global']['A_point']['M'], 4), [f'{tag} A excl lighting_global'], ci=[round(x, 4) for x in h['no_lighting_global']['A_ci']['M']], tol='0.002', unit='AUROC')
    add(f'h2.{M}.A0', round(h['A0']['M']['A0'], 4), [f'{tag} A0'], ci=[round(x, 4) for x in h['A0']['M']['ci']], tol='0.001', unit='accuracy')
    add(f'h2.{M}.A_B1', round(s['A_point']['B1'], 4), [f'{tag} A_B1'], tol='0.002'); add(f'h2.{M}.A_B2', round(s['A_point']['B2'], 4), [f'{tag} A_B2'], tol='0.002')
    for t, v in s['per_type']['M'].items(): add(f'h2.{M}.A.{t}', round(v, 4), [f'{tag} A {t}'], tol='0.002', unit='AUROC')
    add(f'h2.{M}.outcome', h['outcome'], None, status='verified', note='rule applied as in prereg s6 (verifier code); equals the analysis outcome (Detection-limited); M2 also upper CI of A < 0.5 ("Reversed" sub-label) per verifier' if M == 'M2' else 'rule applied as in prereg s6')
h3m2 = V['h3']['M2']
add('h3.M2.vflip_det', pc(h3m2['vflip_a_ref_p']['det']), ['H3 M2 vflip (a)'], ci=[pc(x) for x in h3m2['vflip_a_ref_p']['ci']], unit='%', tol='0.1 pp', src=['P4_M2_ipdev_vflip-high_s1', 'P4_M2_ipdev_clean-mi0_s1'])
add('h3.M2.vflip_det_ref_hflip', pc(h3m2['vflip_b_ref_hflip']['det']), ['H3 M2 vflip (b)'], ci=[pc(x) for x in h3m2['vflip_b_ref_hflip']['ci']], unit='%', tol='0.1 pp')
add('h3.M2.reversal_det', pc(h3m2['reversal_ref_p']['det']), ['H3 M2 reversal'], ci=[pc(x) for x in h3m2['reversal_ref_p']['ci']], unit='%', tol='0.1 pp')
add('h3.M2.hflip_det', pc(h3m2['hflip_ref_p']['det']), None, ci=[pc(x) for x in h3m2['hflip_ref_p']['ci']], unit='%', status='info-only', note='verifier only (no analysis counterpart)')
add('h3.M2.minus_M0r_vflip', pc(h3m2['model_minus_M0r_vflip']['diff']), ['H3 M2 minus M0r vflip'], ci=[pc(x) for x in h3m2['model_minus_M0r_vflip']['ci']], unit='pp', tol='0.1 pp')
add('h3.M2.pairwise_vflip_tiehalf', pc(h3m2['pairwise_acc_vflip']['tiehalf']), ['H3 M2 pairwise vflip tie-half'], unit='%', tol='0.1 pp')
add('h3.M2.G2_pass', h3m2['G2_pass'], ['H3 M2 G2'], status=None)
add('h3.M1.minus_M0r_vflip', pc(h3['model_minus_M0r_vflip']['diff']), ['H3 M1 minus M0r vflip'], ci=[pc(x) for x in h3['model_minus_M0r_vflip']['ci']], unit='pp', tol='0.1 pp')
add('h3.M1.vflip_det_ref_hflip', pc(h3['vflip_b_ref_hflip']['det']), ['H3 M1 vflip (b)'], ci=[pc(x) for x in h3['vflip_b_ref_hflip']['ci']], unit='%', tol='0.1 pp')
# ---------------- dose-response M1
for lv, h in V['h2_dose_M1'].items():
    s = h['all']; lab = lambda x: f'dose-spec {lv} {x}'
    add(f'dose.h2.M1.{lv}.A', round(s['A_point']['M'], 4), [lab('A')], ci=[round(x, 4) for x in s['A_ci']['M']], tol='0.002', unit='AUROC')
    add(f'dose.h2.M1.{lv}.D_1', round(s['D']['B1']['D'], 4), [lab('D_1')], ci=[round(x, 4) for x in s['D']['B1']['ci']], tol='0.002'); add(f'dose.h2.M1.{lv}.D_2', round(s['D']['B2']['D'], 4), [lab('D_2')], ci=[round(x, 4) for x in s['D']['B2']['ci']], tol='0.002')
    add(f'dose.h2.M1.{lv}.holm6_D1', round(s['D']['B1']['holm6'], 5), [lab('Holm-6 B1')], tol='0.001', unit='p'); add(f'dose.h2.M1.{lv}.holm6_D2', round(s['D']['B2']['holm6'], 5), [lab('Holm-6 B2')], tol='0.001', unit='p')
    for t, x in h['per_type_D'].items():
        add(f'dose.h2.M1.{lv}.{t}.A', round(x['B1']['A'], 4), [lab(f'{t} A')], tol='0.002'); add(f'dose.h2.M1.{lv}.{t}.D_1', round(x['B1']['D'], 4), [lab(f'{t} D_1')], tol='0.002'); add(f'dose.h2.M1.{lv}.{t}.D_2', round(x['B2']['D'], 4), [lab(f'{t} D_2')], tol='0.002')
        add(f'dose.h2.M1.{lv}.{t}.holm24', round(max(x['B1']['holm24'], x['B2']['holm24']), 5), [lab(f'{t} Holm-24 B1'), lab(f'{t} Holm-24 B2')], tol='0.001', unit='p')
for c, x in V['h1_dose_M1'].items():
    if c.endswith('_allpairs') or c.endswith('_keep112'): continue
    lab = lambda s: f'H1 dose {c} {s}'
    add(f'dose.h1.M1.{c}.dacc_pp', pc(x['dacc']), [lab('dAcc')], ci=[pc(x['dacc_ci'][0]), pc(x['dacc_ci'][1])], unit='pp', tol='0.1 pp', note='zoom keep set: scale-specific pixel retention >=0.9 (134/120/112 pairs); stored 0.7 retention for high' if c.startswith('zoom') else None)
    add(f'dose.h1.M1.{c}.flip_pct', pc(x['flip']), [lab('flip')], unit='%', tol='0.1 pp'); add(f'dose.h1.M1.{c}.n', x['n_pairs'], [lab('n')], unit='pairs', tol='exact')
    add(f'dose.h1.M1.{c}.holm30_dacc', round(x['holm30_dacc'], 4), [lab('Holm-30 dAcc')], unit='p', tol='Holm x MC'); add(f'dose.h1.M1.{c}.holm30_flip', round(x['holm30_flip'], 4), [lab('Holm-30 flip')], unit='p', tol='Holm x MC')
# ---------------- exploratory
o = V['expl_onset']; so = o['all']
x_ = 'EXPLORATORY onset-aligned'
add('expl.onset.A', round(so['A_point']['M'], 4), ['EXPL onset A'], ci=[round(v, 4) for v in so['A_ci']['M']], exploratory=True, unit='AUROC', tol='0.002', src=['EXPL_M1_ipdev_onset-*-mid_s*', 'kaggle/expl_onset_spec/matches.json'], note='EXPLORATORY post-hoc (Q11). Upper CI < 0.5 so the "Reversed" sub-label applies by rule.')
add('expl.onset.A0', round(o['A0']['M']['A0'], 4), ['EXPL onset A0'], exploratory=True, ci=[round(v, 4) for v in o['A0']['M']['ci']], tol='0.001')
for b, nm in (('B1', 'D_1'), ('B2', 'D_2')):
    add(f'expl.onset.{nm}', round(so['D'][b]['D'], 4), [f'EXPL onset D_{b}'], ci=[round(v, 4) for v in so['D'][b]['ci']], exploratory=True, tol='0.002')
    add(f'expl.onset.holm2_{nm}', round(so['D'][b]['holm2'], 5), [f'EXPL onset Holm-2 {b}'], exploratory=True, unit='p', tol='MC', note='verifier 0.0026 vs analysis 0.0018 for D_1 (MC noise)' if b == 'B1' else None)
add('expl.onset.A_B1', round(so['A_point']['B1'], 4), ['EXPL onset A_B1'], exploratory=True); add('expl.onset.A_B2', round(so['A_point']['B2'], 4), ['EXPL onset A_B2'], exploratory=True)
add('expl.onset.A_nolg', round(o['no_lighting_global']['A_point']['M'], 4), ['EXPL onset A excl lighting_global'], exploratory=True, ci=[round(v, 4) for v in o['no_lighting_global']['A_ci']['M']])
for t, v in so['per_type']['M'].items(): add(f'expl.onset.A.{t}', round(v, 4), [f'EXPL onset A {t}'], exploratory=True)
add('expl.onset.n_transient', o['event_info']['n_transient'], None, exploratory=True, status='verified', src=['kaggle/expl_onset_spec/matches.json'], unit='pairs', note='stored flags; t_on median 49, range 16-88, 0 fallback')
hh = V['expl_halve_hold']
add('expl.halve_hold.dacc_pp', pc(hh['dacc']), ['EXPL halve_hold dacc'], exploratory=True, ci=[pc(hh['dacc_ci'][0]), pc(hh['dacc_ci'][1])], unit='pp', tol='0.1 pp', src=['EXPL_M1_ipdev_halve_hold-high_s1', 'P4_M1_ipdev_clean_s1'])
add('expl.halve_hold.flip_pct', pc(hh['flip']), ['EXPL halve_hold flip'], exploratory=True, unit='%', tol='0.1 pp'); add('expl.halve_hold.f0_pct', pc(hh['f0_dither']), ['EXPL halve_hold f0'], exploratory=True, unit='%', tol='0.1 pp')
add('expl.halve_hold.flip_minus_f0_pp', pc(hh['flip_minus_f0']), ['EXPL halve_hold flip_minus_f0'], exploratory=True, ci=[pc(hh['flip_minus_f0_ci'][0]), pc(hh['flip_minus_f0_ci'][1])], unit='pp', tol='0.1 pp')
# ---------------- IntPhys 2 Main
mn = V['ip2_main']
for nm in ('M1', 'B1', 'B2', 'B3'):
    for st_ in ('all', 'without_debug_overlap'):
        c = mn[nm][st_]
        add(f'ip2main.{nm}.{st_}.tiehalf', pc(c['tiehalf']), [f'Main {nm} {st_} tie-half'], ci=[pc(c['tiehalf_ci'][0]), pc(c['tiehalf_ci'][1])], unit='%', tol='0.1 pp (CI 1 pp)', src=['P4_M1_ip2main_clean_s1'], note='descriptive; scene-cluster bootstrap CI (253 scenes)')
        add(f'ip2main.{nm}.{st_}.strict', pc(c['strict']), [f'Main {nm} {st_} strict'], unit='%', tol='0.1 pp'); add(f'ip2main.{nm}.{st_}.n_pairs', c['n'], None, status='verified', unit='pairs', src=['P4_M1_ip2main_clean_s1'])
        for b, v in c['per_block'].items(): add(f'ip2main.{nm}.{st_}.{b}.tiehalf', pc(v['tiehalf']), [f'Main {nm} {st_} {b} tie-half'], unit='%', tol='0.1 pp', src=['P4_M1_ip2main_clean_s1'])
add('ip2main.n_debug_overlap_videos', mn['n_debug_name_overlap_videos'], ['Main overlap videos'], unit='videos', tol='exact'); add('ip2main.n_debug_overlap_pairs', mn['n_pairs_with_debug_overlap'], ['Main overlap pairs'], unit='pairs', tol='exact')
# ---------------- pending / not verifiable
for kk, why in (('m2.dose.h1.{brightness,noise,blur,jpeg,zoom}.{low,mid}.dacc_pp / flip_pct', 'M2 H1 dose-response runs (low/mid) still running'),
                ('m2.dose.h2.{lighting_global,lighting_local,jolt_base,zoom_base}.{low,high}.A / D_1 / D_2 / holm', 'M2 spec dose-response (low/high) runs still running; only mid exists'),
                ('m2.dose.h2.pooled.{low,mid,high}.A / D_1 / D_2', 'depends on the pending M2 low/high spec runs'),
                ('clean.B1_whole_window.tiehalf (58.6)', 'b1_whole_window is not stored in the run arrays; not recomputable by the verifier'),
                ('m3.*', 'M3 (VideoMAE V2) not run'), ('ip2main.h2', 'H2 on IntPhys 2 Main not run by design (no event-time column)')):
    E.append(dict(key=kk, value=None, ci=None, unit=None, sources=[], tolerance=None, status='pending', exploratory=False, note=why))
out = dict(generated=str(datetime.date.today()), generator='verify/p7_make_verified.py (values from verify/p7_recompute.json = verifier code, no src/analysis; status from verify/p7_compare.md)',
           conventions='tie-half primary; tau_m = 2e-4 x median score (mean agg for clean/H1, full-clip max for H2/H3); bootstrap seed 20261015, 10,000 scene-cluster draws stratified by block; percentages in % units, pp = absolute percentage points',
           status_legend={'verified': 'verifier recompute agrees with results/analysis within tolerance (and with the prereg where it quotes a value)', 'mismatch': 'verifier and analysis/prereg differ; see note; writer must not use without lead decision', 'info-only': 'verifier-only or definition-dependent; usable as stated in the note', 'pending': 'not yet verifiable (runs missing / not stored)'},
           entries=E)
import os
os.makedirs('results', exist_ok=True)
json.dump(out, open('results/VERIFIED.json', 'w'), indent=1)
from collections import Counter
print(Counter(e['status'] for e in E), len(E))
