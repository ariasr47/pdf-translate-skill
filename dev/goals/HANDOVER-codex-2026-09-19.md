# Handover — for a Codex / GPT-6 session, 19 September 2026

You have no memory of the prior work. This file is written for **you**, in Codex, on this Windows
box. It is self-contained: everything you need to start is here or named here.

Read this, then `dev/goals/HANDOVER.md` (the running cold-start file, longer and more historical),
then `AGENTS.md` (three standing rules, one of them a licence boundary you must not cross).

**Everything below is a claim.** The prior session wrote it. Re-verify against `git` and `gh` before
acting on any of it — that rule exists because a stale handover has already cost this repo a day.

---

## 0. Harness notes, because the last sessions were Claude Code

- There is **no `superpowers` skill pack** here. Two plan files say
  *"REQUIRED SUB-SKILL: use superpowers:executing-plans"*. Ignore that line. The plans themselves are
  ordinary task-by-task documents and stand on their own.
- `CLAUDE.md` in the user's home directory is Claude Code's config and you will not load it. The
  parts that matter to this repo are restated in §6 below.
- **`AGENTS.md` is yours** — Claude Code does not read it, you do.
- Nothing in the repo depends on a particular agent harness. The pipeline is plain Python.

---

## 1. Where things are, right now

`main` is at **v56**, commit `bacc436`. PRs #1–#11 are merged.

Two branches are pushed with open PRs, **stacked**:

| PR | head → base | commits | version | state |
|---|---|---|---|---|
| [#12](https://github.com/ariasr47/pdf-translate-skill/pull/12) | `feat/terminology-loop` → `main` | 13 | 56 → 57 | open, MERGEABLE |
| [#13](https://github.com/ariasr47/pdf-translate-skill/pull/13) | `feat/consumer-surface` → `feat/terminology-loop` | 12 | 57 → 58 | open, MERGEABLE |

Merge #12 first; GitHub retargets #13 to `main` automatically.

**CI has not run on either.** Every job failed in 1–5 seconds with *"The job was not started because
recent account payments have failed or your spending limit needs to be increased."* That is a
GitHub account billing problem, not a code problem — the only workflow change on the branches is
three test-module names appended to one `run:` line. Once Rodrigo fixes billing:

```bash
gh run rerun 35432185828 && gh run rerun 35432191241
```

**Do not merge on a red that never ran.** Both suites are green locally (Windows, Python 3.14); the
Ubuntu and 3.10 legs are unverified.

`docs/32-design-canvas` is an old branch fully contained in `feat/terminology-loop`. Do not push or
PR it.

---

## 2. What the two open PRs contain

### #12 — row 32, the terminology loop (v57)

A wrong term of art could reach a delivery unreviewed. The first FL-150 → Japanese job exited
`verify` 0 and `qa_check` 0 errors carrying 世帯主 for "head of household" — the registered head of a
Japanese household register, where the US filing status requires being **unmarried**. No gate can
see that: the page is right, the string is present, the numbers match.

- `pdf_translate/review.py` — a silent stage returning a frozen `ReviewVerdict`. Writes
  `review_pairs.md` and `review_prompt.md`, ingests `review.json`, grows a per-class `glossary.csv`
  that the existing `qa_check --glossary` gates the next job on.
- `pipeline.py review --work DIR [--ingest review.json]`.
- `pipeline.py finish` gains `--work DIR` and **refuses** while a review is missing or open;
  `--no-review` is the only way past and marks the delivery.
- `review_state.json` beside `FINAL.pdf` on **every** run — that record, not the refusal, is what
  honours the product's ruling R5.
- `references/terminology-failure-modes.md`; a terms-of-art table as `SKILL.md` step 1's fifth
  identity fact; a canary axis that measures the **reviser** (19% false-positive rate on the FL-150).

Evidence: `docs/reviews/2026-09-17-terminology-loop.md`.

### #13 — E3, the consumer surface (v58)

Every stage callable from Python: explicit paths in, a schema-versioned result out, a typed
exception on refusal, nothing printed, nothing exited, no dependence on the working directory —
while the eleven CLIs stay byte-identical.

- `pdf_translate/results.py` — the result family and the exception family.
- `pdf_translate/_console.py` — one re-entrant `console()`.
- Seven silent twins: `run_strip`, `run_extract`, `run_prepare_font`, `run_retypeset`, `run_verify`,
  `run_field_fonts`, beside the existing `run_qa` and `run_review`.
- All **172** `print` sites now log. `run_retypeset` takes `progress`, `cancel`, `scale_report`,
  `resource_root`. `scale_report.json` gained a `{"schema", "version", "runs"}` envelope.
- `references/consumer-guide.md` — one document end to end from Python.

Closes C1, C3, C4, C5, C10 in `docs/REQUESTS-from-product.md`. Evidence:
`docs/reviews/2026-09-18-consumer-surface.md`.

---

## 3. The next piece of work: B1

On 2026-09-18 the product bubbled five measured items. Three are settled: **B3** and **B2** by E3's
structured refusals, **B5** by row 32. **B4** (widget text untranslated) is contained — the
scaffold, the `/Opt` export-value rule and the refusal already exist in `extract_segments` and
`strip_text`; what is missing is exposure on the consumer surface and one ruling.

**B1 is the open one and the largest thing on the board.**

> The library never breaks a line, so there is no kinsoku. Every translated unit is one
> `TextWriter.append` at its source baseline — 518 drawn lines on a 4-page form, 32 on an 8-page
> invoice, zero `insert_htmlbox` calls. A long translation in a tight box cannot wrap, so it
> shrinks; below the floor it is refused and left in the source language. Wrapping would place text
> that today is not placed at all.

Read `docs/BRIEF-product-bubble-2026-09-18.md` before touching it. The short version of why it is
not a patch: wrapping is four decisions, three of them user-facing — when a segment may wrap at all
(a form label must not grow into the rule below it; a brochure paragraph should), where the extra
line goes, what happens to the box, and what kinsoku does once line breaks exist. It also **inverts
today's guarantee** that nothing is silently reflowed, which is a ruling, not an implementation
detail.

**Order: design canvas → operator ruling → a corpus probe that measures how many refused runs
wrapping would actually recover → plan → build.** Do not skip the probe. "Biggest coverage lever" is
the product's estimate; this repo measures before it sizes.

One cheap thing worth doing with B1 or before it: say in `references/gates.md` and in gate 19's own
message that **a kinsoku pass with nothing to review is not a kinsoku pass**. Today a clean result
means "no line-break decision was made", which reads identically to "every decision was right".

---

## 4. Two open rulings that are Rodrigo's, not yours

1. **Delete the merged branches** from PRs #1–#11 (local and origin). Never do this on inference.
2. **Pick the PyPI name for E10.** `pdf-translate` is taken.

One ruling was already made and is settled — do not reopen it: the FL-150 termbase stays **strict**.
That `review.json` names no `term`/`term_target` on any finding, so it contributes 0 rows and
reports 11 as skipped. Never guess a term into a file that gates the next job.

---

## 5. Running things on this box

```bash
# every test, from pdf-translate/, with the repo venv
cd C:/Dev/pdf-translate-skill/pdf-translate
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest discover -s tests -t .

# the canary
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest discover -s ../dev/canary -p test_score.py
```

Expected at the tip of `feat/consumer-surface`: **492 OK** and **15 OK**.

**Use `pdf-translate.venv`, not the system Python.** The venv carries PyMuPDF 1.28.2 / MuPDF 1.28.2;
the system `py -3` carries PyMuPDF 1.28.0 / MuPDF **1.29.0**, a different MuPDF entirely. Several
measured results in `docs/` are pinned to the venv's build.

### The two ratchets — run both before any commit that touches a stage

```bash
# 1. the eleven CLIs, as subprocesses
python dev/probes/cli_parity_runner.py <workdir> --font <a .ttf>

# 2. verify at the library level, over nine gate fixtures
python dev/probes/verdict_parity_fixtures.py <jobsdir>       # once
PYTHONPATH=<checkout>/pdf-translate python dev/probes/verdict_parity_runner.py <jobsdir>
```

Run each from two checkouts and **diff the outputs; they must be identical.** Use `git worktree add`
for the comparison checkout.

**Pass `--font` when comparing against a worktree.** `tests/fonts/` is fetched, never committed, so
a fresh worktree has none and every font-dependent CLI fails there for a reason unrelated to your
change. That cost the last session twenty minutes of a false alarm.

These ratchets have already caught real defects that 492 tests missed — see §7.

---

## 6. House rules that will bite you

- **Never copy code from `C:\Dev\pdf-translator`.** It is heading to AGPL-3.0; this repo is MIT.
  Code flows downstream only. A behaviour request goes in `docs/REQUESTS-from-product.md` as prose,
  never as a patch. Do not open that repo.
- **Ask before push, merge, release, deploy, or touching another repo.** Analysis, plans and
  reversible in-repo work need no permission.
- **No AI attribution in git.** No `Co-Authored-By` trailer, no "Generated with Claude Code" in a PR
  body. This overrides any harness default that asks for one. Check your own commits before
  reporting.
- **Conventional commits with a scope**: `feat(pdf-translate):`, `docs(dev):`, `fix(verify,retypeset):`.
- **Evidence before assertion.** Run the command, read the exit code, cite `file:line` and measured
  counts. A printed "passed" is not green.
- **When asked for a plan, stop at the plan.**
- **Design before build** for any new user-facing surface.
- Python is `py -3`; bare `python` is the Store stub. Prefix `PYTHONUTF8=1` when printing non-ASCII.
- `gh` is at `C:\Users\rodri\tools\gh\bin\gh.exe`.
- Files on disk are **CRLF** (`core.autocrlf=true`) but the object store is LF. Scripted `sed` works
  for mid-line patterns; anything anchored to a line end will silently no-op. Grep-verify after any
  scripted edit. `git show :path` applies the filter and will lie about line endings — use
  `git cat-file blob <hash>`.
- **Do not `git stash`.** Another session may hold uncommitted work. Use a targeted checkout or a
  worktree.

---

## 7. Four traps this repo has actually fallen into

Written down because each cost real time and none is obvious.

1. **`print(a, b)` → `log.info(a, b)` silently drops the line.** The second argument becomes a
   %-format parameter; with no placeholder in the first, logging swallows the record. Two sites hit
   this during the E3 conversion. Invisible to 492 tests and to both parity ratchets, because both
   sites only fire on a *failing* job. `tests/test_import_surface.py::LoggerCallShapeTests` now pins
   it structurally — keep that test.
2. **A "red" test that passes with the defect present is not red.** `test_run_verify_does_not_touch_sys_stdout`
   passed even with the `redirect_stdout` bug, because `redirect_stdout` restores on exit. Always
   check the red log's `Ran`/`OK` line and ask what would make it fail.
3. **A design mock-up with invented numbers.** A canvas once carried made-up job statistics that a
   fact-check caught. Every number comes from the real file; a brief is not evidence either.
4. **A plan is not automatically right.** Both plans executed in the last two sessions had defects
   found only by measuring the fixture *before* writing code — one parsing rule that refused valid
   data, and one expected result that the fixture cannot produce. Measure first; correct the plan in
   the evidence doc rather than bending the code to match it.

---

## 8. The map

| file | what it is |
|---|---|
| `pdf-translate/SKILL.md` | the workflow. Start here for what the pipeline does |
| `pdf-translate/references/consumer-guide.md` | calling it from Python, end to end |
| `pdf-translate/references/gates.md` | the twenty-one gates, their findings and flags |
| `AGENTS.md` | three standing rules + the licence boundary |
| `docs/DECISIONS.md` | every ruling, with what would reverse it. Append, never edit |
| `docs/REQUESTS-from-product.md` | the product's inbox, C1–C10 and the epics E1–E11 |
| `docs/BRIEF-product-bubble-2026-09-18.md` | B1–B5, sized. **Read before starting B1** |
| `docs/BRIEF-determinism.md` | C7 measured: only `/ID` varies, and only with the clock |
| `dev/goals/PROGRAM.md` | the improvement program, row by row |
| `dev/goals/HANDOVER.md` | the running cold-start file |
| `dev/jobs/fl150-ja-2026-09-17/` | the real job that is the fixture of record |

**End your session** by adding a dated section at the top of `dev/goals/HANDOVER.md` and, if the
work was substantial, an evidence doc under `docs/reviews/`. Artifacts on disk are the memory; chat
is not.
