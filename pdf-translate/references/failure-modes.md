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
strips `BT..ET` blocks from content streams instead: widgets are
annotations, not page content, so a content-stream edit cannot touch them.

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
a header centered on the wrong midpoint, a paragraph that re-wrapped one
line taller and now kisses the rule below it, two segments overlapping by a
few points. Render every page beside the original and look. This is not
optional polish — in practice it is where half the defects surface, and it
is the difference between "plausible" and "indistinguishable".

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

## Also worth knowing

- Extraction geometry must come from the ORIGINAL (text intact); writing
  targets the STRIPPED file. Keep both; never extract from the stripped one.
- Insert at the baseline origin from the text dict, not the bbox top —
  bbox-top insertion sits text visibly low.
- Fields' `/DA` default appearance references a Latin font; typed-in
  target-script text falls back or vanishes in some viewers until
  `field_fonts.py` rewires it. Values still store; the *rendering* is what
  breaks — easy to miss if you only test with ASCII.
- Tagged PDFs: stripping text orphans `/StructTreeRoot`. Check for it and
  tell the user accessibility metadata was lost if present.
