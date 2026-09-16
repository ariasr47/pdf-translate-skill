# BRIEF — unattended delivery: every gate outcome reaches the customer, and REVIEW shrinks

**For:** the agent doing this work in `C:\Dev\pdf-translate-skill`.
**Written:** 2026-09-15, in this repo, after the pdf-translate session's recommendation of the same
day was checked against the code and against measurements. Status of the work it assumed: PRs #1–#4
are merged; `main` is at skill version 50.
**Self-contained:** you do not need the product repo or the chat that produced this. Everything
you need is below or in the files named.

---

## 1. The problem, in one paragraph

In production there is no reviewer. A customer uploads a document and receives a file. The
render-and-look step that `verify.py` says it does not replace never happens, and every verdict
that is not PASS or FAIL ships to the person paying. A REVIEW line ("a human must look") is
indistinguishable from PASS at the point of delivery. The failure that loses a customer is not a
document that comes back obviously broken; it is one that comes back **looking fine and being
wrong** — a tone mark on top of a vowel, a conjunct drawn as consonant-plus-halant — discovered
later, in front of someone who matters. The same structural checks, *shown*, are the reason to
pay: the competition returns a file and says nothing.

## 2. What is true today (verified 2026-09-15 against `main` at v50)

- `verify` runs 18 gates and prints PASS / FAIL / REVIEW / SKIP lines; exit 1 on any FAIL; REVIEW
  never changes the exit code.
- `pdf_translate.verify.run_verify(...)` returns a `VerifyVerdict(exit_code, gates)`. Since PR #4,
  `gates` mirrors the console line for line: one `GateResult(name, status, message)` per printed
  outcome, names from the closed list `verify.GATE_NAMES` (22). **What it lacks:** *where*. The
  console prints the page, field name, font, token or run under each non-PASS line (`for x in
  items[:10]: print('   ...')`); the verdict carries only a count in `message`.
- `retypeset` already writes one sidecar beside its output: `scale_report.json` (the precedent for
  a machine-readable artifact next to the PDF). `extract_segments` already writes structured
  review items into `segments.json["warnings"]` (`kind`, `page`, `bbox`, `why`).
- The product request inbox (`docs/REQUESTS-from-product.md`) is empty.

### Every REVIEW the skill can print, and who can make it go away

| verdict name | when | who eliminates it |
|---|---|---|
| `leak-isolated` | **every job**, even "none" | this repo: "none" should be PASS (task B) |
| `metadata-lang` | mapping has no `lang` | the product: always pass `lang` |
| `conjunct-shaping` "cannot attest" | embedded face lacks the probe glyphs | the product: build faces with `prepare_font`, which adds them |
| `conjunct-shaping` Thai / Lao / Hebrew niqqud | any such text on the page | this repo: a mark-layout tell (tasks C, D) |
| `conjunct-shaping` Gujarati … Tibetan | unmeasured conjunct scripts | this repo: faces + measured rows (task E) |
| `leak-scan` | source and output share a spaceless family (zh→ja) | this repo: a verbatim-segment tell (task F) |
| `scaled-runs` | a run shipped below source size | nobody — a real decision; the report must carry page, ratio and key so the product can set a policy |

`extract_segments` warnings (image regions, narrow columns, …) are the same kind of item and
already structured; the product surfaces them from `segments.json`.

## 3. Measured this day — do not re-derive, do not alter

Script: `dev/probes/mark_layout_tell.py` (`--render DIR` regenerates the images). PyMuPDF 1.28.2,
the nine fetched Noto faces. Method: render a probe off the SAME face glyph by glyph (`insert_text`
with `fontname=`) and through the Story engine (`insert_htmlbox`), read every drawn glyph's id and
origin from `get_texttrace()`, and compare the run's **signature** — the multiset of (glyph id, dx,
dy) relative to the first glyph. Both arms assert the face that drew them.

| script | probe | shaped ≠ naive | subset keeps it | face with GSUB+GPOS removed |
|---|---|---|---|---|
| Thai | ป้า, ที่ | yes (variant glyph ids) | yes | **identical to naive** |
| Thai | กิ่, ปู่ | yes (ids and positions: stacked / below-base marks) | yes | **identical to naive** |
| Hebrew niqqud | שָׁלוֹם, בְּ | yes (marks move 5–20 pt at 24 px) | yes | *differs*: HarfBuzz composes presentation forms (U+FB2A, U+FB31, U+FB4B; 7→5, 3→2 glyphs) |

Rendered at 600 dpi:

- **Thai, table-less face through the Story engine:** the tone mark collides with po pla's
  ascender in ป้า and ปู่, and sits *on top of* sara i / sara ii in กิ่ and ที่ instead of above them.
  Broken, visibly. Identical to the glyph-by-glyph render. The full face draws every mark clear.
- **Hebrew, TextWriter (the path `retypeset` uses for Hebrew today, `retypeset.py:162`):**
  readable with Noto Sans Hebrew — the mark glyphs carry negative side bearings that land them over
  the base. The Story engine refines each mark by 1–2 pt at 36 px (qamats centred under shin,
  sheva centred under bet). Not a broken-output defect with this face; font-dependent.
- The `pyftsubset` subset `prepare_font` writes (16 glyphs, 7.5 KB for the Thai probes) keeps
  GDEF, GPOS and GSUB and produces the same shaped signature as the full face.

**What the tell attests:** the face's layout tables fire on the probe — the same standard gate 18
applies to conjuncts ("has usable GSUB"). It does not attest that every mark in a document lands
right. Lao is unmeasured: no face is fetched. Measure before claiming.

## 4. Tasks, in order

### Task A — the per-document report (v51)

**Goal.** Every outcome `verify` prints, with its *where*, as a machine-readable artifact the
product can show a customer and a support engineer can start from.

**Design.**

- `Finding(page, where, text)` — frozen dataclass in `verify.py`. `page` is 1-based or `None`;
  `where` names the thing (field name, font PostScript name, script, `lang`, a `U+XXXX` code
  point, `0.85x`); `text` is the run, caption, token or detail, untruncated (the console keeps its
  `[:10]` / `[:20]` limits; the report does not).
- `GateResult` gains `findings: tuple = ()` and `to_dict()`. `VerifyVerdict` gains `to_dict()`:

  ```json
  {"schema": 1, "version": "51", "original": "orig.pdf", "output": "out.pdf", "exit_code": 1,
   "gates": [{"name": "metadata", "status": "FAIL", "message": "lang",
              "findings": [{"page": null, "where": "lang",
                            "text": "translations.json asks for \"es\", output declares \"nothing\""}]}]}
  ```

- Which gate yields which findings (all of these are printed today, so this is plumbing):
  field-parity → (label, field name); opt-export-parity → (field, "old → new"); fill-roundtrip →
  field; extractable-text, ink-ratio, visible-text, arabic-letterforms → per page with the number;
  canonical-text → (U+XXXX NAME, count); conjunct-shaping → (font, the probe line, pages);
  leak-running → (page, phrase); leak-isolated → token; empty-targets, placement,
  shaped-actualtext, identifiers → the target string; button-captions, caption-width → (field,
  caption); override-markers → (contains, token); metadata → (what, detail); scaled-runs → (page,
  `ratio`x, key). `leak-scan` and `metadata-lang` carry no findings.
- CLI: `--report PATH` writes `verdict.to_dict()` as JSON, `ensure_ascii=False`, indent 1. Off by
  default: the documented stdout and exit codes do not change. `pipeline.py rebuild` passes
  `--report <work>/verify_report.json` (the work dir is the pipeline's, so this is not a new file
  beside the customer's PDF).
- CLI and library: `--fail-on-review` / `fail_on_review=True` → exit 1 when any gate is REVIEW and
  none is FAIL. Off by default. This is how an unattended product makes REVIEW visible at
  delivery without this repo choosing its policy.
- `qa_check`'s `QAVerdict.findings` already carry `kind`, `severity` and the text; leave it. The
  product merges the two.

**This is a new surface.** The JSON is the contract the product's customer-facing view will be
built on. Flag it to the operator before building so a design canvas can come first if wanted;
the schema above is the proposal.

**Acceptance (Rule 2 — observable, with a verify-by).**

1. A job whose mapping asks `lang: es` and whose output declares no language: `run_verify(...,
   translations=...)` returns gate `metadata` FAIL with exactly one finding, `where == 'lang'`.
2. A job with a translated pushbutton caption wider than its widget: gate `caption-width` FAIL
   with a finding whose `where` is the field name and whose `text` is the caption.
3. A job with 35 missing placement targets: the console prints 30 (its `[:30]` limit); the report
   carries all 35.
4. `--report R.json` on any job: `R.json["gates"]` equals `[g.to_dict() for g in verdict.gates]`
   and the console output is byte-identical to the same run without the flag (extend
   `dev/probes/verdict_parity_runner.py`).
5. `--fail-on-review` on a job that prints REVIEW and no FAIL exits 1; without it, 0.
6. Every gate in `GATE_NAMES` that prints an itemised line has at least one test asserting a
   finding's `where` and `text`. Verify by `python -m unittest tests.test_verify_report` from
   `pdf-translate/`, written first and watched to fail.
7. Full suite as CI runs it green; `git diff --check` clean; version 51 in the three files;
   `references/gates.md` "As a library" section documents `Finding`, `--report`,
   `--fail-on-review`; a `docs/DECISIONS.md` row.

Effort: about a day. No rendering change, so Rule 1 verification is not required; the parity diff
is the evidence.

### Task B — REVIEW hygiene (inside task A's version)

- `REVIEW isolated source-script tokens: none` becomes `PASS isolated source-script tokens: none`
  (console and verdict). One deliberate wording change, named in the DECISIONS row and the PR.
- `references/gates.md` "As a library": say plainly which REVIEWs a consumer eliminates by always
  passing `lang` and by building faces with `prepare_font`.

### Task C — Thai (and Lao) join gate 18 through the mark-layout tell (parked 2026-09-16; v52 became the kinsoku gate — see docs/reviews/2026-09-16-cjk-request-assessment.md)

**Design.** `shaping_probe` gains a second kind of probe: `MarkProbe(script, text, note)` judged
by *signature* — `shaped_signature != naive_signature`, both arms drawn by the expected face. PASS
when they differ; FAIL when identical ("the face has no Thai layout tables; tone marks collide
with the consonant or sit on the vowel"); the count tell stays for conjunct scripts. Thai rows:
กิ่ and ปู่ (positions and ids move) and ป้า (ids only). Both `prepare_font` and `verify` hooks
already iterate `PROBE_FOR[script]`; extend them to the new kind. Thai leaves `BLIND_SCRIPTS`.

**Lao** stays REVIEW until a face is fetched (`tools/fetch_test_fonts.py`: Noto Sans Lao, OFL),
the probe is measured with the same script, and a row is recorded. Do not infer Lao from Thai.

**Acceptance.** The measured table in §3 reproduced by `tests/test_shaping_probe.py`; a real red
run: `prepare_font` on a Thai face with GSUB and GPOS deleted exits 1, `pipeline.py rebuild` with
that face fails `verify` on gate 18 while gate 17 still prints PASS; the real face passes both;
600 dpi renders of both outputs described in the evidence doc. **Rule 1 applies** (shaping): an
independent pass on another model re-runs the table, the red and green runs, and looks at the
renders. DECISIONS rows: Thai probed by signature (reverses "Thai stays REVIEW; no probe", whose
reversal condition was a *count* tell — this is not one, say so); Lao unmeasured.

Effort: half a day plus the verifier.

### Task D — Hebrew with niqqud: shape it, then attest it (v53, low priority)

Today `retypeset` keeps Hebrew on TextWriter ("only needs direction", `retypeset.py:162`) and gate
17's `needs_shaping` excludes it, so niqqud is never shaped and gate 18 says REVIEW. Measured:
readable anyway with Noto Sans Hebrew; the Story engine is 1–2 pt better. Font-dependent.

**Design.** Route a Hebrew target through the Story engine *when it contains combining marks*
(U+0591–U+05C7); plain Hebrew stays on TextWriter (its leaders, mirroring and RTL tests exist and
must not move). Extend `needs_shaping` the same way so gate 17 covers it. Then a `MarkProbe` for
Hebrew (שָׁלוֹם) judged by signature. Rule 1 applies: it is a rendering change.

Do this after C. If the product has no Hebrew-with-niqqud demand, park it with a `PARKED` note.

### Task E — the eight unmeasured conjunct scripts

Gujarati, Gurmukhi, Oriya, Telugu, Kannada, Malayalam, Sinhala, Tibetan print REVIEW. For each:
fetch a Noto face, find a cluster that loses glyphs (`dev/probes/measure_shaping_tell.py`), record
the row in `PROBES` and `AGENTS.md`'s measured table, DECISIONS row. Rule 1 applies. Only worth
doing for scripts the product will target; ask which before fetching eight faces.

### Task F — the spaceless leak scan (zh→ja): a design experiment first

When source and output share a spaceless family the scan cannot tell them apart and prints one
REVIEW. With `--source-words-from segments.json` the exact source strings are known: a source
segment's text found verbatim in the output while its mapped target differs is a leak, whatever
the script. Measure first: build a ja→zh job, leave one segment untranslated, and show the rule
finds it and does not flag a segment whose translation legitimately equals its source (numbers,
names). Only then design the gate. Not a rendering change.

### The production loop, honestly

Every FAIL or REVIEW the product sees in the wild is a real document exercising a real weakness.
It is **not** a corpus case for free: the corpus holds constructed PDFs and their verdicts, and a
customer's document cannot be committed. The loop is: the product keeps the report (task A) and
the segments; an agent builds a *constructed* minimal reproduction the way every existing corpus
PDF was built; the case and its recorded verdict land in `corpus/` with a README line. Budget
that per finding.

## 5. Not doing, on purpose

- **No plausibility judge.** An LLM asked "does this render look right?" says yes. Nobody here
  can eyeball Khmer, and a grader that can be fooled launders an unknown into a green check.
- **No breadth for its own sake.** A script joins the gates when it has a probe with a measured
  red case, not before.
- **No code from the product repo** (`C:\Dev\pdf-translator`, AGPL-bound; this repo is MIT).
- **No merge, push or delete by the agent.** Report and wait.

## 6. Hand back

For each task: the evidence doc under `docs/reviews/`, the DECISIONS rows, the PR link, the
suite line, and — where Rule 1 applies — the verifier's report beside it.
