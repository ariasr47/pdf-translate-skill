# Objective (lane B): the pipeline can add the notice it requires

> Hand this to a `/goal` session. Self-contained. Read
> `references/compliance.md` §1, `scripts/retypeset.py` (how a placed run
> gets its font, colour and the canonical text layer), the three notice
> scripts in `runs/canary-2026-09-03/*/` (`add_notice.py`,
> `insert_notice.py`, `place_notice.py` — not committed; re-run the canary
> if they are gone), and the run-2 records. Not FL-150.

---

## 1. Compass (not done)

`compliance.md` requires a target-language "translation for information
only" notice on page 1 of any form the reader signs or files. The
pipeline has no way to add text that is not the translation of an
existing string. Measured: **four of five runs on a form that needs the
notice wrote their own script** — Fable in run 1 and run 2, Sonnet, Opus
— each re-deriving fonts, placement and the canonical-layer rewrite by
hand. Opus's variant put the notice text in `translations.json` so the
subset and the gates covered it; the others patched the layer afterwards.
Haiku did not add one. The skill says "if nothing fits, say so"; it does
not say how to add one when something does.

## 2. Done when — closed bar

1. **`notices`** in `translations.json`: a list of `{page, text, box,
   size?, bold_lead?}` the author writes, placed by retypeset with the
   job's fonts (regular, or a bold lead-in via `‖`), at the box the author
   chose, through the same glyph check, canonical-layer rewrite and
   placement gate as every other run. No page is added; nothing else
   moves; a box that overlaps existing ink is the author's to see on the
   render.
2. **The leak scan is already right** (row 20): the quoted source title
   inside the notice is a kept run. A test proves a notice that quotes
   `/Title` passes and one that leaves a source-language sentence fails.
3. **`compliance.md` §1** says: put the wording in `notices`, choose the
   box from the render, keep the source title as one unit.
4. **Tests.** A notice placed at the foot of page 1: present verbatim in
   the layer, the glyph check applied, page count unchanged; a `null`
   text refuses like a null translation.
5. Full unittest + corpus green; `metadata.version` bumped.

## 3. Not done when

- Choosing the box by geometry
- Adding a page
- A notice the reader cannot read (source-language wording)
- Any change to what the leak scan keeps

## 4. Method

Take the wording from `compliance.md`, the box from a render, place it
through retypeset; assert the layer and the gates.

## 5. Invariants

Nothing added but what the author wrote; every run goes through the same
gates.

## 6. Proof

The fixture's notice in the layer and on the render; the leak-scan test;
full unittest + corpus.

## 7. Closing note — 3 September 2026, closed

**The premise, restated from the measurement.** Four of five canary runs
on a form that requires the notice wrote their own script to place it —
`add_notice.py`, `insert_notice.py`, `place_notice.py` — each re-deriving
fonts, placement and the canonical-layer rewrite by hand. Nothing was
wrong with what they produced; the point is that the pipeline made them
build it five times.

**Done bar, item by item.**

1. **`notices`** in `translations.json`: `{page, text, box, size?,
   bold_lead?}`. retypeset places each one through the Story engine into
   the author's rect with the job's own fonts, and it goes through
   everything a merge goes through — `check_glyphs` on the regular face
   (and the bold face when `bold_lead` is set), `consider_ratio` and so
   row 25's scale report, the `/ToUnicode` canonicalization (the notice's
   characters join `placed`), and verify's placement gate. `‖` splits the
   bold lead-in, the same split a translation uses; `size` defaults to
   8 pt; `mirror` flips the box like any other rect. No page is added and
   nothing else moves.

   Refused by name, before anything is drawn: a null or blank text, a page
   outside the document, a box that is not four numbers, an empty or
   inverted box.

2. **The leak scan is unchanged and was already right.** The end-to-end
   test places a notice quoting the source `/Title` and verify exits 0
   with the title printed as a kept note; the same build with one English
   sentence left untranslated on the page FAILs on that sentence and not
   on the notice.

3. **`compliance.md` §1** gained *How to put it there* — the JSON, what
   the gates do to it, `‖` and `bold_lead`, the 8 pt default — and *Choose
   the box from a render, not from arithmetic*: nothing computes it, no
   gate judges what it overlaps. `translations-format.md` carries the
   block; `SKILL.md` steps 1 and 8 point at it instead of leaving the
   author to write a script.

4. **Tests** (`NoticeChannelTests`, 7): the notice verbatim in the layer
   (with the gate's own whitespace rule, because it wraps in its box like
   a merged paragraph), placed at its own size, page count unchanged,
   verify 0 with the title kept as a note; the gate collecting notice
   text as a target; a source-language sentence beside it still failing;
   a character the font cannot draw failing; five malformed notices
   refused by name with no file written; an empty `notices` changing
   nothing.

   The seventh discriminates the bold role, which font names cannot: only
   one Latin face ships with the tests, so `bold` is pointed at a face
   with no Latin — `bold_lead: true` then fails on the glyph check and
   `bold_lead: false` builds, which is only possible if the lead really
   goes through the bold font.

5. **Looked at the render**, as the brief asks: the notice sits at the
   foot of page 1 in two wrapped lines, inside its box, with the form's
   own text untouched above it.

6. 212 tests, no skips, green locally; corpus table unchanged. SKILL.md
   body 498 → 499 lines. `metadata.version` 43 → 44.

Not done, as the brief asked: no box is chosen by geometry, no page is
added, nothing checks that the wording is in the target language (that is
the author's judgment and the visual pass's), and what the leak scan keeps
did not change.
