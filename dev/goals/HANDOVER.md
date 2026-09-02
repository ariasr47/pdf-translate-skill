# Handover — pdf-translate (read this in a new session)

Paste this file (or: “read `dev/goals/HANDOVER.md` and continue”) into a
**new** agent session that has no memory of prior work.

**There are exactly three rows, and they were not invented.** The audit
roadmap and the repo's own queue are closed. The 2 September canary then
produced three defects, each from a model doing a real job against the
fixture: rows 18, 19 and 20 in `dev/goals/PROGRAM.md`, with measurements in
`dev/canary/runs/`. One sitting each, cheapest first. **Row 18 is closed**
(2 September, version 30); 19 and 20 remain. When they are done, do not
invent a fourth — run the canary again.

**Evening of 2 September:** a deep review (`docs/REVIEW-2026-09-02.md`;
queue in `PROGRAM.md` → *Backlog after the review*) added a second,
*product* lane. Lane A — 19, 20, then canary run 2 — is unchanged and still
goes first. Lane B rows (plugin packaging, a measured wild corpus,
`SKILL.md` under 500 lines, eval automation) each have a closed bar and one
sitting. The wild corpus ran that same evening (P1 closed): seventeen
public PDFs, no crashes, no wrong verdicts, and it opened rows **21** and
**22** and lane B row **P6** — `dev/wild/ANALYSIS.md` has the numbers.
The PDFs are re-fetched from `dev/wild/SOURCES.md`, never committed.

**Repo:** `<REPO>` — GitHub `ariasr47/pdf-translate-skill`, branch `main`
**Skill dir:** `pdf-translate/` (the only directory you install)
**Dev material:** `dev/` — this file, the goal briefs, the canary, explainers
**Interpreter:** `python3` (`py -3` on Windows; bare `python` is the Store alias)
**Tests:** from `pdf-translate/`:

```bash
python3 -m pip install -r requirements.txt
python3 tools/fetch_test_fonts.py      # or the shaping tests skip
python3 -m unittest tests.test_pipeline tests.test_corpus_verdicts -v
```

On the macOS box, bare `python3` is Apple's 3.9 with none of the
dependencies; use `pdf-translate/.venv/bin/python` (3.14, pymupdf 1.28,
pikepdf 10) for everything above.

**State of play, 2 September 2026, end of the row-18 sitting:**

- **158 tests, no skips**, ~25 s locally. The 157 before this sitting were
  green on GitHub Actions across Linux and Windows, Python 3.10 and 3.13;
  the 158th is green locally and has not been through CI yet — push and
  check.
- `SKILL.md` is at `metadata.version: "30"`.
- Working tree clean, everything committed. Nothing is half-finished.
- Program rows 01–18 and the whole September audit roadmap are **closed**.
- The canary has run once. It opened rows **18, 19 and 20** — see §5. Row
  18 is closed; 19 and 20 are open.

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

## 5. What is not done

### Three rows, and nobody invented them

The 2 September canary put Opus 5, Fable 5.1 and Haiku 4.5 on the same
two-page fixture with the same one-line prompt. Opus and Fable scored 5/5,
Haiku 3/5. All three produced a structurally sound file — so the pipeline
is not what separates models — and between them they walked into three
defects. Each has a measurement in `dev/canary/runs/` and a brief to copy
into `/goal`:

| # | Brief | What | Found by |
|---|---|---|---|
| **18** | `goals/18-center-example.md` | **Closed 2 Sep.** `center` was documented for "signature captions", the one case where it is wrong: those are left-flush under a rule, and centring moved one 7.5 pt off its own rule, past every gate. Example corrected, SKILL.md step 5 says it, `test_center_moves_a_left_flush_caption_off_its_rule` locks the geometry; no warning built, by decision (closing note in the brief). | Haiku 4.5 |
| **19** | `goals/19-list-marker-gap.md` | retypeset re-emits `marker + ' '` where the source had two spaces, shifting every list body **3.06 pt left** (measured). Touches the segment schema and every placement path. | Opus 5 |
| **20** | `goals/20-notice-title-leak.md` | `compliance.md` tells the author to name the source form title in the notice; the leak scan then FAILs that title as untranslated running text. Two features disagreeing. | Fable 5.1 |

Do them **one sitting each, in that order** — cheapest first. 18 is closed;
19 is next, then 20. When they are closed, do **not** invent a row 21: run
the canary again and see what it walks into.

One defect from that canary is already fixed: the placement gate could not
pass a wrapped merge, which broke paragraph mode on the day it shipped
(`MergePlacementGateTests`).

### Two things this machine could not do

- **The installed skill copy is stale** — `metadata.version` 16 against the
  repo's 29, so anything invoking it gets the pre-audit pipeline. It lives
  at `%APPDATA%\Claude\…\skills\pdf-translate` on a **Windows** box, not
  the macOS machine this was built on. Copy the whole of `pdf-translate/`
  minus `tests/fonts/*.ttf` and `evals/fixtures/`, and refresh the manifest
  description.
- **`docs/audit-2026-09-01.html` is stale** — 16 "Open" badges for findings
  that are all fixed. `docs/RESEARCH-AND-FINDINGS.md` is current; the HTML
  page a reader actually opens is not. ~20 minutes.

### Out of scope forever, unless the user reverses it

A shipped glossary, OCR implementation, a semantic term checker, a winner
model named in `SKILL.md`, FL-150 as a gold fixture.

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

---

## 8. First message for the next session (copy this)

```
Read dev/goals/HANDOVER.md, then pdf-translate/SKILL.md.

Work in <REPO>. Interpreter: python3 (py -3 on Windows).
Tests, from pdf-translate/:
  python3 tools/fetch_test_fonts.py
  python3 -m unittest tests.test_pipeline tests.test_corpus_verdicts

158 tests, no skips, green locally; confirm CI after pushing. Everything is
committed. Program rows 01-18 and the whole audit roadmap are closed. Do
not redo them.

Next sitting: copy dev/goals/19-list-marker-gap.md into /goal and close that
bar only. Do not start 20 in the same session. Do not mix in a canary
run. No glossary. Not FL-150 as a fixture.

When the bar is green: full unittest + corpus, bump metadata.version in
SKILL.md, commit, stop.
```

Swap `19-list-marker-gap.md` for `20-notice-title-leak.md` when that is
the sitting. If the user wants the
stale audit HTML or the installed-copy re-sync instead, say so and do only
that — neither is a gate, and neither needs a fixture.
