# Review — PR #2 `feat/core-library-packaging` → `codex/explicit-canary-delivery`

**Reviewed:** 2026-09-15 · **Head:** `9970411` · **Base:** `26e1f25` (PR #1's head)
**Size:** 2 commits, 26 files, +6199 / −5536 · **CI:** 5/5 green (run 35021688588)
**Verdict:** the central claim — all eleven CLIs keep their names, flags,
documented stdout and exit codes — **holds on every axis I could measure**.
Mergeable after #1. One medium finding on the new library surface
(`VerifyVerdict.gates` is a partial list), one API wart, three nits.

The −5,536 lines are the eleven script bodies moving into
`pdf-translate/pdf_translate/`; nothing was dropped. Evidence below.

## Shape of the change

- `pdf_translate/` package: eleven modules, `__init__.py` re-exporting
  the stage functions plus additive `run_verify` / `run_qa` that return
  verdict objects without printing; `pyproject.toml` (setuptools, version
  48.0.0, deps pinned to the same bounds as `requirements.txt`).
- `scripts/*.py`: eleven identical 20-line wrappers. Each inserts the skill
  root on `sys.path`, and under `__main__` reconfigures stdout/stderr to
  UTF-8 (`errors="replace"`) and does `raise SystemExit(main())`. When
  *imported* instead, the wrapper replaces itself in `sys.modules` with the
  package module, so `sys.path.insert(0, 'scripts'); import verify` still
  yields the real implementation.
- `tests/test_import_surface.py`: 13 tests (import without side effects,
  verdict objects, CLI files exist, no-arg exit codes, cp1252 console).
- CI: the suite line gains `tests.test_import_surface`. `SKILL.md`
  unchanged; skill version stays 48.

## Per-module diff: old `scripts/X.py` (26e1f25) vs new `pdf_translate/X.py`

| module | diff | what changed |
|---|---|---|
| bilingual, compare, field_fonts, prepare_font, render_pages, retypeset, strip_text | **byte-identical** | moved only |
| extract_segments | −4 / +1 | `sys.path` hack → `from .strip_text import …` |
| pipeline | −10 / +9 | nine sibling imports → relative imports |
| qa_check | −5 / +31 | imports relative; `QAVerdict` dataclass + `run_qa()` appended; `qa_check()` / `main()` untouched |
| verify | −10 / +95 | imports relative; `GateResult` / `VerifyVerdict`; body renamed `_execute_verify` returning `(rc, gates)` with `record()` calls added beside existing prints; `verify()` keeps its exact signature and int return; `run_verify()` wraps with stdout redirected |

All eleven old scripts ended with `def main(argv=None)` … `raise
SystemExit(main())`; every new module still defines `main(argv=None)` and
no module uses `__file__` (so nothing depended on living in `scripts/`).

## CLI identity — what I ran

**28 invocations at base and head, from a neutral cwd, `PYTHONUTF8=1`,
repo venv (Python 3.14):** each of the 11 CLIs with no arguments and with
`--help`, plus `pipeline.py` with `init`, `rebuild`, `render`, `finish`,
`from-cores` and a bogus subcommand. Compared exit code, stdout bytes, and
the final stderr line (tracebacks differ only in file paths and line
numbers, as expected).

| Result | count |
|---|---|
| exit code identical | 28 / 28 |
| stdout byte-identical | 28 / 28 |
| last stderr line identical | 28 / 28 |

Exit codes observed: `bilingual`, `pipeline`, `qa_check` → 2 with usage;
the other eight → 1 with `IndexError` (pre-existing, disclosed in the PR
body); `compare --help` → 1 (opens `original.pdf`, pre-existing, disclosed).

**Real pipeline through the wrappers.** `dev/canary/score.py` imports
`verify`, `qa_check` and `extract_segments` via `scripts/` and runs the
whole gate set. On the frozen Spanish delivery
(`runs/fresh-canary-2026-09-05/job`) the head produced a report identical
to the base's (timings stripped): verify exit 0, 4/4 identifiers, 1 QA
warning, exit 0.

**Suites.** Base: 228 + 11 canary, OK. Head: `Ran 241 tests in 54.874s —
OK` (228 + 13 import-surface) + 11 canary, 0 skipped with the nine test
faces present. `git diff --check` clean. `pip show pdf-translate` confirms
the editable install (`pip install -e .`) works; `*.egg-info/` is ignored.

**Tests still hit the library, not the wrapper.** Verified
`import retypeset; retypeset.__file__` →
`pdf_translate/retypeset.py`, and `sys.modules['verify'] is
sys.modules['pdf_translate.verify']`. Monkeypatching in the 228 existing
tests therefore patches the real module.

**Does green CI cover the claim?** Partly. `test_import_surface` pins the
no-argument exit codes and the cp1252 behaviour for all eleven; the 228
pipeline tests and 11 canary tests exercise every stage's logic through
the wrappers. What CI does *not* do is compare CLI **stdout content**
before/after — my 28-run comparison did that by hand. A small golden test
for the three usage texts would make that repeatable (optional).

## Findings

**F1 — medium: `VerifyVerdict.gates` is a partial list.** `record()` is
called for field parity, `/Opt` parity, fill round-trip, extractable text,
ink ratio, visible text, canonical text, running leaks, empty targets,
placement, button captions, identifiers. It is **not** called for: unshaped
Arabic (gate 12), shaped marks (gate 17), caption width, override markers,
document metadata (and its REVIEW), scaled runs (REVIEW/SKIP), the two
leak REVIEW lines. A consumer reading `verdict.gates` to explain
`exit_code == 1` can see every listed gate PASS. Either record every gate,
or document `gates` as "the structural subset" until it is complete. The
CLI and `verify()`'s int return are unaffected, so this is a library-surface
issue, not a regression.

*Resolved the same day on `fix/verify-verdict-records-every-gate`: every
printed outcome now records under a name from `verify.GATE_NAMES`;
`tests.test_import_surface.VerdictCompletenessTests` counts printed gate
lines against recorded entries; `docs/DECISIONS.md` has the row; version
49 → 50.*

**F2 — low, API wart: submodule names are shadowed by function re-exports.**
`__init__.py` does `from .verify import verify` (and the same for
`retypeset`, `strip_text`, `qa_check`, `prepare_font`, `field_fonts`,
`render_pages`, `compare`, `extract_segments`), so `pdf_translate.verify`
is the *function*, and `import pdf_translate.verify as m` binds the
function too — I tripped on it. `from pdf_translate.verify import
needs_shaping` works because the import system reads `sys.modules`. Worth
one sentence in the package docstring; renaming the re-exports is the
consumer's call per the brief.

**F3 — low, disclosed: the only CLI behaviour change.** On a legacy
Windows console (cp1252) the wrappers now print non-encodable characters
as `?` instead of dying with `UnicodeEncodeError`; `qa_check.py` with no
arguments moves from exit 1 (crash) to exit 2 (usage) there. The PR body
says so; `test_import_surface` proves it; on UTF-8 consoles nothing
changes. Acceptable — it is a crash fix on a path SKILL.md documents.

**F4 — nit: the version lives in three files now** (`plugin.json`,
`SKILL.md`, `pyproject.toml`); the CI lockstep check covers two. Extend
the `package` job's Python snippet to read `pyproject.toml` as well.

**F5 — nit: `license = {text = "MIT"}`** is the deprecated table form in
current setuptools (≥ 77 warns; SPDX string `license = "MIT"` is the
replacement). Warning only today.

**F6 — nit: commit body vs title.** "No logic was added" is slightly
overstated: `GateResult` / `VerifyVerdict` / `record()` / `run_verify` /
`QAVerdict` / `run_qa` are new code paths (additive, silent, tested). The
brief asked for exactly that, so this is a wording note.

## Claims in the PR body, checked

- "CLI names, flags, stdout on the documented paths, and exit codes are
  unchanged" — measured, 28/28 (above).
- "228 → 241 tests OK; canary 11 OK" — reproduced.
- "`SKILL.md` is unchanged" — not in the file list; documented invocations
  still run (the 28 runs used them).
- "Nothing was taken from the product repo" — not verifiable from the diff
  alone; the seven byte-identical moves and the small, self-describing
  additions are consistent with the claim.
- "`requirements.txt` bounds were not raised" — unchanged; `pyproject.toml`
  mirrors them.

## Recommendation

Merge after #1 (operator's action). F1 is worth fixing before any consumer
relies on `run_verify().gates`; it can be a follow-up commit on this branch
or the next one. F2–F6 are nits.
