# Typography implementation: plan review

20 September 2026 · design and plan approved · **native execution underway**

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

**Approved execution:** one implementation session, with an independent
reviewer running and inspecting the rendering checks before completion.
The tasks share closely connected interfaces, so this keeps coordination small.
The alternative is a new implementer/reviewer pair for every task.

The plan includes exact files, interfaces, test cases, commands and stopping
conditions. It starts in an isolated branch so earlier uncommitted work stays
intact. Implementation is underway; [the execution record](../reviews/2026-09-20-typography-implementation.md)
separates completed checks from acceptance work still pending.

**Acceptance limits:** genuine fonts and both skill hosts must be exercised;
missing resources remain unverified. A01 invalid-review delivery remains a
separate public-readiness prerequisite. B1 and app migration remain separate.

Rodrigo's approval permits this implementation method. Push, merge, release
and app changes still require separate authorization.
