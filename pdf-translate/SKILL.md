---
name: pdf-translate
description: >-
  Translate a PDF from any language to any language while keeping the visual
  layout pixel-faithful and every fillable form field working — same field
  names, types, positions. Uses a strip-and-retypeset pipeline (never overlay,
  never redaction) with bundled scripts for text stripping, segmentation,
  font preparation, re-typesetting, and verification. Use this skill whenever
  the user wants a PDF translated, localized, or converted to another
  language — government, court, tax, immigration, or medical forms; contracts;
  applications; manuals; brochures; or any born-digital PDF — even if they
  only say "make this form Japanese", "Spanish version of this PDF", or
  "translate this document but keep the formatting". Also use it when a user
  complains that a translated PDF broke its layout or its form fields.
metadata:
  version: "20"
---

# pdf-translate: high-fidelity PDF translation

*The YAML block above is optional metadata for systems that auto-load skills;
ignore it if yours doesn't. This document is self-contained — it works as plain
instructions for any agent or person with Python. Paths below are relative to
this file's directory; set `SK=/path/to/pdf-translate` and prefix them if you
are working elsewhere.*

Produce a translated PDF that is visually indistinguishable from the original
— same tables, rules, columns, checkboxes, dot leaders, page count — with
every fillable field preserved and working. Any born-digital PDF, any
language pair the pipeline can place. The architecture that achieves this
is **strip-and-retypeset**: delete the
original text at the content-stream level, then re-insert translated text at
the original coordinates. Overlaying white boxes looks like a scanlation;
regenerating the document never matches; redaction annotations **delete form
fields**. Don't use those.

The seven scripts are **provider-neutral**: plain Python, no vendor SDK, no
assumption about which model or CLI is driving. Source-string translation is
a JSON mapping any person or any model can author; the rest of the pipeline
runs without that author. Do not ship a terminology glossary. Lexicon is
*this document's*: name what it is, look up the issuer's translation or that
class's established usage (step 1), then author the mapping. A public skill
cannot maintain per-domain dictionaries. A model that will not inspect page
images, will not look up, or will not iterate should not author
`translations.json`. The visual pass is not optional — roughly half of all
real defects are invisible to every automated gate.

Priority order when requirements conflict: **1) structure** (fields, links,
bookmarks must survive and work) > **2) layout** (only the text changes) >
**3) natural translation in the document's register** > 4) file size,
aesthetics, everything else.

Never regress: field names/types/rects stay identical (adding widgets is a
regression unless asked); never strip with redaction annotations; leave the
graphics layer untouched; feed the renderer only TrueType-flavored (glyf)
fonts; a missing non-passthrough translation fails the build.

## Requirements

Python with `pymupdf`, `pikepdf`, `fonttools` (`pip install pymupdf pikepdf
fonttools`). Born-digital PDFs only. Scans are out of scope with or without an OCR
layer: `extract_segments.py` and `verify.py` **fail** when a page has ink
or an image but no text, and also when a page's text is invisible (an OCR
layer over the scanned pixels, or text hidden under an image). In both
cases the words the reader sees are pixels; strip-and-retypeset would
print the translation over them, and this pipeline has no masking mode.
Tell the user; do not ship that file as a translation. If the target script needs shaping (Arabic, every Indic script, Thai,
Khmer, Myanmar), retypeset places those runs with the Story engine so
letters join and conjuncts form, and writes `/ActualText` in logical
order; `--translations` looks there as well as `get_text()`. Hebrew is
direction only. verify fails an output whose Arabic came out unshaped. **Layout is not mirrored
unless** translations.json sets `"mirror": true` (flips text x and
field/link rects; graphics stay). Read `references/fonts.md` and halt
unless you have checked the render, the logical text layer, *and*
whether the skeleton (default) or the opt-in mirror is acceptable.
Confidently wrong text direction is worse than a halt.

## Workflow

Run the bundled scripts from `scripts/` in this order. They do all the
deterministic work; your work is the identity record, the mapping, and
the visual inspection loop.

**Where the time goes.** On a 4-page form the seven scripts finish in a few
seconds. A 30–40 minute run is almost entirely translation authoring and
2–3 visual passes — not Python. After the first extract:

- Do **not** re-run strip, extract, or prepare_font unless the source PDF or
  the translation charset changed.
- Inner loop: edit `translations.json`, then `pipeline.py rebuild` (retypeset
  + verify) and `pipeline.py render` (PNGs at 110 dpi). Look at those PNGs.
- Run `compare.py` / `pipeline.py finish` **only when delivering.** compare
  rasterizes every page twice at 120 dpi into one HTML file; doing that every
  round is wasted work.

```bash
python3 scripts/pipeline.py init original.pdf --work .
python3 scripts/pipeline.py from-cores --work .
# write identity record, author every null, prepare_font once
python3 scripts/pipeline.py rebuild --work . original.pdf out.pdf \
    --fill-text "text in target script" --source-words-from segments.json
python3 scripts/pipeline.py render original.pdf out.pdf renders/
```

### 1. Recon

**Geometry.** Open the PDF and note: page count, fields per page
(`page.widgets()`), fonts, whether `'/XFA' in pdf.Root.AcroForm` (hybrid
LiveCycle form — Acrobat renders the XFA layer instead of your edited pages
until it's removed). Read `references/failure-modes.md` **now** — it is short
and every item in it was a real, silent, hours-costing failure.

**Identity — write this down before filling any translation.** Session notes
or `NOTES.md`, not `translations.json` (the scripts do not read it). Four
facts:

1. **Class** — one sentence a librarian could file (court income form,
   hospital consent, tax instructions, product brochure, …).
2. **Issuer** — who published it, or `none` / `unknown`.
3. **Parallel text** — URL or path of *this same document* in the target
   language, or `none`, or `not searched`.
4. **Identifiers** — names on *this* PDF the reader must still write, find,
   or say in the source language. Fill after extract (step 3).

**Lookup.** If you can search, you must. Search where a translator of this
class would look: the issuer's catalog (form number or title), the regulator,
the vendor's localized product. If a published translation of this same
document exists, **those terms of art win**. If none exists, use established
usage for that class in the target language — not a calque, not a word
invented on the page. If you cannot search, record `not searched` and do not
pretend you matched an official file.

### 2. Strip

```bash
python3 scripts/strip_text.py original.pdf stripped.pdf
# optional: rewrite pushbutton captions and widget text in place
python3 scripts/strip_text.py original.pdf stripped.pdf \
    --captions captions.json --widget-text widget_text.json
```

Removes all page text, keeps graphics/images/widgets, wraps content in q/Q,
removes XFA, and reports pushbuttons with no action (dead XFA scripts). Prefer
`--captions captions.json` (field-name → caption) to rewrite `/MK /CA` in
place and drop stale `/AP` streams so the widget count stays exact and
viewers do not keep drawing the source-language caption. The new caption
must fit the widget; verify `--translations` fails overflow. Hide
(`--hide-buttons`) only when the button should disappear; hiding plus a
drawn replacement adds widgets unless you are replacing, not duplicating.

**Widget text is not page text.** Tooltips (`/TU`), dropdown labels
(`/Opt`) and text-field defaults (`/V`, `/DV`) live in the annotation
dictionaries and never reach a content stream, so strip-and-retypeset
cannot touch them: without this channel a "fully translated" form still
shows the source language on every hover and in every dropdown.
`extract_segments.py` writes the `widget_text.json` scaffold; author each
`target`, then pass it back with `--widget-text` (or
`pipeline.py init … --widget-text`). A `null` target is a refusal, not a
skip — author it or delete the key. **Export values stay:** an `/Opt`
entry becomes `[export, display]` and only the display half is
translated, so `/V` and everything the form submits keep working. A spec
that asks to translate a choice field's `/V` is refused; verify's `/Opt`
parity gate fails any output whose export values moved.

Strip is also a gate. After saving, it re-reads the stripped file with
annotation appearances excluded; if any page still has text it prints
`FAIL` with the page and the text, exits non-zero and **does not leave the
stripped file on disk** (the same rule as retypeset on overflow). Text
inside nested Form XObjects and under `/Resources` inherited from the page
tree is stripped like page text. Widget captions and field values are
appearance streams, not page text; they never trip this gate.

### 3. Extract and translate

```bash
python3 scripts/extract_segments.py original.pdf
```

Produces `segments.json` (geometry), `to_translate.json` (unique strings)
and `widget_text.json` (the annotation strings — see step 2). Page text is
read from an annotation-free display list, so field values and the current
dropdown selection do **not** arrive as cores; translating those would draw
the translation on the page underneath a widget still showing the source.
If a page has visible content but zero extractable text, the script exits
non-zero and names OCR — that is a refusal, not an empty successful job.
Scaffold the mapping (no model, no auto-merge) then author every value:

```bash
python3 scripts/pipeline.py from-cores --work .
```

That writes `translations.json` with a **null** per core so retypeset still
fails until you fill them in. It will not overwrite an existing file unless
you pass `--force`. Format in `references/translations-format.md`.
The extractor also prints warnings: in-span gaps (need `overrides`),
write/find/say candidates (quoted strings, `Form`/`Schedule` names, URLs —
halt-and-confirm, not optional color), possible wrapped-paragraph
merges (declare them explicitly; never auto-merge by geometry, it swallows
sibling list items), and `narrow-column` stacks — three or more cores
sharing a column under 90 pt wide (pay-stub boxes, label stacks). Those
are warn-only; nothing merges them for you.

Finish the identity record **before** filling any translation: copy
write/find/say warnings into **Identifiers** (halt-and-confirm, not optional
color) and finish **Parallel text** if the form number was not visible at
recon.

The language decisions that matter:

- **Register**: step 1 lookup. Parallel text wins; else that class's
  established usage in the target language. Do not calque.
- **Length**: expansion varies by pair (EN→DE grows ~30%, EN→JA often
  shrinks). Retypeset **fails** if a segment scales below 0.7×. **Reword
  first** — a shorter, equally correct phrase is almost always available,
  and it is the fix that keeps the page readable. `allow_scale` is the
  **last resort**, for a cell whose geometry genuinely cannot hold the
  target at full size; every core you list there ships as smaller type,
  so name them in the delivery summary.
- **Merges**: multi-line paragraphs must be translated as one unit and
  re-flowed. Declare each merge explicitly by its member lines — never
  auto-merge by geometry, it swallows sibling list items.
- **Narrow columns**: when the extractor reports a `narrow-column` stack,
  treat the box as *one* decision, not five. Either declare one merge over
  those lines and let it re-flow, or write one `overrides` entry with a
  `max_width` per part so the target wraps inside the column. Translating
  each line-break on its own is how a pay-stub box turns to crumbs — the
  target's word order rarely breaks where the source's did.
- **Leave verbatim — apply the write/find/say test.** Before translating any
  name or quoted string, ask: *will the reader have to write this, hand it to
  someone, or search for it?* If yes, it stays in the source language,
  because translating it breaks the thing it is for. Recurring kinds:
  - **Quoted payload inside an instruction.** Translate “Write … at the top”;
    keep the quoted span exactly. That paper is matched by people who read
    the source language.
  - **Official document and form names** the reader must locate (`Schedule C`,
    `Form W-2`, `Form I-130`). Transliteration is a defect: it is neither
    meaning nor a search hit.
  - **Statutes, acronyms, URLs, emails, case and form numbers.**
  - **Units the document tells the reader to use** — paper size
    (`8 1/2-by-11-inch` stays; do not convert to A4 on a US filing), currency
    symbols the issuer printed (`$` stays `$` on a US form). Revision codes
    stay; a calendar date may localize.
  When a name is only *referred to* rather than written or searched,
  translating is fine. A name a reader might look up can be bilingual
  (`target (Source)`); that beats a transliteration, which is neither
  meaningful nor searchable. Numbers and currency adapt only where target
  convention requires it *and* the document is not instructing a filing
  convention — say so when you do.
- Heed the extractor's warnings about in-span gaps — each needs an
  `overrides` entry with explicit x positions. An override replaces the
  whole span, so its parts must carry the source list marker (`d.`) and
  the tail after the dot leaders (`$`); `--translations` fails an override
  that drops them (verify reads `segments.json` beside the mapping, or
  `--segments`).

### 4. Fonts

Read `references/fonts.md` for the target script, then:

```bash
python3 scripts/prepare_font.py FONT.ttf translations.json font-sub.ttf \
    [--instance wght=700] --sample "text in target script"
```

The script asserts the font actually rasterizes — never skip this; the
classic failure (subsetted CFF + CJK) draws *nothing* and reports no error.
`pyftsubset` is found on PATH, next to the interpreter, or as
`python -m fontTools.subset` — it does not have to be on PATH.

### 5. Retypeset

```bash
python3 scripts/retypeset.py stripped.pdf segments.json translations.json out.pdf
```

Every character of every placed run is checked against the exact font
object that will draw it. A character the font lacks **fails the build**:
MuPDF substitutes its own fallback face mid-string, or draws a box, and
reports nothing — the ink gate barely moves and the text layer still reads
correctly. Pick a font that covers the target script
(`references/fonts.md`); the run names the code points.

Rotated lines (side labels, margin stamps) keep their angle: the extractor
records each line's direction and retypeset morphs the run about its own
origin, so origin, bbox and direction match the source. The width budget
runs along that direction. Dot leaders, `center` and the RTL mirror are
horizontal-only ideas and are skipped on a rotated run; a rotated run whose
target also needs shaping (Arabic, Indic, Thai…) is **refused**, because
the Story engine places shaped text upright and drawing it flat on a
rotated label ships confidently wrong text.

Fails loudly if any segment lacks a translation — fix and re-run until it
passes. That exit code is your coverage gate; missing text must never ship
silently. It also **fails** (does not save) if any run scales below 0.7×
versus the original size — a note is not a ship. Shorten the translation,
or list that core (or merge first line) in `allow_scale` if the cell must
stay tiny.

### 6. Verify — gates, then eyes

```bash
python3 scripts/verify.py original.pdf out.pdf \
    --fill-text "text in target script" \
    --source-words-from segments.json --allow ACRONYM1,PROPERNOUN \
    --translations translations.json
```

The leak scan follows the **source document's script**, detected from its
text layer and printed (`leak scan: source script CJK; output script
Latin`). When the output is in another script, surviving runs of the
source script are the leaks: three or more consecutive words, or six or
more characters of a spaceless script (CJK, Thai, Khmer…), FAIL; shorter
leftovers are REVIEW. When both sides share a space-delimited script
(EN→ES/FR/DE, RU→UK) the scan uses *this document's own* source words,
harvested from the original automatically; `--source-words-from
segments.json` is still accepted and preferred when you pass it. Expect a
few false positives (proper nouns, words spelled the same in both
languages) and allowlist them deliberately. When both sides share a
spaceless family (ZH↔JA) the scan prints one REVIEW line and cannot gate;
lean on `--translations` and the visual pass.

Pass `--translations translations.json` so verify also fails if an authored
non-passthrough **target** (length ≥ 2) never appears **verbatim** in the
output text layer — a stripped file or a failed write. Missing targets are
listed. This does not judge whether the wording is the right term.

The comparison is verbatim because retypeset **canonicalizes the text
layer**. MuPDF builds an embedded font's `/ToUnicode` by reverse-mapping
its cmap, so the space glyph comes back as NBSP, the hyphen as U+00AD or
U+2010, and common kanji as CJK Compatibility Ideographs (立 as U+F9F7):
the page looks perfect while the words in it cannot be searched, copied or
matched. After saving, retypeset rewrites `/ToUnicode` for the glyphs it
placed to the code points you authored, and the always-on **canonical text
layer** gate FAILs any of those characters that are in neither the original
nor your mapping.

The same flag also checks **pushbutton chrome**. Captions live in `/MK /CA`
and draw on top of the page; `get_text()` still sees them. Either rewrite
them in place with `--captions` at strip time (field count stays exact), or
put the caption in `skip` and leave the button as UI chrome. If the original
caption is still in the output and you did neither, verify fails and lists
it. Do not hide a button and draw a second widget. Captions must **fit the
widget rect**: `--translations` FAILs if Helvetica `text_length` of the
output `/CA` is wider than the button minus a 2 pt pad each side. Prefer
short chrome (`Print` / `OK`) over a sentence in a tiny button.

Choice-field **`/Opt` export parity** is checked always, like field parity:
the export half of every dropdown entry must be byte-identical to the
original's, in the same order. Translate the display half (step 2), never
the export — the export is what the form submits.

The same flag also checks **write/find/say identifiers**. Quoted strings and
`Form` / `Schedule` / `Attachment` / `Exhibit` names from the original page
must still appear in the output text layer. Missing ones FAIL and are
listed. If you meant to translate a span, list it in `allow_translate` and
record why in NOTES (scripts do not read NOTES). It also checks that every
override's parts still carry the source marker and tail (`d.`, `$`); it
needs `segments.json` beside `translations.json` or `--segments`, and
SKIPs rather than fails without one. Omit `--translations`:
field / fill / ink / leak / scan gates are unchanged.

All gates must pass. Then the step that actually creates the quality:
**render every page of the output next to the original (~110 dpi) and look
at them yourself.** Every real defect in this class of work — gray text,
leaders through checkboxes, over-shrunk labels, double-drawn button captions,
mis-centered headers — is caught only by inspecting renders. Fix, rebuild,
re-render. The first build is never right; budget 2–3 iterations and do not
declare victory until a full-page visual pass is clean.

### 7. Field fonts (fillable PDFs the user will type into)

```bash
python3 scripts/field_fonts.py out.pdf FULL_FONT.ttf final.pdf
```

Users type arbitrary names — characters outside your translation's subset —
so this embeds a FULL-coverage font, points every text field's default
appearance at it, and sets NeedAppearances. Skip only for non-form PDFs.

### 8. Deliver

```bash
python3 scripts/compare.py original.pdf final.pdf comparison.html \
    --labels "English (original)|Français (traduit)" --lang fr
```

Deliver three things: the translated PDF, the original used, and the
side-by-side comparison HTML. Summarize every judgment call: the four
identity facts (class, issuer, parallel text or `none`/`not searched`,
identifiers), structural changes (XFA removed, buttons replaced), compressed
translations, `allow_scale` cores, locale adaptations — the user should
learn your decisions from you, not discover them later.

**Name a second reader for official work.** For court, government, medical
and legal filings, say plainly in the delivery that a qualified human
reviser should read the target text before it is relied on, and that the
scripts are not that person. Every gate here checks structure; none of them
can tell a plausible wrong term from the right one (養子支援 on a
child-support page passes every gate). The professional standard for this
class of work is a second linguist, and the honest deliverable says so.

## References

- `references/failure-modes.md` — the fourteen silent failures and their fixes.
  Read during recon, before touching the file.
- `references/translations-format.md` — the translations.json contract
  (translations, merges, overrides, center, skip, fonts). Read before
  authoring translations.
- `references/fonts.md` — per-script font sourcing (CJK, Arabic, Devanagari,
  Thai, Latin/Cyrillic/Greek) and the glyf-flavor rule. Read at step 4.

Regression tests (tiny constructed PDFs, no vendor, no FL-150 dependency):

```bash
python3 -m unittest tests.test_pipeline -v
```
