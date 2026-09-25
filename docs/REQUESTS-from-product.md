# Requests from product

This is the product repo's (`pdf-translator`) inbox to this skill. When the
product finds a behaviour here it wishes this library had, it goes in the
table below — not as a patch, not as a diff, not as pasted code.

**A request describes BEHAVIOUR. It never pastes code.** `pdf-translator` is
heading to AGPL-3.0; this repo is MIT. Code flows downstream from here to
there, never back — see `AGENTS.md`'s licence section. A request that
arrives as a code snippet, a diff, or "here's roughly how we did it" gets
rewritten as a behaviour description before anyone acts on it, or it gets
refused. Describe the input, the observable output, and why it matters;
this repo's own tests and corpus are what any implementation is checked
against.

## How work arrives here — 24 September 2026

The product directs this library and assigns its work (`AGENTS.md` Rule 4,
`docs/DECISIONS.md` 2026-09-24). New work reaches this library as a row in
this file, with:

- a stable ID;
- one owner;
- the behaviour wanted;
- how acceptance is observed.

This repo may add findings or proposals here for the product to decide on,
and records here what it delivered: PR, version and evidence.

Sessions on both sides also message each other directly while they run.
Claude sessions do this by name with `SendMessage`; other agents go through
Rodrigo. Whatever a message settles is written into this file in the same
session.

## Current coordination status — 25 September 2026, night

**Main is v71 at `62e87bf`.** Seven things are in flight, each stacked on
the one before:
- **#42,** R-42 at v72;
- **#43,** R-110 at v73;
- **#44,** R-100 at v74;
- **#45,** R-99 at v75;
- **#46,** the docs items at v76, with the product's GlyphError ask
  (`7c91b4a`);
- **#47,** R-51, tests only, still v76;
- **R-48 with R-49 at v77,** on `perf/r48-r49-pixel-loops`. It waits for
  Rodrigo's go to push.

The app's session merges in order and retargets each to `main` first.

**For a consumer, v77 changes nothing but speed.**
- Extract, the invisible-text oracle and verify give identical output,
  byte for byte, including on the app's call shape.
- `invisible_text_pages` gains an optional `pages=`.
- CPU falls 38–46%, and 63% for a 5-page slice of a long document.

**Next:** R-50, unless E12's rulings arrive first. Two product rows filed
on 25 September wait for Rodrigo's order: #19's capture docs and #42's
line-start position.

**Adoption:** none yet. The app stays on v54.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, evening (historical snapshot)

**Main is v71 at `62e87bf`.** Six things are in flight, each stacked on
the one before:
- **#42,** R-42 at v72;
- **#43,** R-110 at v73;
- **#44,** R-100 at v74;
- **#45,** R-99 at v75;
- **#46,** the docs items R-79, R-80, R-82 and R-83 at v76;
- **R-51,** tests only, still v76, on `perf/r51-test-font-instances`. It
  waits for Rodrigo's go to push.

The app's session merges in order and retargets each to `main` first.

**For a consumer, R-51 changes nothing:** only the test suite changes, and
the version stays 76.

**Next:** R-48 with R-49, then R-50. E12 goes first if its rulings arrive.
The product advises R-48 with R-49 next, with added evidence on its call
shape (the performance row).

**The product reviewed #9–#46 and R-51 on 25 September: no blockers.** Its
review is advice for Rodrigo, not approval.
- **Nothing breaks the app on its v54 pin or its planned upgrade.** It ran
  16 cases shaped like the app's calls, v71 against v76. Return codes,
  stdout, exceptions, refusals and `scale_report.json` were identical in
  all 16. Its 73 files on disk were byte-identical once the trailer `/ID`
  was masked.
- **#46:** one doc ask before merge, now fixed locally in `7c91b4a`. The
  refusal table's exception column now says a glyph miss makes the drawing
  group's refusal a `GlyphError`.
- **R-51:** no reason to hold. Its optional suggestion, keying the memo on
  the file's bytes rather than its declared checksums, is adopted in
  `7274ee2`, locally. `4f7f62d` then closes a file that commit's new test
  left open. The product then read `7c91b4a`, `7274ee2` and `4f7f62d`
  without running them, and had no further ask on #46 or R-51.
- **#42:** it found the recorded position is the start of the text line,
  not of the offending text. Filed as a row below.
- **#19:** it asks for capture's off switch and contents to be documented.
  Filed as a row below.
- **#30 and #33:** it confirms both fix defects that are live in the app
  today on v54.
- **#15:** it measured no ratio shift on FL-150.
- **#43:** it found the SPDX build clean under uv.

**Adoption:** none yet. The app stays on v54.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, late afternoon (historical snapshot)

**Main is v71 at `62e87bf`.** Five things are in flight, each stacked on
the one before:
- **#42,** R-42 at v72;
- **#43,** R-110 at v73;
- **#44,** R-100 at v74;
- **#45,** R-99 at v75;
- **the docs items R-79, R-80, R-82 and R-83 at v76,** on
  `docs/r79-r83-docs-quick-wins`. They wait for Rodrigo's go to push.

The app's session merges in order and retargets each to `main` first.

**For a consumer, v76 changes nothing observable.** Only the shipped docs
and code comments change. No console line changes, so the refusal patterns
the app matches are untouched.

**The review's quick wins are all built.** Next come the performance
items: R-51, then R-48 with R-49, then R-50. E12 goes first if its rulings
arrive.

**Adoption:** none yet. The app stays on v54.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, afternoon (historical snapshot)

**Main is v71 at `62e87bf`.** Four things are in flight, each stacked on
the one before:
- **#42,** R-42 at v72;
- **#43,** R-110 at v73;
- **#44,** R-100 at v74;
- **R-99 at v75,** on `fix/r99-resource-warnings`. It waits for Rodrigo's
  go to push.

The app's session merges in order and retargets each to `main` first.

**For a consumer, v75 changes nothing observable:** files and faces are
closed after use.

**Adoption:** none yet. The app stays on v54.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, early afternoon (historical snapshot)

**Main is v71 at `62e87bf`.** Three things are in flight, each stacked on
the one before:
- **#42,** R-42 at v72, against `main`;
- **#43,** R-110 at v73, on #42's branch;
- **R-100 at v74,** on `chore/r100-dead-code`, on #43's branch. It waits
  for Rodrigo's go to push.

The app's session merges in order and retargets each to `main` first.

**For a consumer, v74 changes nothing observable:**
- `verify.load_segments_for` is gone. It had no caller, and is not among
  the app's five names.
- The legacy untranslated refusal is raised by the early pass, as it always
  was.

**Adoption:** none yet. The app stays on v54.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, midday (historical snapshot)

**Main is v71 at `62e87bf`.** Two things are in flight:
- **#42,** R-42 at v72. It is open against `main` with Auto-fix on;
  Rodrigo approved the push, and merging waits for his word.
- **R-110 at v73,** on `chore/r110-spdx-licence`, stacked on #42. It waits
  for Rodrigo's go to push.

**For a consumer, v73 changes this:** building the package from source
needs `setuptools>=77`, and its metadata says `License-Expression: MIT`. The
app's uv git install fetches that setuptools itself.

**Adoption:** none yet. The app stays on v54.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, later morning (historical snapshot)

**Main is v71 at `62e87bf`.** Rodrigo said "merge", and the app's session
merged #40 (R-33, v70) at 07:17 UTC as `314e1f6`. It then retargeted #41
(R-40, v71) to `main` and merged it as `62e87bf`. GitHub confirms both, with
all checks green, and main's tree equals `beb4c06`'s.

**For a consumer:**
- **v70:** `field_fonts` keeps each field's colour and size.
- **v71:** a legacy `rebuild` with capture on records the source PDF.

**Built, not pushed:** R-42 at v72, on `fix/r42-typography-preflight-names-text`,
whose base `beb4c06` is in `main`. Its PR targets `main`, and it waits for
Rodrigo's go.

**For a consumer, v72 will change this:** a typography source-content
refusal's `occurrence_id` and `source_text` name the text at fault. A
whole-page construct gives only `page`.

**Adoption:** none yet. The app stays on v54, with no typography-1.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, morning (historical snapshot)

**Main is v69 at `b504821`.** #39 (R-69 and R-97, CI only) merged at 06:00
UTC; GitHub confirms it. Two things are in flight:
- **#40,** R-33 at v70. It is open against `main` with Auto-fix on.
  Rodrigo approved the push in this session; merging waits for his word.
- **R-40 at v71,** on `fix/r40-capture-source-pdf`, stacked on #40. It
  waits for Rodrigo's go to push.

**For a consumer:**
- **v70:** `field_fonts` keeps each field's colour and size.
- **v71:** a legacy `rebuild` with capture on records the source PDF in the
  bundle.

The app uses neither.

**Adoption:** none yet. The app stays on v54.

**Proposed:** typography verify's units-per-em drift, and `field_fonts`'s
`/FT` lookup (the last two rows).

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, before dawn (historical snapshot)

**Main is v69 at `19252b7`.** Two things are in flight:
- **#39,** R-69 with R-97. It is open against `main` with Auto-fix on, and
  CI only, with no version bump. Both of its CI runs passed: a cache miss
  that saved, then a hit that fetched nothing.
- **R-33 at v70,** on `fix/r33-field-fonts-keep-appearance`, stacked on #39.
  It waits for Rodrigo's go to push.
- *Update:* #39 merged as `b504821` at 06:00 UTC, confirmed on GitHub, so
  main is v69 at `b504821`. R-33's PR will target `main`.

**For a consumer, v70 will change this:** `field_fonts` keeps each field's
colour and size. Only the font in its `/DA` changes. A plain or missing
`/DA` comes out as before.

**Adoption:** none yet. The app stays on v54, and its route calls no
`field_fonts`.

**Proposed:**
- typography verify FAILs correct lines drawn in a face whose units-per-em
  is not 1,000;
- `field_fonts` skips a field whose `/FT` is inherited from above its
  parent.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, late night (historical snapshot)

**Main is v69 at `19252b7`.** Rodrigo said "merge", and the app's session
merged #38 after its ubuntu, windows and plugin-manifest checks passed. The
merge commit is pinned to the reviewed head `7e04250`. GitHub confirms it:
merged at 03:31 UTC, and main's tree equals `7e04250`'s.

**For a consumer, v69 changes this:** typography verify's page loads no
longer grow with the glyphs checked. On a filled form, one verify's peak
memory falls from gigabytes to about 170 MB, and every verdict is
unchanged.

**Adoption:** none yet. The app stays on v54 until its Python 3.14
migration.

**Built, not pushed:** R-69 with R-97, on `ci/r69-r97-discover-and-font-cache`,
whose base `7e04250` is in `main`. Its PR targets `main`. It is CI only, with
no version bump, and waits for Rodrigo's go to push.

**Proposed:** typography verify FAILs correct lines drawn in a face whose
units-per-em is not 1,000 (the last row).

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, night (historical snapshot)

**Main is v68 at `aa54158`.** Rodrigo said "merge", and the app's session
merged #36 and then #37, each with a merge commit. GitHub confirms both:
- #36, R-04 at v67 and the v66 delivery record: merge `9cfcf63`, pinned to
  the reviewed head `43ec91c`, with CI green.
- #37, R-27 at v68: merge `aa54158`, pinned to `7a9d1a5`. The app's session
  retargeted it from the R-04 branch to `main` first. Main's tree after #36
  equals the tree #37's CI tested against, and main's tree now equals
  `7a9d1a5`'s.
- Main's own CI run on `aa54158` passed: ubuntu and windows py3.14 and the
  plugin manifest.

**For a consumer, v67 and v68 change this:**
- A run drawn in an italic or bold-italic face has a canonical text layer,
  so a correct italic page no longer FAILs verify on NBSP spaces.
- `field_fonts` embeds a variable face as its Regular instance, and
  `FieldFontsResult.instance` names the pins (`''` for a static face).

**Adoption:** none yet. The app stays on v54 until its Python 3.14
migration.

**Built, not pushed:** R-47 at v69, on `perf/r47-typography-verify-page-rects`,
whose base has `main`'s tree. It waits for Rodrigo's go to push.
*Update:* Rodrigo approved it; it is PR #38 against `main`. R-69 with R-97 is
built on `ci/r69-r97-discover-and-font-cache`, stacked on #38. It is CI only,
with no version bump.

**Proposed:** typography verify FAILs correct lines drawn in a face whose
units-per-em is not 1,000 (the last row).

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026, later (historical snapshot)

**Main is v66 at `637e291`.** Rodrigo merged #35, with a merge commit, and
the app's session relayed it. The merge was pinned to the reviewed head
`2ff7746` after the ubuntu and windows py3.14 jobs and the plugin manifest
job passed. It carried R-05 and R-06, the v65 delivery record and the
product's hold on the verify `--flag=value` proposal.

**For a consumer, v66 changes this:**
- A legacy build refuses an output or scale-report path that names one of
  its inputs (`refusals['output_aliases']`), and `rebuild` refuses such an
  OUT with exit 2.
- Text between inline tags, a notice's text and a shaped run land as
  written.

**Adoption:** none yet. The app stays on v54 until its Python 3.14
migration.

**Built, not pushed:** R-04 at v67, on `fix/r04-canonicalize-role-faces`.
It waits for Rodrigo's go to push.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 25 September 2026 (historical snapshot)

**Main is v65 at `a9fd0a9`.** Rodrigo merged #34, with a merge commit, and
the app's session relayed it. The merge was pinned to the reviewed head
`4cf1054` after the ubuntu and windows py3.14 jobs and the plugin manifest
job passed. It carried two things:
- the v64 delivery record;
- R-02, whose row below records the evidence.

**For a consumer, v65 changes this:**
- A shrunk run is drawn at the size that fits its room, never larger than
  its source, and the 0.7× gate sees that ratio.
- Small print that needs less than 0.7× refuses with the existing line, and
  `allow_scale` ships it at the fitted size.

**Adoption:** none yet. The app stays on v54 until its Python 3.14
migration.

**In progress, not pushed:** the quick wins R-05 and R-06, on
`fix/r05-legacy-output-alias` as v66. How they are grouped into PRs is
Rodrigo's call.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 24 September 2026, late (historical snapshot)

**Main is v64 at `154f842`.** Rodrigo merged two PRs in order, each with a
merge commit, and the app's session relayed the merges. Each merge came
after the ubuntu and windows py3.14 jobs and the plugin manifest job passed
on the tested head. `154f842`'s tree is the tested `8c1f4ca`'s.

| PR | contents | version | merge commit |
|---|---|---|---|
| #32 | R-03 and R-01 recorded as delivered; item 3 started (docs only) | 63 | `c0d49e9` |
| #33 | item 3, the `/Rotate` page, with R-64 | 64 | `154f842` |

**Delivered:** item 3 with R-64. Its row below records the evidence.

**For a consumer, v64 changes this:**
- On a `/Rotate` page, `segments.json` geometry is in the unrotated space,
  the space `page.get_text` uses.
- `segments.json` gains an additive `geometry` key.
- A `segments.json` without that key, on a rotated page that carries
  segments, is refused as a stale extraction.
- `retypeset.direction_limit` takes a frame rect; it is not in `__all__`.

**Adoption:** none yet. The app stays pinned to v54 on Python 3.12, and
Rodrigo is still to rule whether N1 waits for the 3.14 migration.

**Next:** R-02, the 4.0 pt clamp (review priority 4). The assignment order
and the shared acceptance bar are unchanged; they are in the snapshot of
"24 September 2026, later" below.

**Unchanged:** E12 is blocked on its six rulings, and R-94 is "not yet".

## Coordination status — 24 September 2026, evening (historical snapshot)

**Main is v63 at `0819091`.** Rodrigo merged three PRs in order, each with
a merge commit, and the app's session relayed the merges. Each merge came
after the ubuntu and windows py3.14 jobs and the plugin manifest job passed
on the exact head.

| PR | contents | version | merge commit |
|---|---|---|---|
| #29 | the review, its assignment and the declined clip-mode proposal (docs only) | 61 | `bcb32f3` |
| #30 | R-03 | 62 | `e5be31d` |
| #31 | R-01 | 63 | `0819091` |

**Delivered:** R-03 and R-01. Each row below records its evidence.

**Adoption:** none yet. The app stays pinned to v54 at `9675c61` on Python
3.12. Adopting v63 means the app's Python 3.14 migration plus an exact
pin. Rodrigo is still to rule whether N1 waits for it.

**Next:** item 3, the `/Rotate` blank page, with R-64. The cause is
diagnosed and the fix is being designed. The assignment order and the
shared acceptance bar are unchanged; they are in the snapshot below.

**E12:** still blocked on its six rulings.

**R-94:** Rodrigo ruled "not yet" on 24 September, so the repository stays
public for now.

## Coordination status — 24 September 2026, later (historical snapshot)

**Main is v61 at `988b787`.** PR #28 merged the earlier status below, the
E12 row and its measurement. Docs only.

**Assigned: the review's findings, in the product's order, while E12 is
blocked.** The library reviewed itself (`docs/REVIEW-2026-09-24.md`: 110
items, the top twelve each reproduced twice) and proposed the findings to
the product. Rodrigo ruled A on 24 September, relayed by the app's session:
build them in the order below. The request of record is the app's
`docs/reference/REQUEST-to-skill-review-2026-09-24.md`; it is provenance
only and was not opened here. The rows at the bottom carry each ID. In
priority order:
1. R-03;
2. R-01;
3. the `/Rotate 90` blank page (diagnosed first), with R-64;
4. R-02;
5. the quick wins, XS each: R-05, R-06, R-04, R-27, R-47, R-69 with R-97,
   R-33, R-40, R-42, R-110, R-100, R-99, then the docs items R-79, R-80,
   R-82 and R-83;
6. performance: R-51, then R-48 with R-49, then R-50.

**E12 comes first again the moment its six rulings arrive.** R-106 stays
with E12.

**Held, not assigned:**
- group C (R-09 to R-25), because the app runs no library verify today;
- group E (typography-1 at scale), because the app has not adopted it.

Group F (repository hygiene) and R-94 (repository visibility) are
Rodrigo's.

**Acceptance for every item:**
- a test that fails on the unfixed code with the item's one-defect PDF and
  passes after the fix;
- Rule 1, plus a rendered pixel comparison, for the drawing, font and layout
  items (R-01, R-02, R-03, R-04, R-06, R-27, R-33);
- for strip changes, a re-run of the 17-PDF wild probe with a render diff;
- one PR per item or small batch, for Rodrigo to merge;
- a version bump, and a notice to the app, for every shipped change.

Performance items must also leave the output identical, shown by a render
or byte diff. No adoption is implied: the app stays on v54 on Python 3.12
until its 3.14 migration, with an exact pin.

## Coordination status — 24 September 2026, earlier (historical snapshot)

**Main is v61 at `0542dc2`.** Since the 23 September status below, PRs #23
(the old B1 checkout reconciled; B1 stays deferred), #24 (A02) and #25 (A06,
with the bump to v61) have merged; #26 added handover notes, and #27
delivered GOV-2026-09-24 (the row at the bottom), docs only. All four
version sources say 61, CI passed on `0542dc2` (run 35981365585), and there
is no release or tag. For a consumer, v61 changes two things:

- **A02, page parity.** Every verify run prints one `page parity` line, and a
  missing, extra, rotated or resized page FAILs the new `page-parity` gate.
  `compare` and `render` show every page and exit 1 when the page counts
  differ; `finish` returns compare's code. Evidence:
  [a02-page-parity](reviews/2026-09-23-a02-page-parity.md).
- **A06, rebuild checks the mapping.** A default legacy `pipeline.py rebuild`
  verifies against the mapping it built from, so an empty target, a dropped
  marker or a translated identifier exits 1 where it used to exit 0.
  Evidence: [a06-rebuild-mapping-checks](reviews/2026-09-23-a06-rebuild-mapping-checks.md).

No consumer pin changed here; the app last reported v54.

**The product has the v61 notice.** On 24 September this library's session
sent it, with the question of what to prioritize, by `SendMessage` to the
app's session on the Mac. The app acknowledged v61 and keeps its pin at v54
(`9675c6196c14eb2a2d37d34e371391eb1955a386`) on Python 3.12. v61 requires
Python 3.14, so adopting it is an app migration, and none has been decided.

**Assigned: E12, priority 1 of 1** (the row at the bottom). Asked what to
prioritize, the app first answered that the priority was Rodrigo's call
and put the question to him. He ruled on 24 September (option C): the app's
pending work is N1, then N2 (beta hardening) and N3 (Next 16), then the
process-boundary migration, then N4 to N9. N1 and N3 need nothing from this
library. E4 and E5 serve the app's N6, which now comes after the migration.
The only library behaviour on the near path is N2's output size, so the one
assignment is E12, a compact, deterministic output save. Nothing else is
assigned, and Rodrigo directs library tech debt himself
(`docs/DECISIONS.md`, 2026-09-24). E12 is blocked before any build: the
measurement ([reviews/2026-09-24-e12-measurement.md](reviews/2026-09-24-e12-measurement.md))
found three of its acceptance checks in conflict, and six rulings are with
the product.

The 16 September sequence below ("E4–E7 in that order, E8–E11 in the gaps")
is no longer the order of record. The app reports that its own work-order
file said so in a status update of 19 September, and that its `ROADMAP.md`
§2 is canonical, with E12 recorded there too; neither file was opened here.
Of the 16 September rows, E2 and E3 have shipped although their status
cells below still read accepted: gates 19, 20 and 21 (PRs #6, #8 and #10,
v52 to v55) and the consumer surface (PR #13, v58; C7 moved to E8). E4 has
not started: no schema file for the verify report is published and its
gates carry no severity or category. E10 waits on the operator's choice of
distribution name.

**Proposed by this library; not assigned.** The app took these to Rodrigo in
the same pass, and his ruling left them unassigned. None of them has started:

- **A21**, the smallest backlog item: validate both manifests explicitly and
  give the type checker its declared environment. Two XS slices; see
  [PROGRAM.md](../dev/goals/PROGRAM.md#public-readiness-backlog).
- **A macOS test finding**, from setting this checkout up on a Mac. On
  `221a86f` the Mac ran CI's 695 tests with one failure:
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`
  compares `os.getcwd()` with the temporary path as strings
  (`tests/test_pipeline.py:3958`), and macOS reports `/var/…` as
  `/private/var/…`. Compared by `realpath`, the same run exits 0 and prints
  its PASS line, so the library is not at fault. CI runs Linux and Windows
  only. XS.
- **The open P1 audit items:** A04 (process-isolated concurrency
  validation), A05 (proven dependency floors) and A14 (review freshness,
  which needs a behaviour ruling first). A07 and A08 wait on owner
  decisions. The rest of the backlog is in PROGRAM.md.

## Coordination status — 23 September 2026 (historical snapshot)

**Main is v60 at `178a06f`.** Since the 20 September snapshot below, PRs
#12/#13 (v57/v58), #17 (typography, v59), #18 (Python 3.14 only), #19 (opt-in
refusal capture, v60), #20, #21 and #22 (A01 invalid-review refusal, A03
rebuild-report invalidation, cleanup) have all merged. PR #22 changed shipped
behaviour without a version bump, so `178a06f` and `b20fadd` both say v60; the
next integration picks the number. The app reports it still runs library v54 at
`9675c6196c14eb2a2d37d34e371391eb1955a386` on Python 3.12. Adopting current
main needs its own Python 3.14 migration and a same-input comparison, which the
app owns. No consumer pin or runtime changed here.

**B1 stays deferred.** The design is approved. The synthetic probe, the
baseline-anchor probe and the known-success capture are complete. No genuine
fit-refusal case exists, and none of that work is an implementation. Opt-in
refusal capture (v60) is how such a case would arrive.

**Next library work:** A02 (legacy page-count verification), then A06
(mapping-dependent checks on the default rebuild), each as a separate change
from main. `dev/goals/HANDOVER.md` has their state. Nothing here is a new
assignment to the app.

## Coordination status — 20 September 2026 (historical snapshot)

**Only B1 is deferred, not the product roadmap.** Its canvas and page-count
ruling are approved; the synthetic probe and real-job capture are complete.
The capture replayed a known success. Further B1 work awaits genuine fit-refusal
evidence and explicitly permitted boxes before testing wrapping. No B1 plan or
implementation is underway. See `dev/goals/HANDOVER.md` for the current evidence.

The v57/v58 work described below has open PRs #12/#13. A branch described as
"built" or "done" does not establish that the product has adopted it; consumer
adoption must cite its actual library version and pin. The captured form used
v54. Historical work orders below are not fresh assignments to another session.

**Typography adoption disposition, 20 September:** the app requested source
serif/sans class and meaningful within-line emphasis preservation without relaxing
its product requirement. No delivered documented API inspected satisfies both.
A same-source probe reproduces lost family/span information at the app-reported
v54 pin, main v56 and open-PR v58. Read the [bounded disposition](reviews/2026-09-20-typography-capability.md)
for existing manual controls, occurrence-selector limits and ownership. Rodrigo subsequently requested proceeding with the typography prerequisite.
Rodrigo approved the additive approach and subsequently the written
[typography design](design/typography-preservation/README.md). The
[implementation plan](plans/2026-09-20-typography-preservation-brief.md) now awaits
his review and execution-method choice; implementation has not started.
The disposition below remains evidence for the existing APIs. No implementation,
new consumer pin or wider app routing is promised.

**Audit follow-ups recorded 19 September:** the current library/skill backlog is
in [PROGRAM.md](../dev/goals/PROGRAM.md#public-readiness-backlog). Its A-IDs are
scoped follow-ups to the existing work, not a second product roadmap:

- E1/C4's earlier fixes do not cover a stale successful PDF/report after rebuild
  refuses before verification; see **A03**.
- C5's stdout-isolation fix does not establish native-backend thread safety.
  **A04** is partial: the library guidance now requires separate processes and
  job directories; process-isolated validation is still open. See the
  [20 September wording evidence](reviews/2026-09-20-concurrency-guidance.md).
  Worker integration remains app-owned and has not been inspected or reassigned
  here. The historical thread-pool request below is not current guidance.
- C3's general serialization/immutability promise needs qualification for QA and
  nested collections; see **A12**, coordinated with E4.
- C8/E11's dependency support needs an actually proven lower bound; see **A05**.
- E10 remains the home for package identity, licenses and release contents;
  see **A07/A08/A13/A20**, rather than duplicating that epic.

The audit is [local reproduced evidence](reviews/2026-09-19-public-readiness.md),
not a new product-side report or implementation authorization. Current status
and closing checks live in PROGRAM; the historical rows below are preserved.

## Ownership split — approved by Rodrigo

| Responsibility | Accountable owner |
| --- | --- |
| Final priorities, scope changes, and product tradeoffs | Rodrigo |
| Product roadmap, user outcomes, app/service work, integration, and real-job evidence | PDF Translator app task |
| Shared PDF engine, reusable API, rendering behavior, and library tests | This library task/repository |

The app task maintains **one existing product roadmap**, linking engine
requests into this inbox rather than creating a second implementation queue.
This inbox records library requests and technical delivery status; it does not
compete with the product's priority order. The app imports the shared library.
Product-specific UI and orchestration remain in the app.

To prevent duplicate work, each cross-repository item needs a stable ID, one
implementation owner per component, current state, blocking dependency, and a
link to its evidence/PR and required library pin. Each task checks that entry
before starting and updates its owned status when handing work back. A changed
priority or conflicting requirement returns to Rodrigo rather than being
silently resolved differently in each repository.

**Coordination complete:** Rodrigo selected A, adopting this split and
authorizing the message to **Boot Spire Tech web app**
(`01a0bc1c-cdb2-7b93-8860-0154a450beb4`). The app task confirmed that its existing
roadmap and companion status documents now record the alignment. Its reported
canonical roadmap is
`C:/Dev/pdf-translator/.spire/clusters/tech/context/ROADMAP.md`.
That file was not opened here; this records the owning task's confirmation.

**App-reported status, 20 September:** N1's seven approved screenshot-reference updates
are complete, with fresh independent verification of **331/331, zero skips**.
This does not close all of N1: the known frontend baseline and historical
process records remain separate closure obligations.

The next available product action is **app-owned preparation of a reviewable
CI authentication arrangement for the private library dependency**. Credential
provisioning and push/merge/deploy remain operator-controlled. This is a status
snapshot from the owning task, not an assignment or authorization for the
library task to perform that work. No new library implementation is assigned.

<details>
<summary>Technical detail (skip freely)</summary>

The app reports that the roadmap's opening ownership note and section 2
component register include stable IDs, one implementation owner per component,
state, blocking dependencies, evidence/PR pointers and adoption pins. Companion
records are `PROJECT_CONTEXT.md` and `INDEX.md` in the same context directory,
plus `C:/Dev/pdf-translator/docs/reference/WORKORDER-skill-2026-09-16.md`.
These paths are provenance only; no product files were inspected here.

No unresolved duplicate implementation assignment was identified in the app's
bounded alignment. Historical N2 save/subset and N6/E5 wording that assigned
reusable rendering behavior to the product is superseded: the library owns
reusable behavior/rendering; the app owns integration, product policy and
evidence. New priority or scope conflicts return to Rodrigo.

The app reports adoption remains `pdf-translate 54.0.0`, pinned at
`9675c6196c14eb2a2d37d34e371391eb1955a386`. B1 alone remains deferred. No library
files, pin, PRs #12/#13, push, merge, or implementation assignment changed in
this documentation alignment. This repo independently rechecked #12/#13 open
with unchanged heads; product-side file contents and deployment were not
independently inspected.

</details>

## Format

`date | what the product needs | why | status`

- **date** — ISO, when the request was filed.
- **what the product needs** — a behaviour, stated as an outcome ("given X,
  produce Y"), not an implementation.
- **why** — the concrete case that surfaced the gap.
- **status** — `open`, `accepted` (being built independently here),
  `declined` (with a one-line reason), or `done` (with the version/commit
  that shipped it).

## The work order of 2026-09-16

The product's work order of 2026-09-16 is the request of record on its side
(its `OPEN_THREADS` §19). It arrived as behaviours and acceptance criteria,
no code. Its rulings are inputs to this repo, recorded here so no session
asks again:

- **R1** — 2d, missing glyph: refusal wins. A job whose face cannot draw a
  character is refused (what ships today); no placeholder glyph, no borrowed
  face.
- **R2** — Tasks C (Thai), D (Hebrew niqqud), E (eight Indic scripts):
  parked from the product's side; reversal condition "the product adds a
  target language in that script". The standalone skill may still do C.
- **R3** — Target languages sold today, the only ones step 2 must not
  regress: es pt fr de it pl ro tr vi uk ru zh-Hans ja. Next candidates on
  demand data: ar hi th. Faces: the Noto family, per language, shipped by
  the product.
- **R4** — The Han-forms gate: yes, as designed in
  `docs/reviews/2026-09-16-cjk-request-assessment.md` §3 item 3 — REVIEW
  when the probe characters are not drawn, when no reference face is
  available, or when neither control matches. The product ships both
  reference faces so PASS is reachable in production.
- **R5** — How the verdict is used: the product always passes `lang`,
  always builds faces with `prepare_font`, never sets `fail_on_review`;
  REVIEW is an advisory notice; a verify FAIL is a needs-attention notice
  **and the document is still delivered** — a verify FAIL must never delete
  or withhold the output file; only a build refusal (retypeset) withholds
  it, and build refusals map to job-fatal closed causes.
- **R6** — Obstacle-bounded placement: still not asked for. Publishing it
  under MIT needs an operator ruling first; nothing here builds toward it.

Answers on record (asked once, answered in the work order): the product runs
Python 3.12 (keep `>=3.10` here) and PyMuPDF 1.28.0 (this repo tests on
1.28.2; one version is chosen at step 2, not now); its LLM authors
`translations.json` through a structured protocol, including `merges.html`
and `notices`, no human; it consumes the verify report and `scale_report`
only — not compare HTML, bilingual output or the reviewer checklist; a "form
job" is one with AcroForm widgets or a class (court / government / medical)
the product decides — the library decides "has widgets"; threads today,
processes later, so no global state; customer PDFs are never sent as
fixtures — findings and constructed corpus cases are the loop; RTL stays in
the skill (excluded from the product's MVP, a product decision); urgency:
E1 now, E2 in flight, E3 before the product's step-2 council (weeks), E4–E7
in that order, E8–E11 in the gaps; the product reviews PRs read-only on
request and never merges.

The product reviewed this transcription read-only on 2026-09-16 (with PRs #6, #7 and #8): faithful, no MUST, NEVER or ALWAYS softened; two compressions it does not want changed — R1 omits "the product surfaces it as a closed cause", R4 omits "(non-Noto family)". Its verdicts: #7 adopt as is (E1 done); #6 adopt — its own engine lets the six small kana counters ゎ ゕ ゖ ヮ ヵ ヶ begin a line, so a REVIEW on one of them is a known difference (now stated in `references/gates.md`); #8 adopt — the product sets no `/Lang` and its pipeline holds display-name language values (`Japanese`, `日本語`), so normalising `lang` to a BCP 47 tag and shipping the two reference faces are its step-2 prerequisites; on its suggestion a `lang` that is not a tag is now REVIEW, not silence. The probe characters 直 骨 海 came from the product's request as behaviour, in words; the measurement and the gate are this repo's.

Not asked for: obstacle-bounded placement (R6), any code from the product
repo, a plausibility judge, breadth for its own sake, merging, pushing or
deleting anything.

## Requests

| date | what the product needs | why | status |
|---|---|---|---|
| 2026-09-16 | **E1 — the stale report.** After a passing run with `--report PATH` (or `pipeline.py rebuild`'s `<work>/verify_report.json`), an unwritable target, and a failing run to the same path, no report at the path claims `exit_code 0`: either no file, or one describing the failing run. The exit code and the `(could not write …)` line stay as they are. | PR #5 defect 1: the report on disk said PASS for a job that failed, attributed to a document the consumer did not ask about. | **done** — v53, branch `fix/stale-verify-report` (abbfbcb, 264b1ac), PR #7 stacked on #6: remove-before-run, temp file + `os.replace`, remove-on-failure; best effort where the directory itself cannot be written (`references/gates.md`, `docs/DECISIONS.md`); evidence `docs/reviews/2026-09-16-stale-verify-report.md`. |
| 2026-09-16 | **E2 — finish CJK parity.** The kinsoku gate on the drawn lines (PR #6 as-is); then the Han-forms gate per R4 with Rule 1 (a verifier on another model re-runs red — a Japanese job set with the SC face — and green, and looks at 600 dpi renders); then task F, the spaceless leak scan, measured first. Acceptance: three new gate lines, each shown red on a constructed job, each with findings; console parity on the nine non-CJK jobs. | The product sells ja and zh-Hans (R3) and has shipped its Japanese face and kinsoku on its side. | **accepted** — kinsoku shipped as gate 19 (REVIEW) in v52, PR #6 open and green; the Han-forms gate is measured (`docs/BRIEF-han-forms-gate.md`, `dev/probes/han_forms_probe.py`) and built as gate 20, v54, on `feat/han-forms-gate` (plan `docs/plans/2026-09-16-han-forms-gate.md`, evidence `docs/reviews/2026-09-16-han-forms-gate.md`: 45 tests, suite 368, console parity identical, an Opus whole-branch review with two fix waves, Rule 1 verified by an independent pass) — merged 2026-09-16 (PR #8); task F built as gate 21 `leak-cjk` (v55, `feat/cjk-leak-tell`, measured in `docs/BRIEF-cjk-leak-tell.md`: the verbatim rule is blind to an echo, a repertoire tell is not) — push and PR are the operator's. |
| 2026-09-16 | **E3 — step-2 readiness (C1–C10).** Every stage callable as a function per C1; results per C3; progress and cancellation per C4; concurrency per C5; determinism per C7; no network per C9; logging per C10; a consumer guide in `references/` that an engineer with zero context follows to run one document end to end from Python and read every output file. Acceptance: `tests/test_consumer_contract.py` — one document through every stage as function calls with stdout captured empty; two concurrent jobs; a cancel between pages leaving no file; sha256 determinism; a fixed-timestamp option; the eleven CLIs byte-identical (parity runner). Rule 1 for anything touching drawing, not for plumbing. | The product's step-2 council needs a library a service can call; weeks, not days. | **accepted** — after E2; about a week; the product writes its step-2 brief against the consumer guide meanwhile. From its PR review of 2026-09-16: the consumer guide must state the BCP 47 requirement for `lang` near the top with an explicit "not a display name" example, and name the reference font files the Han-forms gate needs (`NotoSansJP-VF.ttf`, `NotoSansSC-VF.ttf`) and what the gate does when they are absent. Design pass done 2026-09-18 (`docs/design/E3-consumer-surface/`, eight artboards, measured against v56). **C7 moves to E8** on that pass's sizing: E3 as filed is 8.5–9.5 days against the week accepted, and determinism is the one item whose size is unknown until a probe runs; E8's own acceptance already reads "the C7 determinism test gates", so the implementation belongs beside it. Without C7, E3 is ~7 days. Both PR-review asks are already satisfied elsewhere and the guide will point rather than re-derive: `references/translations-format.md` states the BCP 47 rule with the "not a display name" example, `references/fonts.md` names both faces and the absent-face behaviour. |
| 2026-09-16 | **E4 — findings to product notices.** One combined, versioned report: the verify report's JSON schema published as a file in the repo, versioned by `schema`; `qa_check`'s findings folded into the same envelope (or a sibling with the same envelope); each gate carries a machine-readable severity (`blocks-delivery` / `needs-attention` / `advisory` / `informational`), a category (`structure` / `layout` / `text` / `metadata` / `script`) and a `consumer-eliminable` flag (`metadata-lang`, cannot-attest); REVIEW gates always carry a finding (true since 1f42204; keep the invariant test). Acceptance: the schema file validates every report the suite writes (jsonschema in the test); a gate → severity/category table in `gates.md`; a schema bump rule in DECISIONS. | The product maps gate names to its closed notice codes without reading Python. | **accepted** — after E3; 1–2 days. |
| 2026-09-16 | **E5 — the compliance notice as data, and a placement call.** Reviewed notice strings for the 13 languages in R3, both variants ("file the official version" and "unofficial translation"), with the `{form title}` slot, each marked native-checked or not (never present unchecked as checked); a placement routine that, given the page and the notice, places it in existing room (foot of page 1, margin) at a readable size, never shrinks the form's own text, never adds a page, and returns whether it fit, where, and at what size — "did not fit" is a finding, not a silent drop; a verify line that the notice is present and readable (ink + text layer) when the mapping declares one. Rule 1 (drawing). | Official-looking copies of official forms need the page-1 notice from `references/compliance.md` without an LLM authoring legal text at run time. | **accepted** — after E4; 2–3 days plus reviewers. This repo can author and place the strings and will mark every one unchecked; native review is outside it and stays with the operator. Meanwhile the product ships the English wording translated by its protocol and flagged machine-translated. |
| 2026-09-16 | **E6 — fonts for a service.** `references/fonts.md`'s language → face table as machine-readable data with the OFL source and sha256 of each face; `prepare_font` takes a cache directory so instancing a variable TTF happens once per (face, charset), measured before/after on the Japanese eval; one subset per document, never per page, with a corpus ceiling (output bytes ≤ 2.5× input for text-only fixtures, measured ratios stated); `field_fonts` on by default for a form job and off for a non-form job, decided from the document, the decision in the strip/extract result. Rule 1. | A service applies a per-language face policy without a human choosing files. | **accepted** — after E5; 3–4 days. The product fixes its own per-page subsetting itself. **2026-09-24:** the "one subset per document, never per page" bullet moved to E12, which is assigned; the rest of this row stays accepted and unassigned. |
| 2026-09-16 | **E7 — hostile-input hardening.** Bounded wall-clock and memory per page on malformed input — deeply nested XObjects, recursive resource dictionaries, a 10,000-page skeleton, a 20,000 × 20,000 image, a broken xref PyMuPDF repairs, a stream inflating 1000× — each finishing or refusing within a stated ceiling, never hanging, each with a constructed fixture in `corpus/` and a recorded verdict; never execute or preserve document JavaScript or launch actions, with a per-item decision (stripped, kept or reported) for `/OpenAction`, `/AA`, `/JS`, `/Launch`, `/URI`, `/EmbeddedFiles` in DECISIONS; XFA removal kept; certified / Reader-extended handling documented as it is; a seeded fuzz smoke in CI gating on "did not hang or crash". Independent read of the decisions table. | A service receives strangers' PDFs; a skill received the user's own. The product bounds size (100 MB), pages (200) and refuses encrypted files before calling. | **accepted** — after E6; 3–5 days. |
| 2026-09-16 | **E8 — performance and determinism as a published number.** A benchmark script over the corpus printing per-stage wall-clock and output size per fixture; the numbers in a dated, machine-named table in docs; CI prints them and does not gate on them; the C7 determinism test gates. | Numbers a consumer can plan against. | **accepted** — in the gaps; 1 day. **Gains C7's implementation** (moved here from E3 on 2026-09-18): E8's acceptance already gated on the C7 determinism test, so the fixed-timestamp option and whatever the byte-diff probe finds now land beside the numbers rather than in E3. The probe ran on 2026-09-18 (`docs/BRIEF-determinism.md`) and the answer is small: only `/ID` varies, so C7 is a `doc_id=` parameter and a test, not an epic. **This row is back to about 1 day plus half a day for C7.** The caveat that stood here — determinism measured on a one-page job only — is **closed**: both named fixtures were run on 2026-09-18 and neither `choice_fields.pdf` (3 widgets) nor `dense_table.pdf` (25 cores) produces a second varying key, so the brief's design is sufficient and the sizing stands. E8's first red test is the one open question: that a caller-set `doc_id` survives `ez_save`. **2026-09-24:** E12 needs C7's caller-supplied `doc_id` at its save, so that question is now E12's; the benchmark stays here, unassigned. |
| 2026-09-16 | **E9 — the skill's own placement defects.** `docs/REVIEW-2026-09-04.md` F1 (a vertical rule is not an obstacle, so a cell's translation crosses the table border), F2 (a line takes its size from its first span, so a large bullet inflates a small line), F3 (a fixed pad shrinks a run for no reason). Rule 1. | Named so the skill knows the product will not contribute code for them (R6); the corpus already shows each. | **accepted** — this repo's own order and way. |
| 2026-09-16 | **E10 — packaging and release.** A distribution name before the first publish (`pdf-translate` is taken on PyPI as of 2026-09-16; `pdftranslate`, `pdf-translate-skill`, `pdf-translate-core` were free; the import name stays `pdf_translate`); SPDX `license = "MIT"` (the table form is deprecated); wheels built in CI on a tag; a CHANGELOG, one line per version, what changed for a consumer; version semantics written down (a new gate line is additive; a schema bump is breaking; a console change is a note); the four-way lockstep kept. | The product pins an exact version and needs to know what a bump means without reading every diff. | **accepted** — 1 day once the operator picks the name; the name is the operator's call. |
| 2026-09-16 | **E11 — corpus and evals as the shared oracle.** A stable `verdicts.json` schema; a runner that exits non-zero on any drift from recorded verdicts and prints the diff; fixtures generated, not committed; the three evals runnable headless with a documented expected-files check; a coverage matrix in docs — which of the 13 languages × {form, non-form} has a corpus case and which does not; `evals/permission-slip-japanese` kept working. | The product pins the version and runs this corpus in its CI as the step-2 acceptance oracle. | **accepted** — 1–2 days. Today `corpus/verdicts.json` is a flat file → verdict map with no version field (see C8). |
| 2026-09-16 | **C1 — stages callable without a CLI.** strip → extract → [the product authors the mapping] → prepare_font → retypeset → verify → field_fonts, each a function taking explicit paths or bytes and returning data, raising a typed exception on refusal; no argv parsing, no printing unless asked, no `sys.exit`, no dependence on the working directory, no reading of files the caller did not name. | Step-2 acceptance. | **open** (E3). Today: `pdf_translate` exports a function per stage; `run_verify` and `run_qa` are silent and return verdicts; the others return exit codes and print (`prepare_font` 10 print sites, `retypeset` 32, `extract_segments` 11, `strip_text` 2); no stage calls `sys.exit` or `os.chdir`; only the CLI `main()`s parse argv. **done** — v58, branch `feat/consumer-surface`: each stage has a silent `run_*` twin taking explicit paths, returning a schema-versioned frozen result and raising a typed exception; nothing prints, nothing exits, nothing resolves against the working directory (`run_extract` requires `outdir`, `run_retypeset` takes `resource_root=` defaulting to the mapping's directory, and `Archive('.')` is gone from `retypeset` and `shaping_probe`). The bare names keep their exact signatures, printed bytes and return codes. `references/consumer-guide.md` is the document; every code block in it was run. |
| 2026-09-16 | **C2 — inputs.** The original PDF; a mapping exactly per `references/translations-format.md`; fonts prepared per target language by `prepare_font`; nothing else assumed present. | Step-2 acceptance. | **holds today** — `translations-format.md` is the contract; pinned by E3's contract test. |
| 2026-09-16 | **C3 — outputs, machine-readable and schema-versioned.** The translated PDF; the verify report (schema 1, with findings); `scale_report`; the extractor's warnings; a stage result for strip (what was removed: XFA, actions, counts). A consumer explains every outcome from these files alone. | Step-2 acceptance. | **open** (E3). Today: the verify report yes (schema 1 since v51); `scale_report.json` is written by retypeset without a schema field; the extractor's warnings and the strip result are printed, not returned. **done** — v58. Every stage returns a frozen dataclass whose `to_dict()` carries `schema` and `version` (`pdf_translate/results.py`), and every refusal is a typed exception carrying `refusals`: each refused item by kind, **with the core untruncated**. Corrects this row's earlier note that results were printed and not returned — `verify` and `qa_check` already returned verdicts; the other five did not, and now do. `scale_report.json` also gains the envelope and is written atomically. |
| 2026-09-16 | **C4 — progress and cancellation.** A caller learns "page n is done" during retypeset (callback or generator) and can stop between pages, leaving no partial file at the output path. | The product streams progress to a browser. | **open** (E3). Nothing today. **done** — v58. `run_retypeset(progress=, cancel=)`. `progress(done, total)` fires once per unit and the total is **pages plus merge jobs**, because retypeset runs two loops; `cancel()` is checked at the top of every unit in both. There is one save, at the end, so a cancelled run cannot leave a partial file — `RetypesetResult(cancelled=True, output=None)` and nothing at the path. |
| 2026-09-16 | **C5 — concurrency.** Several jobs at once in one process from a thread pool: no module-level mutable state, no `os.chdir`, no fixed temp names, no shared caches without a lock; documented; a test runs two jobs concurrently and both verify PASS. | Threads today, processes later. | **open** (E3). No `os.chdir` anywhere today; the Han-forms reference cache (E2) is written atomically with this in mind; the audit is E3's. **done** — v58, and it was a real defect, not a gap: `run_verify` was silent by `redirect_stdout(io.StringIO())`, which replaces the **process's** stdout, so one thread inside it silenced every other thread in the host. Now the gates log and no handler is attached. Two concurrent jobs both verify PASS; `scale_report=` lets each job name its own report instead of racing for a fixed name beside the output. |
| 2026-09-16 | **C6 — bounded resources on hostile input** past what the product bounds (100 MB, 200 pages, no encrypted files). | A service receives strangers' PDFs. | **open** (E7). |
| 2026-09-16 | **C7 — determinism.** Same inputs → byte-identical output PDF when the caller supplies a fixed timestamp (and `/ID` is derived from content or supplied). Verify-by: the corpus run twice, sha256 equal per output. | The product's goldens rest on it. | **open** (E8 — moved off E3 on 2026-09-18, since E8's acceptance already gated on this test and the size is unknown until a probe runs). Today `retypeset` sets metadata but has no fixed-timestamp option, and `apply_document_metadata` (`retypeset.py:354`) deliberately never touches `/ModDate`, `/CreationDate`, `/Producer` or `/ID`; `doc.ez_save(out)` (`retypeset.py:1387`) is called with no arguments. **Measured 2026-09-18** (`dev/probes/determinism_probe.py`, brief `docs/BRIEF-determinism.md`, PyMuPDF 1.28.2): on a one-page job, two runs differ in **`/ID` alone** — 29 bytes of 325,777. Content streams, the embedded font program and the `/Info` dates are already byte-identical, because `apply_document_metadata` carries the source's dates through rather than writing "now". The output path does not leak; the clock does, and only into `/ID`'s second element (the first is stable across five runs). **So no `timestamp=` parameter is needed**: C7 reduces to pinning or deriving that one value. Design in the brief §4 — a `doc_id=` parameter on the silent twin, no default, no derivation policy in the library. **Re-measured the same day on the two corpus fixtures the brief named**: `choice_fields.pdf` (3 form widgets) and `dense_table.pdf` (25 cores) both give the same answer — `/ID` element 2 alone, element 1 stable, no second key. Widgets and 25× the placement work add no varying byte, so the sizing holds. The path-does-not-leak claim was also re-derived properly: the first pass inferred it from two runs assumed simultaneous, which a clock tick can fake, so the probe now groups runs by `/ID` element 2 and compares only inside one tick (brief §2.2). One thing remains unmeasured and belongs in E8's first red test — whether MuPDF honours a caller-set `/ID` through `ez_save` at all. **2026-09-24:** E12 needs this `doc_id` at its save and answers that question. |
| 2026-09-16 | **C8 — versions.** Python `>=3.10` here (product 3.12); an exact skill pin; the PyMuPDF window as declared (`>=1.24,<1.30`); the PyMuPDF/MuPDF version each corpus verdict was recorded on stated; one version chosen deliberately at step 2. | The product's attestation is identity-locked. | **open** (E11), and the Python half changed. `pyproject.toml` declared `requires-python = ">=3.10"` when this row was written (confirmed 2026-09-16); since PR #18 on 2026-09-21 it declares **`>=3.14`**, matched by the `compatibility:` line, the README and a CI matrix that now tests 3.14 only. The row said "product 3.12"; the consumer has since reported measuring its own suite on CPython 3.14 — full dependency tree resolving with wheels for PyMuPDF and pikepdf, 990 passed and one failure that is its own deliberate 3.12 tripwire — and has said it does not need the 3.10-3.13 floor restored. That is the consumer's measurement, not one taken here. The rest of the row stands: `pymupdf>=1.24,<1.30` unchanged, this machine runs 1.28.2 and the product 1.28.0, and `verdicts.json` still carries no version field. |
| 2026-09-16 | **C9 — no network at runtime.** Fonts, reference faces and any lookup are files the caller provides; issuer lookup belongs to the agent workflow, never to the library. | A service. | **holds today** — no network import in `pdf_translate/` (grep, 2026-09-16); `tools/fetch_test_fonts.py` is a dev tool; the Han-forms gate takes a reference directory. |
| 2026-09-16 | **C10 — logging.** Through the `logging` module on the package's own logger, never `print`; nothing the library logs contains document text beyond what a finding already carries. | A service's logs. | **open** (E3). 166 `print` sites across the package modules today. **done** — v58. All 172 `print` sites in the package emit through `logging.getLogger('pdf_translate')` at INFO; one re-entrant `console()` attaches the single stdout handler at each CLI entry point; importing the package attaches only a `NullHandler` and sets no level on the root. Two structural tests keep it that way: no module calls `print`, and no `log.info` takes more than one argument (a two-argument call silently drops the record — it happened twice during the conversion). |
| 2026-09-18 | **Row 32 — the terminology loop** (this repo's own row, filed here because it changes a stage the product calls). `pipeline.py finish` now requires `--work DIR` and refuses while `review.json` is absent or any finding is `open`. | A wrong term of art passed every gate on the first FL-150 → ja job and reached a delivery; no gate can see one. | **done** — v57, branch `feat/terminology-loop`. **R5 is not breached and the CLI refusal does not reach the product.** `finish` is packaging, not building, so a refusal there would be a withholding by a non-build stage; the refusal is built for the person driving the CLI by hand, and for the product the load-bearing artefact is the **record**: `review_state.json` is written beside `FINAL.pdf` on every run, refused or not, carrying `schema`, `version`, `blocks_delivery`, the counts and the one `REVIEW` line — surfaceable without parsing console text. Nothing here deletes or withholds an output file that was built: the refusal happens before `field_fonts` runs, so no delivery is produced and then held back. A consumer driving the library calls `run_review(work, generate=False)` and decides for itself; a consumer driving the CLI and wanting today's behaviour passes `--no-review`, which delivers and marks the delivery. C10 (logging) is honoured for the two new commands ahead of E3: they emit through the package logger, and `import pdf_translate` attaches only a `NullHandler`. |

| 2026-09-18 | **The five bubbled items (B1–B5)**, each a measurement taken while integrating 54.0.0 (rev `9675c619`). B1: the library never breaks a line, so a long translation shrinks and below the floor is left untranslated. B2: the refusal report truncates the core to 40 characters. B3: refusals are printed, not returned. B4: widget text is not translated. B5: terminology quality is invisible to every gate. | Each one costs a customer something: untranslated text, a silent revert of 247 of 247 cores, a consumer's regex that stopped matching, form fields still in the source language, and a wrong legal term on a legal form. | **read and queued** — `docs/BRIEF-product-bubble-2026-09-18.md`. **B3 done (v58)**: every stage raises a typed exception carrying structured attributes and `refusals`. **B2 done for library consumers (v58)**: `refusals` carries every refused core **in full**; the printed line keeps its 40-character abbreviation deliberately, because it is read by a person and changing it breaks console parity — ask for that separately if it is wanted. **B5 built (v57)**: row 32's review loop, `references/terminology-failure-modes.md`, the per-class termbase and the canary's reviser axis (19% false-positive rate on the FL-150). **B4 open but contained**: the widget-text scaffold, the `/Opt` export-value rule and the refusal already exist in `extract_segments` and `strip_text`; what is missing is exposure on the consumer surface and a ruling on whether an unauthored scaffold should warn. **B1 design approved; further work deferred (19 September)**: exact page count, same-page placement, per-occurrence permission and a caller-authored fixed box. The synthetic probe and known-success real-job capture are complete; genuine fit-refusal evidence remains missing. No plan or implementation has begun. See `docs/design/B1-line-wrapping/README.md` and `docs/reviews/2026-09-19-b1-captured-case.md`. Correction to the original report: explicit merges already reflow and gate 19 is called; ordinary-line overflow is a build refusal, not automatic source-text restoration by the library. |

| 2026-09-20 | **Typography preservation for wider library adoption.** Preserve source serif-versus-sans class and meaningful within-line bold/italic distinctions; exact source font reuse is not required. Retain an unambiguous relationship between translated style runs and repeated source occurrences, and explicitly report unsupported/ambiguous cases. | The app reports v54 at `9675c6196c14eb2a2d37d34e371391eb1955a386`: ES/zh-Hans core placement succeeds on synthetic invoices, but mixed families and emphasized tails lose their distinctions. Its five compatibility failures remain app-owned and open. | **Written typography design approved; nine-stage implementation plan saved for review and execution-method choice. Code has not started.** Own-source fixture and AST comparison confirm flattened style flags and missing class/span records at v54, main v56 and open-PR v58, with no extraction warning. Existing four-role fonts, inline emphasis and substring overrides are narrower manual controls. See `docs/reviews/2026-09-20-typography-capability.md` for exact APIs/pins and the library/app ownership split. The app's typography promise is unchanged. The selected approach preserves legacy calls and adds explicit style/occurrence data. Approved first scope is horizontal, single-baseline Latin/Japanese/Simplified Chinese page text; unsupported cases refuse and remain ineligible for adoption under the unchanged promise. See [the written design](design/typography-preservation/README.md), saved locally in `ef52e5f`. Its detailed scope/API is approved; [the implementation plan](plans/2026-09-20-typography-preservation-brief.md) remains unapproved. No new pin or PR change. B1 remains separate and deferred. **Done — v59** (PR #17, merged 21 September): the capability ships as the opt-in `typography-1` mapping format and announces itself in `pdf_translate.MAPPING_FORMATS`; `references/typography.md` documents it. App adoption, routing and its five compatibility failures remain app-owned and are not verified here; the app reports v54. |

| 2026-09-24 | **GOV-2026-09-24 — the product directs this library.** The product sets this library's direction and assigns its work through this file; this repo reports findings and proposes, and builds and tests only what is assigned. Sessions on both sides message each other when a request, the state of work or a version changes, and every outcome is written here in the same session. The app's request file is `docs/reference/REQUEST-to-skill-app-direction-2026-09-24.md` at `a837961` in `pdf-translator`: provenance only, not opened here. | Rodrigo's ruling: one owner of direction and one queue of work, so the two repositories never keep competing roadmaps and nothing agreed in a chat is lost between sessions. | **done** — PR #27, merged 24 September as `0542dc2`: `AGENTS.md` Rule 4, the section "How work arrives here" above, a `CLAUDE.md` that imports `AGENTS.md`, and the `docs/DECISIONS.md` row of 2026-09-24. Docs only; the version stays 61. The ID is the app's, recorded here at its request so both sides name the request the same way. |

| 2026-09-24 | **E12 — a compact, deterministic output save.** A documented, reusable save that any caller can apply to a finished document, including one assembled from per-page parts. Its output: carries each face as exactly one embedded font program, subset once for the whole document; is written compactly, with unused and duplicate objects dropped and streams compressed; draws exactly the same pixels as its input; keeps every form field, its name and its value; is byte-identical across runs when the caller supplies the same `doc_id`. **Acceptance, observable:** (1) on this repo's corpus text-only fixtures, assembled from per-page parts as described, output bytes ≤ 2.5× input, with per-fixture ratios in a dated table; (2) each face appears as exactly one embedded font program per output document, counted in the file; (3) every page rasterised before and after the save at a pinned zoom gives `pixel_diff_ratio == 0.0`; (4) on a form fixture, the field count, names and values are equal before and after; (5) two runs with the same input and `doc_id` give equal sha256, and behaviour without a `doc_id` is documented; (6) checks 1 and 2 are shown red against the unfixed shape (per-part subsets, default save) before the change lands; (7) Rule 1 applies, the API is documented in `references/`, the version bumps, the app gets a notice, and the PR is Rodrigo's to merge. **Owner:** this library builds it; the app integrates it and owns its real-form size evidence. It takes over E6's "one subset per document, never per page" bullet and needs C7's caller-supplied `doc_id` at the save. It traces to the app's ROADMAP N2.output-save-flags. | A consumer that builds a document from per-page parts, each embedding the same faces, each subset on its own and each saved with default settings, delivers files about 6× the input size. The app measured one real government form at 184 KB in and 1,154 KB out: roughly 200 KB of that is a separate font subset per page, and roughly 700 KB is uncompacted structure. | **accepted** — priority 1 of 1, from Rodrigo's ruling of 24 September as relayed by the app's session; nothing else is assigned. No adoption pin: the app stays on v54 at `9675c6196c14eb2a2d37d34e371391eb1955a386` (Python 3.12) and adopts E12 only at its Python 3.14 migration, with an exact, reviewed pin. Delivery does not imply adoption. If E12 as written proves unbuildable or wrong for this code, this library stops and reports the measurement rather than substituting its own version. **Blocked, 2026-09-24, before any build.** The measurement is in [reviews/2026-09-24-e12-measurement.md](reviews/2026-09-24-e12-measurement.md). Checks 3–5 are buildable, with guards: MuPDF's `subset_fonts` flips two verify gates to REVIEW, and garbage 4 folds widgets that have no `/P`. Check 2 holds for page text, but on every delivered form it contradicts the standing full field face. Check 1 cannot hold on the three base-14 fixtures without dropping TrueType hinting, which breaks a strict check 3. Checks 1, 2 and 6 go red only on constructed multi-page fixtures, because every corpus fixture is one page. Six rulings are asked of the product; nothing is built until they are answered. The app acknowledged the block the same day and queued the rulings for Rodrigo after its N1, since E12 serves N2. Its library route opens the whole document once and never slices, so the `insert_pdf` widget loss does not reach it; the per-page route is the older engine that E12 serves. The app flagged the `/Rotate 90` blank-page finding in the review as a possible N1 risk, because its library route runs no verify. Nothing about it is assigned here. |

| 2026-09-24 | **R-03 — widget text by fully qualified field name** (review priority 1). Tooltips (`/TU`), values (`/V`, `/DV`) and choice labels (`/Opt`) are scaffolded, applied and parity-checked by the fully qualified field name, so no field receives another field's text; a page-specific barcode value stays on its page. **Acceptance:** every widget's tooltip, value and options equal those of the same fully qualified field in the source, and each page's barcode value equals that page's source value; plus the shared bar in the status section. | 72 widgets on 5 government forms (57 of 212 on FL-300) announce another field's name to screen readers, and following SKILL.md's identity rule writes page 1's PDF417 value onto every page of G-28, I-864 and N-400. `docs/REVIEW-2026-09-24.md`. | **accepted** — priority 1 of the review assignment (the app's `REQUEST-to-skill-review-2026-09-24`); started 24 September. **done** — v62, PR #30 (merge `e5be31d`, 24 September). 99 fields on 8 wild forms that carried another field's text dropped to 0, and 27 of 30 barcode pages with the wrong value dropped to 0. Rule 1 passed on another model. Evidence: `docs/reviews/2026-09-24-r03-widget-text-names.md`. |

| 2026-09-24 | **R-01 — strip keeps graphics state set inside text objects** (review priority 2). Inside BT…ET, strip drops only the text-state, positioning and showing operators; colour, `gs`, line width and the other graphics-state operators stay, so graphics drawn after the text object keep their colours. **Acceptance:** the shared bar, including the wild probe with a render diff. | On 4 of 17 real PDFs the stripped page repaints graphics in the wrong colour (arxiv table shading black, USCIS N-400 rules white, Medicare blue near-black), and on a constructed page the ink gate PASSes. | **accepted** — priority 2 (the app's `REQUEST-to-skill-review-2026-09-24`). **done** — v63, PR #31 (merge `0819091`, 24 September). On 465 pages across 33 files, 0 non-text pixels now differ from the original. Before the fix, 18 pages in 5 files did. The wild probe's verdicts are unchanged. Rule 1 passed on another model. Evidence: `docs/reviews/2026-09-24-r01-strip-graphics-state.md`. |

| 2026-09-24 | **The `/Rotate 90` blank page, and R-64 — a corpus test that builds outputs** (review priority 3). A translate fixture on a `/Rotate 90` page rebuilds with its text visible; the cause is diagnosed first. The corpus suite gains a test that builds each translate fixture's output and checks it, so this class of defect cannot pass CI again. **Acceptance:** the shared bar. | `corpus/rotated.pdf` rebuilds to a page with no ink and no text layer; verify FAILs it, but the app's route runs no verify, and the corpus suite never builds an output (E12 measurement; review R-64). | **accepted** — priority 3 (the app's `REQUEST-to-skill-review-2026-09-24`). **started** 24 September. Diagnosed: on a `/Rotate` page, extract records text geometry in the rotated (visible) space, but retypeset draws in the unrotated page space. **built** 24 September, v64, branch `fix/rotate-pages-unrotated-space`, awaiting review. `segments.json` is now in the unrotated space, with a `geometry` key; retypeset measures against the unrotated frame; a stale extraction on a rotated page is refused by a stable, documented line. Rule 1 passed: three independent passes on another model. The pixel pass found 0 differing pixels against the rotated control at 90, 180 and 270, where v63 differed by 7,142 to 9,351. One layout saved at `/Rotate` 0/90/180/270 now extracts and rebuilds identically at every rotation: 0 of 13 runs were placed right on rotated pages before, and all are now. The R-64 test identity-rebuilds all 13 `translate` fixtures and checks where each run starts. The app answered the design questions on 24 September. Q1: it reads no segment geometry. Q2: the stale-extraction refusal is acceptable, because extract and retypeset run in one job at one version; keep its text stable. Q3: the row below. Evidence: `docs/reviews/2026-09-24-rotate-pages.md`. **done** — v64, PR #33 (merge `154f842`, 24 September). |

| 2026-09-24 | **R-02 — small print is not drawn over its neighbour** (review priority 4). The 4.0 pt clamp no longer bypasses the 0.7× floor, the gate sees the true ratio, and a run under 4 pt is never enlarged. **Acceptance:** the shared bar. | A 5 pt run needing 0.54× is drawn at 4 pt over its neighbour while verify exits 0; a 3 pt run is drawn larger. | **accepted** — priority 4 (the app's `REQUEST-to-skill-review-2026-09-24`). **started** 24 September. **built** 24 September, v65, branch `fix/r02-small-print-clamp`, awaiting Rule 1 and review. A shrunk run is drawn at the size that fits its room, never larger than its source, and the gate sees that ratio, at all four legacy shrink sites. On 10 wild PDFs rebuilt with longer text (median 1.37× the source's characters), the only change is 33 runs `main` had lifted to exactly 4 pt, and no run got larger. On the IRS 1040-ES, the 5.25 pt "CAUTION" with a doubled target had reported 0.76× and passed the floor; it needs 0.66×. Rule 1 passed: two independent passes on another model, with 0 pixels of the run past its room, where `main` drew 108 to 236. Evidence: `docs/reviews/2026-09-24-r02-small-print.md`. **done** — v65, PR #34 (merge `a9fd0a9`, 25 September). |

| 2026-09-24 | **Review quick wins, XS each** (review priority 5, in this order). R-05: an output path that names an input mapping or segments file is refused on the legacy path too. R-06: text between inline tags is escaped. R-04: every role face is canonicalized, so italic jobs verify. R-27: `field_fonts` refuses a variable face (or instances it). R-47: typography verify reads page rects once. R-69 with R-97: CI discovers its tests and keys the font cache on the fetcher. R-33: `field_fonts` keeps a field's colour and size. R-40: legacy capture bundles record `source_pdf`. R-42: a typography preflight refusal names the offending text. R-110: SPDX licence form in `pyproject.toml`. R-100: dead code removed. R-99: ResourceWarnings closed. Docs: R-79, R-80, R-82, R-83. **Acceptance:** the shared bar. | `docs/REVIEW-2026-09-24.md` has each item's evidence. | **accepted** — priority 5 (the app's `REQUEST-to-skill-review-2026-09-24`). **R-05 built** 24 September, v66, branch `fix/r05-legacy-output-alias`, stacked on #34. A legacy build refuses an output or scale-report path that names one of its inputs, and `rebuild` refuses an OUT that names the original or a work-directory input. On v65 every one of those cases replaced the input, and the build exited 0; for `stripped.pdf` it raised a bare `ValueError`. **R-06 built** 24 September, on the same branch and version. Text between inline tags lands as written. So does a notice's text, which had the same defect. MuPDF 1.28.2's Story engine decodes character references twice, so `&` is escaped twice, and a test pins that. R-05 and R-06: **done** — v66, PR #35 (merge `637e291`, 25 September). **R-04 built** 24 September, v67, branch `fix/r04-canonicalize-role-faces`, stacked on #35. The canonical text layer now covers the italic and bold-italic faces, so an italic cut of Arial or Times no longer fails verify on a correct page. Rule 1 passed with the real Arial and Times italics. Pages render byte-identical, and only `/ToUnicode` changes. Evidence: `docs/reviews/2026-09-24-r04-role-faces.md`. R-04 is in PR #36. **R-27 built** 25 September, v68, branch `fix/r27-field-fonts-variable-face`, stacked on #36. `field_fonts` embeds a variable face as its Regular instance. It used to embed it as-is, so typed text rendered Thin and a 1 KB form grew to 5.9 MB; it is now 3.4 MB, with the `instance` noted in the result. The app confirmed its route calls no `field_fonts`; the face it would pass is already a static Regular instance, so the instancing cost does not apply. Rule 1 passed after one fix: a pinned copy was left behind when the input failed to open. Evidence: `docs/reviews/2026-09-25-r27-field-font-instance.md`. R-04: **done** — v67, PR #36 (merge `9cfcf63`, 25 September). R-27: **done** — v68, PR #37 (merge `aa54158`, 25 September). **R-47 built** 25 September, v69, branch `perf/r47-typography-verify-page-rects`. Typography verify reads each page's crop and source field rects once, not once per glyph. After `field_fonts` sets NeedAppearances, each page load rebuilt the widget appearances and kept them. On a filled N-400-sized form (14 pages, 440 widgets) one verify made 37,618 page loads and peaked at 3.0–3.6 GB; it now makes 533 and peaks at about 170 MB, with byte-identical gate results. Not a Rule 1 item under the bar, but an independent pass on another model ran anyway: PASS. It compared seven of its own cases plus a large form byte for byte, and measured 2,563 → 152 MB on its own 10-page form. Evidence: `docs/reviews/2026-09-25-r47-typography-verify-page-loads.md`. **R-69 with R-97 built** 25 September, branch `ci/r69-r97-discover-and-font-cache`, stacked on #38. CI discovers the tests in every directory that holds them, instead of naming 22 modules by hand, and collects the same 736 test IDs. The font cache is keyed on the fetcher's hash and saved right after the fetch. On main, both legs restored `noto-fonts-v3` and still downloaded 42,585 KB on every run, because a hit is never re-saved. The cache is saved before the suite, so it cannot keep the instanced faces the tests write there. No version bump: nothing shipped changes. Evidence: `docs/reviews/2026-09-25-r69-r97-ci-discovery-and-font-cache.md`. R-47: **done** — v69, PR #38 (merge `19252b7`, 25 September). R-69 with R-97 now targets `main` directly. R-69 with R-97 is PR #39. Its own CI proved the cache fix. The first run missed the new key, fetched the 20 faces (70,964 KB) and saved them before the suite. The second restored the key and fetched 0 KB, with the same 736 tests passing on both legs. **R-33 built** 25 September, v70, branch `fix/r33-field-fonts-keep-appearance`, stacked on #39. `field_fonts` swaps only the font in each field's `/DA` and keeps its size and colour. A widget without a `/DA` of its own gets the inherited one. On the wild forms v69 typed 153 navy IRS fields and 7 red USCIS signature fields in black, and auto-sized 2 I-9 fields; v70 changes 0 of 1,210. Rule 1 passed with renders of real navy and red fields; its two minor findings are fixed. Evidence: `docs/reviews/2026-09-25-r33-field-appearance.md`. R-69 with R-97: **done** — PR #39 (merge `b504821`, 25 September), CI only, so main stays v69. R-33 now targets `main` directly: its base `d1f8a30` is in `main`, with the same tree. Rodrigo approved in this session: R-33 is PR #40 against `main`. **R-40 built** 25 September, v71, branch `fix/r40-capture-source-pdf`, stacked on #40. `rebuild` gives the original to every job, so a legacy capture bundle records `source_pdf` and replays with it. Before, it passed the original only to typography-1 jobs and every legacy bundle said `source_pdf: null`. Legacy output is unchanged apart from MuPDF's save-time `/ID`. The app confirmed it never runs `rebuild` or reads a capture bundle. An independent pass: PASS, no findings. Evidence: `docs/reviews/2026-09-25-r40-capture-source-pdf.md`. Rodrigo approved in this session: R-40 is PR #41, stacked on #40. R-33: **done** — v70, PR #40 (merge `314e1f6`, 25 September). R-40: **done** — v71, PR #41 (merge `62e87bf`, 25 September). **R-42 built** 25 September, v72, branch `fix/r42-typography-preflight-names-text`, on `beb4c06`, which is in `main`. A typography source-content refusal (shear, clip, transparency, paint over glyphs) now names the occurrence that holds the offending text; it used to name the page's first. On the 17 wild PDFs that was a different line for 235 of 366 issues. A whole-page construct names only the page. Two independent passes: the named line is right (7 of 7 constructed, 17 of 17 wild checks), and verify is unchanged. One major finding, a malformed `/CropBox` crashing the check, is fixed with a test. The app has not adopted typography-1 and reads no `refusals`. Evidence: `docs/reviews/2026-09-25-r42-content-refusal-names-text.md`. Rodrigo approved in this session: R-42 is PR #42 against `main`. **R-110 built** 25 September, v73, branch `chore/r110-spdx-licence`, stacked on #42. `pyproject.toml` declares `license = "MIT"` with `license-files = ["LICENSE"]` (PEP 639) and builds with `setuptools>=77`. The deprecated table form warned on every build and stops working on 2027-02-18. An offline build shows 0 warnings where there were 4, and `License-Expression: MIT`; the wheel and sdist carry the same files. The app installs the pin as a uv git source with build isolation, and nothing reads the licence field, so v73 builds there. Evidence: `docs/reviews/2026-09-25-r110-spdx-licence.md`. Rodrigo approved in this session: R-110 is PR #43, stacked on #42. **R-100 built** 25 September, v74, branch `chore/r100-dead-code`, stacked on #43. Four pieces were removed:
- the late untranslated pass in legacy retypeset, which cannot fire because the early pass refuses first (the late refusal keeps an empty `untranslated` key);
- `_run_typography`'s unused `resource_root`;
- a duplicate path helper;
- `verify.load_segments_for`.

None of the app's five names is touched. A tripwire on the late pass never fired across the suite, corpus rebuilds and eleven adversarial jobs; an adversarial independent pass: PASS. Evidence: `docs/reviews/2026-09-25-r100-dead-code.md`. Rodrigo approved in this session: R-100 is PR #44, stacked on #43. **R-99 built** 25 September, v75, branch `fix/r99-resource-warnings`, stacked on #44. The suite's ResourceWarnings go from 45 to 0.
- 43 were the `NOTES.md` that `run_review` read with a bare `open().read()`.
- 2 were a lazily loaded face in the test suite's own `han_forms` helper.
- The review's two library sites held no file handle: fontTools reads a face opened by path into memory. They now close their fonts anyway.

Evidence: `docs/reviews/2026-09-25-r99-resource-warnings.md`. Rodrigo approved in this session: R-99 is PR #45, stacked on #44. **R-79, R-80, R-82 and R-83 built** 25 September, v76, branch `docs/r79-r83-docs-quick-wins`, stacked on #45. `references/retypeset.md` lists all nine legacy refusal kinds, where it named two. It shows the enveloped `scale_report.json`, where it showed the pre-v58 bare list. `SKILL.md` counts five identity facts, gives the full-discovery test command (756 test IDs; the old command ran 278), and puts the recon note back on `failure-modes.md`. The evals no longer name `pipeline.py verify`, which exits 2. Comments cite functions, not drifted line numbers. `tests/test_shipped_docs.py` locks each fix against the code, and all 8 of its tests fail on v75. Three independent passes on another model confirmed every claim by running it; their one finding, a miscounted comment, is fixed. Evidence: `docs/reviews/2026-09-25-r79-r83-docs-quick-wins.md`. |

| 2026-09-24 | **Review performance items** (review priority 6). R-51: test CJK faces instanced once, not per test. R-48 with R-49: the pixel and character loops in extract and verify replaced by exact equivalents. R-50: `prepare_font` subsets before instancing. **Acceptance:** the shared bar, and output identical by a render or byte diff. | R-51 is about 79% of Linux CI time; the loops are about half of extract and verify time. | **accepted** — priority 6 (the app's `REQUEST-to-skill-review-2026-09-24`). Rodrigo approved in this session: the docs items are PR #46, stacked on #45. **R-51 built** 25 September, tests only, so the version stays 76, branch `perf/r51-test-font-instances`, stacked on #46. `tests/_instancing.py` memoizes fontTools' instancer for a test run. `test_han_forms` and `test_cjk_leak` opt in, and still call the real library paths. Between them they built four CJK instances 18 times; now each is built once. Cold, the two modules took 139.7 s before and 64.5 s after. Output is identical: independent passes found 46 fonts byte-identical and 22 PDFs pixel-identical with the memo on and off. They found three defects in the memo, each fixed with a test. `test_typography_fonts` does not opt in: measured, it got slower (125.5 s against 137.0 s). The acceptance probe runs as a subprocess and is frozen evidence; R-50 is the library-side fix for its cost. The CI before-and-after comes from the PR's own run. Evidence: `docs/reviews/2026-09-25-r51-test-font-instances.md`. **Product advice on the next item** (the app's session, 25 September; advice for Rodrigo, who decides): R-48 with R-49 next, until E12's rulings arrive. It is the only performance item on the app's route, since it changes `extract_segments` and `strip_text`. R-50 is off that route: the app calls neither `prepare_font` nor `field_fonts`. The app passes the library a subset of the customer's selected pages, at most 40, so R-48's pixel loops matter to it more than R-49's scoping. Nothing here is urgent for the app, which stays on v54 until it moves to Python 3.14 and `run_retypeset`. **Added to R-48 and R-49's acceptance, at the product's request:** the identical-output evidence covers the app's call shape. That means `extract_segments` writing to an outdir, with its outputs compared byte for byte, not only by render. It means `strip_text` with and without a `widget_text` mapping, on a form with widgets (FL-150). It includes one CJK target, and one source with a `/Rotate` page. The app's session is reviewing PRs #9–#46, its last recorded review being #6–#8 on 16 September, and R-51 before it is pushed. Its findings follow. Rodrigo approved in this session: R-51 is PR #47, stacked on #46. #47's CI measured it: `test_han_forms` and `test_cjk_leak` fell from about 0.75 to 0.32 of the untouched modules' time on Linux, and to 0.30 on Windows. **R-48 with R-49 built** 25 September, v77, branch `perf/r48-r49-pixel-loops`, stacked on #47. The pixel and character loops are exact replacements in `pdf_translate/_pixels.py`. The invisible-text oracle judges only extract's `--pages`, against a whole-document strip. Output is identical on every input measured. That covers 311 files of 34 inputs, and the app's call shape: extract to an outdir byte for byte; strip with and without `widget_text` on FL-150; a CJK target's verdict; a `/Rotate` source. It also covers the 17-PDF wild probe, and 132 artifacts from two independent passes; their one minor finding is fixed with a test. CPU: extract 66.3 → 40.4 s, a 5-page slice 46.7 → 17.4 s, verify 111.7 → 68.8 s. Strip is unchanged: stripping only the wanted pages would not be exact. Evidence: `docs/reviews/2026-09-25-r48-r49-pixel-loops.md`. |

| 2026-09-24 | **Proposal from this library: refuse clip-mode text.** Strip drops text drawn in a clipping render mode (`Tr` 4–7) whole, so graphics that relied on that clip draw unclipped. The proposal was (a) refuse such a page with a named reason, or (b) leave it, documented. | Found while measuring R-01. The 17 wild PDFs and 16 corpus fixtures contain 0 cases. | **declined** — the product chose (b) on 24 September. The app reads refusals from retypeset's printed output by fixed patterns, so a new refusal kind could reach an app path that does not recognise it. Documented in `references/failure-modes.md` §4 and the DECISIONS row of 2026-09-24 on the R-01 branch; to be revisited with app-side support if design-heavy PDFs appear. |

| 2026-09-24 | **Proposal from this library: lay out rotated runs in their own reading frame, or refuse horizontal-only features on them by name.** A run whose line is not horizontal in PDF space silently loses dot leaders and tails, `right`, `center` and override `x`; its merges squeeze into a column, and inline markup is drawn as literal tags. | Found while building item 3. Landscape pages, whose content is counter-rotated to read upright under `/Rotate`, send every run down this path. On Rule 1's 12-run landscape fixture, v64 puts every run at its source origin (v63 put none there), but `right`, `center` and leader filling do nothing. | **not assigned** — the product filed it as a proposal on 24 September. Rotated pages are 0 of 449 in the wild set and 0 of 1,199 in the app's sample, so it waits until landscape forms or vertical Japanese matter. Rodrigo can raise it. |

| 2026-09-24 | **Proposal from this library: a right-to-left source run is rebuilt where the source drew it.** MuPDF reports a right-to-left run's origin at its right end, and retypeset draws every run rightward from its origin. So each run of an Arabic or Hebrew source lands one source width to the right: `corpus/ar_source.pdf`'s title spans x 60.9–147.6 and its identity rebuild 140.6–239.9. No verify gate reads positions. | Found by R-64's position check on 24 September. It affects documents whose SOURCE is right-to-left, not right-to-left targets. The wild set has none. Pinned as an expected failure in `tests/test_corpus_verdicts.py`, so a fix shows up. | **proposed** 24 September. **not assigned** — the product answered the same day that it keeps right-to-left out of its MVP. The expected-failure pin holds the defect until Rodrigo decides on right-to-left for the product. |

| 2026-09-24 | **Proposal from this library: a multi-span line keeps its full box when its direction is not +x.** `extract_segments.py`'s span union keeps the first span's left edge, so a line whose spans advance another way loses the rest. Before item 3, a two-span line on a `/Rotate 180` page measured 50 pt wide instead of 161. | Found in item 3's coordinate map. Since item 3, it affects only lines that are not horizontal in PDF space. | **proposed** 24 September; the app noted it. |

| 2026-09-24 | **Proposal from this library: typography-1 measures against the unrotated page.** `typography_verify.py` tests unrotated glyph boxes against the rotated `page.rect`, so a correct typography-1 run near the edge of a `/Rotate 90` page would FAIL. Retypeset's typography placement budget (`_measure_typography`) also reads `page.rect`: called directly at `/Rotate 90`, it refuses a run that fits at `/Rotate 0` (Rule 1, item 3). | Found in item 3's coordinate map. It cannot happen today: typography-1 retypeset refuses rotated pages, and group E is held. | **proposed** 24 September; the app noted it. |

| 2026-09-24 | **Proposal from this library: `python -m pdf_translate.retypeset` and `python -m pdf_translate.verify` print their log.** Run that way, both print nothing: `runpy` re-executes the already imported module as `__main__`, whose logger is not under `pdf_translate`. The exit code and the output file are right. | Found by item 3's Rule 1 review. `scripts/*.py` and `pipeline.py` print normally, and the same happens on v63. | **proposed** 24 September. |

| 2026-09-24 | **Proposal from this library: verify refuses an input flag spelled `--flag=value` instead of ignoring it.** Verify reads its options only as `--flag value`. A caller who writes `--source-words-from=segments.json`, `--translations=…` or `--reference-fonts=…` gets a run with that input silently absent: the gates that need it SKIP or run without it. | Found by R-05's review. `pipeline.py rebuild` now protects a file named in either spelling from being overwritten by OUT, but verify itself still ignores the `=` form. | **proposed** 24 September. **held** the same day with review group C, under Rodrigo's ruling A. The app runs no library verify: it confirmed that `apps/api/api/` makes no verify or `qa_check` call and passes none of these flags. Revisit if the app adopts verify. |

| 2026-09-25 | **Proposal from this library: typography verify accepts the widths MuPDF actually embeds.** MuPDF writes each glyph's width to the PDF's `/W` array in whole thousandths of an em, rounded down. Typography verify predicts each glyph's position from the font program's exact advance. In a face whose units-per-em is not 1,000, every glyph is drawn a little left of the prediction, and the gap passes the 0.05 pt tolerance within about 10–15 glyphs. Verify then FAILs a correct line with "Run N is not at its ordered, uniformly scaled position". Arial, Times New Roman and most TrueType faces use 2,048. | Found while measuring R-47. On an identity typography-1 build in Arial, verify FAILed all 150 of 150 correct lines. In Noto Sans, which uses 1,000 units, the same job PASSes. For Arial Regular's P, 1366/2048 em is 666.99 thousandths and is embedded as 666. All 20 embedded widths equal the rounded-down value, and 9 of them differ from normal rounding. The typography-1 tests and probes use only 1,000-unit Noto faces. | **proposed** 25 September. Typography-1 is group E, which is held, and the app has not adopted it. A fix would be one of: (a) verify predicts positions from the embedded `/W` widths, (b) retypeset embeds exact widths, if MuPDF can be made to, or (c) the tolerance scales with the run's length. Each needs Rule 1. |

| 2026-09-25 | **Proposal from this library: `field_fonts` finds a field's type however far up it is inherited.** It decides whether a widget is a text or choice field from the widget's `/FT` or its parent's. A field whose `/FT` is set only on a grandparent or higher is skipped: its `/DA` is never pointed at the embedded font, so typed target-script text can still fall back or vanish. | Found by R-33's Rule 1 pass, and reproduced here: a text field typed only on its grandparent gets 0 fields rewritten and stays on `/Helv`, on v69 and v70 alike. None of the 17 wild PDFs is built that way. The fix would walk the whole `/Parent` chain for `/FT`, as `inherited_da` already does for `/DA`. | **proposed** 25 September. |

| 2026-09-25 | **Request from the product: capture's off switch and contents are documented.** Three facts. `capture_dir=""` is an explicit off switch that wins over `PDF_TRANSLATE_CAPTURE_DIR`. A bundle holds every source string and the form's fields even without `original=`. With `PDF_TRANSLATE_CAPTURE_BELOW` set, a successful build writes a bundle too. **Acceptance:** each fact is stated in `references/consumer-guide.md`, and `""` beating the environment variable is locked by a test. | From the product's review of #19 (merged). Today `""` works as off only because it is falsy: `resolve_capture_dir("")` returns `""`, which beats the variable, and callers test it with `if`. Its docstring says the return is `None` either way, which is not true for `""`. The app will pass `""` and never set either variable in production. | **requested** 25 September, by the app's session in its PR review. Rodrigo decides when. |

| 2026-09-25 | **From the product's review: a typography content refusal names the occurrence where its offending text starts, even on a split line.** R-42 records the line matrix's start, not the start of the offending text. So when a line holds more than one occurrence, and the offending text follows other text, the refusal names the wrong one. **Acceptance:** a test where the offending text follows other text on the same line names the right occurrence. The fix locates the offending show's first glyph from the MuPDF text trace, as the occluded-text branch already does. Alternatively, the `ContentIssue.at` comment, the R-42 evidence and its DECISIONS row say "start of the text line". | Reported by the product's review of #42, on the typography-1 path, which the app never reaches. It has not been reproduced here yet. It is low priority. | **proposed** 25 September. Rodrigo decides whether to fix it or reword it, and when. |

Add new rows at the bottom. Do not delete a row when its status changes —
update the status column in place so the history of what was asked for
stays readable.
