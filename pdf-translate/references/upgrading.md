# Upgrading — what a Python consumer sees change, version by version

Contents: how to read this · before you switch · by stage (packaging and
import; results, refusals and logging; extract; strip and widget text;
retypeset; prepare_font; field_fonts; verify; review, qa and the CLIs;
capture) · what moves output bytes · the product's checklist · a known issue,
fixed in v83 · later versions.

This is for a consumer that calls the library from Python —
`run_extract` / `extract_segments`, `run_strip` / `strip_text`,
`widget_text_scaffold`, `run_retypeset` / `retypeset`, `run_prepare_font`,
`run_field_fonts`, `run_verify` — pinned to an exact version. It covers
**v54 (`9675c61`) to v81 (`0d58202`)** and grows: every later version adds
its section under [Later versions](#later-versions).

## How to read this

- **Version** is the first version number a change shipped in. A few
  changes landed on `main` under a number that was already out; where the
  first number that *guarantees* the change is later, it says so ("v56,
  guaranteed from v57"). Moving from v54 to v81 includes all of them.
- **Bytes** says whether the change moves output bytes: **yes** for every
  job, **when** for some jobs (named), **no** when outputs are identical.
  JSON reports carry the library version, so their `version` field changes
  at every release whatever else does (see *Results, refusals and
  logging*).
- **What to do** is empty when nothing is needed.
- Each entry was checked against the code at `0d58202` or its version's
  evidence (`docs/reviews/`), and an independent pass tried to refute each
  one. The console is not an API; console lines are mentioned only where a
  document promised them.

## Before you switch

1. **Python 3.14.** `requires-python` is `>=3.14` (v58, guaranteed from
   v59). Nothing checks it at runtime; pip refuses older interpreters.
2. **Building from source needs `setuptools>=77`** (v73). Isolated builds
   fetch it; with `--no-build-isolation` or build constraints, install it
   first. The wheel's licence field is now `License-Expression: MIT`.
3. **Read `scale_report.json` as an envelope:** `{"schema", "version",
   "runs": [...]}` (v58). Take `data['runs']`. Accept both shapes if you
   read reports from mixed versions.
4. **Catch `PdfTranslateError`**, or its subclasses, around every `run_*`
   (v58). Branch on the type, `exc.refusals` and `exc.reason` — never on
   console text. Refusal items of kind `stale_extraction` and
   `output_aliases` carry no `core` key. A missing dependency raises one
   `ImportError` naming every package (v59, guaranteed from v60), not the
   first `ModuleNotFoundError`.
5. **Decide what the library's log does in your process.** Output goes
   through the `pdf_translate` logger (v58), which also propagates to the
   root logger. If your service configures root logging, set
   `logging.getLogger('pdf_translate').propagate = False` or give it its
   own handler.
6. **Keep capture off unless you want it.** Capture writes copies of
   source documents to disk (v60). It is off by default and follows
   `PDF_TRANSLATE_CAPTURE_DIR` when `capture_dir` is `None`; an explicit
   `capture_dir=""` keeps it off even when the variable is set.
7. **Regenerate `widget_text.json`** with v62 or later and key entries by
   fully qualified field name. A partial key still works when it names
   exactly one field; otherwise strip raises `WidgetTextError`.
8. **Re-extract rotated documents.** A `segments.json` made before v64 for a
   document with `/Rotate` pages is refused (`MappingError`,
   `refusals['stale_extraction']`). Re-measure any `x`, merge `box` or
   notice `box` authored on a rotated page: geometry is now in the page's
   unrotated space.
9. **Never pass an output path that names an input** (v66): the build
   refuses before writing (`refusals['output_aliases']`).
10. **Write literal characters, not HTML entities,** in single-line
    targets that carry inline tags, in notices and in shaped-script runs
    (v66). Merges' `html` is unchanged.
11. **Stop reading `<out>.instanced.ttf` and `<out>.chars.txt`** from
    `prepare_font` (v78); they are no longer written. For a field face,
    pass the variable face to `field_fonts`. `prepare_font` needs a
    writable temp directory.
12. **Give `field_fonts` a single-face `.ttf`/`.otf`, not a `.ttc`** (v68),
    and expect `FileNotFoundError` or a fontTools error, not a
    `PdfTranslateError`, for a bad font path.
13. **Regenerate byte and verdict goldens.** See [What moves output
    bytes](#what-moves-output-bytes).

## By stage

### Packaging and import

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 58 (guaranteed from 59) | `requires-python` goes from `>=3.10` to `>=3.14`. Not enforced at runtime. | no | Run on 3.14. |
| 59 (guaranteed from 60) | `import pdf_translate` checks for pymupdf, pikepdf and fontTools first and raises one `ImportError` naming every missing one, with an install line for the running interpreter. The scripts print it and exit 2. | no | Catch `ImportError`, not `ModuleNotFoundError`. |
| 73 | Build requirement `setuptools>=61` → `>=77`; `license = "MIT"` with `license-files` (PEP 639). Runtime dependencies are unchanged: `pymupdf>=1.24,<1.30`, `pikepdf>=8.0,<11`, `fonttools>=4.40,<5`. | no | See *Before you switch* 2. |
| 74 | `verify.load_segments_for` is removed (it was never exported). | no | Use `verify.load_segments_file(...)['segments']`. |

### Results, refusals and logging

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 55 | `__version__` changes at every release from here on (`'54'` → `'81'`). `VerifyVerdict.to_dict()` already carried it at v54; results, `PdfTranslateError.to_dict()` and `scale_report.json` carry it from v58, `ReviewVerdict` from v57, capture bundles from v60. | when: every JSON that carries `version` | Mask or update `version` in goldens. |
| 58 | Silent `run_*` twins return frozen, schema-versioned results (`to_dict()` → `{'schema': 1, 'version', …}`); collection fields are tuples. `run_extract(src, outdir, *, gap=12.0, pages=None)` requires `outdir`. The bare functions keep their signatures, printed output and return codes. | no | Optional: move to `run_*`. |
| 58 | Typed refusals: `PdfTranslateError` with `message`, `console_line`, `exit_code`, `refusals` (untruncated) and `to_dict()`. Subclasses `MappingError`, `GlyphError`, `PlacementError`, `FontError`, `WidgetTextError` (now a subclass; `except WidgetTextError` still works). `run_prepare_font` raises `FontError` with `reason` `fstype`, `no-pyftsubset`, `no-raster`, `no-conjuncts` or `wrong-han-convention`. | no | Catch `PdfTranslateError`. |
| 58 | A legacy build refuses in a fixed order and stops at the first refusal: `output_aliases` (v66), `stale_extraction` (v64), `merges`, then `untranslated` / `unauthored_merges` (all `MappingError`); `notices` (`PlacementError`); after drawing, a glyph miss raises `GlyphError`, else overflow or a rotated shaped run raises `PlacementError`. The post-draw refusals always carry `untranslated`, `overflow`, `glyph_misses` and `rotated_shaped`. The full table is in `references/retypeset.md`, "Every way a build fails". From v59 a mapping that cannot be read refuses before all of these. | no | Catch `GlyphError` before `PlacementError`, or catch `PdfTranslateError`. |
| 58 | Everything goes through `logging`. The loud functions print the same bytes to stdout, and the same records also reach the root logger; the `pdf_translate` logger is set to INFO on the first loud call and stays there. `compare()` and `render_pages()` no longer print when called directly. `run_verify` no longer redirects stdout, so other threads keep theirs. | no | See *Before you switch* 5. Read return values, not stdout. |
| 58 | `run_retypeset` gains `progress(done, total)`, `cancel()` (returns `RetypesetResult(cancelled=True, output=None)` and saves nothing), `scale_report=` (`None` writes none) and `resource_root=`. Authored HTML resolves its resources against the mapping's directory, not the process's working directory, in `retypeset()` too. | when: merge or notice HTML with relative resources, run from another directory | Keep such resources beside `translations.json`, or pass `resource_root`. |
| 59 (guaranteed from 60) | A refusal list cut at 30 entries ends `… N more not shown` and a total line (`console_line` only; `refusals` hold everything). The `notices` list is still cut at 30 without the marker. | no | Count `exc.refusals`, not console lines. |
| 59 | Every stage reads `translations.json` through one loader (UTF-8 with or without BOM). An unreadable file, a missing file, a non-object root or a `format` other than `typography-1` raises `MappingError` (refusals under `typography`, even for a legacy mapping) instead of `JSONDecodeError` or `FileNotFoundError`. The loud `retypeset()` and `prepare_font()` return 1 instead of a traceback. | no | Catch `MappingError`. Do not put a `format` key in a legacy mapping. |
| 59 | Opt-in `typography-1` mapping format, announced by `pdf_translate.MAPPING_FORMATS`. New keyword-only parameters: `typography=` (extract, verify), `font_class=` / `font_role=` (prepare_font), `original=` (retypeset). Legacy calls are unchanged; `to_dict()` leaves out `typography` when it is `None`. | when: typography-1 jobs only | None unless you adopt it (`references/typography.md`). |

### extract

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 62 | `widget_text.json` keys are fully qualified field names, one entry per field (see *strip and widget text*). | when: forms with nested fields | Regenerate the scaffold. |
| 64 | Geometry is in the page's **unrotated** space. `segments.json` gains a top-level `geometry` key on every extraction: `{"space": "unrotated", "rotated_pages": {...}}`. On `/Rotate` pages every `origin`, `bbox` and `dir` changes; warnings computed from geometry can now appear there. `ExtractResult` has no `geometry` attribute. | yes: `segments.json` on every extraction; coordinates on rotated pages | Allow the new key; map rotated-page geometry through `page.rotation_matrix` to draw over a render. |
| 77 | Faster: the invisible-text oracle judges only the pages asked for. `strip_text.invisible_text_pages(src, pages=None)` gains `pages=`. Extract's verdicts are unchanged (it already filtered to its pages). | no | — |
| 79 | Extract no longer writes a fresh scaffold over a `widget_text.json` that holds authored text (a non-null target, a string shorthand, or a file that is not JSON). `ExtractResult.widget_text_kept` (new; between `widget_text_path` and `typography`) and the dict key `widget_text_kept` say so. An all-null file is still refreshed. | when: an authored `widget_text.json` in the output directory | Update `to_dict()` goldens for the new key. |

`segments.json`'s `document.lang` still records the source's `/Lang` as
PyMuPDF shortens it (`en` for `en-US`).

### strip and widget text

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 62 | Widget text by **fully qualified field name** (every `/T` up the `/Parent` chain, joined with dots). A full-name key applies to that field only; a partial key applies only when it names exactly one field; a partial key naming several fields, two keys for one field, or one entry for widgets that share a name but not their text raise `WidgetTextError`. `choice_exports` keys by full name, `'<name> (widget n)'` for a repeated widget. Captions and `hide_buttons` still take partial names. | when: forms whose partial names collide — no more cross-field tooltips or values | Regenerate `widget_text.json`; key by full name. |
| 63 | Strip keeps the graphics state set inside text objects: inside `BT…ET` it drops only the text operators (`Tj TJ ' " Td TD Tm T* Tc Tw Tz TL Tf Tr Ts`) and `BT`/`ET`; colour, `gs`, `w`, `q`/`Q`, `cm` and marked content stay in order. Clip-mode text (`Tr` 4–7) is still dropped whole. | when: any text object carrying non-text operators (27 of 33 corpus files; visible pixels changed on 18 pages of 5) | Regenerate stripped and final PDF goldens. |

### retypeset

These are the legacy path unless marked.

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 56 | The canonical `/ToUnicode` also maps single-substitution alternates an authored character can reach (`locl` digits, vertical forms, stylistic sets) back to that character, so `FL-150` no longer reads back as `FL-Ɍɐɋ`. | when: a placed face has such lookups — both Noto faces tested, Latin and Japanese, do | Regenerate PDF goldens. |
| 56 (guaranteed from 57) | A merge's reported scale is source-relative and includes the 0.98 fit allowance, so every merge appears in `scaled` / `scale_report.json` at about 0.98, and a merge whose engine factor sits just above 0.7 can now fall under the 0.7 floor (overflow). Drawing is unchanged. | when: jobs with merges — `scale_report.json`, not the PDF | Add `allow_scale` for merges near the floor. |
| 64 | `/Rotate` pages build in place: width budgets, the right-to-left mirror and link rects use the unrotated frame. A v63 build of a rotated page drew its runs off the page. A `segments.json` from before v64 on a rotated document is refused: `MappingError`, `refusals['stale_extraction']` (items carry `page` and `rotation`, no `core`). Its console line is documented as stable in `references/failure-modes.md`. | when: documents with `/Rotate` pages | Re-extract; rebuild rotated outputs made before v64. |
| 65 | No 4 pt floor on shrink-to-fit: small print is drawn at the size that fits, and the 0.7× gate sees the true ratio. A 5 pt run needing 0.54× used to report 0.8× and pass; it is now refused (overflow) unless `allow_scale` names it. Sub-4 pt sources are drawn smaller, not larger, and appear in the scale report. | when: runs that were lifted to 4 pt (33 runs on 10 wild PDFs) | Expect new `PlacementError`s on small print; add `allow_scale` where the size is acceptable. |
| 66 | A build whose output or scale-report path names one of its inputs (stripped PDF, `segments.json`, the mapping, `original`, a font) raises `MappingError`, `refusals['output_aliases']`, before reading or writing anything. v63 overwrote the mapping. | no | See *Before you switch* 9. |
| 66 | Text handed to the Story engine is escaped so it lands as written: `&`, `<` and `>` in single-line targets with inline tags (`<b>`, `<i>`, `<strong>`, `<em>`), in notices and in shaped runs. `&copy;` stays `&copy;`; `<u@e.co>` stays. | when: those targets containing `&`, `<` or `>` | See *Before you switch* 10. |
| 67 | The canonical text layer covers the italic and bold-italic faces too (it covered regular and bold). Italic cuts whose space and NBSP share a glyph reported NBSP for every space. | when: builds that drew a distinct italic or bold-italic face | — |
| 72 | typography-1: a source-content refusal names the occurrence that holds the offending text (`occurrence_id`, `source_text`, `core`), not the page's first segment; a whole-page construct gives `None` for all three. | no | Expect different, correct values. |
| 74 | The unreachable second `untranslated` refusal is removed; the post-draw refusal always carries `'untranslated': []`. | no | — |
| 80 | `/Lang` is written exactly as the mapping spells it (`es-US`, `zh-Hant-TW`, even a non-tag such as `Japanese`), not as PyMuPDF's `set_language` shortened it (`es`, `zh`, `jap`). The `metadata: /Lang ->` line reports what the file holds. The 13 region-less tags the product uses are byte-identical. | when: tags with a region, script or variant subtag, or not a tag | Read the catalog `/Lang`, not `doc.language`, to see the whole tag. |

### prepare_font

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 78 | With `instance=`, the variable face is cut to the job's characters before it is instanced: about 3× less CPU. Nothing is left beside the output — no `<out>.chars.txt`, no `<out>.instanced.ttf`. The subset draws the same (glyphs, advances, cmap, names, line metrics and GPOS positioning are identical, as are renders), but `head`'s bounding box, `hhea`/`vhea` extremes and `OS/2.xAvgCharWidth` now describe the job's glyphs and GPOS is encoded more compactly. `FontResult.subset_bytes` can shrink. | when: calls with `instance=` — the font file, not the PDFs built with it | See *Before you switch* 11; regenerate font goldens. |

### field_fonts

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 68 | A variable face is embedded as its Regular instance (wght 400), not its default outlines (Thin for Noto Sans JP). `FieldFontsResult.instance` (new) names the pins, `''` for a static face. | when: the field font is variable | Allow `instance` in `to_dict()` goldens. |
| 68 | The font is opened with fontTools before the PDF: a `.ttc` collection raises `TTLibFileIsCollectionError`, a missing path raises `FileNotFoundError` — neither a `PdfTranslateError` — and a bad font is reported before a bad PDF. | no | See *Before you switch* 12. |
| 70 | Each field keeps its `/DA` size, colour and other operators; only the font before every `Tf` is swapped. A widget with no `/DA` inherits its parent's or the form's (v54 always wrote `/TransFF 0 Tf 0 g`). `/AcroForm /DA` is derived from the form's own. | when: fields whose `/DA` sets a colour, a size or other operators, or is inherited | — |

### verify

The gate list, `verify.GATE_NAMES`, grows from 24 names at v54 to 28 at
v81: `leak-cjk` (v55), `typography` (v59), `page-parity` (v60) and
`widget-text` (v81). Code that indexes gates by position must not.

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 55 | Gate 21 `leak-cjk` judges CJK-to-CJK jobs whose mapping `lang` names a Han convention: 6 or more characters the target cannot carry in a line FAIL, 1–5 REVIEW. `leak-scan` becomes SKIP there, and `leak-running` / `leak-isolated` are not recorded. | when: CJK-to-CJK jobs (verdicts only) | Treat a `leak-cjk` FAIL as real; allowlist names with `allow=`. |
| 56 | Two false FAILs gone: a wrapped spaceless-script target now passes `placement`; hidden pushbuttons (`--hide-buttons`) no longer fail `button-captions` / `caption-width`. | when: those jobs (verdicts only) | — |
| 60 (guaranteed from 61) | Gate `page-parity`, always on: FAIL on a missing or extra page or a changed box or rotation. `compare()` renders every page and returns 1 when page counts differ; `render_pages()` renders unmatched pages too. | yes: every verdict gains a gate | Check `compare()`'s return value. |
| 80 | Verify reads the stored `/Lang` whole, not as `doc.language` shortens it. A typography-1 build for a region tag (`en-US`) now passes `metadata`; han-forms with no mapping `lang` reads `zh-Hant-TW` as Traditional (REVIEW, no reference) instead of Simplified. The legacy comparison changed too, in one direction, until v83: see [A known issue, fixed in v83](#a-known-issue-fixed-in-v83). | when: region-tagged `/Lang` (verdicts only) | — |
| 81 | Gate 22 `widget-text`, REVIEW only: tooltips, dropdown display labels and text-field values and defaults the output still shows as in the original. The widget-text mapping (`widget_text=`, else `widget_text.json` beside `translations`) marks keeps. `verify` / `run_verify` gain `widget_text=None`. | when: forms with widget text (verdicts only) | With `fail_on_review`, pass the authored mapping or translate the strings. |

### review, qa and the CLIs

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 57 | New `run_review(work, ingest=None, notes=None, generate=True)` returning a `ReviewVerdict`. `pipeline.py finish` requires `--work` and refuses (exit 2) until the review is resolved; `--no-review` delivers anyway. It writes `review_state.json` beside the final PDF. | when: finish or review runs | Pass `--work` (and `--no-review` for v54 behaviour). |
| 59 | `qa_check` reads typography-1 mappings (findings gain occurrence context); legacy findings are unchanged. `pipeline.scaffold_from_cores` returns 2 on malformed JSON instead of raising. | no | — |
| 59 | Six CLIs (extract_segments, pipeline, prepare_font, qa_check, retypeset, verify) exit 2 with `usage: <option> requires a value` when an option has no value, instead of a traceback. | no | — |
| 60 (guaranteed from 61) | A review with errors blocks delivery (`ReviewVerdict.blocks_delivery`). | when: invalid reviews | — |
| 60 (guaranteed from 61) | `pipeline.py rebuild` removes earlier verify reports before it starts, so a failed rebuild leaves none. | when: rebuild | Treat an absent report as "not verified". |
| 61 | A default legacy `rebuild` verifies against its own mapping, so mapping-dependent gates run. | when: rebuild | Expect exit 1 on mapping defects v54 passed. |
| 66 | `rebuild` refuses (exit 2) an output that names the original or any input, in `--flag path` or `--flag=path` form. | no | — |
| 71 | `rebuild` passes the original to every retypeset, so legacy capture bundles carry the source PDF. | when: capture on during a legacy rebuild | — |

### capture

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 60 | Opt-in capture: with `capture_dir=` (or `PDF_TRANSLATE_CAPTURE_DIR` when it is `None`), a refusal caused by a run below the 0.7× floor writes a replayable bundle to `<dir>/<UTC timestamp>-<8 hex>/`, then raises as before. `capture_below=` (or `PDF_TRANSLATE_CAPTURE_BELOW`) also captures successful legacy builds near the floor. A write failure is logged and swallowed. An explicit non-numeric `capture_below` raises `ValueError`; a malformed environment value is ignored. | when: capture is on — new directories only | See *Before you switch* 6. Bundles copy source documents. |

## What moves output bytes

- **Every job:** `segments.json` (the `geometry` key, v64);
  `scale_report.json` (the envelope, v58); every JSON that carries
  `version`; every verify verdict (`page-parity`, v60).
- **Stripped and final PDFs:** strip keeping graphics state (v63);
  cross-field widget text no longer written (v62).
- **Retypeset output:** `/ToUnicode` alternates (v56); italic faces'
  `/ToUnicode` (v67); rotated pages (v64); small print below 4 pt (v65);
  Story escaping of `&`, `<`, `>` (v66); `/Lang` with a region or script
  subtag (v80).
- **Fonts:** `prepare_font` with `instance=` (v78, font file only);
  `field_fonts` with a variable face (v68) or a `/DA` carrying colour,
  size or inheritance (v70).
- **Verdicts, not files:** v55, v56, v60, v61, v80 and v81 above.

## The product's checklist

The product asked this note to cover fourteen items. Each is above, with its
version as checked:

| Item | Version | Section |
|---|---|---|
| `requires-python >=3.14` | 58, guaranteed from 59 | Packaging and import |
| `scale_report.json` as an envelope | 58 | Results, refusals and logging |
| `run_retypeset`, `PlacementError` / `GlyphError` precedence, the refusals shape | 58 (order extended in 64 and 66) | Results, refusals and logging |
| The console is not an API | 58 | How to read this; Results, refusals and logging |
| Capture environment variables and `capture_dir` | 60 | capture |
| Fully qualified widget-text keys; a cross-version scaffold raising `WidgetTextError` | 62 | strip and widget text |
| Strip keeps graphics state (moves bytes) | 63 | strip and widget text |
| Rotated geometry and the stale-extraction refusal | 64 | extract; retypeset |
| Story escaping of `&`, `<`, `>` | 66 | retypeset |
| `/ToUnicode` for role faces | 67 | retypeset |
| Extract judges only the pages asked for | 77 (speed only) | extract |
| `widget_text_kept` | 79 | extract |
| `/Lang` written whole | 80 | retypeset; verify |
| `setuptools>=77` | 73 | Packaging and import |

## A known issue, fixed in v83

**v80 to v82 changed verify's legacy `/Lang` comparison in one direction.**
The rule was "the mapping's `lang` starts with the stored tag". v80 reads
the stored tag whole, so a file that stores a longer tag than the mapping
(`es-US` stored, `es` in the mapping) FAILs `metadata` there, where v79
passed it; so does a file whose region differs (`fr-FR` stored, `fr-CA` in
the mapping). A file that stores the mapping's own tag, as every v80+ build
does, passes. v83 compares the primary subtag instead (below). The app runs
no library verify.

## Later versions

### v82 — this note

Docs only: adds this note and a test that it has a section for the current
version. No code, output or console line changes.

### v83 — legacy verify compares `/Lang` by language

| Version | Change | Bytes | What to do |
|---|---|---|---|
| 83 | Verify's legacy `metadata` gate passes an output whose stored `/Lang` has the same primary subtag as the mapping's `lang`, without regard to case, in either direction: `es-US` for `es`, `es` for `es-US`, `fr-FR` for `fr-CA`, `zh-Hant` for `zh-Hans` (han-forms judges the script). It FAILs another language (`pt` for `es`) and an empty `/Lang`. For a region (`es-US`, `fr-FR`) this gives v79's verdicts again, without depending on how PyMuPDF shortens a tag. Two verdicts differ from v79's: `zh-Hant` stored against `zh-Hans` now passes (v79 failed it, because PyMuPDF kept script subtags), and v79's accidental prefix match (`e` passing `es`) is gone. Typography-1 stays exact; han-forms still reads the whole tag. | when: legacy verdicts for a stored tag that is not the mapping's own | — |
