# How this skill keeps improving

The north star is unbounded. A `/goal` session is not. Each session is **one
turn of the loop**, with a closed done bar, a named corpus, and explicit
non-goals. When it ends, the skill is strictly better on a measurable class
of failures — or it refused honestly. Then you pick the next row.

## Public readiness backlog

**Current update: 23 September 2026.** This section is the current
library/skill backlog for the findings of the
[dual-use audit](../../docs/reviews/2026-09-19-public-readiness.md), groomed on
19–20 September at Rodrigo's request. Earlier dated queues below retain their
historical meaning; their “only item left” or “first” statements are not
today's work order. The HTML checklist is a historical view. **Since the
grooming:** A01 and A03 merged in PR #22 (main `178a06f`). The A04 and A15
documentation slices were written in the unmerged `codex/b1-design-canvas`
checkout and carried to the local branch `chore/reconcile-b1-checkout` on 23
September. A02 and A06 were then built as separate changes
from main. All three merged as v61 (PRs #23, #24 and #25).

The [smallest-items shortlist](../../docs/PUBLIC-READINESS-QUICK-WINS-2026-09-19.md)
is a dated reading aid, not a second status tracker. **A04 and A15 have
completed small documentation slices; their broader items remain open. A01,
A02, A03 and A06 are done.** Rows not marked otherwise remain unstarted.
Sizes and proposed
priorities are estimates; scheduling and behavior decisions remain Rodrigo's.
Adding a row does not authorize a PR edit, push, merge, or app-task assignment.

Evidence baseline of the audit: reviewed v58 `1d4f970`, when remote main was v56
`a5629fb`. Main is now v60 at `178a06f`; recheck a finding against current main
before implementing it. B1 remains deferred for real failed-job evidence; none of
these rows authorizes wrapping or changes its approved design.

**Ownership:** this repo owns engine, reusable API, skill, packaging and library
documentation. The app owns its worker integration, service controls and product
roadmap. Existing E/C/P/32 IDs are linked parents, not duplicate implementation
assignments. `A01`–`A26` below identify scoped audit follow-ups. Audit `R1`–`R13`
are finding IDs, distinct from the product's similarly named policy rulings.

**Priority:** P1 = resolve before the affected public/production claim;
P2 = reliability or public usability; P3 = maintainability. **Size:** XS = one
focused edit with a local check; S = a bounded change with targeted verification;
M = several stages/artifacts or new measurement; L = broad refactoring/hardening.
Sizes include verification, but exclude operator decisions and hosted-CI delays.
“Open” means recorded, not started. A documentation subtask never closes a larger
behavior item on its own.

### Correctness and release identity

| ID / priority | Existing home / current state | Scope and estimated size | Observable completion and verify-by |
| --- | --- | --- | --- |
| **A01 · P1** | Row 32; **done — PR #22, merged 23 September (`178a06f`)**; [evidence](../../docs/reviews/2026-09-22-a01-invalid-review-refusal.md). Audit R1. | **Reject invalid review state at delivery. S.** Preserve the explicit no-review disclosure route and the library's advisory consumer boundary. | Malformed reviewer/findings/resolution inputs produce an error state; ordinary `finish` creates no new final PDF; explicit bypass is disclosed. Verify with synthetic review cases, `tests.test_review`, and the saved audit probe. |
| **A02 · P1** | New completeness defect; E1/E4 related, **done — PR #24, v61**; [evidence](../../docs/reviews/2026-09-23-a02-page-parity.md). Audit R2. | **Exact page completeness in verify/render/compare. M.** No B1 implementation. | Synthetic 1→2 and 2→1 inputs receive named mismatch findings; inspection artifacts cannot silently omit the unmatched page. Verify with the audit probe and inspected comparisons. Include page size/rotation cases; retain the app's advisory-verdict policy. |
| **A03 · P1** | E1 + E3/C4; **done — PR #22 (`178a06f`)**: rebuild invalidates its verification reports before any stage runs; PDF/sidecar publication is still not transactional, as the consumer guide says; [evidence](../../docs/reviews/2026-09-22-a03-stale-rebuild-report.md). Audit R3. | **Current-attempt artifact ownership. M.** Retry, cancellation, refusal, interrupted save and sidecar consistency; preserving a previous success must be explicit. | Success→refusal/cancellation with reused paths cannot present the old PDF/PASS as the current attempt. Verify synthetic reused-path and injected-save-failure runs, checking hashes and returned/report state. Decide publication behavior before coding. |
| **A04 · P1** | E3/C5; **partial — documentation corrected 20 September, carried onto main's line 23 September; process validation open**. Audit R4; [wording evidence](../../docs/reviews/2026-09-20-concurrency-guidance.md). | **Correct concurrency guidance and substantiate supported execution. M; wording-only slice XS.** Library guidance here, worker integration in the app. | Docs distinguish logging isolation from native-backend safety and describe separate processes/job directories. Verify the wording against PyMuPDF primary guidance; separately replace unsupported thread-based PDF concurrency checks with process-isolated jobs and check both outputs and paths. Keep stdout-isolation regression coverage without inferring backend safety. The docs correction does not close this remaining validation. |
| **A05 · P1** | C8 + E11; **open follow-up**. Audit R5. | **Prove dependency floors. M.** Do not guess a replacement minimum from the newest successful install. | Declared minimum and newest supported dependency sets install, import and pass representative corpus checks on supported Python versions. Verify clean environments and CI commands; dependency files agree. |
| **A06 · P1** | Existing 01/09 verification behavior; **done — PR #25, v61, with the examples slice**; [evidence](../../docs/reviews/2026-09-23-a06-rebuild-mapping-checks.md). Audit R6; [example evidence](../../docs/reviews/2026-09-20-verification-examples.md). | **Supply mapping context in rebuild and examples. S; examples-only slice XS.** Include final-artifact verification and a target-script fill sample. | The two-label/one-empty-target fixture fails through the documented default rebuild route, with `empty-targets` reported. Verify the audit probe and quickstart commands; explicit caller options remain honored. Docs-only repair does not close the default-command defect. |
| **A07 · P1, distribution** | E10; **open, owner decision needed for licensing policy**. Audit R7. | **Third-party license/notice disclosure. M.** Separate original MIT code from dependencies and embedded/downloaded fonts. | A built release's notices identify actual component licenses; public wording does not imply PyMuPDF is MIT. Verify package metadata, archive contents and primary licensor sources. Any uncertain deployment/license choice goes to Rodrigo/licensor, not an automatic relicensing edit. |
| **A08 · P1, PyPI** | E10; **existing owner decision outstanding**. Audit R8. | **Distribution identity and release route. M.** Retain the import/skill names unless separately decided. | An owner-selected, currently verified distribution route installs this repository at the intended ref/version in a clean environment. Verify registry ownership/availability and artifact metadata. No name is reserved and no publish is authorized. |
| **A09 · P2** | Row 29 + E3 input handling; **open follow-up**. Audit R9. | **Validate override selectors and remove the unbound-variable path. S.** | Empty/missing/wrong-type selectors return an actionable mapping error rather than `UnboundLocalError`; valid overrides remain correct. Verify audit probe, targeted override tests and independent rendering verification if drawing code changes. |
| **A10 · P2** | E3 resource lifecycle, E6 related; **open follow-up**. Audit R10. | **Clean up field-font temporary files. S.** Include early non-form return and errors; do not change embedding policy. | Form/non-form success and failure paths leave no unintended temporary full-document copy; intended output remains readable. Verify a temporary-directory fixture, fault cases, field identity and output comparison; apply Rule 1 for any font/rendering change. |
| **A11 · P2** | E3 CLI compatibility + P2 onboarding; **open follow-up**. Audit R11. | **Predictable help and argument errors across eleven scripts. M.** Keep one underlying implementation. | Every script's `--help` returns 0 with usage, no traceback and no artifact; invalid arguments return a documented nonzero code. Verify subprocess cases from an installed skill copy and the CLI parity probe for normal invocations. |
| **A12 · P2** | E3/C3 + E4; **serialization/immutability assurances qualified**. Audit R12. | **Consistent, truthful result contracts. M.** Coordinate the QA envelope with E4 rather than adding a rival report format. | Every advertised result serializes as documented; schema/version fields and mutation expectations match reality. Verify public API result cases, including QA and nested collections. Document actual data-vs-exception refusal semantics without silently breaking callers. |
| **A13 · P2** | E10; **open packaging follow-up**. Audit R13. | **Define and verify wheel/sdist/skill contents. M.** | Clean wheel supports its advertised API; skill includes its workflow/scripts/references; sdist tests either run with all required inputs or the public testing promise is explicitly scoped to checkout. Verify clean builds/install/test commands and archive inventories. |
| **A14 · P1** | Row 32; **open, source-inspected risk; not a reproduced model failure**. Audit R1 related gap. | **Review freshness after edits. M.** Decide how a changed source/mapping/output invalidates or qualifies its prior review. | A previously resolved review cannot silently attest changed translation inputs. Verify review→edit→finish cases and unchanged-input controls; document the selected behavior before implementation. |

### Skill, documentation and supporting engineering

| ID / priority | Existing home / current state | Scope and estimated size | Observable completion and verify-by |
| --- | --- | --- | --- |
| **A15 · P2** | P5; **partial — README facts/commands corrected 20 September and re-measured on main 23 September (20 configured fonts, 670 tests discovered); broader public support wording remains open**. Audit documentation/organization; [evidence](../../docs/reviews/2026-09-20-readme-facts.md). | **Accurate public entry points and small stale facts. S; count/command fixes XS.** Current font count, test commands, dependencies, support limits and a current docs index. | README test commands discover the intended suite; configured font count matches the fetcher; claims distinguish tested behavior from unsupported cases and historical timing. Verify counts/commands against the current tree and check links. No need to rerun expensive suites solely to edit a count. |
| **A16 · P2** | P2 + E10; **open dual-host onboarding follow-up**. Audit host matrix. | **Claude/Codex installation, update and removal instructions. M; verified local Codex instructions S.** Windows/Unix and skill-vs-library boundaries. | Fresh consumer setup follows each advertised path and discovers the expected version, with dependencies in the intended environment. Verify actual host discovery/install lifecycle and a bounded workflow smoke; label untested Claude cloud/plugin routes explicitly. Optional Codex UI metadata is not a blocker. |
| **A17 · P2** | P3; **reopened: the skill was 616 lines on 19 September and is 629 on main `178a06f`**. Audit instruction quality. | **Shorten main workflow without losing rules. M.** Move reference detail, preserve refusal/inspection/reviser requirements and make trigger scope accurate. | Main `SKILL.md` is under 500 lines, links resolve, and retained rules can be located from the execution path. Verify line/link checks and representative positive/negative invocation cases; make no unmeasured quality-gain claim. |
| **A18 · P2** | Skill safety + E7 boundary; **open**. Audit privacy/untrusted input. | **Document instruction trust and sensitive-artifact handling. M; explicit trust-boundary text XS.** | A benign injection fixture in PDF/metadata/web content is treated as data in host evaluation; documentation states model/network use and where content copies/logs live. Verify host traces and actual artifact paths. Storage/retention enforcement in the service remains app-owned. |
| **A19 · P2** | E6 + C8/E11; **open reproducibility follow-up**. Audit fonts. | **Pin and verify font provenance/bytes. M.** Correct the existing pinned-commit claim as a small documentation slice. | Existing/fetched references match recorded hashes and license/source records; wrong bytes are detected rather than accepted by existence alone. Verify fresh and cached fetch cases; independently check rendering if reference bytes change. |
| **A20 · P2** | E10 + P5; **open, publication review needed**. Audit sanitation. | **Public release inventory and sanitation. M.** History, large/binary files, embedded fonts, local paths, sensitive notes, support/security/contributor docs. | Intended release files have reviewed provenance and no unintended job data; documented secret/privacy scan scope includes its exclusions. Verify artifact and history inventories, sample public links and owner review of sensitive content. No automatic deletions/history rewrites. |
| **A21 · P2** | P2 manifest checks + contributor tooling; **open**. Audit static/CI checks. | **Small explicit tooling baseline. M; each manifest/config slice XS.** Both manifest commands, actual type-check environment, targeted lint, validation-tool provenance and CI permissions/pins. | Both manifests are validated explicitly; the type checker resolves the declared environment/target; chosen static checks run with recorded configuration. Verify local commands and later hosted jobs. Billing repair is operator-owned; local success must not be called green hosted CI. |
| **A22 · P2** | P4 + E11; **existing evaluation work extended, not duplicated**. Audit evaluation limits. | **Installed-artifact and real host evaluations. M.** Add negative prompts and artifact-based checks; maintain language/form coverage. | Saved runs identify host/ref/dependencies and inspect actual artifacts, with structural, linguistic and visual judgments separated. Verify reports plus output files, not trace-string PASS alone. Historical early-access limitation requires a fresh check; no paid run is commissioned here. |
| **A23 · P2** | E7/C6; **existing open item, audit reinforces scope**. Audit hostile-input/active-content risks. | **Resource and document-action boundaries. L.** Keep service worker limits/app storage outside the library. | Constructed malformed/resource-heavy cases finish or refuse within stated ceilings in isolated workers; active-action/resource handling is recorded per supported input. Verify bounded runs and output inspection. Define ceilings/policy before coding; no exploit or production protection is claimed by the audit. |
| **A24 · P2** | E8/C7; **existing open item, link only**. Audit performance. | **Representative per-stage measurement and determinism. M.** Preserve the existing measured `/ID` work; no new speed target inferred. | Dated environment/fixture tables report time, memory where measured, output size and limits; existing determinism cases show the agreed result. Verify benchmark/probe outputs. Historical timing or total unit-test duration is not a service-capacity claim. |
| **A25 · P3** | E3/E9 maintenance; **deferred behind correctness fixes**. Audit architecture/API cleanup. | **Narrow large routines and harden boundaries. L.** Input types, exception/resource handling, focused placement/verification responsibilities; preserve compatibility adapters. | A selected extraction of responsibility preserves observable outputs/refusals and parity on named cases; native resources close on tested exceptions. Verify targeted tests and existing CLI/verdict probes, plus independent drawing checks where applicable. No wholesale formatter/tree/framework migration. |
| **A26 · P2** | E11 + public support documentation; **open evidence gap**. Audit accessibility/viewers. | **Publish fidelity/accessibility limits and check final forms in relevant viewers. M; truthful limitations text XS.** | Support docs disclose removed tagging, unsupported scripts/modes and reading-copy page counts; saved final-form viewer checks cover target-script input and field behavior. Verify actual final files and named viewers. Tag reconstruction/PDF-UA certification is not added to scope. |

**Next, as of 23 September, after v61:** the smallest items are A21's explicit
validation of both manifests and its separate type-check environment slice.
A04's wording and A15's README facts are complete as slices; the broader items
remain open. A01, A02, A03 and A06 are done. These next steps remain
recommendations. A07/A08
need owner decisions, A14 needs behavior clarification, and A23/A25 are not
quick wins.

**Completion discipline:** apply `AGENTS.md`'s observable verification and
independent rendering/font/layout checks. A change to shipped scripts or skill
workflow must follow the existing version-consistency policy. New findings can
qualify older closure claims without erasing their historical evidence.

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
| P2 | Plugin packaging | **Closed 2 Sep evening.** `.claude-plugin/plugin.json` (version `35.0.0`, `skills: ["./"]`) and a one-entry `marketplace.json` at the repo root; `claude plugin validate . --strict` exits 0 and `claude --plugin-dir . plugin details pdf-translate` lists the skill; a CI job validates both and fails if `plugin.json` and `metadata.version` disagree; README and HANDOVER carry the install; the re-sync chore is deleted. `SKILL.md` untouched. **The install from GitHub is proven, 3 September**: marketplace add clones and validates, install exits 0, `plugin list` shows 47.0.0 enabled, and the installed copy carries all 11 scripts and 8 references | — |
| P1 | Wild corpus, measured | **Closed 2 Sep evening.** 17 public PDFs (`dev/wild/SOURCES.md`), 449 pages, 8 of them hybrid XFA: 17/17 `translate`, zero crashes, zero timeouts, 126 pages in 37 s; everything left after strip is annotation text; page-1 renders keep every graphic. It found friction, not wrong verdicts: rows 21 and 22 and lane B row P6 (`dev/wild/ANALYSIS.md`). Re-run: `pdf-translate/.venv/bin/python dev/wild/probe.py` | — |
| P6 | Warnings at scale | **Closed 2 Sep evening.** extract prints a per-kind digest — counts and what each kind asks — then at most `--max-per-kind` lines per kind (the booklet: 2,394 lines → 61); the skill text says what each kind wants and write/find/say is a list to confirm; widget-text data values (USCIS `PDF417BarCode1`) are identity-mapped by instruction. Nothing leaves the JSON | — |
| P3 | `SKILL.md` under 500 lines | **Reopened 19 Sep as A17:** the skill was 616 lines then and is 629 on main on 23 Sep; see the current backlog above. Historical evidence: **closed 2 Sep evening.** Body 573 → 493 lines, ~7.6k → ~6.4k tokens on invoke, by moving five regions into `references/` (new `gates.md`, `widget-text.md`, `retypeset.md`; sections added to `compliance.md`, `fonts.md`, `translations-format.md`), one-line rules left behind, frontmatter untouched but the version. The 5,000-token target is not met without deleting rules — C2 decides whether the tail matters | — |
| **P4** | Eval automation | **Blocked 3 Sep, still open** (`goals/P4-eval-automation.md` — the brief now exists). Three cases and their graders are written under `pdf-translate/evals/` and `claude plugin validate --strict` still passes, but **`claude plugin eval` is in early access and is not enabled for this account**, so nothing has parsed them and no report exists. Needs the grant, then one run: `claude plugin eval . --runs 1 --threshold 0.8 --scaffold --json` | Running in CI on every push; naming a winner; scoring the visual pass by machine |
| P7 | Notice channel | **Closed 3 Sep.** `notices` in translations.json — `{page, text, box, size?, bold_lead?}` — placed by retypeset into the author's rect with the job's fonts, through the glyph check (both roles), the scale report, the canonical layer and the placement gate. Malformed notices refused by name before anything is drawn; no page added; the leak scan untouched and the quoted `/Title` still a kept note. `compliance.md` §1 says how. Was four of five canary runs writing their own script | — |
| P5 | One source of truth | **Closed 2 Sep evening**: README count removed and CI badge added; audit HTML is a banner-marked snapshot; findings §15; tracker carries both lanes. Rule: `checklist.html` tracks, this file queues, `HANDOVER.md` cold-starts; nothing else states counts or open rows | — |

**Canary run 3 (3 September) re-opened lane A with two rows**, both in
code that shipped the same day:

| # | Brief | Trigger |
|---|---|---|
| 30 | `goals/30-font-charset-gaps.md` | **Closed 3 Sep.** The whole walk is now `job_charset(conf)`: a `null` core is skipped rather than iterated, `notices[].text` is harvested, `‖` dropped once at the end, and the docstring names it as the one place the next block goes. Was Opus 5 and Fable 5.1 independently |
| 31 | `goals/31-bold-role-is-real.md` | **Closed 3 Sep.** retypeset names any role that resolved to the regular face, once, with what asked for it — covering both `role()` and the Story engine's `<b>`/`<i>`, since the case that opened the row went through the second. Resolved paths, so a symlink counts. Not a failure. Was Sonnet 5 shipping it and Fable 5.1 catching it by eye |
**17 September (late) re-opened lane A with one row, and it is P0:**

| # | Brief | Trigger |
|---|---|---|
| **32** | `goals/32-terminology-loop.md` | **Built, v57, branch `feat/terminology-loop` (design `docs/design/32-terminology-loop/`, plan `docs/plans/2026-09-17-terminology-loop.md`, evidence `docs/reviews/2026-09-17-terminology-loop.md`). Push and PR are the operator's.** Measured on the fixture of record: 31 findings parse with migration, 25 accepted / 6 rejected, 12 terminology of which 11 accepted, 0 reaching the termbase because that review pass predates the `term`/`term_target` fields — reported, never guessed. The canary's first measurement of the reviser: 15.29 accepted findings per 1,000 source words, 19% false-positive rate. Console parity diffs empty against a `main` worktree. Originally: **Open, P0 — top of the order once PRs #10 and #11 merge.** The first FL-150 → Japanese job on the current skill shipped 世帯主 for "head of household" through verify exit 0 and qa_check 0 errors; an independent MQM review found it (1 critical, 6 major, 24 minor) and a human page-1 read agreed. The fix is a loop, not a model: reviser step required before `finish`, `references/terminology-failure-modes.md`, a termbase per class and language grown from `review.json`, the canary scored on terminology. Was Fable 5.1 authoring, Opus reviewing, a person asking |

**Order (17 September):** row 32 first, after the two pending merges (#10 gate 21 v55, #11 the three gate fixes v56); then E3 from `docs/REQUESTS-from-product.md`. The earlier order is kept for the record: **Order (3 September):** 30 and 31 both closed 3 September. **Only P4 is left, and it is blocked** on its early-access grant; when that lands, or before it does, the canary is what opens the next rows. Rows 24, 25, 27,
28, 26, 29 and P7 all closed on 3 September, one commit and one
`metadata.version` bump each, and canary run 3 confirmed every one of
them held. **P4 is blocked, not queued**: its brief and its three cases
exist, but `claude plugin eval` is in early access and is not enabled
here, so nothing has run them. It needs the account grant, not another
sitting's work.
Every row above came from a measurement — a canary run or the wild
corpus — never from invention; when P4 is closed, run the canary again
rather than inventing a row.

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

## After the 4 September review — lane B row P8

`docs/REVIEW-2026-09-04.md` ran the whole pipeline — retypeset and verify
included — over the wild corpus with a pseudo-localised mapping (no model,
no translator: every core diacritic-marked and padded, identifiers kept
verbatim) and measured the engine's own error at zero expansion. Its §5
holds twenty-one candidate rows (32–52) with their evidence, and the
hypotheses that are not rows. **Only P8 enters the queue now, by decision;
the rest wait for it.**

| # | Row | Closed bar (sketch) | Not done when |
|---|---|---|---|
| **P8** | Identity end to end over the wild corpus | `dev/wild/e2e.py` (dev-only, never shipped; the instrument in the review's appendix A) runs strip → extract → pseudo-localise at E = 1.0 → retypeset → verify → `field_fonts` over all seventeen files with a metric-compatible face (Arial here; Liberation Sans on CI) and writes `dev/wild/E2E.md` plus `e2e.json`: per file, scaled runs by band, overflow count, verify FAIL lines, times. P8 closes when that table exists for 17/17 and the loop says a sitting that touches strip, extract or retypeset re-runs it. The table's target — **zero FAIL and nothing below 0.9× on every file** — is the standing bar the rows it opens are measured against, not the bar for this sitting: today the booklet cannot build at identity (row 32) and the W-9 ships 27 shrunk runs with a metric-identical font (row 48) | Any expansion factor other than 1.0 as a gate; translating anything; committing PDFs or outputs; fixing what the table finds in the same sitting |

Order: P8 first — it is the measurement every row in the review is proved
against, and it needs no fix to ship. When it lands, its table opens rows
the way the canary does, from a measurement, and the loop above gains one
line: *if strip, extract or retypeset changed: `dev/wild/e2e.py`, compared
with `dev/wild/e2e.json` — no file may gain a FAIL or a run below 0.9×.*
