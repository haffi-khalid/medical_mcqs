"""Step 7/9. Apply cross-chapter moves and verify that EVERY source question is accounted for.
Usage: python finalize.py WORK
Reads WORK/final/<CH>.json (items: {cids:[...], stem, options, answer, answer_text?, explanation, key_note, move_to?})
and WORK/final/<CH>.dropped.json ([{cid, reason}]). Items with move_to are moved to that chapter.
Exits non-zero (and prints what is wrong) if any cluster is missing or duplicated, an answer is not one of its options,
an explanation is empty, or an em/en dash appears. Split items may use cids like "C00012#U00456" or cids:[] + split_from.
"""
import sys, os, json, glob, collections
W = sys.argv[1]
tax = json.load(open(os.path.join(W, 'taxonomy.json'))); codes = [c[0] for s in tax['sections'] for c in s['chapters']]
F = {ch: json.load(open(os.path.join(W, 'final', ch + '.json'))) for ch in codes if os.path.exists(os.path.join(W, 'final', ch + '.json'))}
for ch in list(F):
    keep = []
    for it in F[ch]:
        mt = (it.pop('move_to', '') or '').strip()
        if mt and mt != ch:
            if mt not in codes: sys.exit(f'bad move_to {mt} in {ch}')
            F.setdefault(mt, []).append(it)
        else: keep.append(it)
    F[ch] = keep
allin = {c['cid'] for c in json.load(open(os.path.join(W, 'clusters.json')))}
cov = collections.Counter(); drop = {}
for ch in F:
    for it in F[ch]:
        for c in it.get('cids', []): cov[c.split('#')[0]] += 1
for f in glob.glob(os.path.join(W, 'final', '*.dropped.json')):
    for d in json.load(open(f)): drop[d['cid']] = d['reason']
problems = []
miss = sorted(allin - set(cov) - set(drop)); multi = [k for k, v in cov.items() if v > 1 and not any('#' in c for ch in F for it in F[ch] for c in it.get('cids', []) if c.startswith(k))]
if miss: problems.append(f'MISSING clusters: {miss[:20]} ({len(miss)})')
if multi: problems.append(f'clusters in more than one item: {multi[:20]}')
n = 0
for ch in F:
    for it in F[ch]:
        n += 1; o = it.get('options') or {}
        if o and it.get('answer') not in o: problems.append(f'{ch}: answer not in options: {it["stem"][:60]}')
        if not o and not it.get('answer_text'): problems.append(f'{ch}: no options and no answer_text: {it["stem"][:60]}')
        if not it.get('explanation'): problems.append(f'{ch}: no explanation: {it["stem"][:60]}')
        s = json.dumps(it, ensure_ascii=False)
        if '\u2014' in s or '\u2013' in s: problems.append(f'{ch}: em/en dash: {it["stem"][:60]}')
for ch in F: json.dump(F[ch], open(os.path.join(W, 'final', ch + '.json'), 'w'), indent=1, ensure_ascii=False)
print('items', n, 'clusters', len(allin), 'covered', len(set(cov) & allin), 'dropped', len(drop))
print({ch: len(F[ch]) for ch in codes if ch in F})
if problems: print('\n'.join(problems[:60])); sys.exit(1)
print('ALL CHECKS PASSED')
