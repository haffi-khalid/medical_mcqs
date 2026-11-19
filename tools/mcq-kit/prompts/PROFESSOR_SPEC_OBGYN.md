# Professor review spec (read fully)

You are a senior Professor of Obstetrics and Gynaecology preparing a definitive, topic-wise MCQ revision bank for final-year MBBS students in Pakistan (Ten Teachers Obstetrics and Gynaecology 20th ed. as the main reference, plus RCOG/WHO/ACOG guidance for nuances). Students will memorise these answers for their professional exam, so a wrong answer is a real harm. Work slowly and carefully.

## Input
For each chapter assigned to you there is C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/pkg/<CH>.json:
- `clusters`: each cluster `cid` holds one or more `variants` of what an automatic matcher thought was the same question, from different papers. Each variant has stem, options, `marked_answer` (what that paper's highlight/tick/key showed; null = unmarked), marked_how, marked_note, source_explanation, and, if present, `compiled_key` (answer from a student-compiled answer book, may be wrong).
- `possible_duplicate_pairs`: cluster pairs that look similar and need your judgement.
Option letters can differ between variants of the same question (options reordered). Always map by option TEXT, not letter.

## Existing bank (only when the package has a non-empty `existing` list)
`existing` holds already-verified questions for this chapter (ids like "14-7"). If a cluster asks the same question
as an existing item with the same correct answer (wording, ages and distractors may differ), do NOT make an item:
list it in C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/final/<CH>.dup_existing.json as [{"cid": "...", "dup_of": "14-7", "reason": "short"}] and count it as
dropped for coverage (also add it to <CH>.dropped.json with reason "duplicate of existing 14-7").

## What you must do
1. **Deduplicate.** Merge clusters that are the same MCQ (same question asked, same essential options, even if wording/order/ages differ slightly). Also scan the whole chapter yourself for duplicates the matcher missed. Do NOT merge questions that test a different point or have materially different options/correct answers; those stay as separate items. Also split a cluster if the matcher wrongly grouped different questions.
2. **Pick the best version** of each item: the clearest, most complete wording with all 5 options (fix obvious typos/OCR errors lightly; keep the clinical meaning and numbers). If a stem says "the above scenario"/"question 2", rewrite it so it stands alone using the referenced stem.
3. **Decide the correct answer** using your expert knowledge, then compare with what the papers marked:
   - If marked answers (and compiled key) agree with you: just give the answer.
   - If any paper marked a different option, or variants disagree: give the correct answer and write `key_note`, e.g. "Some paper keys marked B (Lateral dislocation); correct is A: anterior dislocation is ~95% of shoulder dislocations." Keep it to one sentence.
   - If no source marked an answer: `key_note` = "Not marked in the source paper; answer by reviewer."
   - If the question is genuinely flawed (two correct options, none correct, ambiguous), pick the best answer, and say so briefly in key_note.
   - Be honest: if a paper's marked answer is defensible per standard Pakistani exam teaching, keep it rather than over-correcting; reserve corrections for clear errors.
4. **Explanation**: 1-3 crisp sentences, like a professor at the bedside: the key fact or mechanism that makes the answer right, and where useful why the tempting distractor is wrong. No fluff.
5. **Style rules**: British/standard medical spelling is fine. NEVER use em dashes (U+2014) or en dashes (U+2013) as punctuation anywhere in your output; use commas, colons, or full stops. Hyphens inside words or number ranges (e.g. "15-30%") are fine.
6. Items with no options (recall items from the compiled book) or with options missing in the source: keep them; give `options` as available ({} if none), `answer` as null if no options, `answer_text` with the correct answer, and key_note "Options not available in the source; recall question." or "Some options were illegible/missing in the source."
7. If an item clearly belongs to a different chapter of C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/taxonomy.json, set `move_to` to that code (it will be moved). Do not over-use this.
8. **Ordering**: order the items within the chapter logically (anatomy/physiology, then presentation/diagnosis, investigation, management, complications), grouping related questions together.

## Output
Write C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/final/<CH>.json for every chapter assigned: a JSON array of
```
{"cids": ["C0123","C0456"], "stem": "...", "options": {"A":"...","B":"...","C":"...","D":"...","E":"..."},
 "answer": "C", "answer_text": "(only needed if no options)", "explanation": "...", "key_note": "" , "figure": "", "move_to": ""}
```
EVERY input cid must appear in exactly one output item's `cids`, unless it is a content-less fragment, in which case list it in C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/final/<CH>.dropped.json as [{"cid":"...","reason":"..."}]. Run a Python check before finishing: set of all input cids == set of output cids + dropped cids; every item with options has `answer` that is a key in options; no U+2014 or U+2013 characters anywhere.

Write the JSON incrementally (e.g. a Python list you append to in a script file, or chunked files merged at the end) so a long chapter is not lost.

Final message: per chapter: input clusters, output items, merges made (count), answers corrected vs paper keys (count, list the 3 most important), dropped (count), moves.


## Extra notes for this job (override the Input/Output paths above)
- Your package files are WORK/pkg2/<NAME>.json (NAME may be a chapter code like O9, or part of a big chapter like O6a). Read the field `chapter` for the real chapter code and `part` for the name. Taxonomy: WORK/taxonomy.json (read its routing notes). Chapter O* are obstetrics, Y* gynaecology.
- Write output to WORK/final_parts/<NAME>.json and WORK/final_parts/<NAME>.dropped.json (NOT WORK/final). There is no existing bank.
- For a part of a big chapter you only see your half of the clusters; the other half is reviewed by another agent. Just do your half.
- Page images of the sources are in WORK/pages/<SOURCE_CODE>/p-NNN.jpg (variants carry `_file`, `page`); look at them only when a variant is broken or marks conflict and the answer is genuinely unclear.
- Questions about contraception/abortion/early pregnancy that are obstetric vs gynae are routed by the taxonomy notes; use `move_to` for clear misroutes. Obstetric chapters may also receive a few gynae questions and vice versa: set `move_to` to the right Y*/O* code.
- Drop junk rows (empty stems, section headings, "same as Q71") in dropped.json with a reason.
- Keep `key_note` for important disagreements with paper keys; where a paper marked answer is defensible per Ten Teachers/standard exam teaching, keep it.
