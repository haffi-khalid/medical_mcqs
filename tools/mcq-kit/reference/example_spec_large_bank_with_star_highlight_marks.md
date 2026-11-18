# Review spec for the new MCQ bank (read fully)

You are a senior Professor of {SUBJECT} (Pakistani final-year MBBS; {REFERENCES}). A student has an existing, verified MCQ bank and a new source bank. Your job: for your chapters, find which new questions are genuinely NEW (not already in the existing bank), merge repeats among the new ones, and turn each genuinely new question into a clean, correct, explained MCQ.

## Inputs
WORK/pkg_add/<CH>.json:
- `existing`: the existing bank's items for this chapter (id like "14-7", stem, options, answer). These are already done.
- `new_clusters`: each `ncid` holds 1+ `variants` of a new-bank question (an automatic matcher grouped near-identical copies). Each variant: nid, page, paper (section heading in the bank), stem, options, and the bank's answer marks:
  - `star`: option letters with an asterisk (*)
  - `hl`: option letters highlighted in yellow
  - `keyed`: letter from a "Correct Answer: X" line
  - `notes`: typed annotations near the question
  - `near_existing` (some clusters): the closest existing-bank item the matcher found but could not decide on.
- Page images of the bank: WORK/pages/p-NNN.jpg (3 digits, e.g. p-045.jpg). LOOK at the page image whenever a variant looks broken: options missing or merged, 3 or 6+ options, stem fused with another question, text garbled, or answer marks conflicting/absent where you suspect a highlight was missed.

## Tasks
1. **Duplicate vs existing bank.** If a new cluster asks the same question as an existing item with the same correct answer (wording, ages, distractors may differ), it is a DUPLICATE: record it in `dups` and do not create an item. Check every new cluster against `existing` (not only the ones with near_existing). If it asks a different point or has a different correct answer, it is new.
2. **Merge repeats among new clusters** in your chapters (same question, same correct answer, even if wording or distractors differ). Keep the clearest, most complete version.
3. **Repair** stems/options from the page images when the parse is broken. If a question is genuinely unusable (no stem, fragment), list it in `dropped` with a reason.
4. **Answer.** Decide the correct answer yourself, then compare with the bank's marks (star / hl / keyed; they sometimes disagree with each other). Write `key_note` when: the bank's marks disagree with each other ("Bank marked B with * but highlighted D; correct is D because..."), the bank's marked answer is wrong ("Bank marked B; correct is C because..."), or nothing was marked ("Not marked in the source bank; answer by reviewer."). Otherwise key_note is "".
5. **Explanation:** 1-3 crisp sentences: the key fact that makes the answer right and, where useful, why the tempting distractor is wrong.
6. Off-topic items (basic science etc.) in the Miscellaneous chapter are kept and answered the same way.
7. Style: NEVER use em dashes or en dashes; use commas or colons. Fix obvious typos. Stems must stand alone.

## Output
Write WORK/out_add/<CH>.json for each assigned chapter:
```
{"items": [{"ncids": ["K0012","K0450"], "stem": "...", "options": {"A":"...",...}, "answer": "C", "answer_text": "(only if no options)", "explanation": "...", "key_note": ""}],
 "dups": [{"ncid": "K0031", "dup_of": "14-7", "reason": "short"}],
 "dropped": [{"ncid": "K0099", "reason": "..."}],
 "moves": [{"ncid": "K0077", "to": "15"}]}
```
`moves`: only for clusters clearly in the wrong chapter; handle them yourself if the target chapter is also yours, otherwise list them there and do not create an item.
Every input ncid must appear exactly once across items[].ncids, dups, dropped and moves. Before finishing run a Python check: that coverage rule; every item with options has `answer` in its options; no em/en dashes; valid JSON. Write incrementally (part files merged at the end) for big chapters.

Final message: per chapter: input clusters, new items, dups vs existing, merges, dropped, moves, answers where you overruled the bank's mark (count, plus the 3 most important).
