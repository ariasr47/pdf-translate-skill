# Typography implementation evidence

20 September 2026; active local development, not a released capability.
Plan: [approved tasks](../plans/2026-09-20-typography-preservation.md).
Design: [approved behavior](../design/typography-preservation/DESIGN.md).

## Execution and base

Rodrigo approved native execution on isolated `codex/typography-preservation`.
Base `48dffcf8fe1c9a5147e4c5bcfee107074e78a457` adds only approved design/plan
files to v58 runtime ancestry. Original checkout's v61/B1/audit edits remain
separate. No product source, PR edits, push or merge is part of this work.

Actual interpreter: Python 3.14.0; PyMuPDF/MuPDF 1.28.2/1.28.2;
pikepdf 10.13.0.post1; fontTools 4.64.0. Package path was asserted inside the
managed implementation checkout, not the original venv's editable target.
Seventeen copied test-font files include eleven configured faces and existing
variable-font instances; their hashes are in ignored runs/typography/baseline-fonts.json.

## Baseline setup finding

`python -m unittest discover -s tests -t .` initially ran 484 tests in
203.250 seconds with 15 errors. All errors named the absent ignored fixture
`dev/jobs/fl150-ja-2026-09-17/NOTES.md`; GeneratorTests setup suppressed eight
cases. Restoring that exact file from this repo's existing checkout, without
runtime edits, made `python -m unittest tests.test_review -v` pass 51 tests.
This is a reproducibility limitation of a fresh checkout, not a typography fix.
Initial ResourceWarnings from old font tests remain documented in the full log.
Canary: `python -m unittest discover -s ../dev/canary -p test_score.py` — 15 OK.

Baseline CLI and verdict probe stdout/stderr are retained separately in
`runs/typography/baseline-*`. Both used the same explicit Noto Sans font path
and unchanged verdict fixtures; package origin/version were recorded.

## Task 1: source evidence

RED: `python -m unittest tests.test_typography_extract -v` — 11 tests,
10 failures on the absent typography opt-in, one passing legacy-shape control.
GREEN focused: same new module plus `tests.test_pipeline.ExtractTests` —
12 tests OK in 2.113 seconds. These cover mixed serif/sans and emphasis,
repeated cores, exact source offsets, source/options/style/geometry binding,
moved paths, page selection, whitespace, rotation and ambiguous font resources.
Source fonts are explicitly selected and independently asserted in each fixture;
no fontfile-only Helvetica fallback is accepted.

Task 1 CLI stdout/stderr and verdict stdout/stderr are all byte-identical to
the captured baseline. Full discovery passed: `python -m unittest discover -s tests -t .` ran
503 tests in 195.370 seconds, OK. Existing font/review ResourceWarnings
remain in the log; there were no failures or skips.
Independent rendering verification remains required later in the approved plan.

## Task 2: strict mapping reader

The new reader retains ordered occurrence/run associations and validates their
extraction binding. It rejects duplicate new-format keys, stale/foreign IDs,
missing occurrences/emphasis, conflicting style resolutions, unsupported
scripts/clusters and missing class/role selections. Metadata cannot substitute
for visible-page coverage. Legacy duplicate-key behavior remains unchanged.

RED: the initial mapping module run exercised 13 test methods with 37 failing
subtests on the absent reader. Additional malformed-extraction cases first
produced five failures and two errors; all now raise typed input errors.
A common-symbol regression first rejected copyright/trademark/arrow text;
the final parser preserves those plain symbols while refusing unsupported
emoji and positioning-dependent clusters. This refines the planned plain-text
scope, without normalization or a shaping claim.

GREEN: `python -m unittest tests.test_typography_mapping tests.test_typography_extract`
ran 28 tests, OK. Final `python -m unittest discover -s tests -t .` ran
520 tests in 148.277 seconds, OK, no skips. Existing ResourceWarnings remain.
Both CLI and verdict probes exited zero; their stdout and stderr are each
byte-identical to the frozen baseline. Logs: `runs/typography/task2-*`.
The new reader is not yet connected to all stages; that is later plan work.

## Task 3: selected font preparation

Preparation accepts explicit class/role selectors, collects only that face's
target characters and checks the current font file before and after subsetting.
Wrong/unresolved classes or emphasis, uninstantiated variables and missing glyphs
raise FontError. Relative source paths resolve beside the mapping. Preparation
does not modify the mapping or require its eventual output font path to exist.
The CLI exposes the same selectors. Legacy console/results remain unchanged.

RED: `python -m unittest tests.test_typography_fonts -v` ran 11 tests with
nine failures and 13 errors on the absent charset, inspection and selectors.
First GREEN: 11 tests, 71.672 seconds. Expanded GREEN: that module plus
`tests.test_pipeline.PrepareFontAndCompareTests`, `tests.test_pipeline.JobCharsetTests`,
`tests.test_han_forms.PrepareFontTests` and `tests.test_consumer_contract` ran
45 tests in 146.984 seconds, OK. No skipped typography cases.

Real static Latin serif/sans regular, bold, italic and bold-italic were prepared
and inspected. Japanese and Simplified Chinese serif/sans regular/bold were
instantiated and subset; 400/700 glyph-outline hashes differ. CJK italic and
bold-italic requests using upright faces refuse: their positive acceptance
cells remain unmeasured, with no synthesized replacement. Corrupted metadata,
file replacement, missing glyphs, separate charsets, a read-only mapping and a
different working directory are covered. A newly added CLI case also passed.

Nine additional open font fixtures were downloaded from verified commit pins;
observed hashes and licence references are in `pdf-translate/tests/fonts/README.md`.
The fetcher's presence check passes all twenty configured files. No binary is
committed. Font downloads remain outside the runtime.
Task 3 CLI/verdict exits are zero; all four stdout/stderr captures are
byte-identical to baseline. Logs: `runs/typography/task3-*`.

## Rulings

- Start directly from the approved plan commit: it has identical runtime files
  to the design base, avoiding a redundant documentation copy.
- Ambiguous actual font resources retain null font_id and every candidate;
  an authored font-class resolution cannot invent the missing association.
- Raw span flags remain evidence, not authoritative class. A measured Noto Sans
  resource has PDF BaseFont `Noto Sans Regular`, exact program PostScript name
  `NotoSans-Regular`, and span flags 4; its program PANOSE resolves sans. Exact
  aliases are extracted from the font program; no fuzzy family-name matching.
- Preserve execution evidence until durable records are saved; ignored scratch
  cleanup cannot erase the independent run evidence required by AGENTS.md.
- Prepare the explicitly supplied source face even when the mapping's subset
  path does not yet exist; placement will independently inspect that path.
- Typography instancing uses fontTools' STAT-based `updateFontNames=True`
  alongside actual outline instancing. Legacy instancing is unchanged;
  regular bits on old 700-weight instances cannot attest a new bold role.

Every item above is local implementation evidence or an explicit limit.
No typography delivery, product adoption or full Claude/Codex host acceptance
is claimed while later tasks remain pending.
