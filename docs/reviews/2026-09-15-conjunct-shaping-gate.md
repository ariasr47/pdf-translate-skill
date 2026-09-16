# Gate 18 — conjunct shaping: the probe table, the gate, and the red run

**Branch:** `feat/shaping-probe-gate` (stacked on PR #2 → PR #1 → `main`)
**Author of the code:** the session that wrote this file (Fable 5.1).
**Independent verification:** a separate pass on a different model, recorded
in `2026-09-15-conjunct-shaping-gate-verification.md` beside this file
(AGENTS.md Rule 1). Nothing below is a claim that pass has not re-run.

## The gap this closes

`docs/RESEARCH-AND-FINDINGS.md` §C1: Arabic and Devanagari were once drawn
without shaping. Gate 12 catches the Arabic case from the drawn letterforms.
For Devanagari the fix was "checked by eye", and `verify.py` said why no
gate existed: *the shaper writes glyph ids, so a broken conjunct and a
correct one look the same in the text layer.*

## The mechanism, measured

Render a probe string that contains a merging cluster twice off the SAME
face — glyph by glyph (`insert_text`, no shaping) and through the Story
engine (`insert_htmlbox`, HarfBuzz, the path retypeset uses) — and count
glyphs with `page.get_texttrace()`. Both arms assert which face drew the
run, read from the texttrace span, because `insert_text(fontfile=...)`
without `fontname=` silently falls back to Helvetica.

PyMuPDF 1.28.2 (repo venv) and 1.28.0 (`py -3`) agree on every row.
Faces: the nine `tools/fetch_test_fonts.py` fetches.

| script | probe | code points | naive | shaped | ratio | verdict |
|---|---|---:|---:|---:|---:|---|
| Devanagari | क्षत्रिय | 8 | 8 | **4** | 0.50 | **probe** (table row) |
| Devanagari | हिन्दी | 6 | 6 | 5 | 0.83 | tell present; not the row |
| Devanagari | कमल | 3 | 3 | 3 | 1.00 | correct, uninformative — never a probe |
| Bengali | ক্ষ | 3 | 3 | **1** | 0.33 | **probe** |
| Bengali | বাংলা | 5 | 5 | 5 | 1.00 | correct, uninformative |
| Tamil | க்ஷ | 3 | 3 | **1** | 0.33 | **probe** |
| Khmer | ខ្មែរ | 5 | 5 | **4** | 0.80 | **probe** (coeng ma) |
| Khmer | កា | 2 | 2 | 1 | 0.50 | vowel sign ligates; not the row |
| Myanmar | သင်္ဘော | 7 | 7 | **5** | 0.71 | **probe** (kinzi + stacked bha) |
| Myanmar | မန္တလေး | 7 | 7 | 6 | 0.86 | tell present; not the row |
| Myanmar | မြန်မာ | 6 | 6 | 6 | 1.00 | no stack — the earlier "undecided" word, uninformative |
| Thai | ป้า | 3 | 3 | 3 | 1.00 | blind |
| Thai | กำไร | 4 | 4 | 5 | 1.25 | **backwards** (sara am decomposes) |
| Hebrew | שָׁלוֹם | 7 | 7 | 7 | 1.00 | blind (niqqud) |
| Arabic | مكتبة | 5 | 5 | 8 | 1.60 | **backwards** — gate 12 owns Arabic |

Two findings that changed the brief's picture:

- **Khmer is not blind.** The 15 September brief listed it among the
  mark-stacking scripts in prose while its own table read Khmer coeng 0.80.
  The measurement wins: Khmer is a table row. `AGENTS.md` prose corrected,
  its measured table untouched; DECISIONS row added.
- **Myanmar has a probe.** The earlier test word had no stack. သင်္ဘော does,
  and reads 7 → 5.

Three design experiments (`scratch/design_experiments.py`, not committed):

| question | measured |
|---|---|
| what does retypeset embed? | the whole font program: 243,520 bytes in, 243,520 out, GSUB intact, 845 glyphs — so verify can extract the face and probe it |
| does a `prepare_font` subset still shape? | yes: 27 KB subset, GSUB kept, probe 8 → 4 |
| does deleting GSUB give the red case? | yes: 8 → 8, same face drawn (no fallback) |

## The gate

`pdf_translate/shaping_probe.py` — the table (`PROBES`), the blind list
(`BLIND_SCRIPTS`: Thai, Lao, Hebrew niqqud), the unmeasured list
(Gurmukhi … Tibetan), `probe_font()` / `probe_font_bytes()`, and the pure
`judge()`.

Two hooks, so the face is attested twice:

1. **`prepare_font`** adds the script's probe cluster to the subset charset
   (a dozen glyphs) and probes the subset it actually wrote. FAIL → exit 1.
   Blind scripts print REVIEW. Latin jobs print nothing.
2. **`verify`** (gate 18, always on) extracts every embedded font program on
   a page that draws Devanagari, Bengali, Tamil, Khmer or Myanmar and
   re-probes it, once per (script, face). No glyph loss → FAIL, exit 1,
   recorded in `VerifyVerdict.gates` as `conjunct-shaping`. A face without
   the probe glyphs → REVIEW "cannot attest" (the fix is named). Blind and
   unmeasured scripts → REVIEW, never PASS.

Tests: `tests/test_shaping_probe.py`, 19 tests, written before the code and
watched to fail (`FAILED (errors=1)` for the module, then `failures=7` for
the hooks). Full suite with the gate: 260 + 11 canary, OK, 0 skipped.

## The red run (real, documented CLI paths, repo venv)

Fixture: one 14 pt Latin line. Target: आपको शांति और शक्ति प्राप्त हो
(conjuncts क्ति, प्रा, प्त). `NotoSansDevanagari-NO-GSUB.ttf` is the fetched
Noto face with its GSUB table deleted by fontTools.

```
$ python scripts/pipeline.py init original.pdf --work job
strip: xfa_removed=False dead_buttons=0
1 segments, 1 unique strings to translate, 0 warnings -> segments.json / to_translate.json
exit=0

## RED — the face cannot shape (no GSUB)
$ python scripts/prepare_font.py NotoSansDevanagari-NO-GSUB.ttf job/translations.json job/font-sub.ttf --sample "आपको शांति"
FAIL conjunct shaping Devanagari: "क्षत्रिय" 8 -> 8 glyphs (NotoSansDevanagari-Regular); no conjunct formed: the Story engine drew 8 glyphs, glyph-by-glyph drew 8; the face has no usable GSUB for Devanagari
FAIL: job/font-sub.ttf does not shape the conjuncts this job draws; a page built with it shows consonant+halant where a conjunct belongs. Use a glyf TTF that carries the script's GSUB tables (references/fonts.md).
exit=1

# prepare_font refused but left job/font-sub.ttf on disk (as after a failed rasterization assert). Build with it anyway:
$ python scripts/pipeline.py rebuild --work job original.pdf out-nogsub.pdf --translations job/translations.json --fill-text "आपको" --min-ink 0.1
PASS field parity
SKIP fill round-trip (no fields)
PASS page 1 ink ratio: 0.92
PASS text layer is visible
PASS canonical text layer
FAIL conjunct shaping Devanagari: "क्षत्रिय" 8 -> 8 glyphs (NotoSansDevanagari-Regular); no conjunct formed: the Story engine drew 8 glyphs, glyph-by-glyph drew 8; the face has no usable GSUB for Devanagari [page 1] — every conjunct drawn with this face is broken; do not ship
PASS no untranslated running text
PASS authored translations present
PASS shaped-script targets carry /ActualText
… (every other gate PASS)
exit=1

## GREEN — the real Noto face
$ python scripts/prepare_font.py tests/fonts/NotoSansDevanagari-Regular.ttf job/translations.json job/font-sub.ttf --sample "आपको शांति"
PASS conjunct shaping Devanagari: "क्षत्रिय" 8 -> 4 glyphs (NotoSansDevanagari-Regular); ksha and tra conjuncts
OK: job/font-sub.ttf (40 KB, 134 chars, render check 432 px)
exit=0
$ python scripts/pipeline.py rebuild --work job original.pdf out-good.pdf --translations job/translations.json --fill-text "आपको" --min-ink 0.1
PASS conjunct shaping Devanagari: "क्षत्रिय" 8 -> 4 glyphs (NotoSansDevanagari-Regular); ksha and tra conjuncts [page 1]
PASS shaped-script targets carry /ActualText
… (every other gate PASS)
exit=0
```

Note what the red run shows about gate 17: `PASS shaped-script targets
carry /ActualText` is printed on the broken output too. Gate 17 proves the
run went through the Story engine; only gate 18 proves the face could
shape it. Both are needed.

## The visual pass (looked at, not inferred)

Both outputs rendered at 600 dpi, cropped to "और शक्ति प्राप्त हो":

- **GSUB-less:** क carries an explicit halant with त drawn separately, the
  i-matra of क्ति lands *after* क instead of hooking in front of the
  cluster, and र stands as a full letter after प् instead of the ra-vattu.
- **Real face:** क्त and प्त are conjuncts, the i-matra sits in front of
  क्त, and प्र shows the ra-vattu under प.

That is the difference the gate turns into an exit code.

## What this gate does not do

- Thai, Lao, Hebrew niqqud: no count tell (Thai even runs backwards). They
  print REVIEW and need a reference raster or a reader. Open problem, not
  a task.
- Gujarati, Gurmukhi, Oriya, Telugu, Kannada, Malayalam, Sinhala, Tibetan:
  routed through the Story engine, no face measured, REVIEW until a probe
  row is measured. Adding faces to the fetcher and rows to `PROBES` is the
  follow-up.
- It attests the face, not every cluster in the document. A face that
  passes its probe yet mis-draws some other cluster would slip through;
  the visual pass remains mandatory.

## Commits on the branch

```
8c81f8e docs(pdf-translate): gate 18 in gates.md, SKILL.md, fonts.md; version 49
d383743 feat(pdf-translate): gate 18, conjunct shaping attested on the embedded face
525d0c1 feat(pdf-translate): conjunct-shaping probe with a measured table
0266d30 docs: review PR #1 (canary delivery) and PR #2 (core-library packaging)
6d47f63 test(pdf-translate): fetch Thai, Khmer, Tamil, Bengali and Myanmar test faces
4440594 docs: adopt AGENTS.md, DECISIONS.md and the product request inbox
```
