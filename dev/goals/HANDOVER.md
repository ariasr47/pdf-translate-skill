# Handover — pdf-translate (read this in a new session)

Paste this file (or: “read `dev/goals/HANDOVER.md` and continue”) into a
**new** agent session that has no memory of prior work.

**The queue is empty.** Every row of `dev/goals/PROGRAM.md` and every row of
the audit roadmap in `docs/checklist.html` is closed, with tests. Do not
invent the next row. Wait for a new silent-PASS class — gates green, output
wrong — then do one constructed fixture, one sitting.

**Repo:** `<REPO>`
**Skill dir:** `pdf-translate/` (the only directory you install)
**Dev material:** `dev/` — this file, the goal briefs, the canary, explainers
**Interpreter:** `py -3` on Windows, `python3` elsewhere
**Tests:** from `pdf-translate/`:
`python3 tools/fetch_test_fonts.py` (optional, stops the shaping tests
skipping), then
`python3 -m unittest tests.test_pipeline tests.test_corpus_verdicts -v`
**Branch:** `main`. Everything below is committed.

---

## 1. What this product is

**pdf-translate** localizes a **born-digital PDF** (any language pair the
pipeline can place) while keeping the **same visual layout** and every
fillable field working (same names, types, rects).

Architecture: **strip-and-retypeset**. Delete page text at the content-stream
level; re-insert translated text at original coordinates. Do not overlay
white boxes, do not regenerate the document, do not use redaction
annotations (they delete widgets).

It is **provider-neutral**: plain Python, no vendor SDK. Any person or model
authors `translations.json`. The scripts do not call an LLM.

It is **not** FL-150 English→Japanese. FL-150 was a hard **canary**, not the
product. Court forms, hospital packets, tax sheets, brochures and manuals all
use the same pipeline.

Priority when requirements conflict:

1. **structure** (fields, links, bookmarks work)
2. **layout** (only the text changes)
3. **natural translation in this document's register**
4. file size / aesthetics

A pretty file with a green verify that did not translate is worse than a halt.

---

## 2. How an agent is supposed to translate (skill text)

`SKILL.md` is the workflow. Scripts are in `scripts/`. Format:
`references/translations-format.md`. Silent pipeline failures:
`references/failure-modes.md`. Fonts: `references/fonts.md`. The reviewer
checklist and the MQM prompt: `references/review.md`. When a notice belongs
in the document, and the certification template: `references/compliance.md`.

**Recon is two parts.** Geometry (pages, fields, fonts, XFA, encryption,
`/Perms`), then **identity** written in NOTES / session notes **before**
filling any translation:

1. **Class** — one sentence a librarian could file
2. **Issuer** — who published it, or `none` / `unknown`
3. **Parallel text** — URL/path of *this same document* in the target
   language, or `none`, or `not searched`
4. **Identifiers** — names on *this* PDF the reader must write, find, or say
   in the source language (complete after extract)

The class also decides whether the output needs a target-language
"translation for information only" notice (`references/compliance.md`).

**Lookup.** If you can search, you must. If a published translation of this
same document exists, **those terms of art win**. Do **not** ship a glossary
in the skill; `glossary.csv` is a per-job input to `qa_check.py`.

**Write/find/say.** If the reader must write it, hand it over, or search for
it, keep the source token (or bilingual `target (Source)`).

Hot loop after first extract: edit `translations.json` → `pipeline.py qa` →
`pipeline.py rebuild` → `pipeline.py render` → look at the PNGs. The visual
pass is mandatory. Gates cannot see wrong jargon (養子支援 on a
child-support page still passes structure).

---

## 3. What is locked (do not regress)

### The mapping actually lands

`--translations` requires every authored target **verbatim** in the output
text layer; empty and whitespace-only values FAIL; overrides must keep the
source marker (`d.`) and tail (`$`); write/find/say identifiers from the
original must survive unless listed in `allow_translate`.

### The file stays a form

Field parity (names, types, rects) is exact. `/Opt` export values are
byte-identical to the original — a dropdown is translated on its display
half only. Fill round-trip works. Nothing is added: leftover pushbutton
captions must be `skip`'d or rewritten with `--captions`, and a caption
wider than its widget FAILs.

### Refusals

Scan or image-only → `refuse+OCR`. Invisible (OCR) text layer →
`refuse+ocr-layer`. Never implement OCR: the refusal is the product. Leftover
page text after strip deletes the stripped file. A rotated run whose target
needs shaping is refused rather than drawn flat. A font whose `OS/2.fsType`
forbids embedding is refused.

### The text layer is honest

retypeset rewrites `/ToUnicode` to the authored code points; NBSP, soft
hyphen, U+2010/U+2011 and CJK compatibility ideographs that are in neither
the original nor the mapping are a FAIL. Shaped scripts go through the Story
engine and are marked with `/ActualText`; a shaping-script target with no
mark was drawn glyph by glyph and FAILs. Every character of every placed run
is checked against the exact font object.

### Geometry proposes, the author decides

`narrow-column`, `right-aligned`, merge candidates and `image-region` are
**warnings**. Nothing merges or realigns by geometry. `propose-merges`
accepts candidates in bulk, with `html: null` that still FAILs.

### Everything else that is not page text

Widget text (`/TU`, `/Opt`, `/V`, `/DV`) has its own channel. `/Lang`,
`dc:language`, `/Title` and outline titles are retargeted. `/Perms` is
always deleted and reported; a certified source is flagged. The orphaned
`/StructTreeRoot` is removed with `/MarkInfo /Marked false`.

---

## 4. Hard constraints (every sitting)

- **Provider-neutral.** No vendor SDK. No per-language branch.
- **No glossary** in the repo. `glossary.csv` is a job input, never shipped.
- **No winner model** in `SKILL.md`.
- **Not FL-150** as a proof fixture. Constructed PDFs.
- **One row per session.** STOP when that bar is green.
- **Never mix a canary with a gate.**
- **Never implement OCR.**
- Never auto-merge or auto-realign by geometry.
- Scripts cannot judge whether jargon is the *right* term. A wrong heading
  is a reason not to use that model as author, not a reason to add a
  dictionary.

---

## 5. What is genuinely not done

**The canary run.** `dev/canary/README.md` has the fixtures command, the
prompt and the five-axis rubric. Nobody has run it. One strong and one weak
model on the generated fixtures, scored on identity record, lookup,
identifiers kept, visual pass and honest delivery. A different day from any
gate; no winner in `SKILL.md`.

Out of scope forever unless the user reverses it: a shipped glossary, OCR
implementation, a semantic term checker, a winner in `SKILL.md`, FL-150 as
gold.

---

## 6. How to run a sitting, when there is one

```
construct ONE tiny PDF that shows the defect
  → drive shipped extract / retypeset / verify (import scripts, not a copy)
  → if gates PASS and output is wrong: the gate is the bug
  → if gates FAIL and output is right: the gate is the bug
  → lock with an in-repo test; corpus unchanged
  → python3 -m unittest tests.test_pipeline tests.test_corpus_verdicts -v
  → bump metadata.version in SKILL.md; STOP
```

---

## 7. File map

| Path | Role |
|---|---|
| `pdf-translate/SKILL.md` | The workflow an agent/person follows |
| `pdf-translate/scripts/*.py` | strip, extract, prepare_font, retypeset, verify, qa_check, field_fonts, compare, bilingual, render_pages, pipeline |
| `pdf-translate/references/` | failure-modes, translations-format, fonts, review, compliance |
| `pdf-translate/tests/` | Constructed-PDF tests of the shipped stages; the corpus table |
| `pdf-translate/corpus/` | Tiny adversarial PDFs + `verdicts.json` |
| `pdf-translate/tools/fetch_test_fonts.py` | OFL faces for the shaping tests (never committed) |
| `pdf-translate/evals/` | Eval prompts and `make_fixtures.py` |
| `dev/goals/PROGRAM.md` | The loop, the closed queue, what is locked |
| `dev/goals/HANDOVER.md` | **This file** |
| `dev/canary/` | The fitness check for a model as mapping author |
| `docs/checklist.html` | The tracker across the program and the audit roadmap |
| `docs/RESEARCH-AND-FINDINGS.md` | The audit and every verified defect with status |
| `.github/workflows/tests.yml` | Linux + Windows, Python 3.10 and 3.13 |

`work/`, `runs/`, `fl150_original.pdf`, `tests/fonts/*.ttf` and the generated
eval fixtures are gitignored.
