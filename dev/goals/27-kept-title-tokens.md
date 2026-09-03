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

## 5. Closing note — 3 September 2026, closed

**Reproduced first, at the unit the row is about.** With the real title,
`verify._run_key('FL-100 Petition—Marriage/Domestic Partnership')` is
`fl petition marriage domestic partnership` while the run the scan builds
keys as `petition marriage domestic partnership`, so `_kept` returned
`False` and row 20's keep never fired. That is the whole defect: the scan
cannot see `FL` (two letters, under the Latin floor) or `100` (not a
word), but the title's key still carried them.

**Done bar, item by item.**

1. `_run_key` now drops tokens below the branch's own word floor —
   `MIN_WORD_LETTERS.get(script, 2)`, the same number
   `source_words_from_text` uses to decide what a word is. Both sides go
   through it, so the filter is symmetric and the keep fires in every
   branch. Non-letter tokens were already dropped.
2. The row-20 tests stand untouched. A proper part of the title is not
   kept (`Petition Marriage Domestic`, `Marriage Domestic Partnership`),
   and a run that contains the title is still a leak — asserted at unit
   level and end to end, where one extra source word beside the quote
   brings the FAIL back.
3. **Tests** (`KeptTitleTokenTests`, 6): the key equality and the keep,
   with the issuer's em dash and with a hyphen; two proper parts; the
   containing run; the spaceless branch unchanged (nothing dropped, still
   whitespace-removed); and the end-to-end notice on a `/Title` of
   `FL-100 Petition-Marriage/Domestic Partnership` — verify exits 0, the
   run is printed as a kept note, and adding ` Form` to the quote fails it
   again.

   One thing the fixture cannot show, and the test says so: the hyphen
   makes `Petition-Marriage` a single token, so a quote with one word
   missing drops to two tokens and is *isolated* rather than running
   text. The missing-word case is covered at unit level instead.
4. `references/compliance.md` says the comparison is on the words the scan
   can see. 192 tests, no skips, green locally; corpus table unchanged.
   `metadata.version` 39 → 40.

Not done, as the brief asked: no prefix or substring matching, the word
floor did not move, and titles still come only from the original's
`/Title`.
