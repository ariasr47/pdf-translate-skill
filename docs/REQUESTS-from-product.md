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

## How work arrives here — 24 September 2026

The product directs this library and assigns its work (`AGENTS.md` Rule 4,
`docs/DECISIONS.md` 2026-09-24). New work reaches this library as a row in
this file, with:

- a stable ID;
- one owner;
- the behaviour wanted;
- how acceptance is observed.

This repo may add findings or proposals here for the product to decide on,
and records here what it delivered: PR, version and evidence.

Sessions on both sides also message each other directly while they run.
Claude sessions do this by name with `SendMessage`; other agents go through
Rodrigo. Whatever a message settles is written into this file in the same
session.

## Current coordination status — 24 September 2026

**Main is v61 at `0542dc2`.** Since the 23 September status below, PRs #23
(the old B1 checkout reconciled; B1 stays deferred), #24 (A02) and #25 (A06,
with the bump to v61) have merged; #26 added handover notes, and #27
delivered GOV-2026-09-24 (the row at the bottom), docs only. All four
version sources say 61, CI passed on `0542dc2` (run 35981365585), and there
is no release or tag. For a consumer, v61 changes two things:

- **A02, page parity.** Every verify run prints one `page parity` line, and a
  missing, extra, rotated or resized page FAILs the new `page-parity` gate.
  `compare` and `render` show every page and exit 1 when the page counts
  differ; `finish` returns compare's code. Evidence:
  [a02-page-parity](reviews/2026-09-23-a02-page-parity.md).
- **A06, rebuild checks the mapping.** A default legacy `pipeline.py rebuild`
  verifies against the mapping it built from, so an empty target, a dropped
  marker or a translated identifier exits 1 where it used to exit 0.
  Evidence: [a06-rebuild-mapping-checks](reviews/2026-09-23-a06-rebuild-mapping-checks.md).

No consumer pin changed here; the app last reported v54.

**The product has the v61 notice.** On 24 September this library's session
sent it, with the question of what to prioritize, by `SendMessage` to the
app's session on the Mac. The app acknowledged v61 and keeps its pin at v54
(`9675c6196c14eb2a2d37d34e371391eb1955a386`) on Python 3.12. v61 requires
Python 3.14, so adopting it is an app migration, and none has been decided.

**Assigned: E12, priority 1 of 1** (the row at the bottom). Asked what to
prioritize, the app first answered that the priority was Rodrigo's call
and put the question to him. He ruled on 24 September (option C): the app's
pending work is N1, then N2 (beta hardening) and N3 (Next 16), then the
process-boundary migration, then N4 to N9. N1 and N3 need nothing from this
library. E4 and E5 serve the app's N6, which now comes after the migration.
The only library behaviour on the near path is N2's output size, so the one
assignment is E12, a compact, deterministic output save. Nothing else is
assigned, and Rodrigo directs library tech debt himself
(`docs/DECISIONS.md`, 2026-09-24). E12 is blocked before any build: the
measurement ([reviews/2026-09-24-e12-measurement.md](reviews/2026-09-24-e12-measurement.md))
found three of its acceptance checks in conflict, and six rulings are with
the product.

The 16 September sequence below ("E4–E7 in that order, E8–E11 in the gaps")
is no longer the order of record. The app reports that its own work-order
file said so in a status update of 19 September, and that its `ROADMAP.md`
§2 is canonical, with E12 recorded there too; neither file was opened here.
Of the 16 September rows, E2 and E3 have shipped although their status
cells below still read accepted: gates 19, 20 and 21 (PRs #6, #8 and #10,
v52 to v55) and the consumer surface (PR #13, v58; C7 moved to E8). E4 has
not started: no schema file for the verify report is published and its
gates carry no severity or category. E10 waits on the operator's choice of
distribution name.

**Proposed by this library; not assigned.** The app took these to Rodrigo in
the same pass, and his ruling left them unassigned. None of them has started:

- **A21**, the smallest backlog item: validate both manifests explicitly and
  give the type checker its declared environment. Two XS slices; see
  [PROGRAM.md](../dev/goals/PROGRAM.md#public-readiness-backlog).
- **A macOS test finding**, from setting this checkout up on a Mac. On
  `221a86f` the Mac ran CI's 695 tests with one failure:
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`
  compares `os.getcwd()` with the temporary path as strings
  (`tests/test_pipeline.py:3958`), and macOS reports `/var/…` as
  `/private/var/…`. Compared by `realpath`, the same run exits 0 and prints
  its PASS line, so the library is not at fault. CI runs Linux and Windows
  only. XS.
- **The open P1 audit items:** A04 (process-isolated concurrency
  validation), A05 (proven dependency floors) and A14 (review freshness,
  which needs a behaviour ruling first). A07 and A08 wait on owner
  decisions. The rest of the backlog is in PROGRAM.md.

## Coordination status — 23 September 2026 (historical snapshot)

**Main is v60 at `178a06f`.** Since the 20 September snapshot below, PRs
#12/#13 (v57/v58), #17 (typography, v59), #18 (Python 3.14 only), #19 (opt-in
refusal capture, v60), #20, #21 and #22 (A01 invalid-review refusal, A03
rebuild-report invalidation, cleanup) have all merged. PR #22 changed shipped
behaviour without a version bump, so `178a06f` and `b20fadd` both say v60; the
next integration picks the number. The app reports it still runs library v54 at
`9675c6196c14eb2a2d37d34e371391eb1955a386` on Python 3.12. Adopting current
main needs its own Python 3.14 migration and a same-input comparison, which the
app owns. No consumer pin or runtime changed here.

**B1 stays deferred.** The design is approved. The synthetic probe, the
baseline-anchor probe and the known-success capture are complete. No genuine
fit-refusal case exists, and none of that work is an implementation. Opt-in
refusal capture (v60) is how such a case would arrive.

**Next library work:** A02 (legacy page-count verification), then A06
(mapping-dependent checks on the default rebuild), each as a separate change
from main. `dev/goals/HANDOVER.md` has their state. Nothing here is a new
assignment to the app.

## Coordination status — 20 September 2026 (historical snapshot)

**Only B1 is deferred, not the product roadmap.** Its canvas and page-count
ruling are approved; the synthetic probe and real-job capture are complete.
The capture replayed a known success. Further B1 work awaits genuine fit-refusal
evidence and explicitly permitted boxes before testing wrapping. No B1 plan or
implementation is underway. See `dev/goals/HANDOVER.md` for the current evidence.

The v57/v58 work described below has open PRs #12/#13. A branch described as
"built" or "done" does not establish that the product has adopted it; consumer
adoption must cite its actual library version and pin. The captured form used
v54. Historical work orders below are not fresh assignments to another session.

**Typography adoption disposition, 20 September:** the app requested source
serif/sans class and meaningful within-line emphasis preservation without relaxing
its product requirement. No delivered documented API inspected satisfies both.
A same-source probe reproduces lost family/span information at the app-reported
v54 pin, main v56 and open-PR v58. Read the [bounded disposition](reviews/2026-09-20-typography-capability.md)
for existing manual controls, occurrence-selector limits and ownership. Rodrigo subsequently requested proceeding with the typography prerequisite.
Rodrigo approved the additive approach and subsequently the written
[typography design](design/typography-preservation/README.md). The
[implementation plan](plans/2026-09-20-typography-preservation-brief.md) now awaits
his review and execution-method choice; implementation has not started.
The disposition below remains evidence for the existing APIs. No implementation,
new consumer pin or wider app routing is promised.

**Audit follow-ups recorded 19 September:** the current library/skill backlog is
in [PROGRAM.md](../dev/goals/PROGRAM.md#public-readiness-backlog). Its A-IDs are
scoped follow-ups to the existing work, not a second product roadmap:

- E1/C4's earlier fixes do not cover a stale successful PDF/report after rebuild
  refuses before verification; see **A03**.
- C5's stdout-isolation fix does not establish native-backend thread safety.
  **A04** is partial: the library guidance now requires separate processes and
  job directories; process-isolated validation is still open. See the
  [20 September wording evidence](reviews/2026-09-20-concurrency-guidance.md).
  Worker integration remains app-owned and has not been inspected or reassigned
  here. The historical thread-pool request below is not current guidance.
- C3's general serialization/immutability promise needs qualification for QA and
  nested collections; see **A12**, coordinated with E4.
- C8/E11's dependency support needs an actually proven lower bound; see **A05**.
- E10 remains the home for package identity, licenses and release contents;
  see **A07/A08/A13/A20**, rather than duplicating that epic.

The audit is [local reproduced evidence](reviews/2026-09-19-public-readiness.md),
not a new product-side report or implementation authorization. Current status
and closing checks live in PROGRAM; the historical rows below are preserved.

## Ownership split — approved by Rodrigo

| Responsibility | Accountable owner |
| --- | --- |
| Final priorities, scope changes, and product tradeoffs | Rodrigo |
| Product roadmap, user outcomes, app/service work, integration, and real-job evidence | PDF Translator app task |
| Shared PDF engine, reusable API, rendering behavior, and library tests | This library task/repository |

The app task maintains **one existing product roadmap**, linking engine
requests into this inbox rather than creating a second implementation queue.
This inbox records library requests and technical delivery status; it does not
compete with the product's priority order. The app imports the shared library.
Product-specific UI and orchestration remain in the app.

To prevent duplicate work, each cross-repository item needs a stable ID, one
implementation owner per component, current state, blocking dependency, and a
link to its evidence/PR and required library pin. Each task checks that entry
before starting and updates its owned status when handing work back. A changed
priority or conflicting requirement returns to Rodrigo rather than being
silently resolved differently in each repository.

**Coordination complete:** Rodrigo selected A, adopting this split and
authorizing the message to **Boot Spire Tech web app**
(`01a0bc1c-cdb2-7b93-8860-0154a450beb4`). The app task confirmed that its existing
roadmap and companion status documents now record the alignment. Its reported
canonical roadmap is
`C:/Dev/pdf-translator/.spire/clusters/tech/context/ROADMAP.md`.
That file was not opened here; this records the owning task's confirmation.

**App-reported status, 20 September:** N1's seven approved screenshot-reference updates
are complete, with fresh independent verification of **331/331, zero skips**.
This does not close all of N1: the known frontend baseline and historical
process records remain separate closure obligations.

The next available product action is **app-owned preparation of a reviewable
CI authentication arrangement for the private library dependency**. Credential
provisioning and push/merge/deploy remain operator-controlled. This is a status
snapshot from the owning task, not an assignment or authorization for the
library task to perform that work. No new library implementation is assigned.

<details>
<summary>Technical detail (skip freely)</summary>

The app reports that the roadmap's opening ownership note and section 2
component register include stable IDs, one implementation owner per component,
state, blocking dependencies, evidence/PR pointers and adoption pins. Companion
records are `PROJECT_CONTEXT.md` and `INDEX.md` in the same context directory,
plus `C:/Dev/pdf-translator/docs/reference/WORKORDER-skill-2026-09-16.md`.
These paths are provenance only; no product files were inspected here.

No unresolved duplicate implementation assignment was identified in the app's
bounded alignment. Historical N2 save/subset and N6/E5 wording that assigned
reusable rendering behavior to the product is superseded: the library owns
reusable behavior/rendering; the app owns integration, product policy and
evidence. New priority or scope conflicts return to Rodrigo.

The app reports adoption remains `pdf-translate 54.0.0`, pinned at
`9675c6196c14eb2a2d37d34e371391eb1955a386`. B1 alone remains deferred. No library
files, pin, PRs #12/#13, push, merge, or implementation assignment changed in
this documentation alignment. This repo independently rechecked #12/#13 open
with unchanged heads; product-side file contents and deployment were not
independently inspected.

</details>

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
| 2026-09-16 | **E3 — step-2 readiness (C1–C10).** Every stage callable as a function per C1; results per C3; progress and cancellation per C4; concurrency per C5; determinism per C7; no network per C9; logging per C10; a consumer guide in `references/` that an engineer with zero context follows to run one document end to end from Python and read every output file. Acceptance: `tests/test_consumer_contract.py` — one document through every stage as function calls with stdout captured empty; two concurrent jobs; a cancel between pages leaving no file; sha256 determinism; a fixed-timestamp option; the eleven CLIs byte-identical (parity runner). Rule 1 for anything touching drawing, not for plumbing. | The product's step-2 council needs a library a service can call; weeks, not days. | **accepted** — after E2; about a week; the product writes its step-2 brief against the consumer guide meanwhile. From its PR review of 2026-09-16: the consumer guide must state the BCP 47 requirement for `lang` near the top with an explicit "not a display name" example, and name the reference font files the Han-forms gate needs (`NotoSansJP-VF.ttf`, `NotoSansSC-VF.ttf`) and what the gate does when they are absent. Design pass done 2026-09-18 (`docs/design/E3-consumer-surface/`, eight artboards, measured against v56). **C7 moves to E8** on that pass's sizing: E3 as filed is 8.5–9.5 days against the week accepted, and determinism is the one item whose size is unknown until a probe runs; E8's own acceptance already reads "the C7 determinism test gates", so the implementation belongs beside it. Without C7, E3 is ~7 days. Both PR-review asks are already satisfied elsewhere and the guide will point rather than re-derive: `references/translations-format.md` states the BCP 47 rule with the "not a display name" example, `references/fonts.md` names both faces and the absent-face behaviour. |
| 2026-09-16 | **E4 — findings to product notices.** One combined, versioned report: the verify report's JSON schema published as a file in the repo, versioned by `schema`; `qa_check`'s findings folded into the same envelope (or a sibling with the same envelope); each gate carries a machine-readable severity (`blocks-delivery` / `needs-attention` / `advisory` / `informational`), a category (`structure` / `layout` / `text` / `metadata` / `script`) and a `consumer-eliminable` flag (`metadata-lang`, cannot-attest); REVIEW gates always carry a finding (true since 1f42204; keep the invariant test). Acceptance: the schema file validates every report the suite writes (jsonschema in the test); a gate → severity/category table in `gates.md`; a schema bump rule in DECISIONS. | The product maps gate names to its closed notice codes without reading Python. | **accepted** — after E3; 1–2 days. |
| 2026-09-16 | **E5 — the compliance notice as data, and a placement call.** Reviewed notice strings for the 13 languages in R3, both variants ("file the official version" and "unofficial translation"), with the `{form title}` slot, each marked native-checked or not (never present unchecked as checked); a placement routine that, given the page and the notice, places it in existing room (foot of page 1, margin) at a readable size, never shrinks the form's own text, never adds a page, and returns whether it fit, where, and at what size — "did not fit" is a finding, not a silent drop; a verify line that the notice is present and readable (ink + text layer) when the mapping declares one. Rule 1 (drawing). | Official-looking copies of official forms need the page-1 notice from `references/compliance.md` without an LLM authoring legal text at run time. | **accepted** — after E4; 2–3 days plus reviewers. This repo can author and place the strings and will mark every one unchecked; native review is outside it and stays with the operator. Meanwhile the product ships the English wording translated by its protocol and flagged machine-translated. |
| 2026-09-16 | **E6 — fonts for a service.** `references/fonts.md`'s language → face table as machine-readable data with the OFL source and sha256 of each face; `prepare_font` takes a cache directory so instancing a variable TTF happens once per (face, charset), measured before/after on the Japanese eval; one subset per document, never per page, with a corpus ceiling (output bytes ≤ 2.5× input for text-only fixtures, measured ratios stated); `field_fonts` on by default for a form job and off for a non-form job, decided from the document, the decision in the strip/extract result. Rule 1. | A service applies a per-language face policy without a human choosing files. | **accepted** — after E5; 3–4 days. The product fixes its own per-page subsetting itself. **2026-09-24:** the "one subset per document, never per page" bullet moved to E12, which is assigned; the rest of this row stays accepted and unassigned. |
| 2026-09-16 | **E7 — hostile-input hardening.** Bounded wall-clock and memory per page on malformed input — deeply nested XObjects, recursive resource dictionaries, a 10,000-page skeleton, a 20,000 × 20,000 image, a broken xref PyMuPDF repairs, a stream inflating 1000× — each finishing or refusing within a stated ceiling, never hanging, each with a constructed fixture in `corpus/` and a recorded verdict; never execute or preserve document JavaScript or launch actions, with a per-item decision (stripped, kept or reported) for `/OpenAction`, `/AA`, `/JS`, `/Launch`, `/URI`, `/EmbeddedFiles` in DECISIONS; XFA removal kept; certified / Reader-extended handling documented as it is; a seeded fuzz smoke in CI gating on "did not hang or crash". Independent read of the decisions table. | A service receives strangers' PDFs; a skill received the user's own. The product bounds size (100 MB), pages (200) and refuses encrypted files before calling. | **accepted** — after E6; 3–5 days. |
| 2026-09-16 | **E8 — performance and determinism as a published number.** A benchmark script over the corpus printing per-stage wall-clock and output size per fixture; the numbers in a dated, machine-named table in docs; CI prints them and does not gate on them; the C7 determinism test gates. | Numbers a consumer can plan against. | **accepted** — in the gaps; 1 day. **Gains C7's implementation** (moved here from E3 on 2026-09-18): E8's acceptance already gated on the C7 determinism test, so the fixed-timestamp option and whatever the byte-diff probe finds now land beside the numbers rather than in E3. The probe ran on 2026-09-18 (`docs/BRIEF-determinism.md`) and the answer is small: only `/ID` varies, so C7 is a `doc_id=` parameter and a test, not an epic. **This row is back to about 1 day plus half a day for C7.** The caveat that stood here — determinism measured on a one-page job only — is **closed**: both named fixtures were run on 2026-09-18 and neither `choice_fields.pdf` (3 widgets) nor `dense_table.pdf` (25 cores) produces a second varying key, so the brief's design is sufficient and the sizing stands. E8's first red test is the one open question: that a caller-set `doc_id` survives `ez_save`. **2026-09-24:** E12 needs C7's caller-supplied `doc_id` at its save, so that question is now E12's; the benchmark stays here, unassigned. |
| 2026-09-16 | **E9 — the skill's own placement defects.** `docs/REVIEW-2026-09-04.md` F1 (a vertical rule is not an obstacle, so a cell's translation crosses the table border), F2 (a line takes its size from its first span, so a large bullet inflates a small line), F3 (a fixed pad shrinks a run for no reason). Rule 1. | Named so the skill knows the product will not contribute code for them (R6); the corpus already shows each. | **accepted** — this repo's own order and way. |
| 2026-09-16 | **E10 — packaging and release.** A distribution name before the first publish (`pdf-translate` is taken on PyPI as of 2026-09-16; `pdftranslate`, `pdf-translate-skill`, `pdf-translate-core` were free; the import name stays `pdf_translate`); SPDX `license = "MIT"` (the table form is deprecated); wheels built in CI on a tag; a CHANGELOG, one line per version, what changed for a consumer; version semantics written down (a new gate line is additive; a schema bump is breaking; a console change is a note); the four-way lockstep kept. | The product pins an exact version and needs to know what a bump means without reading every diff. | **accepted** — 1 day once the operator picks the name; the name is the operator's call. |
| 2026-09-16 | **E11 — corpus and evals as the shared oracle.** A stable `verdicts.json` schema; a runner that exits non-zero on any drift from recorded verdicts and prints the diff; fixtures generated, not committed; the three evals runnable headless with a documented expected-files check; a coverage matrix in docs — which of the 13 languages × {form, non-form} has a corpus case and which does not; `evals/permission-slip-japanese` kept working. | The product pins the version and runs this corpus in its CI as the step-2 acceptance oracle. | **accepted** — 1–2 days. Today `corpus/verdicts.json` is a flat file → verdict map with no version field (see C8). |
| 2026-09-16 | **C1 — stages callable without a CLI.** strip → extract → [the product authors the mapping] → prepare_font → retypeset → verify → field_fonts, each a function taking explicit paths or bytes and returning data, raising a typed exception on refusal; no argv parsing, no printing unless asked, no `sys.exit`, no dependence on the working directory, no reading of files the caller did not name. | Step-2 acceptance. | **open** (E3). Today: `pdf_translate` exports a function per stage; `run_verify` and `run_qa` are silent and return verdicts; the others return exit codes and print (`prepare_font` 10 print sites, `retypeset` 32, `extract_segments` 11, `strip_text` 2); no stage calls `sys.exit` or `os.chdir`; only the CLI `main()`s parse argv. **done** — v58, branch `feat/consumer-surface`: each stage has a silent `run_*` twin taking explicit paths, returning a schema-versioned frozen result and raising a typed exception; nothing prints, nothing exits, nothing resolves against the working directory (`run_extract` requires `outdir`, `run_retypeset` takes `resource_root=` defaulting to the mapping's directory, and `Archive('.')` is gone from `retypeset` and `shaping_probe`). The bare names keep their exact signatures, printed bytes and return codes. `references/consumer-guide.md` is the document; every code block in it was run. |
| 2026-09-16 | **C2 — inputs.** The original PDF; a mapping exactly per `references/translations-format.md`; fonts prepared per target language by `prepare_font`; nothing else assumed present. | Step-2 acceptance. | **holds today** — `translations-format.md` is the contract; pinned by E3's contract test. |
| 2026-09-16 | **C3 — outputs, machine-readable and schema-versioned.** The translated PDF; the verify report (schema 1, with findings); `scale_report`; the extractor's warnings; a stage result for strip (what was removed: XFA, actions, counts). A consumer explains every outcome from these files alone. | Step-2 acceptance. | **open** (E3). Today: the verify report yes (schema 1 since v51); `scale_report.json` is written by retypeset without a schema field; the extractor's warnings and the strip result are printed, not returned. **done** — v58. Every stage returns a frozen dataclass whose `to_dict()` carries `schema` and `version` (`pdf_translate/results.py`), and every refusal is a typed exception carrying `refusals`: each refused item by kind, **with the core untruncated**. Corrects this row's earlier note that results were printed and not returned — `verify` and `qa_check` already returned verdicts; the other five did not, and now do. `scale_report.json` also gains the envelope and is written atomically. |
| 2026-09-16 | **C4 — progress and cancellation.** A caller learns "page n is done" during retypeset (callback or generator) and can stop between pages, leaving no partial file at the output path. | The product streams progress to a browser. | **open** (E3). Nothing today. **done** — v58. `run_retypeset(progress=, cancel=)`. `progress(done, total)` fires once per unit and the total is **pages plus merge jobs**, because retypeset runs two loops; `cancel()` is checked at the top of every unit in both. There is one save, at the end, so a cancelled run cannot leave a partial file — `RetypesetResult(cancelled=True, output=None)` and nothing at the path. |
| 2026-09-16 | **C5 — concurrency.** Several jobs at once in one process from a thread pool: no module-level mutable state, no `os.chdir`, no fixed temp names, no shared caches without a lock; documented; a test runs two jobs concurrently and both verify PASS. | Threads today, processes later. | **open** (E3). No `os.chdir` anywhere today; the Han-forms reference cache (E2) is written atomically with this in mind; the audit is E3's. **done** — v58, and it was a real defect, not a gap: `run_verify` was silent by `redirect_stdout(io.StringIO())`, which replaces the **process's** stdout, so one thread inside it silenced every other thread in the host. Now the gates log and no handler is attached. Two concurrent jobs both verify PASS; `scale_report=` lets each job name its own report instead of racing for a fixed name beside the output. |
| 2026-09-16 | **C6 — bounded resources on hostile input** past what the product bounds (100 MB, 200 pages, no encrypted files). | A service receives strangers' PDFs. | **open** (E7). |
| 2026-09-16 | **C7 — determinism.** Same inputs → byte-identical output PDF when the caller supplies a fixed timestamp (and `/ID` is derived from content or supplied). Verify-by: the corpus run twice, sha256 equal per output. | The product's goldens rest on it. | **open** (E8 — moved off E3 on 2026-09-18, since E8's acceptance already gated on this test and the size is unknown until a probe runs). Today `retypeset` sets metadata but has no fixed-timestamp option, and `apply_document_metadata` (`retypeset.py:354`) deliberately never touches `/ModDate`, `/CreationDate`, `/Producer` or `/ID`; `doc.ez_save(out)` (`retypeset.py:1387`) is called with no arguments. **Measured 2026-09-18** (`dev/probes/determinism_probe.py`, brief `docs/BRIEF-determinism.md`, PyMuPDF 1.28.2): on a one-page job, two runs differ in **`/ID` alone** — 29 bytes of 325,777. Content streams, the embedded font program and the `/Info` dates are already byte-identical, because `apply_document_metadata` carries the source's dates through rather than writing "now". The output path does not leak; the clock does, and only into `/ID`'s second element (the first is stable across five runs). **So no `timestamp=` parameter is needed**: C7 reduces to pinning or deriving that one value. Design in the brief §4 — a `doc_id=` parameter on the silent twin, no default, no derivation policy in the library. **Re-measured the same day on the two corpus fixtures the brief named**: `choice_fields.pdf` (3 form widgets) and `dense_table.pdf` (25 cores) both give the same answer — `/ID` element 2 alone, element 1 stable, no second key. Widgets and 25× the placement work add no varying byte, so the sizing holds. The path-does-not-leak claim was also re-derived properly: the first pass inferred it from two runs assumed simultaneous, which a clock tick can fake, so the probe now groups runs by `/ID` element 2 and compares only inside one tick (brief §2.2). One thing remains unmeasured and belongs in E8's first red test — whether MuPDF honours a caller-set `/ID` through `ez_save` at all. **2026-09-24:** E12 needs this `doc_id` at its save and answers that question. |
| 2026-09-16 | **C8 — versions.** Python `>=3.10` here (product 3.12); an exact skill pin; the PyMuPDF window as declared (`>=1.24,<1.30`); the PyMuPDF/MuPDF version each corpus verdict was recorded on stated; one version chosen deliberately at step 2. | The product's attestation is identity-locked. | **open** (E11), and the Python half changed. `pyproject.toml` declared `requires-python = ">=3.10"` when this row was written (confirmed 2026-09-16); since PR #18 on 2026-09-21 it declares **`>=3.14`**, matched by the `compatibility:` line, the README and a CI matrix that now tests 3.14 only. The row said "product 3.12"; the consumer has since reported measuring its own suite on CPython 3.14 — full dependency tree resolving with wheels for PyMuPDF and pikepdf, 990 passed and one failure that is its own deliberate 3.12 tripwire — and has said it does not need the 3.10-3.13 floor restored. That is the consumer's measurement, not one taken here. The rest of the row stands: `pymupdf>=1.24,<1.30` unchanged, this machine runs 1.28.2 and the product 1.28.0, and `verdicts.json` still carries no version field. |
| 2026-09-16 | **C9 — no network at runtime.** Fonts, reference faces and any lookup are files the caller provides; issuer lookup belongs to the agent workflow, never to the library. | A service. | **holds today** — no network import in `pdf_translate/` (grep, 2026-09-16); `tools/fetch_test_fonts.py` is a dev tool; the Han-forms gate takes a reference directory. |
| 2026-09-16 | **C10 — logging.** Through the `logging` module on the package's own logger, never `print`; nothing the library logs contains document text beyond what a finding already carries. | A service's logs. | **open** (E3). 166 `print` sites across the package modules today. **done** — v58. All 172 `print` sites in the package emit through `logging.getLogger('pdf_translate')` at INFO; one re-entrant `console()` attaches the single stdout handler at each CLI entry point; importing the package attaches only a `NullHandler` and sets no level on the root. Two structural tests keep it that way: no module calls `print`, and no `log.info` takes more than one argument (a two-argument call silently drops the record — it happened twice during the conversion). |
| 2026-09-18 | **Row 32 — the terminology loop** (this repo's own row, filed here because it changes a stage the product calls). `pipeline.py finish` now requires `--work DIR` and refuses while `review.json` is absent or any finding is `open`. | A wrong term of art passed every gate on the first FL-150 → ja job and reached a delivery; no gate can see one. | **done** — v57, branch `feat/terminology-loop`. **R5 is not breached and the CLI refusal does not reach the product.** `finish` is packaging, not building, so a refusal there would be a withholding by a non-build stage; the refusal is built for the person driving the CLI by hand, and for the product the load-bearing artefact is the **record**: `review_state.json` is written beside `FINAL.pdf` on every run, refused or not, carrying `schema`, `version`, `blocks_delivery`, the counts and the one `REVIEW` line — surfaceable without parsing console text. Nothing here deletes or withholds an output file that was built: the refusal happens before `field_fonts` runs, so no delivery is produced and then held back. A consumer driving the library calls `run_review(work, generate=False)` and decides for itself; a consumer driving the CLI and wanting today's behaviour passes `--no-review`, which delivers and marks the delivery. C10 (logging) is honoured for the two new commands ahead of E3: they emit through the package logger, and `import pdf_translate` attaches only a `NullHandler`. |

| 2026-09-18 | **The five bubbled items (B1–B5)**, each a measurement taken while integrating 54.0.0 (rev `9675c619`). B1: the library never breaks a line, so a long translation shrinks and below the floor is left untranslated. B2: the refusal report truncates the core to 40 characters. B3: refusals are printed, not returned. B4: widget text is not translated. B5: terminology quality is invisible to every gate. | Each one costs a customer something: untranslated text, a silent revert of 247 of 247 cores, a consumer's regex that stopped matching, form fields still in the source language, and a wrong legal term on a legal form. | **read and queued** — `docs/BRIEF-product-bubble-2026-09-18.md`. **B3 done (v58)**: every stage raises a typed exception carrying structured attributes and `refusals`. **B2 done for library consumers (v58)**: `refusals` carries every refused core **in full**; the printed line keeps its 40-character abbreviation deliberately, because it is read by a person and changing it breaks console parity — ask for that separately if it is wanted. **B5 built (v57)**: row 32's review loop, `references/terminology-failure-modes.md`, the per-class termbase and the canary's reviser axis (19% false-positive rate on the FL-150). **B4 open but contained**: the widget-text scaffold, the `/Opt` export-value rule and the refusal already exist in `extract_segments` and `strip_text`; what is missing is exposure on the consumer surface and a ruling on whether an unauthored scaffold should warn. **B1 design approved; further work deferred (19 September)**: exact page count, same-page placement, per-occurrence permission and a caller-authored fixed box. The synthetic probe and known-success real-job capture are complete; genuine fit-refusal evidence remains missing. No plan or implementation has begun. See `docs/design/B1-line-wrapping/README.md` and `docs/reviews/2026-09-19-b1-captured-case.md`. Correction to the original report: explicit merges already reflow and gate 19 is called; ordinary-line overflow is a build refusal, not automatic source-text restoration by the library. |

| 2026-09-20 | **Typography preservation for wider library adoption.** Preserve source serif-versus-sans class and meaningful within-line bold/italic distinctions; exact source font reuse is not required. Retain an unambiguous relationship between translated style runs and repeated source occurrences, and explicitly report unsupported/ambiguous cases. | The app reports v54 at `9675c6196c14eb2a2d37d34e371391eb1955a386`: ES/zh-Hans core placement succeeds on synthetic invoices, but mixed families and emphasized tails lose their distinctions. Its five compatibility failures remain app-owned and open. | **Written typography design approved; nine-stage implementation plan saved for review and execution-method choice. Code has not started.** Own-source fixture and AST comparison confirm flattened style flags and missing class/span records at v54, main v56 and open-PR v58, with no extraction warning. Existing four-role fonts, inline emphasis and substring overrides are narrower manual controls. See `docs/reviews/2026-09-20-typography-capability.md` for exact APIs/pins and the library/app ownership split. The app's typography promise is unchanged. The selected approach preserves legacy calls and adds explicit style/occurrence data. Approved first scope is horizontal, single-baseline Latin/Japanese/Simplified Chinese page text; unsupported cases refuse and remain ineligible for adoption under the unchanged promise. See [the written design](design/typography-preservation/README.md), saved locally in `ef52e5f`. Its detailed scope/API is approved; [the implementation plan](plans/2026-09-20-typography-preservation-brief.md) remains unapproved. No new pin or PR change. B1 remains separate and deferred. **Done — v59** (PR #17, merged 21 September): the capability ships as the opt-in `typography-1` mapping format and announces itself in `pdf_translate.MAPPING_FORMATS`; `references/typography.md` documents it. App adoption, routing and its five compatibility failures remain app-owned and are not verified here; the app reports v54. |

| 2026-09-24 | **GOV-2026-09-24 — the product directs this library.** The product sets this library's direction and assigns its work through this file; this repo reports findings and proposes, and builds and tests only what is assigned. Sessions on both sides message each other when a request, the state of work or a version changes, and every outcome is written here in the same session. The app's request file is `docs/reference/REQUEST-to-skill-app-direction-2026-09-24.md` at `a837961` in `pdf-translator`: provenance only, not opened here. | Rodrigo's ruling: one owner of direction and one queue of work, so the two repositories never keep competing roadmaps and nothing agreed in a chat is lost between sessions. | **done** — PR #27, merged 24 September as `0542dc2`: `AGENTS.md` Rule 4, the section "How work arrives here" above, a `CLAUDE.md` that imports `AGENTS.md`, and the `docs/DECISIONS.md` row of 2026-09-24. Docs only; the version stays 61. The ID is the app's, recorded here at its request so both sides name the request the same way. |

| 2026-09-24 | **E12 — a compact, deterministic output save.** A documented, reusable save that any caller can apply to a finished document, including one assembled from per-page parts. Its output: carries each face as exactly one embedded font program, subset once for the whole document; is written compactly, with unused and duplicate objects dropped and streams compressed; draws exactly the same pixels as its input; keeps every form field, its name and its value; is byte-identical across runs when the caller supplies the same `doc_id`. **Acceptance, observable:** (1) on this repo's corpus text-only fixtures, assembled from per-page parts as described, output bytes ≤ 2.5× input, with per-fixture ratios in a dated table; (2) each face appears as exactly one embedded font program per output document, counted in the file; (3) every page rasterised before and after the save at a pinned zoom gives `pixel_diff_ratio == 0.0`; (4) on a form fixture, the field count, names and values are equal before and after; (5) two runs with the same input and `doc_id` give equal sha256, and behaviour without a `doc_id` is documented; (6) checks 1 and 2 are shown red against the unfixed shape (per-part subsets, default save) before the change lands; (7) Rule 1 applies, the API is documented in `references/`, the version bumps, the app gets a notice, and the PR is Rodrigo's to merge. **Owner:** this library builds it; the app integrates it and owns its real-form size evidence. It takes over E6's "one subset per document, never per page" bullet and needs C7's caller-supplied `doc_id` at the save. It traces to the app's ROADMAP N2.output-save-flags. | A consumer that builds a document from per-page parts, each embedding the same faces, each subset on its own and each saved with default settings, delivers files about 6× the input size. The app measured one real government form at 184 KB in and 1,154 KB out: roughly 200 KB of that is a separate font subset per page, and roughly 700 KB is uncompacted structure. | **accepted** — priority 1 of 1, from Rodrigo's ruling of 24 September as relayed by the app's session; nothing else is assigned. No adoption pin: the app stays on v54 at `9675c6196c14eb2a2d37d34e371391eb1955a386` (Python 3.12) and adopts E12 only at its Python 3.14 migration, with an exact, reviewed pin. Delivery does not imply adoption. If E12 as written proves unbuildable or wrong for this code, this library stops and reports the measurement rather than substituting its own version. **Blocked, 2026-09-24, before any build.** The measurement is in [reviews/2026-09-24-e12-measurement.md](reviews/2026-09-24-e12-measurement.md). Checks 3–5 are buildable, with guards: MuPDF's `subset_fonts` flips two verify gates to REVIEW, and garbage 4 folds widgets that have no `/P`. Check 2 holds for page text, but on every delivered form it contradicts the standing full field face. Check 1 cannot hold on the three base-14 fixtures without dropping TrueType hinting, which breaks a strict check 3. Checks 1, 2 and 6 go red only on constructed multi-page fixtures, because every corpus fixture is one page. Six rulings are asked of the product; nothing is built until they are answered. The app acknowledged the block the same day and queued the rulings for Rodrigo after its N1, since E12 serves N2. Its library route opens the whole document once and never slices, so the `insert_pdf` widget loss does not reach it; the per-page route is the older engine that E12 serves. The app flagged the `/Rotate 90` blank-page finding in the review as a possible N1 risk, because its library route runs no verify. Nothing about it is assigned here. |

Add new rows at the bottom. Do not delete a row when its status changes —
update the status column in place so the history of what was asked for
stays readable.
