# Failure modes — every one of these is silent

These were all hit for real while translating a 266-field California court
form. None produced an error at the point of failure; each was only visible
in a rendered page or a specific viewer. The bundled scripts already guard
against most of them, but you need to know them to interpret script output
and to catch the ones only your eyes can see.

## 1. Hybrid XFA forms render the wrong layer in Acrobat

LiveCycle-authored PDFs (most government forms) carry `/AcroForm /XFA`.
Acrobat renders the XFA layer INSTEAD of the page content streams — your
translated pages look perfect in Chrome/Preview/pdfium and are completely
invisible in Acrobat. `strip_text.py` deletes the XFA entry (the AcroForm
fields are independent and survive). Consequence to handle: pushbuttons
whose behavior lived in XFA scripts (no `/A` action) are now dead. The
script inventories them; either hide them and draw translated replacements
wired to standard actions (`this.print();`, `this.resetForm();`,
`app.execMenuItem("SaveAs");` as widget JS), or leave them and say so.

## 2. Redactions delete form fields

`add_redact_annot` + `apply_redactions` removes annotations — including
field widgets — that overlap the redaction area. This is why the pipeline
removes the text from `BT..ET` blocks in the content streams instead:
widgets are annotations, not page content, so a content-stream edit cannot
touch them.

## 3. Subsetted CFF fonts silently drop CJK glyphs in MuPDF

A `pyftsubset`-subsetted OTF (CFF outlines) renders ASCII fine and draws
NOTHING for kanji — no exception, no .notdef boxes, just absence. MuPDF's
own `subset_fonts()` fails on the same fonts ("Reserved charstring byte").
Only TrueType-flavored (glyf) fonts are reliable. `prepare_font.py` enforces
this with a rasterization assert (dark-pixel count on a rendered sample).
Trust the assert, not `has_glyph()`.

## 4. Graphics-state leakage recolors your text

A page's content stream can end with a non-default fill color or alpha
active. Content appended afterward inherits it — symptom: everything you
insert on one particular page comes out gray while other pages are fine.
`strip_text.py` wraps surviving content in `q ... Q` so appended text always
starts from the default state. If you ever see tinted output anyway, check
for nested un-balanced `q/Q` in Form XObjects.

The leak also runs the other way. `BT`/`ET` do not save and restore the
graphics state, so a colour, `gs`, line width or `cm` set inside a text
object stays in effect for the graphics drawn after `ET`. Until v63, strip
dropped whole text objects, and with them that state. arxiv's pale table
shading came out black, USCIS N-400's rules came out white, and no gate saw
it. Strip now removes only `BT`, `ET` and the text operators (showing,
positioning, text state) and keeps everything else in place. The one
exception is text drawn in a clipping render mode (`Tr` 4–7). It is still
dropped whole, so graphics that relied on that clip draw unclipped. The
product chose not to refuse such pages (`docs/DECISIONS.md`, 2026-09-24).

## 5. Dot leaders invade checkbox gaps

Rows like `Public assistance [ ] currently receiving ......... $` put a
widget in a mid-line gap. The dots are text and get stripped with everything
else; if you refill them from the (shorter) translated label to the amount
column, they plow straight through the checkbox. `retypeset.py` refills at
most the ORIGINAL dot-run width anchored at the original right edge. If you
hand-place any leaders, follow the same rule.

## 6. Widgets draw their own captions over your text

Pushbuttons carry captions in `/MK /CA` rendered by their appearance stream
ABOVE page content. Translating the page text underneath just double-draws:
English caption on top, your translation peeking out. Either hide the button
and draw a translated replacement, or skip translating that page text (add
it to `skip` in translations.json) and leave the button as UI chrome.
A rewritten `/CA` can still **clip**: gate 02 only checks leftover English;
`--translations` also measures Helvetica caption width against the widget
rect (2 pt pad each side) and FAILs if the string does not fit. Short
chrome, not a sentence in a 17-pt-tall button.

## 7. Dropped text color turns white headings black

A heading set in white on a dark band is just a span with a color attribute.
If your extraction ignores color and your writer defaults to black, that
heading is re-drawn black-on-dark — illegible, and **no structural gate sees
it**: field parity is fine, and ink density barely moves because the band was
already dark. `extract_segments.py` records `color` per segment and
`retypeset.py` groups segments into one TextWriter per color; merged
paragraphs carry a `color` too. If you hand-place any text, carry the color
with it. This is the clearest case of why the visual pass is mandatory.

## 8. Things only your eyes catch

The verify gates check structure. They cannot see: a label shrunk to 4pt,
a header centered on the wrong midpoint, a left-flush caption that `center`
moved off the rule it labels, a paragraph that re-wrapped one line taller
and now kisses the rule below it, two segments overlapping by a few points.
Render every page beside the original and look. This is not optional
polish — in practice it is where half the defects surface, and it is the
difference between "plausible" and "indistinguishable".

## 9. A scanned page passes every gate untranslated

A PDF that is only a photograph of a page has no `BT`/`ET` text. Strip
removes nothing, extract emits zero segments, retypeset writes the same
bytes, verify sees no fields, ink ratio 1.00, and "no untranslated running
text" is vacuously true. The user is handed a file described as translated
that is the original. `extract_segments.py` and `verify.py` now **fail**
when a page has an image or visible ink but no extractable text.

The OCR'd version of that scan is not better. An OCR layer is invisible
text (render mode 3) laid over the image so the pixels become searchable.
Extract sees text, strip removes it, retypeset prints the translation over
the scanned pixels, the ink ratio stays under the 3× ceiling, and the reader
gets both languages on top of each other. Both scripts now compare a render
of the page with and without its text: if stripping the text changes almost
nothing (under 3% of the text-span area), the text is invisible and the page
is refused. This pipeline has no masking mode; say so instead of shipping.

A related false failure: a pale or blank page has ~0 dark pixels, so
`ratio = translated / max(original, 1)` becomes 0.00 and fails a correct
file. Verify skips the ink ratio when the original has negligible ink.

## 10. Text hiding in nested XObjects and inherited resources

Letterheads, imposed pages and anything built with `show_pdf_page` put
text inside a Form XObject inside another Form XObject; some producers
put the page `/Resources` on the `/Pages` node instead of the page. A
walker that reads the page's own resources one level deep strips
nothing there and reports `form_xobjects_stripped: []`. MuPDF still
extracts that text, so retypeset draws the translation on top of the
surviving source and every structural gate stays green. `strip_text.py`
now recurses through XObject resources, follows `/Parent` inheritance,
and re-reads the stripped file with annotation appearances excluded:
any page text left is a FAIL, the message lists page and text, and the
stripped file is not written. Do not work around that FAIL by hand; it
means the walker has a blind spot worth a fixture.

## 11. Complex scripts drawn without shaping

`TextWriter` places glyphs one by one. Arabic drawn that way is a row of
isolated letterforms; Devanagari shows consonant + halant where a conjunct
belongs. The placement gate still PASSes because it reads the logical
string from `/ActualText`, and the ink ratio barely moves. Runs whose
target script needs shaping now go through the Story engine (the merges
path), and `verify.py` FAILs an output whose Arabic letters are all
isolated forms. Indic scripts leave no code-point signal in the text
layer (the shaper writes glyph ids), so the gate there is *who drew the
run*: every Story-engine run is marked with `/ActualText`, and a
shaping-script target that no `/ActualText` span carries was drawn glyph
by glyph. Dot leaders and the `$` tail are refilled after a shaped or
right-to-left label; they used to be dropped with the whole leader path.

## 12. Widget text is invisible to strip-and-retypeset — twice over

`/TU` tooltips, choice `/Opt` labels and text-field `/V` / `/DV` defaults
live in annotation dictionaries, never in a content stream. Two failures
follow, and both are silent.

*Leaking in*: `get_text()` renders widget appearance streams, so a text
field's default value and a combo box's current selection arrive as page
text. The author translates them, retypeset draws the translation on the
page, and the widget keeps drawing the source value on top — two strings,
one of them wrong, in the same rectangle. `extract_segments.py` now reads
page text from `page.get_displaylist(annots=False)`, so they never become
cores.

*Never coming out*: nothing else in the pipeline can reach them, so a
"fully translated" form still hovers and drops down in the source
language. `extract_segments.py` writes `widget_text.json`; author each
`target` and pass it to `strip_text.py --widget-text`.

The trap inside the fix is the **export value**. An `/Opt` entry may be a
bare string (export and display are the same) or `[export, display]`.
Translate the string and you have silently changed what the form submits
and what `/V` must match — the dropdown looks right and the data is
broken. The channel always writes `[export, display]` pairs and refuses a
spec that touches a choice field's `/V`; `verify.py` compares export
values against the original and FAILs any drift.

One thing to expect on the visual pass: **MuPDF's own appearance generator
draws a choice field's `/V` verbatim**, so a render made with PyMuPDF shows
the *export* value ("First") where a conforming viewer shows the translated
display half ("Primero"). The file is right; the preview renderer is
simple. Do not "fix" it by translating the export — that is the failure this
whole section is about. Check a dropdown in a real viewer instead.

## 13. Rotated lines re-typeset flat

A rotated *line* was re-typeset flat: the extractor kept origin, bbox and
size but not direction, so a 90-degree "FOR OFFICE USE ONLY" side stamp was
re-drawn horizontally across the middle of the form. No gate moved: the
string was placed, the ink ratio barely changed, and the text layer read
correctly. Only the render showed it. Segments now carry the line's
direction vector and retypeset morphs each rotated run about its own origin.

A rotated *page* (`/Rotate` 90, 180 or 270) went wrong differently, from
v17 to v63.
- **Why.** Extract read text through an annotation-free display list, to
  keep widget values out. A display list reports what a viewer shows, so
  segment geometry came back in the rotated space. Retypeset, widget rects,
  `get_text` and every verify reader use the unrotated space.
- **What it did.** On a /Rotate 90 page every run went off the page: a
  blank page, which verify catches (ink 0.00, missing targets). At 270 most
  runs landed turned or upside down. At 180 every run was point-reflected
  onto the opposite corner, on the page, and retypeset and verify both exit
  0 when the page has no other defect. No verify gate reads positions.
- **Now.** Extract maps the text page back to the unrotated space, where
  `segments.json` equals `page.get_text('dict')`. Its `geometry` key names
  that space and lists each rotated page. Width budgets and the RTL mirror
  use the unrotated page frame, not the rotated `page.rect`.
- **Refusal.** A `segments.json` with no `geometry` key was extracted by
  v63 or earlier. When one of its rotated pages carries segments, retypeset
  refuses it with this stable line, which consumers may match:
  `FAIL: stale extraction: segments.json names no geometry space and N
  rotated page(s) carry segments (pP /Rotate R, …); it was extracted before
  v64 in the rotated space: run extract again.`
- **Still degraded: landscape pages.** On these, the content is
  counter-rotated so it reads upright under `/Rotate`. Their text is
  vertical in PDF space, so every run takes the rotated-run path
  (`retypeset.md`, Rotated lines): each lands at its source origin, but
  leaders, `right`, `center`, merges, override `x` and inline markup are
  horizontal-only there.

## 14. The text layer reports characters nobody wrote

MuPDF builds an embedded font's `/ToUnicode` by reverse-mapping the font's
cmap. When several code points share one glyph it can pick the wrong one:
Arial's space comes back as NBSP (U+00A0) and its hyphen as a soft hyphen
(U+00AD); with full Noto Sans JP, common kanji come back as CJK
Compatibility Ideographs (立 as U+F9F7, 年 as U+F98E). The glyphs are
right, so nothing looks wrong — but the words cannot be searched, cannot
be copied, and a string gate comparing against the authored text fails a
correct translation. Subsetting hid it; `field_fonts.py` embeds a full
font, so it was always one delivery away.

After saving, `retypeset.py` rewrites `/ToUnicode` for the glyphs it
placed to the code points you authored (a CMap is executed in order, so an
appended `bfchar` block overrides an earlier `bfrange`). Where two authored
characters share a glyph the lower code point wins — in every drift pair
the canonical character is the lower one. A ligature glyph is nobody's
character, so it is read from the font's GSUB table and mapped to its
components: without that, the Story engine's `fi` puts U+FB01 (or U+007F
in a subset) where you wrote "oficina". `verify.py` then FAILs any
drift-prone character that is in neither the original nor the mapping, and
the placement gate compares verbatim instead of folding.

## Also worth knowing

- Extraction geometry must come from the ORIGINAL (text intact); writing
  targets the STRIPPED file. Keep both; never extract from the stripped one.
- Insert at the baseline origin from the text dict, not the bbox top —
  bbox-top insertion sits text visibly low.
- **A span's bbox is font metadata, not ink.** Noto Naskh Arabic's
  connecting tails reach left of the glyph origin, so MuPDF reports a box
  starting ~11 pt right of where the letters actually are at 12 pt; Arial
  reports one that matches. Placement is correct in both cases. Judge
  placement by the render, not by comparing bboxes — and treat width
  budgets derived from a source bbox as approximate on Naskh-like faces.
- Fields' `/DA` default appearance references a Latin font; typed-in
  target-script text falls back or vanishes in some viewers until
  `field_fonts.py` rewires it. Values still store; the *rendering* is what
  breaks — easy to miss if you only test with ASCII.
- Tagged PDFs: stripping text orphans `/StructTreeRoot`. `retypeset.py`
  removes it and sets `/MarkInfo /Marked false` rather than leaving tags
  pointing at deleted text; tell the user the file is no longer tagged.
