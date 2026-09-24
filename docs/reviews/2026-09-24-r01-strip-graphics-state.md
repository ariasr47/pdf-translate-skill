# R-01: strip keeps the graphics state set inside text objects — 24 September 2026

**Assignment.** The product ranked this priority 2 of the review
assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`; the rule behind it is
`docs/DECISIONS.md`, 2026-09-24, and the finding is R-01 in
`docs/REVIEW-2026-09-24.md`. The product's acceptance criteria are:
- a test that fails on the unfixed code with a one-defect PDF and passes
  after the fix;
- Rule 1 with a rendered pixel comparison;
- for a strip change, the 17-PDF wild probe re-run with a render diff;
- a version bump, and a notice to the app.

## The defect

`strip_ops` dropped every operator between `BT` and `ET`. But `BT`/`ET` do
not save and restore the graphics state (PDF 32000-1 §9.4). Colour, `gs`,
line width and `cm` set inside a text object stay in effect after `ET`, so
whatever the page drew next came out in the wrong state.
- The mandatory visual pass might catch the loudest case: arxiv's pale
  table shading drawn black.
- It would likely miss the quiet ones: USCIS N-400's black rules drawn
  white, Medicare's blue drawn near-black, IRS label boxes.
- No gate sees it. On a constructed page the ink gate even returned PASS
  (1.67) while a pale cell turned black.

## Measured before building

An inventory of every operator inside `BT`…`ET` covered the 17 wild PDFs
and the 16 corpus fixtures: 33 files, 465 pages, 545 streams (465 page
streams and 80 Form XObjects) and 39,981 text objects, with 0 parse errors.

**Inside text objects:**
- Text operators: showing 159,521, positioning 145,989, text state 59,519.
- Other operators: marked content 50,294, general graphics state 3,998
  (`gs` 1,942), colour 3,739, and `cm` ×4.
- Never seen: `q`/`Q`, `Do`, inline images, path operators, `sh`, and clip
  render modes (`Tr` 4–7).
- Marked content always balances within its own text object.

**What the old strip got wrong:** 27 files have non-text operators inside
text objects. The old strip left 1,192 painting operations with the wrong
graphics state, 337 of them visibly. 30,709 pixels changed between the old
strip and the prototype, on 18 pages in 5 files (72 dpi):
- arxiv-babeldoc pages 1, 5 and 9;
- irs-i1040gi, 8 pages;
- medicare-handbook pages 10 and 47;
- state-ds11 pages 2 and 5;
- uscis-n400 pages 4, 6 and 8.

**The prototype.** It drops only `BT`, `ET` and the text operators, and it
rendered every non-text pixel like the original on all 465 pages.

## The change

`strip_ops` in `pdf_translate/strip_text.py`:
- inside a text object, drops `BT`, `ET` and `TEXT_OPERATORS`, the text
  operators of PDF 32000-1 Table 51:
  - showing: `Tj TJ ' "`;
  - positioning: `Td TD Tm T*`;
  - text state: `Tc Tw Tz TL Tf Tr Ts`;
- keeps every other operator in place and in order;
- tracks nesting with a depth counter.

Documentation:
- `references/failure-modes.md` §4 now describes the reverse leak;
- `docs/DECISIONS.md` records the rule;
- the version goes from 62 to 63.

## Red, then green

`tests.test_pipeline.StripKeepsGraphicsStateTests` uses constructed pages
(`build_graphics_state_pdf`). The rectangle drawn after `ET` is probed at
its centre on a 72 dpi render.

On the R-03 base, the tests failed six times (exit 1):
- a light-green fill (229, 255, 229) came out black, on the page and
  inside a Form XObject;
- a grey fill (229) came out black;
- 30% opacity (179) came out black;
- a blue stroke of width 6 came out grey (135);
- `cm`, marked content and the colour inside the text object were dropped.

The control case, with the colour set before `BT`, passed. With the change
all pass, and the corpus verdicts are unchanged.

**The render check.** It was re-run with the shipped fix against the
measured prototype. It gave 0 differing pixels on all 465 pages. Outside
text boxes, the fixed strip differs from the original only on
`rotated.pdf` (1,754 px), and that is the check's own text mask ignoring
`/Rotate 90`.

## Suite, probe, render diff and Rule 1

**Suite.** CI's 22 modules on this branch, on macOS, ran 704 tests: R-03's
701 plus 3 new ones. There was 1 failure, and no errors or skips. The
failure is the macOS-only
`HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
the same on every branch. The other steps passed too: the canary's 15 tests
OK, binary integrity's 3 OK, and the eval fixtures built.

**The wild probe.** It ran into a scratch directory and exited 0 on all 17
files. Compared with the tracked baseline, the only differences are R-03's
scaffold entry counts on 8 forms, which this branch inherits. The baseline
refresh is part of R-03. No verdict, segment count, core count, warning or
per-page text-block count changed.

**The render diff.** All 17 wild PDFs were stripped by R-03 and by this
branch, and every page rendered at 72 dpi with annotations. 20 of the 449
pages differ: arxiv 3, irs-i1040gi 9, medicare 2, state-ds11 3, N-400 3.
All are in the 5 files the inventory flagged, and no other file changes by
a pixel. That count includes any byte difference; the inventory's 18 pages
use a channel threshold of 24 with annotations off.

**The pixel figures, measured three ways.**
- 30,709 pixels differ between the old and the new strip, on 18 pages
  (inventory, channel delta > 24).
- Two independent harnesses counted pixels that differ from the original
  outside text: 19,933 and 19,706 before the fix, each with its own text
  mask. Both found the same 18 pages in the same 5 files. After the fix,
  both found 0 on every page of all 33 files.

**Rule 1.** Independent passes ran on a different model (Sonnet), each with
its own scripts.
- **Reproduce and pixels.** The shipped tests, run against the old
  `strip_text`, fail 6 times; against the new one they pass.
  - The verifier built 15 fixtures of its own: fill, stroke plus width,
    grey, opacity and `cm`, each on a page, in a Form XObject and in a
    nested Form XObject. All 15 were wrong before and right after. Every
    fixture's remaining full-page difference is 225 px, the removed "Hello"
    glyphs.
  - Across the 465 pages, 0 non-text pixels differ from the original after
    the fix. Pass.
- **Break it.** 20 of 20 adversarial checks pass:
  - `q`/`Q` inside a text object is kept and balanced;
  - nested, unterminated and stray `BT`/`ET` do not crash;
  - inline images, `Do` and path painting inside a text object are kept,
    pixel for pixel;
  - clip-mode (`Tr 7`) text strips byte-identically to before, so it is not
    changed here;
  - marked content spanning `BT`/`ET` stays balanced;
  - text state outside `BT` is kept;
  - the OCR-layer and image-only refusals and the corpus verdicts are
    unchanged.
  Pass.
- **Code review.** It found two things, both fixed: this file was
  uncommitted, and it held an unfilled placeholder. The review's own wild
  harness also found the same 5 files and 18 pages before the fix, and 0
  after. Pass once fixed.

**Follow-up, not assigned.** Clip-mode text (`Tr` 4–7) is dropped whole,
as before, so later graphics lose the clip. The corpus has no case of it. A
refusal is proposed separately.
