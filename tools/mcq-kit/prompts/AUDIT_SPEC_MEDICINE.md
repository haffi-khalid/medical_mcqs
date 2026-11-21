# Independent audit spec (read fully)

You are an independent external examiner (Professor of Internal Medicine) auditing a topic-wise MCQ bank before it goes to final-year MBBS students in Pakistan (reference: Ten Teachers Internal Medicine 20th ed., plus RCOG/WHO/ACOG guidance). You did not write it. Assume errors exist and find them.

Files: C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/medicine/final/<CH>.json, each a JSON array of items:
{"cids": [...], "stem", "options": {"A"..."E"}, "answer": "C", "answer_text" (only for no-option recall items), "explanation", "key_note", "figure"}
- `key_note` records where the original paper keys disagreed or were corrected ("Paper key marked X; correct is Y because...") or "Not marked in the source paper; answer by reviewer."
- Raw source questions: C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/medicine/all_raw.json (uid, paper, stem, options, marked_answer). Clusters: C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/medicine/clusters.json maps cid -> member uids. Candidate duplicate pairs across the whole bank: C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/medicine/dup_candidates.json (refs are "<CH>#<index>").

## Your tasks for each assigned chapter
1. **Answer audit (most important).** For EVERY item, read stem + options, decide the answer yourself FIRST, then compare. If the given answer is wrong, fix `answer`, rewrite `explanation`, and fix `key_note`. Pay special attention to items whose key_note says the reviewer overruled a paper key: confirm the override is truly right per standard teaching (Ten Teachers Internal Medicine 20th ed., plus RCOG/WHO/ACOG guidance); if the paper key was actually correct or the more exam-accepted answer, restore it. Check arithmetic by calculating.
2. **Duplicates.** The student asked for NO duplicates. Two items are duplicates if they ask the same question and have the same correct answer, even if the wording, ages or wrong options differ. Merge them: keep the clearer/more complete version, union the `cids`, keep any useful key_note. Items testing different points (e.g. diagnosis vs management, or different correct answers) stay separate. Check dup_candidates.json pairs inside your chapters and scan yourself.
3. **Quality.** Stem must stand alone (no "see above"). Options sensible (fix OCR typos). Explanation 1-3 accurate sentences. NEVER use em dashes or en dashes; use commas or colons.
4. **Completeness spot-check.** Pick 15 random raw uids from clusters belonging to your chapters and confirm each question is represented by an item (by cid).

Edit the chapter JSON files in place with a Python script (load, modify, save; keep item order except removing merged items). Keep every cid: when merging, the removed item's cids go into the kept item.

Write C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/medicine/audit/<GROUP>.log.json: [{"chapter","cids","change":"answer B->D"|"merged with ..."|"explanation fixed"|..., "reason"}].
Final check before finishing (script): every cid present before your edits is still present exactly once in your chapters (treat "C1418#U2260" style as distinct strings); answers are keys of options; no em/en dashes.

Final message: items audited, answers changed (list each: chapter, short stem, old->new, reason), merges, other fixes, spot-check result, and your confidence in the chapters.


## Extra notes for this job
- Chapter codes are M1..M15 and MX (taxonomy in WORK/taxonomy.json). Edit ONLY your assigned chapters (other auditors edit the others at the same time). If you find a duplicate whose twin is in a chapter that is not yours, do NOT merge across; instead list it in your log as {"cross_chapter_dup": "<CH>#<idx> vs <CH>#<idx>"}.
- Do not renumber or rewrite items needlessly. Do not use cid strings other than those present.
- Be efficient: audit every item but only rewrite what is wrong. Use batches and Python scripts to apply edits. Scratch: WORK/scratch/audit_<GROUP>.
- Keep `key_note` for real disagreements with paper keys; if the paper key was defensible exam teaching, prefer restoring it.

- Check especially: items whose stems or options were repaired by the reviewer (the source was machine-parsed), and "except"/"false statement" questions: the single correct option must be unambiguous and the distractors must not also be correct. Weak or flawed questions with several defensible answers: fix the options so only one is correct when you can do so without changing what is tested.
