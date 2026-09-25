# Handover — pdf-translate (read this in a new session)

Paste this file (or: “read `dev/goals/HANDOVER.md` and continue”) into a
**new** agent session that has no memory of prior work.

## Start here — 25 September 2026, late afternoon: #42–#45 open; docs items built (v76), not pushed

**Main is v71 at `62e87bf`.** A stack waits, to be merged in order:
- **#42,** R-42 at v72.
- **#43,** R-110 at v73.
- **#44,** R-100 at v74.
- **#45,** R-99 at v75, with Auto-fix on.
- **`docs/r79-r83-docs-quick-wins`,** R-79, R-80, R-82 and R-83 at v76, on
  #45. It is local and waits for Rodrigo's go.
  - The shipped docs and comments match the code, and
    `tests/test_shipped_docs.py` keeps them matched.
  - Evidence: `docs/reviews/2026-09-25-r79-r83-docs-quick-wins.md`.

**Every review quick win is built.** Next come the performance items
R-51, then R-48 with R-49, then R-50, unless E12's rulings arrive first.
Each must show identical output by a render or byte diff.

## Start here — 25 September 2026, afternoon: #42, #43 and #44 open; R-99 built (v75), not pushed

**Main is v71 at `62e87bf`.** A stack waits, to be merged in order:
- **#42,** R-42 at v72.
- **#43,** R-110 at v73.
- **#44,** R-100 at v74.
- **`fix/r99-resource-warnings`,** R-99 at v75, on #44. It is local and
  waits for Rodrigo's go.
  - The suite's ResourceWarnings go from 45 to 0.
  - Evidence: `docs/reviews/2026-09-25-r99-resource-warnings.md`.

**The code quick wins are done after R-99. Next: the docs items R-79,
R-80, R-82 and R-83.** Then the performance items (R-51, R-48 with R-49,
R-50), unless E12's rulings arrive first.

## Start here — 25 September 2026, early afternoon: #42 and #43 open; R-100 built (v74), not pushed

**Main is v71 at `62e87bf`.** A stack waits:
- **#42,** R-42 at v72.
- **#43,** R-110 at v73, on #42.
- **`chore/r100-dead-code`,** R-100 at v74, on #43. It is local and waits
  for Rodrigo's go.
  - Four pieces of dead code are removed.
  - A tripwire and an adversarial independent pass both confirm nothing
    removed was live.
  - Evidence: `docs/reviews/2026-09-25-r100-dead-code.md`.

**Next quick win: R-99**, closing the ResourceWarnings. Then the docs items
R-79, R-80, R-82 and R-83.

## Start here — 25 September 2026, midday: #42 open (v72); R-110 built (v73), not pushed

**Main is v71 at `62e87bf`.** Two things are in flight:
- **#42** is open against `main`, with R-42 at v72.
- **`chore/r110-spdx-licence`** sits on #42, with R-110 at v73. It is local
  and waits for Rodrigo's go.
  - `pyproject.toml` uses the SPDX licence form and `setuptools>=77`.
  - Evidence: `docs/reviews/2026-09-25-r110-spdx-licence.md`.

**Next quick win: R-100**, dead code removed. Then R-99 (ResourceWarnings
closed), and the docs items R-79, R-80, R-82 and R-83.

## Start here — 25 September 2026, later morning: main is v71; R-42 built (v72), not pushed

**Main is v71 at `62e87bf`.** Rodrigo merged #40 (R-33, v70, merge
`314e1f6`) and #41 (R-40, v71, merge `62e87bf`).

- **`fix/r42-typography-preflight-names-text`,** R-42 at v72, sits on
  `beb4c06`, which is in `main`. It is local and waits for Rodrigo's go, and
  its PR targets `main`.
  - A typography source-content refusal names the occurrence that holds the
    offending text, not the page's first.
  - Two independent passes: PASS. One major finding, a malformed
    `/CropBox` crashing the check, is fixed.
  - Evidence: `docs/reviews/2026-09-25-r42-content-refusal-names-text.md`.

**Next quick win: R-110**, the SPDX licence form in `pyproject.toml`. Then
R-100, R-99, and the docs items R-79, R-80, R-82 and R-83.

## Start here — 25 September 2026, morning: #40 open (v70); R-40 built (v71), not pushed

**Main is v69 at `b504821`** (#39, R-69 and R-97, CI only). Two things are
in flight:
- **#40** is open against `main`, with R-33 at v70.
- **`fix/r40-capture-source-pdf`** sits on #40, with R-40 at v71. It is
  local and waits for Rodrigo's go.
  - `rebuild` gives the original to every job, so a legacy capture bundle
    records `source_pdf`.
  - An independent pass: PASS, no findings.
  - Evidence: `docs/reviews/2026-09-25-r40-capture-source-pdf.md`.

**Next quick win: R-42**, a typography preflight refusal naming the
offending text. Then R-110, R-100, R-99, and the docs items R-79, R-80, R-82
and R-83.

## Start here — 25 September 2026, before dawn: #39 open (CI only); R-33 built (v70), not pushed

**Main is v69 at `19252b7`.** Two things are in flight:
- **#39** is open against `main`, with R-69 and R-97. It is CI only, with no
  version bump. Its two runs proved the cache fix: a miss that saved, then a
  hit with 0 KB fetched.
- **`fix/r33-field-fonts-keep-appearance`** sits on #39, with R-33 at v70.
  It is local and waits for Rodrigo's go to push.
  - `field_fonts` keeps each field's colour and size: on the wild forms,
    160 fields no longer turn black and 2 no longer auto-size.
  - Rule 1 passed. It found two minor latent bugs in the new code, both
    fixed with tests.
  - Evidence: `docs/reviews/2026-09-25-r33-field-appearance.md`.

**Filed in passing:** `field_fonts` skips a field whose `/FT` is set only
two or more levels up (the last REQUESTS row).

**Next quick win: R-40**, legacy capture bundles recording `source_pdf`.
Then R-42, R-110, R-100, R-99, and the docs items R-79, R-80, R-82 and
R-83.

## Start here — 25 September 2026, late night: main is v69; R-69 with R-97 built, not pushed

**Main is v69 at `19252b7`.** Rodrigo merged #38 (R-47), and GitHub
confirms it.

**`ci/r69-r97-discover-and-font-cache`** sits on `7e04250`, which is in
`main`. It carries R-69 with R-97. It is local, waits for Rodrigo's go, and
its PR targets `main`. The evidence doc still needs the PR's two CI runs: a
cache miss that saves, then a hit that fetches nothing.

**Next quick win: R-33**, `field_fonts` keeping a field's colour and size.
Then R-40, R-42, R-110, R-100, R-99, and the docs items R-79, R-80, R-82 and
R-83.

## Start here — 25 September 2026, later that night: #38 open (v69); R-69 with R-97 built

**Main is v68 at `aa54158`.** Two things are in flight:
- **#38** is open against `main`, with R-47 at v69.
- **`ci/r69-r97-discover-and-font-cache`** sits on #38. CI discovers its
  tests, and the font cache is keyed on the fetcher and saved before the
  suite. It is CI only, so there is no version bump. The evidence
  (`docs/reviews/2026-09-25-r69-r97-ci-discovery-and-font-cache.md`) still
  needs the PR's own two CI runs: a cache miss that saves, then a hit that
  fetches nothing.

**Next quick win: R-33**, `field_fonts` keeping a field's colour and size.
Then R-40, R-42, R-110, R-100, R-99, and the docs items R-79, R-80, R-82 and
R-83.

## Start here — 25 September 2026, night: main is v68; R-47 built (v69), not pushed

**Main is v68 at `aa54158`.** Rodrigo merged #36 (R-04, v67, merge
`9cfcf63`) and #37 (R-27, v68, merge `aa54158`). The app's session did the
merges on his word and retargeted #37 to `main` first; GitHub confirms both,
and main's CI on `aa54158` passed.

**`perf/r47-typography-verify-page-rects`** carries R-47 at v69. It sits on
`7a9d1a5`, which is in `main` with the same tree. It is local and waits for
Rodrigo's go to push, and its PR targets `main`.
- Typography verify reads each page's crop and source field rects once, not
  per glyph.
- On a filled N-400-sized form the verify's peak drops from 3.0–3.6 GB to
  about 170 MB, with byte-identical gate results.
- An independent pass on another model passed, with one minor note, ruled
  no change.
- Evidence: `docs/reviews/2026-09-25-r47-typography-verify-page-loads.md`.
  The measurement probe is `dev/probes/r47_verify_page_loads.py`.

**Filed in passing, not built:** typography verify FAILs correct lines drawn
in a face whose units-per-em is not 1,000, because MuPDF embeds widths
rounded down to whole thousandths (the last REQUESTS row). It waits for the
product.

**Next quick win: R-69 with R-97**, CI discovering its tests and keying the
font cache on the fetcher. Then R-33, R-40, R-42, R-110, R-100, R-99, and
the docs items R-79, R-80, R-82 and R-83.

## Start here — 25 September 2026, evening: #36 open (v67); R-27 built (v68), not pushed

**Main is v66 at `637e291`** (#35, R-05 and R-06). Two things are in
flight:
- **#36** is open against `main`, with R-04 at v67 and the v66 delivery
  record.
- **`fix/r27-field-fonts-variable-face`** sits on #36, with R-27 at v68. It
  is local and waits for Rodrigo's go to push. `field_fonts` embeds a
  variable face as its Regular instance, and Rule 1 passed after one fix: a
  temp file left behind on a failed input. Evidence:
  `docs/reviews/2026-09-25-r27-field-font-instance.md`.

**Next quick win: R-47**, typography verify reading page rects once. Then
R-69 with R-97, R-33, R-40, R-42, R-110, R-100, R-99, and the docs items
R-79, R-80, R-82 and R-83.

## Start here — 25 September 2026, later: #35 open (v66); R-04 built (v67), not pushed

**Main is v65 at `a9fd0a9`.** Two things are in flight:
- **#35** is open against `main`, with R-05 and R-06 at v66. Rodrigo asked
  for them to ship together.
- **`fix/r04-canonicalize-role-faces`** sits on #35, with R-04 at v67. It
  is local and waits for Rodrigo's go to push. The canonical text layer now
  covers the italic and bold-italic faces. Rule 1 passed. Evidence:
  `docs/reviews/2026-09-24-r04-role-faces.md`.

**Next quick win: R-27**, `field_fonts` refusing a variable face or
instancing it. Then R-47, R-69 with R-97, R-33, R-40, R-42, R-110, R-100,
R-99, and the docs items R-79, R-80, R-82 and R-83.

## Start here — 25 September 2026: R-02 shipped (v65); R-05 and R-06 built (v66), not pushed

**Main is v65 at `a9fd0a9`** (#34, R-02). Its tree is the reviewed
`4cf1054`.

**Local branch `fix/r05-legacy-output-alias`** sits on `main` and waits for
Rodrigo's go to push, and for how the quick wins are grouped into PRs. It
carries:
- **R-05.** A legacy build refuses an output or scale-report path that names
  one of its inputs, and `rebuild` protects its inputs, including a file
  forwarded as `--flag=value`. Evidence:
  `docs/reviews/2026-09-24-r05-output-alias.md`.
- **R-06.** Text handed to the Story engine lands as written, `&` escaped
  twice because MuPDF 1.28.2 decodes twice, and notices are fixed too.
  Rule 1 passed. Evidence: `docs/reviews/2026-09-24-r06-story-escaping.md`.
- The v65 delivery record, and the product's hold on the verify
  `--flag=value` proposal.

**Next quick win: R-04**, canonicalizing every role face so italic jobs
verify. Then R-27, R-47, R-69 with R-97, R-33, R-40, R-42, R-110, R-100,
R-99, and the docs items R-79, R-80, R-82 and R-83.

## Start here — 24 September 2026, later still: R-02 built (v65), not yet pushed

**One local branch waits for Rodrigo's go to push:**
`fix/r02-small-print-clamp`, from `main` (`154f842`). It carries:
- `4fd6b64`, the v64 delivery record;
- R-02 (v65).

**R-02.** A shrunk run is drawn at the size that fits its room, never
larger than its source, and the 0.7× gate sees that ratio, at all four
legacy shrink sites. The 4.0 pt lift is gone. Small print below the floor
now refuses with the existing line, and `allow_scale` ships it at the
fitted size. The details are in `docs/reviews/2026-09-24-r02-small-print.md`
and its DECISIONS row. Rule 1 passed on Sonnet.

**Next** in the assignment order: the quick wins, XS each (R-05, R-06, R-04,
R-27, R-47, R-69 with R-97, R-33, R-40, R-42, R-110, R-100, R-99, then the
docs items R-79, R-80, R-82, R-83). E12 comes first the moment its rulings
arrive.

## Start here — 24 September 2026, late: item 3 shipped (v64); R-02 next

**Main is v64 at `154f842`.** Rodrigo merged two PRs in order, each with a
merge commit, and every CI check passed on each tested head:
- #32, the R-03 and R-01 delivery record (`c0d49e9`);
- #33, item 3 with R-64 (`154f842`).

The section below was written before the push; its branches are now
merged, and they are still on GitHub. This delivery record is on the
branch `docs/delivered-item3`.

**Next: R-02, the 4.0 pt clamp.** Review priority 4 in
`docs/REQUESTS-from-product.md`. E12 comes first the moment its six
rulings arrive.

## Start here — 24 September 2026, night: item 3 built (v64), not yet pushed

**Two local branches, stacked, waiting for Rodrigo's go to push:**
- `docs/delivered-r03-r01`, from `main`: records R-03 and R-01 as
  delivered. Docs only.
- `fix/rotate-pages-unrotated-space`, on top of it: item 3 plus R-64, v64.

**Item 3.** A `/Rotate` page now extracts and rebuilds exactly like the
same page unrotated.
- The cause and the fix are in
  `docs/reviews/2026-09-24-rotate-pages.md` and the DECISIONS row.
- `segments.json` gains a `geometry` key. A file without it is refused on a
  rotated page, with a stable line from `failure-modes.md` §13; the app
  agreed to that refusal.
- **R-64.** The corpus suite identity-rebuilds every `translate` fixture and
  checks where each run starts.
- **Rule 1** passed on Sonnet with no blocker. The pixel pass found 0
  differing pixels against the rotated control, where v63 differed by 7,142
  to 9,351.

**Filed here, not assigned:**
- A right-to-left SOURCE is rebuilt one source width to the right. The app
  says not now: right-to-left is out of its MVP. An expected-failure test
  pins it.
- A reading-frame layout for rotated runs: not now.
- The span-union box, typography-1's rotated `page.rect`, and
  `python -m` stages printing nothing: proposed.

**Next** in the assignment order: R-02, the 4.0 pt clamp. E12 comes first
the moment its rulings arrive.

## Start here — 24 September 2026, evening: R-03 and R-01 shipped (v63); item 3 next

**Main is v63 at `0819091`.** Rodrigo merged three PRs in order, each with
a merge commit, and every CI check passed on each exact head:
- #29, the review (docs only);
- #30, R-03 (v62);
- #31, R-01 (v63).

Their branches are still on GitHub. Two local-only refs hold the tips from
before the stacking rebase: `backup-local/r03-before-stack` and
`backup-local/r01-before-stack`. Ask before deleting any of them. The
inbox's status section and rows record the delivery.

**Next: item 3, the `/Rotate` blank page, with R-64.**
- **Cause.** Extract reads text through a display list, which keeps the page
  rotation, so segment origin, bbox and dir are in the rotated (visible)
  space. Retypeset draws with `TextWriter`, `insert_htmlbox` and the Story
  engine in the unrotated page space. The two differ by
  `page.derotation_matrix`.
- **Evidence.** Every extract, retypeset and verify site has been measured
  for which space it uses. That map, and the fix design, go into item 3's
  evidence doc when it ships; until then they exist only in this session.
- **Also found.** Legacy verify reads no segment geometry. It catches this
  defect only when the text leaves the page entirely: ink 0.00 and missing
  targets.

**R-94:** Rodrigo said "not yet" on 24 September, so the repository stays
public for now.

## Start here — 24 September 2026, later: review delivered; its findings assigned, R-03 first

**The review.** While E12 waits on the product's six rulings, Rodrigo
directed a tech-debt review. It is `docs/REVIEW-2026-09-24.md`: 110 items
plus 19 notes on rows already tracked. It found no tracked change and fixed
nothing. Its twelve most important claims were each reproduced by two more
independent refuters. Everything else was confirmed by one verifier, so
reproduce it again before building on it. Nothing in it is assigned:
Rodrigo picks items (`docs/DECISIONS.md`, 2026-09-24).

**Assigned, in this order** (Rodrigo's ruling A, relayed by the app): R-03, R-01, the `/Rotate 90`
blank page with R-64, R-02, the quick wins, then performance. E12 comes first again the moment
its rulings arrive. The inbox's status section carries the order, the holds and the shared
acceptance bar; the rows carry each ID. Tell the app's session when each item starts, blocks
or ships.

**Decision pending: R-94.** The repository is public, and has been since 2
September. The 19 September audit and A20 assume it is private. The review
recommends choosing now between making it private until A20's content
review is done, or running that review against the public tree and all
branches.

**A regression to fix under A21.** Since PR #27,
`claude plugin validate .claude-plugin/plugin.json --strict` exits 1: a
`CLAUDE.md` at the plugin root is not loaded as plugin context. CI checks
only the marketplace manifest.

## Start here — 24 September 2026, on the Mac: set up and verified; E12 assigned, blocked on rulings

**Verified state.** `origin/main` is `0542dc2` (v61). CI passed on it (run
35981365585), and there is no release or tag. PR #27 (Rule 4: the product
directs this library; the app calls it GOV-2026-09-24) passed all three
checks on `b24f03a` (run 35978209544). It was merged on Rodrigo's word as
`0542dc2`, whose tree is `b24f03a`'s. It changed only docs, so the version
stays 61. Its branch `docs/app-directs-skill` is still on GitHub.

**This Mac's checkout.** Local `main` held two commits from 12 September
that were on no remote. `ca2dd06` adds `dev/canary/GPT6_PROMPT.md`, which its
message calls the only copy. `c1d9c93` is the Mac's own lane B row P9
restructure (root `AGENTS.md`, `dev/STATUS.md`, `dev/DECISIONS.md`); the
Windows line has its own `AGENTS.md` and `docs/DECISIONS.md` instead. `main`
and `origin/main` had diverged (2 and 206 commits), so `git pull --ff-only`
exited 128. On Rodrigo's word both commits are now on GitHub as
`backup/mac-main-2026-09-12` (at `c1d9c93`) and local `main` was reset to
`origin/main`; whether either commit belongs on `main` is a separate
decision. Everything below ran on `221a86f`; #27 changed no code.

**Setup, as `pdf-translate/README.md` says.** `pdf-translate/.venv` is
CPython 3.14.6. uv created it without pip, so dependencies go in with
`uv pip install --python .venv/bin/python -r requirements.txt`, which gives
PyMuPDF 1.28.2, pikepdf 10.12.0 and fontTools 4.64.0.
`tools/fetch_test_fonts.py` and its `--check` both exit 0, with 20 faces.
`pdf_translate.__file__` resolves into this checkout and `__version__` is 61.

**The suite on macOS.** CI's four test steps, run locally on `221a86f` in
about seven minutes: the 22 unittest modules ran 695 tests, CI's count on the
same commit, with 1 failure, no errors and no skips; the canary's 15 tests
and the binary-integrity 3 passed; the eval fixtures built. The failure is in
the test, not the library, and only on a Mac:
`HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`
compares `os.getcwd()` with the temporary path as strings
(`pdf-translate/tests/test_pipeline.py:3958`), and macOS reports
`/var/folders/…` as `/private/var/folders/…`. Run by hand with the paths
compared by `realpath`, the same rebuild exits 0 and prints its PASS line.
Nobody assigned the fix, so it is proposed in the inbox rather than made.

**Next: E12, the one assignment.** Under Rule 4, work comes from
`docs/REQUESTS-from-product.md`. This session sent the app's session the v61
notice and asked what to prioritize. The app received v61, and its pin stays
v54 on Python 3.12. It put the priority to Rodrigo, who ruled on 24
September (option C). The library's priority 1 of 1 is E12, a compact,
deterministic output save; nothing else is assigned, and Rodrigo directs
library tech debt himself (`docs/DECISIONS.md`, 2026-09-24).

The E12 row carries the behaviour and seven observable acceptance checks.
Checks 1 and 2 are shown red on the unfixed shape before the change lands,
and Rule 1 applies. Tell the app's session when E12 starts, is blocked or is
delivered. If E12 as written proves unbuildable or wrong for this code, stop
and report the measurement rather than substituting a different design.

**E12 is blocked, as of 24 September.** It was measured before any build:
`docs/reviews/2026-09-24-e12-measurement.md`, with the raw evidence in the
ignored `runs/2026-09-24-e12-measurement/` on the Mac. Three acceptance
checks conflict:
- check 1's 2.5× ceiling fails on the three base-14 fixtures unless
  hinting is dropped, which breaks a strict check 3;
- check 2 contradicts the full field face on forms;
- the corpus is all one-page fixtures, so checks 1, 2 and 6 go red only on
  constructed multi-page fixtures.

Six rulings went to the app's session. Build nothing until they come
back.

The backlog in `dev/goals/PROGRAM.md` (A21 and the rest) and this library's
own proposals (the macOS test, A04, A05, A14) stay unassigned; this
supersedes the "Next" of the section below. Merged PRs #22, #26 and #27
still have their branches on GitHub; deleting them is Rodrigo's call.

## Start here — 23 September 2026, night: reconcile, A02 and A06 merged; main is v61

**Verified state.** On Rodrigo's instruction the three PRs were merged into
`main` in order, each after its CI passed on the merged result: #23
(reconcile, merge `7af5d84`), #24 (A02, merge `fdbcd82`) and #25 (A06, this
change, which also carries the version bump). `main` declares **v61** in all
four version sources, and `VersionLockstepTests` pins it. No GitHub release or
tag was made; the repository has none.

v61 changes two things a consumer can see:

- Every verify run prints one `page parity` line, and a missing, extra,
  rotated or resized page FAILs the new `page-parity` gate. `compare` and
  `render` show every page and exit 1 when the page counts differ, and
  `finish` returns compare's code.
- A default legacy `pipeline.py rebuild` verifies against the mapping it
  built from. An empty target, a dropped marker or a translated identifier
  now fails it: exit 1 where it used to exit 0.

The next section ("evening") is the state just before the merges. Its branch
table, CI runs and independent passes describe what landed.

**Cleanup.** After the merges, the three merged branches were deleted on GitHub
on Rodrigo's word; each PR page can restore its branch. `main` is the only
branch this work needs. The old checkout's remote branch
`codex/b1-design-canvas` is still on GitHub.

**Only on the Windows machine where this was built, left standing on purpose
(delete only on Rodrigo's word):** the three local branches and their worktrees
under `C:/Dev/worktrees/` (`pdf-translate-reconcile-b1`, `pdf-translate-a02`,
`pdf-translate-a06`), whose ignored `runs/` folders hold the raw evidence the
23 September reviews cite; the throwaway `trial/integrate-reconcile-a02-a06`
worktree, superseded by `main`; the old checkout `C:\Dev\pdf-translate-skill`
with its snapshot; and `probe/b1-baseline-anchor`. Nothing open depends on
any of them.

**Continuing on any machine.** Clone or pull `main`, then set up from
`pdf-translate/` as its README says: Python 3.14,
`python -m pip install -r requirements.txt`, `python tools/fetch_test_fonts.py`
(test fonts are never committed) and `python tools/fetch_test_fonts.py --check`.
Before trusting a test result, confirm `pdf_translate.__file__` points into the
checkout under test. A full suite took 7 to 15 minutes per runner on CI; GitHub
CI runs it on every PR and every push to `main`, and `workflow_dispatch` covers
other branches.

**Next:** the backlog in `dev/goals/PROGRAM.md`. A21's manifest validation is
the smallest item; A04's process validation and A15's broader wording stay
open. B1 wrapping stays deferred. The separate web app keeps its own pin until
it chooses to adopt v61.

## Start here — 23 September 2026, evening: reconcile, A02 and A06 are built and green on CI; integration is Rodrigo's call

**Verified state.** Remote `main` is still **`178a06f`** (v60). Three branches
from `178a06f` were pushed for CI; nothing was merged or released and no PR
was opened. Each local branch is ahead of its remote by docs-only commits that
record the CI results below and, on A06, its independent pass. There is also a
throwaway local merge of all three:

| Branch | Head | Worktree | State |
|---|---|---|---|
| `chore/reconcile-b1-checkout` | pushed `8a98afc` | `C:/Dev/worktrees/pdf-translate-reconcile-b1` | Done. Full suite 670 OK locally and on CI. Independent review: approve, with two cosmetic nits. |
| `fix/a02-page-count` | pushed `5348082` | `C:/Dev/worktrees/pdf-translate-a02` | Done. CI 687 OK on Linux and Windows. Boundary fix `d9efd44`. Independent verification: verified with findings, both handled. |
| `fix/a06-rebuild-mapping-checks` | pushed `9f9365d` | `C:/Dev/worktrees/pdf-translate-a06` | Done. 30/30 documented examples behave as specified. CI 678 OK on Linux and Windows. Independent verification (real CLI runs, no suites): verified with findings, both existing behaviour, identical on main. |
| `trial/integrate-reconcile-a02-a06` | local only | `C:/Dev/worktrees/pdf-translate-trial` | All three merged. Only `docs/DECISIONS.md` conflicted (tail appends; all 60 rows kept). Links, compilation and binary integrity pass. **Full suite not run.** |

Evidence: `docs/reviews/2026-09-23-b1-checkout-reconciliation.md` (this
branch), `docs/reviews/2026-09-23-a02-page-parity.md` (A02 branch) and
`docs/reviews/2026-09-23-a06-rebuild-mapping-checks.md` (A06 branch). The old
checkout at `C:\Dev\pdf-translate-skill` carries a pointer section at the top
of its own handover; otherwise it is exactly as snapshotted.

**The local machine crashed twice during full-suite runs** on 23 September,
and one run ended in a native Python crash (exit 139). Heavy local runs were
stopped.

**Decision (Rodrigo, 23 September): run the owed full suites on GitHub CI.**
The three branches were pushed as they stand here, and the workflow was started
on each with `workflow_dispatch`: CI runs automatically only for pushes to
`main` and for pull requests, and no PR was opened. Look up the runs with
`gh run list --workflow tests.yml`. The trial branch was not pushed.

| CI run | Branch | Linux | Windows | Canary | Other |
|---|---|---|---|---|---|
| 35935410494 | reconcile `8a98afc` | 670 OK | 670 OK, 1 skip | 15 OK both | new binary-integrity step 3 OK on both OSes; manifest green |
| 35935412655 | A02 `5348082` | 687 OK | 687 OK, 1 skip | 15 OK both | manifest green |
| 35935414545 | A06 `9f9365d` | 678 OK | 678 OK, 1 skip | 15 OK both | manifest green |

The Windows skip is the existing cross-drive relative-path test. The only
annotation is GitHub's notice that the `ubuntu-latest` label moves to Ubuntu 26
on 19 October 2026.

To integrate: merge in the order reconcile → A02 → A06, keep every DECISIONS
row (the trial branch shows the result), and bump the version once, to v61.
The release note should name two behaviour changes. Every verify run prints a
`page parity` line and FAILs a missing, extra or reshaped page. A default
legacy rebuild now runs the mapping checks and can exit 1 where it exited 0.

**Still open, unchanged:** A04's process-isolated validation, A15's broader
public wording, and the other A-rows in `dev/goals/PROGRAM.md`. B1 wrapping
stays deferred.

## Start here — 23 September 2026, old B1 checkout reconciled; A02 then A06

**Verified state.** Remote `main` is **`178a06f`**, v60: PR #22 merged at
17:15Z. Its post-merge CI run `35894389833` passed: Linux 670 tests OK and
Windows 670 OK with one skip, 15/15 canary tests on each, and the manifest job.
No PRs are open. Nothing in this section was pushed, merged or released.

**The old checkout is reconciled, not merged, and B1 is not implemented.**
`C:\Dev\pdf-translate-skill` stays on `codex/b1-design-canvas` at `d2b3395`.
Its 17 edited and 39 untracked files are untouched; a byte snapshot is in its
ignored `runs/b1-checkout-reconciliation-2026-09-23/`. Everything useful from it
is now on the **local** branch `chore/reconcile-b1-checkout` in
`C:/Dev/worktrees/pdf-translate-reconcile-b1`, based on `178a06f`:

| Commit | What |
|---|---|
| `f7326cf` | `.gitattributes` + binary-integrity test + CI step (the three unique commits, reviewed together) |
| `3860c66` | the separate local B1 baseline-anchor probe, cherry-picked from `12c730c` |
| `d99320b` | 38 evidence files: B1 design canvas, dated reviews, probes, data, explainers |
| `509c39e` | A04 concurrency guidance (docs and docstrings only) |
| `0cd8bc2` | A15 README facts, re-measured on main (20 fonts, 670 tests) |
| `498dec4` | backlog, DECISIONS (18 carried + 2 new rows), product inbox, brief, checklist |
| next commit | the reconciliation report and this handover |

Full discovery on the branch at `498dec4`: **670 tests OK in 484.230 s**, the
same count as clean `178a06f` (578.251 s). Every item's disposition, with the
commands that checked it:
[`docs/reviews/2026-09-23-b1-checkout-reconciliation.md`](../../docs/reviews/2026-09-23-b1-checkout-reconciliation.md).
In short: the uncommitted v61 label was dropped (main owns v59/v60), and the A06
verification-examples slice moves with the A06 fix.

**B1 stays deferred.** The design is approved and the synthetic, anchor and
capture evidence is preserved. No genuine fit-refusal case exists, and no
wrapping code was written. Reopen it only on such a case or an explicit change
of scope.

**Next: A02, then A06.** Each is a separate change from `178a06f`: A02 makes
legacy verify and the inspection outputs fail on missing or extra pages, and A06
stops the default legacy rebuild from skipping mapping-dependent checks. Their
branches, results and review state are added to this section as they complete.

**Before integrating.** Three local branches come off `178a06f`. Expect
conflicts only at the tail of `docs/DECISIONS.md` and the top of this file; keep
every row and section. Choose the next version once, at integration (DECISIONS,
23 September); main's `178a06f` already reuses `b20fadd`'s v60. On a Windows
clone with `core.autocrlf=true`, check the tracked files out again after pulling
`.gitattributes`. Do not run `git add --renormalize .` first: it stages
already-smudged binaries as they are.

**Leave in place until Rodrigo decides:** the original checkout and its branch;
`origin/codex/b1-design-canvas` (pushed at `6236be6`, no PR ever opened); and
`probe/b1-baseline-anchor` (`12c730c`, local only, now carried).

## Start here — 23 September 2026, PR #22 merged into main

Rodrigo requested final coordination with the PDF Translator task and a scoped
PR. Its independent final review passed another **88 focused tests** and both
legacy/typography combined workflows; no blocker remained. Exact reviewed
candidate **e2972cfc72c59cec2cdcec9c1299701b03042f01** was pushed on
`codex/simplify-integration-review` and reviewed in:
https://github.com/ariasr47/pdf-translate-skill/pull/22

The final PR-readiness check found that CI omitted the A03/capture regression
modules. Independently approved CI-only follow-up **b39079f** adds exactly those
two modules to both platform jobs, retaining all previous modules. Linux CI
then passed 670 tests plus 15 canary tests, but Windows found nine errors in
UTF-8 JSON test readers using CP1252. Test-only fix **7eeccf2** adds explicit
UTF-8 to the five affected reads, retaining all assertions and production code.
The failure was reproduced locally with UTF-8 mode disabled; 99 focused tests
then passed, plus an independent 27-test CP1252 run. **7eeccf2 is the final PR
head**; CI run **35891927585 passed all jobs**. Linux: 670 tests OK plus 15
canary tests; Windows: 670 discovered, OK with one existing cross-drive skip,
plus 15 canary tests. Both fixture-generation steps and plugin/version checks
passed. No remaining review/CI findings. Rodrigo then explicitly authorized
the merge; the PDF Translator task merged PR #22 at **2026-09-23T17:15:44Z**,
guarded against the exact reviewed head. GitHub's merged PR metadata and
`git ls-remote origin refs/heads/main` independently confirm merge commit
**178a06ffd4e45af30c0366c5f0fb995f8495cb5f** on remote main. Production code
is unchanged from independently reviewed e2972cf. No release, version bump,
deployment or consumer pin/runtime change was performed. The combined
worktree remains clean; preserve the original dirty B1 checkout. Older
sections below record historical states, including earlier no-merge status.
Current review and PR evidence:
`docs/reviews/2026-09-23-simplify-c828dd6-integration-review.md`.

Separate next-work priority: **A02**, then **A06**. Final consumer coordination
also corrected the earlier adoption shorthand: upstream metadata requires
Python >=3.14 while the app remains on Python 3.12/library v54. Adoption needs
an isolated supported Python 3.14/exact-candidate comparison with identical
translation inputs and existing privacy/job-lifetime behavior. It is not a
routine install into 3.12; no consumer runtime or pin change is authorized here.

## Start here — 23 September 2026, cleanup and combined integration reviewed

Independent Codex review closed the remaining capture JSON-null finding in
`simplify/upstream-cleanup` at **c828dd606be40b7f18de67f1727fea1e596b722e**.
Its full suite passed **656 tests**. The supplied A01 and A03 cleanup heads
remain **c4484b7** and **2249171**, clean and unchanged in their separate
`C:/Dev/worktrees/simplify-a01` and `simplify-a03` worktrees.

A combined candidate now exists locally on **codex/simplify-integration-review**
at **e2972cfc72c59cec2cdcec9c1299701b03042f01**, in:
`C:/Users/rodri/.codex/worktrees/simplify-integration-review/pdf-translate-skill`.
It contains all three reviewed heads; the worktree is clean. Documentation
conflicts in both DECISIONS and HANDOVER were resolved by preserving all
entries. Production code merged without manual changes.

The combined full suite passed **670 tests**. Fresh CLI, nine-fixture verdict,
serialized-result and API comparisons match b20fadd. Ten capture failure-path
outcomes match baseline; consecutive rebuild/invalid-review/refusal/recovery
workflows pass in both legacy and typography formats. No remaining actionable
review findings. Evidence and exact commands:
`docs/reviews/2026-09-23-simplify-c828dd6-integration-review.md` in this original
checkout, with raw evidence under `runs/simplify-review-c828dd6/`.

Next: use the existing combined candidate for upstream integration/release
preparation, rather than recreate it. Remote main was verified at b20fadd/v60
with no open PRs. No push, merge to main, release, deployment or consumer pin
change was performed. The PDF Translator task was updated and recommends
integration/release preparation; it reports no new upstream blocker. Adoption
still needs separate Python 3.12 and same-input rendering comparisons in the
consumer, and the pin remains unchanged. This original checkout remains dirty
on the earlier B1 branch; do not merge it wholesale. The earlier sections below
are historical.

## Start here — 22 September 2026, A03 completed locally after A01

Rodrigo authorized the next repair recommended by **Approve sandbox proposal**
(`01a0ca6d-e3e3-7e31-84e8-2b53e80b5dd7`). A03 is now committed locally as
**30c4805a3027fe3f2492edd4d2745c467646d68a** on
`codex/a03-stale-rebuild-report`, based on main b20fadda/v60, in:
`C:/Users/rodri/.codex/worktrees/pdf-translate-a03-stale-report/pdf-translate-skill`.
That worktree is clean. This original checkout's earlier dirty work remains
preserved. Main and the consumer pin are unchanged; nothing was pushed or
published.

Rebuild invalidates its default and selected verification reports before
mapping load or stages can fail. Early failures/refusals preserve prior PDFs;
current status plus a fresh report establish current verification evidence.
Unsafe report paths and unrelated files are preserved/refused. No manifest,
rendering/API change, or transactional PDF/sidecar redesign was introduced.
Evidence and limits: that worktree's
`docs/reviews/2026-09-22-a03-stale-rebuild-report.md`.

Full **657 tests passed in 415.069s**, no failures/errors/skips. Final affected
tests passed after test-only strengthening; independent review found no
actionable issues, with 339 compatibility tests, four real process-kill
sequences and two real locked-report refusals passing. Ordinary 12-command
CLI parity matches v60. Existing resource warnings are documented.

A01 remains separate at **41bdf99** below. Both are unpublished v60-based
candidates ready for integration; pick a release version against current main.
Then take A02/A06 separately unless consumer evidence changes priority.
The app's approved sandbox work remains independent and on its existing pin.

## Start here — 22 September 2026, A03 completed locally

Rodrigo authorized the next bounded upstream repair after coordination with
the PDF Translator task **Approve sandbox proposal**
(`01a0ca6d-e3e3-7e31-84e8-2b53e80b5dd7`). That task's sandbox work is independent;
its current pin is unchanged. No product source was read or copied.

This managed checkout is `codex/a03-stale-rebuild-report`, based on verified
GitHub main **b20fadda/v60**. It invalidates default/selected verification
reports before a rebuild can fail, preserving previous PDFs on early failure
or refusal. Unsafe report paths and files that are not recognizable verifier
output are refused. Read `docs/reviews/2026-09-22-a03-stale-rebuild-report.md`
for acceptance results, commands, independent real-process/locked-file probes
and limitations. This is existing report/return-code behavior, not a manifest
or a transactional PDF/sidecar publication redesign.

Independent review found no actionable issues: 339 compatibility tests passed,
10 strengthened typography tests passed, four real interrupted subprocesses
recovered, and two real locked-report cases safely refused. Author red/green,
final focused tests and 12-invocation ordinary CLI parity are recorded there.
Full discovery passed **657 tests in 415.069s**, no failures/errors/skips;
the final test-only strengthening passed the affected author and independent
reruns. Existing file-handle ResourceWarnings remain documented in the report.

The candidate remains unpublished and declares v60; choose a release version
against current main when preparing publication. A01 is a separate verified
local commit **41bdf9911c81116ab282aa6e39ce3bee0ca82b04** on
`codex/a01-invalid-review-refusal`; it is not included here. Integrate those
bounded candidates before separately taking A02, A06 or capture/B1 work.
The original `codex/b1-design-canvas` checkout's dirty work remains intact.
Do not merge that older branch wholesale or treat its v61 metadata as a release.

## Start here — 22 September 2026, assigned A01 repair completed locally

After the review below, the PDF Translator task assigned A01 on Rodrigo's
behalf. It is now verified and committed **locally only** as
**41bdf9911c81116ab282aa6e39ce3bee0ca82b04** on
`codex/a01-invalid-review-refusal`, based on main b20fadda/v60, in:
`C:/Users/rodri/.codex/worktrees/pdf-translate-a01-review-refusal/pdf-translate-skill`.
That worktree is clean. This original checkout and its earlier dirty work were
preserved; no fix was applied here. Main and the app pin have not changed.

The fix propagates existing review validation/loading errors into delivery
refusal, reports errors, and writes a failed review state. Resolved valid
reviews deliver; explicit no-review remains disclosed. A prior final PDF is
untouched on refusal and never serves as evidence this attempt succeeded.
It does not redesign validation, rendering, or A03's artifact lifecycle.

Evidence in that worktree:
`docs/reviews/2026-09-22-a01-invalid-review-refusal.md`.
Full suite **655 tests OK in 353.699s**, no failures/errors/skips. Independent
review: no actionable issues; **81 focused tests OK**, plus **31 invalid-review
CLI cases refused**, valid controls and typography stale-binding controls.
12-invocation ordinary CLI parity matches v60. The existing NOTES.md resource
warning remains. No push, merge, release, PR or consumer pin changes.

The local candidate still declares version 60; select a release version
against current main when preparing publication. Next work is integration of
this bounded candidate, then separately A03/A02/A06. The app owns staging
translation and Python 3.14/exact-pin adoption. Do not repeat or duplicate A01.

## Start here — 22 September 2026, A01 local repair verified

This managed checkout is `codex/a01-invalid-review-refusal`, based on remote
main **b20fadda (v60)**. The original checkout's dirty B1/v61 work is separate
and untouched. A01 was assigned through the PDF Translator task after Rodrigo
requested review and coordination. No push, merge, publication, PR mutation,
consumer pin change or product-source access is part of this repair.

The local fix makes existing review validation/loading errors block ordinary
finish and prints those errors. Valid resolved reviews still deliver; explicit
no-review still delivers with disclosure and retains errors. An old final PDF
is preserved on refusal, with a fresh failed review state. No renderer, review
schema or broader A03 artifact-lifecycle change is included.

Evidence: `docs/reviews/2026-09-22-a01-invalid-review-refusal.md`. Tests first
showed 29 failing assertions. Focused 81 tests pass; independent reviewer found
no actionable issues after a separate 81-test run and 31 invalid-review CLI
cases. Full discovery passes **655 tests in 353.699s**, with no failures,
errors or skips. The ordinary 12-invocation CLI parity probe matches v60.
Version metadata remains 60 for this unpublished candidate; select the next
release number against current main when preparing publication.

Next after A01: separately scope A03, A02 and A06. The new typography
near-floor capture omission and B1 evidence/containment work remain separate.
The app task owns staging translation and Python 3.14/exact-pin adoption.
Keep capture off for production customer jobs under its existing TTL promise.
The earlier sections below describe historical work, not this branch.

## Start here — 22 September 2026, review complete; A01 recommended next

Fresh review: `docs/reviews/2026-09-22-yesterday-review.md`. GitHub main is
**b20fadda, v60**, zero open PRs. This checkout remains **6236be6** on
`codex/b1-design-canvas`, two unique commits and 36 behind main; its 37
pre-existing dirty/untracked entries were preserved. Do not interpret the
uncommitted v61 metadata as a complete release or merge this work wholesale.
The earlier start-here sections below are historical, not current state.

Eight PRs merged on 21 September local time, including typography, refusal
capture and dependency diagnostics. Two local repository/CI commits remain
unmerged here. Separate `probe/b1-baseline-anchor` at `12c730c` demonstrates
six anchored synthetic successes, independently reproduced today; no B1
wrapping implementation or customer recovery rate follows from that result.

Fresh v60 checks reproduce A01 invalid-review delivery, A03 stale output/PASS
report, A02 legacy page-count acceptance and A06 default mapping omission.
New P2: successful typography builds ignore near-floor capture (0.7402 and
0.7284 both miss capture_below=0.75). Full discovery exercised 649 tests;
the sole test with errors used historical Git archives from the nested export
and passed unchanged after correcting Git context. Six separate typography
acceptance cases PASS, verify 0; three binary-integrity tests pass. See the
review for exact commands, counts, evidence limits and logs.

Rodrigo requested coordination with the PDF Translator task, **Boot Spire Tech
web app** (`01a0bc1c-cdb2-7b93-8860-0154a450beb4`). It confirms app pin v54
`9675c619`, Python 3.12 and legacy mappings, and recommends assigning **A01**
as the next bounded upstream repair. The app owns staging validation and
isolated Python 3.14/exact-pin adoption. Capture stays off in production;
customer-PDF retention beyond job TTL is outside the product promise.

**Next recommendation: A01 only, from clean current main.** Invalid review
inputs must block delivery; resolved valid reviews succeed; explicit no-review
remains disclosed; a stale final file is not success evidence. Include
end-to-end finish checks for typography review-binding errors. Queue
A03/A02/A06 separately. This review did not start implementation, change pins,
push, merge, publish or mutate a PR. The report contains the handoff and
observable acceptance checks; do not repeat the investigation first.

## Start here — 21 September 2026, typography MERGED; B1 is the only thread left

`main` = **`d4d85be`**, **v59**, **zero open PRs**. Six PRs landed today:
#15 (scale ratio), #16 (NOTES.md ignore), #12 (terminology loop, v57),
#13 (E3, v58), #18 (Python 3.14 only) and #17 (typography, v59, all nine
tasks). The typography worktree at
`C:/Users/rodri/.codex/worktrees/typography-preservation/pdf-translate-skill`
is merged and can be removed whenever you like.

This original checkout is still on `codex/b1-design-canvas` at `48dffcf`
with its 37 dirty paths untouched, including the v61 metadata. That metadata
now sits BELOW main: main is v59, so the dirty work renumbers to 60+ when it
lands, which is what choosing 59 implied.

**Python is 3.14 only.** `requires-python`, the `compatibility:` line, the
README and the CI matrix all agree, and the matrix is two jobs. Checked
before narrowing: no file used a 3.11+ construct and all 22 modules parsed
under 3.10 rules, so the old floor was real and this locks out 3.10 to 3.13.

**Still unverified on typography:** the Codex host leg. `codex-cli 0.147.0`
reports its configured `gpt-6-astra` model needs a newer CLI. A host
mismatch, not a result about the code. Also: the eight CJK slanted-role
cells have no measured positive case, and language/emphasis semantics need
a qualified reader.

**Next action: rule on B1.** It is the only thread with no path forward.
Blocked on genuine fit-refusal evidence after three attempts came back
empty: the local archive had none, the web app reported none, and the
authorized capture returned a known SUCCESS. Two of its three measured
engineering blockers cleared today — the scale-report bug (#15) and
occurrence addressing (typography). What remains is baseline anchoring,
plus the evidence problem. Three options were put on the table: add a
capture hook so future refusals are retained (recommended), rule that
synthetic evidence is enough, or keep B1 parked. See
`docs/design/B1-line-wrapping/README.md` and
`docs/reviews/2026-09-19-b1-recovery-probe.md`.

## Earlier — 21 September 2026, typography COMPLETE and awaiting your call

All nine tasks of the approved typography plan are implemented and committed.
Branch `codex/typography-preservation` at **`444a644`**, working tree clean, in
`C:/Users/rodri/.codex/worktrees/typography-preservation/pdf-translate-skill`.
**Local only.** The plan requires asking separately before any push, merge or
release, and that has not been asked.

The branch has `main` merged in, so it carries PRs #12, #13, #15 and #16.
It ships as **version 59** in all four sources, chosen once v57 and v58 landed.
The uncommitted v61 metadata in this original checkout renumbers when it lands;
nothing on the branch touches it, and this checkout's dirty work is untouched.

The capability announces itself through
`pdf_translate.MAPPING_FORMATS == ('legacy', 'typography-1')`, not through the
version number. `references/typography.md` documents it, with every example
copied from a verified probe artifact.

Measured on the branch, not inherited: full discovery **617 tests OK**; both
parity runners byte-identical to the frozen baseline at version 59; the six-case
acceptance probe exit 0 against an actual **installed copy** outside the
checkout, with the probe's own artifact recording the task-local package path
and version it measured.

**Not done, and not claimed: the Codex host leg.** `codex-cli 0.147.0` reports
that its configured `gpt-6-astra` model needs a newer CLI. That is a host
mismatch, not a result about this code, and upgrading that install was outside
the task. Dual-host acceptance is therefore incomplete. A01 and the other
public-readiness blockers remain open, and B1 is still blocked on genuine
fit-refusal evidence.

**Next action: decide what happens to `444a644`.** Push and open a PR, keep it
local, or ask for a review pass first. Merging `main` into it again is cheap if
`main` moves.

## Earlier — 20 September 2026, typography Task 8 committed; Task 9 PARKED

A Codex session executing the approved typography plan stopped mid-run on a
provider usage limit. A Claude session recovered it, re-verified every gate
instead of trusting the unfinished notes, and committed Task 8.

State: managed isolated checkout
`C:/Users/rodri/.codex/worktrees/typography-preservation/pdf-translate-skill`,
branch `codex/typography-preservation`, HEAD **`cf78555`**, working tree clean.
Tasks 1–8 of nine are complete and committed; Task 9 has not started.
The original checkout `C:/Dev/pdf-translate-skill` still holds its dirty
v61/B1/public-readiness work untouched. No push, merge or PR change was made.

Re-verified in this session, not inherited: full discovery **611 tests OK in
441.631s**, no failures, errors or skips; canary 15 OK; both parity runners
exit 0 with all four stdout/stderr captures `diff`-identical to
`runs/typography/baseline-*`; the six-case acceptance probe exit 0 with
`typography=PASS`, `verify=0` and equal source/final page counts. The
interrupted session's own `runs/typography/task8-final-full.log` was found on
disk at 611 OK / 442.695s and names an identical set of 598 test methods.

One defect was found while reproducing: the acceptance probe's documented
command relied on the ambient interpreter, so an editable venv installed from a
different checkout imported the wrong package. The probe now documents the
explicit `PYTHONPATH=<checkout>/pdf-translate` form and records
`pdf_translate.__file__` and its version in `summary.json`.

**PARKED — Rodrigo ruled on 20 September 2026: hold Task 9 for now.**
Do not start it in a later session without a fresh ruling from him. Task 9
exports `MAPPING_FORMATS`, bumps all four version sources in lockstep, writes
`references/typography.md` and requires a bounded workflow run in **both**
Claude and Codex hosts. It was parked because that version bump can collide
with the local v61 metadata in the original checkout, and the plan forbids
reserving a version now. What would restore it: a decision on which version
this capability ships as, after the v61/B1 work in `C:/Dev/pdf-translate-skill`
is reconciled or landed. Until then `MAPPING_FORMATS` stays unexported, so no
installed runtime advertises `typography-1`. Nothing is published, no
capability is claimed and A01 stays open.
Eight genuine CJK slanted-role positive cells remain unmeasured; this candidate
has no remote CI run. Push, merge and release remain the operator's.

## Earlier — 20 September 2026, typography implementation active

Rodrigo approved the written plan and recommended native execution. Work is
active in the managed isolated checkout:
`C:/Users/rodri/.codex/worktrees/typography-preservation/pdf-translate-skill`
on `codex/typography-preservation`, starting at `48dffcf` (v58 runtime).
Read that checkout's plan and
`.superpowers/sdd/2026-09-20-typography-preservation/progress.md` before resuming.
This original checkout's earlier dirty v61/B1/audit work remains preserved.
Do not start a duplicate implementation here. No push/merge/PR changes are
part of the approval; independent final rendering verification remains required.

## Start here — 20 September 2026, typography implementation active

Rodrigo approved the typography design, nine-stage plan and native execution.
Continue all nine tasks without between-task approval questions. This managed
checkout is `codex/typography-preservation`, based on `48dffcf` (v58 runtime).
The original checkout's dirty v61/B1/audit work remains separate; do not import it.
Read `docs/plans/2026-09-20-typography-preservation.md`, its approved design and
`.superpowers/sdd/2026-09-20-typography-preservation/progress.md` before resuming.
Task 1 is committed as `1a730e2`; Task 2 as `3bc3156`; Task 3 as `76d3d72`.
Task 4 placement passed 23 focused tests, full discovery (556 OK, no skips),
both parity comparisons and an author visual pass. Task 5 final-PDF verification
passes 21 focused and 67 affected tests plus both parity comparisons. Continue
to Task 8: independent acceptance. Task 6 occurrence-aware QA/review passes
66 affected tests; Task 7 CLI/mapping focused27 pass and legacy pipeline228
passed in the combined run. Both parity comparisons match. Independent review
and complete acceptance remain pending.
The ledger records subsequent completion commits and commands; verify against Git.
Durable evidence: `docs/reviews/2026-09-20-typography-implementation.md`.

Fresh read-only GitHub recheck: main `a5629fb`; PR #12 OPEN `abc4767`, PR #13
OPEN `1d4f970`. No PR edits, push, merge, release, app messages or product-source
access are authorized. Independent final rendering/font/layout verification
remains required. No public typography capability is claimed yet.

Use the original repo venv with PYTHONPATH set to this checkout's `pdf-translate/`.
Baseline setup needed the original repo's ignored FL-150 NOTES fixture; restored
without runtime edits. Task 1 full suite: 503 OK, no skips. Both parity outputs
match the preserved clean baseline. New fonts/evidence stay inside this checkout.

## Earlier — 20 September 2026, typography plan awaits review

Rodrigo approved the written typography design. The implementation plan is now
saved at `docs/plans/2026-09-20-typography-preservation.md`; start with the short
`docs/plans/2026-09-20-typography-preservation-brief.md` for operator review.
The design documents mark his approval and link to the plan. Local commit
**`48dffcf`**, parent `ef52e5f`, contains exactly these four design/plan files.
No runtime, version or earlier dirty file was included in that commit.

**Next action: review the written plan and select an execution method.**
Recommended: native implementation in one isolated checkout, with an independent
real-run rendering/font/layout reviewer before completion. Alternative: a fresh
implementer/reviewer per task, sequentially. The writing-plans skill requires
plan review and method selection before implementation. No implementation has
started. Preserve this boundary when the operator next replies.

Nine stages cover source evidence, strict mapping, class/role fonts, fixed-line
placement, actual final-PDF verification, occurrence-aware QA/review, pipeline,
independent acceptance and installed Claude/Codex workflows. The approved same-
page-count/baseline requirements and first-scope refusals remain. The plan uses
clean v58 runtime ancestry via `ef52e5f`; its documentation commit `48dffcf` can
be applied to that isolated branch. Do not import the dirty local v61/B1 work.
A01 remains a separate public-readiness prerequisite; A03/A04/A05/A06/A14/E10
retain their ownership. B1 and A21 remain unstarted by this request.

Planning checks: 9 tasks, 14 Python blocks syntax-checked, 6 local document
links resolved, balanced fences and CRLF, no placeholder markers, clean
`git diff --check`. A source-only fixture generated one page with two `Pay NOW`
lines and four explicitly asserted Times/Helvetica font identities; no new
extraction/translation behavior was run. The fixture and before-images are in
ignored `runs/typography-plan-2026-09-20/`. All 45 snapshotted runtime/configuration
file hashes stayed unchanged. No full suite or host acceptance is newly claimed.

Git/gh recheck before planning: main `a5629fb`, PRs #12/#13 OPEN at `abc4767` /
`1d4f970`; branch `codex/b1-design-canvas`, now HEAD `48dffcf`. Local metadata
remains v61; committed runtime remains v58. No push, merge, PR edit, app-task
message or product-source access. The local commit has no attribution trailer.
Request/decision/handover updates remain uncommitted alongside preserved prior
work. Reverify actual state before execution.

## Earlier — 20 September 2026, written typography design awaits review

Rodrigo approved the recommended additive typography approach. The written
proposal is now saved in `docs/design/typography-preservation/DESIGN.md`; open
`docs/design/typography-preservation/README.md` for the short operator review.
Local commit **`ef52e5f`** contains exactly those two new design documents,
parent `1d4f970`. It does not include earlier dirty work or runtime changes.

The design proposes source class/style runs, exact occurrence associations,
a separate opt-in mapping format, class/role fonts, and shared QA/review/final
verification context. First scope is horizontal, single-baseline Latin,
Japanese and Simplified Chinese page text, one source size/color per segment.
Unsupported constructs refuse; they remain ineligible for adoption under the
unchanged product typography promise. Page count and source baseline stay fixed.
The schema, scope details and future acceptance checks remain proposals.

**Next action: operator review of the written design.** Do not start an
implementation plan or code before that ruling. The architectural brainstorming
skill requires written-design approval before planning; approval of the additive
approach permitted writing this document, not approving its unwritten details.
B1 remains separately deferred and A21 housekeeping was not started.

Document self-review, balanced fences, JSON-example parsing, local-link checks
and `git diff --check` passed. These are documentation checks; no typography
implementation, rendering acceptance or new full-suite result is claimed.
The request inbox and decision log reflect the new stage. Their updates and
this handover remain uncommitted with the earlier local work.

Fresh git/gh recheck: branch `codex/b1-design-canvas`, HEAD `ef52e5f`; remote main
`a5629fb`; PRs #12/#13 OPEN at `abc4767` / `1d4f970`, unchanged. Local working-tree
metadata remains v61; the design commit adds no version bump to the v58 runtime
in its ancestry. No push, merge, PR edit, product-source access or app-task
message. The design commit has no AI attribution. Preserve all prior dirty work.

## Earlier — 20 September 2026, typography API approach proposed

Rodrigo said “yes proceed” after the capability disposition. Typography API
design exploration is active; A21 housekeeping was not started. The recommended
approach is additive and opt-in: preserve source class/style runs, associate
authored target runs with exact source occurrences, select class/role fonts per
run, reuse placement where suitable, and expose the same information to QA and
review. Ambiguous/unsupported associations must be reported. Proposed acceptance
includes repeated labels with different styles, regular prefixes with emphasized
tails, reordered translations, family distinction and independent output checks.

Alternatives presented: replace the mapping format (breaking), or do extraction
and diagnostics alone (does not meet the adoption prerequisite). The approach
ruling is pending. No written final API design, implementation plan or code
change was made. The architectural brainstorming skill requires staged design
approval; do not interpret the preceding feature-scope approval as approval of
a not-yet-written design. Preserve the product's requirement and B1 deferral.

Read-only git/gh recheck: HEAD `1d4f970`, branch `codex/b1-design-canvas`, local
metadata v61; main `a5629fb`; PRs #12/#13 OPEN at `abc4767` / `1d4f970`.
Only the request inbox, decision and this handover changed in this turn. Prior
work remains intact. No commit, push, merge, PR edit, product-source access or
outbound message. Next stage after approach approval: a saved typography API
design for review, using this repo's docs/design convention.

## Earlier — 20 September 2026, typography adoption disposition returned

The app task sent Rodrigo's approved, bounded requirements/evidence request:
preserve source serif/sans class and meaningful within-line bold/italic for wider
library adoption. No reduced promise, renderer work, B1 plan/build or PR changes
were authorized. The response is saved in
`docs/reviews/2026-09-20-typography-capability.md`, with sanitized evidence in
`docs/reviews/data/2026-09-20-typography-capability.json` and an independently
authored extraction probe at `dev/probes/typography_capability_probe.py`.

**Disposition: blocked on a library capability gap.** At v54 app-reported pin
`9675c619`, main v56 `a5629fb` and open-PR v58 `1d4f970`, the same one-page fixture
produces four segment IDs / three unique cores, loses font class and source-span
records, flattens mixed emphasis and emits zero extraction warnings. The
`extract_segments` function AST is identical at all three commits. Existing
four-role/inline controls do not establish end-to-end style retention; mapping
and overrides do not select repeated occurrences by ID. This is an extraction
measurement, not a translation/visual-quality or app-corpus acceptance run.

The request inbox records the unprioritized typography prerequisite and the
library/app ownership split. No implementation was started, no future delivery
pin was assigned and no outbound message or extra data packet was requested.
The app still reports v54 adoption and five open compatibility failures; product
source and installation were not inspected. The typography requirement and B1
separate deferral remain intact.

Working tree remains local metadata v61 on `codex/b1-design-canvas`, committed
HEAD `1d4f970`; extraction/retypeset implementations are unchanged from HEAD.
Fresh GitHub checks: main `a5629fb`, PRs #12/#13 OPEN at `abc4767` / `1d4f970`,
no releases/tags. Prior local work was preserved. No commit, push, merge, release
or PR edit. A21 manifest validation remains the next small housekeeping
recommendation; it was not started by this request.

## Earlier — 20 September 2026, A15 README facts corrected

Rodrigo approved the next recommended small item. Both READMEs now document
full unittest discovery, 11 configured test-font files, presence-only checks,
requirements-based installation through the chosen interpreter, and checkout-only
contributor tests. Root navigation points to the canonical backlog and dated
audit instead of a supposed live HTML tracker. Stale runtime promises were
replaced with the identified 19 September v58 Windows/Python 3.14 measurement.

Evidence: `docs/reviews/2026-09-20-readme-facts.md`. Both README commands collect
**492 tests**, matching CI's test IDs, versus **230** selected before. This was
collection only, not a full-suite rerun. All **11 fonts** are present; dependency
constraints match package metadata and a no-network pip dry run succeeded.
The shipped README instruction change advances all four versions to **v61
locally**; its lockstep test passed. Python edits are version-only.

A15 remains partial for broader public-support wording. A04/A06's larger fixes
also remain open. Next smallest recommendation: A21's explicit validation of
both Claude manifests, then its separate type-check configuration slice. The
first small code fix remains A01's invalid-review refusal. None started here.

Fresh git/gh: branch `codex/b1-design-canvas`; committed HEAD `1d4f970` (v58);
remote main `a5629fb` (v56); PRs #12/#13 OPEN at `abc4767` / `1d4f970`.
Previous local changes were preserved. No commit, push, merge, release, PR edit,
product-source access or app-task message. B1 remains deferred.

## Earlier — 20 September 2026, A06 verification examples corrected

Rodrigo approved the recommended A06 documentation slice. Quickstart, hot-loop,
SKILL and Python examples now pass the mapping, segments, source vocabulary and
a target-script fill value. They verify the actual delivery PDF after field-font
embedding or packaging and distinguish its verdict from the intermediate file.
The shipped workflow correction advances the four version sources to **v60
locally**; only version metadata/expectation changed in Python, not PDF logic.

Evidence: `docs/reviews/2026-09-20-verification-examples.md` and its sanitized
JSON companion. Seven CLI examples plus two Python calls, extracted from the
updated docs, behaved correctly on three cases (**27 outcomes**): empty targets
exit 1 with `empty-targets`; complete non-form and fillable controls exit 0.
The fillable control passed the field round-trip; the v60 lockstep test passed.
The unchanged default rebuild still returned 0 for the empty target, so **A06
remains partial**. A04's process-validation work also remains open. No full
suite, non-Latin visual quality or model-driven host validation is claimed.

Next smallest recommendation: A15's small README facts. The first small code
follow-up remains A01's invalid-review refusal. Neither is started here.
Fresh git/gh: branch `codex/b1-design-canvas`, committed HEAD `1d4f970` (v58),
remote main `a5629fb` (v56), PRs #12/#13 open at `abc4767` / `1d4f970`.
Prior A04/B1/audit changes were preserved. No commit, push, merge, release, PR
edit, product-source access or app-task message. B1 remains deferred.

## Earlier — 20 September 2026, A04 concurrency documentation corrected

Rodrigo approved proceeding with the recommended small work. Completed the first
slice only: consumer guidance now distinguishes stdout/logging isolation from
PyMuPDF thread safety and prescribes separate processes, one job at a time per
worker, with private job/output/report paths. The skill reference and related
docstrings agree. The shipped instruction change advances all four version
sources to **v59 locally**; this is not a release or a PDF execution change.

**A04 remains partial.** Two-process validation and replacement of unsupported
thread-based PDF concurrency checks are still open; the current tests are
qualified as fixture observations, not backend safety proof. App worker
integration remains app-owned. Next smallest recommendation: A06's verification
examples. Do not start it merely because it is listed here.

Evidence and exact checks: `docs/reviews/2026-09-20-concurrency-guidance.md`.
Fresh git/gh check: HEAD `1d4f970` (committed v58), remote main `a5629fb` (v56),
PRs #12/#13 open at `abc4767` / `1d4f970`, unchanged. Working branch remains
`codex/b1-design-canvas`; existing dirty B1/audit work was preserved. No commit,
push, merge, release, PR edit, product-source access, or app-task message. B1
remains deferred. Reverify state before the next item.

## Earlier — 19 September 2026, audit findings added to backlog

Rodrigo asked to add/update backlog items from the audit and save a list of the
smallest/easiest work in `docs/`. Completed as documentation only:

- `dev/goals/PROGRAM.md` now opens with the current **A01–A26** audit follow-ups,
  mapped to existing E/C/P/32 work, priorities, estimated sizes, dependencies and
  observable closing checks. Existing history is retained; these are recorded
  candidates, not started implementation. P3's skill-length target is reopened.
- `docs/PUBLIC-READINESS-QUICK-WINS-2026-09-19.md` is the short dated view. Start
  with concurrency wording, mapping-aware verification examples and README
  facts. The highest-value small code follow-up is A01's invalid-review refusal.
  A docs slice does not close its larger behavior item.
- `docs/REQUESTS-from-product.md` links the qualifications to earlier C3/C4/C5
  assurances and existing packaging/dependency work. `docs/checklist.html` is
  explicitly historical and links to the current backlog, avoiding competing
  live status lists.

No fixes, implementation plan, PR edits or app-task messages were performed.
Library/skill work stays here; service integration stays app-owned. B1 remains
deferred. Fresh git/gh check: HEAD `1d4f970` (v58), remote main `a5629fb` (v56),
PRs #12/#13 open at `abc4767` / `1d4f970`. No commit/push/merge/release. Existing
dirty B1/audit work was preserved. Recheck before starting a follow-up.

## Earlier — 19 September 2026, dual-use public-readiness audit

Rodrigo explicitly requested a comprehensive audit of the whole codebase as
both the shared PDF engine and an installable Claude/Codex skill. That analysis
is complete in `docs/reviews/2026-09-19-public-readiness.md`, with sanitized
evidence in `docs/reviews/data/2026-09-19-public-readiness.json` and the synthetic
reproduction script `dev/probes/public_readiness_probe.py`.

The assessment is a capable supervised tool requiring release hardening before
an unrestricted public/production-readiness claim. This is a recommendation,
not an operator-approved implementation plan. Reproduced findings include invalid
review data permitting delivery, stale PDF/PASS artifacts after a failed rebuild,
and verification accepting both missing and added pages. The consumer guide's
thread-safety statement also conflicts with PyMuPDF's documented restriction.
Packaging, dependency bounds/licensing, public sanitation, skill onboarding,
documentation, API consistency, and maintainability are covered in the report.

Fresh local verification: **492 tests passed, zero skips, 202.730 seconds**;
**15 canary-scorer tests passed**. Wheel/sdist builds and clean-wheel installation
passed; Codex 0.147.0 discovered a staged local skill without a model turn; Claude
Code 2.1.270 validated both manifests separately. These checks do not constitute
a complete model-driven host evaluation or fresh Linux/macOS coverage. The audit
was recovered from saved files after the user reported a Codex crash.

Reviewed HEAD remains `1d4f970` (v58); remote `main` was freshly verified at
`a5629fb` (v56). PRs #12/#13 remain open at `abc4767` / `1d4f970`, untouched.
Hosted checks were not started because of GitHub billing/spending limits.
Re-verify git and gh before acting. Existing B1 work was preserved; no library
implementation, commit, push, merge, release, product-source access, or app-task
message resulted from this audit. B1 remains deferred under the earlier ruling.

Rodrigo also reported raw HTML fold tags in replies. Use plain Markdown with a
link to the longer saved report instead of `<details>` folds in chat. Preserve
the compact Status / Do / Recommend / Know / Ask reply format.

## Earlier — 19 September 2026, further B1 work deferred

Rodrigo approved the recommendation to defer further B1 work until a genuine
fit-refusal case is available. The canvas and its exact-page-count ruling remain
approved. The synthetic probe and single real-job capture are complete; the
capture was a known success and supplies no B1 recovery evidence.

There is no outstanding capture request or further B1 action pending now.
Resume evidence measurement with an unchanged failed mapping, source PDF,
fonts, version/options, and occurrence-level refusal evidence; testing wrapping
also requires an explicitly permitted fixed box. Replaying the known success
or constructing a failure does not meet that prerequisite. No implementation
plan, build, or background monitoring was started. Do not advance to another
work item without a new user instruction. The ruling is in `docs/DECISIONS.md`.

Work remains local and uncommitted. PRs #12/#13 were rechecked open at
`abc4767` and `1d4f970`, untouched. Re-verify git and gh before future work.

**Roadmap coordination:** Rodrigo asked who owns the product roadmap and how to
avoid collisions. He selected A, approving the split and sending it to the app
task. `docs/REQUESTS-from-product.md` records the approved split:
Rodrigo sets priorities; the app task coordinates one product roadmap and owns
app/integration work; this repo owns shared engine delivery. The coordination
message was sent to **Boot Spire Tech web app**, which confirmed the alignment
is recorded in its canonical roadmap:
`C:/Dev/pdf-translator/.spire/clusters/tech/context/ROADMAP.md`.
The app's final coordination update reports N1's seven approved screenshot
reference updates complete with fresh independent **331/331, zero skips**.
Known frontend baseline and historical process records remain separate N1
closure obligations. Its next available product action is app-owned preparation
of a reviewable CI authentication arrangement for the private library dependency;
credentials and push/merge/deploy remain operator-controlled. This assigns no
new library work. No unresolved duplicate assignment was found in the bounded
alignment. Old N2 save/subset and N6/E5 product-rendering assignments
are superseded by library ownership of reusable behavior; app ownership is
integration, product policy and evidence. Adoption reportedly remains v54 at
`9675c6196c14eb2a2d37d34e371391eb1955a386`. These are the owning task's status
reports; product files were not opened here. Full confirmation is recorded in
`docs/REQUESTS-from-product.md`. Coordination is complete. No new implementation
was commissioned here; N1 is not a library assignment. Stale B1 entries were
corrected to match the approved design and deferral.

## Earlier — 19 September 2026, B1 original-input search and capture

Following the operator's “okay proceed with the recommended,” the local
archive search found 12 saved mapping paths: three school-permission finals
(including one duplicate), one reviewed FL-150 final, and eight one-core
regression fixtures. No complete representative original failed-job bundle was
found. Details and hashes: `docs/reviews/2026-09-19-b1-local-inputs.md` and its
linked JSON. This establishes local availability only, not that failures never
occurred. No customer recovery rate can yet be measured.

A concrete data-only request for the web-app task **Boot Spire Tech web app**
is saved at `docs/design/B1-line-wrapping/FAILED-JOB-REQUEST.md`. It asks for
source PDFs, unchanged failed mappings, shareable fonts, refusal evidence,
versions, and explicitly permitted boxes; no product code. Rodrigo subsequently
said **“yes send it”**; the request was sent to task
`01a0bc1c-cdb2-7b93-8860-0154a450beb4`. Its data-only reply reports no eligible
replayable real failed-job bundle and no exported cases. Older-path form records
report source-retaining no-room blocks, but lack the exact failed mapping and
occurrence evidence; permitted boxes are unknown. These are reported claims,
not reproduced failures or a recovery denominator. The reply and provenance
are saved in `docs/reviews/2026-09-19-b1-product-inputs.md`. Product files remain
unread. The archive request is answered; no batch was returned.

**Authorized follow-up:** Rodrigo approved option A to ask the web-app task to
capture one genuine form/invoice translation attempt, preserving exact inputs
and results before retries or wording fixes. That request was sent and accepted;
the capture is now complete. The bundle in
`runs/b1-real-jobs/20260919-webapp-fl150-page1-opus-01/` replays a known successful
one-page FL-150 mapping on recorded library v54, not this checkout's v58.
Independent read-only checks passed all 27 file hashes, the font-path-only mapping
change, one-page parity, and all 61 widget names/types/rectangles. Both pages
were rendered and inspected. The logs record 8 shrinks (minimum reported 0.844),
13 PASS / 3 REVIEW, and regular-face role fallbacks. All wrapping permissions
remain unknown; no B1 wrapping was attempted. This is distinct from the earlier
two-page school-permission fixtures, but still a known success, not a new failure
or recovery sample. See `docs/reviews/2026-09-19-b1-captured-case.md` and its raw
audit. The capture request is fulfilled; recovery evidence remains unavailable.
No plan or library implementation has started. Work remains local and
uncommitted; PR #12/#13 heads were rechecked unchanged.

## Earlier — 19 September 2026, B1 probe complete; no plan or build

**Approved:** exact source page count, same-page placement, explicit permission
per occurrence, fixed caller-authored box, downward flow from the original
first baseline; source-size wrapping before shrink within existing limits,
then refusal if impossible. See `docs/design/B1-line-wrapping/README.md`.

**Measured:** `dev/probes/b1_recovery_probe.py` with `b1_cases.json`, repo venv
PyMuPDF/MuPDF 1.28.2. All 8 synthetic stress cases refused on the ordinary-line
path; 6 placed their full targets inside the explicit boxes via existing
one-member merges, keeping page counts, page sizes and widget rectangles.
The tight cell and last-page footer still refused. **All six moved the first
baseline** (−2.481 to +0.502 pt). Five shrank about 2% without a scale-report
entry. A repeated-label control removed the first occurrence while drawing
into the second one's box, leaving the second original placement overlapping.

This is **not a customer recovery rate**. The 16-file seed corpus has source
PDFs and extraction verdicts, not translations. The two saved final translation
jobs rebuilt without refusal, so they supply no failed-job denominator.
Representative refused inputs with permissible boxes are still needed before
sizing customer coverage. Evidence and reproducible command:
`docs/reviews/2026-09-19-b1-recovery-probe.md`; durable raw data beside it in
`data/2026-09-19-b1-recovery.json`. An independent agent reran the probe and
audited raw PDF fonts, positions, widgets, and unclipped target ink at 432 dpi;
both commands exited 0 with the same counts. The reusable independent audit
is `dev/probes/b1_recovery_audit.py`; raw results are in
`docs/reviews/data/2026-09-19-b1-independent-audit.json`.
Scratch PDFs/renders remain under
`runs/b1-recovery-probe-2026-09-19/`. The short web-app note is updated.

Work remains local and uncommitted on `codex/b1-design-canvas` at `1d4f970`.
PR heads #12 `abc4767` and #13 `1d4f970` were rechecked and untouched.
No pipeline/library code, corpus fixtures, versions, or implementation plan
changed. No push/merge. Product repo never opened. Re-verify state next session.

## Earlier — 19 September 2026, B1 direction approved

**Rodrigo approved the recommended B1 direction, including exact source page
count. Design only: no corpus recovery probe, plan, or build has run.**
Open `docs/design/B1-line-wrapping/canvas.png` and its `README.md`. Approved:
explicit permission per occurrence, a caller-authored fixed box, and downward
flow from the original first baseline, preserving exact page count and keeping
text on its source page. An impossible fit refuses; it never adds a continuation
page. The user requested the artifact be saved in docs; the PNG and notes are
there; the PNG preserves the pre-ruling sketch, so its pending labels are
historical. The ruling is appended to `docs/DECISIONS.md`. The requested short
note for the web-app session is `docs/design/B1-line-wrapping/WEB-APP-NOTE.md`;
it was saved for Rodrigo to relay, not sent to another session.
**Next prerequisite:** corpus recovery measurement, before a plan or build.
No later stage was performed in this canvas-and-ruling delivery. Evidence:
`docs/reviews/2026-09-19-b1-design-canvas.md`.

Re-verified with git and gh: checkout began clean on `feat/consumer-surface`
at `1d4f970`. Work is local and uncommitted on `codex/b1-design-canvas` from
that commit. #12 (`abc4767` → `main`) and #13 (`1d4f970` →
`feat/terminology-loop`) remain open, MERGEABLE, with failing checks; neither
was modified. **Correction to the previous handover:** remote `main` is
`a5629fb`, CI concurrency only (#14); local `main` remains `bacc436`.
No commit, push or merge was made. Re-verify these facts on the next session.

The source also corrects two shorthand claims: ordinary lines may shrink to
0.7× (with explicit exceptions), and a library build refusal does not itself
restore source-language text. Explicit merges already reflow. The canvas is
schematic and asserts no measured recovery benefit. The product repo was not
opened.

## Previous start here — 19 September 2026 (superseded by the canvas entry)

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
