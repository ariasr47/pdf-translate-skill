# Objective: shaped scripts go through the HarfBuzz path; unshaped Arabic is a FAIL

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md` Requirements, `references/fonts.md`,
> `scripts/retypeset.py` (single-line placement, `rtl_jobs`, merges via
> `insert_htmlbox`), `scripts/verify.py` (placement gate reads
> `/ActualText`). Do not implement mirroring changes, widget text, a
> glossary, or OCR. Not FL-150.

---

## 1. Compass (not done)

Every single-line run is drawn with `TextWriter`, which does no
complex-script shaping. Arabic comes out as isolated letterforms, Devanagari
conjuncts as consonant + halant sequences. The merges path already uses the
Story engine (`insert_htmlbox`, HarfBuzz) and renders both correctly. The
placement gate reads the logical string from `/ActualText`, the ink gate
barely moves, and `fonts.md` says shaping works. A native reader gets
visibly wrong text with every gate green. This session routes runs whose
target script needs shaping through the Story engine and makes unshaped
Arabic a FAIL.

## 2. Done when — closed bar

1. **Routing.** `retypeset.needs_shaping(text)` is true for Arabic-family
   (Arabic, Syriac, N'Ko), every Indic script, Thai, Lao, Khmer, Myanmar
   and Tibetan; false for Hebrew (bidi only), Latin, Cyrillic, Greek,
   Hangul and CJK. Such runs are placed with `insert_htmlbox` in a rect
   whose top is 0.8 × size above the original baseline and one line tall,
   left edge at the computed x, same size and colour, bold font when the
   source was bold; the returned scale feeds the existing 0.7× gate; the
   logical string is wrapped in `/ActualText`. Overrides and markers keep
   working (marker drawn by TextWriter, body shaped).
2. **Constructed, not FL-150.** An English line translated to a four-word
   Arabic phrase: the output text layer contains initial or medial
   presentation forms, `/ActualText` holds the logical string, the run's
   left edge and baseline are within 1.5 pt of the source segment, and
   `verify --translations` PASSes. A Devanagari target renders like the
   Story engine's own output and unlike TextWriter's (pixel comparison).
   A long Arabic target in a narrow gap FAILs retypeset (no file).
3. **Gate.** `verify.py` reads the output's raw characters: a page with
   three or more joining Arabic letters in isolated form and no initial
   or medial form FAILs "Arabic drawn unshaped". Always runs; silent when
   the output has no Arabic presentation forms.
4. **No regressions.** unittest + corpus green; Hebrew still takes the
   TextWriter path (`RtlTextLayerTests`, `RtlLayoutTests` unchanged); the
   mirror opt-in still flips shaped runs; Latin and CJK placement is
   byte-for-byte what it is today.
5. **Docs.** `fonts.md` RTL and complex-script sections say what is true
   now (shaping is the Story path, the text layer of shaped runs lives in
   `/ActualText`, Hebrew is bidi only, still look at the PNGs);
   `failure-modes.md` gets the unshaped-script class; `SKILL.md`
   Requirements points at it.

## 3. Not done when

- Changing the mirror semantics or the dot-leader path for shaped labels
  (shaped labels with dot leaders keep the plain path, as RTL does today)
- A glyph-form gate for Indic scripts from code points (the text layer of
  shaped Indic is glyph ids; only ActualText is reliable)
- Vertical text, font fallback across scripts, glossary, OCR

## 4. Method

Tiny constructed PDFs; Arabic through a system TTF that has GSUB for
Arabic (`find_rtl_font`), Devanagari through Nirmala UI or Mangal,
`SkipTest` when absent. Import shipped `retypeset` and `verify`. Facts
measured before coding: `insert_htmlbox` puts a single line's baseline at
0.8 × size below the rect top for every font tried, starts the run at the
rect's left edge, and only wraps a one-line-tall rect below the 0.7× gate.

## 5. Invariants

Field identity, no redaction, graphics untouched, provider-neutral,
`/ActualText` for every shaped run, gates 01–15 unchanged.

## 6. Proof

In-repo tests: routing unit, Arabic shaped-and-on-baseline, unshaped
Arabic FAILs verify, Devanagari via the Story path, narrow-gap overflow.
Full unittest + corpus.
