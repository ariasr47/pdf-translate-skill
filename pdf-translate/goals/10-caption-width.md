# Objective: fail verify when a pushbutton caption is wider than its rect

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md` caption paragraphs, `scripts/strip_text.py`
> `--captions`, `scripts/verify.py` chrome gate (02). Do not implement
> 08/09/11/12, glossary, or OCR. Not FL-150.

---

## 1. Compass (not done)

Gate 02 fails leftover **English** chrome. It PASSES a rewritten `/MK
/CA` even when the new string is 40 letters in a 60-pt-wide button
(Terra High: long privacy sentence, still PASS). Clip is a layout
defect `get_text()` cannot see. This session measures width.

## 2. Done when — closed bar

1. **Measure.** With `--translations`, for every output pushbutton with a
   caption of length ≥ 1: `helv` `text_length(caption, fs)` vs
   `widget.rect.width`. `fs` = `widget.text_fontsize` if that value is
   `> 0`, else `max(4, rect.height - 4)`. Pad **2 pt** each side: FAIL
   if `width > rect.width - 4`. List `field_name` + caption. Helvetica
   is the default `/DA` face for these widgets; do not pull CJK metrics
   into this gate (short chrome is the fix; see SKILL.md).
2. **Constructed LTR.** One pushbutton, rect width **60 pt**, caption
   **40 ASCII letters** via `--captions` → FAIL naming the field. Same
   widget with a 2–4 character caption that fits → PASS. Field count
   stays exact (still `--captions`, not hide+draw).
3. **Skip is not a hall pass for overflow.** A `skip`'d original caption
   that already overflowed the *source* button is out of scope (do not
   fail the original form). This gate looks at **output** `/CA` only.
4. **No regressions.** Omit `--translations` → this gate does not run.
   Chrome 02 cases (skip / leftover Print / Imprimir rewrite) still
   behave. unittest + corpus green. No glossary.
5. **Docs.** SKILL.md: captions must fit; gate 10 fails overflow.
   `failure-modes.md` §6 can point at clip as measured, not only eyes.

## 3. Not done when

- Empty targets, identifier round-trip, override markers
- Changing field parity
- A “max 3 kanji” language rule
- Bakeoff

## 4. Method

Tiny constructed PDF. Import shipped `strip_text` + `verify`. Assert the
helper on known (rect, string, fs) triples before wiring the gate.

## 5. Invariants

Field names/types/rects identical. Provider-neutral.

## 6. Proof

Unit tests: overflow FAIL, short caption PASS, omit-flag does not run.
Full unittest + corpus.
