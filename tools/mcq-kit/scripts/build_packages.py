"""Step 6. One work package per chapter for the review ("professor") agents.
Usage: python build_packages.py WORK
Needs WORK/taxonomy.json, WORK/clusters.json, WORK/classify/batch*.out.json ({cid: chapter_code}).
Optional: WORK/existing/<CH>.json = an existing verified bank for this subject (list of final items); if present,
each package carries it so agents can drop questions already in that bank.
Writes WORK/pkg/<CH>.json = {chapter, clusters:[{cid, variants:[raw questions]}], possible_duplicate_pairs, existing:[...]}
"""
import sys, os, json, glob, collections
W = sys.argv[1]
A = {x['uid']: x for x in json.load(open(os.path.join(W, 'all_raw.json')))}
C = json.load(open(os.path.join(W, 'clusters.json')))
cls = {}
for f in glob.glob(os.path.join(W, 'classify', 'batch*.out.json')): cls.update(json.load(open(f)))
missing = [c['cid'] for c in C if c['cid'] not in cls]
if missing: sys.exit(f'{len(missing)} clusters unclassified, e.g. {missing[:5]}: rerun the classifier for them')
tax = json.load(open(os.path.join(W, 'taxonomy.json')))
codes = [c[0] for s in tax['sections'] for c in s['chapters']]
bad = {v for v in cls.values() if v not in codes}
if bad: sys.exit(f'classifier used unknown chapter codes: {bad}')
pairs = json.load(open(os.path.join(W, 'cand_pairs.json')))
by = collections.defaultdict(list)
keep = ['uid', 'paper', 'page', 'qnum', 'stem', 'options', 'marked_answer', 'marked_how', 'marked_note', 'source_explanation', 'figure', 'legibility', 'source_file']
for c in C:
    by[cls[c['cid']]].append({'cid': c['cid'], 'variants': [{k: A[u].get(k) for k in keep} for u in c['members']]})
where = {c['cid']: cls[c['cid']] for c in C}
os.makedirs(os.path.join(W, 'pkg'), exist_ok=True)
for ch in codes:
    ex = os.path.join(W, 'existing', ch + '.json')
    pk = {'chapter': ch, 'clusters': by.get(ch, []),
          'possible_duplicate_pairs': [p for p in pairs if where[p[0]] == ch or where[p[1]] == ch],
          'existing': [dict(id=f'{ch}-{i+1}', stem=it['stem'], options=it.get('options'), answer=it.get('answer')) for i, it in enumerate(json.load(open(ex)))] if os.path.exists(ex) else []}
    json.dump(pk, open(os.path.join(W, 'pkg', ch + '.json'), 'w'), indent=1, ensure_ascii=False)
print({ch: len(by.get(ch, [])) for ch in codes})
