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

01–07 are **closed**. Next rows (skill leftovers, then one `/goal` each):
`goals/IMPLEMENTATION.md`. Copy the matching file into `/goal`.

| # | Session title | Why this next | Closed done bar (sketch) |
|---|---|---|---|
| **0** | Skill leftovers | Identity is in SKILL.md; some layout nits are not | Narrow columns, `allow_scale` last, second-reader deliver — no new gate |
| **08** | Quoted names survive | **Closed** | Source write/find/say tokens in output unless `allow_translate` |
| **09** | Empty is not a translation | **Closed** | Non-skip empty/whitespace targets FAIL named |
| **10** | Caption vs rect | **Closed** | `/CA` width > button width − pad → FAIL |
| **11** | Override keeps `d.` / `$` | **Next `/goal`** | Override parts must contain source marker and tail |
| **12** | Skinny column warning | After 11 | Extractor `narrow-column` warning; no auto-merge |
| **14** | OCR'd scan refusal | **Closed** | Stripping a page's text changes under 3% of its text-span pixels → extract + verify FAIL naming the invisible (OCR) layer; `corpus/ocr_layer.pdf` `refuse+ocr-layer` |
| **13** | Strip completeness | **Closed** | Stripped file, re-read without annotation appearances, has no page text; nested XObjects and inherited `/Resources` stripped; FAIL leaves no file |

Never combine 04+05. Never combine a bakeoff with a gate. Never put OCR
implementation in this skill (refusal is the product). After 08, a canary
on the toy PDF is a **different day**, not this sitting.

## What is already locked (do not regress)

- Provider-neutral seven scripts; no vendor SDK
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

## How to start a session

New session: read `goals/HANDOVER.md` first. Next gate: copy
`goals/11-override-markers.md` into `/goal`. Do not paste Grok NOTES,
`work/translations.json`, or bakeoff scores into that session.
Remaining queue: `goals/IMPLEMENTATION.md` (08–10, 13 and 14 are committed).
