# R-40: a legacy rebuild's capture bundle records the source PDF — 25 September 2026

**Assignment.** R-40 is the next of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-40 in
`docs/REVIEW-2026-09-24.md`, and the assigned behaviour reads "legacy
capture bundles record `source_pdf`".

R-40 is not a drawing item, so its bar is the shared one. An independent
pass ran anyway, because the question that matters here is whether passing
the original changes anything else for a legacy job. It ships as v71,
stacked on #40 (R-33, v70).

## The defect

`pipeline.py rebuild` always has the original PDF in hand. It passed it to
`retypeset` only for typography-1 jobs:
`retypeset(..., **({'original': orig} if typography else {}))`.

A capture bundle (`capture.py`, opt-in with `PDF_TRANSLATE_CAPTURE_DIR`)
copies the source PDF only when it is given one. So every bundle a legacy
rebuild wrote said `source_pdf: null`. Its `command.given.original` was
null as well, and the job's source could not be replayed from the bundle.

A direct `run_retypeset` call without `original` still writes
`source_pdf: null` on purpose, and `test_capture_on_writes_a_replayable_
bundle_with_no_source_pdf_recorded` pins that. R-40 is about `rebuild`,
which has the original and dropped it.

**The app's route.** The app's session checked on 25 September. The app
never runs `rebuild` or the pipeline CLI, and never opens a capture bundle.
Every `source_pdf` in the app is its own variable. So v71 changes nothing
there.

## The change

`pdf_translate/pipeline.py`: `rebuild` passes `original=orig` to every job.
The R-05 comment beside it is updated: `retypeset` now checks the original
too, after `rebuild` has already checked every input.

**What the legacy path does with `original`:**
- it adds the original to the R-05 output-alias check, which `rebuild`
  already runs before writing anything;
- it gives the original to the two capture calls (`retypeset.py:2089`,
  `:2160`).

Nothing in the drawing reads it.

**Measured.** A two-line legacy job was built three ways: twice without the
original and once with it.
- Built within the same second, all three PDFs are byte-identical
  (`fc385d6d…`).
- An earlier pair did differ, in one place only: the second element of the
  trailer `/ID`. MuPDF derives that from the save time. Every object, the
  text and the pixels were equal.
- Built again two seconds later, with and without the original, both PDFs
  changed together (`339766ac…`).

**Docs:** `references/retypeset.md` and `references/consumer-guide.md` now
say `rebuild` always gives the original.

**Records:** the quick-wins row in `docs/REQUESTS-from-product.md`. The
version goes from 70 to 71. No DECISIONS row: this restores what the
capture docs already promised, and makes no new ruling.

## Red, then green

`tests.test_retypeset_capture.LegacyCaptureTests.test_rebuild_records_the_
source_pdf_of_a_legacy_job` runs a legacy job whose translation overflows
the 0.7× floor through `pipeline.cmd_rebuild`, with the capture variable
set. It checks:
- the build still refuses;
- exactly one bundle is written;
- `files.source_pdf` is `source.pdf`, a byte-identical copy of the
  original;
- `command.given.original` names it.

**Red.** On the unfixed code the bundle said `source_pdf: None`.
**Green.** Capture, rebuild and output-alias tests: 46, all passing.

## Suite

These are CI's commands, run on macOS on `6d1d19a`:

| step | result |
|---|---|
| suite | 740 tests: 1 failure, 1 expected failure |
| canary | 15, OK |
| repository | 6, OK |
| eval fixtures | exit 0 |

- **The failure** is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
  It is a `rebuild` test, so its message was checked: it is the same
  `/private/var` against `/var` mismatch as on R-33's run, not this change.
- **The expected failure** is item 3's right-to-left source pin.

## Independent verification

An independent pass on a different model (Sonnet) worked from `git archive`
copies of `8131093` (v70) and `6d1d19a` (v71). It used its own legacy jobs:
a success, a near-floor success at 0.708×, an overflow refusal and a merge
refusal, plus a typography-1 job. Each ran through `rebuild` on both trees,
in separate processes, with capture off and on. Verdict: **PASS, with no
findings.**
- **The bundles.** On v70, all three legacy bundles (overflow, merge,
  near-floor) have `source_pdf` and `command.given.original` null. On v71
  both are set, and `source.pdf` is byte-identical to the original.
  - A recursive diff of the manifests finds only those two fields and the
    version.
  - Every other copied file is byte-identical.
- **Replay.** A v71 refusal bundle, replayed with its own `source.pdf`,
  raises the same refusal: the same line, at the same 0.372×.
- **Nothing else changes:**
  - **Exit codes, console output, and the verify and scale reports** are
    identical in all 8 job and capture combinations.
  - **Legacy output PDFs** differ only in the second element of the trailer
    `/ID`. The same code run twice more than 1.5 s apart differs in the same
    place, so that is MuPDF's save time.
  - **The typography job's output** is byte-identical, `/ID` included.
- **R-05.** `rebuild` with OUT set to the original, to `translations.json`
  and to `segments.json` exits 2 on both trees, with every input's hash
  unchanged.
- **Tests:**
  - With the new test copied into v70, `test_retypeset_capture` runs 25
    tests and only the new one fails. On v71 all 25 pass.
  - `test_rebuild_attempt` passes 16 of 16 on both.
  - `test_verify_report` confirms v71 in all five places.
