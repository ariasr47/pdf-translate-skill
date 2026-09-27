# Item 9 — reserve the drawn space of rotated neighbours

Rodrigo authorized the next product-assigned item. This is the final item
in the existing sequence: a horizontal label could overlap a rotated
neighbour because its budget stopped at the neighbour's source box, while
the new font or translation drew beyond it. Base: PR #63, exact commit
`4d0ba939bf185a2663b53bae13a68cee70a7b7a1` (v88).
Implementation: `codex/rotated-neighbour-layout`, v89. No product source
was read and no AGPL code was copied.

## Behavior and scope

Legacy retypeset stably plans rotated runs before horizontal ones. Each
rotated run follows its existing fit, role, marker and tail rules. Its
prepared TextWriter and morph are drawn on a temporary in-memory page;
the union of actual non-space glyph boxes constrains horizontal room.
The final page reuses that exact writer and morph. `TextWriter.text_rect`
was rejected as a substitute because it includes unused global font
overhang: one measured target occupied about 158 pt while that rectangle
reserved about 192 pt.

Measured neighbours use the horizontal growth anchor and strict row
intersection, so longer vertical targets entering a row and sub-point
intersections count. Right-anchored labels reserve the left side; centred
labels reserve both sides about the existing midpoint. The 1.5 pt gap and
all-horizontal page budgets retain their previous arithmetic. Mixed-page
diagnostic order can put rotated runs first.

If a measured neighbour consumes the anchor, `allow_scale` cannot fix it:
the build raises `PlacementError` with nonempty
`refusals['rotated_neighbours'] = [{page, core, neighbour}]`. The normal
glyph-error precedence keeps every refusal category. No PDF or scale
report is saved on refusal. Positive room keeps the existing floor/opt-in.

This is the assigned neighbour-budget repair, not full rotated
reading-frame layout. Existing rotated-feature/shaping refusals remain.
Authored merge/override boxes, dot-leader geometry and RTL expansion are
outside the change; this is not a general collision engine.

## Observable acceptance and reproduction

Run from `pdf-translate/`, with fetched NotoSans Regular/Bold faces:

```sh
python -m unittest tests.test_rotated_neighbours -v
```

The 11 tests build PDFs through strip, extract and retypeset and inspect
their final saved glyph boxes and actual Noto font names. They require:

- A long horizontal translation beside the upside-down two-span
  "Signature of " / "applicant" line has no intersection between its
  drawn label box and any rotated glyph. Both source segment orders pass.
- Wider-font-only growth, a target entering the source label box, a
  vertical target entering the row, and a 0.518 pt row intersection leave
  disjoint output. Right anchoring and centring use their appropriate sides.
- All four page rotations with an offset crop produce separated text.
- Occupied left/right/center anchors raise the new refusal despite
  `allow_scale`, and save no output PDF. Positive-room below-floor builds
  retain the old refusal. A concurrent glyph miss raises `GlyphError`
  carrying both categories.

The first two tests failed in all four source-order subcases before the
repair: 23 intersecting glyph-box pairs on the left and 20 on the right.
Later red tests pinned the occupied-anchor, entering-vertical, thin-row
and centred cases found during independent review. Final results and
compatibility commands are below.

## Saved before/after measurements

Windows CPython 3.14.0, PyMuPDF/MuPDF 1.28.2, pikepdf 10.13.0.post1.
Interpreter: `C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`.
Worktree: `C:/Users/rodri/.codex/worktrees/cli-input-logging/pdf-translate-skill`.
Local ignored evidence directory: `runs/rotated-neighbour-layout-2026-09-26/`.

An archive of the exact v88 base and v89 each rebuilt five independently
saved copies of the new synthetic fixtures, with explicit Noto fonts:

```sh
python runs/rotated-neighbour-layout-2026-09-26/compare_drawn.py runs/rotated-neighbour-layout-2026-09-26/baseline/pdf-translate runs/rotated-neighbour-layout-2026-09-26/before
python runs/rotated-neighbour-layout-2026-09-26/compare_drawn.py pdf-translate runs/rotated-neighbour-layout-2026-09-26/after
```

Both commands exited 0. `comparison-summary.json` records:

| Fixture | v88 intersecting glyph pairs | v89 pairs | v88 label scale | v89 label scale |
|---|---:|---:|---:|---:|
| Wider face, same rotated text | 3 | 0 | 0.9599 | 0.8977 |
| Longer upside-down target, left label | 23 | 0 | 0.9599 | 0.6279 |
| Longer 1-degree target, right label | 20 | 0 | 0.7879 | 0.4559 |
| Centred label | 6 | 0 | 1.0000 | 0.7404 |
| Thin row intersection | 24 | 0 | 1.0000 | 0.6279 |

These fixtures opt into small labels where necessary; the no-opt-in
regression separately checks refusal. Every rotated glyph's direction,
font, size, origin and box is exactly equal before/after. The implementer
inspected fresh detail rasters for wider-face before/after, long-left and
center: the overlap is gone, with complete text and retained rotation.
This recreates the reported two-span shape, not the exact old Mac artifact
whose historical residual was 1.7 pt by 6.1 pt; the new fixture's measured
numbers are its own.

The existing `dev/probes/cli_parity_runner.py` ran against each checkout
with the same absolute `--font .../NotoSans-Regular.ttf`: 12 invocations,
identical normalized console and exit codes. Only its first `# package:`
checkout-identity header is excluded. `out.pdf`, `out2.pdf` and `final.pdf`
also have identical raw glyph data and 110-dpi raster bytes; each raster's
SHA-256 is `036e0501efbc12cd45426fbd5cc0533cf5c4557fd1ac63fc60fefa409fb8d1f7`.

## Focused compatibility

From `pdf-translate/`:

```sh
python -m unittest tests.test_rotated_neighbours tests.test_rotated_features tests.test_multispan_box tests.test_pipeline.RotatedTextTests tests.test_pipeline.PageRotationTests tests.test_pipeline.AlignmentAndFontRoleTests tests.test_pipeline.ListMarkerGapTests tests.test_pipeline.MarkerFontMetricTests tests.test_pipeline.GlyphCoverageTests tests.test_pipeline.ResourceLeakTests tests.test_pipeline.RefusalGateTests tests.test_pipeline.RefusalTruncationTests tests.test_pipeline.ShrinkBandTests tests.test_pipeline.RightAnchorRoomTests tests.test_import_surface -v
```

**116 tests in 22.626s, OK, exit 0** (`focused-compatibility.log`).

```sh
python -m unittest tests.test_typography_metrics tests.test_typography_verify tests.test_shipped_docs tests.test_verify_report.VersionLockstepTests tests.test_verify_report.PackagingMetadataTests -v
```

**60 tests in 44.858s, OK, exit 0** (`typography-docs.log`). This covers the
unchanged shared typography budget path, refusal table and all v89 version
sources. The existing docs guard now also collects conditional subscript
assignments to `refusals`, so it checks the new category too.

Final acceptance strengthened the comparison from individual horizontal
glyphs to the entire drawn label box. `python -m unittest
tests.test_rotated_neighbours tests.test_shipped_docs -v` then returned
**23 tests in 4.024s, OK, exit 0** (`final-acceptance.log`).

Full discovery runs on the PR's Linux/Windows CI, not this Windows host
after its recorded full-suite crashes. Consult the PR's current head
checks and description for the hosted outcome.

## Independent Rule 1 verification

A separate GPT-6-sol reviewer, which did not edit production code or
tracked files, inspected the implementation and ran from `pdf-translate/`:

```sh
python -m unittest tests.test_rotated_neighbours tests.test_rotated_features tests.test_multispan_box -v
```

**22 tests in 5.538s, OK, exit 0.** This was before the two additional
positive-room/glyph-precedence tests; the geometry implementation was final.
Local commands, results and raster hashes are in `reviewer/EVIDENCE.md`.

Its independent saved-file command, with `PYTHONPATH` explicitly set to
this worktree's `pdf-translate/`, was:

```sh
python runs/rotated-neighbour-layout-2026-09-26/reviewer/recheck_saved.py
```

Exit 0, all four independently discovered cases repaired:

- Occupied anchor: a specific `rotated_neighbours` refusal replaces 31
  overlapping tiny glyph boxes that `allow_scale` previously admitted.
- Entering vertical neighbour: ordinary below-floor refusal at
  0.0344404690 replaces nine intersections.
- Thin row: zero intersections at scale 0.6279 replaces 24 intersections.
- Centred label: zero intersections at scale 0.7404 replaces six.

Eight offset-crop/rotation/order controls had zero intersections; reversing
source segment order produced exactly equal 110-dpi rasters at each of
0/90/180/270 degrees. The reviewer asserted readable embedded final Noto
font buffers and inspected fresh centred, thin-row and crop/90-degree
rasters: complete legible text, retained rotation, no overlap or clipping.
Review approved with no unresolved findings in the assigned routes.
