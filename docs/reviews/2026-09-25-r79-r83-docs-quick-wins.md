# R-79, R-80, R-82 and R-83: the shipped docs match the code — 25 September 2026

**Assignment.** These are the last of the review's quick wins, priority 5
of the assignment: the docs items R-79, R-80, R-82 and R-83. The request of
record is the app's `REQUEST-to-skill-review-2026-09-24`. The findings are
those four rows in `docs/REVIEW-2026-09-24.md`.

They ship together as v76, stacked on #45 (R-99, v75), as R-05 and R-06
did. The version goes up because the shipped `SKILL.md`, references, evals
and module comments change. No code path changes, and no console line
changes, so nothing the app parses moves.

## Each finding, reproduced

The review's line numbers had drifted, so each was found again on
`955bddc` (v75).

- **R-79.** `references/retypeset.md` showed `scale_report.json` as
  `[{page, key, ratio}]`, the bare list builds before v58 wrote. v58 and
  later write `{"schema": 1, "version": …, "runs": [...]}`. Its section
  "The two ways a build fails" named `untranslated` and `overflow`. An AST
  walk of `retypeset.py` finds nine legacy refusal kinds.
- **R-80.** `SKILL.md`:
  - it said "the four identity facts" and listed five;
  - its one test command, `python3 -m unittest tests.test_pipeline -v`,
    collects 278 of the 748 test ids (756 with this change's 8);
  - "Read during recon, before touching the file." sat on the
    consumer-guide entry. `ad52f1d` put it on `failure-modes.md`, and
    entries inserted later separated them.
- **R-82.** `pipeline.py verify` exits 2 with `unknown command verify`. The
  evals README and the three `graders/gates.md` told the author to run it.
- **R-83.** These comments had drifted:
  - `_console.py` cited `pipeline.py` call sites by line number
    (`:87` … `:365`). `:87` is now an import line.
  - `results.py` cited `verify.py:322`.
  - `pipeline.py` cited `qa_check.py:386`.
  - `results.py` said `tests/test_pipeline.py` "holds 177 `redirect_stdout`
    blocks". That was true at `5a6c2af` (v58), where the module was written;
    the file now holds 195.
  - `verify.py`'s gate list gave han-forms' pass bar as "Own reference
    0.000", a measurement. The bar is `OWN_MAX = 0.02`.

## The change

- **`references/retypeset.md`:** a table of all nine refusal kinds, with
  each one's exception, cause and fix. It says:
  - the checks run in the table's order and stop at the first refusal;
  - two groups are listed together;
  - a refused build saves nothing, so an earlier build's output and report
    stay on disk.

  The scale report is shown as a JSON example of the enveloped shape. The
  version placeholder is `…`, so the example does not go stale at the next
  bump.
- **`SKILL.md`:**
  - it says "five identity facts";
  - the test commands are the README's: fetch the fonts, check them, then
    `discover -s tests -t .`;
  - the recon note is back on `failure-modes.md`;
  - the retypeset summary points at the full list.
- **Evals:** the README and graders say `verify.py`, "directly or through
  `pipeline.py rebuild`". Rebuild prints the `PASS field parity` line the
  regex graders match.
- **Comments:** they cite functions, not line numbers. The 177 count is
  dated to v58. The han-forms bar reads `<= 0.02`.

## Red, then green

`tests/test_shipped_docs.py` has 8 tests. Each reads the fact from the
code, not from a copy:
- the refusal kinds come from an AST walk of `retypeset.py`;
- the report's keys come from `write_scale_report`;
- the commands come from `pipeline._main`'s dispatch;
- the thresholds come from `han_forms`.

So the next change to that code fails here instead of leaving the doc
wrong. All 8 fail on `955bddc`, each as a failure, not an error. All 8 pass
on `ceffdf3`.

## Suite

CI's commands, on macOS:

| step | `ceffdf3` | `0d22d9b` |
|---|---|---|
| suite | 756 tests: 1 failure, 1 expected failure, 0 ResourceWarnings | the same |
| canary | 15, OK | 15, OK |
| repository | 6, OK | 6, OK |
| eval fixtures | exit 0 | exit 0 |

- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.

## Independent verification

This is not a Rule 1 item: nothing about rendering, shaping, fonts or
layout changes. The new table makes claims about runtime behaviour, though,
so three passes on a different model (Sonnet) tried to refute every claim
by running it. They worked on `git archive` copies of `955bddc` and
`ceffdf3`. **Every claim was confirmed.**

- **The refusal table.** Each of the nine kinds was triggered from a fresh
  PDF, merges' three causes included. Each raised the named exception, with
  its key and exit code 1.
  - **Order:** four jobs each tripped two kinds from different rows. Only
    the earlier row's key appeared.
  - **Groups:** both groups were tripped together, and every item of every
    kind was listed in one exception.
  - **What stays on disk:** after a refused build, the earlier build's
    `out.pdf` and `scale_report.json` were byte-identical, with the same
    mtimes.
  - **Fixes:** `skip` let a rotated shaped job succeed, and `allow_scale`
    an overflowing one.
  - **Report and console:** a real shrunk build's report matched the JSON
    example. Every kind printed a `FAIL:` block except the unmatched merge,
    which printed one `!!` line.
- **SKILL.md, evals and comments.**
  - The new command collects 756 test ids where the old one collected 278.
  - `pipeline.py verify` exits 2. A real `init` and `rebuild` job printed
    `PASS field parity`.
  - The 177 and 128 figures match `docs/reviews/2026-09-18-consumer-surface.md`.
  - `VerifyVerdict.to_dict` imports `__version__` deferred.
  - Han-forms compares with `<=` against `OWN_MAX` and `>=` against
    `OTHER_MIN`.
  - The 8 tests fail 8 of 8 on the base and pass 8 of 8 on the fix.
- **Completeness sweep of every shipped file.** No other place:
  - describes the bare-list report or "two ways";
  - runs a subset of the suite;
  - names a `pipeline.py` command that does not exist;
  - cites a line number.

  Eight other counts in comments were spot-checked, and all are right.

**One finding, fixed in `0d22d9b`.** `_console.py` and a `pipeline.py`
comment said `pipeline.py` calls "five library functions directly". It runs
nine stages in-process: `extract_segments`, `qa_check`, `verify` and
`bilingual` `main` as well. This predates the change. It was the same kind
of drift, in the sentence R-83 edited, so both comments now name examples
instead of a count.

**A correction to `0d22d9b`'s commit message.** It says "nine
console-opening stages". An AST check shows nine stages run in-process, and
six of them open `console()` themselves: `strip_text`, `render_pages` and
`compare` do not. The comments are right, because the four stages they name
all open it. The message is left as committed, and this note corrects it.

**Not fixed here: a stale output after a refusal.** Nothing removes the
earlier build's output and `scale_report.json` when a later build refuses.
The review already has this as R-15, held with group C. The table now says
it, and nothing else changes.
