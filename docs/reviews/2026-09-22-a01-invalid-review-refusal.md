# A01 — invalid reviews cannot authorize ordinary finish

Local candidate on `codex/a01-invalid-review-refusal`, based on main
`b20fadda832b673b61ce8bc4a5f17189edd58209` (v60), 22 September 2026.
This is not published; version metadata remains 60 until a release version is
selected. Original checkout's unrelated dirty v61 work was not imported.

## Problem and change

An empty review object produced two validation errors and review exit 2, but
`blocks_delivery` ignored errors. `finish` therefore returned 0, wrote a final
PDF and recorded no warning. Dropping an invalid finding could have the same
effect, including typography binding failures that deliberately discard findings.

`ReviewVerdict.blocks_delivery` now requires no errors as well as a present
review and no open findings. Its warning identifies invalid review state.
`finish` reports each review error and the retry command, writes the failed
review state, and returns 2 before packaging. It does not alter rendering,
mapping, schema validation, review-freshness policy or consumer enforcement.

The deliberate `--no-review` behavior is preserved: finish may return 0 and
deliver, with `no_review=true` and an explicit no-reviser line. Validation errors
and review exit 2 remain in that state when the underlying review is invalid.
The review's `blocks_delivery` means it cannot attest the delivery; the explicit
override is not a valid review.

An existing final PDF/comparison is left untouched on refusal, with a current
failed review state replacing the previous successful state. This does not
solve A03's broader rebuild/output lifecycle; callers must use the command's
failure and current review state, not file existence, as the attempt result.

## Observable acceptance and verification

| Outcome | Verify by |
| --- | --- |
| Malformed JSON, non-object reviews, missing/wrong-type reviewer or findings blocks, invalid finding entries, missing finding fields and invalid category/severity/resolution values return review exit 2, block ordinary finish and create no new delivery/comparison. | `tests.test_review.RunReviewTests.test_invalid_review_errors_block_delivery_even_without_open_findings` and `RefusalTests.test_finish_invalid_review_refuses_without_creating_delivery`; 13 input cases each. |
| A formerly successful delivery followed by invalid review returns finish 2, leaves old PDF/HTML bytes untouched and replaces state with blocked/error. | `RefusalTests.test_invalid_review_replaces_prior_success_state_without_touching_old_delivery`. |
| Explicit no-review delivery discloses the bypass in console/state and retains validation errors. | `RefusalTests.test_explicit_no_review_discloses_bypass_of_invalid_review`, plus existing missing-review override test. |
| Valid resolved and empty-findings reviews still deliver. | Existing resolved-review test and `RefusalTests.test_valid_review_with_no_findings_can_deliver`. |
| Missing or mismatched typography review bindings cannot authorize finish; current binding succeeds. | `tests.test_typography_pipeline.TypographyPipelineTests.test_finish_rejects_stale_review_binding_and_accepts_current_binding`, through the actual CLI subprocess. |

## Runs

Python 3.14.0, PyMuPDF 1.28.2, pikepdf 10.13.0.post1. Commands use
`C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`, with
`PYTHONPATH` set to this worktree's `pdf-translate` and `PYTHONUTF8=1`.
Commands below run from `pdf-translate/` unless stated otherwise.

- Baseline `python -m unittest tests.test_review tests.test_typography_review -q`:
  **65 tests OK in 1.994s**.
- Tests first, before runtime edit:
  `python -m unittest tests.test_review tests.test_typography_pipeline -v`:
  **67 tests, 29 failing assertions, no test errors, 16.405s**. Failures show
  wrong delivery success, missing error disclosure or false blocking state.
  Log: `runs/a01/red.log` from the worktree root.
- After the minimal fix:
  `python -m unittest tests.test_review tests.test_typography_review tests.test_typography_pipeline -v`:
  **81 tests OK in 15.837s**, `runs/a01/green.log`.
- Full discovery `python -m unittest discover -s tests -t . -v`:
  **655 tests OK in 353.699 seconds, no failures, errors or skips**.
  Log: `runs/a01/full.log` from the worktree root.
- Existing 12-invocation CLI parity probe run against the candidate and v60
  export: console output identical after the runner's normalization and removal
  of its package-location diagnostic. This covers unchanged ordinary routes;
  the new tests deliberately cover changed invalid-review refusals.
- Independent reviewer: **no actionable A01 findings**. Separate focused run:
  **81 tests OK in 16.418s**. Their own real CLI probe refused **31 invalid
  review cases**, including all seven required finding-field omissions and
  string/null/integer/list/object enum values; every refusal kept prior final
  PDF bytes unchanged and wrote a fresh blocked/error state. Valid empty review
  and four resolved/migrated variants delivered. A valid typography binding
  delivered first; missing/stale bindings then refused over that prior success.
  Original command: `python runs/a01-independent/probe.py` from `pdf-translate/`.
  Evidence was subsequently moved to the repository's ignored
  `runs/a01-independent/` directory; rerun from `pdf-translate/` with
  `python ../runs/a01-independent/probe.py` and the same import environment.

The baseline and focused runs emit the existing `ResourceWarning` for the
unclosed NOTES.md read in review.py. It predates this change and is not repaired
here. No hosted CI or model-driven translation acceptance is claimed.

## Scope remaining

A02 page counts, A03 failed-rebuild artifacts, A06 default mapping verification,
the typography near-floor capture omission, and B1 remain separate work.
This candidate changes propagation of **existing validation errors**; it is not
a redesign or full validation of every field shown in the documentation schema.
No product source was read/copied. No consumer pin, push, merge, publication,
deployment or PR mutation is part of this repair.
