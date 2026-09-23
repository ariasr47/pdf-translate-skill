# Independent review: simplify corrections and A01/A03 cleanup

Date: 2026-09-23. Reviewer: Codex. No candidate code changed, merged, pushed, or published. Consumer source and pins were not touched.

## Verdict

The three reported repairs restore baseline behavior in independently rerun failure cases. The full suite, CLI parity, nine-fixture verdict parity, serialized verdicts and public API comparison pass. One low-priority diagnostic difference remains, so the unqualified claim of **zero behavior change** is still too strong. Restore that edge case before calling this a strictly behavior-preserving cleanup.

The two incremental A01/A03 cleanup commits are acceptable on their own. This is not a test or approval of the three branches combined.

## Finding: P3 — JSON null is mistaken for an unsuccessful read

Location: `C:/Dev/worktrees/simplify-main/pdf-translate/pdf_translate/capture.py:401-402`, introduced by `041447e` and still present at `85d731b`.

`_read_segments()` returns `(None, None)` when the file successfully parses as JSON `null`. `_locate_position()` tests only `data is None`, conflating that result with a failed read. It therefore returns an unknown position with no explanation. Baseline tried `data.get(...)`, logged the capture failure and abandoned the manifest. This is observable even though the main build's refusal is unchanged.

Independent reproduction: run a real below-floor build and have its progress callback replace `segments.json` with the valid JSON text `null` after the build has loaded its input. Same script and font, separate real baseline/candidate checkouts:

| Observable | b20fadd | 85d731b |
|---|---|---|
| Build exception / exit code | PlacementError / 1 | PlacementError / 1 |
| Output PDF exists | false | false |
| Manifests written | 0 | 1 |
| Position notes | [] | [null] |
| Capture failure diagnostic | AttributeError logged | none |

This does not allow a refused PDF to be delivered. It is a small diagnostics/parity issue, not a rendering regression. For this cleanup branch, distinguish an actual failed read from successfully parsed JSON `null` (for example, check the read-error note rather than the parsed data sentinel), retain one parse per bundle, and pin the baseline outcome with a regression test. A deliberate improvement to handling invalid document shapes should be described as a separate behavior change.

Evidence: `runs/simplify-review-85d731b/capture_null_probe.py`, `capture-null-base.stdout`, `capture-null-candidate.stdout`, and corresponding stderr files. These are under `C:/Dev/pdf-translate-skill`.

## Verified revisions

| Scope | Worktree | Reviewed HEAD / range |
|---|---|---|
| Main cleanup | C:/Dev/worktrees/simplify-main | b20fadda832b673b61ce8bc4a5f17189edd58209..85d731bd2a40c5e17580342b4b0a618269ca662a |
| A01 incremental cleanup | C:/Dev/worktrees/simplify-a01 | 41bdf9911c81116ab282aa6e39ce3bee0ca82b04..c4484b721d600027af00bf5567d4795c80acd641 |
| A03 incremental cleanup | C:/Dev/worktrees/simplify-a03 | 30c4805a3027fe3f2492edd4d2745c467646d68a..2249171e63f0a4d094fb597854c46835e115557b |

All three candidate worktrees were clean at review completion. Main cleanup has eight commits, 18 changed files, 341 insertions and 103 deletions. Its original five commits were reviewed in `2026-09-22-upstream-simplify-041447e-review.md`; the additional three were reviewed here.

Baseline worktree: `C:/Users/rodri/.codex/worktrees/simplify-review-b20fadd/pdf-translate-skill`, detached at b20fadd. Runtime: `C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`. Tests use the repository's local test fonts. Every run sets `PYTHONPATH` to the intended worktree's `pdf-translate` directory.

## Fresh test and parity results

| Check | Result |
|---|---|
| Main full unittest discovery | **654 tests, OK, 463.993s**; no failures, errors or skips |
| CLI runner, baseline vs candidate | stdout and stderr diffs empty |
| Verdict runner, nine gate fixtures | stdout and stderr diffs empty |
| Full structured verdicts, same nine fixtures | JSON identical |
| Runtime public API inventory | identical: 48 public package names, 237 module-defined public callables, 19 result dataclasses, five schema entries |
| Capture's original truncated-JSON refusal probe | identical parsed JSON: PlacementError, exit 1, one manifest, no output PDF, explanatory position note |
| A01 focused review and typography suites | **67 tests, OK, 15.058s** |
| A03 focused rebuild, typography and report-policy suites | **23 tests, OK, 30.617s** |
| A03 old/new protected-path collector comparison | **37,449 argv sequences**, zero multiset or membership differences |

The 48-name package inventory includes modules; explicit `__all__` has 39 entries. The 237 callable count excludes three functions in private `_requirements`; including them produces 240, also identical. Dataclass field types/defaults/flags, public method signatures, serializer definitions and schema definitions were compared. Only process-specific object addresses are normalized in the API inventory. The runners' `# package:` provenance line is removed from stderr before comparison; it confirms the different checkouts. No program-output differences are masked.

Some tests emit ResourceWarning messages for existing file reads in `review.py`; that file is unchanged by the main cleanup. They are visible in the retained log and did not fail the suite.

Fresh full A01/A03 suite counts of 655/657 were reported by Claude; they were **not** independently rerun in this follow-up. The original A01/A03 implementations already had independent verification. Here the review and fresh tests target the single added cleanup commit on each.

### Commands and retained evidence

All evidence paths below are relative to `C:/Dev/pdf-translate-skill/runs/simplify-review-85d731b`. The `full.log` command was:

```powershell
$env:PYTHONPATH='C:/Dev/worktrees/simplify-main/pdf-translate'
& C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest discover -s C:/Dev/worktrees/simplify-main/pdf-translate/tests -t C:/Dev/worktrees/simplify-main/pdf-translate
# Ran 654 tests in 463.993s; OK
```

For each checkout, run these with that checkout on PYTHONPATH and the same interpreter:

```text
dev/probes/cli_parity_runner.py <fresh-scratch-job-directory> --font <candidate>/pdf-translate/tests/fonts/NotoSans-Regular.ttf
dev/probes/verdict_parity_runner.py C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/gate-fixtures
C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/api_snapshot.py <output-json>
C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/structured_verdicts.py <same-gate-fixtures> <output-json>
C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/capture_probe.py <fresh-work-directory> <font>
C:/Dev/pdf-translate-skill/runs/simplify-review-85d731b/capture_null_probe.py <fresh-work-directory> <font>
```

CLI fixtures used separate scratch job directories. Logs are `cli-{base,candidate}.{stdout,stderr}`, `verdict-{base,candidate}.{stdout,stderr}`, `api-{base,candidate}.json`, `structured-{base,candidate}.json`, and `capture-{base,candidate}.{stdout,stderr}`. `compare_results.py` writes `comparison.json` and empty `.diff` files for the passing parity checks. The separate null probe is deliberately outside that passing set.

With cwd and PYTHONPATH set to each A01/A03 worktree's `pdf-translate` directory:

```text
python -m unittest tests.test_review tests.test_typography_pipeline
# A01: 67 tests OK, a01-focused.log
python -m unittest tests.test_rebuild_attempt tests.test_typography_pipeline tests.test_verify_report.ReportAndPolicyTests
# A03: 23 tests OK, a03-focused.log
python C:/Dev/pdf-translate-skill/runs/simplify-review-85d731b/a03_loop_audit.py
# 37,449 sequences, zero protected-path multiset/membership mismatches
```

## Independently verified repairs

`error_path_audit.py` runs the new refusal/near-floor tests and independent failure injection against exact historical module source from Git, without checking out or changing a worktree. Supporting imports come from the candidate checkout. The separate original capture probe and parity runs above use complete baseline/candidate packages, not mixed modules.

```powershell
$env:PYTHONPATH='C:/Dev/worktrees/simplify-main/pdf-translate'
# Run each mode separately with the stated Python interpreter:
python C:/Dev/pdf-translate-skill/runs/simplify-review-85d731b/error_path_audit.py base
python C:/Dev/pdf-translate-skill/runs/simplify-review-85d731b/error_path_audit.py broken
python C:/Dev/pdf-translate-skill/runs/simplify-review-85d731b/error_path_audit.py candidate
```

| Probe | Baseline | Defective source | Current candidate |
|---|---|---|---|
| Two unreadable-segments capture tests | 2 pass | 041447e: 2 fail, absent manifest | 2 pass |
| Raising image scan retains handle for inspection | closed | bf05027: still open | closed |
| Malformed mapping plus injected unreadable output | TypeError, zero output reads | a2e47fb: RuntimeError, one output read | TypeError, zero output reads |
| New AST guard against historical capture file | pass | 041447e: detects shadowed `exc` | pass |

Detailed outputs: `error-path-{base,broken,candidate}.json`, `capture-tests-*.log`, `ast-test-*.log`. The image scanner fault uses a real source PDF and verifies the held document's closure before cleanup. The output-read fault is explicitly injected; the test verifies exception ordering, not a particular corrupt PDF parser failure.

The module-level `_read_segments` extraction is reasonable; reducing it to a variable rename is unnecessary. The two extra error-path repairs are directly related to regressions introduced by this cleanup, not unrelated feature work. The structural guard detects the reported historical shadowing bug; it is an additional conservative lint, not proof of all error-path correctness.

## A01 and A03 incremental cleanup

A01's two changes pass `review_json=False` to a fixture helper immediately before each test explicitly writes its own review file. Production code and assertions are unchanged. No additional findings.

A03 collects forwarded protected paths in argv order rather than grouping by flag. The committed old and new blocks were compared over every length-zero-through-five sequence drawn from the five protected flags, an unrelated flag and two path values. Repeated flags, dangling flags and flag-looking values retain identical multiplicities and membership. The downstream `any(_same_path(...))` decision is insensitive to the order change; existing alias protections also passed in the focused suite. No additional findings.

## Recommended next action

1. Make the small capture-null parity correction on `simplify/upstream-cleanup`, with a red/green test. Keep the helper and single parse.
2. Re-run the affected capture tests and the full suite after that code change; re-run parity/API checks for the final submitted revision.
3. Prepare any integration in an isolated worktree after the correction is reviewed. Preserve every DECISIONS row when resolving the documented conflicts, and verify the combined result before adoption. The combined branch has not been tested here.
4. Keep the nine rendering/font/shaping findings and the ten pre-existing behavior bugs as separate work. Neither is necessary to finish reviewing this cleanup. Consumer adoption remains a separate decision.
