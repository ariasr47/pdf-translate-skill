# pdf-translate (provider-neutral)

[![tests](https://github.com/ariasr47/pdf-translate-skill/actions/workflows/tests.yml/badge.svg)](https://github.com/ariasr47/pdf-translate-skill/actions/workflows/tests.yml)

A skill that translates a born-digital PDF from any language to any language
while keeping the visual layout pixel-faithful and every fillable form field
working: same field names, types and positions. Strip-and-retypeset at the
content-stream level, plain Python (PyMuPDF, pikepdf, fontTools), no vendor
SDK; any person or model authors the translation mapping.

## Layout

| Path | What |
|---|---|
| `pdf-translate/` | **The skill**: `SKILL.md`, eleven scripts, references, corpus, tests, evals. Start with `pdf-translate/SKILL.md`. Installed as a plugin from the repository (below), or copied as a directory by any agent or person. |
| `.claude-plugin/` | The plugin and marketplace manifests that make the repository installable with `/plugin marketplace add`. The skill needs nothing in them. |
| `dev/goals/` | The improvement program: one gate per sitting, closed briefs, handover for a cold session. |
| `dev/*.html`, `dev/*_SESSION_PROMPT.md` | Explainers and session prompts. Development material — deliberately outside the skill. |
| [Current backlog](dev/goals/PROGRAM.md#public-readiness-backlog) | Current library/skill follow-ups and completion checks; [smallest-items shortlist](docs/PUBLIC-READINESS-QUICK-WINS-2026-09-19.md) is a dated reading aid. |
| [19 September readiness audit](docs/reviews/2026-09-19-public-readiness.md) | Dated evidence for the shared engine and installable skill, with measured limits and open findings. |
| `docs/RESEARCH-AND-FINDINGS.md`, `docs/REVIEW-2026-09-02.md` | Earlier research, defect history and the 2 September review; consult the current backlog for status. |
| `docs/audit-2026-09-01.html`, `docs/checklist.html` | Historical audit/checklist snapshots; current status lives in the backlog above. |

Job artifacts (`work/`, `runs/`, session exports, bakeoff outputs, the FL-150
sample PDFs) are ignored on purpose; they are large and not the product. So
are the fetched test fonts and the generated eval fixtures.

## Install

As a Claude Code plugin, straight from the repository (a private repository
works wherever `git` has GitHub credentials):

```
/plugin marketplace add ariasr47/pdf-translate-skill
/plugin install pdf-translate@pdf-translate-skill
```

Later versions: `/plugin marketplace update pdf-translate-skill`, then
`/plugin update pdf-translate`. The plugin's version is `metadata.version`
as `N.0.0`, and `/plugin list` shows which one is installed. The CI workflow
invokes plugin validation and checks that the plugin, skill, Python package
metadata and runtime versions agree. Explicit validation of both manifests is
tracked under A21 in the [current backlog](dev/goals/PROGRAM.md#public-readiness-backlog).

Installing the plugin installs the skill, not its Python dependencies. The
pipeline needs `pymupdf`, `pikepdf` and `fonttools` in whichever Python the
agent runs; the tested version ranges are in
[requirements.txt](pdf-translate/requirements.txt). Install them before the
first job, into that interpreter:

```bash
python -m pip install pymupdf pikepdf fonttools
```

The skill states the same requirement in its own **Requirements** section, so
an agent that reads `SKILL.md` will ask for these if they are missing.

## Run the tests

From `pdf-translate/` in a repository checkout, use the same Python environment
for installation and tests. On Windows, use your virtual environment's Python
or `py -3` if `python` resolves to the Store alias.

```bash
python -m pip install -r requirements.txt
python tools/fetch_test_fonts.py
python tools/fetch_test_fonts.py --check
python -m unittest discover -s tests -t . -v
```

This discovers the complete library test suite, rather than only the pipeline
and corpus modules. The fetcher configures **11 Noto font files**, including
script-specific shaping faces and Japanese/Simplified Chinese references, in
`tests/fonts/` (never committed). Missing fonts can cause skips; `--check`
checks presence only, not the font bytes or whether every test will pass.

Dependency bounds are declared in [requirements.txt](pdf-translate/requirements.txt)
and [pyproject.toml](pdf-translate/pyproject.toml); proving the supported lower
bounds remains A05 in the backlog. Use the requirements file rather than an
unbounded package list.

The [19 September 2026 audit](docs/reviews/2026-09-19-public-readiness.md#tests-ci-security-tooling-and-evidence-limits)
records a Windows/Python 3.14 full run in **202.730 seconds**, with no skips,
at v58. That is a dated measurement, not a runtime promise for other versions
or machines. The workflow configures Linux and Windows with Python 3.10 and
3.13; this configuration alone does not establish a passing hosted run.

## The skill's own metadata

`SKILL.md` frontmatter carries `license: MIT`, a `compatibility:` line
(Python 3.10+, the three libraries, an image-viewing harness, network
preferred for fonts and issuer lookups) and `metadata.version`. That YAML
block is optional metadata for systems that auto-load skills; the document
below it is self-contained and works as plain instructions for any agent or
person with Python.

## Versioning

`pdf-translate/SKILL.md` carries `metadata.version`: a monotonic integer,
bumped whenever the shipped scripts or the workflow change. It began as the
number of the last closed program gate and kept counting past 17 as the
audit roadmap closed, so it is no longer a row number — just an ordering.
Re-sync any installed copy when it moves; a copy showing an older number is
running old scripts.

## Licence

MIT — see `LICENSE`. The corpus PDFs and eval fixtures are generated; no
fonts are redistributed here.
