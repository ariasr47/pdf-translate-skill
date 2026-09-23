# A04: concurrency guidance correction

20 September 2026 · documentation slice complete locally; A04 remains partial

The [consumer guide](../../pdf-translate/references/consumer-guide.md#concurrency-and-logging)
now directs concurrent PDF work to separate processes with private job folders
and output/report paths. Silent `run_*` calls fix stdout interference; they do
not establish native-backend thread safety. The skill reference, console/verify
docstrings and historical concurrency-test docstring carry the same distinction.

This is the first small item Rodrigo authorized after backlog grooming. The
four version sources advance together from 58 to 59 because shipped skill
instructions changed. The version-lockstep assertion was updated accordingly.
There is no PDF execution-logic change or process-worker implementation here.

## Evidence

[PyMuPDF's multiprocessing documentation](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html),
checked 20 September, explicitly excludes multithreaded use and recommends
multiprocessing. Its example opens the PDF inside the worker from its filename.
The library's private job/output paths also address its own fixed-name artifacts;
changing only `scale_report=` is insufficient isolation for the whole workflow.

From `pdf-translate/`, using this repo's existing Windows virtual environment:

```powershell
$env:PYTHONUTF8='1'
& '..\pdf-translate.venv\Scripts\python.exe' -m unittest tests.test_verify_report.VersionLockstepTests -v
```

Result, exit 0:

```text
test_four_version_sources_agree ... ok
Ran 1 test in 0.194s
OK
```

Additional checks from the repository root:

- `git diff --check`: exit 0, no output.
- Added-link/anchor inspection: **6 local targets resolve**. All **15** files
  touched by this slice retain CRLF line endings.
- An AST comparison against this turn's before-images passed for all **five**
  edited Python files. It removed module/class/function docstrings, normalized
  only the explicit version assignment and version-test expectation from 59
  back to 58, and compared the parsed trees. Result: **no execution-logic
  changes**. The before-images remain in ignored
  `runs/a04-concurrency-docs-2026-09-20/before/`; they preserve the pre-existing
  dirty state as well as the shipped files this slice edited.
- `rg -n 'thread-safe surface|what is safe to call from a thread' pdf-translate`:
  exit 1, no matches. The older affirmative wording in the dated E3 plan is
  historical; the current consumer guide and A04 supersede it. Earlier decision
  rows and request history were preserved, with a new decision and current
  request qualification rather than rewriting their past evidence.

Fresh read-only git/GitHub checks before editing found:

| Surface | Verified state |
| --- | --- |
| Working branch / committed HEAD | `codex/b1-design-canvas` / `1d4f9707c4d9934fbc88d8f25576ac304b9bb139` (v58) |
| Remote main | `a5629fbd6bc084f9ab849ae3db74992c15807fcc` (v56) |
| PR #12 | OPEN; head `abc47674019aaed8f61b716b83e3d289e38d1f1c`; base `main` |
| PR #13 | OPEN; head `1d4f9707c4d9934fbc88d8f25576ac304b9bb139`; base `feat/terminology-loop` |

Commands: `git branch --show-current`, `git rev-parse HEAD`,
`gh api repos/ariasr47/pdf-translate-skill/branches/main --jq '.commit.sha'`,
and `gh pr view 12` / `gh pr view 13` with JSON fields
`state,headRefOid,headRefName,baseRefName,url`. These checks do not update PRs.

## Remaining scope

A04 stays **partial** in the [canonical backlog](../../dev/goals/PROGRAM.md#public-readiness-backlog).
Replace unsupported thread-based PDF concurrency checks with process-isolated
jobs and verify both outputs, verdicts and paths; retain stdout-isolation
regression coverage. This slice did not run those workers, rerun the full suite,
or validate a consumer's service integration. Worker integration remains app-owned.

The next smallest recommendation is A06's mapping-aware verification examples.
It has not been started. No commit, push, merge, release, PR edit, app-task
message or product-source access occurred. B1 remains deferred; previous local
B1 and audit work is preserved. This finding does not establish the cause of the
user-reported Codex crash.
