# Review of 21 September 2026 and app coordination

Reviewed 22 September, using America/Los_Angeles dates. This is a review and
next-work recommendation, not a release or implementation approval. No product
source was read or copied. The PDF Translator task supplied behavior/status only.

## Findings, highest priority first

1. **P1 / A01 — invalid review data still permits delivery.** On main v60,
   `review.json = {}` produces review exit 2 and two validation errors, but
   `blocks_delivery = false`. `finish` returns 0 and creates `final.pdf` without
   a no-review disclosure. `ReviewVerdict.blocks_delivery` ignores `errors`
   (`pdf-translate/pdf_translate/review.py:144`); `cmd_finish` relies on that
   property (`pipeline.py:600`). This is a previously recorded defect, freshly
   reproduced against the merged terminology/typography work. Typography binding
   validation also needs rejection coverage through **finish**, not just the
   review validator. **Recommended next repair.**
2. **P1 / A03 — failed rebuild retains a prior successful PDF and PASS report.**
   A successful build followed by missing translations returns 1, while both
   prior files remain byte-identical and the old report still says exit 0.
   `pipeline.py:471` returns before refreshing verification state. A caller that
   reads artifacts after failure can mistake the earlier translation for the
   latest result. Preserve intentional prior-success retention only with an
   unambiguous failed-current-attempt result; choose that behavior explicitly.
3. **P1 / A02 — legacy verification accepts missing or extra pages.** Both
   directions return 0 in the synthetic probe. Comparison also returns 0 and
   shows only the common page (`compare.py:37` uses the smaller page count).
   Typography has its own page-geometry check; that does not protect the legacy
   route still used by the app.
4. **P1 / A06 — default legacy rebuild omits mapping-dependent verification.**
   With two labels and one empty target, default rebuild returns 0; explicit
   mapping verification returns 1 with `empty-targets`. Automatic context is
   added only for typography in `pipeline.py:469`. The older local documentation
   repair is useful but is not a code fix.
5. **P2 / new — successful typography builds silently bypass near-floor capture.**
   `run_retypeset` returns directly from `_run_typography` at `retypeset.py:1113`.
   The success capture hook is only on the legacy path near line 2009. A fresh
   `typography-1` fixture succeeds at ratios **0.7402 and 0.7284**, with
   `capture_below=0.75` and a capture directory supplied, but writes no bundle.
   The new API/docs do not state a legacy-only success restriction. Preserve
   occurrence IDs when adding this path; the legacy collector groups by core
   and would collapse these two differently styled occurrences if reused
   unchanged. Reproduction: `runs/review-2026-09-22/capture_near_floor_probe.py`.
6. **P2 / continuity — this branch and its handover are behind the merged work.**
   The handover's first section says main v59/d4d85be and B1 baseline anchoring
   unresolved. Actual remote main is **b20fadda832b673b61ce8bc4a5f17189edd58209,
   v60**, with zero open PRs. This checkout is **6236be6**, two commits unique
   against main and 36 commits behind it, with 37 pre-existing status entries.
   Its uncommitted v61 label is not a complete v61 release. Reconcile the older
   documentation/version edits selectively; do not merge or publish the dirty
   branch wholesale. The local root README also links to audit/shortlist files
   that are still untracked, so those links will be broken in its commit alone.

Two lower-priority old findings also reproduce: an empty override selector
raises `UnboundLocalError` (A09), and non-form `finish` leaves its temporary PDF
(A10). This review did not remeasure dependency lower bounds, licensing,
distribution ownership or model-driven dual-host acceptance.

## Everything that landed or was committed yesterday

Git timestamps and GitHub merge state were checked, rather than treating the
handover as authoritative. Eight PRs merged during the local calendar day:

| Work | Result and review disposition |
| --- | --- |
| #16, just after midnight | Anchored the NOTES ignore rule so the intended FL-150 fixture notes are tracked. |
| #12, v57 | Terminology/reviewer loop, glossary ingestion, review artifacts and finish refusal. Valuable workflow, but A01 prevents treating review presence as a reliable delivery condition. |
| #13, v58 | Callable Python stages, typed results/refusals, logging, progress/cancellation and resource/report controls. This is the app's route away from parsing truncated console output; silent APIs do not establish PyMuPDF thread safety. |
| #18 | Python floor changed to 3.14; hosted matrix covers Linux and Windows at that version. Metadata says `>=3.14`, not an upper bound. The app remains on 3.12, so installation/adoption needs a separate runtime migration. |
| #17, v59 | Opt-in `typography-1`: source class/style evidence, occurrence mapping, role-specific fonts, fixed baseline placement and verification of actual final glyphs. Supported positive cases are useful; unmeasured CJK slanted roles and language semantics remain unproven. |
| #21 | Truncated refusal lists now disclose hidden counts and direct callers to complete typed refusal data. This helps diagnostics; adopting the typed API is still the app's responsibility. |
| #20 | Missing-dependency preflight across eleven CLI shims and import surface. Better onboarding diagnostics; it does not prove supported dependency lower bounds or diagnose every broken binary installation. |
| #19, v60 | Opt-in refusal bundles and a caller-selected near-floor threshold. Replay tests cover legacy bundles; the new typography success omission is finding 5 above. Capture remains default-off. |

#15 (effective scale reporting) merged at **23:21 on 20 September**, immediately
before this window; it is relevant context, not a 21 September merge.

Three additional local commits were reviewed:

- `d9014ec` on this branch: LF/binary attributes and root README changes. Useful
  protection against Git corrupting a NUL-free PDF during CRLF checkout. README
  facts must be reconciled with main's Python/font-count changes before landing.
- `6236be6` on this branch: three binary-integrity checks wired into CI. All three
  pass in this checkout. They are not yet on main.
- `12c730c` on `probe/b1-baseline-anchor`: probe/report only, based on v60. The
  baseline calculation reproduced independently: 107 unshrunk model points
  have zero residual to the recorded precision; six successful cases reach
  zero baseline delta after correction; two cases still refuse. This does not
  implement wrapping. Authored-box containment, multi-member merges, interaction
  with typography and genuine recovery evidence remain open. The report's
  conclusion that nothing engineering-related remains is broader than its data.

The 37 pre-existing dirty/untracked entries include older B1 design/recovery
evidence, public-readiness audit, concurrency/verification/README guidance,
capability probes and v61 metadata. They were preserved. Most date from
19–20 September; filesystem presence alone does not establish work done yesterday.

## Fresh verification and provenance

Tests used an isolated `git archive b20fadd` export under
`runs/review-2026-09-22/main`, with explicit import paths. Runtime: Python
3.14.0, PyMuPDF 1.28.2, pikepdf 10.13.0.post1. Existing test-font files were
copied from this repo's checkouts. No AGPL input was used.

- Full unittest discovery: **649 tests in 359.579 seconds**, with two subtest
  errors in the single historical-runtime compatibility test; no assertion
  failures or skips. Both errors were `git archive` exit 128 because the archive
  directory inherited the enclosing repository's relative path context. With
  `GIT_DIR=C:/Dev/pdf-translate-skill/.git` and `GIT_WORK_TREE` set to the exported
  main root, the unchanged affected test passed both historical revisions:
  **1 test OK in 5.370 seconds**. The full suite was not rerun after that setup
  correction. Logs: `main/full-suite.log` and `historical-rerun.log` under the
  review run directory.
- `python dev/probes/public_readiness_probe.py` in the exported tree: exit 0
  as an observational probe; it reproduced findings 1–4 and A09/A10. Its success
  exit means observations were recorded, **not** that the observed behavior passed.
  Raw results: `runs/review-2026-09-22/main/runs/public-readiness-audit-2026-09-19/reproduction-results.json`.
- `python dev/probes/b1_anchor_probe.py --work ../anchor-rerun`: exit 0;
  107 unshrunk points, six anchored successes, five direct-formula successes,
  two unchanged refusals. Raw log: `runs/review-2026-09-22/anchor.log`.
- `python -m unittest discover -s dev/repo -p test_binary_integrity.py -v`
  from the original checkout: **3 tests OK, 1.187 seconds**.
- Separate six-case typography acceptance run: **exit 0; all six typography
  PASS, verify 0, source/final page counts equal**.
  First attempt stopped on a missing NotoSans-Bold fixture; genuine missing
  fixtures were copied from the typography checkout before the fresh rerun.
  Latin role and italic-overhang final rasters were inspected: the eight
  serif/sans role rows remain visibly distinct and the overhang stays in bounds.
- GitHub main's latest `tests` run at b20fadd reports success. This is hosted
  evidence separate from the local runs. No new hosted run was triggered.

The acceptance script asks Git for HEAD. In an archive nested inside this
checkout that resolves to the enclosing branch (6236be6), so its
`candidate_base` field is **not** the exported runtime revision. The runtime
module path/version and the archive origin b20fadd establish what was tested.
Do not repeat the embedded HEAD as the tested main revision.
All 35 runtime/shim files were compared to b20fadd: no differences after
normalizing Git's CRLF archive conversion. That check is saved in
`runs/review-2026-09-22/runtime-provenance.json`.

## Coordination and next work

Exchanged findings with the existing Codex task **Boot Spire Tech web app**
(`01a0bc1c-cdb2-7b93-8860-0154a450beb4`), as Rodrigo requested. It reports:

- Adopted library remains **v54 / 9675c6196c14eb2a2d37d34e371391eb1955a386** on
  Python 3.12, with legacy mappings, loud retypeset and an app floor of 0.75.
- It owns staging end-to-end validation and isolated Python 3.14/exact-pin
  adoption, followed by typed API and typography integration as proven.
- Its current adapter does not call finish/review; **A01 is an upstream
  delivery-correctness priority, not itself the app's staging blocker**.
- No genuine retained B1 recovery bundle is known. Keep capture off in
  production: retaining customer PDFs beyond job TTL conflicts with its product
  promise. Use synthetic/owned documents locally or staging for bounded evidence.
- It confirmed **A01 next**, then queue A03/A02/A06; do not duplicate B1 or
  typography development without an observed adoption defect. Its app test and
  staging claims are app-reported, not independently verified by this review.

Recommended next action: implement **only A01** in a clean checkout based on
current main. Observable acceptance: malformed JSON, non-object reviews,
missing required review fields and invalid enums cannot deliver; valid resolved
reviews still deliver; an intentional `--no-review` remains visibly disclosed;
an old final file is never cited as proof a refused attempt succeeded. Verify
with focused review/finish cases and the relevant suites. Include typography
binding errors because they share the same delivery property. Do not couple
this repair to B1, an app pin change, or the 37 older local entries.

This review did not start that implementation or push, merge, publish, change a
consumer pin, or mutate a PR. The assignment/recommendation is recorded here so
the next work can start without repeating this investigation.


## Subsequent assigned follow-up

After this review was delivered, the PDF Translator task explicitly assigned
A01 on Rodrigo's behalf. The bounded fix is now local commit
`41bdf9911c81116ab282aa6e39ce3bee0ca82b04` on
`codex/a01-invalid-review-refusal`, in
`C:/Users/rodri/.codex/worktrees/pdf-translate-a01-review-refusal/pdf-translate-skill`.
Full suite: **655 tests OK**, plus independent focused/CLI verification with no
actionable findings. That worktree's
`docs/reviews/2026-09-22-a01-invalid-review-refusal.md` records the exact scope,
commands and results. The candidate is unpublished and retains v60 metadata;
main and the consumer pin are unchanged. The earlier review findings describe
main b20fadd, and A02/A03/A06/capture/B1 remain separate.
