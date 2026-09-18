# FL-150 → 日本語 — the reviewed job of 2026-09-17 (skill v56)

The first real Japanese job on the current skill, kept as the seed of the
Japanese corpus (E11) and of a court-form termbase (row 32). The source PDF
is not committed, following `dev/wild/SOURCES.md`; fetch it and rebuild.

## Files

- `translations.json` — the reviewed mapping (247 cores, 13 merges, 5 overrides, 1 notice), v2 wording
- `widget_text.json` — the 118 tooltips
- `review.json` — the second-reader review (Opus, MQM) with every resolution; the human page-1 read is recorded in `summary.human_review`
- `NOTES.md` — identity record, disclosures, gates, reviewer checklist
- `build_translations.py` — regenerates `translations.json` and fills `widget_text.json` from `segments.json`; run it from this folder after extract

## Rebuild (about ten seconds)

```bash
# 1. the original (Rev. September 1, 2024)
curl -L -o original.pdf https://courts.ca.gov/sites/default/files/courts/default/2024-11/fl150.pdf
# the copy used on 2026-09-17 had sha256 as recorded at the end of this file

# 2. from the skill directory, with its venv
python scripts/pipeline.py init original.pdf --work .
python build_translations.py
python scripts/strip_text.py original.pdf stripped.pdf --widget-text widget_text.json --hide-buttons Print_bt,Save_bt,Reset_bt,T23
python scripts/prepare_font.py tests/fonts/NotoSansJP-VF.ttf translations.json font-regular.ttf --instance wght=400 --sample 収入・支出申告書 --reference-fonts tests/fonts
python scripts/prepare_font.py tests/fonts/NotoSansJP-VF.ttf translations.json font-bold.ttf --instance wght=700 --sample 収入・支出申告書 --reference-fonts tests/fonts
python scripts/pipeline.py rebuild --work . original.pdf out.pdf --fill-text "山田太郎 123" --source-words-from segments.json --translations translations.json --allow "Form Adopted for Mandatory Use,Judicial Council of California,Question 1—Other Jobs,Question 10g,Schedule C,September Family Code" --reference-fonts tests/fonts
python scripts/field_fonts.py out.pdf font-regular.ttf.instanced.ttf final.pdf
python scripts/compare.py original.pdf final.pdf comparison.html --labels "English (original)|日本語（翻訳・参考訳）" --lang ja
```

Expected: verify exit 0, 266/266 fields, kinsoku 322 lines, han-forms
PASS, 16 scaled runs all ≥ 0.88, `qa_check` 0 errors.

## What this job is evidence for

- `docs/DECISIONS.md` row 2026-09-17 (three gate gaps, v56)
- `dev/goals/32-terminology-loop.md` (the review loop, P0)
- the two terms no gate can see: 世帯主 → 特定世帯主, 相手方の親 → 他方の親

Source sha256 (2026-09-17): 46ca00246ae0f26ad893ce3ded2bd502fd6df299258b02070395cc597a3f68b4
