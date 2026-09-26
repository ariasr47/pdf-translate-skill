# Docs batch: capture, the `document` block, R-42's wording — 26 September 2026

**Assignment.** This is the product's second item, advised on 26 September
and approved by Rodrigo. It ships as v84, stacked on #56 (v83). Docs,
comments and tests only; no code path, output or console line changes.

## 1. Capture (#19's request)

`references/consumer-guide.md` states three facts:
- **`capture_dir=""` is off**, even with `PDF_TRANSLATE_CAPTURE_DIR` or
  `PDF_TRANSLATE_CAPTURE_BELOW` set.
- **A bundle holds the document's text even without `original=`.** It
  always has `segments.json` and the stripped PDF with the form's fields,
  beside the mapping; `original=` adds only the untouched source.
- **A successful build can write a bundle too.** With `capture_below` set
  and capture on, a legacy build near the floor writes a `near-floor`
  bundle, one per job. This needs a capture directory: `retypeset.py` calls
  `capture_near_floor` only when both are resolved.

**The lock.** `tests/test_retypeset_capture.py`'s `EmptyCaptureDirTests`
sets both environment variables and runs two builds with `capture_dir=""`:
a refused one and a successful near-floor one. Neither writes anything. A
control without the argument does capture, so the environment is live.

The behaviour already held, so the test passes on v83. It is proved to
guard the behaviour by mutation: with `resolve_capture_dir` patched to
treat `""` like `None`, both off-switch tests fail and the control passes.

## 2. The `document` block

`review_prompt_md` reads five keys from it: `class`, `issuer`,
`parallel_text`, `pair` and `register`. `run_review` takes the block from
`review.json` after an ingest, and otherwise from a legacy
`translations.json`.

**Checked:** a typography-1 mapping with a `document` key is refused
(`invalid-style-reference`, "invalid fields in typography mapping").

**Documented:**
- `references/translations-format.md` has a section with the five keys,
  what each fills and how a missing one reads. It notes that `review.json`
  wins and that typography-1 refuses the key.
- SKILL.md's identity step said the record goes in notes, "not
  `translations.json` (the scripts do not read it)". That was wrong for
  review. It now says to copy the record into the `document` block.

**The guard.** `tests/test_shipped_docs.py`'s `DocumentBlockTests` checks
two things:
- the documented keys are exactly those `review_prompt_md` reads, taken
  from its AST;
- SKILL.md points to the block.

Both fail on the v83 docs.

## 3. R-42's wording

The product's review of #42 found a gap. `ContentIssue.at` records where
the **text line** holding the offending text starts, not where the text
itself starts. So on a line with several occurrences, the refusal names
the line's first.

On its advice the wording changes now, and the fix waits until
typography-1 is next worked on. The wording now says so in:
- the `ContentIssue.at` comment;
- `_content_segment`'s docstring;
- a comment in `typography_content.py`;
- `references/typography.md`;
- the upgrade note's v72 row.

The R-42 evidence file gains a dated correction, and a DECISIONS row
corrects the R-42 row. Neither older record is rewritten.

## Suite

CI's commands on macOS, on this change:
- **Suite:** 798 tests (793 on v83, plus these 5), with 0 ResourceWarnings.
  The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is item 3's expected failure.
- **Canary, repository tests and eval fixtures:** all exit 0.

Rule 1 does not apply: nothing here renders, shapes, lays out or touches a
font.
