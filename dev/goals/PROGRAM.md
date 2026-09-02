# How this skill keeps improving

The north star is unbounded. A `/goal` session is not. Each session is **one
turn of the loop**, with a closed done bar, a named corpus, and explicit
non-goals. When it ends, the skill is strictly better on a measurable class
of failures — or it refused honestly. Then you pick the next row.

## Compass (never the done bar)

Any born-digital PDF, any language pair the pipeline can actually place,
any model or person authoring the mapping — translated so a native reader
would accept it, with fields/links/bookmarks still working; **and when that
is impossible, the scripts exit non-zero and name the reason.**

A pretty file with a green verify that did not translate is worse than a halt.

## Loop (every session)

```
construct or pick ONE adversarial case
  → drive shipped extract / retypeset / verify (not a copy)
  → if gates PASS and output is wrong: the gate is the bug
  → if gates FAIL and output is right: the gate is the bug
  → lock with an in-repo test + a corpus verdict
  → re-run tests + corpus table — nothing may regress
  → STOP. Do not start the next row in the same session.
```

Scripts on a 4-page form take a few seconds. Do not spend the session
micro-optimizing pixmap loops. Spend it on silent PASSes and honest refusals.

## Queue — run these as separate `/goal`s, in this order

Do **not** add a terminology glossary. Wrong legal terms (養子 for child
support) are a reason to not use a weak model as the mapping author, not a
reason to ship per-domain dictionaries. A public skill cannot maintain
glossaries for every pair and register.

Haiku-class models: keep them as a *canary* if you run evals; do not
recommend them as the author; do not add gates whose only purpose is to
launder their output.

| # | Session title | Why this next | Closed done bar (sketch) |
|---|---|---|---|
| **01** | Mapping actually landed | A green verify on a PDF that never received the authored strings | `--translations`: every target string appears in output `get_text()` (NBSP-normalized); corpus/fillable/scan unchanged |
| 02 | Untranslated chrome | English `/MK /CA` still drawing on the page | If original button captions remain in output text and were not `skip`/`--captions`, verify fails; field count stays exact |
| 03 | Overflow is a gate | Sonnet v1 shipped 3.01pt; v2 reworded only because the model cooperated | Retypeset exit non-zero (or verify) when any segment scales below 0.7x unless the mapping opts in |
| 04 | RTL text layer | Shaping looks fine; `get_text()` is reversed | Logical-order `/ActualText` or equivalent; round-trip matches authored Arabic/Hebrew; layout still LTR (not this session) |
| 05 | RTL layout | “Arabic poured into an English skeleton” | Opt-in mirror of x/alignment; visual pass required; no claim of full RTL without it |
| 06 | Corpus axis: structure | Queue 01–03 are content; this is documents | One new constructed class (radio/dropdown **or** mixed rotation **or** attachments) with a recorded verdict |
| 07 | One-command init | Ease, not quality | `pipeline.py init` already exists; add `pipeline.py from-cores` scaffold of empty translations.json — no LLM |

01–07 are **closed**. So are 08–17 and the whole audit roadmap below.

| # | Session title | Why this next | Closed done bar (sketch) |
|---|---|---|---|
| **0** | Skill leftovers | Identity is in SKILL.md; some layout nits are not | Narrow columns, `allow_scale` last, second-reader deliver — no new gate |
| **08** | Quoted names survive | **Closed** | Source write/find/say tokens in output unless `allow_translate` |
| **09** | Empty is not a translation | **Closed** | Non-skip empty/whitespace targets FAIL named |
| **10** | Caption vs rect | **Closed** | `/CA` width > button width − pad → FAIL |
| **11** | Override keeps `d.` / `$` | **Closed** | Override parts must contain source marker and tail; verify reads `segments.json` beside the mapping or `--segments` |
| **12** | Skinny column warning | **Closed** | Extractor `narrow-column` warning on >=3 stacked cores under 90 pt; no auto-merge, no verify gate |
| **16** | Shaped scripts | **Closed** | Arabic/Indic/Thai runs placed through the Story engine on the original baseline with `/ActualText`; verify FAILs unshaped Arabic |
| **15** | Script-aware leak scan | **Closed** | Gate 4 keyed to the source document's script (words for space-delimited, six-char runs for spaceless); same-script pairs use document words automatically; `corpus/ja_source.pdf`, `corpus/ar_source.pdf` |
| **14** | OCR'd scan refusal | **Closed** | Stripping a page's text changes under 3% of its text-span pixels → extract + verify FAIL naming the invisible (OCR) layer; `corpus/ocr_layer.pdf` `refuse+ocr-layer` |
| **13** | Strip completeness | **Closed** | Stripped file, re-read without annotation appearances, has no page text; nested XObjects and inherited `/Resources` stripped; FAIL leaves no file |
| **17** | Widget text | **Closed** | Page text read from an annotation-free display list (field values stop leaking into cores); `widget_text.json` channel for `/TU`, `/Opt` and `/V`/`/DV`; always-on `/Opt` export parity gate |

## The audit roadmap — closed

`docs/checklist.html` is the reading order; every row below is done, with
tests, and nothing regressed.

| Row | What closed it |
|---|---|
| H1 rotated lines | Segments carry the line direction; runs are morphed about their own origin; corpus `rotated_text.pdf`. A rotated run whose target needs shaping is refused, not drawn flat |
| H4/H5 canonical text layer | retypeset rewrites `/ToUnicode` to the authored code points after saving; always-on gate fails drift the original did not have; the placement gate compares verbatim |
| M5 glyph coverage | Every character of every placed run checked against the exact font object |
| M3 encryption / usage rights | Encryption and permissions reported; `/Perms` always deleted; certification flagged; `--keep-encryption` re-applies permission bits with an empty owner password |
| M4 output metadata | `/Lang`, `dc:language`, `/Title` and outline titles retargeted; orphaned `/StructTreeRoot` removed; gate 16 |
| M1/M2 alignment and roles | `right` list proposed by the extractor; four font roles; inline `<b>`/`<i>` in single-line targets |
| Goal 16 leftovers | Dot leaders refilled on shaped and RTL labels; Indic covered by an `/ActualText` gate rather than a render comparison |
| P2 quality layer | `qa_check.py`; `references/review.md`; `references/compliance.md`; the expansion table in SKILL.md; per-job `glossary.csv` input |
| P2 paragraph mode | `propose-merges`, `--pages` slices, `merge-mappings`, `bilingual.py` |
| P2 small guards | image-region review items; choice-field `/DA`; `OS/2.fsType` refusal |
| P3 hygiene | dev material out of the skill; MIT licence; `compatibility:`; pinned ranges; CI on Linux and Windows with fetched OFL fonts; eval fixtures generated |

Never combine 04+05. Never combine a bakeoff with a gate. Never put OCR
implementation in this skill (refusal is the product). The canary
(`dev/canary/`) is a **different day** from any gate.

## What is already locked (do not regress)

- Provider-neutral bundled scripts; no vendor SDK; no glossary shipped
- Scan / image-only → `refuse+OCR` (exit ≠ 0, message names OCR)
- Pale blank → `skip-ink`, not ink 0.00 FAIL
- Corpus table in `corpus/verdicts.json`
- `--captions` + drop stale `/AP`; field identity
- Same-script leak uses this document’s words
- `pipeline.py rebuild` / `render` for the inner loop
- RTL **docs** match measurement (visual-order, not mirrored)
- Strip gate: stripped file has no page text (annotation appearances
  excluded); nested XObjects and inherited `/Resources` are stripped
- OCR'd scan (invisible text layer) → `refuse+ocr-layer`; scans are out
  of scope with or without OCR
- Leak scan follows the source script (JA→EN, AR→EN, RU→ES); Latin-source
  behaviour unchanged; same spaceless family is REVIEW-only
- Shaped scripts (Arabic, Indic, Thai…) go through the Story engine with
  `/ActualText`; unshaped Arabic in an output is a verify FAIL
- `narrow-column` and `right-aligned` are *warnings*: geometry proposes,
  the author decides, nothing merges or realigns itself
- Widget text is a separate channel with `[export, display]` `/Opt` pairs;
  export values are data and never translated
- The text layer reports the authored code points; drift is a FAIL, not a
  fold
- Document metadata (`/Lang`, `/Title`, outline) is retargeted, and the
  orphaned structure tree is removed rather than left pointing at deleted
  text
- No glossary ships with the skill; `glossary.csv` is a per-job input only
- Dev material lives in `dev/`, outside the installed skill

## How to start a session

New session: read `dev/goals/HANDOVER.md` first. Every row of the repo's
queue and of the audit roadmap is closed. **The next three rows exist and
were not invented** — the 2 September canary produced them, each from a
model doing a real job, each with a measurement in `dev/canary/runs/`:

| # | Brief | What | Found by |
|---|---|---|---|
| **18** | `goals/18-center-example.md` | **Closed 2 Sep.** `center` was documented for "signature captions", the one case where it is wrong (left-flush under a rule). Example corrected, SKILL.md step 5 says it, a constructed fixture locks the geometry (a wider translation `center`ed lands left of the source x0; anchored left it lands on it; verify passes both). No warning, by decision | Haiku 4.5 |
| **19** | `goals/19-list-marker-gap.md` | List markers lose the source's gap: `marker + ' '` shifts every list body 3.06 pt left. Touches the segment schema | Opus 5 |
| **20** | `goals/20-notice-title-leak.md` | The compliance notice's source-language title trips the leak scan. A title quoted in a notice is an identifier by the skill's own rule | Fable 5.1 |

One sitting each, in that order (cheapest first). 18 is closed; 19 is
next, then 20. After those, do not invent the next row: run the canary
again and see what it walks into. Do not paste Grok NOTES,
`work/translations.json`, or bakeoff scores into that session.

## Versioning

`SKILL.md`'s `metadata.version` is a monotonic integer, bumped whenever the
shipped scripts or the workflow change. It began as the last closed gate
number and kept counting past 17 as the audit roadmap closed, so it is an
ordering, not a row number. Bump it in the same commit as the change, and
re-sync any installed copy.
