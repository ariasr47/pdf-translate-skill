# Item 8 — bounded ink-ratio investigation

**Result: not reproduced in the inputs tried.** No verifier defect was
established, and no library behavior changed. Version remains 88.

The assigned observation is canary run 4, Opus 5.5, September 25:
page 1 reportedly read **1.18 on `out.pdf`, 1.32 on `final.pdf`**, while
the model described the pages as pixel-identical. The assignment in
`docs/REQUESTS-from-product.md` was one attempt, bounded to about an hour:
reproduce and identify a cause before proposing work, otherwise close
with what was tried.

Initial sampling and independent controls took place within one bounded attempt,
03:33:22–03:47:08 UTC on September 27 (September 26 Pacific), about 14 minutes.
Recording the evidence and publishing the branch followed separately.

## What could be replayed

The original run-4 PDFs, mapping, commands and rasters were not available
in the local library workspaces. The historical record is
`dev/canary/runs/2026-09-25-run4-opus-5.5.md`; it identifies code
`4793f38`, metadata.version 77. The earlier machine's raw run directory
was not transferred. This attempt does **not** disprove the original
observation or claim an exact replay.

The canary fixture was regenerated using `dev/canary/make_fixture.py`.
That script and `pdf-translate/evals/make_fixtures.py` have no diff between
`4793f38` and v88. Generated controls retain the English page content;
they exercise fields and verification, not the missing Spanish translation.
Two saved deliveries were also measured: item 6's CLI parity fixture and
the real Spanish canary from September 5. The latter is a different run.
All saved inputs were read-only; before/after SHA-256 values match.

Both library snapshots ran on this host: Windows, Python 3.14.0,
PyMuPDF/MuPDF 1.28.2, pikepdf 10.13.0.post1. The v77 package was unpacked
with `git archive` and selected explicitly with `PYTHONPATH`; v88 was
`9b36b1f2d185acd4f55fed08d607a4e755f176ab`. This varies the library code,
**not** the historical macOS renderer or dependency environment.

## Method and observable acceptance

`dev/probes/ink_ratio_probe.py ORIGINAL OUT FINAL REPORT_DIR` opens each
input afresh and compares exact raster bytes at 72, 110 and 120 dpi.
It also renders at 72 dpi with annotations hidden. The defaults match
verify (72 dpi, RGB, no alpha, annotations included), the inspect loop
(110 dpi) and delivery comparison (120 dpi).

The probe performs eight actual `run_verify` calls for each case. It
alternates output order and uses `Test value 123`, `José Muñoz García`,
a long ASCII sample, then the first sample again. A recording wrapper
calls the unchanged `verify.ink`; a separate byte loop counts first-channel
values below 100 in fresh rasters. Raw counts are compared, so rounding
to two decimal places cannot hide a mismatch. The probe also compares the
serialized ink findings, repeats same-page raster calls and renders after
text/widget reads in both orders.

Acceptance is observable in each `report.json`:

- `inconsistencies` is empty and every actual ink count equals the fresh
  raster's independent count; exit 0 from the probe checks this.
- Repeated rasters and all four text/widget read orders preserve the exact
  raster signature; every input's `file_unchanged` is true.
- An equal-pixel pair has zero changed pixels and the same ink counts.
  A deliberately filled pair changes pixels and its reported ratio,
  proving the comparison detects a real change.

Other verify gates can fail on identity controls because English content
was intentionally retained. A probe exit 0 is a successful investigation
check, not a claim that those controls are deliverable translations.

## Measurements

**16 cases, 128 instrumented `run_verify` calls, zero inconsistencies.**
Every fill sample and call order preserved each PDF's ink counts. Source,
out and final file hashes remained unchanged. Both code snapshots agree
on every case run under both. The compact durable data includes input
hashes, counts, raster comparisons and report hashes:
`docs/reviews/data/2026-09-26-ink-ratio-investigation.json`.

Page-1 results below are at 72 dpi with annotations included. Page 2, where
present, was unchanged between each pair.

| Pair | Library snapshots | Dark pixels, out → final | Changed pixels | Reported ratio, out → final |
|---|---|---:|---:|---|
| Regenerated canary, before/after `field_fonts` | v77, v88 | 3,666 → 3,666 | 0 | 1.00 → 1.00 |
| Saved CLI parity delivery | v77, v88 | 298 → 298 | 0 | 0.96 → 0.96 |
| Blank fields, existing vs removed text/choice `/AP` | v77, v88 | 3,666 → 3,666 | 0 | 1.00 → 1.00 |
| September 5 Spanish delivery | v77, v88 | 4,532 → 4,588 | 349 | 1.24 → 1.25 |
| Filled canary, before/after `field_fonts` | v77, v88 | 3,837 → 3,837 | 0 | 1.05 → 1.05 |
| Filled fields, existing vs removed text/choice `/AP` | v77, v88 | 3,837 → 3,837 | 0 | 1.05 → 1.05 |
| Positive control: blank vs explicitly filled and saved | v77, v88 | 3,666 → 3,837 | 483 | 1.00 → 1.05 |
| Byte-identical copy | v88 | 3,666 → 3,666 | 0 | 1.00 → 1.00 |
| `/NeedAppearances` true vs false | v88 | 3,666 → 3,666 | 0 | 1.00 → 1.00 |

The positive control writes `José Muñoz García` to the first text field
and checks the first checkbox, then saves a new file. Both it and the
September 5 pair become byte-identical **rasters** when annotations are
hidden. With annotations included, their differences are also present at
110 and 120 dpi (respectively 887/1,021 and 687/769 changed pixels).
These are real widget appearance differences, not an ink measurement
inconsistency. Neither identifies the cause of the missing run-4 pair.

Both v77 and v88 fill and save one document during the round-trip check,
then reopen the supplied translated PDF as `jc` for ink measurement.
The actual-call comparisons above support that isolation on the tested
inputs. No evidence was found that changing the fill sample changes the
subsequent ink measurement of the supplied file.

An uninstrumented current CLI check on the generated final also printed:

```text
PASS fill round-trip
PASS page 1 ink ratio: 1.00
PASS page 2 ink ratio: 1.00
```

Its process exit was 1 due to other gates on deliberately unchanged source
content; the ink findings match the probe.

## Reproduce the central comparison

From the repository root, with the interpreter and `PYTHONPATH` pointing
at the checkout being tested:

```powershell
$env:PYTHONPATH = (Resolve-Path pdf-translate).Path
$probePython = 'C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe'
$probeDir = 'runs/ink-ratio-replay'
& $probePython dev/canary/make_fixture.py --outdir "$probeDir/fixtures"
& $probePython pdf-translate/scripts/field_fonts.py `
  "$probeDir/fixtures/permission_form.pdf" `
  pdf-translate/tests/fonts/NotoSans-Regular.ttf "$probeDir/rebuilt-final.pdf"
& $probePython dev/probes/ink_ratio_probe.py `
  "$probeDir/fixtures/permission_form.pdf" `
  "$probeDir/fixtures/permission_form.pdf" `
  "$probeDir/rebuilt-final.pdf" "$probeDir/replay"
```

Expected on the recorded renderer: 8 verify runs, `inconsistencies: []`,
zero changed pixels, page-1 dark counts 3,666/3,666 and page-2 counts
3,749/3,749. To test the historical code, unpack
`git archive --format=zip --output=ARCHIVE.zip 4793f38 pdf-translate`,
then set `PYTHONPATH` to that archive's `pdf-translate` directory and rerun
the same probe on the same inputs. The report records the imported module
path and renderer versions. Scratch PDFs, full reports, PNGs and the
direct CLI log are under `runs/ink-ratio-investigation-2026-09-26/`.

## Disposition

Close this assigned attempt as **not reproduced**, with the original
observation retained. Reopen if the actual run-4 input/output pair and
commands become available, or another saved pair yields inconsistent
counts under identical 72-dpi rendering and the same source denominator.
Do not assign a cause from visual similarity or from a raster made with
different annotation settings. No speculative runtime fix is proposed.

## Independent check

A different-model reviewer (GPT-6-sol) reviewed the probe and generated its
own two-page fixture: one form page and one blank page. It ran these two
commands under **both** the v77 and v88 package paths, using explicit
`PYTHONPATH` and the interpreter above. In this command block, `R` is
`runs/ink-ratio-investigation-2026-09-26/reviewer`; substitute that path
and the selected version for the placeholders.

```text
python dev/probes/ink_ratio_probe.py R/fixture/source.pdf R/fixture/out.pdf R/fixture/equal.pdf R/VERSION-equal
python dev/probes/ink_ratio_probe.py R/fixture/source.pdf R/fixture/out.pdf R/fixture/changed.pdf R/VERSION-changed
```

Actual output: **four commands exited 0; eight verify runs each;
`inconsistencies: []` in all four reports (32 independent calls)**.

- Different PDF bytes but equal rasters: 0 changed pixels, 353/353 dark
  pixels, both ink ratios 1.24.
- Saved widget text: 654 changed pixels, dark count 353 → 598, ratio
  1.24 → 2.10. The reviewer inspected both rasters and confirmed the
  visible field text change.
- The blank second page was correctly skipped. Input hashes, read-order
  rasters and repeated rasters were stable. Both library snapshots agreed.

The reviewer approved the bounded conclusion and confirmed that the probe
compares independently counted pixels with actual verifier calls. The
scope remains born-digital inputs with extractable text, fixed default
ink thresholds, and the current Windows renderer. Raw commands, the
independent generator and results are in `reviewer/EVIDENCE.md` under the
ignored run directory.

## Final checks

The reproduction commands above were executed as written in the separate
`runs/ink-ratio-replay/` directory: exit 0, eight further verify calls,
`inconsistencies: []`, and the expected counts on both pages. These are a
documentation replay, separate from the 16-case dataset and independent
32-call check.

From `pdf-translate/`,
`python -m unittest discover -s ../dev/repo -v` ran **6 tests in 1.538s,
OK, exit 0**. `git diff --check` passed. Full local discovery was not run;
the unchanged runtime's preceding PR already passed both hosted suites,
and the evidence PR's exact head checks are recorded on that PR.
