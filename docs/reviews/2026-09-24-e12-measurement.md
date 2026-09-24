# E12 measurement — 24 September 2026

**Question.** Can E12 (a compact, deterministic output save; row E12 in
`docs/REQUESTS-from-product.md`) be built as written on this code, and is
the unfixed shape red on acceptance checks 1 and 2 first?

**Answer.** Checks 3, 4 and 5 are buildable, with guards the measurement
names. Check 2 is buildable for page text but is contradicted on every
delivered form by the standing full field face. Check 1 cannot hold on the
corpus's three base-14 fixtures without degrading the embedded face. Checks
1 and 2 are red on the unfixed shape only on constructed multi-page
documents, because every corpus fixture is one page. E12 is blocked on the
product's rulings below; nothing has been built.

## How this was measured

- On `main` at `0542dc2`, whose `pdf-translate/` tree is `221a86f`'s (v61).
  Python 3.14.6, PyMuPDF 1.28.2, pikepdf 10.12.0 and fontTools 4.64.0, on
  macOS.
- The shipped stages were driven by import: `run_strip`, `run_extract`,
  `run_prepare_font` and `run_retypeset`. No library code was copied and
  nothing in the repository changed.
- Four agents measured independently: the save and font-embedding paths,
  PyMuPDF capabilities, the unfixed shape against the best case, and forms
  and determinism. A fifth re-ran the claims that decide E12 with its own
  scripts. The lead session re-checked the `rotated.pdf` claim by hand.
- Pixels were compared by MuPDF 1.28.2 renders only. The raw evidence
  (5,700 files, 909 MB, every script with its log) is in the ignored
  `runs/2026-09-24-e12-measurement/` on the Mac that ran it. The files
  cited below as `critic/…` live there.

## What the save and font paths do today

- **One save per stage.** `retypeset` saves with `ez_save` defaults:
  garbage 3, deflate and object streams (`retypeset.py:2019`). Its last
  writer is the pikepdf save in `canonicalize_text_layer`
  (`retypeset.py:679`). `field_fonts` saves with PyMuPDF defaults and then
  pikepdf (`field_fonts.py:66`, `:130`).
- **Glyph ids differ per subset.** `prepare_font` subsets with pyftsubset
  without `--retain-gids`, so every subset renumbers its glyphs. `ó` is
  glyph 181 in the full face and 103, absent and 105 in three per-page
  subsets.
- **How a face is embedded.** TextWriter embeds a face once per document.
  The Story engine (`insert_htmlbox`) embeds one identical copy per call:
  one page with three inline-bold lines carries 4 programs, 1 distinct.
- **The field face.** `field_fonts` embeds the full field face, 3,884
  glyphs and 621,572 B decoded, on purpose (`field_fonts.py:11-12`). It
  does this even when the document has no `/AcroForm`: `pipeline.py:673`
  calls it unconditionally.
- **Source faces stay.** `strip_text` never removes the source's font
  resources, so faces that nothing draws any more stay in the output.

## Acceptance checks

**Check 1 — output ≤ 2.5× input.** The input is the original source PDF.

| document | pages | input B | unfixed B (×) | best case B (×) |
|---|---:|---:|---:|---:|
| M5: colored, dense_table, expansion, multicolumn, rtl_source | 5 | 69,464 | 486,712 (7.01×) | 95,908 (1.38×) |
| M4: dense_table, xobject_text, rotated, encrypted | 4 | 96,418 | 359,158 (3.73×) | 95,083 (0.99×) |
| M3: the two small forms plus rotated_text | 3 | 4,466 | 55,139 (12.35×) | 21,329 (4.78×) |
| M13: all 13 translate fixtures | 13 | 2,380,195 | 3,125,741 (1.31×) | 2,380,959 (1.00×) |
| rotated_text.pdf | 1 | 1,700 | 18,157 (10.68×) | see below |
| choice_fields.pdf | 1 | 2,305 | 18,606 (8.07×) | see below |
| nested_xobject.pdf | 1 | 2,774 | 19,144 (6.90×) | see below |

- The other ten one-page fixtures are at most 1.95× even in the unfixed
  shape (xobject_text).
- The unfixed shape builds each page as a separate part (its own
  `prepare_font` subset and retypeset), assembles the parts with
  `insert_pdf` and saves with defaults. The best case uses one subset for
  the whole document and a compact save.
- The three base-14 inputs embed no font. The smallest any existing
  primitive reaches is 4.369× on rotated_text, using `subset_fonts`, garbage
  4, `clean`, and `compression_effort=100` (`critic/exp2_floor.py`).
- Only font surgery that also drops TrueType hinting gets under the line:
  3,679 B, 2.164×. That output renders identically under MuPDF's default
  anti-aliasing but differs with anti-aliasing off (0.000564 at zoom 2), so
  **check 1 and a strict check 3 cannot both hold on it**.

**Check 2 — one embedded program per face.**

- **Buildable for page text.** With one subset for the whole document,
  garbage 4 leaves exactly one program per face at pixel diff 0.0.
  `ez_save`'s garbage 3 keeps the identical copies.
- **Per-part subsets.** No save setting and no `subset_fonts` merges
  subsets made separately for each part. Pointing every page at one of them
  changes pixels (up to 2.24e-04). A merge pass that unions the embedded
  programs and writes a `/CIDToGIDMap` does reach one program at pixel diff
  0.0, with the text unchanged. It is prototyped for TrueType faces only,
  not CFF (`critic/exp1_parts.py`).
- **Red on every delivered form.** `final.pdf` carries the page subset and
  the full field face: 2 programs per face, still 2 after any save.
  Collapsing them contradicts the standing decision to embed full faces for
  typing.

**Check 3 — pixel diff 0.0.** It holds for garbage 4, `clean` and the
union merge. It does not protect the gates:

- MuPDF's `subset_fonts` turns conjunct-shaping (Hindi) and han-forms
  (Japanese) from PASS to REVIEW with pixels unchanged.
- It also cuts the `/DR` field face to 5 glyphs with no cmap once an
  appearance stream draws with it.

So a pixel check alone would pass a save that breaks typing into a form.

**Check 4 — fields preserved.** Field count, names and values stay equal in
PyMuPDF's view, but that view misses one hazard:

- Garbage 4 folds identical widgets that have no `/P` into one object
  shared by every page. Moving the page-3 widget then moved it on all three
  pages.
- The shipped pipeline's widgets carry no `/P`.
- The check needs a count of unique widget objects per page, and the save
  needs a guard (`critic/exp6_widgets.py`).

**Check 5 — byte-identical for one `doc_id`.**

- **Buildable.** Write `doc_id` into both `/ID` elements through a
  `tobytes(no_new_id=1)` round trip, `xref_set_key`, then
  `save(no_new_id=1)`. Two fresh processes then give equal sha256.
- **An xref-stream trap.** Setting the key directly on an xref-stream file
  is silently ignored.
- **Without a `doc_id`.** The save inherits the input's `/ID`.
- **Where runs differ.** Today's per-run variation is `/ID[1]` from the
  pikepdf save at `retypeset.py:679`, not from `ez_save` as
  `docs/BRIEF-determinism.md` inferred.

**Check 6 — red first.** Every corpus fixture is one page, so "per-page
parts" is a single part there:

- **Check 2** is red on the corpus only on ar_source: 3 identical Story
  copies of Noto Naskh Arabic plus 3 of the source's Arial. Garbage 4
  clears it.
- **Check 1** is red only on the three base-14 fixtures, which stay red.
- **The red-to-green demonstration** needs constructed multi-page fixtures
  whose sources embed fonts: M5 goes from 7.01× with 5 programs per face to
  1.38× with 1.

## Questions only the product can settle

1. **Check 1's denominator and exemptions.** Is the ratio against the
   original source PDF? Are inputs that embed no font, such as the base-14
   fixtures, exempt? May the save drop TrueType hinting or font tables to
   meet the ratio?
2. **Fixtures for checks 1, 2 and 6.** May they use constructed multi-page
   fixtures in `corpus/`, whose sources embed fonts?
3. **"Subset once for the whole document."** Does it mean callers prepare
   one subset per face before building parts, with the save then removing
   byte-identical copies? Or must the save merge subsets made separately for
   each part, as the union pass does (TrueType only)?
4. **The field face.** Is the full field face in `/AcroForm /DR` exempt
   from "exactly one program per face" and from subsetting?
5. **Verify verdicts.** Must the save keep every verify verdict, so that no
   conjunct-shaping or han-forms PASS becomes REVIEW? That rules out
   MuPDF's `subset_fonts` as a blanket step.
6. **Undrawn source faces.** Are they "unused objects" the save should
   drop? They are 80–99% of the bytes on fixtures whose sources embed fonts
   (ja_source 1,707,058 → 6,750 B with `clean`, pixel diff 0.0, no verdict
   changed on the three jobs checked).

## Found on the way, outside E12 and unassigned

- **`field_fonts` on a document with no form.** It still embeds the full
  field face: colored's delivery grows from 93,386 to 434,242 B
  (`pipeline.py:673`).
- **`corpus/rotated.pdf` (`/Rotate 90`).** A rebuild with a Spanish-like
  mapping draws its three runs where nothing shows: the output page has no
  ink and no extractable text. Verify FAILs page ink ratio 0.00 and missing
  translation targets (3) and exits 1, so it is caught, not silent.
  Re-checked by hand on 24 September.
- **Split widgets.** When a caller splits parts from one source document it
  keeps open, `insert_pdf` copies widgets only on the first insertion; later
  parts silently lose their fields. That is PyMuPDF behaviour, and a hazard
  for a consumer that builds from per-page parts.
