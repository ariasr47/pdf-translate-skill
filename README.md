# pdf-translate (provider-neutral)

A skill that translates a born-digital PDF from any language to any language
while keeping the visual layout pixel-faithful and every fillable form field
working: same field names, types and positions. Strip-and-retypeset at the
content-stream level, plain Python (PyMuPDF, pikepdf, fontTools), no vendor
SDK; any person or model authors the translation mapping.

## Layout

| Path | What |
|---|---|
| `pdf-translate/` | **The skill**, and the only directory you install: `SKILL.md`, eleven scripts, references, corpus, tests, evals. Start with `pdf-translate/SKILL.md`. |
| `dev/goals/` | The improvement program: one gate per sitting, closed briefs, handover for a cold session. |
| `dev/*.html`, `dev/*_SESSION_PROMPT.md` | Explainers and session prompts. Development material — deliberately outside the skill. |
| `docs/RESEARCH-AND-FINDINGS.md` | The September 2026 audit, the research behind it, and every verified defect with status. |
| `docs/audit-2026-09-01.html`, `docs/checklist.html` | The interactive audit page and the living tracker (self-contained). |

Job artifacts (`work/`, `runs/`, session exports, bakeoff outputs, the FL-150
sample PDFs) are ignored on purpose; they are large and not the product. So
are the fetched test fonts and the generated eval fixtures.

## Run the tests

From `pdf-translate/` (use `py -3` on Windows if `python` is the Store alias):

```bash
python -m pip install -r requirements.txt
python tools/fetch_test_fonts.py     # optional, stops the shaping tests skipping
python -m unittest tests.test_pipeline tests.test_corpus_verdicts
```

154 tests on constructed PDFs drive the shipped scripts, in about 25
seconds. The Arabic and Devanagari tests need a font with real shaping
tables: `tools/fetch_test_fonts.py` downloads three OFL Noto faces into
`tests/fonts/` (never committed), and the tests prefer those over whatever
the host ships. Without them they fall back to system fonts and skip where
there are none. GitHub Actions runs the whole thing on Linux and Windows,
Python 3.10 and 3.13.

## The skill's own metadata

`SKILL.md` frontmatter carries `license: MIT`, a `compatibility:` line
(Python 3.10+, the three libraries, an image-viewing harness, network
preferred for fonts and issuer lookups) and `metadata.version`. That YAML
block is optional metadata for systems that auto-load skills; the document
below it is self-contained and works as plain instructions for any agent or
person with Python.

## Versioning

`pdf-translate/SKILL.md` carries `metadata.version`: the number of the last
closed program row (see `dev/goals/PROGRAM.md`). Bump it when a row closes
and re-sync any installed copy of the skill; a copy showing an older number
is running old scripts.

## Licence

MIT — see `LICENSE`. The corpus PDFs and eval fixtures are generated; no
fonts are redistributed here.
