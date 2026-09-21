# Typography preservation: approved design

20 September 2026 · **written design approved**; implementation plan awaits review

[Read the API design](DESIGN.md) or the [short implementation plan](../../plans/2026-09-20-typography-preservation-brief.md).
No implementation or delivery pin exists yet.

| What changes | Approved result |
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

The approved boundary and association rules are detailed in the API design.
The implementation plan contains tasks, interfaces, commands and acceptance
checks. Review that plan and select an execution method before implementation.
No product source was accessed and no message was sent to the app task.
