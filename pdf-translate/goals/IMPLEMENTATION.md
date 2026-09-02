# Step-by-step: implement the recommendations

> For a human or an agent. **One sitting = one row.** Do not start the
> next row in the same session. Do not mix a bakeoff with a gate.
> Copy the matching `goals/0N-….md` into `/goal` when you start that row.

**Goal:** Lock the skill’s identity + write/find/say rules in constructed
tests, then catch empty targets, clipped captions, dropped `d.`/`$`, and
skinny stacked cores — without a glossary, a winner model, or FL-150 as
the proof PDF.

**Architecture:** Skill text first (author behaviour). Then `verify.py` /
`extract_segments.py` gates on tiny LTR fixtures, same loop as PROGRAM
01–07. Scripts still cannot see whether jargon is the right term.

**Tech stack:** Python 3, `pymupdf` / `pikepdf` / `fonttools`. Interpreter
on this machine: `py -3`. Tests: `py -3 -m unittest tests.test_pipeline -v`
from `pdf-translate/`.

## Global constraints

- Provider-neutral. No vendor SDK. No Japanese-only branch.
- No terminology glossary. No winner model in `SKILL.md`.
- Constructed LTR PDFs only. **Not FL-150** as a fixture.
- Existing unittest + `corpus/verdicts.json` stay green.
- Never combine two gates. Never combine a bakeoff with a gate.
- Never implement OCR (refusal is the product).
- Identity record stays in NOTES, not `translations.json`.
- Any born-digital PDF, any pair. FL-150 is a canary, not the product.

---

## Already done — do not redo

| Item | Where |
|---|---|
| PROGRAM 01–07 | scripts + `tests/test_pipeline.py` + corpus |
| Name the document (class, issuer, parallel text, identifiers) | `SKILL.md` recon |
| Lookup: issuer catalog / regulator / vendor; found / none / not searched | `SKILL.md` recon |
| Generic write/find/say (quoted payload, form names, paper size, `$`) | `SKILL.md` extract |
| Transliteration of lookup names is a defect | `SKILL.md` extract |
| Explainer matches the skill | `recommendations.html` |
| PROGRAM **08** identifiers | `verify.py` + `IdentifierTests` (committed) |
| PROGRAM **09** empty targets | `verify.py` + `EmptyTargetTests` (committed) |
| PROGRAM **10** caption width | `verify.py` + `CaptionWidthTests` (committed) |
| Handover for a cold session | `goals/HANDOVER.md` |

---

## Never, in any sitting

- A glossary (申立人, 養育費, medical term banks, …).
- A “use model X” line in `SKILL.md`.
- A grep-gate for one wrong word.
- Treating Fable 5 as structure gold.
- Converting US Letter or `$` because the target locale “prefers” A4/¥.
- Starting 09 while 08 is still open.

---

## How every `/goal` sitting works

```
construct ONE tiny LTR PDF
  → drive shipped extract / retypeset / verify (import scripts, not a copy)
  → if gates PASS and output is wrong: the gate is the bug
  → if gates FAIL and output is right: the gate is the bug
  → lock with an in-repo test + corpus unchanged
  → py -3 -m unittest tests.test_pipeline -v
  → STOP
```

Start a sitting: copy `goals/08-quoted-identifiers.md` (or 09/10/11/12)
into `/goal`. Do not paste bakeoff scores, `work/translations.json`, or
Grok NOTES into that session.

---

## Session 0 — leftover skill text (no gate)

Do this **before** 08. No new verify behaviour. No bakeoff.

**Files:** `SKILL.md`, `references/translations-format.md`, optionally
`references/failure-modes.md` (caption clip as an eyes-only silent PASS
until 10).

Paste these bullets into **Extract and translate** (one home; do not
duplicate in YAML):

1. **Narrow columns are one note.** Consecutive cores, same page, similar
   x, stacked y, skinny bbox: one stacked instruction **or** one override
   with `max_width`. Do not translate each English line-break as its own
   crumb. Do not auto-merge by x (swallows list siblings).
2. **Overrides keep markers.** If the source span had `d.` or `$`, the
   override `parts` keep them.
3. **Captions must fit the widget.** Prefer short chrome. A long sentence
   in a 17-pt-tall button can still PASS gate 02. Look at the PNG. Gate
   10 will measure this later — until then it is eyes.
4. **`allow_scale` is last resort.** Reword, look, then opt in. Gate 03
   already refuses < 0.7×. Do not invite a list of eight tiny cores.
5. **Empty is not a translation.** `""` and `" "` are not values. Mention
   in `translations-format.md`. Gate 09 will fail them; until then, do
   not scaffold blanks.
6. **Deliver.** If a second linguist is available for official/court
   work, they check write/find/say hits and terms against any issuer
   translation. The scripts will not.
7. **Harness, not SKILL.md sprawl.** Bakeoff / Codex session prompts say
   `pdf-translate only` (do not wander into other skills). Extra High/max
   is for visual rounds, not a required model. Haiku-class: evals only.

**Length line in SKILL.md today** says “If a cell must stay tiny, add its
core to `allow_scale`.” Change that to: reword first; `allow_scale` only
after a visual pass still cannot fit.

**Proof for session 0:** grep `SKILL.md` for `allow_scale` / `max_width` /
empty targets; no new test; unittest still green. Commit. Stop.

---

## Then the gates — one file per sitting

| Sitting | Copy into `/goal` | Locks |
|---|---|---|
| **08** | `goals/08-quoted-identifiers.md` | Quoted / `Schedule Q` still in the text layer |
| *after 08, different day* | canary, not a `/goal` | One strong + one weak model on the **same toy PDF** |
| **09** | `goals/09-empty-targets.md` | `""` / `" "` fail `--translations` |
| **10** | `goals/10-caption-width.md` | Caption wider than the button fails |
| **11** | `goals/11-override-markers.md` | Override must not drop `d.` / `$` |
| **12** | `goals/12-narrow-column-warning.md` | Extractor **warns** on skinny stacks; no auto-merge |

12 is warn-only. If 08 is a short sitting, 12 may ride in that session
**only if** you do not touch verify. Prefer its own sitting.

---

## After 08 — canary (not a gate)

Different day from 08. Same constructed fixture as the 08 test PDF (or a
copy). One model that inspects PNGs, one that does not. Score: did they
keep `Attachment A` / `Schedule Q`, write the four identity facts, and
search? Do **not** put the winner in `SKILL.md`. Do **not** add a
glossary because the weak model failed.

Any document class is fine. Do not use a real court form as the proof.

---

## Suggested calendar

```
08–10, 13 closed and committed
Next      /goal 11   override keeps d. and $
Then      /goal 12   skinny-column warning
Also      leftover skill text (allow_scale last; second linguist)
Optional  canary on the 08 toy PDF (not mixed with a gate)
Then      commit 08–12 + skill-text; pause (see HANDOVER §6 terminal stage)
```

Evidence write-up stays `goals/RECOMMENDATIONS.md`. Human explainer:
`recommendations.html`. Word-by-word canary: `quality-bakeoff.html`.
