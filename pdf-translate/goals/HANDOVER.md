# Handover — pdf-translate (read this in a new session)

Paste this file (or: “read `pdf-translate/goals/HANDOVER.md` and continue”)
into a **new** agent session that has no memory of prior work. Then do
**one** next sitting. Do not start two gates. Do not mix a bakeoff with
a gate.

**Repo:** `<REPO>`  
**Skill dir:** `pdf-translate/`  
**Interpreter:** `py -3`  
**Tests:** from `pdf-translate/`:  
`py -3 -m unittest tests.test_pipeline tests.test_corpus_verdicts -v`  
**Branch:** `main`. Gates 01–16 and the any-PDF skill text are committed (`git log -1` shows the latest).  
**After that commit** only bakeoff material, session prompts and HTML explainers remain untracked or ignored; see §9.

---

## 1. What this product is

**pdf-translate** localizes a **born-digital PDF** (any language pair the
pipeline can place) while keeping the **same visual layout** and every
fillable field working (same names, types, rects).

Architecture: **strip-and-retypeset**. Delete page text at the content-stream
level; re-insert translated text at original coordinates. Do not overlay
white boxes, do not regenerate the document, do not use redaction
annotations (they delete widgets).

It is **provider-neutral**: seven Python scripts, no vendor SDK. Any person
or model authors `translations.json`. Scripts do not call an LLM.

It is **not** FL-150 English→Japanese. FL-150 was a hard **canary**, not
the product. Court forms, hospital packets, tax sheets, brochures, manuals
all use the same pipeline.

Priority when requirements conflict:

1. **structure** (fields, links, bookmarks work)
2. **layout** (only the text changes)
3. **natural translation in this document’s register**
4. file size / aesthetics

A pretty file with a green verify that did not translate is worse than a halt.

---

## 2. How an agent is supposed to translate (skill text)

`SKILL.md` is the workflow. Scripts are in `scripts/`. Format:
`references/translations-format.md`. Silent pipeline failures:
`references/failure-modes.md`. Fonts: `references/fonts.md`.

**Recon is two parts.** Geometry (pages, fields, fonts, XFA), then
**identity** written in NOTES / session notes **before** filling any
translation (not in `translations.json`):

1. **Class** — one sentence a librarian could file
2. **Issuer** — who published it, or `none` / `unknown`
3. **Parallel text** — URL/path of *this same document* in the target
   language, or `none`, or `not searched`
4. **Identifiers** — names on *this* PDF the reader must write, find, or
   say in the source language (complete after extract)

**Lookup.** If you can search, you must. Search the issuer catalog,
regulator, or vendor’s localized product. If a published translation of
this same document exists, **those terms of art win**. If none, use
established usage for that class — not a calque, not a word invented on
the page. Do **not** ship a glossary in the skill.

**Write/find/say.** If the reader must write it, hand it over, or search
for it, keep the source token (or bilingual `target (Source)`). Quoted
payload stays; the instruction around it may change language. Form names
(`Schedule C`, `Form W-2`), URLs, paper size the filer must use, `$` the
issuer printed — stay.

Hot loop after first extract: edit `translations.json` →
`pipeline.py rebuild` → `pipeline.py render` → look at PNGs. Visual pass
is mandatory. Gates cannot see wrong jargon (養子支援 on a child-support
page still PASSed structure).

---

## 3. What is locked (do not regress)

### PROGRAM 01–07 (committed in `ad52f1d`)

| # | What |
|---|---|
| 01 | `--translations`: authored targets appear in output text (NBSP/hyphen fold) |
| 02 | Leftover English button `/MK /CA` fails unless `skip` or `--captions` |
| 03 | Retypeset fails below 0.7× unless `allow_scale` |
| 04 | RTL `/ActualText` logical order; layout still LTR by default |
| 05 | Opt-in `"mirror": true` for RTL layout |
| 06 | Corpus `choice_fields.pdf` (ComboBox/ListBox) |
| 07 | `pipeline.py from-cores` scaffolds nulls (not identity, not `""`) |

Also locked: scan/image-only → `refuse+OCR`; pale blank → `skip-ink`;
field identity; no redaction; glyf fonts + rasterization assert;
`pipeline.py rebuild` / `render`; corpus `verdicts.json`.

### PROGRAM 08–10 and 13–16 (committed)

| # | What | Tests |
|---|---|---|
| **08** | Quoted + `Form`/`Schedule`/`Attachment`/`Exhibit` spans from original must appear in output unless `allow_translate` | `IdentifierTests` |
| **09** | Empty / whitespace-only mapping values FAIL, named by core. `skip`/`null` unchanged. Use `skip` not `""` | `EmptyTargetTests` |
| **10** | Output pushbutton `/CA` wider than widget (helv `text_length`, pad 2 pt) FAIL | `CaptionWidthTests` |
| **13** | Stripped file re-read without annotation appearances must have no page text; nested Form XObjects and `/Resources` inherited from `/Pages` are stripped; FAIL deletes the file | `StripCompletenessTests` + corpus strip-clean assertion; `corpus/nested_xobject.pdf` |
| **14** | Invisible text layer (OCR'd scan): stripping the text changes under 3% of its span pixels → extract + verify FAIL; scans refused with or without OCR | `InvisibleTextTests`; `corpus/ocr_layer.pdf` `refuse+ocr-layer` |
| **11** | Override parts must keep the source segment's marker (`d.`) and tail (`$`); verify reads `segments.json` beside the mapping or `--segments`, SKIPs without one | `OverrideMarkerTests` |
| **16** | Runs whose target script needs shaping (Arabic, Indic, Thai, Khmer, Myanmar) are placed with the Story engine on the original baseline, logical string in `/ActualText`; verify FAILs Arabic drawn unshaped | `ShapedScriptTests` |
| **15** | Leak scan keyed to the source document's script; same-script pairs use document words automatically; shared spaceless family is REVIEW-only | `ScriptAwareLeakTests`; `corpus/ja_source.pdf`, `corpus/ar_source.pdf` |

`--translations` omitted → 01/02/08/09/10 do not run.

Hits for 08 come from shipped `extract_segments.write_find_say_hits` —
do not fork those regexes. url-or-email is not a hard fail.

### Skill text already in `SKILL.md`

- Any PDF, any pair; identity record; lookup
- Generic write/find/say (including paper size and `$`)
- Captions must fit (gate 10)
- Identifiers / `allow_translate`
- Empty targets documented in `translations-format.md`

### Human explainers

- `recommendations.html` — seven screens: any PDF, name it, look it up,
  keep the picture. FL-150 is a **canary**, not the product.
- `quality-bakeoff.html` — translation-quality canary (FL-150 EN→JA),
  not a gate.
- `goals/RECOMMENDATIONS.md` — evidence + rejected ideas (no glossary,
  no winner in SKILL, no grep-gate).

---

## 4. Hard constraints (every sitting)

- **Provider-neutral.** No vendor SDK. No Japanese-only branch.
- **No glossary** in the repo (no 申立人/養育費 lists, no medical term banks).
- **No winner model** in `SKILL.md`.
- **Not FL-150** as a proof fixture. Constructed LTR PDFs.
- **One `/goal` row per session.** STOP when that bar is green.
- **Never mix a bakeoff with a gate.**
- **Never implement OCR** (refusal naming OCR is the product).
- Never combine 04+05 (already closed separately).
- Never auto-merge by geometry (swallows list siblings).
- Scripts cannot judge whether jargon is the *right* term. Wrong heading
  is a reason not to use that model as author, not a dictionary.

---

## 5. What is NOT done — do these next

Do **one** of these sittings. Recommended order:

### Next closed gate: `/goal` 11

Copy `goals/11-override-markers.md` into `/goal`.

Inner-gap rows like `d. Label      [widget]     .... $`. Override `parts`
must keep source `marker` (`d.`) and `tail` (`$`). Constructed LTR, not
FL-150. Do not start 12 in the same sitting.

### Then `/goal` 12

Copy `goals/12-narrow-column-warning.md` into `/goal`.

Extractor **warns** (`kind: narrow-column`) on ≥3 stacked skinny cores
(same x, width < 90 pt). **No auto-merge.** Warn-only; do not touch
verify unless you must.

### Leftover skill text (no gate) — still open

`SKILL.md` still says “If a cell must stay tiny, add its core to
`allow_scale`” without “reword first.” Still missing:

- Narrow columns are one note / one override with `max_width` (until 12
  the extractor does not yell)
- Overrides keep `d.` / `$` as skill prose (until 11 the gate does not)
- `allow_scale` is last resort
- Deliver: a second linguist for official/court work; scripts will not
  be that person

Do this as its **own** sitting or fold the 11/12-related sentences into
those goal docs (already required by 11/12 done bars). Do not dump a
glossary in while you are there.

### Optional canary (not a `/goal`, different sitting from any gate)

Same constructed PDF as 08 (`Write "Attachment A"…` / `Schedule Q`).
One model that inspects PNGs, one that does not. Score: identity record,
lookup, identifiers kept. Do not put the winner in `SKILL.md`.

ChatGPT bakeoff was local **Codex CLI** (`gpt-5.6-sol|terra|luna`).
Claude evidence recovered from `Claude-Session-Handover.zip` (damaged
zip; recovery under `runs/claude-handover/` if present). Winner notes
live in `runs/BAKEOFF-*.md` if that tree exists — **not** in SKILL.md.

---

## 6. Comfortable terminal stage

You are at a comfortable pause when **all** of these are true:

1. **11 and 12 closed** with in-repo tests; full unittest + corpus green.
2. **Leftover skill sentences** in `SKILL.md` (narrow columns,
   `allow_scale` last, second-reader deliver).
3. **Working tree committed** on `main` (or a named ship commit) covering
   08–12 + skill-text + `goals/08–12` + `HANDOVER.md` + explainers you
   want to keep. Do not commit `work/`, `runs/`, FL-150 PDFs, or the
   Claude zip unless the user asks.
4. **North star still holds:** any born-digital PDF, any pair, layout
   preserved, honest refuse when impossible.
5. You can say, without lying: *gates catch structure, identifiers,
   empty values, clipped chrome, dropped list markers, and skinny-column
   stacks (warn). They still cannot catch 養子支援 vs 養育費. A human
   looks at PNGs. A second linguist is named for court/official work.*

After that pause, **do not invent the next PROGRAM row**. Wait for a
new silent-PASS class (gates green, output wrong). Then one constructed
fixture, one sitting.

Still out of scope forever unless the user reverses it: glossary, OCR
implementation, semantic term checker, winner-in-SKILL, FL-150 as gold.

---

## 7. How to run a `/goal` sitting

```
construct ONE tiny LTR PDF
  → drive shipped extract / retypeset / verify (import scripts, not a copy)
  → if gates PASS and output is wrong: the gate is the bug
  → if gates FAIL and output is right: the gate is the bug
  → lock with an in-repo test; corpus unchanged
  → py -3 -m unittest tests.test_pipeline tests.test_corpus_verdicts -v
  → STOP
```

Start: copy the matching `goals/NN-….md` into `/goal`. Add:

```
Work in <REPO>/pdf-translate.
Interpreter: py -3. Do not start the next number. Do not mix a bakeoff.
```

Do not paste bakeoff scores, `work/translations.json`, or old NOTES.

---

## 8. File map

| Path | Role |
|---|---|
| `SKILL.md` | Workflow an agent/person follows |
| `scripts/*.py` | strip, extract, prepare_font, retypeset, verify, field_fonts, compare, pipeline |
| `tests/test_pipeline.py` | Constructed LTR (and RTL) unittests — import shipped scripts |
| `tests/test_corpus_verdicts.py` | `corpus/verdicts.json` table |
| `corpus/` | Tiny adversarial PDFs + verdicts |
| `goals/PROGRAM.md` | Loop + queue |
| `goals/01–07-*.md` | Closed goal briefs |
| `goals/08–12-*.md` | 08–10 closed in code; 11–12 next |
| `goals/IMPLEMENTATION.md` | Session-by-session recs queue (08 calendar is stale; 08–10 done) |
| `goals/RECOMMENDATIONS.md` | Why no glossary / no winner |
| `goals/HANDOVER.md` | **This file** |
| `recommendations.html` | Any-PDF explainer (7 screens) |
| `quality-bakeoff.html` | FL-150 wording canary |
| `references/` | format, fonts, failure-modes |

`work/`, `runs/`, `fl150_original.pdf` are gitignored job artifacts.

---

## 9. Uncommitted / untracked (as of this handover)

**Committed:** gates 08–16 (verify gates 08–10, strip gate 13, OCR-layer refusal 14, script-aware leak scan 15, shaped scripts 16), the any-PDF skill text, goal briefs 08–13, HANDOVER / IMPLEMENTATION / RECOMMENDATIONS, `corpus/nested_xobject.pdf`, `.gitignore` (`runs/`).

**Untracked, keep with the skill (not yet committed):**  
`recommendations.html`, `quality-bakeoff.html`, `CHATGPT_SESSION_PROMPT.md`

**Untracked, do not treat as the product:**  
`Claude-Session-Handover.zip`, `Claude Session Handover/`, `bakeoff/`,
`v1_vs_v2_report.html`, session prompt markdowns. FL-150 runs stay in
`work/` / `runs/` (ignored).

Confirm with `git status` before you commit.

---

## 10. First message for the next session (copy)

```
Read pdf-translate/goals/HANDOVER.md and pdf-translate/SKILL.md.

Work in <REPO>/pdf-translate.
Interpreter: py -3.

08–10 and 13 are closed and committed. Do not redo them.
Do not start 12. Do not mix a bakeoff. No glossary. Not FL-150 as fixture.

Next sitting: copy goals/11-override-markers.md into /goal and close
that bar only. Unittest + corpus must stay green.
```

If they want skill leftovers instead of 11, say so and edit `SKILL.md`
only (no new verify gate).
