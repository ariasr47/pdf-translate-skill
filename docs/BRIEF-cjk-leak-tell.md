# Brief: the CJK leak tell — task F, measured first (v55)

Date: 2026-09-16. Measured on `feat/cjk-leak-tell` (stacked on `feat/han-forms-gate`, PR #8) with
the fetched Noto Sans JP / SC variable faces, PyMuPDF 1.28.2. Probe: `dev/probes/cjk_leak_tell_probe.py`
(log excerpt below). Scoped by `docs/BRIEF-unattended-delivery.md` Task F and the product's work order
E2 ("task F, the spaceless leak scan, measure first").

## 1. The problem, in one paragraph

When source and output share the spaceless CJK family (ja → zh-Hans, zh → ja) the leak scan prints one
REVIEW — "cannot tell them apart" — and gates nothing. Task F proposed a rule: a source segment's text
found verbatim in the output while its mapped target differs is a leak. Measuring it first showed the
rule is blind to the leak that actually ships: `retypeset` already refuses a segment the mapping omits,
so the leak that reaches a delivered document is an **echo** — the translator returns the source as the
target, and the mapping says target == source, exactly as it does for a number or a name. The rule that
sees an echo is a script tell: characters that cannot belong to the target language.

## 2. Measured — do not re-derive, do not alter

**Tell sets.** For a target convention (from the mapping's `lang`, `han_forms.convention_for_lang`):

| target | a character that cannot belong to it |
|---|---|
| ja (JP) | a Han character not encodable in cp932 (JIS X 0208 + Microsoft extensions) |
| zh-Hans (SC) | any kana; a Han character not encodable in GB 2312 |
| zh-Hant (TC) | any kana; a Han character not encodable in Big5 |

Encoding sanity, single characters: 请 书 东 门 GB 2312 only; 気 図 桜 cp932 only; 国 会 学 in both
(shinjitai = simplified — never a tell); 東 請 寫 cp932 + Big5 (a tell for zh-Hans only); 髙 﨑 cp932
(extensions — never a tell for ja); 镕 in none (a rare name character: a tell for every target).

**Section 1 — tells per text, NFKC-folded.** A text of the target's own language must show 0.

| text | letters | kana | Han | target ja | target zh-Hans | target zh-Hant |
|---|---|---|---|---|---|---|
| ja form paragraph 1 | 72 | 39 | 33 | **0** | 49 | 39 |
| ja form paragraph 2 | 83 | 44 | 39 | **0** | 56 | 51 |
| ja kinsoku paragraph (test_cjk) | 40 | 33 | 7 | **0** | 35 | 34 |
| ja kanji-only line (東京都千代田区霞が関… 確定申告書) | 24 | 1 | 23 | **0** | 6 (が庁書東確関) | 7 (が区国庁税関) |
| ja `corpus/ja_source.pdf`, all pages | 27 | 10 | 17 | **0** | 13 | 10 |
| zh-Hans form paragraph 1 | 51 | 0 | 51 | 9 (处您栏确签请须) | **0** | 10 |
| zh-Hans form paragraph 2 | 48 | 0 | 48 | 16 | **0** | 17 |
| zh-Hans form paragraph 3 | 38 | 0 | 38 | 12 | **0** | 14 |
| zh-Hans shared-form sentence (日本国东京都 2026年3月31日 山田太郎 电话 …) | 15 | 0 | 15 | 3 (东电话) | **0** | 4 (东国电话) |
| zh-Hant form sentence | 38 | 0 | 38 | **1** (您) | 11 | **0** |
| mixed: zh-Hans with a Japanese name in kana (やまだ たろう) | 17 | 6 | 11 | 1 | 6 (the name) | 7 |

Zero false tells on every text in its own language, the corpus's real Japanese document included.
The one weak direction: a Traditional Chinese text shows a single tell for a Japanese target — JIS
X 0208 carries most traditional forms (請 寫 欄 準 確 簽 處) — so a zh-Hant echo inside a Japanese
delivery is nearly invisible to the repertoire tell.

**Section 2 — a real ja → zh-Hans delivery** (build → extract → strip → `prepare_font` SC wght 400 →
`retypeset`, `lang: zh-Hans`, five segments: two translated, one echoed, two legitimately equal —
`2026年3月31日`, `山田太郎`):

| rule | echoed segment (指定された欄に氏名と住所を記入してください。) | 2026年3月31日 | 山田太郎 | translated segments |
|---|---|---|---|---|
| V — source verbatim in output while target differs | — (target == source: not a candidate) | — | — | — |
| S — tells for a zh-Hans target, raw | **LEAK**, 14 tells in 22 letters | LEAK (年 = U+F98E) | LEAK (郎 = U+F92C) | — |
| S — tells, NFKC-folded | **LEAK**, 14 tells | — | — | — |
| verify today | `REVIEW leak scan: source and output share the spaceless CJK family` — one line, no finding | | | |

Rule V finds nothing, by construction. Rule S raw finds the echo and two false leaks: the source PDF's
ToUnicode drifts (the variable font's cmap maps the compatibility ideographs U+F98E 年 and U+F92C 郎 to
the same glyphs as U+5E74 / U+90CE and MuPDF's reverse mapping picks them — audit finding H4); the
mapping is authored from `segments.json`, so the drift reaches the output through an authored target,
which the canonical-text gate rightly accepts. NFKC folds both back; folded, rule S finds exactly the
echo. (The probe's fixture also FAILs the ink-ratio gate at 26.7 — a 12 pt Thin source against a
Regular output; a fixture artefact, not a finding.)

## 3. What the measurements decide

1. **Rule S, not rule V.** The verbatim rule cannot see the leak that ships; the script tell sees it
   with zero false tells on eleven own-language texts. Rule V is not built.
2. **Three tell sets, by target convention**, from the mapping's `lang` (`han_forms.convention_for_lang`;
   no `lang` → the old REVIEW stays, as it does today). Repertoires by encoding (cp932, GB 2312, Big5)
   are the proxy: no data files, no OpenCC-style tables.
3. **NFKC before the tell.** Compatibility ideographs from source drift must fold, or a legitimately
   equal date and name are leaks.
4. **Severity by tells per drawn line, not by contiguous runs** — kana interleave with Han (された欄に
   …してください: runs of 3, 1, 1, 1, 6 in a 14-tell line). Six or more tells in a line FAIL, one to five
   REVIEW, mirroring the existing scan's "six characters of a spaceless script FAIL; shorter leftovers
   REVIEW": an echoed sentence carries 9–56; a kana name (やまだ たろう, 6) FAILs and is allowlisted
   with `--allow`, as a proper noun is in the Latin scan; a rare name character outside every
   repertoire (镕) is one REVIEW. Kept runs (`skip`, `allow_translate`) and the original's `/Title` are
   excluded, as the Latin scan excludes them.
5. **The source's convention decides whether the pair can be judged.** The same tells applied to the
   source text name its language (the convention with 0 tells; ambiguous → cannot tell). Measured
   strong pairs: JP → SC, JP → TC (kana), SC → JP (9–16 per paragraph), SC → TC and TC → SC (10–17),
   TC → SC. **TC → JP is weak** (1 tell in 38 letters) and stays REVIEW "cannot tell" — the product
   sells no zh-Hant target or source, so nothing it does is affected.
6. Not a rendering change: Rule 1 does not apply. Sonnet lane; review on another model.

## 4. Design

Gate 21 `leak-cjk`, printed only when source and output share the spaceless CJK family
(`same_spaceless`) **and** the mapping's `lang` names a convention with a measured tell set **and** the
source's convention makes a strong pair.

- `pdf_translate/cjk_tell.py` (new, no printing): `TELLS = {'JP': …, 'SC': …, 'TC': …}` as predicates
  built from the encodings; `tells_in(text, convention) -> list[str]` (NFKC first); `convention_of(text)
  -> code | None` (the one convention with zero tells over the letters, else None);
  `STRONG_PAIRS = {('JP','SC'), ('JP','TC'), ('SC','JP'), ('SC','TC'), ('TC','SC')}`;
  `LINE_FAIL = 6`.
- `verify._execute_verify`, at the `same_spaceless` branch: with a convention for the mapping's `lang`
  and `convention_of(o_text)` forming a strong pair, scan every drawn line of every output page
  (`page.get_text('dict')` lines, joined spans, NFKC), skipping lines that are kept runs or the
  original's `/Title`; one `Finding(page, 'line', text)` per line with tells, its message `N tell(s):
  <the tell characters>`; status FAIL if any line has ≥ `LINE_FAIL` tells, REVIEW if any has 1–5, PASS
  otherwise. Console: `FAIL leak scan (CJK tell): N line(s) carry characters that cannot belong to a
  <Simplified Chinese> target:` + the lines with their tells, or `REVIEW …`, or `PASS leak scan (CJK
  tell): M line(s) hold only characters a <Simplified Chinese> target can carry`. The old
  `REVIEW leak scan: source and output share the spaceless …` line and its `leak-scan` REVIEW record
  are printed only when the tell cannot run (no `lang`, unknown source convention, a weak pair), with
  the reason appended.
- `--allow WORD` (existing) removes a line whose tells are all inside an allowed word; kept runs are
  excluded before counting.
- `references/gates.md`: the leak-scan section's "cannot gate" sentence becomes the tell; the
  `where`/`text` table gains `leak-cjk | line | the drawn line`; SKILL.md one bullet; DECISIONS row with
  the tables above; version 54 → 55.

**Acceptance (Rule 2).** `tests/test_cjk_leak.py`, written first and watched to fail: the eleven-text
table reproduced (0 own-language tells, the counts within ±0 — they are exact); a ja → zh-Hans delivery
with one echoed segment → FAIL with that line as the finding and the legitimately equal date and name
untouched; the same with the echo allowlisted → PASS; a zh-Hans → ja delivery with an echoed Chinese
sentence → FAIL; a kana name in a zh-Hans delivery → FAIL at six tells and PASS with `--allow`; source
drift (a compatibility ideograph in the mapping) → no tell; no `lang` → the old REVIEW line, unchanged;
a zh-Hant source into ja → the old REVIEW with the "weak pair" reason; console parity on the nine
non-CJK jobs byte-identical to `main`; `FindingsInvariantTests` holds; version 55 in lockstep.

Effort: half a day plus a review on another model. Depends on nothing beyond `main` once #8 merges
(`han_forms.convention_for_lang` is on #8).

## 5. Not doing, on purpose

- No rule V: it cannot see an echo, and `retypeset` already refuses an omitted segment.
- No simplified ↔ traditional mapping tables (OpenCC and the like): the repertoire proxy measures 0
  false tells and needs no data file.
- No TC → JP judgement: measured weak; stays REVIEW until a tell for it is measured.
- No change to the Latin or different-script scans.
