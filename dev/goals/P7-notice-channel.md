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
