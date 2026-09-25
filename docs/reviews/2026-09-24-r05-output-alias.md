# R-05: a legacy build never writes over its own inputs — 24 September 2026

**Assignment.** This is the first of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-05 in
`docs/REVIEW-2026-09-24.md`: "an output path that names an input mapping or
segments file is refused on the legacy path too." The acceptance is the
shared bar:
- a test that fails on the unfixed code and passes after the fix;
- a version bump;
- a notice to the app.

R-05 is not a drawing, font or layout item, so Rule 1 is not part of its
bar. An independent review ran anyway (below).

## The defect

typography-1 refused an output or scale-report path that named one of its
inputs. A legacy mapping went straight to `doc.ez_save(out)`. Reproduced on
v65 by the tests below, each case in a fresh directory:

| output names | v65 |
|---|---|
| the mapping | exit 0; `translations.json` is now PDF bytes |
| `segments.json` | exit 0; overwritten |
| a font file | exit 0; overwritten |
| `stripped.pdf` | a bare `ValueError: save to original must be incremental` |
| the scale report, pointed at the mapping | not refused |
| `rebuild` with OUT = the original PDF | exit 0: the original is replaced by the translation and verified against itself |
| `rebuild` with OUT = `translations.json` or `segments.json` | the input is overwritten, then the rebuild crashes reading it back |

## The change

**`pdf_translate/retypeset.py`:**
- `_legacy_fonts` is the existing font resolution, moved into a helper and
  called once, early.
- `_refuse_output_aliases` then checks the output PDF and the scale-report
  path against the stripped PDF, `segments.json`, the mapping, the
  original and every resolved font. It also checks the output against the
  report.
- A hit raises `MappingError`, with `refusals['output_aliases']` as
  `{writes, path, input}` and exit 1, before anything is read or written.
- typography-1 keeps its own check, unchanged.

**`pdf_translate/pipeline.py`:** `rebuild` checks OUT against the original,
the work directory's stripped PDF, segments and mapping, and any forwarded
input path, and exits 2 first. A legacy retypeset is never told the
original, so this is the only check that protects it.

**Docs:** `references/consumer-guide.md`, next to the refusal types.

**Records:** a `docs/DECISIONS.md` row, and the quick-wins row in
`docs/REQUESTS-from-product.md`. The version goes from 65 to 66.

## Red, then green

`tests.test_pipeline.OutputAliasTests`:
- the output named as each of the mapping, `segments.json`, `stripped.pdf`
  and a private font copy: refused, with exit 1, and the input's sha256
  unchanged;
- the scale report named as the mapping: `MappingError` with the one
  `output_aliases` entry, the mapping unchanged and no output written;
- `rebuild` with OUT named as `translations.json`, `orig.pdf` and
  `segments.json`: exit 2, the file unchanged;
- `rebuild` with OUT named as a file forwarded through
  `--source-words-from`, spelled as `--flag path` and as `--flag=path`:
  exit 2, the file unchanged (added after the review, below);
- a control: a distinct output still builds.

**Red.** On the unfixed code, 5 subtests failed and 3 errored (exit 1),
exactly as in the table above. **Green:** all pass.

## Suite

CI's 22 modules on this branch, on macOS, ran 725 tests. There was 1
failure and 1 expected failure, with no errors or skips.
- The failure is the macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
  Its assertion is the same as on R-02's run: `/private/var` against `/var`
  in a temp path. It exercises `rebuild`'s argument handling, so it was
  checked, and nothing here changed it.
- The expected failure is item 3's right-to-left source pin.
- The canary, binary integrity and the eval fixtures passed.

## Independent review

A pass on a different model (Sonnet) worked from `git archive` copies of
`f5cf474` and `4cf1054`, with its own job and scripts: about 25 scenarios.
Verdict: PASS with one major finding, now fixed.

**What held:**
- **Old behaviour reproduced.** On v65 the mapping, segments and a font were
  replaced with exit 0, `stripped.pdf` raised `ValueError`, and `rebuild`
  overwrote the original and then verified PASS against it.
- **Every other spelling of an input is caught:** a relative path, `..`, a
  symlink, a hard link, a case-only difference on APFS, `./` and a trailing
  slash. So is a font given mapping-relative or caller-relative, and the
  caller-relative NOTE prints once.
- **Reports.** `scale_report=None` is never checked. A mapping named
  `scale_report.json` beside OUT is caught through the default report path.
- **No false refusals** for a new OUT next to the inputs, null font paths,
  one font for every role, or no original.
- **Nothing is written** when the guard fires: no output, no scale report,
  and no capture bundle even with `capture_dir` set.
- **typography-1's guard is byte-identical to v65**, and its 58 tests pass.
- `OutputAliasTests` passes on v66 and fails on v65 (5 failures, 3 errors).

**The finding (major): the `--flag=value` spelling.** `rebuild` paired
forwarded input flags only as `--flag value`. `--source-words-from=path` or
`--reference-fonts=path` with OUT set to that path built with exit 0 and
overwrote the file.
- Verify reads only the separate spelling (`_arg`), so in that form the file
  is never read. It is still the file the caller named, so `rebuild` now
  protects both spellings, and a test pins them.
- That verify silently ignores `--flag=value` is older than this change.
  It is filed as a proposal in `docs/REQUESTS-from-product.md`.
