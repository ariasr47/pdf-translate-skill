# Public readiness audit — library and installable skill

19 September 2026 · reviewed checkout v58 / `1d4f9707c4d9934fbc88d8f25576ac304b9bb139`

**Assessment: a capable tool for supervised translation, with substantial PDF-specific engineering, but not ready for an unrestricted public release or an unattended production-readiness claim.** The most consequential gaps concern trustworthy delivery state, incomplete verification, concurrency guidance, and distribution. This is a hardening assessment, not a recommendation to replace the engine.

**Recommended next decision:** prioritize the release blockers below before adding features. Keep one shared engine and one canonical skill workflow for Claude and Codex. Rodrigo owns priority decisions; this repository owns reusable engine and skill behavior; the app owns service integration and product policy.

This audit does not authorize a fix, implementation plan, release, or change to an open PR. B1 remains deferred under its existing ruling. The findings below are recommendations, not additional approved roadmap assignments.

## Read this first

| Question | Assessment | Evidence and limit |
| --- | --- | --- |
| Is the engine substantial and useful? | Yes | 18 runtime modules, 9,021 source lines, 492 passing tests, and specialized form, shaping, font, and text-layer checks. |
| Can a consumer install the Python package? | Yes, from a built artifact | Wheel and sdist built; a clean environment installed the wheel; all 38 exported names resolved outside the source checkout. This does not establish every supported dependency combination. |
| Can Codex discover it as a skill? | Yes | The actual Codex 0.147.0 `skills/list` parser discovered a committed copy staged at `.agents/skills/pdf-translate`, enabled with no matching parse errors. No model translation turn was run. |
| Is Claude packaging valid? | Manifest validation passes | Claude Code 2.1.270 validated the marketplace and plugin manifest separately. This is not an end-to-end install/update/translation test. |
| Is it ready for a self-service public user? | Not yet | Installation documentation is predominantly Claude Code/source-tree oriented; nine of eleven script `--help` calls traceback; package identity and distribution boundaries need resolution. |
| Is it ready for a concurrent public web service? | Not demonstrated | The consumer guide incorrectly promises thread safety despite PyMuPDF's documented restriction; lifecycle and bad-input gaps remain. The app's deployment was not inspected. |
| Does a passing verifier guarantee the approved page count? | No | Synthetic 1→2 and 2→1 page comparisons both returned verification exit 0. The builder did not create those mismatches; the audit supplied them to the verifier. |
| Do all green tests establish public readiness? | No | Independent edge cases reproduced defects despite the green suite. |

## Scope and provenance

Read the Codex handover, running handover, standing rules, and skill instructions; rechecked the claims using local git and GitHub. Inspected the runtime modules, CLI adapters, public workflow and references, tests, packaging, CI, corpus/evaluation setup, and repository organization. Source analysis was combined with fresh runs and primary documentation; this was not a formal proof of every execution path.

| Item | Freshly verified state |
| --- | --- |
| Working branch | `codex/b1-design-canvas`, HEAD `1d4f9707c4d9934fbc88d8f25576ac304b9bb139`, package 58.0.0 |
| Remote default branch | `main`, `a5629fbd6bc084f9ab849ae3db74992c15807fcc`, package 56.0.0 |
| PR #12 | Open, head `abc47674019aaed8f61b716b83e3d289e38d1f1c`, base `main` |
| PR #13 | Open, head `1d4f9707c4d9934fbc88d8f25576ac304b9bb139`, base `feat/terminology-loop` |
| Visibility / releases | GitHub repository private; GitHub identifies MIT; no GitHub releases or local tags listed |
| Hosted CI | Latest inspected PR checks failed before execution because of account billing/spending limits. GitHub check annotation `105871237182` states that the job was not started. This is not a code-test failure or a green remote run. |
| Local test environment | Windows 11, Python 3.14.0, PyMuPDF 1.28.2, pikepdf 10.13.0.post1, fontTools 4.64.0 |
| Fresh consumer environment | Separate venv without system packages; PyMuPDF 1.28.2, pikepdf 10.13.0.post1, fontTools 4.65.0 resolved from the package ranges |

The full test run applies to this v58 checkout, not automatically to v56 `main` or the app's adopted engine. The v57 review loop and v58 consumer surface are still stacked PR work. Findings involving those surfaces must be read with that distinction.

Existing B1 files and dirty documentation were preserved. No product source was opened, no other project was edited, and neither PR was changed. No commit, push, merge, release, or deployment occurred.

The compact, path-sanitized [evidence JSON](data/2026-09-19-public-readiness.json) is durable. The [synthetic reproduction script](../../dev/probes/public_readiness_probe.py) is also saved. Full logs, clean environments, staged skill, archives, and generated PDFs are local ignored scratch material in `runs/public-readiness-audit-2026-09-19/`.

## Release blockers and high-priority findings

Here, **P1** means resolve before a broad release or a production claim for the affected use. It does not mean every item is a remotely exploitable security vulnerability. **P2** means a meaningful reliability, usability, or maintenance gap. Closing evidence describes an observable result, not an approved implementation plan.

### R1 · P1 · Invalid review data can authorize final delivery

**Reproduced.** With `review.json` containing just `{}`, `run_review` reports two validation errors and `exit_code=2`, but `blocks_delivery=False`. `pipeline finish` then returns 0, writes the final PDF, and produces a review record with `present=true`, `no_review=false`, no named reviewer, and an empty warning line.

The cause is `ReviewVerdict.blocks_delivery` checking presence and open findings but ignoring errors. Validation drops malformed findings; dropping a finding must not turn it into an accepted review. The finish stage trusts that narrower predicate.

**Locations:** `pdf-translate/pdf_translate/review.py:128`, `review.py:189`, `review.py:551`; `pdf-translate/pdf_translate/pipeline.py:533`.

**Recommendation:** make invalid and missing review states explicit and consistent at the CLI delivery boundary. Keep the existing deliberate `--no-review` disclosure route distinct. For the library's advisory consumer policy, an invalid review must still be surfaced as invalid data; this finding does not propose silently imposing the skill's withholding policy on the app.

**Closing evidence:** malformed reviewer/findings/resolutions yield an error state; normal `finish` creates no new delivery; the explicit bypass produces its expected disclosure. Rerun the saved probe and dedicated malformed-review cases.

**Related gap, source inspection:** review records are not bound to the exact source/mapping/output revision. A review file can remain after translations change. Define how stale review state is exposed and invalidated without adding a separate governance system.

### R2 · P1 · Page-count mismatches pass verification and disappear from comparison

**Reproduced.** `run_verify` returned exit 0 for both a one-page source with a two-page output and a two-page source with a one-page output. The ink loop only checks `min(len(original), len(output))`. Neither case received a page-count failure.

`compare` returned 0 and created one page-pair section for a two-page source and one-page output. `render_pages` likewise produced only two PNG files: one matched pair. The unmatched page therefore vanished from the very visual artifacts used to inspect completeness.

**Locations:** `pdf-translate/pdf_translate/verify.py:1761`; `pdf-translate/pdf_translate/compare.py:37`; `pdf-translate/pdf_translate/render_pages.py:27`.

**Recommendation:** make exact page-count comparison explicit and make unmatched pages visible in inspection results. Preserve the approved same-page B1 constraint. This is a verifier/comparison defect, not evidence that the current retypesetter itself adds pages.

**Closing evidence:** synthetic 1→2 and 2→1 comparisons both produce a named mismatch result; comparison/rendering cannot silently omit the unmatched page. Check page dimensions and rotation separately as well: counts alone do not establish geometry preservation.

### R3 · P1 · A failed rebuild leaves a previous PDF and PASS report in place

**Reproduced.** First rebuild succeeded. The mapping was then changed to omit its only required translation. Second rebuild returned 1, but the old output PDF and old `verify_report.json` remained byte-for-byte unchanged; the report still said exit 0.

The renderer exits before saving a new output, and `cmd_rebuild` returns before invoking verification. Its verifier's stale-report cleanup never runs in that path. The consumer guide's claim that a build refusal means there is no file is consequently unsafe when paths are reused. A carefully written caller that checks the current return value can avoid serving the stale artifact; a folder watcher or retry workflow can misidentify it.

**Locations:** `pdf-translate/pdf_translate/pipeline.py:413`; `pdf-translate/pdf_translate/retypeset.py:888`; `pdf-translate/references/consumer-guide.md:94` and `:165`.

**Recommendation:** clearly distinguish the previous successful artifact from the current attempt. Use explicit attempt/output ownership and atomic publication where needed; preserve a prior successful result intentionally rather than presenting it as a new success. Define cancellation, refusal, interrupted save, and partial sidecar behavior together.

**Closing evidence:** success→refusal and success→cancellation runs cannot expose a previous PASS record as the latest attempt; consumers can unambiguously identify which input revision produced a delivery. Reproduce with reused paths, not only fresh temporary directories.

### R4 · P1 · The consumer guide's thread-safety promise is too broad

**Confirmed documentation conflict.** The guide says the `run_*` surface can run in different threads. Avoiding global stdout redirection improves logging isolation, but does not make the native PDF backend thread-safe. PyMuPDF explicitly says multi-threaded use is unsupported and may cause incorrect behavior or crash Python. [PyMuPDF multiprocessing guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html).

**Locations:** `pdf-translate/references/consumer-guide.md:174`; `pdf-translate/pdf_translate/verify.py:2135`; `pdf-translate/pdf_translate/_console.py:20`.

**Recommendation:** document process isolation for concurrent PDF jobs, with job-specific directories. Limit any thread-safety claim to the particular pure-Python operation actually supported. The application owns its worker architecture; this library owns accurate API guidance. No attempt was made to trigger a native crash, and this finding does not claim the user's Codex crash was caused by the library.

**Closing evidence:** consumer documentation matches the backend's supported execution model; a separate-process integration check demonstrates concurrent isolated jobs without mixed artifacts. A stdout-isolation test alone does not close this issue.

### R5 · P1 · The declared dependency floor admits an import-incompatible PyMuPDF

**Artifact inspection confirmed.** Both dependency files allow `pymupdf>=1.24`. The downloaded official Windows CPython 3.10 wheel for PyMuPDF 1.24.0 contains `fitz` and `fitz_old`, but no `pymupdf` top-level package. The engine imports `pymupdf`. Installing an allowed older version can therefore satisfy the package resolver while making the engine unimportable.

**Locations:** `pdf-translate/pyproject.toml:16`; `pdf-translate/requirements.txt`; runtime imports throughout `pdf_translate`.

**Recommendation:** set a lower bound proved by clean installation/import and representative rendering checks. Test the minimum supported dependency set separately from the newest allowed set. A constraints file for reproducible development/evaluation complements, rather than replaces, sensible library dependency ranges.

**Closing evidence:** every declared minimum dependency configuration imports and completes an agreed small corpus; CI exercises the floor. The 1.24.0 wheel was inspected, not executed under Python 3.14.

### R6 · P1 · Common examples run only a subset of verification

**Reproduced plus documentation inspection.** Default `pipeline rebuild` knows the mapping path but does not pass it to verification. In the probe it ran seven gate records, with none of the authored-target checks. The README quickstart/hot loop and consumer guide's Python example also omit the translations argument. The full skill's detailed verification example includes it, creating conflicting levels of assurance across the entry points.

A second synthetic case makes the consequence concrete: one of two source labels was mapped to an empty string. Default rebuild returned **0**. Verifying the same output with the mapping explicitly supplied returned **1**, with `empty-targets` failing. The missing argument can therefore turn a detected omission into a passing documented workflow.

**Locations:** `pdf-translate/pdf_translate/pipeline.py:421`; `pdf-translate/README.md:51` and `:71`; `pdf-translate/SKILL.md:105`; `pdf-translate/references/consumer-guide.md:55`; `pdf-translate/pdf_translate/verify.py:1965`.

**Recommendation:** make the complete intended verification context the normal documented route, and report which checks were applicable, omitted, or unable to attest. Check the artifact after final field-font changes too. Use a target-script fill sample for a target-script form, not just the default Latin test string.

**Closing evidence:** a translated-target omission fixture fails the documented quickstart and rebuild path; emitted results identify every expected mapping-dependent check. Do not describe a subset of checks as all checks passed.

### R7 · P1 for public distribution · MIT labeling does not describe the whole dependency stack

**Confirmed dependency metadata and primary documentation.** This repository's original code is labeled MIT. PyMuPDF/MuPDF are distributed under AGPL or an Artifex commercial license. The repository's MIT license does not grant MIT rights to those dependencies. [PyMuPDF licensing](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright).

The README's short MIT statement, package metadata, and skill frontmatter need accompanying third-party licensing information so consumers can evaluate their own distribution and service use. Keep the existing prohibition on importing product code. This audit does not change the repository license or conclude that a particular deployment is unlawful.

**Recommendation:** document the dependency licenses, relevant notices, and the AGPL/commercial choice, with any uncertain deployment interpretation resolved with the licensor or appropriate legal advice. Separately preserve font license/embedding provenance; the source-code license does not license arbitrary downloaded fonts.

**Closing evidence:** a public distribution clearly identifies its own license and dependency obligations, and its included notices match the actual release contents. Operator/license owner approval is needed for a licensing-policy decision.

### R8 · P1 for PyPI publication · The distribution name is already used

**Verified against PyPI.** `pdf-translate` currently identifies another project, version 1.0.0, whose repository is `guilt/pdf-translate`. This checkout declares the same distribution name at 58.0.0. A generic `pip install pdf-translate` is not a reliable way to obtain this repository. [Existing PyPI project](https://pypi.org/project/pdf-translate/).

**Location:** `pdf-translate/pyproject.toml:6`.

**Recommendation:** settle a publishable distribution identity before documenting a public package-index install. Until then, document an explicit repository/artifact installation with a verified ref. An import name, skill name, and PyPI distribution name can differ; a rename needs its own compatibility decision. No publication or name reservation was attempted.

**Closing evidence:** the advertised install command resolves to the intended owner, source, and version in a clean environment. GitHub release artifacts are another possible distribution path, but none are currently published.

## Additional reproduced defects and API debt

| ID / priority | Finding and evidence | Recommendation and observable check |
| --- | --- | --- |
| R9 / P2 | An override with `contains: ""` reaches `retypeset.py:1147` and raises `UnboundLocalError` because `t` is used before assignment. Isolated Ruff also identifies F821. | Validate nonempty selectors and part types at the boundary; return an actionable mapping error. Empty/missing/wrong-type selectors should never produce this traceback. |
| R10 / P2 | `run_field_fonts` returns early for a non-form PDF at `field_fonts.py:78`, before cleanup below `:131`. The probe left `final.pdf.tmp_withfont.pdf`. | Guarantee temporary-file cleanup on each intended success/failure path; no extra full-document file after a non-form pass. Preserve diagnostics intentionally when useful and document retention. |
| R11 / P2 | Nine of eleven staged script `--help` calls traceback, interpreting help as a file or indexing missing arguments. `pipeline` and `bilingual` print usage but return 2. | Standardize usage/help and malformed-argument behavior, preferably with the standard library parser. All eleven `--help` calls should print usage, return 0, and create no artifacts. |
| R12 / P2 | Clean-wheel `run_qa(...)` returns a `QAVerdict` with no `to_dict`, while the consumer guide says every result has schema/version serialization. `QAVerdict.findings` is a mutable list; other frozen result objects also contain nested mutable dictionaries. | Make the serialization and mutability promises precise and consistent. Exercise JSON serialization and mutation expectations across the advertised result families, not only selected dataclasses. |
| R13 / P2 | Built sdist contains test modules but omits `tests/__init__.py`, wrappers, fixtures/corpus, skill instructions, and references. Running `unittest discover -s tests -t . -v` there fails with “Start directory is not importable.” | Decide whether the sdist promises runnable contributor tests; include the required inputs if so. Give the package README installation/API instructions appropriate to that artifact. |

Other API observations from source inspection:

- `run_extract` reports scan/refusal conditions in result fields; callers must inspect them. `run_strip` returns `ok=False` on leftover text even though its docstring broadly says it raises on refusal. State each stage's actual success/refusal/error semantics; do not turn every result into exceptions just for uniformity.
- Malformed JSON, unreadable files, native-library errors, callback exceptions, and font-subsetter failures can escape outside the advertised typed refusal family. Distinguish invalid input, expected unsupported-document cases, environmental failure, and programming errors.
- Several successful-path document opens are followed by explicit closes rather than a whole-operation context manager/finally. Check resource cleanup on intermediate exceptions. `field_fonts` uses a predictable temp name; same-directory/same-output concurrent calls must not share it.
- `interleave` is an exported library function; the fillable-document refusal/disclosure is in its CLI wrapper. Document that difference. Its optional doubled-page reading copy must remain clearly separate from the exact-page-count translated deliverable.
- `run_retypeset` writes the scale report before saving/canonicalizing the final PDF. Evaluate failures between those steps as part of artifact lifecycle work, not merely the happy path.
- Progress/cancellation is offered for the retypesetter's page and merge work units. It is not a guarantee of immediate cancellation inside native rendering or of cancellation across every pipeline stage.

## Deep dive: the skill as a public product

### What is already well designed

The skill has a clear, useful specialty: translating born-digital PDFs while retaining form behavior and layout. The engine does not call an LLM. Translation authoring remains a mapping supplied by the caller, which is a good boundary for both model independence and library reuse.

The workflow describes actual PDF failure modes, asks the operator to inspect rendered pages, makes terminology review distinct from structural checking, and explains why OCR scans and certain shaping cases cannot be promised. The references are substantive rather than decorative. Narrow measured shaping probes and explicit REVIEW outcomes are particularly valuable: the code does not pretend that glyph counts prove Thai or Hebrew mark placement.

The installed skill can contain the Python package beside its thin script adapters. That provides a single implementation for the CLI and imported API. The actual Codex discovery check succeeded with this layout; no separate Codex translation engine is needed.

### Readiness by host and installation method

| Surface | What was checked | Missing evidence or documentation |
| --- | --- | --- |
| Claude Code plugin | Both JSON manifests separately passed `claude plugin validate ... --strict`. | Fresh installation, discovery, invocation, update, and removal from a clean user configuration. CI's single root validation invocation printed marketplace validation locally; validate the plugin file explicitly too. |
| Codex local skill | Committed skill copied into an isolated consumer project's `.agents/skills/pdf-translate`; real local app-server `skills/list` returned it enabled with no matching errors. | Public install/update/uninstall instructions and a complete model-driven translation run. This audit did not install it into the user's personal skill collection. |
| Codex distributed plugin | No dedicated distribution test. | Decide whether a plugin is needed beyond local skill installation and verify the selected host's packaging. Claude's manifest validation is not evidence of a Codex plugin install. |
| Claude web/Cowork upload | Frontmatter uses the portable skill fields. | A release ZIP and actual upload/runtime checks, including dependency installation, fonts, network availability, file access, and image inspection. Claude Code success does not establish cloud-host compatibility. |
| Python library wheel | Clean installation, `pip check`, isolated import and resolution of all 38 exports passed. | Installed-artifact end-to-end smoke coverage, minimum dependency validation, public identity, and documentation present in the distributed artifact. |

Codex's local discovery locations and optional `agents/openai.yaml` are documented by OpenAI. The metadata file is optional; its absence is a discoverability/presentation opportunity, not a validity defect. Keep installation instructions version-aware. [OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills).

### Instruction quality and agent usability

- **Size:** `SKILL.md` is 616 lines and 5,049 whitespace-delimited words. No token count was measured. Move detailed gate explanations and repeated rationale into the existing references; leave a compact execution path, essential refusals, expected artifacts, and recovery rules in the main skill. Both Claude and the Agent Skills specification recommend fewer than 500 lines. [Claude skill guidance](https://code.claude.com/docs/en/skills), [Agent Skills specification](https://agentskills.io/specification).
- **Trigger wording:** “any language to any language,” “pixel-faithful,” and “every field working” overstate the evidence. State supported born-digital input, font availability, documented refusals, and mandatory visual/reviser work close to the opening claim. Do not advertise automatic certification or universal script coverage.
- **Cross-platform setup:** provide verified Windows PowerShell and Unix examples, a virtual environment, the skill root versus job directory, and exactly which requirements to install. The main skill's unbounded `pip install pymupdf pikepdf fonttools` bypasses the repository's stated version ranges.
- **Recovery:** explain missing dependencies/fonts, extraction refusals, malformed mappings, scale/glyph refusals, missing reference faces, interrupted jobs, and invalid review state with the next concrete user action. The current traceback-heavy help surface adds avoidable debugging for agents and humans.
- **Selection tests:** test natural positive prompts and negative cases: PDF summary only, OCR scan, a non-PDF document, a partial-page request, an already-translated PDF, and a request requiring certification. These are candidate evaluation cases, not measured success rates.
- **Evaluation quality:** current case graders partly match strings in the agent trace. A claimed PASS in prose is weaker than running the verifier against the produced artifact. Preserve output files, mappings, tool exit codes, environment versions, and separate semantic/visual judgments.

The repo's evaluation README explicitly records that the three `claude plugin eval` cases were never executed. This audit read that limitation but did not retry a paid/model evaluation; current account enablement remains unverified. Historical canary reports are useful evidence for their recorded versions and runs, not current Claude/Codex success percentages.

### Privacy and untrusted input

No explicit instruction boundary was found in the skill/reference set for commands embedded in PDFs, metadata, issuer websites, or reviewer artifacts. The workflow reads these sources and may browse for terminology, so this is a practical skill-level gap. Tell the agent to treat document content as translation data, never as authority to change its tools, reveal information, or follow unrelated instructions. Add a harmless injection fixture to the eventual host evaluation; no adversarial model run was performed here.

Distinguish the offline Python engine from the surrounding host workflow. PDF text/images, mappings, review files, comparisons, and logs can contain sensitive user data. Specify where those files go, what is sent to a model or website, what the user receives, and how job artifacts are retained or removed. A self-contained comparison HTML embeds page images and is itself a copy of document content.

The PDF translator is not a general PDF sanitizer: preserving form behavior may preserve active document behavior. There is no demonstrated comprehensive removal policy for JavaScript/actions, attachments, or external references. Likewise, authored Story HTML and font/resource paths should be trusted inputs or constrained by the consumer. This audit did not establish a path-traversal or remote-code-execution exploit.

## Architecture, modern code quality, and simplification

### Runtime map

All paths in this table are under `pdf-translate/pdf_translate/`.

| Modules | Responsibility | Assessment |
| --- | --- | --- |
| `__init__.py`, `results.py` | Exported API, result/exception families, version | Useful public boundary; strengthen consistent serialization and documented failure semantics. |
| `_console.py`, `pipeline.py` | CLI logging adapter and orchestration | Keeping CLI behavior separate from silent imports is sound; argument parsing and current-attempt state need attention. |
| `strip_text.py` | Content-stream stripping, XObjects, XFA, permissions and widget display text | Sophisticated preservation logic with explicit disclosures. Keep narrowly targeted regression tests and ensure cleanup on exceptional exits. |
| `extract_segments.py` | Geometry, cores, metadata, obstacles and warnings | Good evidence-rich output. Extraction, classification, and artifact writing are concentrated in one large routine. |
| `prepare_font.py` | Embedding checks, instancing, subsetting and raster/shaping checks | Strong specialist checks; improve reproducible font provenance and environmental-error handling. |
| `retypeset.py` | Font roles, placement, shaping, merges, overrides, metadata and canonical text | Central complexity hotspot: 1,651 lines; `run_retypeset` alone spans 933 lines. |
| `verify.py` | Structural, content, script and font diagnostics | 2,265 lines; `_execute_verify` spans 510 lines. Valuable diagnostics but incomplete completeness checks and too much orchestration in one function. |
| `shaping_probe.py`, `han_forms.py`, `cjk_tell.py` | Conjunct, regional-form and script-leak evidence | Relatively focused components with measured limits; retain those limits and reference-font provenance. |
| `qa_check.py`, `review.py` | Mapping mechanics, human/model revision records, termbase updates | Correct separation from rendering; review validation must not silently turn invalid findings into approval. |
| `field_fonts.py` | Final text/choice-field font embedding | Useful output stage; temp cleanup and verification of the final artifact need tightening. |
| `render_pages.py`, `compare.py`, `bilingual.py` | Visual inspection and optional delivery formats | Small modules worth keeping separate; completeness and reading-copy distinctions must be explicit. |

### Highest-value cleanup

1. **Validate inputs once at boundaries.** Typed mapping/segment/review structures and precise errors are more useful than many scattered `.get` assumptions. Keep deliberate backwards compatibility visible. A lightweight dataclass/TypedDict approach may be sufficient; no new framework is required to establish the need.
2. **Separate computation from file publication.** Layout decisions, validation findings, and output writes have different failure modes. Make current-attempt ownership and cleanup clear before reorganizing file names.
3. **Reduce the two large routines by responsibility.** Candidate boundaries are mapping validation, font/resource preparation, placement jobs, serialization, and verification groups. Preserve byte/semantic behavior with the existing CLI/verdict parity probes and independent rendering verification for any actual rendering change.
4. **Keep compatibility adapters thin.** The loud and silent APIs are documented migration machinery, not automatically redundant code to delete. Deprecation would need a separate versioned decision. The eleven wrappers already delegate to one package implementation.
5. **Adopt a small, explicit static baseline.** Isolated Ruff with `E4,E7,E9,F` produced 19 findings: 16 E402 import-position items, two unused imports, and the reproduced undefined `t`. Some import ordering is intentional. Configure exceptions explicitly; do not count every stylistic warning as a correctness defect.
6. **Bring tooling into agreement.** `pyrightconfig.json` points at `pdf-translate/.venv` and Python 3.14, while the recorded environment is `pdf-translate.venv` and advertised support begins at Python 3.10. Configure a repeatable contributor environment and appropriate target checks. No type-check pass was claimed in this audit.
7. **Make output models honest.** Frozen dataclasses containing lists/dictionaries are only shallowly protected. Either document this or make the intended immutability real at the public boundary. Avoid promising identical result capabilities when QA is an exception.

Do not start with a repository-wide formatter rewrite, a new web service inside the library, or a second copy of the engine for another agent host. Retaining the existing implementation and narrowing risky boundaries is the recommended direction.

### Performance and operational limits

There is no fresh representative throughput/RSS benchmark in this audit. The 202.730-second full test run is a test-suite measurement, not a customer-document latency estimate. Historical four-page examples do not establish large-document capacity.

Code inspection shows repeated document opens and whole-document rendering passes; comparison HTML retains base64 page images in memory. Runtime limits for input bytes, page count/dimensions, raster DPI, elapsed time, and memory are not a demonstrated public-service boundary. The library can expose/document resource-sensitive operations; the app or hosting harness should impose process and job limits. Avoid embedding a scheduler, authentication, or service quota system here.

Measure representative Latin/CJK/shaped-script documents before optimization. Include extraction, preparation, typesetting, verification, inspection, and final size separately. Test cancellation and corrupted/encrypted PDFs in isolated workers. No denial-of-service corpus or native-parser fuzzing was run.

### Accessibility and fidelity

The renderer deliberately removes an obsolete structure tree and clears marked status after replacing text (`retypeset.py:419`). That is preferable to claiming stale tags remain accurate, but it means the translated output does not preserve tagged-PDF accessibility. Logical `/ActualText`, bookmarks, and translated metadata help; they do not by themselves establish PDF/UA conformance or correct reading order.

Publish a supported-feature/limitation table covering born-digital input, scans, mixed raster text, rotated shaped text, regional CJK forms, mark-stacking scripts, signatures/encryption changes, accessibility tags, form viewers, and manual review. Test final fillable outputs in relevant real viewers; a PyMuPDF round-trip is not proof of identical behavior in Acrobat and browser viewers.

Existing B1 measurements already document baseline movement and occurrence-selection limitations of current merges. Treat those as open, measured layout limitations; the prior synthetic 6/8 placement result is not a production recovery rate. See the existing [B1 evidence](2026-09-19-b1-recovery-probe.md). No new wrapping behavior was built here.

## Packaging, repository layout, and public sanitation

### Distribution boundaries

The built wheel intentionally contains the Python runtime and metadata/license, not `SKILL.md`, wrappers, tests, corpus, or references. That can be a sound library distribution. It is not an installable agent skill by itself. Conversely, a skill folder containing scripts needs its Python dependencies installed in the execution environment; skill discovery alone does not install them.

Maintain one source of truth while documenting three distinct user routes: use the skill in Claude, use the skill in Codex, or import the engine from Python. State each artifact's contents and verified compatibility. Add release checks for both the library artifact and skill artifact instead of assuming one proves the other.

Missing public-release basics include a coherent release/tag strategy, an artifact-appropriate install guide, changelog/support policy, contributor guide, security-reporting route, and third-party notices. Package project URLs and classifiers would improve identification. The current four-way version consistency check is useful; retain it unless version generation replaces it with something equally observable.

### Organization

The committed tree contains 247 files: 102 under the skill directory, 83 under `dev/`, and 54 under `docs/`, plus root/configuration files. The separation between runtime skill material and development records is a good starting point. The public root README, however, directs readers to several dated audits and a living tracker, so it is hard to distinguish current support from historical progress.

Recommended organization outcomes:

| Area | Keep | Clarify or simplify |
| --- | --- | --- |
| Root README | Short purpose and repository map | Clear Claude/Codex/Python entry points; actual support limits; latest release/status; contributor link. |
| Skill root | Canonical `SKILL.md`, scripts, runtime package, references | Main workflow shorter; accurate dependency setup; a clear job directory outside installed files. |
| Public references | Mapping format, fonts, failure modes, API usage | Current examples must execute from a clean install and use the intended verification context. |
| Tests/corpus/evals | Synthetic corpus, measured shaping tests, representative host evaluations | Distinguish deterministic code tests from model/semantic/visual evaluation; decide which are distributed. |
| `dev/` | Reproduction scripts and developer working history | Keep internal handovers/session prompts out of the minimal skill release artifact. |
| `docs/` | Decisions and evidence | One current index with dated archives clearly labeled; retain useful provenance rather than deleting history wholesale. |

A forced `src/` migration is not presently justified by the findings. The existing co-location makes a self-contained skill possible. Build/install tests and clear artifact boundaries matter more than a fashionable directory tree.

### Sanitation findings

The bounded history scan examined **955 text-like blobs reachable from local git refs**, skipping 15 binary blobs and three blobs larger than 2 MB. It checked recognizable GitHub/OpenAI/AWS/Slack credentials and private-key headers and found **zero matches**. This is not a comprehensive secret clearance: other credential formats, binary contents, oversized files, remote-only refs, and sensitive prose may be missed. No secret values were printed.

The tracked-tree path/email scan produced **95 candidates across 20 files**, chiefly developer documents containing local paths and session details. Author attribution is intentional metadata and should not be stripped as if it were a credential. Review each candidate for public usefulness and permission rather than mass-redacting.

Before a public publication decision, review:

- Tracked session logs, internal product requests, handovers, absolute workstation paths, private project links, and any user/customer narrative.
- Full git history as well as the release tree. Deleting a file from the latest checkout does not remove its history. History rewriting would require separate explicit approval.
- The real FL-150 development mapping/review artifacts and their provenance. The recorded source is a public court form; that does not automatically certify every surrounding note as intended for publication.
- Generated corpus PDF metadata, embedded fonts, and redistribution rights. No standalone font files are tracked, but PDFs can embed font programs; evaluate the actual release contents rather than relying only on the README's “no fonts redistributed” wording.
- License notices for downloaded/test fonts and deterministic download provenance. `fetch_test_fonts.py` uses branch-tip URLs, checks existence, and prints hashes without enforcing them. Its opening docstring incorrectly says pinned commits. The font cache key also does not validate byte identity.
- Ignore rules and published-artifact inclusion. Current local runs, environments, and B1 captures are ignored; a release assembled from a working directory instead of an explicit file set could accidentally include them.

No product code was consulted as a source for this audit or its reproduction script.

## Tests, CI, security tooling, and evidence limits

| Check | Result | Interpretation |
| --- | --- | --- |
| Complete unittest discovery | **492 tests, 202.730s, OK, zero skips** | Fresh local Windows/Python 3.14 run. |
| Canary scorer unit tests | **15 tests, OK** | Tests the scorer; not 15 live translated documents. |
| Font presence check | Passed for all 11 configured faces | Existence is not a pinned-byte check. |
| Wheel and sdist build | Passed from a `git archive HEAD` snapshot | Avoided incidental uncommitted job files in the package build. |
| Fresh wheel install / `pip check` | Passed | Six runtime dependency packages resolved; isolated import used site-packages. |
| Codex discovery | Passed for staged local skill | No model turn, installed plugin lifecycle, or translation quality claim. |
| Claude validation | Marketplace and plugin passed separately | Manifest checks only. |
| Synthetic lifecycle/completeness probes | Defects reproduced | Review failure, stale output/report, missing/extra pages, temp leak, malformed selector. |
| CLI help / sdist tests | Gaps reproduced | Nine tracebacks; sdist test discovery fails. |
| Isolated Ruff | 19 findings | One reproduced runtime defect; the rest require ordinary lint triage. An earlier run inherited ambient configuration and is not the reported baseline. |
| Bandit | 10 low-severity findings, no medium/high | Eight broad exception-handling findings and two subprocess-related flags. These are review leads, not ten confirmed exploits; the font subset command uses an argument list. |
| `pip-audit` on fresh environment | No advisory entries for the six resolved runtime dependencies | The unpublished local distribution could not be matched. Installer pip 25.2 had 12 returned entries representing six distinct advisory IDs; those concern the setup tool, not twelve engine vulnerabilities. Applicability varies. No global packages were changed. |
| Narrow secret-pattern scan | Zero matches in the scanned set | Limited patterns/size/type/ref scope; not publication approval. |

CI already has useful Linux/Windows and Python 3.10/3.13 configuration, mandatory font presence, deterministic tests, fixture generation, and version consistency. It needs a working hosted execution budget before it supplies fresh platform evidence. This audit did not repair billing or rerun Linux/macOS.

High-value missing checks are installed-wheel execution, declared-minimum dependencies, explicit validation of both manifests, host skill discovery, invalid review/mapping cases, same-path retries/cancellation, page/geometry completeness, and final-artifact verification. Restore confidence in those behaviors before adding broad style-only coverage.

For reproducibility, pin or verify font bytes and record the environment used for visual/shaping evidence. Pin the tool versions used for validation; the existing workflow installs the latest Claude CLI. Action revision pinning and explicit minimal workflow permissions are supply-chain housekeeping candidates, not evidence that the current repository was compromised.

No fresh linguistic-quality score, model comparison, production load test, vulnerability penetration test, or accessibility certification is claimed. Test coverage percentage was not measured. The audit also does not attest the consuming web app's deployment or licensing configuration.

## Reproduction and saved evidence

Run the synthetic findings probe from the repository root after installing dependencies and fetching the test fonts:

```powershell
$env:PYTHONUTF8='1'
& .\pdf-translate.venv\Scripts\python.exe dev/probes/public_readiness_probe.py
```

It creates its own small PDFs and mappings beneath `runs/public-readiness-audit-2026-09-19/repro/`, then writes `reproduction-results.json`. It does not edit the library, product repository, or existing source PDFs. The observed defective behavior is recorded, not accepted as a regression-test expectation.

The full suite command, from the skill directory, was:

```powershell
& ..\pdf-translate.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Additional recorded commands:

```text
python -m unittest discover -s dev/canary -p test_score.py -v
python tools/fetch_test_fonts.py --check
claude plugin validate . --strict
claude plugin validate .claude-plugin/plugin.json --strict
python -m build --outdir <audit-dist>                  # in committed snapshot's skill folder
python -m pip install <audit-dist>/pdf_translate-58.0.0-py3-none-any.whl
python -m pip check
python -m ruff check --isolated --select E4,E7,E9,F pdf-translate/pdf_translate pdf-translate/scripts --output-format json
python -m bandit -r pdf-translate/pdf_translate -f json
python -m pip_audit --path <consumer-venv>/Lib/site-packages --format json
codex app-server generate-json-schema --out <audit-schema>
```

Codex discovery used that locally generated protocol schema, `initialize`, and `skills/list` against an isolated staged consumer directory. No chat/task or paid model invocation was created. The test command templates above omit only environment-specific scratch locations; exact local logs remain in the ignored audit directory.

## Decisions for the owner

The evidence supports retaining this codebase and prioritizing a bounded release-hardening effort. Correctness findings R1–R6 should shape that scope; licensing and package identity R7–R8 need explicit owner decisions before distribution. Skill onboarding, predictable CLI behavior, artifact packaging, and a current public documentation entry point are necessary parts of public readiness, not merely cosmetic cleanup.

The app should remain the owner of service workers, authentication, storage, quotas, deployment, and product-level delivery policy. This repository should provide truthful engine results and skill instructions that each host can use. No parallel product roadmap or duplicate renderer is recommended. Share a concise data-only finding summary with the app task only when Rodrigo authorizes that communication.

Future claims of readiness should identify the exact released ref, dependency/font versions, supported hosts, representative corpus, measured results, and known limits. A successful model demonstration or a large unit-test count alone is not that claim.
