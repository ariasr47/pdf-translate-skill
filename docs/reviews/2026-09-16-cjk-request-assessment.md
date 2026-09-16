# Assessment: the product's CJK request (faces, Han forms, kinsoku, missing glyphs)

Date: 2026-09-16. Checked read-only against `main` at `c28ada9` (skill v51), PyMuPDF 1.28.2,
fontTools 4.64.0, Windows 11. The product repo was not opened; its "Decision #4" and
"OPEN_THREADS §19.2" are quoted from the request and could not be verified here.

The request arrived as a paste that begins at "Why this, now." Its own closing section refers to
a **section 1 — "a live correctness bug in an interface the product is about to consume"** —
that is not in the paste. Nothing below assesses it.

## Verdict, item by item

| item | request | what is true on `main` | verdict |
|---|---|---|---|
| 2a | Add Noto Sans JP and SC to `tools/fetch_test_fonts.py` | Nine faces, none CJK. Both google/fonts URLs answer 200 (JP 9,589,900 bytes, SC 17,772,300 bytes, OFL.txt present); the fetcher's TrueType magic check accepts a variable TTF. | **Do it.** Small. CI font cache key bumps (`noto-fonts-v2` → v3), +27 MB. |
| — | "NO CJK test can run at all" | CJK tests run today on MuPDF's bundled Droid Sans Fallback (`tests/test_pipeline.py` `cjk_font_file`, `build_ja_source_pdf`; `tests/test_verify_report.py` `_spaceless_job` via `fontname='japan'`). What cannot run is a **language-specific** CJK test. | Overstated; the conclusion (2a first) still holds. |
| 2b | "A Japanese target draws Han through the Japanese face" | The skill never selects a face. `retypeset` draws with the caller's `fonts['regular']`/`bold` (retypeset.py:748–755); `references/fonts.md:14–26` names Noto Sans JP/SC/TC/KR per language. Nothing checks that the face matches `lang`, at prepare time or in the delivered PDF. `/Lang` is written from `translations.json` `lang` (retypeset.py:354–371) and reads back (`doc.language`). | **Reframe:** not "face selection" but a **verify gate on the delivered document** plus a `prepare_font` check. The product's render-compare design is sound with the caveats in §3. Medium; Rule 1 applies. |
| 2c | Implement kinsoku | The Story engine already does it: 158 lines drawn at six widths, **0** begin with a prohibited character, **0** end with an opener, **0** run past the box; a naive breaker on the same face and widths gives 38 and 8. Per character, **91/91** JLREQ line-start members (cl-02..cl-11, half-width forms included) and **15/15** line-end members (cl-01) are protected. Mechanism: MuPDF `source/html/html-parse.c` classifies with `ucdn_get_resolved_linebreak_class` and a UAX #14 pair table. | **No engine work.** What is missing is a gate that measures the lines actually drawn (the one path that can violate is the author splitting a target across source lines) and a DECISIONS row recording the measurement. Small. |
| 2d | Missing glyph → placeholder in the selected face, reported, never borrowed | Stricter today: `retypeset` refuses the job — `FAIL: N character(s) the chosen font cannot draw … U+XXXX`, exit non-zero, nothing saved (retypeset.py:1291–1306; `test_cjk_target_in_a_latin_font_fails_and_saves_nothing`). There is no second CJK face to borrow from; MuPDF's mid-string fallback is pre-empted by the refusal. Measured: Noto Sans JP 2.04 (17,936 glyphs) has 直骨海東 and **lacks 东**; Microsoft YaHei has it. | **Already satisfied, more strictly.** Add the precondition test once 2a lands; do not build placeholder rendering unless the product rules that a degraded delivery beats a refusal — that is a policy change. |
| 3 | Task F after 2 | As the brief says. | Agree. |
| 4 | Park C, D, E with a reversal condition | Brief already says "ask before E" and "park D without demand". C is half a day and its measurement exists (`dev/probes/mark_layout_tell.py`). | Agree on D and E. C is the operator's call: park it for product priority, or keep it for the standalone skill. |
| — | Obstacle-bounded placement: not asked for | Nothing above touches placement. | Agree. |

## 1. Measured — do not re-derive

Commands ran from the repo root with the venv interpreter and `PYTHONUTF8=1`.

**Kinsoku on the lines the Story engine draws** — `dev/probes/cjk_kinsoku_probe.py`
(face: Noto Sans JP 2.04, the Windows copy; line breaking is the engine's, not the face's):

```
1. Story engine, paragraph at 6 widths: 158 lines drawn; 0 begin with a prohibited character;
   0 end with an opener; 0 run past the box
2. naive greedy breaker, same face and widths: 148 lines; 38 begin with a prohibited character;
   8 end with an opener
3. per character (Story engine): every class protected —
   cl-02 14/14 (+ half-width 1/1), cl-03 4/4, cl-04 6/6, cl-05 3/3, cl-06 2/2 (+1/1),
   cl-07 2/2 (+1/1), cl-09 6/6, cl-10 1/1 (+ half-width ｰ 1/1), cl-11 12/12 + 12/12 (+ half-width 9/9);
   cl-01 14/14 (+ half-width ｢ 1/1)
kinsoku violations by the Story engine: 0
```

The engine pulls the break earlier (oidashi); it never hangs punctuation past the box, so a
paragraph rect stays a geometric guarantee. The sets were transcribed from JIS X 4051 / W3C JLREQ
Appendix A and the half-width block; the probe is the only place they live.

**Where this skill breaks lines.** Merges → `insert_htmlbox` (kinsoku holds, above). Single-line
segments → `TextWriter`, never broken (shrink instead; `scaled-runs` REVIEW). Shaped single lines →
Story engine, one line. A multi-line source paragraph **not** declared a merge → the author splits
the target across the source's lines (SKILL.md:290–293 warns against exactly this). That last path
is the only one that can start a line with 。 or ー, and it is invisible to the engine.

**Faces.** cmap: Noto Sans JP 2.04 — 直 骨 海 東 present, 东 (U+4E1C) absent; Microsoft YaHei 6.31 —
all five present; Yu Gothic 1.95 — 东 absent; bundled Droid Sans Fallback (50,483 glyphs) — 东 and
直 present. GSUB language systems: Noto Sans JP declares `hani:JAN`; YaHei `hani:ZHP/ZHS`. **Not
measured:** the shape difference between Noto Sans JP and Noto Sans SC for 直 骨 海 — no SC face on
this machine; it needs 2a.

**Missing glyph today.** `retypeset.check_glyphs` collects every character the chosen face lacks
before anything is drawn; `glyph_misses` prints the FAIL block and the job exits non-zero with no
output file. The Latin-font test asserts `U+3053` in the log and that the output does not exist.

## 2. Corrections to the request

- "NO CJK test can run at all" → CJK tests run on the bundled face; language-specific ones cannot.
- "no kinsoku" → the engine's paragraphs already obey it, measured. The skill has no kinsoku *set*
  to "remove a member from"; the red case for the gate is a delivered page whose author-split lines
  violate the rule, beside a Story-laid page that does not.
- "no Japanese-vs-Chinese face selection" → the skill selects no face at all; the gap is that
  nothing verifies the caller's face against `lang`.
- 2d's behaviour is a *loosening* of what ships: refusal, not placeholder. Say so before anyone
  builds it.

## 3. Recommended shape and order

0. **Section 1.** Cannot be assessed until the operator supplies it. If it is a defect in this
   repo's library surface, it goes first, as the request says.
1. **2a** — two faces in the fetcher, cache key v3, `tests/fonts/README` line. No version bump.
2. **Kinsoku gate (2c′)** — a new gate on the delivered PDF: for every page whose text is CJK,
   read the drawn lines (`get_text('dict')`), FAIL a line that begins with a JLREQ line-start
   member or ends with a line-end member, `Finding(page, 'line', text[:n])`. Red first: a
   constructed page with author-split lines; green: the same paragraph as a merge. DECISIONS
   row for the measurement above; one SKILL.md sentence on line-splitting. Not a rendering
   change, so no Rule 1 pass — the probe is the evidence. Version 52. Half a day.
3. **Han-forms gate (2b′)** — reads `lang` (`--translations`, else `/Lang`); extracts each embedded
   face the way gate 18 does (`conjunct_shaping_report`, `doc.extract_font`); renders 直 骨 海 off
   it and off the two reference faces at the same geometry; PASS when the clip matches its own
   language's control at ratio 0.0 and differs from the other; REVIEW when the probe characters
   are not drawn, when no reference face is available, or when neither control matches (a
   non-Noto family — the compare is exact only within one design family). `prepare_font` gets
   the same check at build time so the caller learns early. Rule 1 applies: a verifier on another
   model re-runs the red (a Japanese job set with the SC face) and green runs and looks at 600 dpi
   renders. The product must ship the two reference faces to get PASS in production. Version 53.
   One to two days plus the verifier. This is a new gate line and finding — additive to schema 1.
4. **2d′** — one test after 2a: assert 东 absent from the JP face and present in the SC face
   (precondition), then that a Japanese job containing 东 is refused with `U+4E1C` in the log and
   no output. One hour. No placeholder rendering.
5. **Task F** as the brief describes it.
6. **Park C, D, E** in the brief under `PARKED` markers with the reversal condition "the product
   adds a target language in this script." Keep `dev/probes/mark_layout_tell.py` and its DECISIONS
   rows; they are the restore path.

Budget: Sonnet lanes for 1, 2, 4, 5; the Rule 1 verifier for 3 on Opus or Fable.

## 4. Not doing, on purpose

- No kinsoku implementation in `retypeset`: the engine's is standard (UAX #14) and measured.
- No borrowing from a second CJK face, and no placeholder glyphs, without an explicit ruling.
- No obstacle-bounded placement, and nothing that reads the product repo.
