# R-02: small print is drawn at the size that fits — 24 September 2026

**Assignment.** The product ranked this priority 4 of the review
assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`, the rule behind it is
`docs/DECISIONS.md` (2026-09-24), and the finding is R-02 in
`docs/REVIEW-2026-09-24.md`. The product's acceptance criteria:
- the 4.0 pt clamp no longer bypasses the 0.7× floor;
- the gate sees the true ratio;
- a run under 4 pt is never enlarged;
- plus the shared bar: a failing-then-passing test, Rule 1 with a rendered
  pixel comparison, a version bump, and a notice to the app.

## The defect

Every legacy shrink-to-fit lifted the fitted size to 4.0 pt:
`fs2 = max(4.0, fs * room / width)`. This happened at four sites in
`pdf_translate/retypeset.py`:
- a plain run;
- a dot-leader label;
- a right-to-left dot-leader label;
- an override part with `max_width`.

The ratio passed to the 0.7× gate was the lifted `fs2 / fs`, so:
- **A source of 5.71 pt or less** that needed more than its room was drawn
  at 4 pt. That is wider than the room, so it ran over the next cell. The
  gate saw 4 / 5 = 0.8 for a run that needed 0.54, so it passed the floor,
  and verify exited 0.
- **A source under 4 pt** was drawn at 4 pt, *larger* than the source.
  `fs2 < fs` was false, so it was not even reported as scaled.

This contradicts the `DECISIONS.md` row of 2026-09-20: the ratio is the
size the page shows divided by the source size. It also contradicts the
module's own promise that shrink-to-fit is "bounded by the nearest
same-row obstacle ... so text never overlaps fields or neighboring cells".

## The change

`fitted_size(fs, width, room)` replaces the lift at all four sites:
- it returns `fs` when the run fits, and `fs * room / width` when it does
  not;
- a room of 1 pt or less counts as 1 pt, the guard the other budgets use,
  so a size is never 0;
- `consider_ratio` receives `fs2 / fs`, which is now what the page shows.

Consequences:
- **Small print** that needs less than 0.7× refuses like any other run.
- **`allow_scale`** ships it at the size that fits, and the scaled-runs
  report gives that ratio.

**Unchanged:**
- **Merges and shaped runs.** They are sized by the Story engine and never
  had the lift.
- **Typography-1.**
- **Verify's caption font-size fallback** (`max(4, rect.height - 4)`). It
  is a different thing: an estimate of a widget's font.

**Docs:**
- `references/retypeset.md` (the source-relative ratio);
- a new `references/failure-modes.md` §15, with SKILL.md and README
  counting fifteen.

**Records:** a `docs/DECISIONS.md` row, and the R-02 row in
`docs/REQUESTS-from-product.md`. The version goes from 64 to 65.

**Tradeoff.** A 4 pt legibility minimum and staying inside the room cannot
both hold. The lift chose legibility and got overlap, which was silent. This
change chooses the room, and the smaller size is reported and gated. A
product ruling on a minimum size would need a refusal or a wrap for runs
that cannot fit above it, not a lift.

## Red, then green

`tests.test_pipeline.SmallPrintClampTests` builds `build_small_print_pdf`:
a small label with a neighbour 90 pt to its right, or a small dot-leader
row. Each target is built from words until it needs a chosen ratio of the
label's room. The tests:
- a 5 pt run needing about 0.5× refuses without `allow_scale`;
- with `allow_scale` it is drawn at 5 × ratio (under 4 pt), ends before the
  neighbour's left edge, and reports that ratio;
- a 3 pt run needing about 0.9× is drawn under 3 pt, inside its room, and
  reported;
- a 5 pt leader label, a 5 pt Hebrew leader label (right-to-left and not
  shaped, so the right-to-left site) and a 5 pt override part each refuse
  below the floor.

**Red.** On the unfixed code (the `154f842` tree), all 6 failed (exit 1).
- The four floor tests built with exit 0: the lifted ratio passed.
- The allowed run was drawn at 4.0 pt where it fits at 2.51 pt.
- The 3 pt run was drawn at 4.0 pt.

**Green.** All 6 pass.

## Suite

CI's 22 modules on this branch, on macOS, ran 721 tests. There was 1
failure and 1 expected failure, with no errors or skips.
- The failure is the macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  the same on every branch.
- The expected failure is item 3's right-to-left source pin.
- The canary, binary integrity and the eval fixtures passed, and the
  version tests pass at 65.

## Measured on the wild corpus

The 17 wild PDFs were rebuilt on `main` (`154f842`) and on this branch, in
scratch directories, twice.

**1. An identity mapping** (each core to itself, Noto Sans).
- 6 files build, and their drawn spans are identical: 0 differ.
- The other 11 refuse identically on both, for glyph coverage (Noto Sans
  has no ► or ●).
- Identity text rarely needs to shrink, so this shows only that nothing
  else moved.

**2. A longer pseudo-translation.** Each core is followed by its own words
again, from the first, until the target has at least 1.3 times the
source's characters. That makes the median target 1.37 times its source,
and a one-word core doubles (77 of 1,117 cores on the 1040-ES). Characters
Noto Sans cannot draw become `-`. Every core is in `allow_scale`, so
nothing stops at the floor and the drawn sizes can be compared.
- 10 files build on both; 7 refuse identically, for glyph coverage in
  pass-through text.
- **Every difference is a removed lift.** 33 drawn spans differ, and every
  one was drawn at exactly 4.0 pt on `main` and smaller here: 2.84–3.98 pt
  for 31 of them.
  - The other 2 are two right-to-left runs on page 124 of
    `medicare-handbook.pdf`, which MuPDF groups into spans differently
    once they are smaller. They drew at 2.26 and 0.87 pt, ratios 0.19 and
    0.07, which `allow_scale` accepted.
- **Nothing got larger.**
- **The renders differ on 13 of 272 pages in 7 files.** These are the pages
  carrying those runs.
- **The overlap count falls.** Span pairs that overlap on the same row went
  from 332 to 325. The 7 removed are all on `irs-1040es.pdf`, where 7
  lifted runs had overlapped a neighbour.
- **The floor bypass happens on real forms.** On `irs-1040es.pdf`,
  "CAUTION" is a 5.25 pt label. With its synthetic target "CAUTION CAUTION"
  it needs 0.6642×, and on three pages `main` drew it at 4 pt and reported
  0.7619, which passes the floor. Without `allow_scale` it now refuses.
  A Rule 1 verifier padded by a different rule, and its CAUTION needed
  0.9058× on both trees; the number depends on the target's length. The other
  ratios that changed were already below 0.7 when lifted, so they refused
  either way, but they reported a size the page did not show: 0.6667
  (4 pt from 6 pt) for runs that need 0.47–0.66.

No source under 4 pt occurs in a file that builds. `irs-i1040gi.pdf` has 4,
but it refuses on glyphs. The 3 pt behaviour rests on the constructed
test.

## Rule 1

Two independent passes on a different model (Sonnet), each working from
`git archive` copies of `2f7e108` and `154f842`, with its own fixtures.

**Reproduce and pixels: PASS.** Five one-defect PDFs of its own covered
all four sites, plus a 3 pt source.
- At every site, `main` reported 0.80 and passed the floor. The branch
  refuses without `allow_scale`, and with it draws at the fitted size
  (2.47 to 2.56 pt from 5 pt) and reports that ratio.
- On `main` the 3 pt source was drawn at 4.00 pt and left out of the scale
  report. On the branch it is 2.61 pt, reported as 0.8706.
- **Pixels.** At 288 dpi, with only the translated run on the page, dark
  pixels inside the neighbour's box and past the room's end were 214 and
  236 on `main` for the 5 pt case, and 108 and 137 for the 3 pt case. On
  the branch they are 0 in every region.
- On `main` the 5 pt case's verify exited 0 with only
  `REVIEW scaled runs (1) p0 0.80x`.

**Break it and review: PASS, one minor finding.** It ran 14 edge cases on
both trees: room of 0 or less, zero width, `allow_scale` at 0.05,
`right` and `center` anchoring, list markers, a rotated run and
right-to-left text without leaders.
- The branch never crashed, drew at size 0, or drew outside the page, and
  always reported the true ratio.
- A normal-size page with shrinks that stay above 4 pt renders
  sha256-identical on both trees.
- On 6 wild PDFs that built on both, all 7 of its span differences were
  4.0 pt on `main` and smaller on the branch, never larger.
- The docs match, and failure-modes has 15 numbered sections.

The findings:
- **Minor: the CAUTION figures did not reproduce** under the verifier's own
  padding. The measurement section now states the padding rule and why the
  number depends on it.
- **Note: a degenerate room ships a sliver.** When the room was already
  negative before any translation, `allow_scale` ships a run a fraction of
  a point high (0.017 pt, reported as 0.00×) instead of refusing. `main`
  drew the same run at 4 pt over its neighbour or off the page. It is left
  as it is; the report shows it.
- **Note: a crash fixed on the way.** On `main`, an override part with empty
  text and a `max_width` of 0 or less raised `ZeroDivisionError`. The
  width guard in `fitted_size` prevents it.
