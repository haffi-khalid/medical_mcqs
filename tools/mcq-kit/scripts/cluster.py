"""Step 4. Group copies of the same question (fuzzy match on stem + option set) and make classification batches.
Usage: python cluster.py WORK [batches=5]
Writes WORK/clusters.json [{cid, members:[uid]}], WORK/cand_pairs.json (borderline cluster pairs for the
review agents), WORK/classify/batchN.tsv (cid, stem, options) for the classifier agents.
Thresholds come from the surgery run: auto-merge if stem>=88 and options>=85; borderline if stem>=70 & opts>=60, or stem>=88.
Needs: rapidfuzz, numpy.
"""
import sys, os, re, json
from rapidfuzz import fuzz
from rapidfuzz.process import cdist
W = sys.argv[1]; NB = int(sys.argv[2]) if len(sys.argv) > 2 else 5
A = json.load(open(os.path.join(W, 'all_raw.json')))
def norm(s):
    s = (s or '').lower()
    s = re.sub(r'^\s*\(?\d{1,3}\s*[.,):\-]\s*', '', s)                       # leading question numbers
    s = re.sub(r'\d+\s*(-|\s)?\s*(years?|yrs?|yr|months?)\s*(-|\s)?(old)?', ' AGE ', s)
    return re.sub(r'[^a-z0-9 ]', ' ', s)
S = [norm(x['stem']) for x in A]
O = [' '.join(sorted(norm(v) for v in (x.get('options') or {}).values())) for x in A]
ms = cdist(S, S, scorer=fuzz.token_set_ratio, workers=-1); mr = cdist(S, S, scorer=fuzz.ratio, workers=-1)
mo = cdist(O, O, scorer=fuzz.token_set_ratio, workers=-1)
n = len(A); par = list(range(n))
def f(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
cand = []
for i in range(n):
    for j in range(i + 1, n):
        s = max(ms[i, j] * 0.5 + mr[i, j] * 0.5, mr[i, j]); o = mo[i, j]
        if len(S[i]) < 25 or len(S[j]) < 25: s = mr[i, j]          # short stems: token_set is too generous
        if s >= 88 and o >= 85: par[f(i)] = f(j)
        elif (s >= 70 and o >= 60) or s >= 88: cand.append((i, j))
cl = {}
for i in range(n): cl.setdefault(f(i), []).append(i)
roots = sorted(cl, key=lambda r: min(cl[r]))
C = [{'cid': f'C{k+1:05d}', 'members': [A[m]['uid'] for m in sorted(cl[r])]} for k, r in enumerate(roots)]
r2c = {r: C[k]['cid'] for k, r in enumerate(roots)}
pairs = sorted({tuple(sorted((r2c[f(i)], r2c[f(j)]))) for i, j in cand if f(i) != f(j)})
json.dump(C, open(os.path.join(W, 'clusters.json'), 'w'), indent=0)
json.dump(pairs, open(os.path.join(W, 'cand_pairs.json'), 'w'))
U = {x['uid']: x for x in A}; os.makedirs(os.path.join(W, 'classify'), exist_ok=True)
lines = []
for c in C:
    x = U[c['members'][0]]
    o = ' | '.join(f"{k}) {v}" for k, v in sorted((x.get('options') or {}).items()))
    lines.append(f"{c['cid']}\t{x['stem'][:300]}\t{o[:250]}".replace('\n', ' '))
k = len(lines) // NB + 1
for b in range(NB):
    open(os.path.join(W, 'classify', f'batch{b+1}.tsv'), 'w').write('\n'.join(lines[b*k:(b+1)*k]))
print('raw', n, '-> clusters', len(C), 'borderline pairs', len(pairs))
