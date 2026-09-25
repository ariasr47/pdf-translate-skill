# R-50: prepare_font instances the job's subset, not the whole face — 25 September 2026

**Assignment.** R-50 is the third performance item, priority 6 of the
assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`; the finding is R-50 in
`docs/REVIEW-2026-09-24.md`. It ships as v78, stacked on #48 (v77).

The app calls neither `prepare_font` nor `field_fonts`, and its
Japanese face comes from its own script. So this is off the app's route;
the app's session checked that and confirmed no side-file dependency.

## What changed

**Before.** `prepare_font --instance wght=N` loaded the whole variable face,
instanced it, and saved the whole instance beside the output as
`<out>.instanced.ttf`. It then wrote `<out>.chars.txt` and ran `pyftsubset`
on the whole instance. Instancing reads every glyph's variations, so a CJK
face (17,936 glyphs for Noto Sans JP) cost 5 to 13 s of CPU a call.

**Now:**
- `_variable_subset` first cuts the face to the job's characters, in
  memory, keeping everything the instancer and the final subset could use:
  - every layout feature (`layout_features='*'`);
  - every name record and language;
  - glyph names and the `.notdef` outline;
  - `legacy_kern` and both cmap options;
  - every table, with none dropped and unknown tables passed through.
- It instances that: 465 glyphs for the Japanese test job, including every
  glyph any feature reaches.
- The final `pyftsubset` step is the same as before.

The instanced source and the charset file go to a temporary directory, so
nothing is left beside the output.

**The field face.** The old `.instanced.ttf` was the whole face, and the
FL-150 job README used it as its field face. An instance of the job's
subset under that name would draw tofu for any typed name outside the
job's characters, so no file is left at all.
- `references/fonts.md` now says to pass the variable face to
  `field_fonts`, which has pinned its Regular instance since v68.
- The README's step changes to match, with a dated note.
- The app's session confirmed nothing on its side reads either file.

## Not byte-identical, and why

The scripts are in `dev/probes/`: `r50_prepare_font_ab.py`, `r50_deliver.py`, `r50_deliver_compare.py` and `r50_gpos_equal.py`. The 37-case results are in `docs/reviews/data/2026-09-25-r50/`.

Before and after, 37 `prepare_font` cases ran on archive copies of
`4793f38` and the change:
- **Legacy:** 4 CJK faces × weights 400 and 700 × with and without a
  han-forms judgement, plus a wrong-region refusal and four
  non-instancing controls.
- **Typography:** sans and serif × JP and SC × four roles.

The subset differs in bytes in every instanced case, and only in these
tables:

| table | what differs | why |
|---|---|---|
| `head` | `xMin`, `yMin`, `xMax`, `yMax` | The old order saved the whole instance, which recalculated the box over all 17,936 glyphs; `pyftsubset` keeps it. Now it is computed over the job's glyphs. |
| `hhea`, `vhea` | side-bearing minimums, max extent | The same reason. |
| `OS/2` | `xAvgCharWidth` | The same reason: an average over the whole face then, over the job's glyphs now. |
| `GPOS` | its encoding (21 of 25) | The whole face needed extension lookups, and its subset kept them. The new subset is re-encoded compactly, so a serif JP subset is 264 bytes smaller. |

**Identical in every case:**
- glyph order, `glyf`, `hmtx`, `vmtx`, `cmap`, `name` and `post`;
- the line and style metrics:
  - `hhea` ascent, descent and line gap;
  - `OS/2` typo and win metrics, `usWeightClass` and `fsSelection`;
  - `head` `unitsPerEm` and `macStyle`.
- **GPOS positioning:** compared per glyph and per pair for every single
  and pair adjustment, and as rule sets for the contextual lookups, with
  extension wrappers unwrapped (`dev/probes/r50_gpos_equal.py`).

Those whole-face values could only be kept by instancing every glyph,
which is the cost R-50 removes.

## What it draws: identical

- **`prepare_font`'s console,** in all 37 cases: `validate_font`, the render
  check's pixel count and the han-forms verdicts are identical, as are the
  errors. The one exception is the reported KB size of a serif JP subset,
  41 → 40.
- **Six legacy deliveries built end to end with each tree:** Japanese sans
  and serif and Chinese sans, at 400 and 700, each with single lines and a
  merged paragraph laid out by the Story engine, which applies `kern`. All
  six match in page content streams, `get_text('rawdict')`, glyph IDs and
  positions from `get_texttrace`, and 200-dpi renders.
- **The six typography-1 deliveries of `dev/probes/typography_acceptance.py`,**
  run on both trees, `ja` and `zh-Hans` among them: both the output and the
  field-font final match in content, glyph positions and renders.

## Speed

CPU seconds across the 37 cases went from **209.9** to **72.3**:

| face | before | after |
|---|---:|---:|
| Noto Sans JP | 5.0 | 1.8 |
| Noto Sans SC | 8.9 | 3.1 |
| Noto Serif JP | 7.1 | 2.4 |
| Noto Serif SC | 12.5 | 4.2 |

Non-instancing faces are unchanged. What remains is subsetting and the
render and han-forms checks.

## R-51's memo, removed

R-51's test-run memo (`tests/_instancing.py`) reused whole-face instances.
After R-50, `prepare_font` instances an in-memory subset, which the memo
rightly never reuses. So R-51's `InstancingTests` failed on `4272a79`, and
both independent passes found it too.

The han-forms references the memo could still reuse are cached on disk, so
each is built once per run either way. Cold, on a busy machine,
`test_cjk_leak` and `test_han_forms` took 104 s with the memo and 92 s
without.

R-51's DECISIONS row named this as its reverse condition. `484b46b`
removes the memo and its tests, and returns `test_han_forms` and
`test_cjk_leak` byte for byte to their `e72e8f1` text. A new DECISIONS row
records it, and R-51's stays.

## Red, then green

`tests/test_prepare_font_instancing.py` has three tests:
- **The instancer sees under a twentieth of the face.** Fails on `4793f38`:
  it saw 17,936 glyphs.
- **Nothing is left beside the output.** Fails on `4793f38`: `.chars.txt`,
  plus `.instanced.ttf` when instancing.
- **The new order draws what the old one drew.** On a small real variable
  face, instancing the whole face (the old order, reproduced by patching
  the subset step) gives:
  - the same tables, except the five summary ones;
  - the same line and style fields;
  - the same pixels, through `TextWriter` and through the Story engine.

  The test also asserts the renders were drawn by the subset, so a fallback
  face cannot make them agree vacuously.

## Suite

CI's commands on macOS, on `484b46b`:
- **Suite:** 768 tests (the memo's 11 removed, R-50's 3 added), 0
  ResourceWarnings. The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is item 3's expected failure.
- **Canary:** 15, OK.
- **Repository tests:** 6, OK.
- **Eval fixtures:** exit 0.

## Independent verification (Rule 1)

This changes how fonts are prepared, so two passes on a different model
(Sonnet) verified it by running code on `4793f38` against `4272a79`.

**Deliveries: confirmed.**
- **Legacy:** 8 real deliveries (sans and serif, JP and SC, 400 and 700)
  are identical in page content, 200-dpi pixels, glyph IDs and positions,
  `rawdict` and `run_verify` verdicts.
- **Typography:** 4 builds give structurally identical subsets.
- **Console:** `prepare_font`'s console is byte-identical, including the
  han-forms PASS and the wrong-region FAIL with its ratios.
- **Side files:** confirmed gone on the new tree, present on the base.
- **The field face:** `field_fonts` with the variable face renders a typed
  name outside the job's characters (山田花子) pixel-identically to the old
  `.instanced.ttf`.

**Fonts: confirmed.**
- **Hostile charsets:** vertical-form targets, an Ideographic Variation
  Sequence through cmap format 14, a CJK compatibility ideograph,
  full-width Latin, half-width katakana and enclosed numerals.
- **Weights 100, 250, 400, 700 and 900, on both paths.** The Sans faces'
  one GPOS FeatureVariations condition (`palt`/`vpal`) fires at 700 and
  900, and its decoded, resolved values are identical.
- **Only the summary fields differ.**
- **A static face with `--instance`** behaves the same in both trees:
  typography refuses cleanly. Legacy raises an uncaught `ValueError` in
  both; that predates this change and is noted, not fixed.

**Their findings:**
- **Major, fixed before this record:** the R-51 memo test failed on
  `4272a79`. It is removed in `484b46b`, above.
- **Left unverified by them:** typography-path deliveries through
  `run_retypeset`. That was then run here: the typography probe's six
  deliveries, above.
