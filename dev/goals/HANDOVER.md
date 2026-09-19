# Handover — pdf-translate (read this in a new session)

Paste this file (or: “read `dev/goals/HANDOVER.md` and continue”) into a
**new** agent session that has no memory of prior work.

## Start here — 19 September 2026 (this section wins over everything below it)

**Both branches are pushed and both PRs are open: [#12](https://github.com/ariasr47/pdf-translate-skill/pull/12) (row 32, v57, base `main`) and [#13](https://github.com/ariasr47/pdf-translate-skill/pull/13) (E3, v58, stacked on #12). Merge #12 first; GitHub retargets #13.** Both MERGEABLE. **CI has not run on either** — every job failed in 1–5 seconds with *"The job was not started because recent account payments have failed or your spending limit needs to be increased"*. That is GitHub account billing, not the code; the only workflow change is three test-module names on one `run:` line. After billing is fixed: `gh run rerun 35432185828 && gh run rerun 35432191241`. Do not merge on a red that never ran — both suites are green locally (Windows / Python 3.14, 492 and 15), but the Ubuntu and 3.10 legs are unverified.

**Next work is B1** — the library never breaks a line, so a long translation shrinks or goes untranslated. It is the coverage lever and it needs a design pass first: canvas → ruling → corpus probe to size it → plan. `docs/BRIEF-product-bubble-2026-09-18.md` has the reasoning and the other four bubbled items (B2, B3 answered by v58; B5 by v57; B4 contained).

**Starting in Codex / GPT-6?** Read `dev/goals/HANDOVER-codex-2026-09-19.md` first — it is written for that harness (no superpowers skills, `AGENTS.md` is yours, the venv-vs-system-Python trap, the two parity ratchets and the four traps this repo has actually fallen into).

## 18 September 2026 — superseded by the section above

*Kept for the record. Where it and the 19 September section differ, the one above is right: both branches ARE pushed now, both PRs are open, and `feat/consumer-surface` is 12 commits, not 9.*

**State.** `main` is at **v56**: PRs **#10** (gate 21 `leak-cjk`, v55) and **#11** (three gate gaps from the first FL-150 → ja job, v56) are **merged**, `main` at `bacc436`. Two branches are ahead and **none is pushed** — merge, push and delete are the operator's, always:

- `feat/terminology-loop` — **row 32 is built and complete**, v56 → **57**. 13 commits: the design canvas and both plans, the determinism probe work, then row 32's five tasks. Suite **452 OK**, canary **15 OK**, console parity diffs empty against a `main` worktree. Evidence: `docs/reviews/2026-09-17-terminology-loop.md` (including the §4 Proof run for real).
- `feat/consumer-surface` — **E3 complete**, v57 → **58**. 9 commits. Every stage has a silent `run_*` twin returning a schema-versioned result and raising typed exceptions; all 172 `print` sites now log; `run_retypeset` takes `progress`, `cancel`, `scale_report` and `resource_root`; `scale_report.json` gained its envelope; `references/consumer-guide.md` is written and every code block in it was run. Suite **492 OK**, canary **15 OK**, and **both** parity runners hash-identical against a v57 worktree. Evidence `docs/reviews/2026-09-18-consumer-surface.md`. Not done: the whole-branch review on the most capable model.

**Do first.** Push `feat/terminology-loop` and open its PR (it carries the design canvas and both plans), then `feat/consumer-surface` stacked on it. Both are built and green; nothing is half-done. After that, the five items the product bubbled on 2026-09-18 are the queue — B1 (the library never breaks a line, so there is no kinsoku and a long translation shrinks instead of wrapping) is the coverage lever and needs a design pass before any build; B2 and B3 are **already answered** by E3's structured refusals (`exc.refusals` carries every refused core in full); B4 (widget text untranslated) is contained; B5 is row 32's terminology loop, which is built. See the end of `docs/reviews/2026-09-18-consumer-surface.md` and the session's closing notes.

**What row 32 shipped.** A `review` stage (`pdf_translate/review.py`, silent, schema-versioned `ReviewVerdict`) that writes `review_pairs.md` and `review_prompt.md`, ingests `review.json`, and grows a per-class `glossary.csv` the existing `qa_check --glossary` gates the next job on. `finish` gains `--work DIR` and refuses while a review is missing or open; `--no-review` delivers and marks the delivery. `review_state.json` is written beside `FINAL.pdf` on **every** run — that record, not the refusal, is what honours R5 for the product. Plus `references/terminology-failure-modes.md`, a terms-of-art table as SKILL.md step 1's fifth identity fact, and a canary terminology axis (FL-150: 15.29 accepted findings per 1,000 source words, **19% reviser false-positive rate**).

**Two plan defects found by measuring first** (both in `docs/reviews/2026-09-17-terminology-loop.md` §4). The plan's leading-token rule stopped at the colon, which puts `rejected on measurement` outside the enum — it needs `.split()[0]`. And the FL-150 `review.json` carries **no** `term`/`term_target` on any finding, so the measured termbase result is **0 added / 11 skipped**, not the plan's 5 and 6. Implemented the strict way (never guess a term into a file that gates the next job) and pinned. **This is the one item the operator may reasonably rule differently on** — enriching the fixture is one edit plus one test's numbers.

**Determinism (C7/E8) is measured and closed as a question.** `docs/BRIEF-determinism.md`: only `/ID` element 2 varies, only with the clock, on all three shapes including a 3-widget form and a 25-core table. No `timestamp=` parameter is needed; C7 is a `doc_id=` parameter and a test. The path-does-not-leak claim is now established by a controlled tick-grouped experiment, not by a lucky pair of runs. One thing stays unmeasured and is E8's first red test: that a caller-set `doc_id` survives `ez_save`.

**Open threads.**
1. Operator: push `feat/terminology-loop`, open its PR; then `feat/consumer-surface`.
2. B1 — line breaking and kinsoku. Measured by the product: zero `insert_htmlbox` calls on a 4-page form, 518 drawn lines, each one `TextWriter.append` at its source baseline. No design exists; do the design pass first.
3. E4–E7 in the product's order (`docs/REQUESTS-from-product.md`).
4. FL-150 job follow-ups, only if asked (unchanged, below).
5. Operator: delete the merged branches from #1–#11; pick the PyPI name for E10.

## 17 September 2026 — superseded by the sections above

**State.** `main` is at v54 (gates 19 kinsoku, 20 han-forms; the product's work order transcribed in `docs/REQUESTS-from-product.md`). Two branches are ahead: `feat/cjk-leak-tell` — PR #10, gate 21 `leak-cjk`, v55, CI green, base `main` — and `fix/cjk-job-gates` on top of it (v56: three gate gaps found by the first FL-150 → Japanese job — wrapped CJK paragraphs invisible to the placement gate, Noto Sans JP `locl` digit alternates drifting in the text layer, hidden pushbuttons counted as chrome — red-first tests, suite 401 OK; pushed, **PR #11**, base `feat/cjk-leak-tell`, CI 5/5 green at `bf96f65`). A third is ahead of that: `docs/32-design-canvas` — row 32's design pass and implementation plan, docs only, **not pushed**. Merge, push and delete are the operator's, always.

**Do first — P0: row 32 in `PROGRAM.md`, brief `dev/goals/32-terminology-loop.md`.** The design pass is **done** (canvas sources in `docs/design/32-terminology-loop/`, eight artboards) and so is the plan (`docs/plans/2026-09-17-terminology-loop.md`, five tasks, red-first, v56 → 57) — both on `docs/32-design-canvas`. Three rulings are settled in the plan: `finish` gains `--work DIR`; `resolution` is the strict enum with prose moved to `resolution_note` (the one real `review.json` stores prose, so `--ingest` migrates by leading token); a terminology finding without `term`/`term_target` is reported and skipped, never guessed into a termbase. One measured tension is recorded there too: ruling **R5** says only a build refusal withholds an output, and `finish` is packaging, not building — so the refusal is built for the CLI user while the product is served by `review_state.json`, written on every run. Build starts once #10 and #11 merge, on `feat/terminology-loop` off `main`. Then **E3** (step-2 readiness for the product; inventory in `docs/E3-surface-inventory-2026-09-17.md`; design before build).

**Open threads.**
1. Operator: merge #10 then #11 (both open, mergeable, CI green; GitHub retargets #11 to `main` when #10 merges). Then push `docs/32-design-canvas` and open its PR.
2. Row 32 (above).
3. E3 design pass, then E4–E7 in the product's order (`docs/REQUESTS-from-product.md`).
4. FL-150 job follow-ups, only if asked: re-caption and re-wire the four hidden dead buttons; a human read of pages 2–4; a bilingual tooltip on the court name. The job lives in `dev/jobs/fl150-ja-2026-09-17/` (its README fetches the source and rebuilds in ten seconds).
5. Operator: delete merged branches; pick the PyPI name for E10.

**Session log:** `docs/sessions/Session_Log_2026-09-17_FL150_Japanese_And_Gate_Fixes.md` (verbatim prompts, decisions, artifact inventory). The Claude memory directory on the Windows box mirrors this file and is not portable; on a new machine this file is the truth. End the next session by adding a dated section above this one and a log under `docs/sessions/`.

**Nothing in lane A is open, and nothing in it was invented.** The audit
roadmap and the repo's own queue are closed, and so is every defect the
two canary runs and the wild corpus produced — rows 18 to 29 in
`dev/goals/PROGRAM.md`, each with a measurement in `dev/canary/runs/` or
`dev/wild/ANALYSIS.md` and a closing note in its brief. What is left is
one lane B row: **P4** (eval automation). P7, the notice channel, closed
on 3 September. When P4 is done, do not invent a row — run the canary.

**Evening of 2 September:** a deep review (`docs/REVIEW-2026-09-02.md`;
queue in `PROGRAM.md` → *Backlog after the review*) added a second,
*product* lane. Lane A — 19, 20, then canary run 2 — is unchanged and still
goes first. Lane B rows (plugin packaging, a measured wild corpus,
`SKILL.md` under 500 lines, eval automation) each have a closed bar and one
sitting. The wild corpus ran that same evening (P1 closed): seventeen
public PDFs, no crashes, no wrong verdicts, and it opened rows **21** and
**22** and lane B row **P6** — `dev/wild/ANALYSIS.md` has the numbers.
The PDFs are re-fetched from `dev/wild/SOURCES.md`, never committed.
Rows 19 to 23 closed the same night (version 35, 174 tests); the corpus
measurement made while closing 19 opened row 23, and closing 23 measured
the drift it corrects on every file with one-space lists. Lane B's P2,
P6 and P3 closed the same night too: the repository is a Claude Code
plugin, the extractor prints a digest instead of one line per warning,
and `SKILL.md` is back under 500 lines with the detail in `references/`.
Canary run 2 followed the same night — Opus 5 and Fable 5.1 at 5/5,
Sonnet 5 at 4/5, Haiku 4.5 at 0/5, and Fable 5.1 at 5/5 on the real
FL-100 beside the Judicial Council's own Spanish — and opened rows 24–29.

**3 September:** rows **24, 25, 27, 28, 26 and 29 all closed**, in that
order, one sitting's worth of work each — reproduce, fix, lock, full
suite, `metadata.version` bump, commit — and one commit apiece. **Lane A
is now empty.** 205 tests, no skips; `metadata.version` 43.

**Repo:** `<REPO>` — GitHub `ariasr47/pdf-translate-skill`, branch `main`
**Skill dir:** `pdf-translate/` (the only directory you install)
**Dev material:** `dev/` — this file, the goal briefs, the canary, explainers
**Interpreter:** `python3` (`py -3` on Windows; bare `python` is the Store alias)
**Tests:** from `pdf-translate/`:

```bash
python3 -m pip install -r requirements.txt
python3 tools/fetch_test_fonts.py      # or the shaping tests skip
python3 -m unittest tests.test_pipeline tests.test_corpus_verdicts -v
```

On the macOS box, bare `python3` is Apple's 3.9 with none of the
dependencies; use `pdf-translate/.venv/bin/python` (3.14, pymupdf 1.28,
pikepdf 10) for everything above.

**State of play, 3 September 2026, end of the lane-A sitting:**

- **225 tests, no skips**, ~32 s locally, green on GitHub Actions across
  Linux and Windows, Python 3.10 and 3.13.
- `SKILL.md` is at `metadata.version: "47"`; `plugin.json` at `47.0.0`.
  The body is 499 lines and about 6.5k tokens on invoke; its references
  are one level deep and each opens with a contents line.
- Working tree clean apart from `dev/canary/last-score.json`, a scratch
  file `score.py` rewrites on every run. Nothing is half-finished.
- Program rows 01–29, the whole September audit roadmap and lane B's P7
  are **closed**. **Canary run 3 opened rows 30 and 31**, both in code
  that shipped the same day. Lane B's **P4 is blocked**: its brief and
  its three cases exist, but `claude plugin eval` is in early access and
  is not enabled for this account, so nothing has ever parsed them.
- The canary has run three times. Run 1 opened 18, 19 and 20; the wild corpus
  21, 22 and 23; run 2 (Opus 5, Sonnet 5, Fable 5.1 and Haiku 4.5 on the
  fixture, Fable 5.1 on the real FL-100 —
  `dev/canary/runs/2026-09-03-summary.md`) opened 24–29 and gave P7 its
  brief. All twelve are closed, and so is P7. **Canary run 3 ran on
  3 September** — Opus 5, Sonnet 5 and Fable 5.1 on the permission slip,
  all three 5/5, `dev/canary/runs/2026-09-03-run3-summary.md`. It
  confirmed rows 24–29 and P7 held (three of three used `notices`, down
  from four of five writing their own script; three of three used
  `merges[].box`; nothing shipped below source size) and opened rows
  **30** and **31**. P4 remains blocked on an account grant, not on
  work.

---

## 1. What this product is

**pdf-translate** localizes a **born-digital PDF** (any language pair the
pipeline can place) while keeping the **same visual layout** and every
fillable field working (same names, types, rects).

Architecture: **strip-and-retypeset**. Delete page text at the content-stream
level; re-insert translated text at original coordinates. Do not overlay
white boxes, do not regenerate the document, do not use redaction
annotations (they delete widgets).

It is **provider-neutral**: plain Python, no vendor SDK. Any person or model
authors `translations.json`. The scripts do not call an LLM.

It is **not** FL-150 English→Japanese. FL-150 was a hard **canary**, not the
product. Court forms, hospital packets, tax sheets, brochures and manuals all
use the same pipeline.

Priority when requirements conflict:

1. **structure** (fields, links, bookmarks work)
2. **layout** (only the text changes)
3. **natural translation in this document's register**
4. file size / aesthetics

A pretty file with a green verify that did not translate is worse than a halt.

---

## 2. How an agent is supposed to translate (skill text)

`SKILL.md` is the workflow. Scripts are in `scripts/`. Format:
`references/translations-format.md`. Silent pipeline failures:
`references/failure-modes.md`. Fonts: `references/fonts.md`. The reviewer
checklist and the MQM prompt: `references/review.md`. When a notice belongs
in the document, and the certification template: `references/compliance.md`.

**Recon is two parts.** Geometry (pages, fields, fonts, XFA, encryption,
`/Perms`), then **identity** written in NOTES / session notes **before**
filling any translation:

1. **Class** — one sentence a librarian could file
2. **Issuer** — who published it, or `none` / `unknown`
3. **Parallel text** — URL/path of *this same document* in the target
   language, or `none`, or `not searched`
4. **Identifiers** — names on *this* PDF the reader must write, find, or say
   in the source language (complete after extract)

The class also decides whether the output needs a target-language
"translation for information only" notice (`references/compliance.md`).

**Lookup.** If you can search, you must. If a published translation of this
same document exists, **those terms of art win**. Do **not** ship a glossary
in the skill; `glossary.csv` is a per-job input to `qa_check.py`.

**Write/find/say.** If the reader must write it, hand it over, or search for
it, keep the source token (or bilingual `target (Source)`).

Hot loop after first extract: edit `translations.json` → `pipeline.py qa` →
`pipeline.py rebuild` → `pipeline.py render` → look at the PNGs. The visual
pass is mandatory. Gates cannot see wrong jargon (養子支援 on a
child-support page still passes structure).

---

## 3. What is locked (do not regress)

### The mapping actually lands

`--translations` requires every authored target **verbatim** in the output
text layer; empty and whitespace-only values FAIL; overrides must keep the
source marker (`d.`) and tail (`$`); write/find/say identifiers from the
original must survive unless listed in `allow_translate`.

### The file stays a form

Field parity (names, types, rects) is exact. `/Opt` export values are
byte-identical to the original — a dropdown is translated on its display
half only. Fill round-trip works. Nothing is added: leftover pushbutton
captions must be `skip`'d or rewritten with `--captions`, and a caption
wider than its widget FAILs.

### Refusals

Scan or image-only → `refuse+OCR`. Invisible (OCR) text layer →
`refuse+ocr-layer`. Never implement OCR: the refusal is the product. Leftover
page text after strip deletes the stripped file. A rotated run whose target
needs shaping is refused rather than drawn flat. A font whose `OS/2.fsType`
forbids embedding is refused.

### The leak scan keeps what the reader must find

The original's `/Title` quoted as one run (the compliance notice names the
form) and any multi-word `--allow` phrase are kept, printed as a note, and
never counted; a longer run that contains them is still a leak; nothing in
`skip` is exempt; the three-word threshold is unchanged.

### The text layer is honest

retypeset rewrites `/ToUnicode` to the authored code points; NBSP, soft
hyphen, U+2010/U+2011 and CJK compatibility ideographs that are in neither
the original nor the mapping are a FAIL. Shaped scripts go through the Story
engine and are marked with `/ActualText`; a shaping-script target with no
mark was drawn glyph by glyph and FAILs. Every character of every placed run
is checked against the exact font object.

### Geometry proposes, the author decides

`narrow-column`, `right-aligned`, merge candidates and `image-region` are
**warnings**. Nothing merges or realigns by geometry. `propose-merges`
accepts candidates in bulk, with `html: null` that still FAILs.
`right-aligned` proposes only a column tucked within one em of a rule, a
field or the next segment — justified text, hanging indents and tables of
contents are not columns (row 21, measured on the wild corpus).

### Everything else that is not page text

Widget text (`/TU`, `/Opt`, `/V`, `/DV`) has its own channel. `/Lang`,
`dc:language`, `/Title` and outline titles are retargeted. `/Perms` is
always deleted and reported; a certified source is flagged. The orphaned
`/StructTreeRoot` is removed with `/MarkInfo /Marked false`.

---

## 4. Hard constraints (every sitting)

- **Provider-neutral.** No vendor SDK. No per-language branch.
- **No glossary** in the repo. `glossary.csv` is a job input, never shipped.
- **No winner model** in `SKILL.md`.
- **Not FL-150** as a proof fixture. Constructed PDFs.
- **One row per session.** STOP when that bar is green.
- **Never mix a canary with a gate.**
- **Never implement OCR.**
- Never auto-merge or auto-realign by geometry.
- Scripts cannot judge whether jargon is the *right* term. A wrong heading
  is a reason not to use that model as author, not a reason to add a
  dictionary.

---

## 5. What is not done

### Both canary-run-3 rows closed; one blocked row left

**Row 30** — **closed 3 September.** The charset walk is now
`job_charset(conf)`: a `null` core skipped rather than iterated,
`notices[].text` harvested, and a docstring naming it as the one place
the next block goes.

**Row 31** — **closed 3 September.** retypeset names any role that
resolved to the regular face, once, with what asked for it; both
mechanisms are covered (`role()` and the Story engine's `<b>`/`<i>`),
since the case that opened the row went through the second.

**Lane A is empty again.** The only thing still open, and blocked: **P4**, eval
automation (`goals/P4-eval-automation.md`, written 3 September). Three
`case.yaml` cases and their graders are in `pdf-translate/evals/` and
`claude plugin validate --strict` passes with them, but **`claude plugin
eval` is in early access and is not enabled for this account** — every
form of the command, including `eval init --bare`, exits with "`plugin
eval` is currently in early access". So the cases have never been
parsed, no report exists, and the row cannot close here. It needs the
grant, then one run; the brief's §7 says exactly what to do with it.

With the queue drained, **canary run 3** is what produces the next rows.
Do not invent one.

The twelve closed rows below are kept for the record. Each came from a
model or a real document walking into something:

| # | Brief | What | Found by |
|---|---|---|---|
| **18** | `goals/18-center-example.md` | **Closed 2 Sep.** `center` was documented for "signature captions", the one case where it is wrong: those are left-flush under a rule, and centring moved one 7.5 pt off its own rule, past every gate. Example corrected, SKILL.md step 5 says it, `test_center_moves_a_left_flush_caption_off_its_rule` locks the geometry; no warning built, by decision (closing note in the brief). | Haiku 4.5 |
| **19** | `goals/19-list-marker-gap.md` | **Closed 2 Sep.** retypeset re-emitted `marker + ' '` where the source had two spaces, shifting every list body **3.06 pt left**. Segments now carry `gap`; every marker path re-emits it; an old segments.json gets one space. Row 23 holds the font-metric remainder. | Opus 5 |
| **20** | `goals/20-notice-title-leak.md` | **Closed 2 Sep.** `compliance.md` told the author to name the source form title in the notice; the leak scan then FAILed that title. The original's `/Title` quoted as a unit is now a kept run (noted, not counted), `--allow` takes phrases, and a longer run is still a leak. | Fable 5.1 |
| **24** | `goals/24-merge-ligatures.md` | **Closed 3 Sep.** The Story engine shapes Latin: `liga` put U+FB01 (or U+007F in a subset) where the author wrote "oficina". Both CSS switches were measured and MuPDF 1.28 honours neither, so retypeset reads the ligatures out of **GSUB** — cmap cannot see them in a subset — and maps each ligature glyph to its component code points with a multi-code-point `bfchar`. U+FB00–FB06 and U+007F joined the drift list. | Sonnet 5 and Opus 5, independently |
| **25** | `goals/25-shrink-band-reported.md` | **Closed 3 Sep.** `consider_ratio` records every ratio below 1.0; retypeset prints a `scaled runs (N)` digest and writes `scale_report.json` beside the output (even when empty); `verify --translations` reads it back as REVIEW / PASS / SKIP, never a new FAIL. The 0.7× floor did not move. | Sonnet 5 (0.81×) and Opus 5 (0.91×) |
| **27** | `goals/27-kept-title-tokens.md` | **Closed 3 Sep.** `_run_key` drops tokens below the branch's own word floor on both sides, so a verbatim quote of `FL-100 Petition—Marriage/Domestic Partnership` is kept although `FL` and `100` are invisible to the scan. A part of it, or a run containing it, still leaks. | Fable 5.1, real FL-100 |
| **28** | `goals/28-right-anchor-room.md` | **Closed 3 Sep.** A `right` core's budget is now the room on its **left** (new `left_limit`, mirroring `right_limit`). Measured: **0.47× and a FAIL** before, **full size** after, right edge on the original's; with a neighbour close on the left it shrinks to 0.79× and stops at the limit. | Fable 5.1, real FL-100 |
| **26** | `goals/26-merge-box.md` | **Closed 3 Sep.** `merges[].box` replaces the union bbox as the re-flow rect, used exactly as given; malformed boxes refused by name. Measured: 0.7× FAIL without, 1.0× and three lines with. `propose-merges` writes `"box": null`; geometry still chooses nothing. | Fable 5.1, Sonnet 5, Opus 5 |
| **29** | `goals/29-override-plain-value.md` | **Closed 3 Sep.** The coverage check counts an override as coverage, so a core it covers everywhere may be `null`; an uncovered occurrence still fails and names its page. verify and `qa_check` needed no change and are now asserted. | Fable 5.1, real FL-100 |

All twelve measured rows are closed, and so is every lane B row but the
blocked one:
P2 (the repository is a plugin), P6 (the warning digest), P3 (`SKILL.md`
under 500 body lines), P1 (the wild corpus), P5, and P7 (the notice
channel — `notices` in `translations.json`, placed by retypeset through
every gate a merge goes through). Rows 24, 25, 27, 28, 26, 29 and P7 all
closed on 3 September, one commit and one `metadata.version` bump each,
with a measurement in every closing note. What is left: **P4** (bar in
`PROGRAM.md`'s table and in `docs/REVIEW-2026-09-02.md` §5, no brief file
yet).

One defect from that canary is already fixed: the placement gate could not
pass a wrapped merge, which broke paragraph mode on the day it shipped
(`MergePlacementGateTests`).

### Installing it (the re-sync chore is gone)

The repository is a Claude Code plugin and a one-entry marketplace
(`.claude-plugin/`, lane B row P2, closed 2 September):

```
/plugin marketplace add ariasr47/pdf-translate-skill
/plugin install pdf-translate@pdf-translate-skill
```

Later versions: `/plugin marketplace update pdf-translate-skill`, then
`/plugin update pdf-translate`. A private repository works wherever `git`
has GitHub credentials. The manual copy on the Windows box
(`%APPDATA%\Claude\…\skills\pdf-translate`, version 16) is replaced by
that install; do not copy directories by hand again. `plugin.json`'s
version is `metadata.version` as `N.0.0` and CI fails when they disagree.

**The install from GitHub is proven** (3 September, this Mac):
`claude plugin marketplace add ariasr47/pdf-translate-skill` clones over
HTTPS and validates, `claude plugin install pdf-translate@pdf-translate-skill`
exits 0, and `plugin list` shows **47.0.0, enabled, user scope**. The
installed copy under
`~/.claude/plugins/marketplaces/pdf-translate-skill/pdf-translate/` carries
the whole skill — 11 scripts, 8 references, `SKILL.md` at `version: "47"`
— not just the frontmatter. Later versions: `marketplace update
pdf-translate-skill`, then `plugin update pdf-translate`.

`docs/audit-2026-09-01.html` carries a snapshot banner and is not
maintained; `docs/checklist.html` is the tracker.

### Out of scope forever, unless the user reverses it

A shipped glossary, OCR implementation, a semantic term checker, a winner
model named in `SKILL.md`, FL-150 as a gold fixture.

## 6. How to run a sitting, when there is one

```
construct ONE tiny PDF that shows the defect
  → drive shipped extract / retypeset / verify (import scripts, not a copy)
  → if gates PASS and output is wrong: the gate is the bug
  → if gates FAIL and output is right: the gate is the bug
  → lock with an in-repo test; corpus unchanged
  → python3 -m unittest tests.test_pipeline tests.test_corpus_verdicts -v
  → if strip or extract changed: python dev/wild/probe.py --out <scratch>
    and compare with dev/wild/results.json — zero differences (the
    fixtures are single-span lines; real documents are not)
  → bump metadata.version in SKILL.md; STOP
```

---

## 7. File map

| Path | Role |
|---|---|
| `pdf-translate/SKILL.md` | The workflow an agent/person follows |
| `pdf-translate/scripts/*.py` | strip, extract, prepare_font, retypeset, verify, qa_check, field_fonts, compare, bilingual, render_pages, pipeline |
| `pdf-translate/references/` | failure-modes, translations-format, fonts, review, compliance |
| `pdf-translate/tests/` | Constructed-PDF tests of the shipped stages; the corpus table |
| `pdf-translate/corpus/` | Tiny adversarial PDFs + `verdicts.json` |
| `pdf-translate/tools/fetch_test_fonts.py` | OFL faces for the shaping tests (never committed) |
| `pdf-translate/evals/` | Eval prompts and `make_fixtures.py` |
| `dev/goals/PROGRAM.md` | The loop, the closed queue, what is locked |
| `dev/goals/HANDOVER.md` | **This file** |
| `dev/canary/` | The fitness check for a model as mapping author |
| `docs/checklist.html` | The tracker across the program and the audit roadmap |
| `docs/RESEARCH-AND-FINDINGS.md` | The audit and every verified defect with status |
| `.github/workflows/tests.yml` | Linux + Windows, Python 3.10 and 3.13; plus the plugin-manifest job |
| `.claude-plugin/` | `plugin.json` and `marketplace.json`: the repository installs as a Claude Code plugin |

`work/`, `runs/`, `fl150_original.pdf`, `tests/fonts/*.ttf` and the generated
eval fixtures are gitignored.

---

## 8. First message for the next session (copy this)

```
Read dev/goals/HANDOVER.md, then pdf-translate/SKILL.md.

Work in <REPO>. Interpreter: python3 (py -3 on Windows).
Tests, from pdf-translate/:
  python3 tools/fetch_test_fonts.py
  python3 -m unittest tests.test_pipeline tests.test_corpus_verdicts

212 tests, no skips, green locally; confirm CI after pushing. Everything is
committed. Program rows 01-29, the audit roadmap and lane B's P7 are
closed. Do not redo them. Lane A is empty; do not invent a row.

Note: strip's XObject traversal is sorted (3 September) because pikepdf's
dictionary order is hash-randomized; `dev/wild/results.json` was
regenerated from that deterministic run, so a re-run now really should
differ only in timings. `dev/wild/ANALYSIS.md` section 10 has it.

Canary run 3 ran on 3 September (three models, all 5/5) and opened rows
30 and 31; both were closed the same evening. THE QUEUE IS EMPTY except
P4, which is BLOCKED, not queued: `claude plugin eval` is in early
access and is not enabled for this account, so the three cases written
for it under pdf-translate/evals/ have never been parsed. Read
dev/goals/P4-eval-automation.md section 7 before touching it.

Next sitting: canary run 4 (dev/canary/README.md), which is what opens
rows — or P4 if its early-access grant has landed. Do not invent a row. Do not mix in a
canary run. No glossary. Not FL-150 as a fixture.

When the bar is green: full unittest + corpus, bump metadata.version in
SKILL.md, commit, stop.
```

P4 is the only queued row and it is blocked; the canary is what comes
next. If the user wants the
stale audit HTML or the installed-copy re-sync instead, say so and do only
that — neither is a gate, and neither needs a fixture.
