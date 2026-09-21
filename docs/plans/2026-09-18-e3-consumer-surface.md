# E3 — the consumer surface — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every stage is callable from Python without a CLI — explicit paths in, a schema-versioned result object out, a typed exception on refusal, nothing printed, nothing exited, no dependence on the working directory — while the eleven CLIs stay **byte-identical** and not one existing test moves. Version 57 → 58.

**Architecture:** The design pass is `docs/design/E3-consumer-surface/` (eight artboards; do not re-derive it). Its central finding: the stage functions cannot simply be silenced, because `tests/test_pipeline.py` holds 177 `redirect_stdout` blocks of which **128 wrap a library function directly** (`verify.verify(` 64, `retypeset.retypeset(` 55, `prepare_font.prepare_font(` 5, `field_fonts.field_fonts(` 2, `strip_text.strip_text(` 1, `pipeline.propose_merges(` 1) and only ~41 wrap a `main()`. So E3 **finishes a pattern the repository already has twice** — `verify`/`run_verify` and `qa_check`/`run_qa` — rather than inventing one: each stage gains a silent `run_*` twin returning a result and raising typed exceptions, while the bare name keeps its exact signature, its exact printed bytes and its exact return code.

**Tech stack:** Python 3.10+ / 3.14, `unittest`, stdlib `logging`, `dataclasses`, `contextlib`. No new dependencies. Not a rendering change: Rule 1 does not apply.

---

## Rulings this plan is built on

Settled by the operator on 2026-09-18 against `docs/design/E3-consumer-surface/DecideFirst.dc.html`. None is open.

1. **Row 32 ships first and builds to this surface.** `docs/plans/2026-09-17-terminology-loop.md` already carries the convention — `pipeline.py` gains `log` and `_console()`, `cmd_review`/`cmd_finish` emit through `log.info`, `__init__.py` attaches the package `NullHandler`, and `review.py` is silent and returns a verdict. **This plan therefore starts from a `main` that already has the logger foundation and `review.py` as its first compliant stage** (v57). If row 32 has not landed when this starts, Task 1 adds the foundation instead — and nothing else changes.
2. **`scale_report.json` breaks in E3.** Its bare-list top level becomes `{"schema": 1, "version": …, "runs": [...]}`. Cheapest now, before the product pins a version and builds goldens on the current shape.
3. **C7 is not in this epic.** Determinism moved to E8 on 2026-09-18, since E8's acceptance already read "the C7 determinism test gates" and the size is unknown until a probe runs. **Do not add a `timestamp=` parameter here**, and do not touch `apply_document_metadata`.

## What E3 is not

- Not C6 (hostile input — E7), not C8 (versions — E11), not C7 (determinism — E8).
- Not a rename. `strip_text`, `extract_segments`, `prepare_font`, `retypeset`, `field_fonts`, `verify`, `qa_check` keep their names, signatures and behaviour exactly. `tests/test_import_surface.py` pins them and 128 capture blocks call them.
- Not a re-levelling. Everything printed today logs at `INFO`. The console is the contract; changing what is said, or at what level, is a separate argument.

---

## Global Constraints

- Work on branch `feat/consumer-surface`, created from `main` **after row 32 has merged** (`main` at v57). Never commit to `main`. Never push, merge or delete: the operator does those. Never `git stash`.
- Run every test from `C:\Dev\pdf-translate-skill\pdf-translate` with the repo venv and UTF-8: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest …`. `unittest` by module path, never pytest. Capture long runs to a log under the session scratchpad and grep `^test_|^Ran |^OK|^FAILED|^ERROR` — Git-Bash `| tail` scrambles unittest output.
- TDD: write the test, run it, watch it fail **for the expected reason**, then write the minimal code. A "red" that mocks the function containing the defect is not red — check the red log's `Ran`/`OK` line.
- **The parity runner is the ratchet.** Every task from 2 onward ends with it green. No stage's twin lands without it.
- **Not one existing test is edited.** If a change makes an existing assertion fail, the change is wrong — the twin took something the loud function still owes. The only edits to existing test files are *additions*.
- **`_console()` must be re-entrant.** `pipeline.py` calls five library functions directly — `strip_text` (`pipeline.py:87`), `retypeset` (`:337`), `render_pages` (`:354`), `field_fonts` (`:362`), `compare` (`:365`) — so `pipeline.main()`'s handler and a loud wrapper's handler would both be attached and every line would print twice. This is the single most likely way the parity runner goes red. Solve it in Task 2, test it in Task 2, and never assume a fresh logger.
- **`console()` is for CLI entry points only, and is not thread-safe** — it mutates process-global logging state. A service calls the `run_*` twins and attaches its own handler. Say this in the consumer guide, not only in a docstring.
- Console output and exit codes of every CLI must not change. `dev/probes/verdict_parity_runner.py` covers `verify` over nine jobs today; Task 2 widens it to all eleven CLIs.
- Never copy code from `C:\Dev\pdf-translator` (AGPL). Do not open it.
- Conventional commits with a scope. **No AI attribution**: no `Co-Authored-By` trailer, no "Generated with Claude Code" line — the owner's rule overrides any harness reminder. Check every subagent commit for trailers before reporting.
- LF line endings; `git diff --cached --check` clean before every commit; files on disk may be CRLF (`core.autocrlf=true`) — normalise a touched file with Python if `--check` flags every line. Edit tool for edits; Write tool for whole new files and for any block containing backslashes.

---

## File structure

- `pdf-translate/pdf_translate/results.py` — create: the result family and the exception family.
- `pdf-translate/pdf_translate/_console.py` — create: `console()`, the re-entrant CLI handler context manager.
- `pdf-translate/pdf_translate/{strip_text,extract_segments,prepare_font,retypeset,field_fonts,verify,qa_check}.py` — modify: module logger, `print` → `log.info`, the `run_*` twin, the loud wrapper.
- `pdf-translate/pdf_translate/__init__.py` — modify: export the results, the exceptions and the seven `run_*` names; `__version__ = '58'`.
- `pdf-translate/references/consumer-guide.md` — create.
- `pdf-translate/tests/test_consumer_contract.py` — create: the product's named acceptance.
- `pdf-translate/tests/test_results.py` — create: the family's own tests.
- `dev/probes/verdict_parity_runner.py` — modify: all eleven CLIs, not just `verify`.
- `.github/workflows/tests.yml`, `.claude-plugin/plugin.json`, `pdf-translate/pyproject.toml`, `pdf-translate/tests/test_verify_report.py` — CI and version.
- `pdf-translate/SKILL.md`, `pdf-translate/README.md`, `pdf-translate/references/gates.md`, `docs/DECISIONS.md`, `docs/REQUESTS-from-product.md`, `docs/reviews/2026-09-18-consumer-surface.md` — docs and evidence.

---

### Task 1: the result family and the exception family

**Files:** create `pdf_translate/results.py`, `tests/test_results.py`, `docs/reviews/2026-09-18-consumer-surface.md`.

**Interfaces produced:**

```python
SCHEMA = 1

class PdfTranslateError(Exception):
    """Base. Never raised directly. Carries the console line and the exit
    code the loud wrapper must reproduce, so the CLI stays byte-identical."""
    console_line: str
    exit_code: int = 1

class WidgetTextError(PdfTranslateError): ...   # moves here; strip_text re-exports
class MappingError(PdfTranslateError): ...      # core unauthored / null target
class GlyphError(PdfTranslateError): ...        # page, char
class PlacementError(PdfTranslateError): ...    # page, key
class FontError(PdfTranslateError): ...         # face, reason

@dataclass(frozen=True)
class _Result:
    """Base: to_dict() carries schema and version, like VerifyVerdict."""
    def to_dict(self): ...

StripResult      # encryption, perms_removed, certified, xfa_removed, pages,
                 # dead_buttons, hidden, rewritten_captions,
                 # rewritten_widget_text, leftover_text, …
ExtractResult    # segments, warnings, cores, document, pages,
                 # unextractable_pages, invisible_text_pages, …paths
FontResult       # face, roles, glyphs_added, subset_bytes
RetypesetResult  # output, pages, placed, scaled (tuple), cancelled
FieldFontsResult # output, fields, face
```

- [ ] **Step 1: red.** `tests/test_results.py`:
  - `test_every_result_to_dict_carries_schema_and_version`
  - `test_results_are_frozen_and_use_tuples` — a list field would let a caller mutate a returned result.
  - `test_every_exception_carries_a_console_line_and_an_exit_code`
  - `test_widget_text_error_is_still_importable_from_strip_text` — the re-export, so nothing that catches it today breaks.
  - `test_exceptions_carry_structured_attributes` — `GlyphError(page=3, char='请').page == 3`, so a service renders the cause without parsing English.
- [ ] **Step 2: green.** Mirror `VerifyVerdict.to_dict()` (`verify.py:322`) including the deferred `from . import __version__` inside the method to dodge the import cycle. **`strip_text.WidgetTextError` keeps working by re-export, not by moving the name** — `from .results import WidgetTextError` at the top of `strip_text.py`.
- [ ] **Step 3:** create the evidence doc with the design finding, the three rulings, and an empty `## Review` for the whole-branch reviewer.
- [ ] **Step 4: commit** — `feat(pdf-translate): the result and exception families (v58)`

---

### Task 2: the logger foundation, one twin, and the widened parity runner

**Files:** create `pdf_translate/_console.py`; modify `verify.py`, `__init__.py`, `dev/probes/verdict_parity_runner.py`; add to `tests/test_import_surface.py`.

`verify` is the first twin because `run_verify` already exists: the work is to make it silent the right way and prove nothing moved.

- [ ] **Step 1: red.** Added to `tests/test_import_surface.py`:
  - `test_console_is_reentrant` — nested `with console(): with console(): log.info('x')` emits `x` **once**. This is the `pipeline.py` double-print, isolated.
  - `test_console_removes_its_handler_on_exit` — the package logger has no handlers of ours afterwards; a library that leaves one attached has configured logging for its host.
  - `test_run_verify_does_not_touch_sys_stdout` — swap `sys.stdout` for a sentinel object and assert `run_verify` never replaces it. Red today: `verify.py:2124` does exactly that.
  - `test_run_verify_is_silent_and_verify_is_loud` — exists in spirit already; assert both against the new mechanism.
  - `test_two_threads_running_run_verify_do_not_swallow_each_other` — one thread in `run_verify` while another prints; the other's output must survive. **Red today.** This is the C5 bug in a test.
- [ ] **Step 2: green.** `_console.py`:

```python
_depth = 0
_handler = None

@contextlib.contextmanager
def console():
    """Attach the one handler that reproduces today's console exactly.
    Re-entrant: nested uses share the outermost handler. CLI entry points
    only — it mutates process-global logging state and is not thread-safe."""
    global _depth, _handler
    pkg = logging.getLogger('pdf_translate')
    if _depth == 0:
        _handler = logging.StreamHandler(sys.stdout)
        _handler.setFormatter(logging.Formatter('%(message)s'))
        pkg.addHandler(_handler)
        pkg.setLevel(logging.INFO)
    _depth += 1
    try:
        yield
    finally:
        _depth -= 1
        if _depth == 0:
            pkg.removeHandler(_handler)
            _handler = None
```

  Then in `verify.py`: `log = logging.getLogger(__name__)`; its 70 `print(` sites become `log.info(...)`; `run_verify` **drops `redirect_stdout`** and the `io` import if now unused; `verify()` becomes `with console(): …`. `__init__.py` gains the `NullHandler` if row 32 has not already added it.
- [ ] **Step 3: widen the parity runner.** Today it runs `verify` over nine fixture jobs (`dev/probes/verdict_parity_runner.py`, 38 lines). Widen it to invoke each of the eleven `scripts/*.py` CLIs with a representative argv, capture stdout **and** the exit code, and print a stable, diffable block per invocation. Usage stays: run once per checkout, diff the two outputs. Record the pre-change baseline into the evidence doc **before** Step 2's code lands, so the diff has something to be equal to.
- [ ] **Step 4:** full suite. Expect green with **no test edited**. Parity diff empty.
- [ ] **Step 5: commit** — `feat(pdf-translate): re-entrant console handler; verify logs; parity runner covers eleven CLIs`

---

### Task 3: the remaining twins, one commit each

**Files:** `strip_text.py`, `extract_segments.py`, `prepare_font.py`, `retypeset.py`, `field_fonts.py`, `qa_check.py`.

Same shape each time, in this order — smallest surface first, `retypeset` last because it is the largest and Task 4 builds on it:

`strip_text` (2 prints, 1 capture block) → `field_fonts` (4, 2) → `qa_check` (3, 0 — `run_qa` exists; it needs only the envelope and the logger) → `prepare_font` (12, 5) → `extract_segments` (11, 0) → `retypeset` (32, 55).

For each stage:

- [ ] **Red:** `run_X` exists, is silent, returns the result type, and raises the typed exception where the loud one returns non-zero. Plus, for each: `test_X_console_is_unchanged` asserting the literal lines the loud function prints today.
- [ ] **Green:** module logger; `print` → `log.info`; extract the body into `run_X` returning a result and raising; the bare name becomes the loud wrapper (`with console(): try: … except PdfTranslateError as exc: log.info(exc.console_line); return exc.exit_code`).
- [ ] **Ratchet:** full suite + parity runner before every commit.
- [ ] **Commit** per stage — `feat(pdf-translate): run_<stage>, the silent twin`

**`extract_segments` has no capture blocks to protect**, and already returns its refusal reasons as data. It still gets `run_extract` — a consumer should not have to learn which one stage is different — but its loud wrapper is the thinnest of the seven, and the plan says so rather than leaving the asymmetry to be discovered.

---

### Task 4: progress, cancellation, and the two paths that collide

**Files:** `retypeset.py`, `tests/test_consumer_contract.py` (created here).

- [ ] **Step 1: red.**
  - `test_progress_is_called_once_per_unit_and_total_is_pages_plus_merges` — `retypeset` runs **two** loops (a per-page pass, then a per-merge-job pass). A counter of pages alone reaches 100% and keeps working.
  - `test_progress_done_is_monotonic_and_never_exceeds_total`
  - `test_a_cancel_between_units_writes_no_file_at_the_output_path` — the product's exact acceptance.
  - `test_a_cancelled_run_returns_cancelled_true_and_no_output`
  - `test_two_concurrent_jobs_both_verify_pass` — from a thread pool, per C5.
  - `test_two_concurrent_jobs_do_not_share_a_scale_report` — red today: a fixed name beside `out` (`retypeset.py:1379`).
  - `test_authored_html_resources_resolve_against_the_mapping_not_the_cwd` — red today: `pymupdf.Archive('.')` (`retypeset.py:862`).
- [ ] **Step 2: green.** `run_retypeset(stripped, segf, trf, out, *, progress=None, cancel=None, scale_report=None, resource_root=None)`. Cancel checked at the top of each unit in both loops; `RetypesetResult(cancelled=True, output=None)` returned before `ez_save` — which is the single save at `retypeset.py:1387`, so **no partial file is possible by construction** and no cleanup path is needed. `resource_root` defaults to the mapping's directory; `Archive` is built from it. `scale_report` defaults to `None` meaning *return the runs and write nothing*; the loud `retypeset()` passes today's path so its file and console are unchanged.
- [ ] **Step 3.** `shaping_probe.py:227` builds its own `Archive('.')` and `extract_segments.py:520` defaults `outdir='.'` — same class of defect, fixed the same way, with a test each.
- [ ] **Step 4: commit** — `feat(pdf-translate): progress, cancellation, explicit resource root and scale-report path (C4, C5)`

---

### Task 5: `scale_report.json` gains its envelope

**Files:** `retypeset.py`, `references/retypeset.md`, `tests/test_pipeline.py` (**additions only**).

Ruling 2. The file's top level goes from a bare list to `{"schema": 1, "version": "58", "runs": [ … ]}`, written the way `verify.write_report` writes (`verify.py:2181`): temp file beside the target, `os.replace`, stale removal on failure, a printed note and never a raise.

- [ ] Red: `test_scale_report_carries_schema_and_version`; `test_scale_report_is_written_whole_or_not_at_all`; `test_a_failed_scale_report_write_does_not_change_the_return_code`.
- [ ] Any existing test that reads `scale_report.json` as a list is **the one place** this plan edits an existing assertion. Grep for it first and list what you find in the commit message; if the count is larger than a handful, stop and report — that would mean the format has more consumers than the ruling assumed.
- [ ] Commit — `feat(pdf-translate): scale_report.json is schema-versioned and written atomically (C3)`

---

### Task 6: the consumer guide

**Files:** create `references/consumer-guide.md`; modify `SKILL.md`, `README.md`.

Shape is settled on `docs/design/E3-consumer-surface/ConsumerGuide.dc.html`. Sections: before you start · the six calls · what each returns · the files on disk and which call wrote them · refusals · progress and cancellation · threads · what this library never does.

- [ ] Opens with a contents line (house rule). Every code block runs as written against the corpus fixture — **run them**.
- [ ] The three "before you start" items **point, they do not re-derive**: `lang` is BCP 47 with the "not a display name" example (already in `references/translations-format.md`), the two reference faces and what the Han-forms gate does without them (already in `references/fonts.md`), and no network.
- [ ] States plainly that the `run_*` twins are the thread-safe surface and the bare names are the older, printing shape; that `console()` is not thread-safe and a service attaches its own handler.
- [ ] `SKILL.md` and `README.md` gain one pointer each. No new gate is described: `references/gates.md` gains a line saying E3 added none.
- [ ] Commit — `docs(pdf-translate): references/consumer-guide.md — one document, end to end, from Python`

---

### Task 7: the contract test, docs, version 58, CI

**Files:** `tests/test_consumer_contract.py`, `.github/workflows/tests.yml`, the four version sites plus the lockstep literal, `docs/DECISIONS.md`, `docs/REQUESTS-from-product.md`, the evidence doc.

The product named this acceptance; reproduce it literally:

- [ ] One document through every stage **as function calls**, with stdout captured and asserted **empty**.
- [ ] Two concurrent jobs, both verify PASS.
- [ ] A cancel between pages leaving no file.
- [ ] The eleven CLIs byte-identical (the parity runner, run in CI).
- [ ] `sha256` determinism and the fixed-timestamp option are **not here** — ruling 3, they are E8's. Say so in the test module's docstring so nobody adds them back.
- [ ] Version 57 → 58 in `SKILL.md` (`version: "58"`), `.claude-plugin/plugin.json`, `pyproject.toml`, `__init__.py`, and the lockstep literal in `tests/test_verify_report.py` — red first.
- [ ] `docs/DECISIONS.md`: one row — the silent-twin design, why silencing was rejected (128 library-level capture blocks), the `scale_report` break, C7's move, and the reversal conditions (a consumer that needs one entry point per stage; a measured cost to carrying two).
- [ ] `docs/REQUESTS-from-product.md`: C1, C3, C4, C5, C10 move to **done** with the version; correct C3's stale "printed, not returned" note.
- [ ] Commit — `docs(pdf-translate): consumer contract test, guide and DECISIONS row; version 58`

---

## After the tasks

1. **The acceptance, run for real.** The parity runner over all eleven CLIs, diffed against a baseline taken from `main` before the branch. Paste both halves' hashes into the evidence doc.
2. Whole-branch review on the most capable model (`scripts/review-package $(git merge-base main HEAD) HEAD`), Minor findings from the task reviews handed to it for triage. Not a rendering change: no Rule 1 verifier; the parity diff is the independent check.
3. The controller fills `## Review` in the evidence doc and reports. Push and PR are the operator's.

## Self-review

- **Coverage against C1–C10.** C1 → Tasks 1–3 (callable, silent, typed refusals) and Task 4 (`resource_root`, the last cwd dependency). C2 → untouched, already holds. C3 → Task 1 (result envelopes) and Task 5 (`scale_report`). C4 → Task 4. C5 → Task 2's thread test and Task 4's concurrency tests. C6 → E7, not here. C7 → E8, not here, deliberately. C8 → E11, not here. C9 → untouched, already holds. C10 → Tasks 2–3, all 172 print sites including `pipeline.py`'s 31.
- **The one risk this plan takes:** two entry points per stage, forever. The alternative — silencing the existing functions — breaks ~200 assertions and every caller written against today's shape. Recorded in DECISIONS with its reversal condition.
- **The one thing most likely to go wrong:** the `console()` double-attach through `pipeline.py`'s five direct library calls. It has its own red test in Task 2, before any stage but `verify` is converted.
- **Type consistency.** Every `run_X` returns its own frozen result with `to_dict()` carrying `schema` and `version`. Every loud `X` returns `int` exactly as today. Every exception carries `console_line` and `exit_code`, which is the whole mechanism keeping the CLIs byte-identical.
- **Placeholders:** none. Every task names its red tests; Task 3 names the six stages, their print counts and their capture-block counts so a lane knows what it must not break.
