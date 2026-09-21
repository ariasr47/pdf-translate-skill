# Typography implementation: plan review

20 September 2026 · design approved · **plan awaiting review**

[Detailed implementation plan](2026-09-20-typography-preservation.md)
is the canonical task list. This page is its short review summary.

**Outcome:** preserve serif/sans class and meaningful bold/italic within eligible
translated lines, keeping the original page count and first baseline. Cases
outside the approved scope refuse explicitly.

| Stage | What it delivers |
| --- | --- |
| 1–2 | Exact source styles and occurrence identities; reject stale or ambiguous mappings. |
| 3–4 | Correct font faces and one-line placement with the existing scale floor. |
| 5–7 | Inspect final PDF typography; carry every occurrence through QA, review and commands. |
| 8 | Independent rendering checks, repeated-label cases and old-format compatibility. |
| 9 | Verified capability discovery and actual installed workflows in Claude and Codex. |

**Recommended execution:** one implementation session, with an independent
reviewer running and inspecting the rendering checks before completion.
The tasks share closely connected interfaces, so this keeps coordination small.
The alternative is a new implementer/reviewer pair for every task.

The plan includes exact files, interfaces, test cases, commands and stopping
conditions. It starts in an isolated branch so earlier uncommitted work stays
intact. No implementation has started; planning checks only validated document
structure and the source fixture's two repeated lines/four font identities.

**Acceptance limits:** genuine fonts and both skill hosts must be exercised;
missing resources remain unverified. A01 invalid-review delivery remains a
separate public-readiness prerequisite. B1 and app migration remain separate.

Approval here permits the chosen implementation method. Push, merge, release
and app changes still require separate authorization.
