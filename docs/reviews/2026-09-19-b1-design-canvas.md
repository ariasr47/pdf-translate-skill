# B1 canvas — evidence and scope, 19 September 2026

Design artifact: [canvas and choices](../design/B1-line-wrapping/README.md).
This records read-only checks, not a renderer verification or a corpus probe.

## State checked before authoring

Commands ran in `C:\Dev\pdf-translate-skill` and exited 0. `gh` was invoked
through `C:\Users\rodri\tools\gh\bin\gh.exe`.

| Command | Observed output |
| --- | --- |
| `git status --short --branch` | `## feat/consumer-surface...origin/feat/consumer-surface`; no changed files. |
| `git log -5 --oneline` | HEAD `1d4f970`, the Codex handover commit. |
| `git branch -vv` | Local `main` `bacc436`, behind `origin/main` by one commit. |
| `gh repo view --json nameWithOwner,defaultBranchRef,url` | `ariasr47/pdf-translate-skill`, default branch `main`. |
| `gh api repos/ariasr47/pdf-translate-skill/commits/main --jq '.sha'` | `a5629fbd6bc084f9ab849ae3db74992c15807fcc`. |
| `gh api repos/ariasr47/pdf-translate-skill/commits/a5629fbd6bc084f9ab849ae3db74992c15807fcc --jq '{sha: .sha, message: .commit.message, files: [.files[].filename]}'` | `ci: cancel superseded runs on the same ref (#14)`; only `.github/workflows/tests.yml` changed. |
| `gh pr list --state open --json number,title,headRefName,baseRefName,headRefOid,url,mergeable,statusCheckRollup` | #12 `abc4767`, `feat/terminology-loop` → `main`; #13 `1d4f970`, `feat/consumer-surface` → `feat/terminology-loop`; both MERGEABLE, both with FAILURE checks. |

The handover's remote-main claim was stale. The newly observed #13 check run
is `35433169821`; #12 is `35432185828`. This session did not inspect billing
annotations, rerun jobs, or claim that previous local test totals still pass.

`git switch -c codex/b1-design-canvas` then exited 0. The canvas is local and
uncommitted on that separate branch. No PR branch, remote ref, or PR was edited.

## Source checks used to bound the proposal

`rg -n` searches and numbered `Get-Content` excerpts read this repository's
files only. The following are source observations at `1d4f970`, not new runs:

| Evidence location | What it establishes |
| --- | --- |
| `pdf-translate/pdf_translate/retypeset.py:90`, `:760`, `:1332`, `:1378` | Floor `0.7`; scaled runs are recorded; explicit exceptions exist; ordinary width fitting changes size and appends text on the original y-coordinate. |
| `pdf-translate/pdf_translate/retypeset.py:209` | The Story line path is deliberately a single-line baseline box; a call to `insert_htmlbox` is not itself proof of useful multi-line wrapping. |
| `pdf-translate/pdf_translate/retypeset.py:781`, `:791`, `:844` | Merge matching consumes source text in order; the loop has no requirement that a merge contain at least two lines, and a single baseline has a fallback leading. A one-member merge is therefore a source-level possibility worth distinguishing from a missing renderer; it was not exercised here. Repeated-string selection remains a design concern. |
| `pdf-translate/pdf_translate/retypeset.py:1419`, `:1427`, `:1463` | Authored merge boxes are used as given; merge and notice paths call `insert_htmlbox`. |
| `pdf-translate/references/translations-format.md:44`, `:54`, `:62` | Explicit merge authoring and boxes are already documented; the current workflow does not promise box collision checks. |
| `pdf-translate/pdf_translate/retypeset.py:1510`, `:1539` | Overflow closes the document and raises a structured build refusal before saving. There is no source-language fallback here. |
| `pdf-translate/pdf_translate/verify.py:1340`, `:1373`, `:1380`, `:1391`, `:1852` | Gate 19 reads delivered geometric stacks, counts even exempt lines, returns no result when none are judged, and emits PASS or REVIEW when lines are judged; `run_verify` calls it. It does not know which breaks this build introduced. |
| `docs/REQUESTS-from-product.md:50`, `:56` | R5 leaves advisory verification to the consumer; R6 does not authorize obstacle-bounded placement. |

No source was opened in `C:\Dev\pdf-translator`. No product measurements
were presented as independently reproduced. No universal Story-engine or
language-standard conformance claim was inferred from past probes.

## Artifact review and stop

The generated image was visually inspected: it draws the four required
choices, labels itself schematic, separates fixed boxes from automatic growth,
and marks the recommendation as pending. Its abstract text bars are not font
or rendering evidence. The README supplies the scope limits, alternatives,
unknowns, and observable outcomes with verify-by methods.

No pipeline, reference, test, corpus, dependency, or version file was changed.
No tests or corpus probes were run for this documentation-only delivery.
No implementation plan was written. B1 behavior awaits the operator's ruling.

## Follow-up — no added pages

The operator subsequently required that the translated PDF not have more pages
than the source and asked to save the artifact in docs. The existing PNG was
confirmed at `docs/design/B1-line-wrapping/canvas.png` (1,529,980 bytes); it is
preserved. The accompanying README now records the requirement, recommends
exact page-count preservation and same-page placement, and names a verify-by
method for successful fits and last-page overflow. This is a design constraint,
not a new implementation or test result. The remaining canvas choices are open.

The constraint is recorded in DECISIONS and the current handover. Read-only git
and gh checks confirmed the same local branch and unchanged PR #12/#13 heads
before these documentation edits.

## Follow-up — recommended direction approved

Rodrigo then said “yes proceed with the recommended” and requested a short note
to relay to the web-app session. The approved direction, including exact page
count and same-page placement, is appended to DECISIONS and reflected in the
canvas README and handover. `docs/design/B1-line-wrapping/WEB-APP-NOTE.md` is the
requested note. It distinguishes the design ruling from an available API or
implemented capability. The original PNG remains the pre-ruling artifact.

No note was sent to another session, and the product repository was not opened.
No corpus probe, implementation plan, or pipeline change was made. Read-only
git and gh checks again showed branch `codex/b1-design-canvas` and the unchanged
#12/#13 heads. Documentation whitespace was checked with `git diff --check`.
