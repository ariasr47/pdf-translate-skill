# pdf-translate — instructions for any agent, any provider

Read this file, then `dev/STATUS.md` (what is open and what comes next),
then `pdf-translate/SKILL.md` if you will run the pipeline. The reasons
behind every standing rule are in `dev/DECISIONS.md`; the queue with its
closed bars is `dev/goals/PROGRAM.md`.

## What this is

A skill that translates a born-digital PDF from any language to any
language with the layout pixel-faithful and every fillable form field
working: same names, types, positions. Strip-and-retypeset at the
content-stream level, plain Python (PyMuPDF, pikepdf, fontTools), no
vendor SDK. Any person or model authors `translations.json`; the scripts
never call an LLM. When the job is impossible the scripts exit non-zero
and say why: scans and OCR layers are refused, not translated. Priority
when requirements conflict: structure > layout > natural translation in
the document's register > everything else. It installs as a Claude Code
plugin from this repository (`README.md`) or is copied as the
`pdf-translate/` directory by anyone.

## Layout

| Path | Role |
|---|---|
| `pdf-translate/` | The skill: `SKILL.md`, eleven scripts, eight references, corpus, tests, evals. The only directory that ships. |
| `AGENTS.md`, `CLAUDE.md` | This file, and Claude Code's one-line import of it. |
| `dev/STATUS.md` | Current state only: version, open and blocked rows, the next sitting. Rewritten at the end of every sitting. |
| `dev/DECISIONS.md` | Append-only ledger of decisions with their reasons, and the table of locked behaviours with the row that locked each. |
| `dev/goals/` | `PROGRAM.md` (the loop and the queue) and one brief per row with its closing note; `HANDOVER.md` is superseded and kept as history. |
| `dev/canary/` | Is a model fit to author the mapping: protocol, fixture generator, scorer, dated run records. |
| `dev/wild/` | Seventeen public PDFs, re-fetched from `SOURCES.md` and never committed, and the probe over them. |
| `docs/` | Dated deep reviews (`REVIEW-*.md`, `RESEARCH-AND-FINDINGS.md`) and two HTML snapshots. |
| `.claude-plugin/` | Plugin and marketplace manifests; CI fails if `plugin.json` and `metadata.version` disagree. |

`work/`, `runs/`, fetched fonts, generated fixtures and the wild PDFs are
gitignored on purpose.

## Environment

- **macOS:** `pdf-translate/.venv/bin/python` (3.14). Bare `python3` is
  Apple's 3.9 with no dependencies and fails at import; Homebrew's 3.11
  has none either. Never `pip install` into either of them.
- **Windows:** `pdf-translate\.venv\Scripts\python.exe`, created with
  `py -3 -m venv` (bare `python` is the Store alias).
- **CI:** Linux and Windows, Python 3.10 and 3.13 (`.github/workflows/tests.yml`).
- Set `PYTHONUTF8=1`; Windows needs it and it is harmless elsewhere. The
  test fonts are fetched once, over the network.

From `pdf-translate/`, with that interpreter:

```bash
python -m pip install -r requirements.txt
python tools/fetch_test_fonts.py           # or the shaping tests skip
python -m unittest tests.test_pipeline tests.test_corpus_verdicts
```

It must finish with no skips. The count is whatever it prints; no document
states it, and the badge in `README.md` is CI (D-26).

## How a sitting works

One row per sitting, taken from `dev/STATUS.md`, with the closed bar from
its brief; stop when the bar is green. Rows come from a measurement (a
canary run, the wild corpus, a review's instrument), never from invention.
A canary is a different day from any gate.

```
construct ONE tiny PDF that shows the defect
  → drive the shipped scripts by import, not a copy
  → gates PASS and output wrong: the gate is the bug (and the reverse)
  → lock with an in-repo test; corpus verdicts unchanged
  → full unittest + corpus; if strip or extract changed, dev/wild/probe.py
    against dev/wild/results.json, zero differences
  → if the shipped skill changed: bump metadata.version in SKILL.md and
    plugin.json together, in the same commit
  → rewrite dev/STATUS.md; append to dev/DECISIONS.md if a decision was made
  → one commit per row; never push, merge, rebase or delete without asking
  → STOP
```

## Standing rules (the why, with dates and sources, is `dev/DECISIONS.md`)

- Strip-and-retypeset; never white boxes, regeneration or redaction
  annotations. Field names, types and rects stay identical; an added
  widget is a regression (D-01, D-02).
- Provider-neutral: no vendor SDK, no per-language branch, no winner model
  named anywhere in the skill (D-03, D-08).
- No shipped glossary and no semantic term checker; `glossary.csv` is a
  per-job input (D-07, D-11).
- Never implement OCR: the refusal is the product (D-05).
- The visual pass is part of the workflow and is never scored by machine (D-04).
- Fixtures are constructed PDFs; FL-150 is a canary, never proof (D-09).
- Geometry proposes, the author decides: nothing merges or realigns itself (D-12).
- `SKILL.md` body under 500 lines; dev material stays out of `pdf-translate/` (D-15, D-20).
- Supersede, never rewrite: a closed brief, a review or a ledger entry gets
  a banner or a status, not an edit (D-26).
