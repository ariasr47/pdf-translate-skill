# Objective: fail strip when any page text survives, however deep it hides

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md` step 2, `scripts/strip_text.py`, then
> `corpus/verdicts.json`. Do not implement OCR, a glossary, RTL shaping,
> widget-text extraction (`/TU`, `/Opt`), or the leak-scan rewrite —
> those are separate rows. Not FL-150.

---

## 1. Compass (not done)

`strip_text.py` walks the page's own `/Resources /XObject` one level
deep. Text inside a Form XObject nested in another Form XObject, or on a
page whose `/Resources` are inherited from the `/Pages` node, survives
strip while the report says `form_xobjects_stripped: []`. MuPDF extracts
that text anyway, so retypeset draws the translation on top of the
surviving source. No gate looks at the stripped file. This session makes
"page text survived strip" a **FAIL** and closes the two walker blind
spots.

## 2. Done when — closed bar

1. **Gate.** After saving, `strip_text.py` re-reads the stripped file with
   annotation appearances excluded (`page.get_displaylist(annots=False)`).
   Any page with non-blank text → exit non-zero, **list page + text**, and
   the stripped file is **not left on disk** (same rule as retypeset on
   overflow). Widget captions and field values are appearance streams,
   not page text; they never trip the gate.
2. **Walker.** Form XObjects are stripped recursively (visited set) and
   `/Resources` are resolved through `/Parent` inheritance. The report
   records `depth` per stripped XObject.
3. **Constructed, not FL-150.** One page: body text + a Form XObject that
   contains text and a second Form XObject with text; a variant with the
   page `/Resources` moved to `/Pages`. Both strip clean; the text field
   and the vector rule survive. A simulated blind spot (patched
   `strip_ops` that keeps everything) → rc 1, FAIL names the text, no
   file. `pipeline.py init` returns non-zero the same way.
4. **Corpus.** `corpus/nested_xobject.pdf` with verdict `translate`. The
   corpus harness also strips every `translate` PDF and asserts no
   leftover text.
5. **No regressions.** unittest + corpus green. Field identity, caption
   rewrite, XFA removal, q/Q wrapping unchanged. The gate always runs;
   there is no flag to skip it.
6. **Docs.** `SKILL.md` step 2: strip fails and writes nothing on leftover
   text. `failure-modes.md`: the nested / inherited class.

## 3. Not done when

- Stripping annotation appearance streams (widgets are not page text)
- Extracting or translating widget text (`/TU`, `/Opt`, `/V`)
- Pattern, Type3 or optional-content special cases without a fixture
- A `--force` / `--allow-leftover` escape hatch

## 4. Method

Tiny constructed PDFs (`show_pdf_page` twice for two-level nesting — note
PyMuPDF wraps each shown page in two XObject levels; PyMuPDF xref surgery
moves `/Resources` to `/Pages`, because pikepdf pushes inherited
attributes back onto the page whenever it saves). Import shipped
`strip_text`.
The oracle is independent of the walker: MuPDF text extraction of the
*stripped* file, not the pikepdf walker's own bookkeeping.

## 5. Invariants

Field identity, no redaction, graphics untouched, provider-neutral.

## 6. Proof

In-repo tests: nested, inherited, widget text ignored, refuse-and-no-save,
pipeline init. Corpus row + strip-clean assertion. Full unittest + corpus.
