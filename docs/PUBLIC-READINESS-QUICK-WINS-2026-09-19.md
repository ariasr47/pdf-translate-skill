# Public readiness: smallest useful items

19 September 2026 · shortlist from the [audit](reviews/2026-09-19-public-readiness.md)

**20 September follow-up:** the first three small slices are complete locally:
A04's concurrency wording, A06's verification examples and A15's README facts.
Their broader items remain open. Next: A21's explicit validation of both
manifests. See the [concurrency evidence](reviews/2026-09-20-concurrency-guidance.md),
[verification-example evidence](reviews/2026-09-20-verification-examples.md),
[README evidence](reviews/2026-09-20-readme-facts.md), and
[current backlog](../dev/goals/PROGRAM.md#public-readiness-backlog).

**Original recommendation:** correct concurrency guidance first, then the verification
examples. Both reduce misleading assurances with a small, reviewable edit. The
first small code fix should be invalid review data permitting delivery.

The [current backlog](../dev/goals/PROGRAM.md#public-readiness-backlog) contains
the full A01–A26 entries, links to existing work, and observable completion
checks. This document is a dated shortlist, not a second status tracker or an
implementation plan. **The original 19 September backlog update performed no listed fix.**

## Smallest documentation and tooling slices

XS means a focused edit plus a local check; S means several related edits or a
bounded code change plus targeted verification. These are estimates, not time
promises. Each row below is deliberately narrower than its parent backlog item.

| Suggested order | Item / backlog link | Size | What would visibly improve | Verify by |
| --- | --- | --- | --- | --- |
| **1** | **Correct thread-safety wording — A04, docs slice** | XS | Consumer guidance stops promising safe parallel PyMuPDF work in threads; it distinguishes logging isolation and recommends process-isolated jobs. | Compare the guide/docstrings with [PyMuPDF's guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html); search for remaining unconditional thread-safety claims. Process-worker validation remains open under A04. |
| **2** | **Supply mapping context in verification examples — A06, docs slice** | XS | Quickstart, hot-loop and Python examples pass the mapping, use a target-script fill sample when relevant, and verify the final artifact. | Run the saved two-label/empty-target case through the revised command; it must report `empty-targets`, exit 1. Changing default `rebuild` behavior is the separate code slice. |
| **3** | **Correct small README facts — A15, facts slice** | XS | Font count matches the 11 configured faces; test instructions select the full suite; dependencies use the declared requirements; old timing is clearly dated. | Compare commands/counts with current files, check links and inspect the existing full-suite discovery record. This does not require a new benchmark. |
| **4** | **Validate both Claude manifests explicitly — A21, manifest slice** | XS | CI contains separate validation commands for the marketplace and plugin, matching the two locally verified checks. | Both `claude plugin validate . --strict` and `claude plugin validate .claude-plugin/plugin.json --strict` return 0. Hosted execution remains pending its billing prerequisite. |
| **5** | **Align type-check configuration — A21, environment slice** | XS–S | The configuration resolves the actual project environment and targets the stated minimum Python syntax/API support. | Run the configured checker/import-resolution check and record pre-existing diagnostics separately. Resolving every type warning is outside this small slice. |
| **6** | **State the skill's instruction trust boundary — A18, wording slice** | XS | PDF text, metadata, websites and review files are explicitly data, not instructions to change tools, disclose secrets or take unrelated actions. | Inspect the main workflow for the rule and link to a harmless evaluation fixture. A passing adversarial host run is separate A18/A22 work, not implied by adding prose. |
| **7** | **Document the already-proven local Codex install route — A16, local slice** | S | A new user can copy/install the complete skill into the documented location, set up dependencies, discover it and identify its version. | Repeat the isolated `.agents/skills/pdf-translate` discovery check using the written instructions. Do not claim untested plugin/cloud installation or translation quality. |

These are small slices, not permission to mark their whole parent item complete.
In particular, clearer concurrency text does not fix an app worker pool, and
better verification examples do not change the default rebuild command.

## Small code fixes after the documentation

| Recommended priority | Item | Size | Concrete completion check |
| --- | --- | --- | --- |
| **First** | **A01 — refuse invalid review state** | S | `review.json = {}` and malformed findings produce an error and no new final PDF through normal `finish`; explicit bypass remains disclosed. Run focused review tests and the audit probe. |
| Next | **A06 — pass mapping context by default in rebuild** | S | The default rebuild of the empty-target fixture changes from a false pass to exit 1 with the expected finding; explicit options and normal valid jobs still behave correctly. |
| Next | **A10 — remove the non-form temporary-file leak** | S | Form/non-form success and failure fixtures leave the intended output and no unintended `.tmp_withfont.pdf`; fields/output remain intact. |
| Next | **A09 — reject invalid override selectors cleanly** | S | Empty/missing/wrong-type selectors produce a clear mapping error; valid overrides still render correctly without the unbound-variable failure. |

Font/rendering/layout changes require an independent real-run check under the
standing rules. That verification is part of the work, even when the edit looks
like a one-liner. No code fix here is authorized to change PRs #12/#13.

## Small-looking work that should not be treated as a quick win

- **A02 page-count completeness:** counting pages is easy, but verifier results,
  unmatched-page inspection and geometry cases must agree. It is high priority
  and sized M; it does not require implementing B1 wrapping.
- **A03 stale artifacts / A14 review freshness:** require a coherent decision
  about current-attempt identity and what happens to a prior successful output.
- **A05 dependency minimum:** changing a version string is easy; proving the
  supported floor across relevant environments is the actual work.
- **A07 licensing / A08 package identity:** involve owner decisions; no automatic
  relicensing, name reservation or publishing.
- **A11 all CLI parsers / A17 shortening the skill:** broad consistency edits
  need compatibility checks; avoid disguising them as a one-file cleanup.
- **A23 hostile input / A25 large-function refactoring:** keep separate from
  quick cleanup and behind the relevant correctness work.

All engine/skill work remains owned here. App service integration and product
policy remain app-owned; no message or assignment was sent to that task. B1's
real-failure evidence prerequisite and deferral remain unchanged.
