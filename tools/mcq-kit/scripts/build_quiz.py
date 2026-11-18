"""Step 10. Build the tap-to-answer quiz page for a subject into the website repo.
Usage: python build_quiz.py WORK REPO SLUG "Title" KEY
  e.g. python build_quiz.py work/obgyn repo obgyn "Obs & Gynae MCQ Practice" obg_mcq
Writes REPO/SLUG/quiz.html from templates/quiz_template.html.
Each item may carry a permanent "qid" (used as the progress id); new items without one get "<chapter>-<position>".
KEY must be unique per subject and NEVER change later (it is the localStorage key that holds Kashaf's progress;
changing it wipes her progress). Item ids are "<chapter>-<n>", so append new questions at the END of a chapter
when updating a bank, never reorder, or saved answers will point at the wrong questions.
"""
import sys, os, json
W, REPO, SLUG, TITLE, KEY = sys.argv[1:6]
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tax = json.load(open(os.path.join(W, 'taxonomy.json'))); data = []
for sec in tax['sections']:
    for c, name in sec['chapters']:
        p = os.path.join(W, 'final', c + '.json')
        if not os.path.exists(p): continue
        for i, it in enumerate(json.load(open(p))):
            o = it.get('options') or {}
            data.append({'s': sec['title'], 't': (f'{c}. ' if c[0].isdigit() else '') + name, 'id': it.get('qid') or f'{c}-{i+1}', 'q': it['stem'], 'o': o,
                         'a': it.get('answer') if it.get('answer') in o else None, 'at': it.get('answer_text') or o.get(it.get('answer'), ''),
                         'e': it.get('explanation', ''), 'k': it.get('key_note', ''), 'n': 1 if it.get('_new') else 0})
tpl = open(os.path.join(KIT, 'templates', 'quiz_template.html')).read()
html = tpl.replace('__TITLE__', TITLE).replace('__KEY__', KEY).replace('/*DATA*/[]', json.dumps(data, ensure_ascii=False))
os.makedirs(os.path.join(REPO, SLUG), exist_ok=True)
open(os.path.join(REPO, SLUG, 'quiz.html'), 'w').write(html)
print(f'{len(data)} MCQs -> {REPO}/{SLUG}/quiz.html')
print('Add to SUBJECTS in REPO/index.html:', json.dumps({'href': f'{SLUG}/quiz.html', 'title': 'MCQ Practice', 'desc': f'{len(data):,} MCQs with answers and explanations'}))
