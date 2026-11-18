"""Step 3. Merge every extraction agent's output into one raw list.
Usage: python merge_extracts.py WORK
Reads WORK/extract/*.json (one per source/part, schema in prompts/EXTRACTION_SPEC.md), skips *KEY*.json answer-book files.
Writes WORK/all_raw.json with a unique uid per question and prints per-file counts.
"""
import sys, os, json, glob
W = sys.argv[1]; allq = []
for f in sorted(glob.glob(os.path.join(W, 'extract', '*.json'))):
    if 'KEY' in os.path.basename(f).upper() and 'SENDUP' not in f.upper(): continue
    d = json.load(open(f)); code = os.path.basename(f)[:-5]
    for x in d:
        x['_file'] = code
        if isinstance(x.get('options'), list): x['options'] = {k: v for k, v in zip('ABCDEFGH', x['options'])}
    print(f'{code:30s} {len(d):5d} marked={sum(1 for x in d if x.get("marked_answer"))}')
    allq += d
ids = [x['id'] for x in allq]
dup = {i for i in ids if ids.count(i) > 1}
if dup: print('WARNING duplicate ids (fix the extract files):', list(dup)[:10])
for i, x in enumerate(allq): x['uid'] = f'U{i+1:05d}'
json.dump(allq, open(os.path.join(W, 'all_raw.json'), 'w'), indent=1, ensure_ascii=False)
print('TOTAL', len(allq))
