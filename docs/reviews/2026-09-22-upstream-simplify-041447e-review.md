# Independent review: simplify/upstream-cleanup

**Verdict: request changes. All four requested acceptance checks pass, but
the zero-behavior-change claim is disproved by a reproduced capture regression.**

Reviewed five commits from `b20fadda832b673b61ce8bc4a5f17189edd58209` through
`041447eb730f708cc162f7eca254c88ecddcab86` in
`C:/Dev/worktrees/simplify-main`, branch `simplify/upstream-cleanup`.
The candidate started and ended clean at that exact commit. Review made no
changes to its tracked files, index, branch, or HEAD.

## Finding: P2 — preserve the refusal exception when reading segments fails

Location: `pdf-translate/pdf_translate/capture.py:238`, introduced by `041447e`.

`_write_bundle` receives the original refusal as its `exc` argument. The new
`except (OSError, ValueError) as exc` binds that same name to the segment-read
error. Python clears an exception target when its handler exits, so later
uses of the original refusal at lines 258 and 285 raise `UnboundLocalError`.
The outer best-effort capture wrapper swallows this and returns `None`,
leaving copied inputs without the previously produced manifest.

This is an observed regression, not just a code-reading concern. A synthetic
legacy job actually exceeds the placement floor. Its public progress
callback truncates `segments.json` after the build has already loaded it,
exercising capture's existing unreadable-geometry fallback:

| Observation | b20fadd | 041447e |
|---|---|---|
| Original build exception | `PlacementError`, exit 1 | Same |
| Translated output created | No | No |
| Capture manifest written | 1 | 0 |
| Geometry read error | Recorded in `occurrence.position_note` | `UnboundLocalError` logged; capture abandoned |

The original translation refusal is not replaced and no failed PDF becomes
deliverable. The regression loses diagnostic evidence on the error path.
The commit message explicitly claims this fallback remains unchanged; it does
not. Normal capture tests and the ordinary parity fixtures do not exercise
this branch.

Recommended correction: use a separate exception name for the read/parse
failure, retaining the original `exc`. Add a regression that checks the
completed bundle and original refusal data when geometry parsing fails;
cover refusal and near-floor capture because both use `_write_bundle`.
Keep parsing once per bundle. This review does not implement the correction.

## Fresh acceptance results

| Required check | Independent result |
|---|---|
| Complete library suite | **649 tests, 411.247s, OK**, no failures/errors/skips |
| CLI parity against a b20fadd worktree | **12 invocations; empty diff** |
| Verdict parity across nine gate fixtures | **Nine cases; empty console and verdict-summary diffs** |
| Public API surface, fields and schemas | **Identical snapshots** |

The API snapshot records the initial **48 public package names**, including
the **39 explicit `__all__` entries**, plus **237 module-defined public
callables** excluding the private dependency-preflight module. It also checks
that module's three callables, for a broader total of **240 signatures**.
Both versions have identical parameter kinds, defaults, annotations and return
annotations; **19 dataclasses** have identical field order, types, defaults,
factories, comparison/init options and frozen/slot attributes. Five schema
constants/blocks, public class method signatures, and serializer source hashes
also match. Process-specific addresses on default sentinels are normalized;
no signature differences are discarded.

Additional verification:

- Complete serialized `run_verify(...).to_dict()` results match for all nine
  fixtures, including every gate and finding, beyond the supplied runner's
  abbreviated stderr summary.
- **15 canary scorer tests passed in 0.787s**, covering the changed developer
  tool that is outside library discovery.
- `git diff b20fadd..041447e --check` succeeds. No test, CI, package-export or
  result-model files changed in this range.
- The suite emits existing `ResourceWarning`s for review NOTES.md and
  fontTools file handles. They did not produce test failures.

## Commands and durable local evidence

Interpreter:
`C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`, Python
3.14.0. Candidate imports were printed and verified to resolve under
`C:/Dev/worktrees/simplify-main/pdf-translate/pdf_translate/`.

Baseline is a newly created clean, detached worktree at exact b20fadd:
`C:/Users/rodri/.codex/worktrees/simplify-review-b20fadd/pdf-translate-skill`.
Its ignored test fonts were copied from the candidate's existing fixture
fonts. No dependencies or consumer source were imported/copied.

All fresh logs, fixture jobs, snapshots, diffs and independent probe scripts:
`C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/` (ignored scratch).
`comparison.json` records empty diffs and matching SHA-256 values. Useful
artifacts include `full.log`, `canary.log`, `api-base.json`,
`api-candidate.json`, `capture-base.stdout`, `capture-candidate.stdout`, and
`capture-candidate.stderr`.

Commands below use PowerShell variables only to shorten the exact paths:

```powershell
$reviewPy = 'C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe'
$reviewCandidate = 'C:/Dev/worktrees/simplify-main'
$reviewBase = 'C:/Users/rodri/.codex/worktrees/simplify-review-b20fadd/pdf-translate-skill'
$reviewEvidence = 'C:/Dev/pdf-translate-skill/runs/simplify-review-041447e'
$reviewFont = "$reviewCandidate/pdf-translate/tests/fonts/NotoSans-Regular.ttf"

$env:PYTHONPATH = "$reviewCandidate/pdf-translate"
& $reviewPy -m unittest discover -s "$reviewCandidate/pdf-translate/tests" -t "$reviewCandidate/pdf-translate"
& $reviewPy -m unittest discover -s "$reviewCandidate/dev/canary" -p test_score.py -v

# Generate the shared nine-case fixtures once, using the baseline runtime.
$env:PYTHONPATH = "$reviewBase/pdf-translate"
& $reviewPy "$reviewBase/dev/probes/verdict_parity_fixtures.py" "$reviewEvidence/gate-fixtures"

# Run each pair with its own checkout first on PYTHONPATH.
foreach ($reviewPair in @(@('base', $reviewBase), @('candidate', $reviewCandidate))) {
    $reviewLabel, $reviewRoot = $reviewPair
    $env:PYTHONPATH = "$reviewRoot/pdf-translate"
    & $reviewPy "$reviewRoot/dev/probes/cli_parity_runner.py" "$reviewEvidence/cli-$reviewLabel-job" --font $reviewFont
    & $reviewPy "$reviewRoot/dev/probes/verdict_parity_runner.py" "$reviewEvidence/gate-fixtures"
    & $reviewPy "$reviewEvidence/api_snapshot.py" "$reviewEvidence/api-$reviewLabel.json"
    & $reviewPy "$reviewEvidence/structured_verdicts.py" "$reviewEvidence/gate-fixtures" "$reviewEvidence/structured-$reviewLabel.json"
    & $reviewPy "$reviewEvidence/capture_probe.py" "$reviewEvidence/capture-$reviewLabel" $reviewFont
}
```

Actual runs captured stdout/stderr in the matching named evidence files.
CLI comparisons use the unchanged runner's built-in path/timing
normalization. The only extra exclusion is the expected `# package:` import
location on stderr. Verdict stdout and complete serialized verdicts compare
without path/timing substitutions because both consume the same fixture
directory. All four runner processes returned 0, and their 12/9 case counts
were inspected rather than treating runner exit alone as proof.

## Scope and next step

No additional actionable defect was found in the other four commits. Their
ordinary behavior and API comparisons passed, but passing these fixtures is
not a proof of equivalence on every possible input. The reported nine
deferred rendering/shaping/font proposals and ten pre-existing behavior bugs
were not implemented or closed by this review. This review concerns the five
commits only; A01/A03 and their separate simplification branches are outside
this range. It does not approve publication, merging the older B1 branch, or
PDF Translator adoption.

Fix the new capture error-path regression, rerun its new regression tests and
the existing capture tests, then recheck the final revision before integration.
Keep the consumer dependency unchanged until its separate adoption checks.
