# B1 local failed-job search — 19 September 2026

**Result:** the local archive search found no complete, representative bundle
of an original failed translation attempt and its refusal evidence. A real-job
recovery rate remains unmeasured. The
[data request](../design/B1-line-wrapping/FAILED-JOB-REQUEST.md) was sent to
**Boot Spire Tech web app** after Rodrigo explicitly authorized it. Its
[reply](2026-09-19-b1-product-inputs.md) reports no eligible replayable real
failed-job bundle; no cases were exported. Its product evidence paths were not
opened here.

<details>
<summary>Technical detail (skip freely)</summary>

The [inventory](data/2026-09-19-b1-local-inputs.json) records 12 saved mapping
paths, their SHA-256 values, nearby PDFs, and whether their referenced font
paths exist. It does not claim that every nearby PDF is the matching source,
or that missing historical font paths mean the fonts cannot be recovered.

| Saved mappings | Finding | Use for recovery measurement |
| --- | --- | --- |
| 3 school-permission mappings | Two final variants and one byte-identical copy; the two variants already rebuilt in the preceding probe | No current overflow refusals |
| 1 FL-150 Japanese mapping | The job README identifies reviewed v2 wording with 13 merges; source PDF is not beside the mapping and historical font paths are absent | An archived final job, not the retained original failure |
| 8 one-core mappings | Determinism, path, structural, scorer, and finish regression fixtures | Synthetic checks, not representative translation attempts |

The search covered mapping/refusal/report filenames within this repository,
including ignored local runs. It excluded Git internals, dependency/runtime
directories, checkout copies, and the new B1 probe outputs. Mapping contents,
adjacent filenames, and the FL-150 job README were inspected. No product
repository content was opened. A filename-based search can miss differently
named or externally stored inputs; this is a local availability finding, not
proof that the original failed jobs never existed.

The history check was:

```powershell
git log --all --oneline -- 'dev/jobs/*/translations.json' '**/translations*.json'
```

It returned only `bf96f65`, the FL-150 archive commit, among the local refs
searched. No earlier failed mapping was found by that check. The final FL-150
mapping was not changed or rebuilt to manufacture an overflow case.

PRs #12 and #13 were queried read-only with `gh pr view`; they remain open at
`abc47674019aaed8f61b716b83e3d289e38d1f1c` and
`1d4f9707c4d9934fbc88d8f25576ac304b9bb139`, respectively. Work remains local and
uncommitted on `codex/b1-design-canvas`. No implementation plan, library edit,
push, or merge was performed in this follow-up.

</details>
