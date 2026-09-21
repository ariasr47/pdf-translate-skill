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

## Task 4: complete occurrences on one baseline

The new branch validates original/extraction binding and complete page selection,
source/stripped boxes/rotation/field identities, source scope, selected fonts,
actual glyph bounds and both source/proposed neighbor collisions before saving.
Every translated occurrence advances ordered runs from the original baseline;
any shrink applies uniformly. Below-floor permission addresses one occurrence
and never permits a collision. Input/report aliases are refused. Cancellation
or an input refusal preserves prior artifacts and reports no new output.

The existing horizontal width-budget arithmetic is shared unchanged with legacy
placement. FontTools BoundsPen supplies actual selected outline bounds: the
backend's glyph_bbox returned whole-font boxes in a measured probe, even for
space. Stroked edges are conservative obstacles; filled backgrounds are retained.
Unmeasurable text or distinct codepoints sharing a glyph refuse explicitly.
Text is canonicalized per selected face on a private PDF before publication.
The successful result and schema-2 scale report carry source/mapping digests,
selected font evidence, occurrence/run positions, scale reasons and output hash.

RED: 16 tests produced 25 errors on the absent original argument/new path.
Two initial fixture mistakes used a zero-based page list where the existing API
expects a one-based string, and a tuple where Widget.rect expects Rect; correcting
the fixtures gave 16 passing tests without altering either API. A new translated-
neighbor collision test then failed because the build succeeded; checking proposed
glyphs against each other fixed it. An assumed space/NBSP collision was not real
in Noto (glyph IDs 3/98); the negative fixture now modifies its own copied cmap
and asserts equal IDs before testing the refusal. Genuine distinct glyphs retain
both Unicode choices without normalization.

Focused GREEN: `python -m unittest tests.test_typography_retypeset -v` — 23 tests
in 4.011 seconds, OK. Coverage includes eight Latin class/role faces, full repeated
label association, all source pages including a trailing blank, baseline/color,
metadata/graphics/fields, explicit scale exceptions, wrong/stale inputs, glyph
refusals, unsupported constructs, input aliases and cancellation between pages.
Task 4 CLI and verdict probes exit zero; all four captured streams match baseline.
Initial full discovery ran 556 tests in 324.272 seconds with one old merge-test
failure. The expanded fixture directory changed alphabetical Latin selection
from Noto Sans Regular to Noto Sans Bold; the paragraph then needed 0.67 scale.
Running that same real case with the original regular face passed. The existing
Latin fixture helper now prefers that explicit face, retaining its old fallback
only when unavailable. No renderer or scale floor was changed for this failure.
ShrinkBandTests plus the typography placement module then passed 28 tests in
4.961 seconds. Final full discovery ran 556 tests in 291.451 seconds, OK,
no failures or skips; existing ResourceWarnings remain in the log.

`python ../runs/typography/task4-render.py` built two retained visual fixtures:
two repeated mixed-style labels and all eight class/role combinations, each one
page. Direct `scripts/retypeset.py ... --original ...` also exited zero.
The source/rebuilt repeated-label rasters and eight-role output were inspected at
150 dpi: visible serif/sans/emphasis are retained, the reordered bold word leads
its line, no wrapping or baseline movement is visible. Graphics are additionally
asserted pixel-identical in a fixed non-text crop. Artifacts are under
`runs/typography/task4-visual/`. These are author checks; independent final review
is still required by the plan and AGENTS.md.

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
- Use measured glyph outlines, compare proposed translated neighbors, and keep
  exact per-face Unicode choices; an ambiguous glyph-to-text mapping refuses.
- Publish a new typography PDF only after private-file canonicalization. This
  does not change the separate A03 legacy artifact-lifecycle work.
- Keep older Latin geometry fixtures on Noto Sans Regular; adding style assets
  cannot silently switch their measured font to the alphabetically earlier Bold.

Every item above is local implementation evidence or an explicit limit.
No typography delivery, product adoption or full Claude/Codex host acceptance
is claimed while later tasks remain pending.

## Task 5 — actual final typography

The verifier reads final text traces, page geometry, glyph outlines and embedded
font programs independently of scale_report.json. Repeated labels are located
by page, source baseline and ordered advances, with exclusive glyph ownership.

Actual commands from pdf-translate/ (the interpreter and PYTHONPATH above):
- `python -m unittest tests.test_typography_verify tests.test_verify_report tests.test_consumer_contract -v`: 67 tests, 16.165s, OK.
- Expanded `python -m unittest tests.test_typography_verify -v`: 21 tests, 10.516s, OK.
- Both parity runners exited 0; all four stdout/stderr captures match the frozen clean baseline byte for byte.

The initial 19-test run had 17 failures and two errors before the check existed.
The first implementation left three failures. Real embedded-font inspection
showed MuPDF subsets retain OS/2 and head but omit post, and field embedding
adds a second resource containing identical program bytes. The subset path now
requires exact surviving class/weight/slant evidence plus matching used-glyph
outlines and advances. Byte-identical resources can share that evidence;
different programs with ambiguous names remain cannot-attest. Unknown complete
font metadata still produces REVIEW. Two added regressions ensure missing post
cannot hide changed outlines or inconsistent surviving metadata.

The original altered-font fixture moved every P point together; the glyph-set
reader compensates using the unchanged side bearing, leaving the drawn shape
unchanged. Moving one outline point creates a real distortion and now FAILs.
Wrong class/role, wrong repeated occurrence/page, shifted baseline, nonuniform
size, color changes, missing/extra pages and clipped italic glyphs also fail
while leaving the delivered PDF and untouched successful report in place.
Correct independent drawings, coalesced equal-style spans, actual subsets and
final field-font embedding pass. This remains author testing; independent
acceptance and whole-branch review are still required.

## Task 6 — occurrence QA and reviewer input

`python -m unittest tests.test_import_surface.QAVerdictTests tests.test_typography_review tests.test_review -v`: 66 tests, 1.677s, OK. The initial 12-case new module failed with 10 failures and one error; a separate metadata regression failed before adding title/bookmark QA and review support. Both parity runners exit0 and all four captures match baseline.

QA reads plain joined text per occurrence and includes exact occurrence/run/page context. Number and glossary findings preserve both repeated labels; consistency compares wording independently of style. Literal HTML remains text. Metadata pairs retain language QA separately. Reviewer pairs show source positions and ordered class/role associations with escaped text. The prompt carries current extraction/mapping hashes; stale or missing bindings and incorrect associations accept no findings or terminology updates. Bound explicit terms still append idempotently. New optional finding IDs serialize only when present, keeping legacy keys intact. A directory snapshot confirms generate=False changes no files. General invalid-review delivery policy remains A01, outside this change.

## Task 7 — CLI and pipeline context

Initial new-command tests: nine tests, six failures/two errors. After integration,
`python -m unittest tests.test_typography_pipeline tests.test_typography_mapping tests.test_pipeline -v` ran255 tests in45.552s with one new workflow-fixture failure; all228 legacy pipeline cases passed. The corrected focused run (`tests.test_typography_pipeline tests.test_typography_mapping`) ran27 tests in13.243s, OK. Both parity runners exited0 and allfour captures still match baseline.

The full subprocess sequence now runs from another working directory: opt-in
init, unauthored scaffold, refused unfilled build, explicit Spanish authoring,
rebuild with bound original/mapping/extraction, reviewer files, field-font
embedding and verification of that final PDF. The mapping parser retains one
format detector shared by every mapping reader, including helper commands.
Missing option values are named usage errors. New/mixed/unknown mappings refuse
lossy merge helpers before any write; stale extraction/reference, conflicting
forwarded context and report/input aliases preserve previous files.

The initial short Pay NOW fixture triggered the existing Latin leak scanner:
its three-letter words produce an empty source vocabulary, which selects the
generic Latin heuristic even with --source-words-from. The command fixture now
uses Payment NOW so the same existing option checks a real source word against
Pague AHORA. No language heuristic or acceptance check was disabled. This is a
known limitation to disclose in examples, separate from typography preservation.

Mapping-reader audit: remaining direct JSON reads consume extraction geometry,
review input, scale reports or widget/caption dictionaries. They are not an
alternate translations mapping path. PR12/13 heads were rechecked read-only and
remain abc4767/1d4f970; no remote changes.

## Task 8 — independent acceptance and adversarial corrections

Candidate base: `95886f67022a569cfd48daf159a5bc8f5cf2f84d` plus the Task 8
working changes. Independent evidence is retained under
`runs/typography/independent-review/`; the reviewer did not implement the runtime.
The committed probe and regression tests reproduce the supported cases.

The independent six-case command was:
`python ../dev/probes/typography_acceptance.py --work ../runs/typography/independent-review/official-final-probe --fonts tests/fonts`.
It exited 0: repeated/reordered emphasis, eight Latin class/role combinations,
italic overhang, horizontal Japanese, horizontal Simplified Chinese and an
original blank trailing page all returned typography PASS and verify exit 0.
Page geometry remained equal, including the two-page blank-page case. The
reviewer inspected source/final rasters at 150 dpi, actual font programs and
baselines. Full field-font embedding left all seven final rasters byte-identical
to the previously inspected versions. Actual embedded field-font cmaps contain
2,965 Latin, 16,732 Japanese and 30,890 Simplified Chinese entries, with no fvar
and weight 400. Those are supplied-face coverage counts, not universal typing
or language-quality guarantees.

Independent adversarial runs found and reproduced seven feature defects:

| Defect | Correction and observed outcome |
| --- | --- |
| Source transparency, stroke or affine transform silently flattened | Parse actual PDF text drawing state; unsupported source paint refuses before replacing an existing PDF or report. |
| Final shear could retain normal-looking text traces | Inspect text/graphics transforms; distortion fails. |
| Clipped glyphs retained their complete text trace | Arbitrary clip paths and text in clipped Form XObjects remain REVIEW/cannot-attest. |
| Later page/annotation paint could conceal glyphs | Inspect ordered paint bounds; possible occlusion remains REVIEW. |
| A metadata title sharing page wording could not receive its own review | Exact document source/target pairs without page IDs use the metadata channel; page findings require occurrence/run IDs where ambiguous. |
| UserUnit doubled physical pages behind unchanged raw boxes | Bind effective page rectangles as well as raw boxes/rotation. Changed final physical size fails; nondefault source UserUnit refuses in this first scope. |
| Filled widget values were treated as unassigned page text | Read page-only glyphs separately from widget/comment appearances; retain annotation paint for occlusion and restore the in-memory document before returning. |

Full field fonts also exposed ambiguous aliases beside page subsets. Actual
text-selected PDF font resources now determine which program can attest page
glyphs; an unused field font cannot stand in for the drawn page font. Complete
unknown font metadata remains REVIEW. Full fonts are used for fields; page
subsets cannot prove coverage of future user input.

Source clipping, text-containing Forms, nonuniform transforms, stroke,
transparency, soft masks, unusual blending, possible occlusion and nondefault
page units are explicit first-scope refusals. This is conservative support,
not preservation of those constructs. The effective-page field changes the
unreleased extraction binding: regenerate old development extractions/mappings.

Actual regression commands and results:

- `python -m unittest discover -s tests -t . -v`: 610 tests, 337.429s, OK,
  before the final filled-widget correction; final rerun recorded below.
- `python -m unittest tests.test_typography_verify -v`: 26 tests, 12.998s, OK
  after that correction. Both new filled-widget/comment cases failed beforehand.
- `python -m unittest discover -s ../dev/canary -p test_score.py`: 15 tests,
  0.631s, OK. Both parity runners exited 0 after the final correction; all four
  stdout/stderr captures match the original baseline byte for byte.

### Final rerun after an interrupted session

The session running Task 8 stopped on a provider usage limit before it recorded
its final full rerun. A new session re-ran the gates on the same working tree
rather than adopting an unrecorded claim:

- `python -m unittest discover -s tests -t . -v`: **611 tests, 441.631s, OK**,
  no failures, errors or skips. This is the complete run after the filled-widget
  correction. Existing font/review ResourceWarnings remain in the log, unchanged.
  The interrupted session's own final log, `runs/typography/task8-final-full.log`,
  had in fact reached 611 tests in 442.695s, OK; the two runs name an identical
  set of 598 test methods, compared with `diff`. Both are recorded because the
  first was found on disk, not inherited from a claim.
- `python -m unittest discover -s ../dev/canary -p test_score.py`: 15 tests,
  0.657s, OK.
- Both parity runners re-run from this tree: `cli_parity_runner.py` and
  `verdict_parity_runner.py` each exited 0, and all four stdout/stderr captures
  are byte-identical to `runs/typography/baseline-*` — verified with `diff`, not
  by inspection.
- The six-case acceptance probe re-run exited 0 with `typography=PASS`,
  `verify=0` and equal source/final page counts in every case, including the
  two-page blank-page case. `candidate_base` recorded
  `95886f67022a569cfd48daf159a5bc8f5cf2f84d`.

Measured interpreter: Python 3.14.0, PyMuPDF/MuPDF 1.28.2, pikepdf
10.13.0.post1, fontTools 4.64.0; package resolved inside this managed checkout
at version 58.

### Probe reproducibility correction

Reproducing the probe exposed a defect in its own documented command. The
docstring said to run it from `pdf-translate/`, which is true only when the
ambient interpreter already imports the checkout under test. `sys.path[0]` is
the probe's own directory, so with an editable venv installed from a *different*
checkout the documented command imported that other package and died on
`ModuleNotFoundError: No module named 'pdf_translate.mapping'`. An independent
verifier following the written instruction would either fail outright or, on a
checkout where the import happened to resolve, measure the wrong code.

The probe now documents the explicit `PYTHONPATH=<checkout>/pdf-translate` form
the existing parity runners already use, and records `pdf_translate.__file__`
and its version in `summary.json`, so each artifact names the package it
actually measured. No probe case, threshold or runtime behavior changed; the
rerun above used the corrected command.
- Earlier focused correction runs: 51 paint tests OK; 65 metadata/review tests
  OK; 80 field-font/physical-page tests OK. Independent affected run: 83 tests,
  21.413s, OK before the final filled-widget correction.
- Actual v54 and v56 Git archives refuse new-format build without creating a
  PDF; the installed-style capability guard exits 2 before old QA/review.
- Eight genuine CJK slanted-role positive cells remain unmeasured. Supplying
  their upright regular faces instead produces typed wrong-role refusal in
  all eight negative cells; none is silently relabeled or synthesized.

The italic stress source is 90 italic f glyphs and the target is 110: measured
uniform scale 0.797794, size 9.57353, baseline 60. This isolates overhang without
turning a normal phrase into an unrelated huge ink-ratio change. It is a glyph
stress fixture, not a translation example. Qualified language/emphasis semantics
remain unjudged. Other OS/Python combinations and host installations are separate
acceptance work. No public-ready or app-adopted claim follows from these tests.

Read-only GitHub recheck on 20 September: main run 35475768236 succeeded at
`a5629fbd6bc084f9ab849ae3db74992c15807fcc`; PR 13's last listed run 35433169821
failed. Earlier billing failure is historical, not a claim about all current
CI. This local candidate has no remote run, so its Windows/Linux 3.10/3.13
matrix remains unverified. The existing ignored NOTES fixture requirement and
old ResourceWarnings remain the baseline limitations described above.
