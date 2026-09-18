# Requests from product

This is the product repo's (`pdf-translator`) inbox to this skill. When the
product finds a behaviour here it wishes this library had, it goes in the
table below — not as a patch, not as a diff, not as pasted code.

**A request describes BEHAVIOUR. It never pastes code.** `pdf-translator` is
heading to AGPL-3.0; this repo is MIT. Code flows downstream from here to
there, never back — see `AGENTS.md`'s licence section. A request that
arrives as a code snippet, a diff, or "here's roughly how we did it" gets
rewritten as a behaviour description before anyone acts on it, or it gets
refused. Describe the input, the observable output, and why it matters;
this repo's own tests and corpus are what any implementation is checked
against.

## Format

`date | what the product needs | why | status`

- **date** — ISO, when the request was filed.
- **what the product needs** — a behaviour, stated as an outcome ("given X,
  produce Y"), not an implementation.
- **why** — the concrete case that surfaced the gap.
- **status** — `open`, `accepted` (being built independently here),
  `declined` (with a one-line reason), or `done` (with the version/commit
  that shipped it).

## The work order of 2026-09-16

The product's work order of 2026-09-16 is the request of record on its side
(its `OPEN_THREADS` §19). It arrived as behaviours and acceptance criteria,
no code. Its rulings are inputs to this repo, recorded here so no session
asks again:

- **R1** — 2d, missing glyph: refusal wins. A job whose face cannot draw a
  character is refused (what ships today); no placeholder glyph, no borrowed
  face.
- **R2** — Tasks C (Thai), D (Hebrew niqqud), E (eight Indic scripts):
  parked from the product's side; reversal condition "the product adds a
  target language in that script". The standalone skill may still do C.
- **R3** — Target languages sold today, the only ones step 2 must not
  regress: es pt fr de it pl ro tr vi uk ru zh-Hans ja. Next candidates on
  demand data: ar hi th. Faces: the Noto family, per language, shipped by
  the product.
- **R4** — The Han-forms gate: yes, as designed in
  `docs/reviews/2026-09-16-cjk-request-assessment.md` §3 item 3 — REVIEW
  when the probe characters are not drawn, when no reference face is
  available, or when neither control matches. The product ships both
  reference faces so PASS is reachable in production.
- **R5** — How the verdict is used: the product always passes `lang`,
  always builds faces with `prepare_font`, never sets `fail_on_review`;
  REVIEW is an advisory notice; a verify FAIL is a needs-attention notice
  **and the document is still delivered** — a verify FAIL must never delete
  or withhold the output file; only a build refusal (retypeset) withholds
  it, and build refusals map to job-fatal closed causes.
- **R6** — Obstacle-bounded placement: still not asked for. Publishing it
  under MIT needs an operator ruling first; nothing here builds toward it.

Answers on record (asked once, answered in the work order): the product runs
Python 3.12 (keep `>=3.10` here) and PyMuPDF 1.28.0 (this repo tests on
1.28.2; one version is chosen at step 2, not now); its LLM authors
`translations.json` through a structured protocol, including `merges.html`
and `notices`, no human; it consumes the verify report and `scale_report`
only — not compare HTML, bilingual output or the reviewer checklist; a "form
job" is one with AcroForm widgets or a class (court / government / medical)
the product decides — the library decides "has widgets"; threads today,
processes later, so no global state; customer PDFs are never sent as
fixtures — findings and constructed corpus cases are the loop; RTL stays in
the skill (excluded from the product's MVP, a product decision); urgency:
E1 now, E2 in flight, E3 before the product's step-2 council (weeks), E4–E7
in that order, E8–E11 in the gaps; the product reviews PRs read-only on
request and never merges.

The product reviewed this transcription read-only on 2026-09-16 (with PRs #6, #7 and #8): faithful, no MUST, NEVER or ALWAYS softened; two compressions it does not want changed — R1 omits "the product surfaces it as a closed cause", R4 omits "(non-Noto family)". Its verdicts: #7 adopt as is (E1 done); #6 adopt — its own engine lets the six small kana counters ゎ ゕ ゖ ヮ ヵ ヶ begin a line, so a REVIEW on one of them is a known difference (now stated in `references/gates.md`); #8 adopt — the product sets no `/Lang` and its pipeline holds display-name language values (`Japanese`, `日本語`), so normalising `lang` to a BCP 47 tag and shipping the two reference faces are its step-2 prerequisites; on its suggestion a `lang` that is not a tag is now REVIEW, not silence. The probe characters 直 骨 海 came from the product's request as behaviour, in words; the measurement and the gate are this repo's.

Not asked for: obstacle-bounded placement (R6), any code from the product
repo, a plausibility judge, breadth for its own sake, merging, pushing or
deleting anything.

## Requests

| date | what the product needs | why | status |
|---|---|---|---|
| 2026-09-16 | **E1 — the stale report.** After a passing run with `--report PATH` (or `pipeline.py rebuild`'s `<work>/verify_report.json`), an unwritable target, and a failing run to the same path, no report at the path claims `exit_code 0`: either no file, or one describing the failing run. The exit code and the `(could not write …)` line stay as they are. | PR #5 defect 1: the report on disk said PASS for a job that failed, attributed to a document the consumer did not ask about. | **done** — v53, branch `fix/stale-verify-report` (abbfbcb, 264b1ac), PR #7 stacked on #6: remove-before-run, temp file + `os.replace`, remove-on-failure; best effort where the directory itself cannot be written (`references/gates.md`, `docs/DECISIONS.md`); evidence `docs/reviews/2026-09-16-stale-verify-report.md`. |
| 2026-09-16 | **E2 — finish CJK parity.** The kinsoku gate on the drawn lines (PR #6 as-is); then the Han-forms gate per R4 with Rule 1 (a verifier on another model re-runs red — a Japanese job set with the SC face — and green, and looks at 600 dpi renders); then task F, the spaceless leak scan, measured first. Acceptance: three new gate lines, each shown red on a constructed job, each with findings; console parity on the nine non-CJK jobs. | The product sells ja and zh-Hans (R3) and has shipped its Japanese face and kinsoku on its side. | **accepted** — kinsoku shipped as gate 19 (REVIEW) in v52, PR #6 open and green; the Han-forms gate is measured (`docs/BRIEF-han-forms-gate.md`, `dev/probes/han_forms_probe.py`) and built as gate 20, v54, on `feat/han-forms-gate` (plan `docs/plans/2026-09-16-han-forms-gate.md`, evidence `docs/reviews/2026-09-16-han-forms-gate.md`: 45 tests, suite 368, console parity identical, an Opus whole-branch review with two fix waves, Rule 1 verified by an independent pass) — merged 2026-09-16 (PR #8); task F built as gate 21 `leak-cjk` (v55, `feat/cjk-leak-tell`, measured in `docs/BRIEF-cjk-leak-tell.md`: the verbatim rule is blind to an echo, a repertoire tell is not) — push and PR are the operator's. |
| 2026-09-16 | **E3 — step-2 readiness (C1–C10).** Every stage callable as a function per C1; results per C3; progress and cancellation per C4; concurrency per C5; determinism per C7; no network per C9; logging per C10; a consumer guide in `references/` that an engineer with zero context follows to run one document end to end from Python and read every output file. Acceptance: `tests/test_consumer_contract.py` — one document through every stage as function calls with stdout captured empty; two concurrent jobs; a cancel between pages leaving no file; sha256 determinism; a fixed-timestamp option; the eleven CLIs byte-identical (parity runner). Rule 1 for anything touching drawing, not for plumbing. | The product's step-2 council needs a library a service can call; weeks, not days. | **accepted** — after E2; about a week; the product writes its step-2 brief against the consumer guide meanwhile. From its PR review of 2026-09-16: the consumer guide must state the BCP 47 requirement for `lang` near the top with an explicit "not a display name" example, and name the reference font files the Han-forms gate needs (`NotoSansJP-VF.ttf`, `NotoSansSC-VF.ttf`) and what the gate does when they are absent. |
| 2026-09-16 | **E4 — findings to product notices.** One combined, versioned report: the verify report's JSON schema published as a file in the repo, versioned by `schema`; `qa_check`'s findings folded into the same envelope (or a sibling with the same envelope); each gate carries a machine-readable severity (`blocks-delivery` / `needs-attention` / `advisory` / `informational`), a category (`structure` / `layout` / `text` / `metadata` / `script`) and a `consumer-eliminable` flag (`metadata-lang`, cannot-attest); REVIEW gates always carry a finding (true since 1f42204; keep the invariant test). Acceptance: the schema file validates every report the suite writes (jsonschema in the test); a gate → severity/category table in `gates.md`; a schema bump rule in DECISIONS. | The product maps gate names to its closed notice codes without reading Python. | **accepted** — after E3; 1–2 days. |
| 2026-09-16 | **E5 — the compliance notice as data, and a placement call.** Reviewed notice strings for the 13 languages in R3, both variants ("file the official version" and "unofficial translation"), with the `{form title}` slot, each marked native-checked or not (never present unchecked as checked); a placement routine that, given the page and the notice, places it in existing room (foot of page 1, margin) at a readable size, never shrinks the form's own text, never adds a page, and returns whether it fit, where, and at what size — "did not fit" is a finding, not a silent drop; a verify line that the notice is present and readable (ink + text layer) when the mapping declares one. Rule 1 (drawing). | Official-looking copies of official forms need the page-1 notice from `references/compliance.md` without an LLM authoring legal text at run time. | **accepted** — after E4; 2–3 days plus reviewers. This repo can author and place the strings and will mark every one unchecked; native review is outside it and stays with the operator. Meanwhile the product ships the English wording translated by its protocol and flagged machine-translated. |
| 2026-09-16 | **E6 — fonts for a service.** `references/fonts.md`'s language → face table as machine-readable data with the OFL source and sha256 of each face; `prepare_font` takes a cache directory so instancing a variable TTF happens once per (face, charset), measured before/after on the Japanese eval; one subset per document, never per page, with a corpus ceiling (output bytes ≤ 2.5× input for text-only fixtures, measured ratios stated); `field_fonts` on by default for a form job and off for a non-form job, decided from the document, the decision in the strip/extract result. Rule 1. | A service applies a per-language face policy without a human choosing files. | **accepted** — after E5; 3–4 days. The product fixes its own per-page subsetting itself. |
| 2026-09-16 | **E7 — hostile-input hardening.** Bounded wall-clock and memory per page on malformed input — deeply nested XObjects, recursive resource dictionaries, a 10,000-page skeleton, a 20,000 × 20,000 image, a broken xref PyMuPDF repairs, a stream inflating 1000× — each finishing or refusing within a stated ceiling, never hanging, each with a constructed fixture in `corpus/` and a recorded verdict; never execute or preserve document JavaScript or launch actions, with a per-item decision (stripped, kept or reported) for `/OpenAction`, `/AA`, `/JS`, `/Launch`, `/URI`, `/EmbeddedFiles` in DECISIONS; XFA removal kept; certified / Reader-extended handling documented as it is; a seeded fuzz smoke in CI gating on "did not hang or crash". Independent read of the decisions table. | A service receives strangers' PDFs; a skill received the user's own. The product bounds size (100 MB), pages (200) and refuses encrypted files before calling. | **accepted** — after E6; 3–5 days. |
| 2026-09-16 | **E8 — performance and determinism as a published number.** A benchmark script over the corpus printing per-stage wall-clock and output size per fixture; the numbers in a dated, machine-named table in docs; CI prints them and does not gate on them; the C7 determinism test gates. | Numbers a consumer can plan against. | **accepted** — in the gaps; 1 day. |
| 2026-09-16 | **E9 — the skill's own placement defects.** `docs/REVIEW-2026-09-04.md` F1 (a vertical rule is not an obstacle, so a cell's translation crosses the table border), F2 (a line takes its size from its first span, so a large bullet inflates a small line), F3 (a fixed pad shrinks a run for no reason). Rule 1. | Named so the skill knows the product will not contribute code for them (R6); the corpus already shows each. | **accepted** — this repo's own order and way. |
| 2026-09-16 | **E10 — packaging and release.** A distribution name before the first publish (`pdf-translate` is taken on PyPI as of 2026-09-16; `pdftranslate`, `pdf-translate-skill`, `pdf-translate-core` were free; the import name stays `pdf_translate`); SPDX `license = "MIT"` (the table form is deprecated); wheels built in CI on a tag; a CHANGELOG, one line per version, what changed for a consumer; version semantics written down (a new gate line is additive; a schema bump is breaking; a console change is a note); the four-way lockstep kept. | The product pins an exact version and needs to know what a bump means without reading every diff. | **accepted** — 1 day once the operator picks the name; the name is the operator's call. |
| 2026-09-16 | **E11 — corpus and evals as the shared oracle.** A stable `verdicts.json` schema; a runner that exits non-zero on any drift from recorded verdicts and prints the diff; fixtures generated, not committed; the three evals runnable headless with a documented expected-files check; a coverage matrix in docs — which of the 13 languages × {form, non-form} has a corpus case and which does not; `evals/permission-slip-japanese` kept working. | The product pins the version and runs this corpus in its CI as the step-2 acceptance oracle. | **accepted** — 1–2 days. Today `corpus/verdicts.json` is a flat file → verdict map with no version field (see C8). |
| 2026-09-16 | **C1 — stages callable without a CLI.** strip → extract → [the product authors the mapping] → prepare_font → retypeset → verify → field_fonts, each a function taking explicit paths or bytes and returning data, raising a typed exception on refusal; no argv parsing, no printing unless asked, no `sys.exit`, no dependence on the working directory, no reading of files the caller did not name. | Step-2 acceptance. | **open** (E3). Today: `pdf_translate` exports a function per stage; `run_verify` and `run_qa` are silent and return verdicts; the others return exit codes and print (`prepare_font` 10 print sites, `retypeset` 32, `extract_segments` 11, `strip_text` 2); no stage calls `sys.exit` or `os.chdir`; only the CLI `main()`s parse argv. |
| 2026-09-16 | **C2 — inputs.** The original PDF; a mapping exactly per `references/translations-format.md`; fonts prepared per target language by `prepare_font`; nothing else assumed present. | Step-2 acceptance. | **holds today** — `translations-format.md` is the contract; pinned by E3's contract test. |
| 2026-09-16 | **C3 — outputs, machine-readable and schema-versioned.** The translated PDF; the verify report (schema 1, with findings); `scale_report`; the extractor's warnings; a stage result for strip (what was removed: XFA, actions, counts). A consumer explains every outcome from these files alone. | Step-2 acceptance. | **open** (E3). Today: the verify report yes (schema 1 since v51); `scale_report.json` is written by retypeset without a schema field; the extractor's warnings and the strip result are printed, not returned. |
| 2026-09-16 | **C4 — progress and cancellation.** A caller learns "page n is done" during retypeset (callback or generator) and can stop between pages, leaving no partial file at the output path. | The product streams progress to a browser. | **open** (E3). Nothing today. |
| 2026-09-16 | **C5 — concurrency.** Several jobs at once in one process from a thread pool: no module-level mutable state, no `os.chdir`, no fixed temp names, no shared caches without a lock; documented; a test runs two jobs concurrently and both verify PASS. | Threads today, processes later. | **open** (E3). No `os.chdir` anywhere today; the Han-forms reference cache (E2) is written atomically with this in mind; the audit is E3's. |
| 2026-09-16 | **C6 — bounded resources on hostile input** past what the product bounds (100 MB, 200 pages, no encrypted files). | A service receives strangers' PDFs. | **open** (E7). |
| 2026-09-16 | **C7 — determinism.** Same inputs → byte-identical output PDF when the caller supplies a fixed timestamp (and `/ID` is derived from content or supplied). Verify-by: the corpus run twice, sha256 equal per output. | The product's goldens rest on it. | **open** (E3, E8). Today retypeset sets metadata but has no fixed-timestamp option; unmeasured. |
| 2026-09-16 | **C8 — versions.** Python `>=3.10` here (product 3.12); an exact skill pin; the PyMuPDF window as declared (`>=1.24,<1.30`); the PyMuPDF/MuPDF version each corpus verdict was recorded on stated; one version chosen deliberately at step 2. | The product's attestation is identity-locked. | **open** (E11). `pyproject.toml` declares `requires-python = ">=3.10"` and `pymupdf>=1.24,<1.30` (confirmed 2026-09-16); this machine runs 1.28.2, the product 1.28.0; `verdicts.json` carries no version field. |
| 2026-09-16 | **C9 — no network at runtime.** Fonts, reference faces and any lookup are files the caller provides; issuer lookup belongs to the agent workflow, never to the library. | A service. | **holds today** — no network import in `pdf_translate/` (grep, 2026-09-16); `tools/fetch_test_fonts.py` is a dev tool; the Han-forms gate takes a reference directory. |
| 2026-09-16 | **C10 — logging.** Through the `logging` module on the package's own logger, never `print`; nothing the library logs contains document text beyond what a finding already carries. | A service's logs. | **open** (E3). 166 `print` sites across the package modules today. |

Add new rows at the bottom. Do not delete a row when its status changes —
update the status column in place so the history of what was asked for
stays readable.
