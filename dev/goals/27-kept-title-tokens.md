# Objective: a quoted title is kept however the scan tokenizes it

> Hand this to a `/goal` session. Self-contained. Read `scripts/verify.py`
> (`_run_key`, `_kept`, `scan_leaks` and `_scan_leaks_script`,
> `MIN_WORD_LETTERS`), `dev/goals/20-notice-title-leak.md` §7, and
> `dev/canary/runs/2026-09-03-fable-5.1-fl100.md`. Not FL-150.

## 1. Compass (not done)

Row 20 keeps a run whose letters equal the original `/Title`'s. On FL-100
the title is `FL-100 Petition—Marriage/Domestic Partnership`, the notice
quotes it verbatim, and the scan's run is `Petition Marriage Domestic
Partnership`: `FL` is under the four-letter Latin floor and `100` is not
a word, so the run's key never equals the title's and the keep never
fires. The author allowlisted two spellings by guesswork.

## 2. Done when — closed bar

1. The title's key is built with the same filter the branch applies to
   runs — drop tokens shorter than the branch's minimum, drop non-letter
   tokens — so a verbatim quote of the title is kept in every branch.
2. A run that is a proper *part* of the title is still not kept, and a
   run that contains the title is still a leak: the row-20 tests stand.
3. Tests: a `/Title` with a short token and a form number (`FL-100
   Petition…`), quoted verbatim in a notice → kept; the same title with
   one word missing → running text; the CJK branch unchanged.
4. Full unittest + corpus green; `metadata.version` bumped.

## 3. Not done when

- Prefix or substring matching of the title
- Raising or lowering the word floor
- Reading titles from anywhere but the original's `/Title`

## 4. Proof

The FL-100 title kept under a neutral `verify`; the row-20 fixtures
unchanged; full unittest + corpus.
