# Objective: logical-order RTL text layer without mirroring layout

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md`, `references/fonts.md` (Arabic/Hebrew). Do not
> read `work/translations.json`. Do not implement layout mirroring,
> glossary, OCR, or overflow work.

---

## 1. Compass (not done)

MuPDF TextWriter *draws* Arabic/Hebrew so it looks right. `get_text()`
does not: Hebrew is visual-order unless `right_to_left=True`; Arabic is
presentation-form glyphs, so even `s[::-1]` is not the authored string.
Copy/paste, search, and `--translations` then lie. Layout is still the
LTR skeleton (labels at the original origin). This session fixes the
**text layer** only. Queue 05 is mirroring.

## 2. Done when — closed bar

1. **Round-trip.** Constructed LTR English page (not FL-150) retypeset to
   authored Arabic **and** Hebrew. The authored logical string is
   recoverable from the output: `/ActualText` (UTF-16BE) and/or
   `get_text()` after NBSP normalize. `verify --translations` PASSes.
   Same mapping against stripped PDF still FAILs (01).
2. **Not mirrored.** Span bbox `x0` stays on the original LTR side
   (e.g. ~72pt), not flipped to the right margin. No x-mirror, no
   `align=right` as a substitute for ActualText.
3. **LTR unchanged.** Existing unittest + corpus. Fillable EN→ES still
   0. Scans / skip-ink / chrome / overflow gates unchanged.
4. **Docs.** `fonts.md` + SKILL: logical order is ActualText (get_text
   may stay visual for Arabic); layout still not mirrored. Update the
   unittest that currently requires “visual-order” as the whole story.

## 3. Not done when

- Opt-in mirrored layout (05)
- Glossary, OCR, `/StructTreeRoot` rebuild, PDF/UA claim

## 4. Method

Detect RTL in the **target** (Hebrew/Arabic blocks). Those runs:
`TextWriter.append(..., right_to_left=True)` then wrap the last `BT..ET`
with `/Span << /ActualText <FEFF…> >> BDC … EMC`. Verify placement hay
is `get_text()` plus extracted ActualText. Tiny constructed PDFs.
Arial-or-Noto if it `has_glyph` Arabic and Hebrew; else SkipTest.

## 5. Invariants

Field identity, no redaction, graphics untouched, provider-neutral, no
Japanese-only branch.

## 6. Proof

In-repo Arabic + Hebrew tests. Unittest + corpus still green.
