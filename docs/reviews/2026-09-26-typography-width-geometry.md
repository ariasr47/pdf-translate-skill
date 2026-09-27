# Item 7 — typography widths and unrotated geometry, 26 September 2026

Base: v87, PR #61 at `2c871328ea78f444edb107cf00970ad081df78ec`.
Candidate: v88, `codex/typography-width-geometry`,
[PR #62](https://github.com/ariasr47/pdf-translate-skill/pull/62), stacked on #61.
Rodrigo authorized this product-assigned pair after item 6. Items 8 and 9
remain separate; no consumer pin changes or merges are part of this repair.

## Observed defects

A correct TextWriter output using this repository's OFL Noto faces rescaled
to 2,048 units per em failed typography verification. The 31-character sans
prefix accumulated a 0.193710 pt difference from the verifier's exact font
advance prediction. The actual PDF stores integer `/W` widths rounded down
in thousandths of an em. A new font span starts at the full-precision authored
origin; adjacent authored runs in the same face may share one PDF span.
The old verifier passed an independently edited copy with exact fractional
PDF widths, confirming which representation caused the failure.

The verifier also compared unrotated glyph bounds with the viewer's rotated
page rectangle. On offset-crop landscape and portrait pages, correct glyphs
near the far edge failed at 90 and 270 degrees, while real overflow could
pass on the wider viewer rectangle. Calling the internal typography measurer
on the same placement at those rotations raised `PlacementError` even though
it fit at zero degrees.

## Repair and observable acceptance

From `pdf-translate/`, run
`python -m unittest tests.test_typography_metrics -v`.

- Long 2,048-unit sans and serif prefixes with bold/bold-italic tails return
  typography PASS. Tests assert the actual drawn font names and embedded
  programs' `unitsPerEm`, including uniform shrink, same-face coalescing and
  subsetting. Exact fractional PDF widths also pass.
- The verifier reads `/W` array and range forms plus `/DW`, and compares each
  used width with the selected TrueType program's exact advance, its integer
  floor, or the floor after MuPDF's floating-point normalization. A 2/1000-em
  alteration returns a named PDF-width FAIL even though its
  0.024 pt position change is below the unchanged 0.05 pt tolerance. Extra
  character spacing and a real 0.2 pt shifted style boundary still fail.
- Equal font-program bytes require equivalent PDF width tables before
  duplicate resources can be treated as one. Conflicting tables return
  REVIEW for ambiguity; identical duplicates pass. Unresolved CID mappings
  cannot receive width attestation.
- The internal measurement returns the same placement at all four rotations
  for landscape and portrait offset-crop pages. Correct final glyphs pass
  against unrotated crop bounds; real overflow fails. The public builder
  still refuses rotated typography sources and preserves previous output.

Verification still reads the delivered file and leaves its bytes unchanged.
Widths are cached per resource, and equivalence signatures are hashed once
per font. Existing constant page-load coverage for filled forms remains green.

The PDF width representation follows ISO 32000-1, §9.7.4.3 and the CIDFont
dictionary in §9.7.4.2 ([Adobe's specification](https://developer.adobe.com/document-services/docs/assets/35e4369068f86065372c18787171a17e/PDF_ISO_32000-1.pdf)).
Portable test faces use the supported
[`fontTools.ttLib.scaleUpem.scale_upem`](https://fonttools.readthedocs.io/en/stable/ttLib/scaleUpem.html)
helper on the repository's downloaded OFL fonts; no installed proprietary
font or product code is used.

## Commands and results

Windows, Python 3.14.0, PyMuPDF 1.28.2, pikepdf 10.13.0.post1,
fontTools 4.64.0. Interpreter:
`C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`.
Raw logs and fixture PDFs are under the ignored repository-root directory
`runs/typography-width-geometry-2026-09-26/`. Commands run from `pdf-translate/`
unless their path starts with `runs/`.

| Check | Command | Observed output |
|---|---|---|
| Existing baseline | `python -W default -m unittest tests.test_typography_verify tests.test_typography_retypeset -q` | `Ran 56 tests in 19.964s`, `OK` |
| Reproduction before production edits | `python runs/typography-width-geometry-2026-09-26/probe.py` | Both correct 2,048-unit occurrences FAIL; exact versus actual PDF width drift recorded per glyph; same-face authored runs coalesce |
| Red regressions before production edits | `python -W default -m unittest tests.test_typography_metrics -v` | Initial 12 tests: `FAILED (failures=9, errors=4)` across subtests; the four errors are the reproduced internal `PlacementError` at 90/270 degrees |
| Green typography coverage | `python -W default -m unittest tests.test_typography_metrics tests.test_typography_verify tests.test_typography_retypeset -q` | `Ran 69 tests in 52.853s`, `OK` |
| Pipeline, imports, reports and docs | Previous command plus `tests.test_typography_pipeline tests.test_import_surface tests.test_verify_report tests.test_shipped_docs` | `Ran 163 tests in 81.714s`, `OK` |
| Final regression module | `python -W default -m unittest tests.test_typography_metrics -v` | `Ran 16 tests in 14.337s`, `OK` |
| Repository integrity/discovery | From repository root, `python -W default -m unittest discover -s dev/repo -v` | `Ran 6 tests in 1.516s`, `OK` |

Three additional controls subsequently promote the reviewer's width-range
and duplicate-resource checks into permanent coverage and require unresolved
CID mapping evidence to remain REVIEW. A subsequent CI boundary regression
brings the final module to 17 tests (below).

## Independent Rule 1 verification

The implementation was written by GPT-6-astra. A separate GPT-6-sol reviewer
did not edit production code. It independently ran
`python -m unittest tests.test_typography_metrics tests.test_typography_verify -v`:
**42 tests in 29.260s, OK, exit 0**, and approved the production repair.
After the final test additions it independently reran
`python -m unittest tests.test_typography_metrics -v`:
**16 tests in 14.210s, OK, exit 0**, and approved with no findings.

It also wrote and ran these independent probes from repository root:

- `python runs/typography-width-geometry-2026-09-26/reviewer/verify_fixture.py`:
  the same correct 2,048-unit PDF changed from FAIL before repair to PASS
  afterward; the exact fractional-width control also passes. All four drawn
  font programs were asserted embedded with `unitsPerEm=2048`. Actual PDF
  widths predicted every glyph origin within 0.000034 pt. The reviewer
  inspected its 2x raster: complete, legible lines, correct regular and
  bold/bold-italic styling, no clipping or overlap.
- `python runs/typography-width-geometry-2026-09-26/reviewer/verify_checks.py`:
  sub-tolerance width corruption FAIL with the explicit metric finding;
  identical embedded bytes with conflicting resource widths REVIEW;
  range-form widths PASS; an actual 0.2 pt style-boundary shift FAIL.

## Full-suite finding and repair

The first full run, [36287520695](https://github.com/ariasr47/pdf-translate-skill/actions/runs/36287520695),
ran 838 tests on both platforms: Linux 340.968s, Windows 419.592s. Both had
exactly one failure in the existing saved typography acceptance probe:
`latin-roles` failed for NotoSans-Bold `s`; the other five saved cases passed.
The pre-existing expected failure remained; Windows also retained its skip.

The actual selected and embedded face has hmtx 502 / 1000, but MuPDF returns
`0.5019999742507935`; flooring that normalized value times 1000 produces
the observed `/W 501`. Comparing only against exact integer font arithmetic
was too strict. The verifier now also accepts that measured renderer floor,
while retaining exact/mathematical-floor controls and the fixed position
tolerance. It does not accept arbitrary nearby widths.

`python -W default -m unittest tests.test_typography_metrics.TypographyWidthTests.test_integer_font_units_can_round_below_a_pdf_width_boundary -v`
failed before this correction: **1 test in 7.614s, FAIL**, naming U+0073's
PDF width. This small regression uses the existing 1,000-unit OFL faces.
The original saved `latin-roles` probe is also retained locally for replay
and independent raster review.

After correction,
`python -W default -m unittest tests.test_typography_metrics tests.test_typography_verify tests.test_typography_retypeset -q`
returned **73 tests in 35.595s, OK**. The separate reviewer inspected the
additional renderer-floor branch and independently ran
`python -m unittest tests.test_typography_metrics tests.test_typography_verify -v`:
**46 tests in 33.446s, OK, exit 0**. It approved again with no findings.
Both its saved previously failing `latin-roles` PDF and a fresh run of the
existing `build_case(..., 'latin-roles')` probe now PASS all eight occurrences.
It asserted all eight actual font resources were embedded, independently
measured the 502-to-501 boundary, and inspected the fresh raster: complete,
correctly styled lines without clipping or overlap. Its width-corruption,
duplicate-resource, range-width and displacement probes retained their
intended FAIL/REVIEW/PASS/FAIL results.

Full Linux/Windows discovery reruns on the PR. Its current head's checks and
description record the hosted result. The local handover records two host
crashes during full-suite runs, so only focused suites run on this machine.

## Limits

Width attestation covers the Identity-H CIDFontType2 resources emitted by
the supported builder, with absent or named Identity CID-to-glyph mapping.
Other encodings, explicit mapping streams and malformed/ambiguous widths
add REVIEW evidence; other proven discrepancies may still make the overall
gate FAIL. This is not a general PDF font interpreter or an expansion to
rotated typography builds. Supported build drawing stays the same; affected
typography verdicts and the report version change. The legacy path is unchanged.
