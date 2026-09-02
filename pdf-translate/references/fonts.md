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

## Arabic (and Syriac, N'Ko): shaped through the Story engine

Arabic letters join. A run drawn glyph by glyph comes out as isolated
letterforms, which is what `TextWriter` produces. Since gate 16, every run
whose target script needs shaping is placed with the Story engine
(`insert_htmlbox`, HarfBuzz), the same path merges use: letters join,
lam-alef ligates, and the run sits on the original baseline at the
original size and colour. `verify.py` FAILs an output whose Arabic came
out unshaped (joining letters in isolated form and nothing connected).

**Text layer.** What a shaped run leaves in the text layer is what the
shaper drew (presentation forms, sometimes glyph ids), so the logical
string lives in `/ActualText` (UTF-16BE). `verify.py --translations`
searches `get_text()` **and** those ActualText strings, so an authored
logical line must round-trip even when MuPDF's default extract is
visual-order or presentation-form glyphs (`طلب المساعدة` must appear in
ActualText, not only as `ةدعاسملا بلط`).

**Hebrew** needs no shaping, only direction: it still takes the
`TextWriter` path with `right_to_left=True` and the same `/ActualText`
wrap.

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
glyf); the font must carry the script's GSUB tables, which
`prepare_font.py` keeps when subsetting. Arial on Windows has both
scripts for tests.

## Devanagari, Bengali, Tamil, Thai, Khmer, Myanmar (complex shaping)

These scripts need conjunct and mark shaping. Runs in them take the Story
engine path automatically (gate 16), and the logical string goes into
`/ActualText`, because the text layer of a shaped Indic run is glyph ids.
Thai additionally has no spaces: line-breaking a merged paragraph needs
dictionary-based segmentation the engine does not do. Dot leaders on a
shaped-script label are not refilled (same as RTL). Still verify a
rendered sample with a reader of the script before building the whole
document. Fonts: Noto Sans Devanagari / Bengali / Tamil / Thai (glyf,
with GSUB).

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
- `retypeset.py` checks every character of every placed run against the
  exact font object that will draw it and FAILs on a miss, naming the code
  points. It is the cheapest signal that you picked the wrong face: MuPDF
  itself substitutes a fallback mid-string, or draws a box, and says
  nothing.
