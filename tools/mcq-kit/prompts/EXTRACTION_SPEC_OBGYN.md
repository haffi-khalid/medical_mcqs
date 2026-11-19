# MCQ extraction spec (read fully before starting)

You are extracting EVERY multiple-choice question from past Obstetrics and Gynaecology exam papers (Pakistani MBBS final year). Accuracy and completeness are critical: a medical student will study from this. Missing a question or recording the wrong marked answer is a serious failure.

## Inputs
- Page images: C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/pages/<FOLDER>/p-<N>.jpg (one JPEG per PDF page). View them with the Read tool.
- Text layer (often empty for scans, sometimes garbled OCR): C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/text/<FOLDER>.txt
- No OCR tool is installed; read the page images yourself.

## Method (mandatory)
1. LOOK AT EVERY PAGE IMAGE with the Read tool. Answers are often shown only visually: yellow/green highlight, a tick, a circle around the letter, an underline, handwritten letter in the margin, bold text, a printed key table at the end, or "Ans:" lines. The text layer never shows highlights, so never rely on text alone.
2. Use the text layer only to get exact wording faster; fix obvious OCR errors using the image. Two-column layouts: be careful not to mix columns.
3. Questions can continue across page breaks; join them.
4. Check numbering continuity (1..N). If numbers skip or repeat, look again; if truly missing in the source (e.g. cropped page), record it in the report.
5. Skip non-MCQ items (SEQs, short-answer) but mention them in the report.
6. If a file is an answer key/solution set without full options, still record each item with whatever is present.

## Output
Write a JSON array to C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/extract/<CODE>.json, one object per MCQ:
```
{
 "id": "<CODE>-<qnum>",
 "source_file": "<original PDF filename>",
 "paper": "<human label, e.g. 'HBS Surgery A Pre-Prof 2025'>",
 "page": 3,
 "qnum": "17",
 "stem": "full question text, exactly as written (typos lightly fixed)",
 "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
 "marked_answer": "C",            // letter marked in the source, or null if none
 "marked_how": "yellow highlight", // highlight | tick | circled | underlined | handwritten | bold | printed key | Ans line | none | unclear
 "marked_note": "",               // e.g. 'two options ticked: B and D', 'handwriting ambiguous between B/D', 'answer crossed out and changed to C'
 "source_explanation": "",        // any explanation printed in the source for this question
 "figure": "",                     // describe any image/X-ray/table the question depends on
 "legibility": "ok"                // ok | partly illegible: <what>
}
```
Use option letters A-E in order of appearance even if the paper uses a/b/c or 1/2/3. Keep option text verbatim.

Then write a short report to C:/Users/ASDF/Desktop/medical_mcqs/medical_mcqs/work/obgyn/extract/<CODE>.report.md: total MCQs found, numbering range, count with marked answers vs none, any gaps/illegible items, any non-MCQ content skipped, and any oddities. Return the same summary as your final message.

Do not answer the questions yourself and do not "correct" marked answers. Just record faithfully what the source shows. Work page by page and write the JSON incrementally if large (e.g. per-page files merged at the end) so nothing is lost.


## Extra notes for this job
- Subject mix: Obstetrics and Gynaecology papers/banks from Pakistani colleges (HBS, IMDC, FMDC, Rawal, RIHS, UM, Szabmu etc.), mixed Obs and Gynae. Record both; do not filter.
- Some files are compilations of several papers: label each question with its paper heading and use ids CODE-PAPERTAG-qnum when numbering restarts.
- If a file is a student answer book/compiled key (title + answer + explanation, few stems), write it to extract/<CODE>_KEY.json instead and say so in the report.
- For a page range: take a question that straddles your last page fully; skip one that straddles your first page (the previous agent takes it). Output file name for a range: extract/<CODE>_<start>-<end>.json (ids still CODE-...).
- Docx/markdown sources: text is in WORK/text/<CODE>.md with **bold** and ==highlight== marks; there are no page images. Line ranges are given instead of pages.
- Write JSON with a Python script (json.dump, ensure_ascii=False) and validate it loads. No em or en dashes in your own text fields (use commas/colons) but keep source wording otherwise.
- Use your own scratch folder given below for temporary files.
