# Reconciling the old `codex/b1-design-canvas` checkout

23 September 2026. Library repo only; no product source was opened.

## Outcome

**The checkout is reconciled, not merged. B1 line wrapping is not
implemented, and B1 stays deferred.** Everything useful in the old checkout now
sits on the local branch `chore/reconcile-b1-checkout`, based on main
`178a06f`. Every item is accounted for below: carried, adapted, routed to
another change, dropped, or left in place. The original checkout was not
reset, cleaned, stashed, switched or merged. Nothing was pushed.

| Branch commit | Content |
|---|---|
| `f7326cf` | `.gitattributes`, `dev/repo/test_binary_integrity.py` and its CI step |
| `3860c66` | the B1 baseline-anchor probe, cherry-picked (`-x`) from local `12c730c` |
| `d99320b` | 38 evidence files that were untracked in the old checkout |
| `509c39e` | A04 concurrency guidance (docs and docstrings) |
| `0cd8bc2` | A15 README facts plus the README half of `d9014ec` |
| `498dec4` | PROGRAM backlog, DECISIONS rows, product inbox, brief, checklist |
| this commit | this report and the handover |

## Verified starting state

Checked with commands on this date, not taken from the handover:

| Claim | How checked | Result |
|---|---|---|
| PR #22 merged | `gh pr view 22 --json state,mergedAt,mergeCommit,headRefOid` | MERGED 2026-09-23T17:15:44Z, head `7eeccf2`, merge `178a06f` |
| Remote main | `git fetch --prune`; `git ls-remote origin refs/heads/main` | `178a06ffd4e45af30c0366c5f0fb995f8495cb5f` |
| Post-merge CI | `gh run view 35894389833 --log` | success: Linux 670 OK (762.938 s), Windows 670 OK skipped=1 (899.030 s), canary 15 OK on both, plugin manifest job green |
| Open PRs | `gh pr list --state open` | none |
| Old checkout | `git rev-parse HEAD`; `git log origin/main..HEAD` | `d2b3395` on `codex/b1-design-canvas`, 3 commits unique, 54 behind, merge-base `48dffcf` |
| Old checkout's remote branch | `git rev-parse origin/codex/b1-design-canvas`; `gh pr list --state all --head codex/b1-design-canvas` | `6236be6` (so `d2b3395` is local only); no PR ever opened |
| Dirty state | `git diff --stat HEAD`; `git ls-files --others --exclude-standard` | 17 modified tracked files (+1,123/−61); 39 untracked files |
| Unmerged local branches | `git branch --no-merged origin/main` | only `codex/b1-design-canvas` and `probe/b1-baseline-anchor` (`12c730c`, never pushed) |

The byte-level snapshot is in the old checkout's ignored
`runs/b1-checkout-reconciliation-2026-09-23/`: `head.txt`,
`status-porcelain-v2.txt`, `tracked-dirty.patch` (sha256 `004f905b…a5cb9d`),
`tracked-dirty.stat` and `untracked-sha256.txt`.

## The three unique commits, reviewed together

| Commit | Content | Disposition |
|---|---|---|
| `d9014ec` | `.gitattributes`; root README edits | `.gitattributes` carried byte for byte in `f7326cf`. The README was merged by hand in `0cd8bc2`: main had changed the same paragraphs (Python 3.14, dependency preflight), and the branch text still said Python 3.10/3.13 and 11 fonts. Its own two install lines also contradicted each other (unbounded `pip install` vs "use the requirements file"). |
| `6236be6` | binary-integrity test, CI step | test carried as `d2b3395`'s final form; CI hunk applied unchanged to main's workflow (`f7326cf`) |
| `d2b3395` | test refactor; frozen-probe DECISIONS row | test in `f7326cf`; row carried in `498dec4` |

Main's 274 blobs were read raw (`git cat-file --batch`): every text blob was
already LF. The only CR bytes are in four PDFs covered by `*.pdf binary`
(`ar_source`, `ja_source`, `image_only`, `ocr_layer`). Adding the file
therefore re-normalises nothing. On this tree, `python -m unittest discover
-s ../dev/repo -p test_binary_integrity.py` from `pdf-translate/` gave:

| Run | Result |
|---|---|
| clean tree | 3 tests OK |
| `corpus/pale_blank.pdf` re-smudged to 693 bytes | FAIL naming `pdf-translate/corpus/pale_blank.pdf` |
| `*.pdf binary` rule commented out | FAIL listing all 11 NUL-carrying corpus PDFs |
| restored | 3 tests OK |

**Trap found while doing this.** In a working tree checked out before
`.gitattributes` existed, `pale_blank.pdf` is already smudged (693 bytes). Two
things go wrong from there. `git checkout-index -f -a` does not rewrite files
whose stat data matches the index. And `git add --renormalize .` staged the
smudged bytes as they were, which is the exact corruption this commit guards
against. It was caught before any commit, unstaged, and the index was verified
against HEAD (blob `33816f5`). The fix: remove the tracked files, check them out
again, then `git add -u` to refresh stat data. Every blob was then confirmed
identical to HEAD. Any Windows clone with `core.autocrlf=true` that pulls this
commit needs the same refresh before touching the index.

## The 17 modified tracked files

| File(s) | Hunks | Disposition |
|---|---|---|
| `.claude-plugin/plugin.json`, `pyproject.toml`, `pdf_translate/__init__.py`, `SKILL.md` version line, `tests/test_verify_report.py` | v58 → **v61** | **Dropped.** Main assigned v59 (typography) and v60 (refusal capture); the local labels named other releases. Candidates keep v60 until integration (DECISIONS, 23 September). |
| `references/consumer-guide.md` (Threads section, contents line), `pdf_translate/_console.py`, `pdf_translate/verify.py` (`run_verify` docstring), `tests/test_consumer_contract.py` (class docstring), `SKILL.md` reference line | A04 concurrency | **Carried** (`509c39e`). Main still said the `run_*` twins are "the thread-safe surface". PyMuPDF's multiprocessing recipe was rechecked today and still says it "does not support running on multiple threads". Only docstrings changed: with docstrings stripped, the ASTs match `178a06f`. The guide section is byte-identical to the old text. |
| `SKILL.md` (rebuild/verify/final-verify examples), `references/gates.md`, `references/consumer-guide.md` (six-calls example), `pdf-translate/README.md` (quickstart, hot loop) | A06 verification examples | **Routed to the A06 change.** It is true on main today, but the A06 fix changes the default rebuild these sentences describe ("rebuild does not add the verifier's mapping argument automatically"). Landing it here and rewriting it there would make two branches edit the same lines. Evidence: `docs/reviews/2026-09-20-verification-examples.md`; harness in the old checkout's `runs/a06-verification-examples-2026-09-20/`. |
| `pdf-translate/README.md` (install, test commands, requirements line) | A15 README facts | **Carried, re-measured** (`0cd8bc2`). The fetcher now configures 20 fonts (the slice said 11). `discover -s tests -t .` collects 670 tests. `--check` exits 0. |
| `docs/checklist.html` | historical banner | **Carried** (`498dec4`); its links now resolve |
| `dev/goals/PROGRAM.md` | A01–A26 backlog; P3 → A17 | **Carried with statuses refreshed** (`498dec4`): A01/A03 done in PR #22; A04/A15 slices carried; A06 slice routed; A17 now 629 lines |
| `docs/DECISIONS.md` | 17 uncommitted rows | **Carried verbatim** with `d2b3395`'s committed row, appended after main's 38 rows in their original order, plus 2 new rows. A script asserted the result is main's rows unchanged, then the 18 carried, then the 2 new: 58 rows, nothing removed. |
| `docs/REQUESTS-from-product.md` | coordination status, ownership split, B1–B5 status, typography request | **Three-way merged** with main's C8 change (no conflict). The 20 September status is kept as a labelled snapshot under a new, dated 23 September status. The typography row is marked done in v59, with adoption left app-owned. |
| `docs/BRIEF-product-bubble-2026-09-18.md` | B1 status banner | **Carried**, dated 23 September, naming the anchor probe |
| `dev/goals/HANDOVER.md` | 22 sections from 19–23 September | **Carried verbatim** (this commit). Main's three unique sections sit beside the account of the same event; main's "Earlier — 19 September" body was identical to the old checkout's relabelled copy, so it appears once. A script asserted every section of both files survives. |

## The 39 untracked files

| Files | Disposition |
|---|---|
| `docs/design/B1-line-wrapping/` (README, `canvas.png` 1,529,980 bytes, `WEB-APP-NOTE.md`, `REAL-JOB-CAPTURE.md`, `FAILED-JOB-REQUEST.md`) | carried (`d99320b`): the approved design reference; mockups belong in `docs/` |
| 15 reviews under `docs/reviews/` (19 September B1 canvas/inputs/recovery/capture, public readiness; 20 September A04/A06/A15/typography capability; 22–23 September review, simplify and integration reviews) | carried verbatim (`d99320b`); dated records, not current state |
| `docs/reviews/assets/` (2 PNG), `docs/reviews/data/` (9 JSON) | carried (`d99320b`) |
| `dev/probes/b1_recovery_probe.py`, `b1_recovery_audit.py`, `public_readiness_probe.py`, `typography_capability_probe.py` | carried unedited (`d99320b`); frozen under the 22 September DECISIONS row |
| `dev/probes/b1_cases.json` | carried through the anchor cherry-pick (`3860c66`): same blob `2497abb` |
| `docs/PUBLIC-READINESS-QUICK-WINS-2026-09-19.md` | carried (`d99320b`) |
| `docs/explainers/` (2 HTML, 21 September decisions: capture hook, typography task 9) | carried (`d99320b`); self-contained, no local paths |

Each of the 38 staged blobs matched `git hash-object --path` of its original.
27 originals had CRLF working copies; the index holds them as LF. No product
source is among them: four files name `C:\Dev\pdf-translator` only as
provenance paths or to state it was not opened. The carry also repairs main's
one broken relative link (`docs/design/typography-preservation/DESIGN.md` →
`reviews/2026-09-20-typography-capability.md`).

## Left in place, deliberately

| Item | Where it stays | Why |
|---|---|---|
| The old checkout, `codex/b1-design-canvas` (`d2b3395`) | `C:\Dev\pdf-translate-skill` | the instruction was to preserve it; deleting it is Rodrigo's call |
| `origin/codex/b1-design-canvas` (`6236be6`) | GitHub | remote deletion is outward-facing; no PR ever existed |
| `probe/b1-baseline-anchor` (`12c730c`) and its worktree | `C:/Dev/worktrees/pdf-translate-b1anchor` | carried by cherry-pick; the branch can go once this lands |
| 25 ignored evidence directories under the old checkout's `runs/`; 16 are cited by the carried reviews | local only | raw logs, PDFs and harnesses, some from real jobs (`runs/b1-real-jobs`); never committed, and whether to keep them is Rodrigo's decision |

## Validation

| Check | Result |
|---|---|
| Full suite on clean `178a06f` (baseline, from `pdf-translate/`: `python -m unittest discover -s tests -t .`) | 670 tests OK, 578.251 s |
| Full suite on this branch at `498dec4` (same command) | 670 tests OK, 484.230 s; exit 0 |
| Binary integrity: green, two reds, green | as above |
| A04 affected modules (`test_consumer_contract`, `test_import_surface`, `test_verify_report`) | 88 tests OK, 14.106 s |
| Relative links and heading anchors, whole tree | all resolve except main's 16 pre-existing references to its design canvases' uncommitted `support.js` |
| `git diff --check` per commit | clean |

Runtime: `C:/Dev/pdf-translate-skill/pdf-translate.venv` (Python 3.14.0, PyMuPDF
1.28.2, pikepdf 10.13.0.post1, fontTools 4.64.0) with `PYTHONPATH` set to this
worktree's `pdf-translate/`. That venv holds an **editable install of the old
checkout** (it reports version 61), so an unset `PYTHONPATH` tests the wrong
tree. Every run here printed or asserted the worktree path. The fresh worktree
got the 26 font files (20 fetched, 6 instanced) from the integration worktree.

**AGENTS.md Rule 1.** Nothing here changes rendering, shaping, fonts or layout.
`.gitattributes` affects how Git checks files out, not what the library
draws, and the rest is documentation, docstrings, evidence and a test that
only reads files. Rule 1's independent rendering run therefore does not apply.
A separate review pass over this reconciliation is recorded in the handover
once it has run.

## What remains, and where it belongs

| Item | Home |
|---|---|
| A02 legacy page-count verification | separate change from `178a06f` (next) |
| A06 default-rebuild mapping checks, plus the routed examples slice | separate change from `178a06f` (after A02) |
| A04 process-isolated validation | backlog A04, open |
| A15 broader public-support wording | backlog A15, open |
| Next version number | chosen once at integration (DECISIONS, 23 September) |
| B1 wrapping | deferred until a genuine fit-refusal case or an explicit change of scope |
| Old checkout, remote branch, anchor branch, local `runs/` | Rodrigo decides when to delete; nothing depends on them after integration |
