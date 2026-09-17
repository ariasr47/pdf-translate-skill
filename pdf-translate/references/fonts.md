# Fonts by target script

Contents: the glyf-flavor rule · CJK · Arabic and Hebrew · Devanagari and
other Indic · Thai · Latin, Cyrillic, Greek · shaped and right-to-left
scripts in this pipeline (at the end).

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

`verify`'s `han-forms` gate (20) compares the delivered face with the Noto
Sans JP and SC references at the same weight, exactly. Use the same builds
for the job's face and for the references — the google/fonts variable TTFs
that `tools/fetch_test_fonts.py` fetches — or a legitimately Japanese face
can read above the 0.02 match bound and come back REVIEW instead of PASS. A
service ships the two reference faces beside its job faces and passes their
directory (`--reference-fonts DIR` / `reference_fonts=`). The directory must
hold `NotoSansJP-VF.ttf` and `NotoSansSC-VF.ttf` under exactly those names
(google/fonts publishes them as `NotoSansJP[wght].ttf` and
`NotoSansSC[wght].ttf`; rename on copy). An installed package has no
`tests/fonts/`, so until a service ships them every CJK job is REVIEW
`reference faces not found`, and a pipeline that runs with
`--fail-on-review` exits 1 on every CJK job from version 54 on.

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
document. Fonts: Noto Sans Devanagari / Bengali / Tamil / Khmer / Myanmar
/ Thai (glyf, with GSUB).

`prepare_font` probes the subset it writes for these scripts: the script's
probe cluster (क्षत्रिय, ক্ষ, க்ஷ, ខ្មែរ, သင်္ဘော) is rendered off the subset
glyph by glyph and through the Story engine and must lose glyphs (8 → 4
for Devanagari). A face with no usable GSUB fails there, and `verify`
re-probes the font program embedded in the output (gate 18), so a face
that cannot form conjuncts cannot ship. Thai and Lao have no such tell —
mark stacking never changes the count — so they are REVIEW there and the
rendered sample is the check. A face for a script nobody has measured
(Gujarati, Telugu, …) is REVIEW until a probe row is added to
`shaping_probe.PROBES`.

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
- A role you do not name falls back to the nearest one you did, and
  retypeset says so once per role that was actually used: `font roles:
  "bold" resolved to the regular face; 1 run(s) asked for it
  (notices[0])`. It is not a failure — a one-face job is legitimate — but
  a `<b>`, an `italic` part or a notice's `bold_lead` then draws at the
  regular weight, and the delivery must say so rather than call the page
  faithful. Paths are compared resolved, so a symlink to the regular face
  is the regular face.
- The harvested charset is every block of `translations.json` that gets
  drawn — targets, `merges[].html`, `overrides[].parts[].text` and
  `notices[].text` — collected by `job_charset()`. A `null` core is
  skipped, not iterated: it is covered by an override and never drawn.
  When the format grows a block, that function is the one place to add
  it, or the subset silently will not cover it and retypeset's glyph
  check will fail a correct build.
- `prepare_font.py` refuses a source font whose `OS/2.fsType` forbids
  embedding or subsetting. Noto, DejaVu and the other OFL families are
  always fine; a system font shipped with an operating system usually is
  not licensed for redistribution inside your output.
- `retypeset.py` checks every character of every placed run against the
  exact font object that will draw it and FAILs on a miss, naming the code
  points. It is the cheapest signal that you picked the wrong face: MuPDF
  itself substitutes a fallback mid-string, or draws a box, and says
  nothing.

## Shaped and right-to-left scripts in this pipeline

If the target script needs shaping (Arabic, every Indic script, Thai,
Khmer, Myanmar), retypeset places those runs with the Story engine so
letters join and conjuncts form, and writes `/ActualText` in logical
order; `--translations` looks there as well as `get_text()`. Dot leaders
and the `$` tail are refilled on those labels too. Hebrew is direction
only. verify fails an output whose Arabic came out unshaped, and — since
a broken Devanagari conjunct leaves no code-point tell — it also fails
any shaping-script target that no `/ActualText` span carries, because
that run was drawn glyph by glyph, and it probes every embedded face
that draws a conjunct-forming script (gate 18), so a face with no usable
GSUB fails even when the run went through the Story engine. **Layout is
not mirrored unless**
translations.json sets `"mirror": true` (flips text x and field/link
rects; graphics stay). Halt unless you have checked the render, the
logical text layer, *and* whether the skeleton (default) or the opt-in
mirror is acceptable. Confidently wrong text direction is worse than a
halt.
