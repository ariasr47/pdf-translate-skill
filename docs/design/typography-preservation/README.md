# Typography preservation: review the proposed design

20 September 2026 · additive approach approved; **written details await approval**

[Read the API design](DESIGN.md). No implementation or delivery pin exists yet.

| What changes | Proposed result |
| --- | --- |
| Extraction | Keep each source style run and its exact occurrence, instead of only whole-line bold/italic flags. |
| Translation | The author links target runs to source runs, allowing word order to change while preserving emphasis. |
| Fonts and placement | Select serif/sans plus the needed role for each run; reuse placement with the same page count and baseline. |
| Invalid input | Unknown styles, stale IDs and ambiguous associations are reported; no silent legacy fallback. |
| QA and review | Read the same occurrence/run data and check the final PDF, including repeated text. |

**First-scope boundary:** horizontal single-baseline page text, one size/color per
segment, source/target Latin, Japanese or Simplified Chinese. Legacy merges,
overrides, list markers/dot leaders, added notices, rotation and other scripts
are refused in the new mode. Legacy calls retain their existing behavior.
Documents outside that boundary remain ineligible for adoption under the
unchanged product typography promise; it is not permission to discard styles.

The library owns this capability. The app owns font provisioning, orchestration,
its five compatibility failures and migration/adoption evidence. B1 remains
separately deferred. A01 invalid-review delivery and A03/A14 lifecycle/freshness
work are explicitly distinguished from this design's new-format checks.

Review the boundary and association rules first; the detailed document contains
API shapes, error behavior and observable future acceptance checks. Approval of
the written design permits writing an implementation plan, not executing one
that has not been reviewed. No product source was accessed and no message was
sent to the app task.
