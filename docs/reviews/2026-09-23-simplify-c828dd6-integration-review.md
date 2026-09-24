# Independent review: c828dd6 and the combined A01/A03 candidate

Date: 2026-09-23. Reviewer: Codex.

## Outcome

The P3 JSON-null finding is closed. **Approve the cleanup and local combined candidate: no remaining actionable review findings.** Both full suites passed, as did the parity/API checks and the combined workflow. This approves the tested upstream changes; it does not publish a release or adopt it in the consumer.

## Exact revisions

| Component | Revision |
|---|---|
| Baseline / remote main | b20fadda832b673b61ce8bc4a5f17189edd58209 |
| Cleanup | c828dd606be40b7f18de67f1727fea1e596b722e |
| A01 | c4484b721d600027af00bf5567d4795c80acd641 |
| A03 | 2249171e63f0a4d094fb597854c46835e115557b |
| Local combined candidate | e2972cfc72c59cec2cdcec9c1299701b03042f01 |
| Combined tree | 5d1063ae2a4f681c71d7e8ccbc46a634bd208d04 |

The combined candidate is on `codex/simplify-integration-review` in:

`C:/Users/rodri/.codex/worktrees/simplify-integration-review/pdf-translate-skill`

It contains cleanup, A01 and A03, joined by two local merge commits. No source code was manually changed during integration. The three supplied branches remained clean and at their supplied revisions. The original dirty checkout was preserved; only this report and review evidence were added there.

At completion of the independent review, remote main was checked with `git ls-remote origin refs/heads/main` and still pointed to b20fadd; there were no open PRs and nothing had been pushed. The later authorized PR and merge steps are recorded below. No release, deployment, version bump or consumer pin change has been performed.

## P3 correction

The private `_UNREAD` object distinguishes a failed read from every successfully parsed JSON value. `_read_segments` and single-parse reuse remain in place. Parsed `null` again reaches the same baseline failure path as other non-object values. This preserves a known baseline defect; it does not claim to improve capture of malformed document shapes.

Independently ran real builds that replace `segments.json` after the build has read its input. Five payloads were tested in both a refusing build and a successful near-floor build, on complete baseline, cleanup and combined checkouts:

| Payload | Baseline, cleanup and combined |
|---|---|
| `null`, `[]`, `"nope"`, `5` | No capture manifest; baseline AttributeError diagnostic preserved |
| Truncated `{` | One manifest, with explanatory position note |

For every payload, refusing builds still raise PlacementError with exit 1 and no output PDF. Near-floor builds still succeed and write their PDF. All ten normalized outcome records, including final diagnostic lines and position notes, match baseline exactly. This extends the supplied five-case refusal check to near-floor capture as well.

## Fresh results

| Check | Cleanup | Combined |
|---|---|---|
| Full unittest discovery | **656 OK, 424.546s** | **670 OK, 415.713s** |
| Capture suite | **24 OK, 2.850s** | Included in combined discovery |
| CLI runner against baseline | Empty stdout/stderr diffs | Empty stdout/stderr diffs |
| Verdict runner, nine fixtures | Empty stdout/stderr diffs | Empty stdout/stderr diffs |
| Full serialized verdicts, nine fixtures | Identical | Identical |
| Public API inventory | Identical | Identical |
| Ten capture failure-path outcomes | Identical | Identical |

API inventory: 48 public package names (39 explicit `__all__` entries), 237 public module-defined callables excluding private dependency-preflight helpers, 19 result dataclasses and five schema entries. Including the private preflight helpers yields 240 callables, also unchanged. Public signatures, dataclass fields/defaults/flags, schema definitions and serializer definitions were compared.

The runners normalize paths/timing according to their existing implementation. The additional comparison removes only their `# package:` provenance line from stderr. Raw outputs retain those lines to identify each imported checkout. API snapshots normalize process-specific object addresses. No observed behavioral difference is removed by the reviewer-side comparison.

The combined candidate intentionally includes A01 and A03 behavior fixes. Passing ordinary CLI/verdict fixtures does not mean those fixes are behavior-neutral: invalid reviews now refuse delivery and failed rebuilds invalidate previous success reports.

Both full runs have zero failures, errors and skips. Existing ResourceWarning messages remain visible in the logs and are not introduced by the capture correction. The combined worktree is clean at completion. Its full run began on the already-resolved working tree immediately before the merge commit was recorded; the tested file contents are the committed tree above, and no source files changed during the run.

## Combined workflow and merge review

A real CLI sequence was run in both legacy and typography formats using one reused job directory per format:

1. Successful rebuild: exit 0, fresh verification report.
2. Write an invalid empty-object review; finish: exit 2, review errors recorded, no final PDF or comparison HTML written.
3. Corrupt the mapping; rebuild: exit 1, previous success report removed, prior output PDF preserved byte-for-byte.
4. Restore the valid mapping; rebuild: exit 0, fresh verification report written.

All checks passed in both formats. These are real subprocess runs; no pipeline stages were mocked.

The trial integration found **two** documentation conflicts, not just one: `docs/DECISIONS.md` and `dev/goals/HANDOVER.md`. All three new decision rows were preserved in date order. Both handover sections were preserved, A03 followed by A01, ahead of the unchanged baseline history. A reconciliation script asserted that these edits consist only of the original branches' added rows/sections.

`pipeline.py` and `test_typography_pipeline.py` merged automatically. The resulting production-code diff was read: A01 changes review refusal/diagnostics, A03 changes rebuild report invalidation, and cleanup's argument helper remains intact. Git confirms all three supplied heads are ancestors of the combined head. `git diff --check b20fadd..HEAD` passes.

## Reproduction and evidence

Evidence directory:

`C:/Dev/pdf-translate-skill/runs/simplify-review-c828dd6`

Interpreter: `C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`, Python **3.14.0**. Each run sets PYTHONPATH to the checkout being tested. The fresh combined worktree received the existing repository test font files; no dependencies or package versions were changed.

```powershell
$env:PYTHONPATH='<checkout>/pdf-translate'
& C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest discover -s '<checkout>/pdf-translate/tests' -t '<checkout>/pdf-translate'
```

Logs: `full-cleanup.log`, `full-combined.log`, `capture-cleanup.log`.

Run these once for each baseline/cleanup/combined checkout, using separate scratch output paths and the stated interpreter:

```text
<checkout>/dev/probes/cli_parity_runner.py <fresh-job-dir> --font <cleanup>/pdf-translate/tests/fonts/NotoSans-Regular.ttf
<checkout>/dev/probes/verdict_parity_runner.py C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/gate-fixtures
C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/api_snapshot.py <output-json>
C:/Dev/pdf-translate-skill/runs/simplify-review-041447e/structured_verdicts.py <same-gate-fixtures> <output-json>
C:/Dev/pdf-translate-skill/runs/simplify-review-c828dd6/capture_payloads.py <fresh-job-dir> <font>
```

`compare_results.py` records both comparisons in `comparison.json`; all fourteen comparisons are equal with zero-byte diffs. Raw files are named by check and revision label. `combined_workflow.py` writes `combined-workflow.json` and retains real CLI logs and job artifacts. `resolve_integration_docs.py` records the exact conflict-resolution method.

## Next step

Use the existing combined candidate for upstream integration/release preparation; no second throwaway merge or additional broad simplification pass is needed. Select the release version against current upstream state and verify any subsequent code changes. Publication and PDF Translator's exact-pin adoption remain separate steps. The deferred rendering/font/shaping findings and pre-existing behavior bugs are outside this cleanup approval.

The PDF Translator task **Approve sandbox proposal** was updated with these results and asked for its next upstream priority. It recommends integration/PR preparation, reports no new upstream engine blocker from its sandbox work, and keeps A02/A06 separate. Final coordination clarified that upstream metadata already requires **Python >=3.14**, while the app remains on Python 3.12/library v54. Eventual adoption needs an isolated supported Python 3.14/exact-candidate comparison, preserving the current Japanese-only imported route and document-erasure/job-lifetime behavior, and comparing rendered output against the existing pin using identical translation inputs. Those consumer checks have not been performed by this review; no runtime or pin change is authorized or implied. The hosted sandbox subsequently completed without a new upstream blocker.

## PR coordination, later on 23 September

Rodrigo authorized final review coordination and a scoped PR through the PDF Translator task. That reviewer confirmed the unchanged combined commit/tree, found no remaining blocker, and independently reran **88 focused tests OK in 17.431s**, plus both real combined workflows. New evidence is in `C:/Dev/pdf-translate-skill/runs/consumer-coordination-review-20260923/`.

The exact candidate was pushed as `origin/codex/simplify-integration-review` and [PR #22](https://github.com/ariasr47/pdf-translate-skill/pull/22) was opened against main. The initial remote head was e2972cf; main remains b20fadd. The PR includes both reviewers' evidence and the distinction between behavior-preserving cleanup and intentional A01/A03 failure-behavior fixes.

Final PR-readiness review identified that GitHub's enumerated test command omitted `tests.test_rebuild_attempt` and `tests.test_retypeset_capture`. CI-only follow-up **b39079fdfd3048da4dde1ec1f4981deff74451c1** adds exactly those modules to the existing Ubuntu/Windows Python 3.14 command, preserving every previous module. No other file differs from e2972cf. The coordination reviewer independently confirmed the one-line diff, clean worktree and exact remote head, and approved the follow-up. Its review is in `runs/consumer-coordination-review-20260923/REVIEW.md`.

CI run **35889556779** on b39079f completed: Linux passed **670 tests in 761.317s**, **15 canary tests**, and fixture generation; plugin validation passed. Windows discovered **670 tests in 901.375s**, with **9 errors and one skip**. All nine errors were A01 test assertions reading UTF-8 `review_state.json` through locale-default `Path.read_text()`, which used CP1252 on the hosted Windows runner and raised UnicodeDecodeError. The production refusal/delivery assertions before those reads passed. The skip was the existing relative-report-path test, where the temporary directory was on another drive.

Focused test-only follow-up **7eeccf2b19a7fd05ba283fb06dd7ee8642e32795** changes exactly five readers to `read_text(encoding='utf-8')`: four in `test_review.py`, one in `test_typography_pipeline.py`. All assertions are preserved. No production code or global CI encoding changed. Local reproduction with `python -X utf8=0` confirmed `locale=cp1252`: before the fix, the 16 refusal tests reproduced all nine errors; after it, the same 16 passed in 1.073s and the wider **99-test** review/rebuild/capture/typography suite passed in 36.287s. Evidence: `windows-locale-{red,green,focused99}.log` under the main evidence directory. The coordination reviewer independently approved the exact five-line fix and passed **27 tests** under CP1252 in 18.593s (`runs/consumer-coordination-review-20260923/windows-encoding-fixed.log`).

Why local discovery missed it: this task's default environment has `PYTHONUTF8=1` / `sys.flags.utf8_mode == 1`, even though the locale encoding is CP1252. The hosted Windows process exposed the locale-default reads. The repair matches the existing `_write_review_state` writer's explicit UTF-8 encoding; it does not change the format or hide the issue with a CI environment override. Under `-X utf8=0`, the remaining short CI stages also passed locally: **15 canary tests in 0.664s** and generation of both evaluation fixture PDFs.

PR head is **7eeccf2b19a7fd05ba283fb06dd7ee8642e32795**. Fresh final-head [CI run 35891927585](https://github.com/ariasr47/pdf-translate-skill/actions/runs/35891927585) **passed all three jobs**:

| Final-head check | Actual job result |
|---|---|
| Ubuntu / Python 3.14 | 670 tests OK in 588.107s; 15 canary tests OK in 0.641s; both evaluation fixtures generated |
| Windows / Python 3.14 | 670 tests discovered, OK (skipped=1) in 879.772s; 15 canary tests OK in 1.147s; both evaluation fixtures generated |
| Plugin manifest | Plugin/marketplace validation and version-source agreement passed |

No failures or errors remain. The Windows skip is the existing cross-drive relative-report-path case, not an omitted regression suite. Raw final logs: `ci-linux-7eeccf2.log`, `ci-windows-7eeccf2.log`, `ci-watch-7eeccf2.log`; run metadata: `ci-final-7eeccf2.json`, all under the main evidence directory. The exact remote head and clean local worktree were rechecked; at PR-preparation completion GitHub reported the PR OPEN and merge state CLEAN, with main still b20fadd. Production code still matched independently reviewed e2972cf byte-for-byte. **Review and PR preparation were complete.** Merge authorization followed, as recorded below.

Both reviewers confirmed the updated workflow's 21 selected modules exactly match the 21 top-level `test_*.py` modules, with none omitted. After this PR, the recommended separate implementation priority is **A02** (legacy missing/extra-page acceptance), then **A06** (legacy rebuild mapping context). Consumer adoption remains the supported-runtime migration/comparison task above.

## Authorized merge, 23 September 2026

Rodrigo explicitly requested “merge”. Both coordinating tasks checked the reviewed head **7eeccf2b19a7fd05ba283fb06dd7ee8642e32795**, passing checks and clean mergeability. The PDF Translator task completed the merge with an exact-head guard. This task's matching guarded command returned that PR #22 was already merged; independent read-only checks then confirmed:

```text
gh pr view 22 --json state,mergedAt,mergeCommit,headRefOid,url
state: MERGED
mergedAt: 2026-09-23T17:15:44Z
headRefOid: 7eeccf2b19a7fd05ba283fb06dd7ee8642e32795
mergeCommit: 178a06ffd4e45af30c0366c5f0fb995f8495cb5f

git ls-remote origin refs/heads/main
178a06ffd4e45af30c0366c5f0fb995f8495cb5f refs/heads/main
```

PR #22 is now integrated into remote main. The verified CI results above belong to the reviewed PR head; no new test run is claimed for the merge commit. No release, version bump, deployment or consumer pin/runtime change was made. The original dirty B1 checkout was preserved, and the separate A02/A06 priorities remain pending.
