# Consumer guide — one document, end to end, from Python

Contents: before you start · the six calls · what each returns · the files on
disk · refusals · progress and cancellation · concurrency and logging · what this library never
does.

This is for an engineer with zero context who has to run one document through
the pipeline from Python and read every output file. Nothing here uses a CLI.

The rule that shapes everything below: **`run_*` is the surface a service
calls.** It is silent, it returns a schema-versioned result, and it raises a
typed exception on refusal. The bare names (`verify`, `retypeset`, …) are the
older shape — they print and return an `int`, and they exist because the CLIs
and the test suite are built on them. Both are supported. Only one is for you.

## Before you start

Three things, each documented elsewhere. This guide points; it does not
re-derive.

1. **`lang` is a BCP 47 tag, not a display name.** `ja`, not `Japanese` or
   `日本語`. `references/translations-format.md` has the rule and the example.
   A value that is not a tag does not fail — it produces a REVIEW, so a
   wrong-format value never yields a clean verdict from a gate that did not run.
2. **A CJK job wants the two reference faces.** `NotoSansJP-VF.ttf` and
   `NotoSansSC-VF.ttf`, passed as `reference_fonts=`. Without them the
   Han-forms gate (20) returns REVIEW rather than PASS, because it cannot
   attest what it cannot compare. `references/fonts.md` says what it does in
   each case.
3. **There is no network access at runtime.** Fonts, reference faces and any
   lookup are files you provide. Nothing here fetches anything, ever.
4. **Ask what the installed engine can read before you author for it.**
   `pdf_translate.MAPPING_FORMATS` is a tuple of the mapping formats this build
   understands. The six calls below all use `legacy`, which every version has
   read. If you need the source's serif/sans class and its within-line
   bold/italic preserved, check for `typography-1` first and follow
   `references/typography.md` — an older engine refuses at build time, after
   the authoring is already done:

   ```python
   formats = getattr(pdf_translate, 'MAPPING_FORMATS', ())
   if 'typography-1' not in formats:
       raise RuntimeError('This installed engine does not support typography-1')
   ```

## The six calls

Pass each job's mapping and extracted segments to verification. Relative input
paths in this example resolve against the process's working directory; `work`
is an explicit directory you provide. The example is a fillable Spanish job;
choose `target_fill` in your job's target script and a font that covers it.

```python
import pdf_translate

work = '/tmp/job'                      # a directory you own
target_fill = 'Prueba 123'             # Spanish example; use the job's script

strip = pdf_translate.run_strip('source.pdf', f'{work}/stripped.pdf')
extract = pdf_translate.run_extract('source.pdf', work)
#   ... author work/translations.json from extract.cores ...
font = pdf_translate.run_prepare_font('NotoSans.ttf',
                                      f'{work}/translations.json',
                                      f'{work}/font-sub.ttf')
built = pdf_translate.run_retypeset(f'{work}/stripped.pdf',
                                    extract.segments_path,
                                    f'{work}/translations.json',
                                    f'{work}/out.pdf')
verdict = pdf_translate.run_verify(
    'source.pdf', built.output, fill_text=target_fill,
    translations=f'{work}/translations.json', segments=extract.segments_path,
    source_words_from=extract.segments_path)
final = pdf_translate.run_field_fonts(built.output, 'NotoSans.ttf',
                                      f'{work}/final.pdf')
final_verdict = pdf_translate.run_verify(
    'source.pdf', final.output, fill_text=target_fill,
    translations=f'{work}/translations.json', segments=extract.segments_path,
    source_words_from=extract.segments_path)
```

Read `final_verdict.exit_code` and every FAIL/REVIEW finding before reporting
the delivery's verification state. A verdict for `out.pdf` does not attest
`final.pdf` after field-font embedding. For a non-form job, omit `run_field_fonts`
and verify `built.output` as the delivery path. Repeat verification after any
later modification to the delivered PDF.

`translations=` enables mapping-dependent checks, including empty targets and
authored-target placement. Omitting it can produce exit 0 without checking
those properties. `segments=` supplies override-marker context;
`source_words_from=` supplies the leak scan's source vocabulary. For a Japanese
job, a fill value such as `山田太郎 123` must be paired with an appropriate full
field font. Structural findings remain advisory on the library surface; visual
inspection and language review are still required. (The CLI's `pipeline.py
rebuild` passes its work directory's mapping to verification itself.)

Two more are advisory rather than structural:

```python
qa = pdf_translate.run_qa(f'{work}/translations.json',
                          segments_path=extract.segments_path)
review = pdf_translate.run_review(work, ingest='review.json')
```

`run_qa` also takes `glossary_path=`; pass it only when that file exists,
which after a `run_review --ingest` it will.

`run_qa` checks mechanics — numbers that moved, punctuation parity, the
expansion band. `run_review` is the second-reader loop: it writes the pairs
file and the MQM prompt, reads the reviser's verdict back, and grows a
per-class termbase. Neither judges whether the wording is right. No script
can; see `references/terminology-failure-modes.md` for the five ways a term of
art goes wrong while every gate passes.

## What each returns

Every result is a frozen dataclass whose `to_dict()` carries `schema` and
`version`, and is JSON-serialisable as it stands.

| call | returns | the fields you will actually use |
| --- | --- | --- |
| `run_strip` | `StripResult` | `ok`, `leftover_text`, `xfa_removed`, `certified`, `encrypted`, `dead_buttons` |
| `run_extract` | `ExtractResult` | `cores`, `segments_path`, `warnings`, `unextractable_pages`, `invisible_text_pages` |
| `run_prepare_font` | `FontResult` | `output`, `glyphs_added`, `subset_bytes` |
| `run_retypeset` | `RetypesetResult` | `output`, `cancelled`, `scaled`, `scale_report_path` |
| `run_verify` | `VerifyVerdict` | `exit_code`, `gates` (each a `GateResult` with `status` and `findings`) |
| `run_field_fonts` | `FieldFontsResult` | `output`, `fields`, `acroform`, `instance` (the axis values a variable face was pinned to, or `''`) |
| `run_qa` | `QAVerdict` | `findings`, `exit_code` |
| `run_review` | `ReviewVerdict` | `present`, `blocks_delivery`, `open_findings`, `review_line`, `counts` |

`run_verify` returning `exit_code == 1` is a **needs-attention notice, not a
withholding.** The document is built and on disk. Only a build refusal
(`run_retypeset` raising) means this attempt produced no successful document.
An older file can still exist at a reused output path — see `docs/DECISIONS.md`
and the product's ruling R5.

## The files on disk, and which call wrote them

| file | written by | what it is |
| --- | --- | --- |
| `stripped.pdf` | `run_strip` | the source with every page text run deleted |
| `segments.json` | `run_extract` | geometry, one entry per placeable segment. Every `origin` and `bbox` is in the page's unrotated space, the space `page.get_text` reports. The top-level `geometry` names that space and lists each `/Rotate` page with its `rotation` and unrotated `width` and `height`. To draw over a render of such a page, map through `page.rotation_matrix` |
| `to_translate.json` | `run_extract` | the unique cores, with counts |
| `widget_text.json` | `run_extract` | the tooltip / dropdown / default scaffold. A file that already holds authored text is kept, not overwritten, and `ExtractResult.widget_text_kept` is true |
| `translations.json` | **you** | the mapping. The library never writes it |
| `font-sub.ttf` | `run_prepare_font` | the subset face |
| `out.pdf` | `run_retypeset` | the translated document |
| `scale_report.json` | `run_retypeset` | `{"schema": 1, "version": …, "runs": [...]}` — every run below source size. Pass `scale_report=` to move it, or `None` to write nothing and read `result.scaled` instead |
| `final.pdf` | `run_field_fonts` | the delivery copy, fields able to render typed text |
| `review_pairs.md`, `review_prompt.md`, `glossary.csv` | `run_review` | the second reader's inputs, and the termbase their verdict grows |

### Rebuilding in an existing work directory

`pipeline.py rebuild` invalidates `work/verify_report.json` and its selected
`--report` path before loading the mapping or starting any stage. A failed or
interrupted attempt cannot inherit an earlier success report at those paths.
Verification writes a fresh report if it runs to completion, including a
report with `exit_code: 1` when verification finds a problem.

Use the current command's return code and its fresh report together. A
missing report means verification evidence is unavailable, even if the
command returns 0 after a report-write warning. An old PDF or scale sidecar
is never proof that this attempt succeeded. Early failures and build refusals
leave the previous PDF in place; a verification failure may leave the newly
built PDF. This change does not make PDF/sidecar publication transactional.

Report paths must be dedicated to verifier output. Before removing any
report, rebuild checks for aliases to inputs/output and requires existing
files to have the verifier's schema-1 report shape. Unrelated, unreadable or
unrecognized files are preserved and the command returns 2. If the operating
system prevents removing an old report, rebuild refuses before typesetting
and explains that the retained report does not describe this attempt.

The default report is invalidated even when switching to a custom path.
Older reports at other custom paths remain caller-owned history; rebuild
does not discover or manage them. Invalid CLI syntax rejected before rebuild
starts does not invalidate reports. Use a separate workspace for each
concurrent job.

Direct `run_retypeset` callers retain the existing result/exception contract:
check the result's `cancelled` and `output` fields or catch the refusal, and
run verification on the successful current result. These calls do not manage
the pipeline's verification report.

## Refusals

A refusal is an exception, not a printed line and not a return code.

```python
from pdf_translate import PdfTranslateError, GlyphError

try:
    built = pdf_translate.run_retypeset(stripped, segments, mapping, out)
except GlyphError as exc:
    # The face cannot draw a character the target needs. R1: refusal wins —
    # no placeholder glyph, no borrowed face.
    print(exc.page, exc.char, exc.face)
except PdfTranslateError as exc:
    for kind, items in exc.refusals.items():
        for item in items:
            print(kind, item['core'])        # the FULL core, never truncated
```

Every exception carries:

- `console_line` — exactly what the loud function would have printed. You do
  not need it; it exists so the CLIs stay byte-identical.
- `exit_code` — what the loud function would have returned.
- `refusals` — **every refused item, by kind, with the core in full.** One
  build can fail for several reasons at once; the exception type names the
  first by precedence and `refusals` carries all of them, so you fix the
  mapping in one pass instead of rebuilding to discover the next reason.
- `to_dict()` — all of the above plus `schema` and `version`.

The types are `MappingError` (an unauthored core, a merge that does not
match), `GlyphError` (`page`, `char`, `face`), `PlacementError` (`page`,
`key`, `scale`), `FontError` (`face`, `reason`), `WidgetTextError`. All
descend from `PdfTranslateError`, so one `except` catches every refusal.

An output PDF or scale-report path that names one of the build's own inputs
is refused before anything is written. The inputs are the stripped PDF,
`segments.json`, the mapping, the original and any font. For a legacy
mapping the refusal is a `MappingError` whose `refusals['output_aliases']`
lists `{writes, path, input}`; typography-1 refuses the same thing as
`invalid-style-reference`. Until v66 a legacy build wrote straight over the
input and returned 0. `pipeline.py rebuild` also refuses, with exit 2, an
OUT that names the original PDF, a work-directory input, or a file passed to
an input flag, as `--flag path` or as `--flag=path`.

**Do not parse the console.** A printed format is an undeclared API: it
changes without a version bump, and a consumer whose regex stops matching
fails silently, which is the worst way to fail.

### Capturing a below-the-floor refusal for later evidence

`run_retypeset(..., capture_dir='/path/to/captures')` is opt-in, off by
default. When a refusal is caused specifically by a run scaling below
`SCALE_MIN` — not any `PlacementError`, only that one — a self-contained,
replayable bundle is written under a new timestamped subdirectory of
`capture_dir`: the source PDF (if you passed `original`; `pipeline.py
rebuild` always does) and stripped PDF,
segments, the authored mapping with its fonts, the structured refusal
(`exc.to_dict()`), the occurrence's page and position, and its box
permission if one is on record (`null`, with a note, when it is not — never
guessed). `PDF_TRANSLATE_CAPTURE_DIR` is the same switch for a caller that
cannot pass the keyword, checked only when `capture_dir` is not given.

Leave it unset and nothing changes — no directory, no extra file, same
console output. A problem writing the bundle is logged and swallowed; it
never changes, masks, or replaces the exception you catch. Details and the
exact bundle layout: `references/retypeset.md` and `pdf_translate/capture.py`.

## Progress and cancellation

```python
def on_progress(done, total):
    print(f'{done}/{total}')

result = pdf_translate.run_retypeset(
    stripped, segments, mapping, out,
    progress=on_progress,
    cancel=lambda: user_pressed_stop)

if result.cancelled:
    assert result.output is None          # no output from this attempt
```

`total` is **pages plus merge jobs**, because `run_retypeset` runs two loops —
a per-page pass and then a per-merge pass. A counter of pages alone reaches
100% and keeps going.

`cancel()` is checked at the top of every unit in both loops. There is exactly
one save, at the very end, so a cancelled run does not publish its candidate.
A file from a previous successful run can remain at `out`; cancellation does
not remove it.

## Concurrency and logging

**Do not run PDF stages concurrently in multiple threads.** PyMuPDF does not
support multithreaded use; it can produce incorrect results or crash Python.
See its [multiprocessing guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html).

For concurrent PDF jobs, use separate processes, with one job running at a time
in each worker. Pass input paths and plain job data to the worker; open PDFs and
create PyMuPDF resources inside that process. Do not share live PyMuPDF documents,
pages or fonts between workers. Each job needs its own `work` directory and
output/report paths. A distinct `scale_report=` path alone does not isolate the
other files a job writes.

The silent `run_*` functions avoid process-global stdout redirection. This fixes
logging interference; it does not make the native PDF backend thread-safe.
Existing thread-based regression checks cover observed output/report isolation
on their fixtures, not backend thread safety. End-to-end validation of two
process-isolated jobs remains pending; this guidance is not a claim that a
consumer's worker integration has been tested.

For logging in a service, use the silent functions and attach your own handler:

- **`console()`** (`pdf_translate._console`) mutates process-global logging
  state and is not thread-safe. It exists for CLI entry points; a service does
  not call it.
- **The loud names** (`verify`, `retypeset`, …) open `console()` themselves;
  use their `run_*` counterparts in each service worker.

To see the library's output in your own logs:

```python
import logging
logging.getLogger('pdf_translate').setLevel(logging.INFO)
logging.getLogger('pdf_translate').addHandler(your_handler)
```

Importing `pdf_translate` attaches a `NullHandler` and nothing else. It sets
no level on the root logger and configures nothing for its host.

## What this library never does

- **Never reaches the network.** Not for fonts, not for lookups, not ever.
- **Never invents a glyph.** A character the face cannot draw is a refusal
  (R1), not a box and not a borrowed face.
- **Never writes `translations.json`.** The mapping is authored by a person or
  a model you run. No model is called from inside this package.
- **Never ships a glossary.** A termbase is a job input and a job output, never
  repository content.
- **Never withholds a document it built.** A verify FAIL is advisory; only a
  build refusal means this attempt did not produce a successful document.
- **Never configures logging for you.**
- **Never judges whether the wording is right.** Nothing can. That is what
  `run_review` and a second human reader are for.
