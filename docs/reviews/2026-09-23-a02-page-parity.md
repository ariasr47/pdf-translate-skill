# A02: a translation keeps exactly the original's pages

23 September 2026 · local branch `fix/a02-page-count`, from main `178a06f` ·
pushed for CI on 23 September; not merged or released · version unchanged (v60)

## Outcome

Legacy verification now fails when a page is missing, added, rotated or
resized, with or without a mapping. `compare` and `render` show every page of
both files and exit 1 when the counts differ. `finish` returns that code after
writing everything. Matching jobs behave exactly as before: the same verdicts,
byte-identical comparison HTML and renders, and one added PASS line on the
verify console.

## The defect, reproduced on main

`dev/probes/a02_page_parity_probe.py` builds a genuine two-page legacy job
through the shipped stages (`run_strip`, `run_extract`, `run_retypeset`,
Noto Sans, Spanish targets). It then derives four broken outputs from the good
one and runs the CLIs as subprocesses and `run_verify` in-process. Against an
exact `git archive` export of `178a06f`:

| Output | verify, mapping | verify, no mapping | compare | render |
|---|---|---|---|---|
| equal (2 pages) | 0 | 0 | 0, 2 pages shown | 0, 4 files |
| page 2 deleted | 1, but only `placement` | **0** | **0, 1 page shown** | **0, 2 files** |
| page 3 added | **0** | **0** | **0, 2 pages shown** | **0, 4 files** |
| page 2 rotated 90° | **0** | **0** | 0 | 0 |
| page 2 A4 → Letter | **0** | **0** | 0 | 0 |

The ink, text-layer and leak gates iterate `range(min(len(o), len(j)))`, and
no gate compared counts or boxes. The missing page failed only because a
mapping target lived on it, so it passed without the mapping, the audit's
original R2 shape. Typography's own gate already refused changed page geometry;
the legacy route, which the app uses, had nothing.

## What changed (`06f2c35`, boundary fix `d9efd44`)

| Surface | Behaviour |
|---|---|
| `verify` / `run_verify` | New always-on gate `page-parity`, recorded after `fill-roundtrip` (`GATE_NAMES`). It FAILs with findings `missing` (the original's page number), `extra` (the translation's), `media-box`, `crop-box` (differences over 0.01 pt) or `rotation`. One status line per run; details are indented, ten at most, then `… N more not shown`; the verdict keeps every finding. |
| `compare` | Every page of both files; the side that lacks a page shows "No page N in this file."; a banner states both counts; returns 1 on a count mismatch. Matching output is byte-identical to before. |
| `render_pages`, `pipeline.py render`, `scripts/render_pages.py` | Every page of each file is rendered; a FAIL line and exit 1 on a count mismatch. New helper `page_count_mismatch()`. |
| `pipeline.py finish` | Returns `compare`'s code after writing FINAL, the comparison and `review_state.json`. It still packages, and never withholds. |

**Decisions.** The gate records after `fill-roundtrip`, beside the page-level
gates, which keeps `field-parity` first as an existing test pins it. Box and
rotation changes are left to `verify`: compare and render show them in the
images, so those two check counts only. There is no override. No stage adds or
reshapes a page, B1 forbids a continuation page, and a verify FAIL stays
advisory (the product's R5). The 0.01 pt tolerance absorbs re-serialised boxes;
A4 against Letter differs by 17 pt.

## Verification

| Check | Result |
|---|---|
| New tests `tests/test_page_parity.py` (API, CLI subprocesses, compare, render, finish) | 17 tests. RED on `178a06f`: 14 failed for the missing feature, and the matching-pages compare control passed. GREEN on the fix. The 17th, the float32 boundary, came from the independent pass (below). |
| Mutation: remove the ten-line console cut | the truncation test fails (11 ≠ 10); restored, it passes |
| Full discovery at `06f2c35` (from `pdf-translate/`: `python -m unittest discover -s tests -t .`) | 686 tests OK in 536.723 s, exit 0: the 670 of `178a06f` plus 16 new, and no existing test changed |
| Probe after the fix (same command, fresh directory) | all four broken outputs FAIL `page-parity` with and without the mapping (the missing page also still FAILs `placement` with it); compare/render exit 1 with 2 or 3 pages and 3 or 5 files; equal output unchanged, 0 everywhere |
| False-FAIL sweep (`dev/probes/a02_page_parity_sweep.py`) | 16/16 corpus PDFs against their own `run_strip` output: no finding, including `rotated.pdf` (90°) and `encrypted.pdf`. A retained real delivery (FL-150 page 1, captured 19 September): source vs stripped and source vs output, no finding; `run_verify` records `page-parity` PASS. |
| Verdict ratchet (`verdict_parity_runner.py`, nine fixture jobs, `178a06f` vs fix) | stdout: one added `PASS page parity` line per job, except `arabic/bad.pdf`, whose fixture draws the bad output on a Letter page against an A4 original: the new gate reports that (media and crop box). All nine exit codes are unchanged; that job was already exit 1. |
| CLI ratchet (`cli_parity_runner.py`, eleven CLIs) | exactly two added lines, the PASS line in `verify` and in `rebuild`; nothing else differs |
| Matching-page `compare` and `render`, `178a06f` vs fix | HTML byte-identical (64,140 bytes); all four PNGs identical |
| CI | `tests.test_page_parity` added to the enumerated modules; the list equals all 22 `tests/test_*.py` modules |
| GitHub CI, run 35935412655 at `5348082`, dispatched after the push | Linux 687 tests OK in 593.161 s, Windows 687 OK with the existing cross-drive skip in 874.203 s (the 670 of main plus 17 page-parity tests), the canary 15 OK on both, the plugin manifest job green |

Commands (from the repository root, with the repository's venv and `PYTHONPATH`
set to the tree under test; raw outputs are in this worktree's ignored
`runs/a02/`, and [sanitised results](data/2026-09-23-a02-page-parity.json) are
committed):

```text
python dev/probes/a02_page_parity_probe.py --root <tree>/pdf-translate --work <fresh> --out <json>
python dev/probes/a02_page_parity_sweep.py <tree>/pdf-translate <retained job dir> <fresh> <json>
PYTHONPATH=<tree>/pdf-translate python dev/probes/verdict_parity_runner.py <gate fixtures>
python <tree>/dev/probes/cli_parity_runner.py <fresh> --font pdf-translate/tests/fonts/NotoSans-Regular.ttf
cd pdf-translate && python -m unittest tests.test_page_parity -v
```

**AGENTS.md Rule 1.** This changes verification and the inspection outputs,
not what the pipeline draws. The independent pass is recorded below regardless.

**Independent verification (a separate pass on another model, with real runs
only, against the baseline export and `06f2c35`): verified with findings.**
All seven acceptance criteria held through the API, the CLI with `--report`,
`compare.py`, `pipeline.py render` and `pipeline.py finish` (whose FINAL, HTML
and `review_state.json` it listed on disk). A genuine
strip/extract/retypeset build passed with and without the mapping, and six
corpus files, including `rotated.pdf` and `encrypted.pdf`, gave no finding.
Every broken case reproduced on the baseline as described. Its adversarial
round found no false PASS: a mixed-page-size swap failed on both pages, and
rotations written as −90 or 450 were normalised by PyMuPDF. Two findings:

- **Minor, fixed in `d9efd44`.** PyMuPDF reads box values as 32-bit floats,
  so a box exactly 0.01 pt off (612 → 612.01, read as 612.0100098) failed,
  although the rule says "beyond 0.01 pt". The comparison now allows that
  representation error (relative 2.4 × 10⁻⁷ on top of the tolerance). The new
  test `test_the_box_tolerance_holds_at_its_boundary` failed before the change
  and passes after it: 612.01 passes and 612.02 fails.
- **Informational, not a regression.** A hand-made zero-page PDF crashes
  `verify.py` with `pikepdf.PdfError` inside the older `opt-export-parity` gate,
  before page parity runs, identically on `178a06f`. PyMuPDF refuses to save a
  genuine zero-page PDF, and `compare` and `render` handle the malformed file.
  It is recorded in the limits below.

Its report and scripts are in this worktree's ignored `runs/a02-verifier/`.

## Limits

- Boxes are compared as PyMuPDF resolves them (inherited attributes
  included). `/UserUnit`, the bleed, trim and art boxes, and annotation
  geometry are not compared; field geometry stays with `field-parity`.
- A malformed zero-page input crashes `verify` in `opt-export-parity`, as it
  did before this change; handling unreadable inputs belongs to the
  hostile-input item (A23), not here.
- A consumer with its own comparison or rendering loop keeps its own page
  handling. Only the library's `compare`, `render_pages`, `pipeline.py render`
  and `finish` changed.
- The version stays v60 on this candidate. The integration that lands it
  should bump, and should note the one new console line per verify run.
