# medical_mcqs: Kashaf's revision site

Static GitHub Pages site: https://haffi-khalid.github.io/medical_mcqs/

- `index.html`: home page (hub). Its `SUBJECTS` list holds one entry per subject.
- `<subject>/quiz.html`: tap-to-answer MCQ bank (progress in localStorage, Save/Restore backup codes).
- `surgery/flashcards.html`: flip cards. Root `quiz.html` / `flashcards.html` are redirects for old links.
- `sw.js`: offline cache; bump its cache name whenever pages change.
- `tools/data/<subject>/`: taxonomy + final JSON of each published bank (source of truth for rebuilding).

**Before any task about creating or extending an MCQ bank, read `tools/mcq-kit/HANDOFF.md` and follow it exactly.**

Rules: never change a published subject's storage key (Surgery: `surg_mcq`, flashcards `dogar_fc`), never reorder or
delete published items (progress ids depend on them), no em or en dashes in anything you write.
