# R-51: each repeated CJK test instance is built once — 25 September 2026

**Assignment.** R-51 is the first performance item, priority 6 of the
assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`, and the finding is R-51 in
`docs/REVIEW-2026-09-24.md`: "test CJK faces instanced once, not per test".
The acceptance bar for performance items asks for a before-and-after
measurement and identical output.

Only tests change, so there is no version bump. The precedent is the
2026-09-25 R-69 row: nothing an installed plugin runs changes. It stacks on
#46 (v76).

## Measured before building

**CI, from #45's run `36158853052` (v75).** Each test's time is the gap
since the previous test line, charged to its own module. Actions stamps a
line when it completes.

| module | Linux | Windows |
|---|---:|---:|
| `test_han_forms` | 131.8 s | 253.7 s |
| `test_typography_acceptance` | 112.0 s | 216.5 s |
| `test_typography_fonts` | 100.8 s | 210.9 s |
| `test_cjk_leak` | 27.5 s | 51.2 s |
| whole suite, 748 tests | 489.6 s | 964.5 s |

The three modules the review named take 70.4% of the Linux suite and 70.6%
of the Windows one. The review measured 784 s on Linux; the suite has got
faster since.

**Locally, cold.** An M1 Pro ran a copy with only the 20 fetched fonts,
which is what CI starts with. fontTools' `instantiateVariableFont` was
wrapped to log each call:
- **In process:** 33 calls, 134.0 s in all, for 14 distinct inputs (face,
  weight, calling path).
- **In `test_han_forms` and `test_cjk_leak`:** 18 of those calls, 79.1 s.
  They build the same four instances again and again: Noto Sans JP and SC,
  at 400 and 700.
- **In `test_typography_fonts`:** 10 calls. Eight are distinct and are the
  subject of `test_cjk_instancing_produces_actual_regular_and_bold_faces`.
  Two repeat JP 400 and 700 in the italic-refusal test.
- **The acceptance probe** (`dev/probes/typography_acceptance.py`) runs as a
  subprocess, so it was run on its own under the same log: 10 calls, 55.7 s
  of its 92.4 s. Within the probe each input is new.

## The change

**`tests/_instancing.py`** memoizes `instantiateVariableFont` for a test
run. The first request for an input runs the instancer in full and keeps
the saved bytes; a repeat gets a copy.
- **What it reuses:** only a font that is still its file. It was read into
  memory, as `TTFont(path)` reads it, and every table it has read compiles
  back to the file's bytes.
- **The key:** the table directory's checksums, the axis values as floats,
  and every other option. Axis ranges, arguments it cannot read, and fonts
  on an open file go straight to the instancer.
- **What a reuse replaces:** only what the font is: its reader, tables and
  glyph order. The caller's own settings stay, as a real call leaves them.

**What opts in:** `test_han_forms` and `test_cjk_leak`, through
`setUpModule` and `tearDownModule`. `prepare_font`, `han_forms` and
`field_fonts` still run their real code paths.

**What does not, and why:**
- **`test_typography_fonts`.** Keeping a copy costs one extra save of each
  new instance. Six of its eight instances are asked for once, so opting in
  is slower. Measured cold, back to back: 125.5 s as it is, 137.0 s opted
  in.
- **The acceptance probe.** It is a subprocess, and the 2026-09-22 row
  freezes it as evidence. Its instancing is not repeated within itself; it
  repeats `test_typography_fonts`' across processes. R-50, which subsets
  before instancing, is the library-side fix for that cost.

## Red, then green

| test | fails on | passes on |
|---|---|---|
| `test_han_forms.InstancingTests`: two identical `prepare_font` runs instance at most once (a spy on `instancer.instantiateFvar` counts real runs), and their subsets are the same | v76: `2 not less than or equal to 1` | `aade52b` and later |
| `test_instancing`: a reuse keeps the caller's settings | `2392e5d` | `b08f4d6` and later |
| `test_instancing`: a font on an open file is not reused | `2392e5d` | `b08f4d6` and later |
| `test_instancing`: a reuse leaves the caller's own buffer open | `b08f4d6` | `1d2a8e1` |

The rest of `test_instancing` guards the memo against handing back the
wrong font:
- a reuse equals a real instance, in place and not;
- different axes or options are different instances;
- a table only read is still the file;
- a font changed in memory, or a range, goes to the instancer;
- bad arguments raise the instancer's own error.

## After

**Locally, cold, back to back:** `test_cjk_leak` and `test_han_forms`
together took **139.7 s** before and **64.5 s** after. That is 54% less,
with one more test. The instancer ran 4 times, once per face and weight,
where it ran 18.

**CI:** not measured yet. This PR's first CI run gives the after column
for the table above, and it is added here then.

**CI's commands on macOS, on `1d2a8e1`:**
- **Suite:** 766 tests, which is 756 plus the 10 new ones, with 0
  ResourceWarnings. The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is item 3's expected failure.
- **Canary:** 15, OK.
- **Repository tests:** 6, OK.
- **Eval fixtures:** exit 0.

## Independent verification

These are test changes, not Rule 1 items. They decide which fonts the CJK
tests build, though, so three passes on a different model (Sonnet) tried to
refute them by running code.

**Round 1, on `2392e5d`: two passes.**
- **Same outputs.** Both modules ran cold with the memo on and off. Every
  font and PDF they wrote was captured:
  - 46 fonts were byte-identical, with `head.modified` zeroed;
  - 22 PDFs were pixel-identical, every page rendered at 100 dpi;
  - the test outcomes were the same;
  - real instancing fell from 21 runs to 4.
- **Red and green.** `InstancingTests` failed on the base with 2 runs, and
  passed on the fix.
- **Correctness attacks that held:**
  - `AxisLimits` objects, ranges and dropped axes;
  - int against float values, positional against keyword arguments, and
    each option;
  - exceptions, which are not cached;
  - isolation between reuses;
  - TrueType collections, `BytesIO` and lazy fonts;
  - ResourceWarnings;
  - the real JP face, byte for byte against a real call.
- **Found, major:** an in-place reuse replaced the caller's whole `TTFont`
  state. That discarded `recalcTimestamp`, `recalcBBoxes`, `lazy`, `cfg`
  and any attribute the caller had set, which a real call keeps. No
  current caller sets any of them. Fixed in `b08f4d6`.
- **Found, minor:** the memo's docstring cited this document before it
  existed; it exists now. `test_typography_fonts` and the probe are not
  covered, which is the decision above, with its measurement.

**Round 2, on `b08f4d6`: one pass.**
- **The major finding is fixed.** Every attribute other than the font's
  content matched a real call, in place and not. The saved bytes matched on
  the small face and on the full JP face.
- **78 of 78 passed cold** across the three modules.
- **Found, minor:** an in-place reuse still closed the caller's old reader.
  A font opened lazily from the caller's own `BytesIO` lost its buffer.
  Fixed in `1d2a8e1`: the reader is left open.
- **Found, minor:** both font-comparison helpers zeroed `head.modified` but
  left `recalcTimestamp` on. `save()` then wrote the clock back, so two
  saves either side of a second boundary differed; it failed once live.
  Fixed in `1d2a8e1`: the helpers turn it off.
