# Handoff: build a topic-wise MCQ bank from past papers and publish it to Kashaf's revision site

You are Claude Code working in Haffman's repo `haffi-khalid/medical_mcqs`. This document tells you exactly how
the existing Surgery bank was built (2,542 verified MCQs from 25 sources) so you can do the same for a new
subject from a pile of PDFs and Word files, then publish it to the website and give Haffman a link for Kashaf
(a final-year MBBS student in Pakistan) that remembers her progress.

Everything you need is in this kit:

```
tools/mcq-kit/
  HANDOFF.md                 this file
  prompts/EXTRACTION_SPEC.md one extraction agent per source file (or part of a big file)
  prompts/CLASSIFY_PROMPT.md classifier agents (sort questions into chapters)
  prompts/PROFESSOR_SPEC.md  review agents: dedupe, verify answers, write explanations (the core step)
  prompts/AUDIT_SPEC.md      independent second-opinion agents
  scripts/prepare_sources.py render pages + text layers + docx markup
  scripts/merge_extracts.py  merge agent outputs into all_raw.json
  scripts/cluster.py         fuzzy-group copies of the same question, make classifier batches
  scripts/build_packages.py  one work package per chapter for the review agents
  scripts/finalize.py        apply moves + hard coverage/quality checks (must print ALL CHECKS PASSED)
  scripts/dup_sweep.py       leftover duplicate candidates for the auditors
  scripts/build_quiz.py      builds <subject>/quiz.html (tap to answer, progress saved, backup codes)
  scripts/build_pdf.py       optional topic-sorted PDFs with answers, explanations and amber key notes
  templates/                 quiz page, site home page (hub), service worker, manifest, icon
  reference/                 the surgery taxonomy (example) and an example spec for a messy 483-page bank
tools/data/surgery/          the finished surgery bank (taxonomy.json + final/<chapter>.json), for reference
```

Requirements (install if missing): `poppler-utils` (pdftoppm, pdftotext, pdfinfo), `tesseract-ocr`,
`python3` with `pip install rapidfuzz numpy reportlab python-docx pymupdf pillow`, fonts-dejavu (for PDFs), git, gh.

---

## 0. Non-negotiables

1. **Nothing missed, nothing duplicated.** Every question in every source must end up as exactly one item, merged
   into its duplicate, or explicitly dropped with a reason (content-less fragment only). `finalize.py` enforces this.
   Never "sample" a file; agents must look at every page.
2. **Answers must be right.** Kashaf memorises these. Paper keys and student answer books are often wrong. The
   reviewer decides the correct answer from standard references and flags every disagreement in `key_note`.
3. **Use agents (subagents) for the heavy work**, in parallel, as described below. Give each agent a private scratch
   folder (`/tmp/<job>`); shared scratch files get clobbered when agents run together.
4. **No em dashes or en dashes** anywhere in output (Haffman's rule). Use commas or colons.
5. **Ask before you start** (section 2). Then work without stopping; report at the end.
6. **Never change a published storage key, and never reorder a published bank** (section 9), or Kashaf loses progress.
7. **Usage limits.** If you hit a rate/usage limit mid-run, note which jobs finished (their output files exist and pass
   their checks), and resume only the unfinished ones later. Never redo finished chapters.

---

## 1. What "the same as Surgery" means (the deliverable)

Per subject:
- `<slug>/quiz.html` on the website: every distinct MCQ, sorted by the subject's textbook chapters. Tap an option:
  green/red, then "Why" explanation, plus an amber "Exam note" where a paper key was wrong/disputed or nothing was
  marked. Topic picker (any mix of sections/topics), shuffle, Unanswered / Got wrong filters, search, score bar,
  two-tap Reset, Save / Restore backup code. Progress saves in her phone's browser.
- A card for it on the site home page (`index.html`, the hub).
- Optional on request: topic-sorted PDFs (mega + per section), and flashcards (section 11).

Live site: `https://haffi-khalid.github.io/medical_mcqs/` (GitHub Pages, branch `main`, root).

---

## 2. Ask Haffman these before starting (use one message / AskUserQuestion)

1. **Subject name and short slug** (e.g. "Obstetrics & Gynaecology", `obgyn`).
2. **The chapter list to sort by.** Best: a photo of the contents page of the textbook Kashaf uses (Surgery used
   Dogar's *Systemic Surgery* contents). Questions that fit no chapter go into an extra "General & Other" section.
3. **Reference books** that settle answers (e.g. Obs: Ten Teachers / Dewhurst; Gynae: Ten Teachers Gynaecology;
   Medicine: Davidson's; Paeds: Nelson/Illustrated Textbook; Surgery used Bailey & Love 28th + ATLS 10th).
4. **Where the source files are** (folder path or attachments) and whether any are answer books / keys.
5. Duplicates: keep one copy, no source tags (Surgery's choice). Wrong keys: correct and flag (Surgery's choice).
   Only ask if he might want something different.

Fill `{SUBJECT}` and `{REFERENCES}` in the prompt files with his answers when you hand them to agents.

---

## 3. Folder layout for a run

```
work/<slug>/
  src/            the user's files (copy them here; never edit originals)
  pages/<CODE>/   page images (prepare_sources.py)
  text/           text layers / docx markup
  extract/        one JSON per source (extraction agents)
  taxonomy.json   chapters (you write it, section 4)
  all_raw.json  clusters.json  cand_pairs.json  classify/  pkg/  final/  audit/  out/
```
Keep `work/` out of git (add to .gitignore). Commit only the website files and `tools/data/<slug>/` (taxonomy +
final JSON) so the bank can be extended later.

---

## 4. Write `work/<slug>/taxonomy.json`

Same schema as `reference/example_taxonomy_surgery.json`:
```json
{"sections":[{"code":"S1","title":"Obstetrics","chapters":[["1","Antenatal care"],["2","..."]]},
             {"code":"S9","title":"General & Other Topics (not in your contents list)","chapters":[["G1","..."],["G9","Miscellaneous"]]}],
 "notes":"routing rules: e.g. ectopic pregnancy -> 6; anaemia in pregnancy -> 3; ..."}
```
Chapter codes are short strings ("1", "35X", "B", "G3"). Mirror the book's chapter order and numbering. Add an extra
"General & Other" section for topics outside the book list, ending in a Miscellaneous chapter. The `notes` routing
rules matter: write 10-20 rules for the ambiguous boundaries of this subject (surgery example in the reference file).

---

## 5. The pipeline (this is exactly how Surgery was done)

### Step 1. Prepare sources
```
python tools/mcq-kit/scripts/prepare_sources.py work/<slug>
```
Read `inventory.json`. Note which PDFs are scans (text_chars near 0): those need visual reading. Huge phone photos are
auto-shrunk. `.doc`/`.pptx`: convert to PDF first (`libreoffice --headless --convert-to pdf`). For .docx the answer is
usually **bold** or ==highlighted== in the markup file.

### Step 2. Extraction agents (parallel)
One agent per source file; split files over ~35 pages into page ranges (one agent per range, tell it to take a
question that straddles the boundary fully, and the next agent to skip it). Group tiny files 2-3 per agent. Prompt:
"Read tools/mcq-kit/prompts/EXTRACTION_SPEC.md and follow it exactly. FOLDER=<pages/CODE> source_file=<name>,
<N> pages. CODE=<CODE>. (Page range if split.)" Replace WORK in the spec with the real path.

Key facts from the Surgery run that the spec already encodes, so expect them:
- Answers are marked every possible way: yellow/green/blue highlight, tick, circle, red handwritten letter, underline,
  bold, asterisk, "Ans:" line, printed key table at the end, "True" labels. **Only page images show highlights**; the
  text layer never does. Agents must look at every page image.
- Highlights often bleed onto the neighbouring option, pen circles from a second student disagree with the highlight,
  printed key tables disagree with highlights. Agents record what they see plus notes; they do not judge.
- Some "papers" are compilations of several papers: label each question with its paper; ids like CODE-PAPERTAG-qnum.
- Student "compiled answer books" (title + answer + explanation, few stems) are extracted separately as
  `extract/<NAME>_KEY.json` (merge_extracts skips files with KEY in the name). Match them to questions later and pass
  their answer as `compiled_key` evidence; items that exist only in the answer book become recall items.
- Unsolved papers (no marks) are normal: marked_answer null.
If an agent says it could not read something, look at the page yourself; if a file arrived blank (image-only PDF
uploaded as text), ask Haffman to re-attach the original.

### Step 3. Merge
```
python tools/mcq-kit/scripts/merge_extracts.py work/<slug>
```
Check the per-file counts against each agent's report (numbering ranges, e.g. 120/120).

### Step 4. Cluster
```
python tools/mcq-kit/scripts/cluster.py work/<slug> 5
```
Groups copies of the same question across papers (Surgery: 2,362 raw -> 1,520 clusters). Borderline pairs go to
the reviewers in their packages.

### Step 5. Classify (parallel, ~300 rows per agent)
One agent per `classify/batchN.tsv` with `prompts/CLASSIFY_PROMPT.md`. Output `classify/batchN.out.json`.

### Step 6. Packages
```
python tools/mcq-kit/scripts/build_packages.py work/<slug>
```
If adding to an existing bank for the same subject, first copy its final items to `work/<slug>/existing/<CH>.json`
(from `tools/data/<slug>/final/`); reviewers will then drop questions already in it (PROFESSOR_SPEC covers this).

### Step 7. Review ("professor") agents (parallel, the core step)
Group chapters so each agent has roughly 80-130 clusters (a big chapter alone, small related chapters together;
keep a section's chapters together where possible so the agent can spot cross-chapter duplicates). Surgery used 14
agents for 1,547 clusters. Prompt: "Read tools/mcq-kit/prompts/PROFESSOR_SPEC.md and follow it exactly. Your chapters:
X, Y, Z. Use scratch folder /tmp/prof_<n>." Each agent writes `final/<CH>.json` (+ `.dropped.json`).
Then:
```
python tools/mcq-kit/scripts/finalize.py work/<slug>
```
Fix every problem it lists (usually: a cluster an agent forgot, a cross-chapter merge listed in the wrong file,
split items). Rerun until **ALL CHECKS PASSED**.

### Step 8. Independent audit agents (parallel, never skip)
```
python tools/mcq-kit/scripts/dup_sweep.py work/<slug>
```
Then fresh agents (not the reviewers) with `prompts/AUDIT_SPEC.md`, about 200-250 items each, split by chapters.
They answer every question themselves before looking, restore over-corrected keys, merge remaining duplicates
(same question + same correct answer even if wording or distractors differ), fix typos. Rerun `finalize.py`.
In Surgery the audit changed only ~2 answers but merged ~150 near-duplicates, so it is mainly a dedupe pass; still
read every agent report for flagged judgement calls and pass the important ones to Haffman.

### Step 9. Spot-check yourself
Open 10 random items per section in `final/` and compare against their source page images (uid -> page in
`all_raw.json`). Recompute any arithmetic (drug doses, fluid formulas, scores).

---

## 6. Build and publish

```
python tools/mcq-kit/scripts/build_quiz.py work/<slug> . <slug> "<Subject> MCQ Practice" <key>
```
- `<key>`: short, unique, permanent, e.g. `obg_mcq`. Surgery uses `surg_mcq` (do not reuse).
- Add the printed entry to the `SUBJECTS` list in the root `index.html` (hub). Example:
  `{name: "Obstetrics & Gynaecology", links: [{href: "obgyn/quiz.html", title: "MCQ Practice", desc: "..."}]}`
- Bump the cache name in `sw.js` (`revision-vN` -> `vN+1`) so phones pick up the new page.
- Copy `work/<slug>/taxonomy.json` and `work/<slug>/final/` to `tools/data/<slug>/`.
- Test locally before pushing: `python3 -m http.server 8765` in the repo, then with Playwright/Chromium at 390x844:
  open the hub, open the quiz, answer 3 questions, reload (score must persist), Save/Restore round-trip, no page
  errors. (Surgery's test script did exactly this.)
- Commit and push:
```
git add index.html sw.js <slug>/ tools/data/<slug>/
git commit -m "Add <Subject> MCQ bank (<N> MCQs)"
git push
```
- Pages is already enabled on `main` / root. If it is not (fresh repo):
  `gh api -X POST repos/haffi-khalid/medical_mcqs/pages -f "source[branch]=main" -f "source[path]=/"`
- Verify: wait ~1-2 min, then `curl -sI https://haffi-khalid.github.io/medical_mcqs/<slug>/quiz.html` returns 200.

Give Haffman: the link `https://haffi-khalid.github.io/medical_mcqs/` (the hub; same link as before, the new subject
just appears on it) and the direct quiz link.

### How Kashaf's progress is saved (tell Haffman if he asks)
- Progress lives in her phone browser's localStorage for `haffi-khalid.github.io`, keyed per subject. It persists when
  she closes the page as long as she opens the **link** in Chrome/Safari (or the home-screen icon), not a WhatsApp
  file preview. The page shows a red warning if it is opened somewhere that cannot save.
- Save / Restore gives a backup code (`MCQ1:...`, Surgery's is `SURG1:...`) she can keep in WhatsApp and paste back.
- Home screen: iPhone Safari Share -> Add to Home Screen; Android Chrome menu -> Add to Home screen.

---

## 7. Lessons from the Surgery run (read before starting)

- Count check every extraction: numbering 1..N with no gaps, or an explained gap (missing page, cropped scan).
- Two copies of the same paper (one solved, one not) are common; extract both, the clustering merges them, the
  differing marks become evidence.
- Expect wrong keys at ~5-10% in student-solved papers; reviewers corrected ~150 of 1,336 in Surgery. Classic traps:
  "most common X" questions where old keys follow outdated editions; staging (TNM edition changes); drug doses.
  Keep the exam-accepted answer when it is defensible and put the modern nuance in the explanation.
- Questions that refer to "the above case" must be rewritten to stand alone.
- Recall-only items (no options survive) are kept with `answer_text`; the quiz shows a Reveal button for them.
- A tiny share of items will have 4 or 6 options or garbled text: reviewers repair from page images.
- Cross-chapter merges: an agent may put a cluster from another chapter into its own file; finalize.py accepts that as
  long as each cluster appears exactly once overall.
- Agents sometimes overwrite shared /tmp files; always give each one its own scratch folder.
- Scanned PDFs whose text layer is empty must be read from images (tesseract helps with wording but is often poor).
- Very large single-file banks (hundreds of pages, mixed marking: asterisks + highlights + "Correct Answer:" lines):
  parse programmatically with PyMuPDF (highlight annotations are type 8; use them to flag highlighted options),
  then send everything through the same cluster/classify/review steps. See reference/example_spec_large_bank...md.

---

## 8. Adding a new set of papers to an EXISTING subject later

Run the pipeline on the new files only, with `existing/` filled from `tools/data/<slug>/final/` (step 6). Reviewers
drop duplicates of existing items. Then **append** the new items to the END of each chapter's final list (never insert
or reorder: quiz ids are `<chapter>-<position>`), tag them `"_new": true` if Haffman wants a "New" filter, rebuild the
quiz with the SAME key, push.

## 9. Never break saved progress
- Never change a subject's storage key or slug folder after publishing.
- Never reorder or delete items in a published chapter; to retire a bad item, fix its text in place.
- Keep the site on the same origin (haffi-khalid.github.io); moving folders inside the repo is fine.

## 10. Final report to Haffman
Short: number of sources read, raw questions found, distinct MCQs after dedupe, how many paper keys were corrected
(3 notable examples), anything genuinely uncertain he should check with a teacher, the link to send Kashaf, and the
reminder that she should open the link (not a WhatsApp file) and use Save / Restore occasionally.

## 11. Optional: flashcards from textbooks
Surgery also has `surgery/flashcards.html` (1,263 cards built from Dogar's books + the MCQs, each with answer, why,
memory hook, trap, book page). Only build these if Haffman asks and supplies the books as full-quality scans
(attach the PDFs directly; image-only PDFs added as project knowledge arrive blank). Approach: OCR each book, give one
card-writing agent per ~100 MCQs + the matching chapters, require every MCQ id to be covered by at least one card,
cap extra book-only cards at ~2 per agent, then an independent checker pass. Copy the storage-key and Save/Restore
pattern from the quiz template.
