# Brief: gate 20 `han-forms` — a Japanese target draws Han through Japanese forms (v53)

Date: 2026-09-16. Measured on `feat/kinsoku-gate` (PR #6) with the fetched Noto Sans JP / SC
variable faces, PyMuPDF 1.28.2, fontTools 4.64. Probe: `dev/probes/han_forms_probe.py`.
Scoped by `docs/reviews/2026-09-16-cjk-request-assessment.md` §3 item 3 (the product's 2b).

## 1. The problem, in one paragraph

Han unification gives 直 骨 海 one code point each, but a Japanese reader sees the Chinese
shape at once. This skill never selects a face — the caller supplies one — so nothing today
checks that a `lang: ja` delivery was drawn with a Japanese face, or a `zh-Hans` one with a
Chinese face. The gate must judge the delivered document, not a synthetic render, and must say
"cannot attest" rather than guess.

## 2. Measured — do not re-derive, do not alter

Diff ratio = pixels that are ink in one render and not the other, over the union of ink, at 4×
zoom, 48 pt, grey; 0.000 means identical rasters.

| measurement | 直 | 骨 | 海 | 東 (control: same in both) |
|---|---|---|---|---|
| Noto JP vs Noto SC, both at the default instance (Thin) | 0.507 | 0.217 | 0.364 | 0.000 |
| own face vs itself | 0.000 | 0.000 | 0.000 | 0.000 |
| Noto JP wght 400 vs Noto JP wght 100 (weight only) | 0.523 | 0.508 | 0.553 | 0.541 |
| Noto JP 400 vs Noto SC 400 (region only) | 0.454 | 0.171 | 0.212 | 0.000 |
| Noto JP 400 vs Noto SC 100 (both) | 0.651 | 0.548 | 0.607 | 0.541 |

**A real delivery** (build → extract → strip → `prepare_font --instance wght=400` → `retypeset`
with the JP subset, 20 KB, "Noto Sans JP Regular"):

| judged how | vs JP 400 | vs SC 400 |
|---|---|---|
| A. the embedded font program re-rendered (`doc.extract_font`, the way gate 18 re-probes) | 0.000 / 0.000 / 0.000 / 0.000 | 0.454 / 0.171 / 0.212 / 0.000 |
| B. each character clipped from the delivered page vs a control drawn at its origin and size | 0.000 / 0.000 / 0.000 / 0.000 | 0.445 / 0.189 / 0.242 / 0.000 |

**Other families** at the same geometry, against the Noto references (Thin): Yu Gothic (JP)
0.56–0.63 vs JP and 0.59–0.67 vs SC; Microsoft YaHei (SC) 0.71–0.82 vs JP and 0.69–0.80 vs SC.
Both are far from both references; the nearer one wins by 0.02–0.04, which is noise.

**Not drawn:** a `prepare_font` subset for a target with no probe character does not carry 直
(measured) — exactly gate 18's situation before it taught `prepare_font` to add its probe cluster.

**Cost:** instancing a reference at a weight with fontTools: JP 4.3 s, SC 7.7 s on this machine.

## 3. What the measurements decide

1. **The tell is real and exact within one family.** Own face 0.000 on every probe; the other
   region 0.17–0.51 at equal weight; 東 stays 0.000 as a negative control. Three probes with
   two independent regional differences (骨 is the weakest at 0.17) — require at least two of
   the three to separate.
2. **Weight is as large a difference as region.** JP 400 vs JP 100 reads 0.51–0.55, the same
   order as JP vs SC. References must be instanced at the delivered face's weight
   (`OS/2.usWeightClass` of the embedded program; the subset here says Regular = 400), or the
   comparison is meaningless. Instanced references are cached on disk keyed by (face, weight).
3. **Judge the face, not the page.** A (re-render the embedded program) and B (clip from the
   page) both give 0.000 / >0.17 — the product's warning that a clip is the only honest witness
   does not hold here, because MuPDF re-renders the embedded outlines identically. A needs no
   probe character in the document text and covers Story-engine merges the same as TextWriter
   lines; B only works where a control can be drawn with the same engine at the same origin,
   which is not knowable for a merge. Choose A, exactly gate 18's pattern; keep B as the
   probe's cross-check.
4. **The probes must be in the subset.** `prepare_font` adds 直 骨 海 東 to every CJK subset
   (as it adds gate 18's cluster); a face without them is REVIEW "cannot attest", never PASS.
5. **A non-Noto family cannot be judged.** Neither reference comes near 0.000; the gate says
   REVIEW "no reference of this family", never picks the nearer one.
6. **Which convention a `lang` wants.** `ja` → Noto Sans JP; `zh`, `zh-Hans`, `zh-CN`, `zh-SG` →
   Noto Sans SC; `zh-Hant`, `zh-TW`, `zh-HK` → Noto Sans TC and `ko` → Noto Sans KR, both
   REVIEW "no reference fetched" until a face is added to the fetcher and measured the same way
   (the product sells neither). No `lang` (neither `--translations` nor `/Lang`) → REVIEW.

## 4. Design

Gate 20 `han-forms`, always on, prints only when a page draws CJK text.

- `shaping_probe` (or a sibling module `han_forms.py`) gains `HAN_PROBES = '直骨海東'`,
  `CONVENTION_FOR_LANG`, `reference_face(convention, weight, fonts_dir)` (instance and cache),
  `judge_face(program, convention, fonts_dir) -> ProbeResult` with status PASS / REVIEW / FAIL
  and a line like `PASS han-forms: Noto Sans JP Regular draws Japanese forms (直 0.000 vs JP,
  0.454 vs SC) [page 1]`.
- `verify`: for each page whose text is CJK, each embedded face with a program (the gate-18
  loop), once per (face, convention): **PASS** when own-convention ratio ≤ 0.02 and the other
  ≥ 0.10 on at least two of 直 骨 海; **FAIL** when the other convention's reference reads ≤ 0.02
  and own ≥ 0.10 on at least two — the red case, a Japanese job set with the SC face; **REVIEW**
  otherwise, with the reason (no `lang`; convention has no reference; probes not in the subset;
  no reference of this family; reference faces directory missing). One `Finding` per judged
  face: `where` = the face's PostScript name (or the script / `lang` when unjudgeable), `text` =
  the ratio line or the reason. Exit code 1 only on FAIL.
- Reference faces: `tests/fonts/` by default (the fetcher's JP and SC), overridable with
  `--reference-fonts DIR` (CLI) / `reference_fonts=` (library) — the product ships its own
  copies. Instanced references are cached beside them (`<face>-<wght>.ttf`), never committed.
- `prepare_font`: adds `HAN_PROBES` to the subset when the job's charset contains CJK, and
  probes the subset it wrote against the job's `lang` when references are present (fails early
  with the same wording as verify's FAIL).
- `references/gates.md` "As a library": the consumer eliminates this REVIEW by passing `lang`,
  building faces with `prepare_font`, using Noto Sans JP / SC, and shipping the reference faces.

**Rule 1 applies:** `prepare_font` changes what is embedded (four more glyphs in every CJK
subset). An independent pass on another model re-runs the probe table above, the red (a `ja`
job set with the SC subset FAILs; the SC job with the JP subset FAILs) and the green (each with
its own face PASSes), and looks at 600 dpi renders of 直 from both deliveries.

**Acceptance (Rule 2).**
1. `tests/test_han_forms.py`, written first and watched to fail: the reference table above
   reproduced within 0.02; a `ja` delivery built through the pipeline with the JP subset → gate
   `han-forms` PASS with one finding naming the face; the same with the SC subset → FAIL; a `ja`
   delivery whose subset lacks the probes (built before this change, or with `prepare_font`
   patched) → REVIEW "cannot attest"; no `lang` → REVIEW; a delivery in Yu Gothic → REVIEW "no
   reference of this family" (skipped off Windows); Noto JP wght 700 subset → PASS (references
   instanced at 700, not at 400).
2. Console parity: non-CJK jobs byte-identical to `main` (`dev/probes/verdict_parity_runner.py`).
3. `FindingsInvariantTests` still holds (every FAIL/REVIEW carries a finding).
4. Version 53 in four sources plus the lockstep literal; gates.md row and table row; SKILL.md
   bullet; DECISIONS row with the table above; evidence doc with the verifier's report.

Effort: one to two days plus the Rule 1 verifier. Depends on PR #6 (the faces).

## 5. Not doing, on purpose

- No "nearest reference wins": a non-Noto family is REVIEW.
- No page clipping as the primary witness (B): exact only for TextWriter lines.
- No Noto Sans TC / KR until the product targets a language that needs them.
