# B1 captured case - independent inspection

**Result:** the requested bundle arrived and passed integrity and PDF geometry
checks. It contains a known successful one-page FL-150 Japanese translation,
not a new failed job. The capture is complete; **B1 recovery remains untested**.

**Recommendation:** retain the approved design and this reproducible example.
Further recovery measurement needs a genuine failed attempt and permitted
wrapping areas. Replaying this success again will not supply that evidence.

<details>
<summary>Technical detail (skip freely)</summary>

## Retained evidence

Bundle: `runs/b1-real-jobs/20260919-webapp-fl150-page1-opus-01/`.
It contains the source and output PDFs, original and font-relocated mappings,
font and OFL/provenance, extraction geometry, occurrence records, original
stage logs, scale and verification reports, and hashes. No product source or
implementation was read. Original paths inside the product are provenance
strings only and were not followed.

The bundle records **library 54.0.0** at upstream commit
`9675c6196c14eb2a2d37d34e371391eb1955a386`, not this checkout's v58. The commit
exists in this repository. No placement rerun was performed here, so the stage
return codes and the installed runtime's identity remain captured evidence,
not an independently reproduced v58 result.

The input was already a **one-page excerpt**. Its printed "Page 1 of 4" label
does not make this a four-page test. This 86-entry FL-150 mapping is distinct
from the two 25-entry, two-page school-permission mappings rebuilt in the
earlier probe. The product task's earlier suggestion that these were the same
jobs must not be used to deduplicate the evidence.

## Independent checks

An inline, read-only Python audit ran through
`.\pdf-translate.venv\Scripts\python.exe -` from the repository root, using
PyMuPDF 1.28.2, and exited **0**:

```text
PASS: 27 bundled file hashes; 5 input hashes; font-path-only mapping change
PASS: one page in/out; all 61 widget names, types and rectangles match
CONFIRMED: 86 entries; 97 occurrences; all wrapping permissions unknown
RECORDED, not rerun: v54 build; verify 13 PASS / 3 REVIEW; 8 shrinks, min 0.844
```

The audit checked every manifest path stayed inside the bundle, byte lengths
and SHA-256 hashes, all five input hashes, and deep equality of the two mappings
after changing only `fonts.regular`. It checked the effective font path points
to the identical bundled font. Identity to the inaccessible product originals
is reported by the exporting task; the independently checked relationship is
between the retained copies and their manifests.

PDFs were opened directly to compare page counts, page rectangles, and widget
names, types and rectangles (rounded to 0.0001 pt). All 97 occurrence records
explicitly mark wrapping permission unknown and the approved box null. The
source bboxes are not permissions. [Raw audit](data/2026-09-19-b1-captured-case-audit.json)
and [retained file manifest](data/2026-09-19-b1-captured-files-manifest.json).

Both complete pages were separately rendered with Poppler and visually
inspected at 144 dpi. From the repo root, these commands exited **0**:

```powershell
pdftoppm -png -r 144 -singlefile runs/b1-real-jobs/20260919-webapp-fl150-page1-opus-01/source.pdf runs/b1-real-jobs-audit-2026-09-19/source-144dpi
pdftoppm -png -r 144 -singlefile runs/b1-real-jobs/20260919-webapp-fl150-page1-opus-01/output.pdf runs/b1-real-jobs-audit-2026-09-19/output-144dpi
```

The invoked executable was the bundled Poppler `pdftoppm.exe`. The combined
render command emitted "No display font" warnings for Symbol and ArialUnicode;
both images were produced. The one-page form and Japanese text render. This
inspection is not bilingual acceptance, proof of all text fitting correctly,
canonical AcroForm validation, or a general collision-safety guarantee.

## Existing output limitations

The retained verifier reports 13 PASS, 3 REVIEW, and no FAIL (exit 0 with
`fail_on_review=false`). REVIEW covers absent Han reference faces, five isolated
source-language tokens, and eight scaled runs. The minimum **reported** ratio is
0.844. The original placement log also records regular-face fallback for 11 bold,
15 italic and 3 bold-italic runs. These disclosures were preserved, not fixed
or treated as approval.

The selection intentionally reused an available, previously successful authored
mapping. It supplies a complete retained example, but no fit-refusal denominator,
B1 wrapping attempt, approved fixed box, or customer recovery rate. No plan or
library implementation follows from the capture. PRs #12/#13 remain open at
`abc4767` and `1d4f970`, respectively, unchanged on the read-only recheck.

</details>
