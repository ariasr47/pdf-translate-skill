# pdf-translate (provider-neutral)

A skill that translates a born-digital PDF from any language to any language
while keeping the visual layout pixel-faithful and every fillable form field
working: same field names, types and positions. Strip-and-retypeset at the
content-stream level, plain Python (PyMuPDF, pikepdf, fontTools), no vendor
SDK; any person or model authors the translation mapping.

## Layout

| Path | What |
|---|---|
| `pdf-translate/` | The skill: `SKILL.md`, ten scripts, references, corpus, tests. Start with `pdf-translate/SKILL.md`. |
| `pdf-translate/goals/` | The improvement program: one gate per sitting, closed briefs, handover for a cold session. |
| `docs/RESEARCH-AND-FINDINGS.md` | The September 2026 audit, the research behind it, every verified defect with status, and what closing gates 13–16 taught us. |
| `docs/audit-2026-09-01.html`, `docs/checklist.html` | The interactive audit page and the living tracker (self-contained). |

Job artifacts (`work/`, `runs/`, session exports, bakeoff outputs, the FL-150
sample PDFs) are ignored on purpose; they are large and not the product.

## Run the tests

From `pdf-translate/` (use `py -3` on Windows if `python` is the Store alias):

```bash
python -m unittest tests.test_pipeline tests.test_corpus_verdicts
```

84 tests on constructed PDFs drive the shipped scripts. Arabic and
Devanagari tests use system fonts (Arial, Nirmala UI) and skip where absent.

## Versioning

`pdf-translate/SKILL.md` carries `metadata.version`: the number of the last
closed program gate (see `pdf-translate/goals/PROGRAM.md`). Bump it when a
gate closes and re-sync any installed copy of the skill.
