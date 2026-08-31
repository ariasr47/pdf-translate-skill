---
name: pdf-translate
description: >-
  Translate a PDF from any language to any language while keeping the visual
  layout pixel-faithful and every fillable form field working — same field
  names, types, positions. Uses a strip-and-retypeset pipeline (never overlay,
  never redaction) with bundled scripts for text stripping, segmentation,
  font preparation, re-typesetting, and verification. Use this skill whenever
  the user wants a PDF translated, localized, or converted to another
  language — especially government/court/tax/immigration forms, contracts,
  applications, or any fillable PDF — even if they only say "make this form
  Japanese", "Spanish version of this PDF", or "translate this document but
  keep the formatting". Also use it when a user complains that a translated
  PDF broke its layout or its form fields.
---

# pdf-translate: high-fidelity PDF translation

*The YAML block above is optional metadata for systems that auto-load skills;
ignore it if yours doesn't. This document is self-contained — it works as plain
instructions for any agent or person with Python. Paths below are relative to
this file's directory; set `SK=/path/to/pdf-translate` and prefix them if you
are working elsewhere.*

Produce a translated PDF that is visually indistinguishable from the original
— same tables, rules, columns, checkboxes, dot leaders, page count — with
every fillable field preserved and working. The architecture that achieves
this is **strip-and-retypeset**: delete the original text at the
content-stream level, then re-insert translated text at the original
coordinates. Overlaying white boxes looks like a scanlation; regenerating the
document never matches; redaction annotations **delete form fields**. Don't
use those.

The seven scripts are **provider-neutral**: plain Python, no vendor SDK, no
assumption about which model or CLI is driving. Source-string translation is
a JSON mapping any person or any model can author; the rest of the pipeline
runs without that author. Do not ship a terminology glossary to compensate
for a weak model — register is the mapping author’s job, and a public skill
cannot maintain per-domain dictionaries. A model that will not inspect page
images or iterate should not author `translations.json`. The visual pass is
not optional — roughly half of all real defects are invisible to every
automated gate.

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
fonttools`). Born-digital PDFs only — a scanned PDF needs OCR first.
`extract_segments.py` and `verify.py` **fail** if a page has visible ink or
an embedded image but no extractable text; do not ship that file as a
translation. If the target script is RTL, retypeset writes `/ActualText` in
logical order and `--translations` looks there as well as `get_text()`
(which may still be visual-order for Arabic). **Layout is not mirrored
unless** translations.json sets `"mirror": true` (flips text x and
field/link rects; graphics stay). Read `references/fonts.md` and halt
unless you have checked the render, the logical text layer, *and*
whether the skeleton (default) or the opt-in mirror is acceptable.
Confidently wrong text direction is worse than a halt.

## Workflow

Run the bundled scripts from `scripts/` in this order. They do all the
deterministic work; your work is the language (translating, deciding
paragraph merges) and the visual inspection loop.

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
# author every null in translations.json, prepare_font once
python3 scripts/pipeline.py rebuild --work . original.pdf out.pdf \
    --fill-text "text in target script" --source-words-from segments.json
python3 scripts/pipeline.py render original.pdf out.pdf renders/
```

### 1. Recon

Open the PDF and note: page count, fields per page (`page.widgets()`), fonts,
whether `'/XFA' in pdf.Root.AcroForm` (hybrid LiveCycle form — Acrobat
renders the XFA layer instead of your edited pages until it's removed).
Read `references/failure-modes.md` **now** — it is short and every item in it
was a real, silent, hours-costing failure.

### 2. Strip

```bash
python3 scripts/strip_text.py original.pdf stripped.pdf
# optional: rewrite pushbutton captions in place (field count stays exact)
python3 scripts/strip_text.py original.pdf stripped.pdf \
    --captions captions.json
```

Removes all page text, keeps graphics/images/widgets, wraps content in q/Q,
removes XFA, and reports pushbuttons with no action (dead XFA scripts). Prefer
`--captions captions.json` (field-name → caption) to rewrite `/MK /CA` in
place and drop stale `/AP` streams so the widget count stays exact and
viewers do not keep drawing the source-language caption. Hide
(`--hide-buttons`) only when the button should disappear; hiding plus a
drawn replacement adds widgets unless you are replacing, not duplicating.

### 3. Extract and translate

```bash
python3 scripts/extract_segments.py original.pdf
```

Produces `segments.json` (geometry) and `to_translate.json` (unique strings).
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
confirm before translating), and possible wrapped-paragraph merges (declare
them explicitly; never auto-merge by geometry, it swallows sibling list
items).

The language decisions that matter:

- **Register**: match the document's domain (legal, medical, marketing) and
  use that domain's established terminology in the target language, not
  literal renderings.
- **Length**: expansion varies by pair (EN→DE grows ~30%, EN→JA often
  shrinks). Retypeset **fails** if a segment scales below 0.7×. Reword more
  compactly. If a cell must stay tiny, add its core to `allow_scale`.
- **Merges**: multi-line paragraphs must be translated as one unit and
  re-flowed. Declare each merge explicitly by its member lines — never
  auto-merge by geometry, it swallows sibling list items.
- **Leave verbatim — apply the write/find/say test.** Before translating any
  name or quoted string, ask: *will the reader have to write this, hand it to
  someone, or search for it?* If yes, it stays in the source language, because
  translating it breaks the thing it is for. Three kinds recur:
  - **Strings the form tells the reader to write.** FL-150 says: attach a sheet
    and write `"Question 1—Other Jobs"` at the top, and label an attachment
    `"Question 10g"`. That paper goes to a court whose staff reads the source
    language; a translated label cannot be matched to its question. Quoted
    strings inside an instruction are almost always this case — check every one.
  - **Official document and form names**: `Schedule C`, `Form W-2`,
    `Form I-130`. The reader must locate a real document carrying that exact
    name; スケジュールC sends them hunting for something that does not exist.
  - **Statutes, acronyms, URLs, emails, case and form numbers.**
  When a name is only being *referred to* rather than written or searched —
  "Social Security", "State of California" — translating is fine. For statutes
  a reader might look up ("Family Code"), a bilingual form such as
  `家族法（Family Code）` serves both, and beats a transliteration like
  ファミリーコード, which is neither meaningful nor searchable.
  Numbers and currency adapt only where target convention requires it, and say
  so when you do.
- Heed the extractor's warnings about in-span gaps — each needs an
  `overrides` entry with explicit x positions.

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

Use `--source-words-from segments.json` for same-script pairs (EN→ES/FR/DE):
the default regex flags the translation itself and tells you nothing, whereas
this asks the only useful question — did any of *this document's own* source
words survive? Expect a few false positives (proper nouns, words spelled the
same in both languages) and allowlist them deliberately.

Pass `--translations translations.json` so verify also fails if an authored
non-passthrough **target** (length ≥ 2, whitespace/NBSP normalized, hyphen
U+2010/U+2011 folded to ASCII `-`) never appears in the output text layer —
a stripped file, a failed write, or an NBSP/hyphen mismatch. Missing targets
are listed. This does not judge whether the wording is the right term.

The same flag also checks **pushbutton chrome**. Captions live in `/MK /CA`
and draw on top of the page; `get_text()` still sees them. Either rewrite
them in place with `--captions` at strip time (field count stays exact), or
put the caption in `skip` and leave the button as UI chrome. If the original
caption is still in the output and you did neither, verify fails and lists
it. Do not hide a button and draw a second widget. Omit `--translations`:
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
side-by-side comparison HTML. Summarize every judgment call: structural
changes (XFA removed, buttons replaced), compressed translations, locale
adaptations — the user should learn your decisions from you, not discover
them later.

## References

- `references/failure-modes.md` — the eight silent failures and their fixes.
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
