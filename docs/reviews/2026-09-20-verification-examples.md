# A06: mapping-aware verification examples

20 September 2026 · documentation slice complete locally; default-command fix open

The [quickstart](../../pdf-translate/README.md#quickstart),
[skill workflow](../../pdf-translate/SKILL.md#workflow),
[Python guide](../../pdf-translate/references/consumer-guide.md#the-six-calls)
and [gate reference](../../pdf-translate/references/gates.md) now pass translation
mapping, segments, source vocabulary and an explicit target-script fill value.
They verify the actual delivery PDF after font embedding or packaging, with a
separate final report/verdict. Non-form instructions identify `out.pdf` as the
delivery file when no `final.pdf` was created.

The examples explain that omitting the mapping omits checks such as empty targets
and authored-target placement; exit 0 is not proof of those properties. The gate
reference also distinguishes REVIEW findings from failures. Library verdicts
remain advisory. No default behavior, delivery policy or PDF implementation
changed; shipped workflow instructions advance the four version sources to v60.

## Executed checks

The local smoke harness read **seven CLI commands and two Python verification
calls directly from the edited documentation**, rather than maintaining a second
copy of their arguments. It ran them against three isolated synthetic cases:

| Case | Default rebuild | Each revised verification/rebuild example | Delivery-path check |
| --- | --- | --- | --- |
| Saved two-label mapping with one empty target | 0; `empty-targets` absent | 1; `empty-targets` FAIL | Actual `out.pdf` / `final.pdf` reported |
| Same source, both targets authored in Spanish | 0 | 0; no FAIL | Actual `out.pdf` / `final.pdf` reported |
| Complete Spanish mapping with one text field | 0 | 0; field round-trip PASS | `final.pdf` checked after field-font embedding |

**27 expected example outcomes**, plus three unchanged-default controls.
`Prueba 123` was the target-script fill value. The two non-form final-path copies
retained the built bytes; the fillable final went through `run_field_fonts`.
The original saved audit fixture was copied into fresh folders and preserved.

From the repository root, with the existing virtual environment:

```powershell
$env:PYTHONUTF8='1'
& '.\pdf-translate.venv\Scripts\python.exe' runs/a06-verification-examples-2026-09-20/check_examples.py
```

Exit 0:

```text
PASS empty-target: default rebuild=0; 7 documented CLI examples + 2 documented Python calls=1; final path checked
PASS complete-targets: default rebuild=0; 7 documented CLI examples + 2 documented Python calls=0; final path checked
PASS fillable-complete: default rebuild=0; 7 documented CLI examples + 2 documented Python calls=0; final path checked
PASS: 27 example outcomes; 3 default-command controls; fillable control exercises target-script field round-trip.
```

The harness, PDFs, raw reports and per-command logs remain in ignored
`runs/a06-verification-examples-2026-09-20/`. It intentionally refuses to reuse
its case directories; do not delete existing evidence to rerun it. The retained
input comes from the earlier audit probe's `empty-target` case.
[Sanitized results](data/2026-09-20-verification-examples.json) record each outcome
and CLI argument list. On Windows the harness substituted the repository's
Python interpreter and paths, then invoked the extracted arguments directly;
it did not run the Bash examples through a Bash shell. The two Python calls
were extracted as AST statements and run in fresh subprocesses.

From `pdf-translate/`:

```powershell
$env:PYTHONUTF8='1'
& '..\pdf-translate.venv\Scripts\python.exe' -m unittest tests.test_verify_report.VersionLockstepTests -v
```

Exit 0: **Ran 1 test in 0.057s; OK**. `git diff --check` also exited 0.
The only Python edits are the version constant and its lockstep expectation;
source comparison against this turn's saved before-images verifies that scope.

## Limits and remaining work

This is a focused run of the verification examples, not the entire quickstart,
a full-suite rerun, a non-Latin shaping/visual judgment, or a model-driven host
evaluation. Existing review/delivery defects from the audit remain open.
Default `rebuild` still fails to forward mapping context automatically, and
`finish` still does not invoke final verification. A06 remains **partial** in
the [canonical backlog](../../dev/goals/PROGRAM.md#public-readiness-backlog).

Next smallest recommendation: A15's README facts. No commit, push, merge,
release, PR edit or app-task message occurred. Git/GitHub were rechecked before
editing: local HEAD `1d4f970` on `codex/b1-design-canvas`; remote main `a5629fb`;
PRs #12/#13 OPEN at `abc4767` / `1d4f970`, still stacked. Prior A04/B1/audit work
was preserved, the product repository was not opened, and B1 remains deferred.
