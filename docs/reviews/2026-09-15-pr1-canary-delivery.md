# Review — PR #1 `codex/explicit-canary-delivery` → `main`

**Reviewed:** 2026-09-15 · **Head:** `26e1f25` · **Base:** `main` @ `b157172`
**Size:** 3 commits, 11 files, +517 / −68 · **CI:** 5/5 green (run 33956447838)
**Verdict:** mergeable. No blocking findings. Two nits and one untested
branch, none of which change the recommendation.

This PR is the foundation of PR #2; it had sat ten days unreviewed.
Merging #2 alone does not reach `main` — #1 must land first.

## What it changes

| Area | Change |
|---|---|
| `dev/canary/score.py` | Output selection is declared (`delivery.json` or `--output`) instead of "newest PDF anywhere in the tree". Ambiguous root-level candidates are an error, not a guess. Original excluded by SHA-256, not by byte size. `--allow`, `--fill-text`, `--report` flags; the report must sit outside every run directory and can never overwrite the original. Report carries the verification settings and the full verify log. Exit codes: 0 pass, 1 failed gates / lost identifier / QA error / no output, 2 invalid config or ambiguous selection. |
| `dev/canary/test_score.py` | New, 11 tests: nested diagnostics ignored, ambiguity, same-size PDFs, manifest replay of the allowlist, invalid manifests do not fall back, report placement guards, CLI exit codes. |
| `pipeline.py rebuild` | No longer `chdir`s into the work directory, so caller-relative `--translations` / `--segments` / `--source-words-from` paths keep meaning. |
| `retypeset.py` | Font paths in `translations.json` resolve beside the mapping, with a visible `NOTE` fallback to the old caller-relative behaviour. CSS `url()` for `@font-face` is now quoted and escaped, so a job path with spaces no longer silently substitutes a font. |
| Tests | 3 new `HotLoopTests`: rebuild with caller-relative verification paths (cross-drive on Windows CI), direct retypeset with a mapping-relative font, Story engine keeps the configured face in a directory named `job with spaces (ñ)'s`. |
| Docs / version | canary README (manifest schema, exit codes), `translations-format.md`, skill README; plugin `47.0.0` → `48.0.0`, `metadata.version` `47` → `48`; CI gains the canary test step. |

## What I ran (not what I read)

| Check | Command / evidence | Result |
|---|---|---|
| Suite at head | worktree `C:\Dev\pdf-translate-skill.wt\pr1`, fonts copied in, `python -m unittest tests.test_pipeline tests.test_corpus_verdicts -v` | `Ran 228 tests in 49.972s — OK`, 0 skipped |
| Canary tests | `python -m unittest discover -s ../dev/canary -p test_score.py -v` | `Ran 11 tests — OK` |
| Whitespace | `git diff --check main...codex/explicit-canary-delivery` | clean |
| Real scorer run | `score.py runs/fresh-canary-2026-09-05/fixtures/permission_form.pdf runs/fresh-canary-2026-09-05/job --report <outside>` (the frozen 45-file Spanish delivery with its `delivery.json`) | exit 0; `verify: exit 0, 0 gate(s) failing`; identifiers 4/4 kept; `qa_check: 0 error(s), 1 warning(s)` (the documented unchanged school name); run directory untouched |
| Version lockstep | `plugin.json` 48.0.0 vs `SKILL.md` metadata.version 48 | consistent (CI asserts this) |

Interpreter: the repo venv, Python 3.14.0, PyMuPDF 1.28.2, pikepdf 10.13.

## Findings

**F1 — behaviour change in scoring, correct but worth knowing.**
`score_run` now passes `source_words_from=segments.json` to `verify`
(it did not before), so the leak scan uses the document's own source
words rather than the harvested-from-original fallback. That is the
preferred mode per `SKILL.md`. Scores of old runs may shift slightly.
No action; noting it so nobody attributes the shift to the PDF.

**F2 — untested branch: CSS escape path.** `css_url()` in
`retypeset.py` escapes `"`, `\` and control characters as CSS hex escapes.
The new test exercises spaces, parentheses, `ñ` and `'`, none of which hit
the escape branch; nothing does. On Windows the branch cannot fire (`"` is
not a legal filename character and backslashes are POSIX-ified first); on
Linux a filename containing `"` or `\` would. Low risk. A Linux-only test
or a one-line comment saying the branch is unexercised would close it.

**F3 — nit: silent resolution when neither font path exists.**
`retypeset` tries mapping-relative, then caller-relative with a `NOTE`.
If neither exists the mapping-relative path wins silently and the failure
surfaces later as a font-load error naming only that path. A `NOTE` naming
both attempted paths would save a minute of confusion. Not blocking.

**F4 — nit: commit subjects lack the conventional-commit scope**
(`Score declared PDF deliveries…`, `Keep relative-path regression…`,
`Canonicalize canary roots…`). The repo convention is `feat(scope):`. A
squash-merge title can fix it; otherwise ignore.

**F5 — subtle but fine.** `candidate_output` hands `run_file()` an
absolute path where the function's contract is "a path inside the run";
it works because `root / absolute` yields the absolute path. A comment
would help the next reader.

## Claims in the PR body, checked

- "239 local tests passed (228 + 11)" — reproduced: 228 + 11.
- "Hash checks confirmed the delivery was unchanged by scoring" — reproduced
  on the frozen job: `git status` of the ignored run tree unchanged, report
  written outside it.
- "Windows coverage includes separate checkout/TEMP drives and 8.3 aliases"
  — the test comments and `Path.resolve()` canonicalisation match; CI ran on
  `windows-latest`. Not re-measured here.
- "Human Spanish revision and interactive viewer testing are recorded as
  outstanding" — honest; the delivery's `DELIVERY.md` says the same.

## Recommendation

Merge #1 into `main` (operator's action). Nothing here needs a change
first. F2 and F3 are follow-ups, not conditions.
