# /Lang keeps the whole language tag — 25 September 2026

**Assignment.** Canary run 4 found the defect, and it was filed as a proposal
on 25 September. The product called it a quick win, and Rodrigo assigned it
in this session. It ships as v80, stacked on #50 (v79).

## The defect, reproduced

Retypeset set `/Lang` with PyMuPDF's `set_language`. On PyMuPDF 1.28.2 that
stores only part of many tags:

| mapping `lang` | stored `/Lang` |
|---|---|
| `es-US`, `es-419` | `es` |
| `pt-BR` | `pt` |
| `en-GB` | `en` |
| `zh-Hant-TW` | `zh` |
| `sr-Latn-RS` | `sr` |
| `de-CH-1996` | `de` |
| `zh-Hans`, `ja` | kept whole |
| `Japanese` (not a tag) | `jap` |

Retypeset's console still said `/Lang -> es-US`, and XMP's `dc:language`
got the whole tag, so the file contradicted itself.

**Reading is cut too.** `doc.language` shortens a whole stored tag the same
way: `zh-Hant-TW` reads as `zh`, `es-US` as `es`. Two consequences, both
reproduced on the v79 tree:
- **A typography build for any region tag failed its own verify.** For
  `en-US`, the metadata gate said "expected en-US; output declares en".
  The typography comparison is exact, so no region tag could pass.
- **Han-forms read `zh-Hant-TW` as Simplified.** With no mapping `lang`,
  the gate takes its convention from the output's `/Lang`, and `zh` is SC.

## What changed

`pdf_translate/_lang.py`, shared the way `_pixels.py` is:
- `write_language(doc, tag)` sets the catalog's `/Lang` to the tag as
  given, and returns what the file now holds.
- `declared_language(doc)` reads the stored string. An indirect `/Lang`,
  which nothing here writes, falls back to PyMuPDF's reading.

**Who uses it:**
- **`retypeset.apply_document_metadata`,** on both the legacy and the
  typography paths: it writes with `write_language`, and its report, which
  the console line prints, is the value read back.
- **Verify's three readers:** the legacy and typography metadata checks,
  and han-forms' output tag.

**Unchanged:**
- **The legacy comparison.** An output whose `/Lang` starts the mapping's
  tag still passes, so outputs written before v80, such as `es` for an
  `es-US` mapping, still verify.
- **Region-less tags.** For 20 of them (`es`, `ja`, `zh-Hans`, `ko`, `de`,
  `fr`, `ar`, `hi`, `ru`, `it`, `pt`, `vi`, `th`, `he`, `tr`, `pl`, `en`,
  `nl`, `uk`, `id`), the old and new writes give byte-identical files on
  `corpus/choice_fields.pdf`. The app's 16 tags carry no region.
- **Extract's record of the source `/Lang`** still goes through
  `doc.language`. It is on the app's route and outside this request, so it
  is raised with the app, not changed.

**Docs:**
- `references/retypeset.md`;
- `references/gates.md`, which says how `/Lang` is read and compared;
- `references/translations-format.md`.

## Red, then green

`tests/test_lang_tag.py` has 6 tests; every one fails on `c148b73` (v79):
1. **The request's acceptance.** A legacy build with `lang` `es-US` stores
   `es-US`, and the console says `/Lang -> es-US`.
2. **Nine tags and a display name** are stored as given, and the report
   matches.
3. **The legacy gate:**
   - it passes `es-US`, and the old `es`;
   - it fails `fr-CA`, naming `fr-CA`, not `fr`.
4. **Han-forms** receives `zh-Hant-TW` from a `zh-Hant-TW` output.
5. **A typography build for `en-US`** stores it, and its metadata gate
   passes.
6. **The same build relabelled `en-GB`** fails, naming `en-GB`.

## Suite

CI's commands on macOS, on this change:
- **Suite:** 780 tests (774 on v79, plus these 6), with 0 ResourceWarnings.
  The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is item 3's expected failure.
- **Canary, repository tests and eval fixtures:** all exit 0.

Rule 1 does not apply: nothing here renders, shapes, lays out or touches a
font. Han-forms' verdict can change only through the tag it is given, and
test 4 pins that.
