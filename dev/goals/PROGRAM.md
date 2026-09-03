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
  → if strip or extract changed: dev/wild/probe.py into a scratch dir,
    compared with dev/wild/results.json — 17/17 translate, zero count
    differences (row 19 shipped a TypeError that 161 single-span
    fixtures could not see; the corpus saw it in seconds)
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
- The original's `/Title` quoted as a unit, and a multi-word `--allow`
  phrase, are kept runs in the leak scan, printed as a note; a longer run
  that contains them is still a leak; `skip` exempts nothing
- A list body starts where the source's characters put it (`gap` and
  `body_dx` in the segment); the marker stays Helvetica; a segments.json
  without either key still builds
- Shaped scripts (Arabic, Indic, Thai…) go through the Story engine with
  `/ActualText`; unshaped Arabic in an output is a verify FAIL
- `narrow-column` and `right-aligned` are *warnings*: geometry proposes,
  the author decides, nothing merges or realigns itself; `right-aligned`
  proposes only a column tucked within one em of a rule, a field or the
  next segment, never justified text
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
| **19** | `goals/19-list-marker-gap.md` | **Closed 2 Sep.** List markers lost the source's gap: `marker + ' '` shifted every list body 3.06 pt left. Segments now record the `gap`; retypeset re-emits it; old files fall back to one space | Opus 5 |
| **20** | `goals/20-notice-title-leak.md` | **Closed 2 Sep.** The compliance notice's source-language title tripped the leak scan. The original's `/Title` quoted as a unit is kept; `--allow` takes phrases; a longer run is still a leak | Fable 5.1 |

One sitting each, in that order (cheapest first). 18, 19 and 20 are
closed, and so are 21, 22 and 23. Canary run 2 (3 September, five runs,
two fixtures) opened 24–29; *Backlog after the review* has the order. Do
not paste Grok NOTES,
`work/translations.json`, or bakeoff scores into that session.

The evening review of 2 September (`docs/REVIEW-2026-09-02.md`) added a
second lane — product rows with their own closed bars — without changing
lane A's order. See **Backlog after the review** at the end of this file.

## Versioning

`SKILL.md`'s `metadata.version` is a monotonic integer, bumped whenever the
shipped scripts or the workflow change. It began as the last closed gate
number and kept counting past 17 as the audit roadmap closed, so it is an
ordering, not a row number. Bump it in the same commit as the change.
`.claude-plugin/plugin.json` carries the same number as `N.0.0`; bump both
together — CI fails when they disagree — and an installed copy picks the
new version up with `/plugin marketplace update` and `/plugin update`
(users only receive an update when the plugin version changes).

## Backlog after the review — groomed 2 September 2026 (evening)

Two lanes, one discipline: one sitting, a closed bar, explicit non-goals,
proof, and a `metadata.version` bump whenever the shipped skill changes.
The full done bars, the research behind them and the hypotheses to measure
are in `docs/REVIEW-2026-09-02.md` §5; this is the queue.

**Lane A — defects a model walked into.** Unchanged; still first.

| # | Brief | Trigger |
|---|---|---|
| 19 | `goals/19-list-marker-gap.md` | **Closed 2 Sep evening.** Segments record the whitespace after a marker (`gap`); retypeset re-emits it in every marker path; absent key → one space, so stale work directories still build. Was Opus 5, measured 3.06 pt; 0.00 after |
| 20 | `goals/20-notice-title-leak.md` | **Closed 2 Sep evening.** The original's `/Title` quoted as a unit, and a multi-word `--allow` phrase, are kept runs in the leak scan (printed as a note); anything longer is still a leak. Was Fable 5.1 and Opus 5 both allowlisting word by word |
| C2 | canary run 2 | **Closed 3 Sep.** Five runs, two fixtures (`dev/canary/runs/2026-09-03-summary.md`): Opus 5 and Fable 5.1 5/5, Sonnet 5 4/5, Haiku 4.5 0/5 on the permission slip; Fable 5.1 5/5 on the real FL-100 against the issuer's own FL-100 S. Opened 24–29 and gave P7 its brief |
| 24 | `goals/24-merge-ligatures.md` | **Closed 3 Sep.** Neither CSS switch is honoured by MuPDF 1.28, so retypeset reads the ligatures out of GSUB — cmap cannot see them in a subset — and maps each ligature glyph to its component code points with a multi-code-point `bfchar`; U+FB00–FB06 and U+007F join the drift list, so the always-on gate names a ligature that is still there. Was Sonnet 5 and Opus 5 independently |
| 25 | `goals/25-shrink-band-reported.md` | **Closed 3 Sep.** `consider_ratio` records every ratio below 1.0; retypeset prints a `scaled runs (N)` digest and writes `scale_report.json` beside the output; `verify --translations` reads it back as a REVIEW (SKIP when absent, so older builds still verify). The floor did not move and nothing new fails. Was Sonnet 5 at 0.81× and Opus 5 at 0.91× |
| 26 | `goals/26-merge-box.md` | **Closed 3 Sep.** `merges[].box` replaces the union bbox as the re-flow rect, used exactly as given; malformed boxes are refused by name; `propose-merges` writes `"box": null` and nothing computes one from geometry. Measured: 0.7× FAIL without, 1.0× and three lines with. Was Fable 5.1, Sonnet 5 and Opus 5 |
| 27 | `goals/27-kept-title-tokens.md` | **Closed 3 Sep.** `_run_key` drops tokens below the branch's own word floor on both sides, so a verbatim quote of a numbered title is kept while a part of it, or a run containing it, still is not. Was Fable 5.1 on the real FL-100, allowlisting two spellings by guesswork |
| 28 | `goals/28-right-anchor-room.md` | **Closed 3 Sep.** A `right` core's budget is now the room on its left (new `left_limit`, mirroring `right_limit`) — measured on the fixture: 0.47× and a FAIL before, full size and the original right edge after. `center`, plain and rotated runs unchanged. Was Fable 5.1 on the real FL-100 |
| 29 | `goals/29-override-plain-value.md` | **Closed 3 Sep.** The coverage check counts an override as coverage, so a core it covers everywhere may be null; an occurrence on an uncovered page still fails and names that page. verify and qa_check needed no change and are asserted. Was Fable 5.1 on the real FL-100, 13 phantom warnings |
| 21 | `goals/21-right-aligned-on-text.md` | **Closed 2 Sep evening.** A group is proposed only when at least half its members sit within one em of a rule, a field or the next segment; corpus 1,485 → 158 groups, 11,507 → 642 segments, FL-100's caption stacks kept, everything else identical |
| 22 | `goals/22-merge-candidate-kind.md` | **Closed 2 Sep evening.** Merge candidates carry `kind: "merge-candidate"`; `propose_merges` still accepts a kind-less candidate from an older `segments.json`; the corpus re-run names all 2,484 |
| 23 | `goals/23-marker-font-metrics.md` | **Closed 2 Sep evening.** Segments carry `body_dx`, measured from the source's characters; retypeset starts the body there in every marker path; absent key → row-19 placement. Corpus: 952/952 marker lines measured, drift of up to 4.9 pt (FL-300) now corrected |

**Lane B — product rows.** New. Triggered by product evidence, not by a
model's defect; never a gate.

| # | Row | Closed bar (sketch) | Not done when |
|---|---|---|---|
| P2 | Plugin packaging | **Closed 2 Sep evening.** `.claude-plugin/plugin.json` (version `35.0.0`, `skills: ["./"]`) and a one-entry `marketplace.json` at the repo root; `claude plugin validate . --strict` exits 0 and `claude --plugin-dir . plugin details pdf-translate` lists the skill; a CI job validates both and fails if `plugin.json` and `metadata.version` disagree; README and HANDOVER carry the install; the re-sync chore is deleted. `SKILL.md` untouched. The install from GitHub is proven on the box that runs it | — |
| P1 | Wild corpus, measured | **Closed 2 Sep evening.** 17 public PDFs (`dev/wild/SOURCES.md`), 449 pages, 8 of them hybrid XFA: 17/17 `translate`, zero crashes, zero timeouts, 126 pages in 37 s; everything left after strip is annotation text; page-1 renders keep every graphic. It found friction, not wrong verdicts: rows 21 and 22 and lane B row P6 (`dev/wild/ANALYSIS.md`). Re-run: `pdf-translate/.venv/bin/python dev/wild/probe.py` | — |
| P6 | Warnings at scale | **Closed 2 Sep evening.** extract prints a per-kind digest — counts and what each kind asks — then at most `--max-per-kind` lines per kind (the booklet: 2,394 lines → 61); the skill text says what each kind wants and write/find/say is a list to confirm; widget-text data values (USCIS `PDF417BarCode1`) are identity-mapped by instruction. Nothing leaves the JSON | — |
| P3 | `SKILL.md` under 500 lines | **Closed 2 Sep evening.** Body 573 → 493 lines, ~7.6k → ~6.4k tokens on invoke, by moving five regions into `references/` (new `gates.md`, `widget-text.md`, `retypeset.md`; sections added to `compliance.md`, `fonts.md`, `translations-format.md`), one-line rules left behind, frontmatter untouched but the version. The 5,000-token target is not met without deleting rules — C2 decides whether the tail matters | — |
| **P4** | Eval automation | Three `evals/**/case.yaml` cases with graders wrapping `dev/canary/score.py` plus an LLM grader for the identity and honest-delivery axes; `claude plugin eval . --runs 1 --json` produces a report; a `--threshold` documents the bar; one report committed under `dev/canary/runs/` | Running in CI on every push; naming a winner; scoring the visual pass by machine |
| **P7** | Notice channel | `goals/P7-notice-channel.md`: four of five runs on a form that needs the notice wrote their own script (Fable in runs 1 and 2, Sonnet, Opus). A `notices` list in translations.json — text, page, the box the author chose — placed by retypeset with the job's fonts through the same glyph check, canonical layer and placement gate as every other run | Choosing the box by geometry; adding a page; a notice the reader cannot read |
| P5 | One source of truth | **Closed 2 Sep evening**: README count removed and CI badge added; audit HTML is a banner-marked snapshot; findings §15; tracker carries both lanes. Rule: `checklist.html` tracks, this file queues, `HANDOVER.md` cold-starts; nothing else states counts or open rows | — |

**Order:** 24 → 25 → 27 → 28 → P7 → 26 → 29 → P4. Every row above came
from a measurement — canary run 2 or the wild corpus — never from
invention; when they are closed, run the canary again.

**Hypotheses, after the wild corpus** (`dev/wild/ANALYSIS.md` §5): hybrid
XFA — answered on page 1 of eight forms, the AcroForm layer renders
complete once XFA is gone (no Acrobat here to compare the XFA rendering);
scale — answered, 126 pages in 37 s; visible annotation text — unmeasured,
none of the seventeen files carries a non-widget annotation; fonts — only
Type1, TrueType and Type0 seen, no Type3, no outlined text; compaction —
untouched, C2's job.

**Still parked, still rejected:** a shipped glossary, OCR, a semantic term
checker, a winner model, FL-150 as gold, auto-merge or auto-realign,
vertical CJK, tag rebuild (no library support), `paths:` auto-activation
(Claude Code-only field — decide at P2).
