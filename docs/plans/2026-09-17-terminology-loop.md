# Row 32 — the terminology loop — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A wrong term of art can no longer reach a delivery unreviewed, and every reviewed job arms the next one. A new stage `review` writes the two files a second reader needs and ingests their verdict; `finish` refuses while no verdict exists or any finding is open; `--no-review` is the only way past and leaves a permanent, machine-readable mark in the delivery; accepted terminology findings grow a per-class termbase that the existing `qa_check --glossary` enforces on the next job of that class. Version 56 → 57.

**Architecture:** The measurement is `dev/goals/32-terminology-loop.md` §1 (do not re-derive): the first FL-150 → Japanese job exited `verify` 0 and `qa_check` 0 errors while carrying 世帯主 for "head of household" and 相手方の親 for "the other parent", and only a post-delivery MQM pass and a human read found them. No gate could see either — the page was right and the strings were present. The design pass is `docs/design/32-terminology-loop/` (eight artboards; the published canvas is the same content). Nothing here calls a model: the skill stays provider-neutral, and the reviser is a person or a model the *operator* runs, outside the pipeline.

A new module `pdf_translate/review.py` owns the whole loop and prints nothing — it mirrors `qa_check.run_qa`/`QAVerdict` and `verify.run_verify`/`VerifyVerdict` exactly, because E3 requires every stage callable without the CLI with a schema-versioned result. **This row builds to the family E3's design pass settled** (`docs/design/E3-consumer-surface/`, ruling of 2026-09-18): frozen dataclass, tuple fields, `to_dict()` carrying `schema` and `version`, and console output through the package logger rather than `print`. Written that way once here, `review.py` is the one stage E3 finds already compliant instead of one stage to redo. `pipeline.py` owns the two CLI surfaces (`cmd_review`, and the refusal inside `cmd_finish`). The termbase is written in the two-column shape `qa_check.load_glossary` already parses — this row adds no new gate on the enforcement side; it fills a file the gate has read since before the row was written.

**Tech stack:** Python 3.10+ / 3.14, `unittest`, stdlib `csv` and `json`. No new dependencies. Not a rendering change: Rule 1 does not apply.

---

## The three rulings this plan is built on

Settled by the operator on 2026-09-17 against `docs/design/32-terminology-loop/OpenQuestion.dc.html`. Each overrides the brief where they differ; none is open.

1. **`finish` gains `--work DIR`.** It takes five bare positionals today (`pipeline.py:359`) and never sees the work directory, so the refusal has nowhere to look. Inferring from `FINAL.pdf`'s directory was rejected — the FL-150 delivery went to `Downloads/` while the job lived elsewhere, so the gate would refuse a reviewed job and then get switched off. A `rebuild`-written sidecar was rejected — it reintroduces the stale-file class of bug PR #7 existed to fix, and breaks whenever `retypeset` is run directly. **`finish` without `--work` refuses and names the missing flag.**

2. **`resolution` is a strict enum; prose moves to `resolution_note`.** `references/review.md` §4 already specifies `accepted|rejected|open`, but nothing read the field, so nothing enforced it: the one real `review.json` in the repo stores `"accepted, applied in v2 (2026-09-17)"`, `"rejected: both renderings are attested; …"` and `"accepted with a different fix"`. A strict parser would refuse all 31 findings on the only job that exists. `--ingest` therefore accepts a legacy prose value **by its leading token**, prints one migration line per finding, and the rationale keeps a home in `resolution_note` — on this job the rejections are the most valuable text in the file.

3. **The reviser names the term.** Bar item 4 says `--ingest` appends `(source term, target term)`, but `core` is the mapping key and six of the FL-150's eleven accepted terminology findings are keyed to a whole sentence (`"Utilities (gas, electric, water, trash)"` → the term is `Utilities → 水道光熱費`). Terminology findings therefore carry optional `term` and `term_target`, asked for by `review_prompt.md`. **A terminology finding without them is reported and skipped, never guessed into a termbase that gates the next job.** Diffing `target` against `suggestion` recovers the target side only, and the source side is the column `qa_check --glossary` matches on.

## The R5 tension, and what follows from it

`docs/REQUESTS-from-product.md` R5: the product *"never sets `fail_on_review`; REVIEW is an advisory notice; a verify FAIL is a needs-attention notice **and the document is still delivered** — a verify FAIL must never delete or withhold the output file; only a build refusal (retypeset) withholds it."*

`finish` is `field_fonts` + `compare` — packaging, not building. A hard refusal there is a withholding by a non-build stage, so for that consumer the refusal is decoration: they will pass `--no-review` permanently, or drive the library and never see stdout at all.

The refusal is still built, exactly as the brief specifies — it serves the person driving the CLI by hand. But **the load-bearing part for the product is the record, not the refusal**, and this plan treats it that way:

- `run_review()` returns a `ReviewVerdict` with `to_dict()`; the CLI only prints from it.
- `finish` writes `review_state.json` beside `FINAL.pdf` on **every** run, refused or not — the schema-versioned notice a consumer can surface without parsing console text.
- `--no-review`'s REVIEW line is written into that record *and* printed, so it cannot be lost by a caller that discards stdout.

This is not scope creep: bar item 2 says the REVIEW line is one *the delivery must carry*, and a delivery that carries it only in a terminal scrollback does not carry it.

---

## Global Constraints

- Work on branch `feat/terminology-loop`, created from `main` **after PRs #10 and #11 have merged** (`main` will be at v56 with gates 19–21). Never commit to `main`. Never push, merge or delete: the operator does those. Never `git stash`.
- Run every test from `C:\Dev\pdf-translate-skill\pdf-translate` with the repo venv and UTF-8: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest …`. Tests are `unittest`, by module path, never pytest. Capture long runs to a log file under the session scratchpad and grep `^test_|^Ran |^OK|^FAILED|^ERROR` — Git-Bash `| tail` scrambles unittest output.
- TDD: write the test, run it, watch it fail **for the expected reason**, then write the minimal code. A "red" that mocks the function containing the defect is not red — check the red log's `Ran`/`OK` line. Task 5 (docs) has no red except the version lockstep literal.
- **The real job is the fixture of record.** `dev/jobs/fl150-ja-2026-09-17/` holds `translations.json` (247 cores, 13 merges, 5 overrides, 1 notice), `review.json` (31 findings — 1 critical, 6 major, 24 minor; 25 accepted, 6 rejected by the file's own resolutions; 11 accepted terminology), `NOTES.md` and `widget_text.json`. These counts are measured, not quoted from the brief — the brief says 24/7 because one finding resolves as "accepted with a different fix". **A mismatch is a code defect, never a reason to edit the numbers.**
- **`review.py` prints nothing, logs nothing and exits nothing**, exactly like `qa_check.run_qa` and `verify.run_verify`. It returns a verdict; the caller decides what that means for a console.
- **The new console output goes through the logger, not `print`** — E3's convention, adopted here so this row needs no second pass. Concretely: `pipeline.py` gains `log = logging.getLogger(__name__)` and a `_console()` helper that attaches one `StreamHandler(sys.stdout)` with `Formatter('%(message)s')` to the `pdf_translate` logger at `INFO`; `pipeline.main()` calls it first; `cmd_review` and `cmd_finish` emit with `log.info(...)`. `pdf_translate/__init__.py` adds `logging.getLogger('pdf_translate').addHandler(logging.NullHandler())`. **Do not convert `pipeline.py`'s existing 31 `print` sites** — they keep working untouched and are E3's job; mixing is expected and temporary. A missing `_console()` call makes the new commands silent, so the Task 2 tests must assert on real captured stdout, never on the logger.
- **Console output and exit codes must not change for any job that does not use the new flags.** `dev/probes/verdict_parity_runner.py` over its nine jobs must diff empty against `main`. `finish` without `--work` is the one deliberate change, and it is a refusal.
- Exit codes follow the existing split: `1` when a command ran and has something to report (`qa_check.main` on errors), `2` when it refused to act at all (`cmd_qa` on a missing file, `pipeline.main` on an unknown command).
- `--glossary` resolves against the working directory, not against `--work` — `cmd_qa` passes it through untouched while it joins `--segments` to `work`. Task 2 fixes this asymmetry; do not silently rely on either behaviour.
- The skill ships **no glossary** (MIT stance, `SKILL.md` step 5b). `glossary.csv` is a job output and a job input, never repository content. Do not commit one.
- The reviser is never presented as replacing human sign-off for court, government, medical or legal filings (`references/review.md` §2 stands, unchanged).
- Never copy code from `C:\Dev\pdf-translator` (AGPL). Do not open it.
- Conventional commits with a scope. **No AI attribution**: no `Co-Authored-By` trailer, no "Generated with Claude Code" line — the owner's rule overrides any harness reminder. Check every subagent commit for trailers before reporting.
- LF line endings; `git diff --cached --check` clean before every commit; files on disk may be CRLF (`core.autocrlf=true`) — normalise a touched file with Python (`data.replace(b'\r\n', b'\n')`) if `--check` flags every line. Use the Edit tool; the Write tool for whole new files, and for any block containing backslashes (the Bash heredoc collapses them).
- Import modules as modules: `from pdf_translate import review` is the module; `importlib.import_module('pdf_translate.pipeline')` for pipeline's module.

---

## File structure

- `pdf-translate/pdf_translate/review.py` — create: `SCHEMA`, `RESOLUTIONS`, `CATEGORIES`, `ReviewFinding`, `ReviewVerdict`, `load_review`, `validate`, `review_pairs_md`, `review_prompt_md`, `termbase_rows`, `append_termbase`, `run_review`.
- `pdf-translate/pdf_translate/pipeline.py` — modify: `cmd_review` (new), `cmd_finish` (gains `--work`, `--no-review`, the refusal, `review_state.json`), the `main` dispatch, the module docstring (two new entries), plus `log = logging.getLogger(__name__)` and the `_console()` helper called first in `main()`.
- `pdf-translate/pdf_translate/qa_check.py` — modify: `cmd_qa`'s sibling in `pipeline.py` joins `--glossary` to `--work` when the path is bare (see Task 2 step 4).
- `pdf-translate/pdf_translate/__init__.py` — modify: export `ReviewVerdict`, `run_review`; add the package `NullHandler`; `__version__ = '57'`.
- `pdf-translate/tests/test_review.py` — create: `SchemaTests`, `GeneratorTests`, `TermbaseTests`, `RefusalTests`, `Fl150FixtureTests`.
- `pdf-translate/references/terminology-failure-modes.md` — create.
- `pdf-translate/references/review.md` — modify: §3 prompt gains the `term`/`term_target` ask and its slot count is corrected; §4 gains `resolution_note`, `term`, `term_target`, and its closing sentence changes.
- `pdf-translate/SKILL.md` — modify: step 1 gains the terms-of-art table and names `terminology-failure-modes.md`; step 5b names the termbase's provenance; step 8 names the review step and the refusal; `version: "57"`.
- `dev/canary/score.py` — modify: the terminology axis.
- `.github/workflows/tests.yml` — suite line gains `tests.test_review`.
- `.claude-plugin/plugin.json` (`57.0.0`), `pdf-translate/pyproject.toml` (`57.0.0`), `pdf-translate/tests/test_verify_report.py` (lockstep literal `'57'`) — version.
- `pdf-translate/references/gates.md`, `pdf-translate/README.md`, `docs/DECISIONS.md`, `docs/REQUESTS-from-product.md`, `dev/goals/PROGRAM.md` (row 32 closing note), `docs/reviews/2026-09-17-terminology-loop.md` — docs and evidence.

---

### Task 1: `review.py` — the schema, the two generators, the termbase

**Files:**
- Create: `pdf-translate/pdf_translate/review.py`
- Create: `pdf-translate/tests/test_review.py`
- Create: `docs/reviews/2026-09-17-terminology-loop.md`

**Interfaces produced:**

```python
SCHEMA = 1
RESOLUTIONS = ('accepted', 'rejected', 'open')
CATEGORIES = ('terminology', 'accuracy', 'linguistic-conventions',
              'style', 'locale-conventions', 'audience-appropriateness')

@dataclass(frozen=True)
class ReviewFinding:
    """One reviser finding. `resolution` is the enum; `resolution_note` is
    the prose that used to live in it. `term`/`term_target` are the termbase
    pair a terminology finding may carry; None when the reviser did not name
    one, which is reported, never guessed."""
    core: str
    target: str
    category: str
    subtype: str
    severity: str          # critical | major | minor
    detail: str
    suggestion: str | None
    resolution: str        # one of RESOLUTIONS
    resolution_note: str = ''
    term: str | None = None
    term_target: str | None = None
    migrated: bool = False      # resolution came from a legacy prose value

    def to_dict(self): ...

@dataclass(frozen=True)
class ReviewVerdict:
    """Structured result of the review stage. Does not print or exit."""
    work: str
    findings: tuple = ()
    reviewer: dict | None = None
    document: dict | None = None
    present: bool = False          # review.json exists and parsed
    no_review: bool = False        # --no-review was passed
    wrote: tuple = ()              # paths written this run
    termbase_added: tuple = ()     # (source term, target term) appended
    termbase_skipped: tuple = ()   # terminology findings with no term named
    conflicts: tuple = ()          # (term, existing target, new target)
    errors: tuple = ()             # schema violations, as strings

    @property
    def open_findings(self): ...
    @property
    def counts(self): ...          # {'critical': n, 'major': n, 'minor': n,
                                   #  'accepted': n, 'rejected': n, 'open': n}
    @property
    def blocks_delivery(self): ...  # not present, or any finding open
    @property
    def exit_code(self): ...        # 2 when errors; 1 when open; else 0
    @property
    def review_line(self): ...      # the one REVIEW line, or ''
    def to_dict(self): ...          # {'schema': 1, 'version': __version__, ...}
```

**Free functions:**
- `load_review(path) -> (dict, [error])` — JSON only; never raises on a malformed file.
- `validate(doc) -> ([ReviewFinding], [error])` — enforces the enums; a legacy prose `resolution` is parsed by its leading token (`resolution.split(',')[0].split(':')[0].strip().casefold()`) and the whole original string is kept as `resolution_note` with `migrated=True`; a leading token outside `RESOLUTIONS` is an error, not a guess.
- `review_pairs_md(translations, segments, notes) -> str`
- `review_prompt_md(document, pairs_path) -> str`
- `termbase_rows(findings) -> ([(src, tgt)], [skipped_core])` — accepted **terminology** findings only; a finding without both `term` and `term_target` goes to `skipped`.
- `append_termbase(path, rows) -> ([added], [conflict])` — idempotent: a pair already present is not written twice; a source term already mapped to a *different* target is a conflict, returned and never written. Writes the two-column, `utf-8-sig`-readable shape `qa_check.load_glossary` parses; a term containing a comma quotes, as `csv.writer` does by default.
- `run_review(work, ingest=None, notes=None) -> ReviewVerdict` — reads only; writes `review_pairs.md`, `review_prompt.md` and `glossary.csv` under `work`; prints nothing, raises nothing, exits nothing.

- [ ] **Step 1: Write the failing tests**

Create `pdf-translate/tests/test_review.py` with these, red first:

`SchemaTests`
- `test_the_enum_resolutions_are_accepted_as_is`
- `test_a_legacy_prose_resolution_is_parsed_by_its_leading_token` — the four real shapes from `dev/jobs/fl150-ja-2026-09-17/review.json`: `'accepted, applied in v2 (2026-09-17)'`, `'rejected: both renderings are attested; …'`, `'rejected on measurement'`, `'accepted with a different fix'` → `accepted|rejected|rejected|accepted`, each `migrated=True`, each keeping the whole original in `resolution_note`.
- `test_a_leading_token_outside_the_enum_is_an_error_not_a_guess` — `'deferred to the client'` → one error, no finding invented.
- `test_an_unknown_category_is_an_error`
- `test_a_malformed_review_json_is_an_error_not_an_exception`
- `test_a_missing_reviewer_block_is_an_error`

`GeneratorTests`
- `test_review_pairs_lists_every_core_merge_override_and_notice` — against the real mapping: 247 cores, 13 merges, 5 overrides, 1 notice, and the identity table's five fields.
- `test_review_pairs_reproduces_the_mapping_key_verbatim` — `head of household` stays lowercase; findings key on this string, so a case-folded column would break `--ingest`.
- `test_review_pairs_states_page_numbers_are_one_based` — the mapping stores 0-based `page`; the generated file is 1-based and says so.
- `test_review_prompt_fills_every_identity_slot_from_notes` — no `{brace}` survives in the output.
- `test_review_prompt_asks_for_term_and_term_target`
- `test_review_prompt_is_the_reference_template_verbatim_otherwise` — diff against `references/review.md` §3 with the slots filled; any other divergence fails.

`TermbaseTests`
- `test_only_accepted_terminology_findings_reach_the_termbase` — an accepted *accuracy* finding and a rejected terminology finding are both absent.
- `test_a_terminology_finding_without_a_named_term_is_skipped_and_reported` — six of the FL-150's eleven, by the real file.
- `test_appending_the_same_pair_twice_writes_one_row`
- `test_a_source_term_remapped_to_a_different_target_is_a_conflict_not_a_second_row`
- `test_a_term_containing_a_comma_round_trips_through_load_glossary` — `married, filing separately` written by `append_termbase`, read back by `qa_check.load_glossary`.
- `test_the_written_file_is_readable_by_qa_check_glossary_findings` — the real enforcement path, end to end.

`Fl150FixtureTests` (the brief's §4 Proof, first half)
- `test_the_real_review_json_validates_with_migration` — all 31 findings parse; 11 accepted terminology; 25 accepted / 6 rejected by the file's own resolutions; zero errors.
- `test_the_real_job_produces_the_measured_termbase` — five named pairs added, six skipped for want of a term.

Run them. Expect every one to fail on `ModuleNotFoundError: pdf_translate.review`.

- [ ] **Step 2: Write `review.py`**

Minimal code to green. Notes that bite:

- `to_dict()` carries `{'schema': SCHEMA, 'version': __version__, …}` — copy `VerifyVerdict.to_dict`'s shape (`verify.py:322`), including the deferred `from . import __version__` inside the method to dodge the import cycle.
- Dataclasses are `frozen=True` with tuple fields, as `Finding`, `GateResult`, `VerifyVerdict` and `QAVerdict` all are.
- `review_pairs_md` reads `translations.json` for `translations`, `merges`, `overrides`, `notices` and `lang`, and `segments.json` for page attribution. **`overrides` are positioned multi-part placements** (`page`, `contains`, `parts` with `x`), not cores kept in the source language — render them as parts in x order on one line, and do not describe them as anything else.
- `notices[].text` uses `‖` as a line break. Render it as one; say so in the generated file.
- `append_termbase` opens with `newline=''` and `encoding='utf-8'`; `load_glossary` reads `utf-8-sig`, so a BOM written by anything else still parses — do not write one.
- `run_review` never creates `work`; a missing directory is an error in `errors`, not an exception.

Run the module's tests: expect green.

- [ ] **Step 3: Create the evidence doc**

`docs/reviews/2026-09-17-terminology-loop.md` — the compass from the brief §1, the three rulings and their costed alternatives (from `docs/design/32-terminology-loop/OpenQuestion.dc.html`), the R5 tension and what followed from it, and a `## Review` heading left empty for the whole-branch reviewer's verdict line.

- [ ] **Step 4: Commit** — `feat(pdf-translate): review.py — the reviser loop as a stage, schema-versioned, printing nothing (v57)`

---

### Task 2: the CLI — `pipeline.py review`, and the refusal in `finish`

**Files:**
- Modify: `pdf-translate/pdf_translate/pipeline.py`
- Modify: `pdf-translate/tests/test_review.py` (append `RefusalTests`)

**Interfaces consumed:** everything Task 1 produced. **This task adds every `print` in the feature.**

- [ ] **Step 1: Write the failing tests** (`RefusalTests`, red first)

- `test_finish_without_work_refuses_and_names_the_flag` — exit 2; the message names `--work`.
- `test_finish_refuses_when_review_json_is_absent` — exit 2; names the path, the one command that fixes it, and `--no-review`; never more than three lines before `elapsed`.
- `test_finish_refuses_while_any_finding_is_open` — exit 2; one `OPEN` line per open finding in `qa_check`'s exact column shape.
- `test_finish_passes_when_every_finding_is_resolved` — exit 0.
- `test_no_review_delivers_and_prints_one_review_line` — exit 0; exactly one line matching `^REVIEW no reviser: `.
- `test_finish_writes_review_state_json_on_every_run` — present on the refused run *and* the delivered run; `schema` and `version` keys present.
- `test_review_state_json_records_the_no_review_escape` — `no_review: true` and the REVIEW line inside the record, not only on stdout.
- `test_review_subcommand_generates_then_ingests` — the two runs of the canvas, exit 0 then exit 1 with two open findings.
- `test_console_parity_for_a_job_that_passes_no_new_flags` — `dev/probes/verdict_parity_runner.py` diffs empty.
- `test_the_new_commands_reach_real_stdout` — run `cmd_review` through `pipeline.main(['review', …])` with `redirect_stdout`, and assert the lines are actually there. This is the regression test for the one way the logger change fails silently: `log.info` with no handler attached produces nothing at all, and every other test in this task would still pass.
- `test_importing_the_package_configures_no_logging` — `import pdf_translate` attaches only the `NullHandler` and sets no level on the root logger; a library must never configure logging for its host.

- [ ] **Step 2: `cmd_review`**

```
review --work DIR [--ingest review.json] [--notes NOTES.md]
```

Emits through `log.info(...)`, in this order, one fact per line, `elapsed` last — matching every other command's voice (lowercase, no colour, no box drawing). With `_console()` attached in `main()` these are byte-identical to what a `print` would have written:

```
review: 247 cores, 13 merges, 5 overrides, 1 notice
review: identity from NOTES.md — en->ja, court form, です・ます register
review: wrote fl150-ja/review_pairs.md
review: wrote fl150-ja/review_prompt.md
review: no review.json yet. finish will refuse.
elapsed 0.31s
```

and on `--ingest`:

```
review: reviewer Claude Opus (model, not qualified in pair)
review: 31 finding(s) — 1 critical, 6 major, 24 minor
review: 25 accepted, 4 rejected, 2 open
OPEN  terminology   'head of household': 世帯主 → 特定世帯主 — US filing status is for the unmarried
OPEN  terminology   'Cash and checking accounts, savings, credit unio': 信用組合 → マネーマーケット
review: 11 accepted terminology finding(s) → fl150-ja/glossary.csv
review: 6 skipped — no term named; add "term" and "term_target"
review: 2 open finding(s). finish will refuse until each is accepted or rejected.
elapsed 0.09s
```

The finding line is `f"{sev:5} {kind:13} {core[:48]!r}: {detail}"` — `qa_check.main`'s format at `qa_check.py:386`, reused verbatim so a reader who knows one command can read the other. `OPEN ` is the severity column. A migrated resolution adds one line per finding: `review: migrated resolution 'accepted, applied in v2 (2026-09-17)' → accepted; prose kept in resolution_note`.

- [ ] **Step 3: the refusal in `cmd_finish`**

Signature becomes `finish ORIGINAL.pdf OUT.pdf FONT.ttf FINAL.pdf HTML --work DIR [--no-review]`. Parse `--work` and `--no-review` out of `argv` **before** the five positionals are taken, exactly as `cmd_rebuild` does at `pipeline.py:319`.

Order of operations: resolve the review state → refuse or emit the REVIEW line → `field_fonts` → `compare` → write `review_state.json` beside `FINAL.pdf` → `elapsed`. The record is written on the refused path too, before returning 2.

The three consoles are drawn in `docs/design/32-terminology-loop/FinishRefusal.dc.html`; reproduce them. A refusal names what is missing, the one command that fixes it, and the escape — and nothing else.

- [ ] **Step 4: `--glossary` joins `--work`**

In `cmd_qa`, join a bare `--glossary` value to `work` when `os.path.isfile(os.path.join(work, value))` and the bare path does not exist, mirroring how `--segments` is already joined. An explicit relative or absolute path that resolves is left alone. Add `test_a_bare_glossary_name_resolves_against_work`. This is the asymmetry named in the Global Constraints; fixing it here keeps the two-command story (`review --ingest` writes `glossary.csv` into `work`; `qa --work … --glossary glossary.csv` reads it back) true without a path dance.

- [ ] **Step 5: docstring** — the module docstring gains a `review` entry and the `finish` entry gains `--work` / `--no-review`, in the existing style.

- [ ] **Step 6: Commit** — `feat(pdf-translate): pipeline review; finish refuses without a resolved review.json (v57)`

---

### Task 3: the references — failure modes, terms of art, the amended review.md

**Files:**
- Create: `pdf-translate/references/terminology-failure-modes.md`
- Modify: `pdf-translate/references/review.md`
- Modify: `pdf-translate/SKILL.md`

- [ ] **Step 1: `terminology-failure-modes.md`**

The twin of `failure-modes.md`: opens with a contents line (house rule — every reference does), then five categories, each with its FL-150 instance and its rule. Categories, not page facts — they transfer to every pair. Content is settled in `docs/design/32-terminology-loop/TermsOfArt.dc.html`; copy the wording.

1. **Legal-status homonyms** — 世帯主 is the registered head of a 住民票 household, normally a married person; US head-of-household requires the filer to be unmarried. *Rule: a status the reader ticks about themselves is looked up in the target country's own law before it is translated.*
2. **Party-role words reused inside compounds** — 相手方 was already RESPONDENT, so 相手方の親 grew a possessive reading. *Rule: a term already bound to a party never appears inside a compound naming someone else.*
3. **Verbs of legal acts, chosen by object** — "executed" an order became 締結, a contract verb. *Rule: the verb follows what is being acted on.*
4. **Head nouns narrower than their own examples** — 光熱費 excludes the water and trash its own parenthetical lists. *Rule: a head noun is checked against the examples in its own parenthetical.*
5. **Label sets mixing patterns** — 月額／週額／時給 mixes two patterns; a set shares one. *Rule: labels offered as a choice are authored together and read as a column.*

- [ ] **Step 2: `review.md` §3 and §4**

§3: the prompt gains, after the "Do not rewrite anything you cannot justify" paragraph —

> For a terminology finding, also return `term` and `term_target`: the shortest source phrase that is wrong and the established rendering that replaces it, not the whole segment. A finding without them cannot enter a termbase.

and its opening line "fill the four identity facts first" is corrected — the template carries six braces before `{schema}`. Say **six**, and list them.

§4: `resolution` keeps the enum and gains `resolution_note` (string, the prose rationale — the rejections are the most valuable text in the file); terminology findings gain optional `term` and `term_target`. The closing sentence *"Nothing in the pipeline reads it — it is for the humans who accept the work"* is now false and must change: `pipeline.py review --ingest` reads it, `finish` refuses on it, and it is still for the humans who accept the work.

- [ ] **Step 3: `SKILL.md` step 1 — the terms-of-art table**

The identity record's "Four facts" becomes five; the new one is a **terms-of-art table** (term, established rendering, source) with one row for every status, role, benefit programme and verb of legal act on the page, written **before** authoring and read by the reviser. "No established rendering found" is a legitimate row and a flag. Add `references/terminology-failure-modes.md` to the "Read this now" sentence beside `failure-modes.md`, so step 1 names both and neither is optional prose.

- [ ] **Step 4: `SKILL.md` steps 5b and 8**

5b: one sentence that `glossary.csv` is now grown by `review --ingest` from accepted terminology findings, and that the skill still ships none.

8: the deliver list gains the review step ahead of the checklist — `review --work` before authoring is finished, the reviser, `--ingest`, and that `finish` refuses until every finding is resolved. The existing "Name a second reader for official work" paragraph stands unchanged; it is the reason this row exists.

- [ ] **Step 5: Commit** — `docs(pdf-translate): terminology-failure-modes reference; terms-of-art table in step 1; review.md schema and prompt`

---

### Task 4: the canary scores terminology

**Files:**
- Modify: `dev/canary/score.py`

Two numbers, fed by a job's `review.json`:

- **Accepted findings per 1,000 source words** — how much a reviser still has to fix. Should fall as the reference and the termbases grow.
- **Reviewer false-positive rate** — rejected ÷ total. On the FL-150: **6 of 31, 19%**. The loop measures the reviewer too, because the reviser was wrong twice in its own top seven. This is the first measurement, not a target.

- [ ] Red first: `test_the_axis_reproduces_the_fl150_measurement` against `dev/jobs/fl150-ja-2026-09-17/review.json` — 19%, and the per-1,000 figure computed from `translations.json`'s source words.
- [ ] A job with no `review.json` scores the axis as `None`, never 0 — an unmeasured job and a perfect one are not the same number.
- [ ] Commit — `feat(canary): terminology axis — accepted findings per 1,000 words, reviewer false-positive rate`

---

### Task 5: docs, version 57, CI

**Files:**
- Modify: `.github/workflows/tests.yml` (suite line gains ` tests.test_review`)
- Modify: version 56 → 57 in `pdf-translate/SKILL.md` (`version: "57"`, line 21), `.claude-plugin/plugin.json` (`57.0.0`, line 4), `pdf-translate/pyproject.toml` (`57.0.0`, line 7), `pdf-translate/pdf_translate/__init__.py` (`'57'`, line 13), `pdf-translate/tests/test_verify_report.py` (lockstep literal, line 648) — **red first** at `'57'` against the four sources.
- Modify: `pdf-translate/pdf_translate/__init__.py` — export `ReviewVerdict`, `run_review`; both into `__all__`, alphabetically.
- Modify: `pdf-translate/README.md` — the workflow list gains the review step.
- Modify: `pdf-translate/references/gates.md` — a short section saying the review loop is **not** a gate: it is a refusal in `finish`, it produces no `GateResult`, and `verify`'s twenty-one gates are unchanged. State it explicitly so no one looks for gate 22.
- Modify: `docs/DECISIONS.md` — one row: the three rulings with their costed alternatives, the R5 tension and the record that answers it, and the reversal conditions (a consumer that needs `finish` never to refuse; a reviser population whose false-positive rate makes the termbase worse than nothing).
- Modify: `docs/REQUESTS-from-product.md` — a row noting that `finish`'s refusal is a CLI-path behaviour, that R5 is honoured by the library path and the `review_state.json` record, and that neither withholds an output file that was built.
- Modify: `dev/goals/PROGRAM.md` — row 32's closing note with the measurement and the evidence path.
- Modify: `docs/reviews/2026-09-17-terminology-loop.md` — append `## Docs and version`.

Steps: the lockstep red then green; each edit at its anchor (grep first; report NEEDS_CONTEXT if an anchor is missing); the full suite once more; commit `docs(pdf-translate): review loop in SKILL.md, gates.md and README; DECISIONS row; row 32 closed; version 57`.

---

## After the tasks

1. **The brief's §4 Proof, run for real.** Re-run the FL-150 job from `dev/jobs/fl150-ja-2026-09-17/` (its README rebuilds in ten seconds): `finish` refuses before `review.json` exists, refuses again with a finding forced back to `open`, and passes once every finding is resolved. Then build a fresh mapping that reintroduces 世帯主 and confirm `qa_check --glossary` flags it from the `glossary.csv` this loop produced. Paste the three consoles into the evidence doc.
2. Whole-branch review on the most capable model (`scripts/review-package $(git merge-base main HEAD) HEAD`), Minor findings from the task reviews handed to it for triage. Not a rendering change: no Rule 1 verifier; the §4 Proof re-run is the independent pass.
3. The controller fills `## Review` in the evidence doc and reports to the operator. Push and PR are the operator's.

## Self-review

- **Spec coverage against the brief §2's six items.** (1) `review --work`, the two files, `--ingest` → Tasks 1–2. (2) `finish` refuses, `--no-review`, the one REVIEW line → Task 2, plus the `review_state.json` record the R5 section requires. (3) `terminology-failure-modes.md` and the step-1 terms-of-art table → Task 3. (4) the termbase, appended by `--ingest`, enforced by the existing `qa_check --glossary` → Tasks 1–2. (5) the canary axis → Task 4. (6) red-first tests for 1, 2 and 4, docs, version bump → Tasks 1, 2, 4, 5.
- **Spec coverage against §3's "not done when".** No model is fine-tuned and no glossary ships inside the skill (Global Constraints). The reviser never replaces human sign-off (`review.md` §2 untouched, Task 3 step 2). `finish` cannot pass an open finding without the REVIEW line in the delivery — `review_state.json` is written on every path, tested by `test_review_state_json_records_the_no_review_escape`. The terms-of-art table is a named slot in step 1, read by the reviser, not optional prose.
- **Type consistency.** `run_review(work, ingest=None, notes=None) -> ReviewVerdict` matches its two call sites (`cmd_review`, `cmd_finish`). `termbase_rows` returns `([(str, str)], [str])` and both callers unpack two. `append_termbase` returns `([added], [conflict])`. `ReviewVerdict.to_dict()` carries `schema` and `version` like `VerifyVerdict.to_dict()`. Every dataclass is `frozen=True` with tuple fields.
- **Nothing in `review.py` prints, logs or exits**; all console output is in `pipeline.py` (Task 2), through `log.info`. This is the E3 premise and the thing most likely to be got wrong by a lane working from Task 1 alone.
- **Forward compatibility with E3, checked.** This row writes one stage to the surface E3's design pass settled, so E3 inherits it rather than reworking it: the verdict is a frozen dataclass with tuple fields and a `to_dict()` carrying `schema` and `version`; the stage itself is silent and returns data; console output goes through the package logger; and `__init__.py` carries the `NullHandler` a library is supposed to attach. What this row deliberately does **not** do is convert `pipeline.py`'s other 31 `print` sites, touch any other stage, or add the eleven-CLI parity runner — all three are E3's, and doing them here would make this row unreviewable.
- **Placeholders:** none. Every console block in Task 2 is the literal expected output; the counts in it are the measured job's.
- **Known scope limit, to record in the evidence doc:** the termbase is per document class and language and is only as good as the reviser that filled it. A reviser with a high false-positive rate poisons the next job's `qa_check` with confident wrong terms — which is exactly why Task 4 measures the reviewer and why a finding without a named term is skipped rather than guessed.
