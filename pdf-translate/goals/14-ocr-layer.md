# Objective: refuse an OCR'd scan — invisible text over pixels is not a text layer

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md` Requirements, `references/failure-modes.md` §9,
> `scripts/extract_segments.py` (`page_has_visible_content`),
> `scripts/verify.py` (gate 5), then `corpus/verdicts.json`. Do not
> implement OCR, a masking / white-box mode, per-span invisible-text
> handling, or the leak-scan rewrite — separate rows. Not FL-150.

---

## 1. Compass (not done)

Gate 5 refuses a page that has ink or an image but no text, and the skill
then says "OCR first". An OCR'd scan is exactly what that advice produces:
an image plus an invisible text layer (render mode 3). Extract sees text,
strip removes it, retypeset prints the translation over the scanned
pixels, the ink ratio (~2×) stays under the 3× ceiling, and verify PASSes.
The reader gets both languages on top of each other. This session makes
"the text a page carries is not what the reader sees" a **FAIL** in extract
and verify, and corrects the advice: a scan is out of scope with or
without an OCR layer.

## 2. Done when — closed bar

1. **Oracle.** `strip_text.invisible_text_pages(src)` strips a temp copy
   and compares 72-dpi renders page by page. If the pixels that change are
   fewer than 3% of the page's text-span area (annotation appearances
   excluded), the text is invisible. Returns `[(page, fraction)]`. Pages
   whose original render has negligible ink are skipped (pale blank is not
   a scan).
2. **Refuse.** `extract_segments.py` exits non-zero listing those pages;
   the message says the text layer is invisible (an OCR layer), that the
   visible words are pixels, and that this pipeline has no masking mode.
   `verify.py` FAILs the same way from the original.
3. **Constructed, not FL-150.** (a) Full-page image of rendered text plus
   the same text in render mode 3 → extract and verify FAIL. (b) Visible
   text over a full-page light background image (a brochure) → not
   flagged. (c) A plain text page → not flagged.
4. **Corpus.** `corpus/ocr_layer.pdf` with the new verdict
   `refuse+ocr-layer`; the harness asserts both exits non-zero and the
   message; README lists the kind.
5. **No regressions.** unittest + corpus green: `image_only.pdf` still
   `refuse+OCR`, `pale_blank.pdf` still `skip-ink`, `colored.pdf` (white
   text on a dark band) still `translate`. Gate 13 unchanged.
6. **Docs.** `SKILL.md` Requirements no longer says "OCR first": scans are
   out of scope with or without an OCR layer, and it says why.
   `failure-modes.md` §9 gets the OCR-layer paragraph.

## 3. Not done when

- A masking / white-box translation mode
- Per-span classification on mixed pages (a later warn-only row)
- Parsing `3 Tr` from content streams as the oracle (pixels are the oracle)
- OCR, glossary, RTL shaping

## 4. Method

Tiny constructed PDFs. Import shipped `strip_text` / `extract_segments` /
`verify`. The oracle is "does removing the text change the rendering?":
it needs no render-mode parsing and also catches text hidden under an
image or drawn in the background colour.

## 5. Invariants

Field identity, no redaction, graphics untouched, provider-neutral; the
helper reuses gate 13's strip and never writes next to the source.

## 6. Proof

In-repo tests: helper unit, extract + verify FAIL, brochure not flagged.
Corpus row. Full unittest + corpus.
