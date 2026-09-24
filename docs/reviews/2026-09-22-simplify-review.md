# Review of Claude's simplify commit

Reviewed commit `d2b33957d687fd79f6713b31e035fa1fe965d563` against its
parent `6236be6` on `codex/b1-design-canvas`.

Verdict: no actionable correctness findings in this change. It reads only
the first 8,000 bytes for binary detection, obtains the repository root from
the test module's location, and uses `as_posix()` for Git attribute paths.
The decision note preserves previously cited probe evidence instead of
refactoring independent verification to use the implementation's helper.

## Scope discrepancy

This was a cleanup of `dev/repo/test_binary_integrity.py`, not the suggested
A01/A03 candidate review. Both candidate worktrees remain clean and unchanged:
A01 `41bdf9911c81116ab282aa6e39ce3bee0ca82b04`, A03
`30c4805a3027fe3f2492edd4d2745c467646d68a`.

No library runtime, public API, renderer, dependency declaration, or consumer
pin is changed by this commit. GitHub main remains `b20fadda` at review time.
The older branch is three commits unique and 36 behind main; existing dirty
changes are separate and were not reviewed as part of this cleanup. Do not
treat this review as approval to merge the older branch wholesale.

## Fresh verification

Using `C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`:

- `python -m unittest dev.repo.test_binary_integrity -v`: three tests pass,
  0.120s, no skips.
- Compared original full-read sniff and new bounded-read sniff over all 253
  tracked files: identical set of 11 binaries; all relative path strings match.
- Checked empty files, NUL at byte 7,999, NUL at byte 8,000, and a 100,000-byte
  non-NUL file: all four match the intended first-8,000-byte behavior.
- Executed old/new test classes against this checkout: identical three passes.
- Executed old/new classes against the main-based A03 linked worktree:
  identical three failures, expected because that worktree predates the
  separate `.gitattributes`/binary-integrity commits. The `.git` file is
  recognized. An initial synthetic check used a nonexistent `dev/repo` parent,
  causing the old Git subprocess to skip; corrected to the existing
  `dev/probes` directory at the same depth before drawing this conclusion.

No full runtime suite was repeated for this test-helper-only diff. Claude's
commit message reports 492 tests; that is not a fresh result established by
this review and does not establish A01/A03 simplification coverage.

The work is reasonable to retain as a separate repository-test cleanup.
To evaluate the originally proposed cleanup, run Claude against the exact
A01 and A03 worktrees and preserve each candidate's behavior and regression
assertions. Any downstream adoption remains separate.
