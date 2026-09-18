# Row 32 — the terminology loop — evidence

Branch `feat/terminology-loop`, off `docs/32-design-canvas` at `ecde609`, which is itself `main` at
`bacc436` (v56, gates 19–21 merged as PRs #10 and #11) plus the design and plan commits.
Plan: `docs/plans/2026-09-17-terminology-loop.md`. Design: `docs/design/32-terminology-loop/`
(eight artboards). Version 56 → 57.

> The plan says to branch off `main`, assuming the design branch would be merged first. It is not
> pushed yet, so branching off `main` would have left the build with no plan, no canvas, and no
> `.gitignore` rule for the seeded canvas HTML — the first commit tried to add 2.5 MB of editor
> payload. Stacking on the design branch is the same content in the right order; it changes nothing
> about what gets built.

## 1. The compass

The first FL-150 → Japanese job exited `verify` with 0 and `qa_check` with 0 errors while carrying
世帯主 for "head of household" and 相手方の親 for "the other parent". Both are wrong, one of them
critically: 世帯主 is the registered head of a Japanese 住民票 household, normally a married person,
where the US filing status is available only to someone unmarried. A reader would tick the wrong
box about themselves.

No gate could have seen either. The page was right, the strings were present, the script was
correct, the numbers matched. A post-delivery MQM review pass and a human read found them.

That is the whole argument for this row: **the second reader is a deliverable, not an option**, and
nothing in the pipeline made them one.

## 2. The three rulings

Settled by the operator on 2026-09-17 against `docs/design/32-terminology-loop/OpenQuestion.dc.html`.
Each was costed against its alternatives before it was settled.

### Ruling 1 — `finish` gains `--work DIR`

`cmd_finish` takes five bare positionals and never sees the work directory, so a refusal has nowhere
to look for `review.json`.

- *Rejected: infer from `FINAL.pdf`'s directory.* The FL-150 delivery went to `Downloads/` while the
  job lived elsewhere. The gate would have refused a fully reviewed job, and then been switched off.
- *Rejected: a sidecar written by `rebuild`.* Reintroduces the stale-file class of defect that PR #7
  exists to fix, and breaks whenever `retypeset` is run directly.
- **Settled:** an explicit `--work`. `finish` without it refuses and names the missing flag.

### Ruling 2 — `resolution` is a strict enum; prose moves to `resolution_note`

`references/review.md` §4 has specified `accepted|rejected|open` since before anything read the
field, so nothing enforced it. The one real `review.json` in this repo stores prose in all 31
findings.

- *Rejected: a strict parser.* It would refuse all 31 findings on the only job that exists.
- **Settled:** `--ingest` accepts a legacy prose value by its leading token, reports one migration
  line per finding, and keeps the whole original string in `resolution_note` — on this job the
  rejections are the most valuable text in the file.

### Ruling 3 — the reviser names the term

`core` is the mapping key, and six of the FL-150's eleven accepted terminology findings are keyed to
a whole sentence: `"Utilities (gas, electric, water, trash)"` where the term is `Utilities →
水道光熱費`.

- *Rejected: diff `target` against `suggestion`.* That recovers the target side only. The source side
  is the column `qa_check --glossary` matches on, and there is nothing safe to infer it from.
- **Settled:** terminology findings carry optional `term` and `term_target`, asked for by
  `review_prompt.md`. **A terminology finding without them is reported and skipped, never guessed
  into a termbase that gates the next job.**

## 3. The R5 tension, and what answers it

`docs/REQUESTS-from-product.md` R5: a verify FAIL is advisory and **the document is still
delivered**; only a build refusal withholds it.

`finish` is `field_fonts` + `compare` — packaging, not building. A hard refusal there is a
withholding by a non-build stage. For the product consumer the refusal is therefore decoration: they
will pass `--no-review` permanently, or drive the library and never read stdout at all.

The refusal is still built, because it serves the person driving the CLI by hand. But the
load-bearing part for the product is **the record, not the refusal**:

- `run_review()` returns a `ReviewVerdict` with `to_dict()`; the CLI only prints from it.
- `finish` writes `review_state.json` beside `FINAL.pdf` on **every** run, refused or not.
- `--no-review`'s REVIEW line is written into that record *and* printed, so a caller that discards
  stdout cannot lose it.

A delivery that carries its REVIEW line only in a terminal scrollback does not carry it.

## 4. Two corrections to the plan, measured before any code was written

The plan was written against the fixture; these two claims in it did not survive contact with the
file itself. Both were found by measuring `dev/jobs/fl150-ja-2026-09-17/review.json` before
implementing, and neither changes a ruling.

### 4.1 The leading-token rule needed one more step

The plan specifies `resolution.split(',')[0].split(':')[0].strip().casefold()`. Three of the four
real prose shapes carry a qualifier *before* the colon:

| stored resolution | the plan's rule yields | in the enum? |
| --- | --- | --- |
| `accepted, applied in v2 (2026-09-17)` | `accepted` | yes |
| `rejected: both renderings are attested; …` | `rejected` | yes |
| `rejected on measurement: the label ends at 259.5 pt…` | `rejected on measurement` | **no** |
| `accepted with a different fix: 月給／週給／時給…` | `accepted with a different fix` | **no** |

So the rule refuses two findings the file resolves perfectly clearly. The token is the first **word**
of the trimmed head — `.split()[0]` — which yields `accepted|rejected|rejected|accepted` and
reproduces the plan's own stated counts of 25 accepted / 6 rejected exactly. Implemented as
`review.leading_token`, tested by `test_a_legacy_prose_resolution_is_parsed_by_its_leading_token`
against all four real shapes.

### 4.2 The fixture names no terms at all, so nothing reaches the termbase

The plan's Task 1 expects "five named pairs added, six skipped for want of a term". Measured, the
union of keys across all 31 findings is:

```
['category', 'core', 'detail', 'resolution', 'severity', 'subtype', 'suggestion', 'target']
```

There is no `term` and no `term_target` on any finding — this review pass predates the fields that
ruling 3 adds. So the measured outcome is **0 added, 11 skipped**, not 5 and 6.

Two ways to reach 5/6 were considered and both rejected:

- *Edit the fixture to add `term`/`term_target` to five findings.* The plan's own Global Constraints
  make the real job the fixture of record and say a mismatch is a code defect, never a reason to
  edit the numbers. Adding fields to the record of a review pass that actually happened is rewriting
  what a reviser said.
- *Fall back to `(core, suggestion)` when the core is "short enough" to be the term.* This is exactly
  the inference ruling 3 forbids, and any threshold is arbitrary: of the eleven, `head of household`
  and `married, filing separately` are terms, `from this domestic partnership` contains one, and
  `I declare under penalty of perjury under the laws of…` is a sentence. Guessing wrong writes a
  wrong term into a file that gates the next job — the precise harm this row exists to prevent.

**Settled conservatively:** the strict reading of ruling 3 is implemented, and
`test_the_real_job_names_no_terms_so_every_pair_is_skipped` pins the measured 0/11. The loop reports
all eleven by core so the operator can see exactly which findings need a term named. The FL-150
termbase gets filled when that job is re-reviewed under the new prompt, which is what the prompt
change in Task 3 is for.

*This is the one item on this branch where the operator may reasonably rule differently.* If the
FL-150 record should be enriched, the change is one fixture edit plus the expected numbers in that
one test.

## 5. Task 1 — `review.py`

`pdf-translate/pdf_translate/review.py`, `pdf-translate/tests/test_review.py`.

- `SCHEMA`, `RESOLUTIONS`, `CATEGORIES`, `SEVERITIES`, `leading_token`.
- `ReviewFinding` and `ReviewVerdict`, both `frozen=True` with tuple fields and a `to_dict()`
  carrying `schema` and `version` — the shape `VerifyVerdict.to_dict` set (`verify.py:322`), with the
  same deferred `from . import __version__` to dodge the import cycle.
- `load_review`, `validate`, `review_pairs_md`, `review_prompt_md`, `termbase_rows`,
  `append_termbase`, `run_review`.
- The module prints nothing, raises nothing and exits nothing.

Measured against the real files:

| measurement | value |
| --- | --- |
| cores / merges / overrides / notices | 247 / 13 / 5 / 1 |
| findings | 31 — 1 critical, 6 major, 24 minor |
| resolutions after migration | 25 accepted, 6 rejected, 0 open |
| terminology findings | 12, of which 11 accepted |
| termbase rows added / skipped | 0 / 11 (§4.2) |

One design decision not in the plan: the break marker `‖` appears in **core targets**, not only in
the notice. It is a layout instruction, and a reviser who reads it as a character reports it as an
error. `review_pairs.md` renders it as `<br>` inside table cells (a real newline would break the
row), as a line break in the notices block, and states what it means. Pinned by
`test_review_pairs_renders_every_break_marker_as_a_line_break`.

```
Ran 38 tests in 0.155s
OK
```

## 6. Task 2 — the CLI

`pipeline.py` gains `cmd_review`, and `cmd_finish` gains `--work` / `--no-review`, the refusal, and
`review_state.json`. Both new commands emit through `logging.getLogger('pdf_translate')` — E3's
convention, adopted here so this row needs no second pass. `pipeline.main` wraps `_main` in a
re-entrant `_console()` that attaches one `StreamHandler(sys.stdout)` with `Formatter('%(message)s')`.
`pdf_translate/__init__.py` attaches a `NullHandler` and nothing else.

`pipeline.py`'s existing 31 `print` sites are deliberately **not** converted. They are E3's job; the
mixture is expected and temporary.

Two things this task surfaced that the plan did not anticipate:

- **`finish` must read the review without writing anything.** The first implementation called
  `run_review(work)` with no `ingest`, so it never read `review.json` at all and every job looked
  unreviewed. Adding `ingest='review.json'` fixed that but introduced a worse problem: a packaging
  step would have silently regenerated the reviser's inputs and appended to the termbase behind
  `review --ingest`'s back. `run_review` therefore gained `generate=False`, and `finish` uses it.
- **`--glossary` now joins `--work`.** `cmd_qa` joined `--segments` to the work directory but left
  `--glossary` against the caller's cwd, so the two-command story (`review --ingest` writes
  `work/glossary.csv`; `qa --work … --glossary glossary.csv` reads it back) needed a path dance. A
  bare name that exists under `--work` now resolves there; an explicit path that resolves is
  untouched.

### Console parity

Not asserted — run. A `main` worktree at `bacc436` and this branch, the same nine fixture jobs,
`dev/probes/verdict_parity_runner.py` under each:

```
# package: C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py
# package: C:\Users\rodri\AppData\Local\Temp\parity-main\pdf-translate\pdf_translate\__init__.py
--- diff stdout halves
IDENTICAL: console parity holds
```

Only `__init__.py` and `pipeline.py` touch `logging`; `verify.py`, `retypeset.py` and `qa_check.py`
are untouched, which is why the handler on the package logger cannot reach them.

### One observation for the operator

The plan specifies one migration line per migrated finding. On the FL-150 that is **30 lines**,
which buries the two lines a reader is actually looking for (the `OPEN` findings and the closing
count). It is implemented as specified and the summary line is last, so nothing is lost — but if
this stays noisy in practice, grouping identical values with a count would cut it to four lines
without losing information.

## 7. Task 4 — the canary's terminology axis

`dev/canary/score.py` gains `terminology_axis()` and `source_words()`. The FL-150, measured:

```json
{"findings": 31, "accepted": 25, "rejected": 6, "open": 0,
 "terminology": 12, "terminology_accepted": 11, "termbase_ready": 0,
 "source_words": 1635, "accepted_per_1000_source_words": 15.29,
 "false_positive_rate": 0.1935}
```

A job with no readable `review.json` scores `None`, never `0` — an unmeasured job and a job whose
reviser found nothing are not the same number, and a zero would read as the second.

The false-positive rate measures the **reviser**, which is the point: 6 of 31, and two of those six
were in the reviser's own top seven findings. A loop that gates the next job on a reviser's output
has to measure the reviser too. This is the first measurement, not a target.

## Docs and version

Version 56 → 57 across all four sources, red first against the lockstep test
(`tests/test_verify_report.py:648`). `.github/workflows/tests.yml` gains `tests.test_review`.
`references/gates.md` gains a section stating that the review loop is **not** a gate and that nobody
should look for a gate 22. `SKILL.md` step 1 gains the terms-of-art table as the fifth identity
fact, step 5b names the termbase's new provenance, step 8 puts the review step ahead of the
delivery checklist. `README.md`, `docs/DECISIONS.md`, `docs/REQUESTS-from-product.md` and
`dev/goals/PROGRAM.md` all carry the row.

## Review

_(the whole-branch reviewer's verdict goes here)_
