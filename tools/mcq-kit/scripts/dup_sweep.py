"""Step 8 helper. Candidate duplicates still left in the final bank (same question + same answer), for the auditors.
Usage: python dup_sweep.py WORK   -> WORK/dup_candidates.json [{a:"CH#idx", b:"CH#idx", stem_sim, ans_sim}]
"""
import sys, os, json, re
from rapidfuzz import fuzz
W = sys.argv[1]
tax = json.load(open(os.path.join(W, 'taxonomy.json'))); codes = [c[0] for s in tax['sections'] for c in s['chapters']]
items = [(ch, i, it) for ch in codes if os.path.exists(os.path.join(W, 'final', ch + '.json')) for i, it in enumerate(json.load(open(os.path.join(W, 'final', ch + '.json'))))]
n = lambda s: re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower())
def at(it): o = it.get('options') or {}; return n(o.get(it.get('answer'), '') or it.get('answer_text', ''))
P = []
for a in range(len(items)):
    for b in range(a + 1, len(items)):
        A, B = items[a][2], items[b][2]
        s = fuzz.token_set_ratio(n(A['stem']), n(B['stem'])); r = fuzz.ratio(at(A), at(B))
        if s >= 72 and r >= 80: P.append({'a': f'{items[a][0]}#{items[a][1]}', 'b': f'{items[b][0]}#{items[b][1]}', 'stem_sim': round(s), 'ans_sim': round(r)})
json.dump(P, open(os.path.join(W, 'dup_candidates.json'), 'w'), indent=0)
print(len(P), 'candidate pairs')
