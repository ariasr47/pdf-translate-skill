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
| `docs/RESEARCH-AND-FINDINGS.md` | The September 2026 audit, the research behind it, and every verified defect with status. |
| `docs/REVIEW-2026-09-02.md` | The 2 September deep review: verdict, fresh research, and the two-lane backlog. |
| `docs/audit-2026-09-01.html`, `docs/checklist.html` | The audit page (a dated snapshot) and the living tracker (self-contained). |

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

Installing the plugin copies files and runs nothing, so it succeeds on a
machine with no Python. The first command is where that shows up: every CLI
checks for `pymupdf`, `pikepdf` and `fonttools` first and, if any are
missing, names them all and exits 2 without a traceback.

Nothing tells you when a new version exists. Auto-update is off by default
for a marketplace like this one, and no notification is sent when the
repository publishes. To pick up a later version, run
`/plugin marketplace update pdf-translate-skill`, then
`/plugin update pdf-translate`. The plugin's version is `metadata.version`
as `N.0.0`, and `/plugin list` shows which one is installed. CI validates
both manifests and fails if the two versions disagree.

## Run the tests

From `pdf-translate/` (use `py -3` on Windows if `python` is the Store alias):

```bash
python -m pip install -r requirements.txt
python tools/fetch_test_fonts.py     # optional, stops the shaping tests skipping
python -m unittest tests.test_pipeline tests.test_corpus_verdicts
```

The suite — constructed PDFs driving the shipped scripts; the current count
is in the CI log and in `dev/goals/HANDOVER.md` — runs in about 25 seconds
locally and 40 on CI, with **no skips** once the fonts are there.
The Arabic, Hebrew and Devanagari tests need faces with real shaping
tables: `tools/fetch_test_fonts.py` downloads four OFL Noto faces into
`tests/fonts/` (never committed), and each test asks for a font covering
the characters it needs — no single Noto face carries both Arabic and
Hebrew, which is why these tests used to run only on macOS and Windows.
Without the fetch they fall back to system fonts and skip where there are
none. GitHub Actions runs the whole thing on Linux and Windows, Python
3.14.

## The skill's own metadata

`SKILL.md` frontmatter carries `license: MIT`, a `compatibility:` line
(Python 3.14+, the three libraries, an image-viewing harness, network
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

A consumer should not read that number to decide what it can do. Ask the
engine instead: `pdf_translate.MAPPING_FORMATS` is a tuple of the mapping
formats the installed build can read — `legacy` always, and `typography-1`
where the source's serif/sans class and within-line bold/italic are preserved
(`pdf-translate/references/typography.md`).

## Licence

MIT — see `LICENSE`. The corpus PDFs and eval fixtures are generated; no
fonts are redistributed here.
