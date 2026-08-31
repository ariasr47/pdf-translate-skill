# Fonts by target script

The one rule that overrides everything: **feed MuPDF only TrueType-flavored
(glyf) fonts.** Subsetted CFF/OTF renders ASCII and silently drops CJK and
other complex-script glyphs (failure-modes.md #3). System-installed Noto CJK
is usually OTF/OTC — do not use it directly; get a glyf source below.
`prepare_font.py`'s rasterization assert is the enforcement; if it fails,
your font source is wrong, not the pipeline.

## CJK (Japanese, Chinese Simplified/Traditional, Korean)

Google Fonts ships glyf-flavored VARIABLE TTFs — the reliable source:

- Japanese: `https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf`
- Simplified Chinese: `.../ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf`
- Traditional Chinese: `.../ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf`
- Korean: `.../ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf`

Instance weights from the variable font (`--instance wght=400`, `wght=700`),
then subset. Serif alternatives (Noto Serif JP/SC/TC/KR) exist for documents
whose original is serif. Bold in CJK forms is often better served by the
700 weight than synthetic bolding.

For field input (field_fonts.py) use the FULL instanced font, not the
translation subset — users type names with characters outside the document.

## Arabic, Hebrew (RTL)

Shaping at *render* time often looks correct: MuPDF's TextWriter joins Arabic
letters and draws Hebrew right-to-left. That is not the same as a correct
RTL document.

What the pipeline now does for the **text layer**: RTL targets (Hebrew /
Arabic unicode ranges) are written with `right_to_left=True` and wrapped in
`/ActualText` (UTF-16BE). `verify.py --translations` searches `get_text()`
**and** those ActualText strings, so an authored logical line must round-trip
even when MuPDF's default extract is still visual-order or presentation-form
glyphs (`طلب المساعدة` must appear in ActualText, not only as `ةدعاسملا بلط`).

**Layout is not mirrored by default.** Labels stay on the original LTR
baselines. Set `"mirror": true` in translations.json to flip text x
(`page_width - origin - run_width`) and field/link rects the same way.
Field names and types stay; rects change. **Graphics are not flipped**
(logos, rules, images stay). Look at the PNGs. Do not claim full RTL
without that visual pass — the page is still a source-language skeleton
with fields and type mirrored.

Do not claim full RTL from a pretty render. Halt unless you have verified
(1) the pixels, (2) the logical string is in ActualText / verify
`--translations`, and (3) whether default (un-mirrored) or `mirror: true`
is acceptable. Fonts: Noto Naskh Arabic / Noto Sans Hebrew (Google Fonts,
glyf). Arial on Windows often has both scripts for tests.

## Devanagari, Bengali, Tamil, Thai (complex shaping)

Same caution as RTL: these scripts require conjunct/mark shaping that plain
glyph placement does not do. Thai additionally has no spaces — line-breaking
a merged paragraph needs dictionary-based segmentation. Verify a rendered
sample with a reader of the script (or a careful glyph-level comparison
against a browser rendering) before building the whole document. Fonts:
Noto Sans Devanagari / Bengali / Tamil / Thai.

## Latin, Cyrillic, Greek (including Vietnamese)

Easiest case: almost any glyf TTF works — Noto Sans / DejaVu Sans cover all
three plus Vietnamese's stacked diacritics. Match the original's serif/sans
and approximate weight. Expansion warning: EN→DE/FR/ES/RU typically grows
15–35%, so expect the reword-over-shrink loop to matter more here, not less.

## Sizing guidance

- Subset translation fonts to the harvested charset (~100–300 KB per weight).
- Field-input fonts stay full-coverage; accept the size (a few MB) — blank
  glyphs in a user's typed name is the worse trade.
- Re-run prepare_font.py whenever translations change: a character added
  after subsetting renders as nothing.
