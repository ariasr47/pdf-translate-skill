# Handover — pdf-translate (read this in a new session)

Paste this file (or: “read `dev/goals/HANDOVER.md` and continue”) into a
**new** agent session that has no memory of prior work.

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
The install from GitHub itself has not been exercised from this machine —
the first `/plugin install` on the Windows box is the proof.

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
