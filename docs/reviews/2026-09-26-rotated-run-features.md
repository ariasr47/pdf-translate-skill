# Rotated runs: horizontal-only features refused by name, the tail kept — 26 September 2026

**Assignment.** This is the product's fifth item, in its minimal version,
advised on 26 September and approved by Rodrigo. It ships as v86, stacked
on #59 (v85). The full reading-frame layout waits for the app's adoption
comparison.

## What happened on a rotated run

"Rotated" means a line not horizontal in PDF space (`is_rotated(seg_dir)`).
Such a run is drawn along its own direction. Read in the v85 code:

| feature | what happened |
|---|---|
| `right`, `center` | silently ignored |
| override | parts placed at their horizontal `x`, or all at the origin when no `x` is given, so they pile up |
| inline markup (`<b>`, `<i>`) | the inline path skips rotated runs, so the tags were drawn as literal text |
| a merge that takes in a rotated line | laid out as a horizontal box; the test fixture overflowed |
| source dot leaders and their tail | both dropped: the leader paths skip rotated runs, and the plain path draws only the label |

## What changed

**Refused by name.** The first four are asked by the mapping, and the
author can take each back. So before drawing, and after the `untranslated`
/ `unauthored_merges` refusal, the build raises `MappingError` with
`refusals['rotated_features']`:
- the shape is `[{page, core, feature}]`, and every item is listed at
  once;
- `core` is on every item, because the app's handler falls back to the
  source text for that core;
- a line in `skip` is never judged;
- a merge whose `html` is still null is refused as `unauthored_merges`
  first.

**Leaders dropped, tail kept.** This is the product's option (b). Leaders
and a tail come from the source, so a refusal would leave the author
nothing to act on. It would even make an identity build impossible.
- The tail is the currency sign extract records after the leaders (`$`,
  `€`, `£` or `¥`). It is content, so it is drawn after the label, along
  the line, in Helvetica, like the horizontal leader path.
- The run is fitted with the tail included.
- Each line that lost its leaders is reported twice: in the new
  `RetypesetResult.warnings` as `{"kind": "leaders_dropped", "page",
  "core"}`, and as a console `NOTE`. The product asked for the result as
  well, because the console is not an API.
- Horizontal lines keep their old paths.

**Docs:**
- `references/retypeset.md`: the rotated-lines section, and the failure
  table, now ten kinds, which its docs test enforces;
- the consumer guide's result fields;
- SKILL.md;
- the module docstring;
- the upgrade note's v86 section.

## Red, then green

`tests/test_rotated_features.py` has 9 tests:
- each feature refused by name, with a merge and several at once;
- a plain rotated run and the same features on a horizontal line still
  build;
- a rotated `Total ........ $` line keeps `$`, draws no dots and reports
  the line;
- a horizontal leader line is unchanged with no warnings;
- the fixture checks.

On v85, 6 fail and 2 error; the errors are the missing `warnings` field.

## Independent verification (Rule 1)

Two passes on Sonnet ran on archive trees of `84412ec` and `b694dcd`, and
printed which package each run imported.

**Identity: confirmed.**
- **The corpus:** all 13 `translate` fixtures rebuild byte-identically
  (`/ID` masked) and render-identically. Only `rotated_text.pdf` has
  rotated runs, and none of them has leaders.
- **The wild set:** 5 of its 17 documents have rotated runs, and none has
  leaders or a tail. The 2 a single test font can draw (IRS 1040-ES and
  W-9) rebuild identically, with no refusal for an identity mapping. The
  other 3 could not be drawn in either tree, for want of a font.
- **Order:** `untranslated` comes before `rotated_features`, and
  `rotated_features` before `notices`, checked at runtime.

**Adversarial: confirmed.**
- **The refusal:** every feature is refused with exactly `{page, core,
  feature}`, override with and without `x`, and `<b>` and `<i>`. A merge
  lists one item per merged line. A passthrough rotated line with an
  override is refused under its text.
- **What still builds:** a feature on a horizontal line builds byte for
  byte as before, and so does a rotated line in `skip` with `center`.
- **The tail:** a rotated `Total … $` reads `Total $` along the line
  direction with no dots, is fitted with the tail (0.88× against none
  before) and is reported. A list marker, a longer translation and a bold
  split (`A‖B`) keep their tails too. A horizontal leader line is
  byte-identical.
- **Findings:**
  - Minor: a hand-edited segment with a tail and no leaders keeps its tail
    but is not reported. It is unreachable from extract, whose `DOTS`
    pattern sets a tail only with leaders, and nothing is lost there.
  - Note: the tail is only ever a currency sign. The first draft of this
    change's docs said "a unit, a page number", and they are corrected.
  - Note: no real document in the corpus or the wild set has a rotated
    leader line, so the tail path is proven only on constructed PDFs.

## Suite

CI's commands on macOS, on the fix:
- **Suite:** 809 tests (800 on v85, plus these 9), with 0 ResourceWarnings.
  The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is the right-to-left expected failure.
- **Canary, repository tests and eval fixtures:** all exit 0.
