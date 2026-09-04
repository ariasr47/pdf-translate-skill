# Objective: the font subset covers everything the job will draw

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/prepare_font.py` (the `chars` collection around line 113),
> `scripts/retypeset.py` (`notices`, and the coverage check's override
> rule), `references/fonts.md`, and
> `dev/canary/runs/2026-09-03-run3-summary.md`. Not FL-150.

---

## 1. Compass (not done)

`prepare_font.py` builds the subset's character set from
`translations`, `merges[].html` and `overrides[].parts[].text`. Two
things shipped on 3 September moved past it:

- **Row 29** made a core `null` where an override covers every
  occurrence. `chars.update(v)` on that value raises
  `TypeError: 'NoneType' object is not iterable`, so the font step
  crashes on a mapping the pipeline itself calls valid.
- **P7** added `notices`. The charset never reads them, so a character
  used only in the notice is missing from the subset; retypeset's glyph
  check then FAILs the build. Loud rather than silent, but it blocks a
  correct notice.

Both reproduce directly:

```
null core -> RAISES TypeError 'NoneType' object is not iterable
notice-only chars -> rc 0 | missing from the subset: ['ó', '“', '”']
```

Canary run 3 hit both. Opus 5 worked around the crash with a hand-built
`font_charset.json`; Fable 5.1 rewrote its notice with straight quotes.
Two models, independently, on the day the two features shipped.

## 2. Done when — closed bar

1. A `null` translation value is skipped, not iterated: `prepare_font`
   builds the same charset it would have built with that core absent.
2. `notices[].text` is harvested, with `‖` discarded like every other
   weight split, so every character the notice will draw is in the
   subset.
3. The pass is one function that takes the mapping and returns the set,
   so the next block added to `translations.json` has one obvious place
   to be added — and a comment saying that is what it is for.
4. Tests: a mapping with a null override-covered core subsets without
   raising and covers the override's parts; a notice-only character
   (`ó`, a curly quote) is in the subset and the same job then builds
   through retypeset with the glyph check passing; the existing
   `prepare_font` tests unchanged.
5. Full unittest + corpus green; `metadata.version` bumped.

## 3. Not done when

- Adding characters the job will not draw "just in case"
- Reading anything but the mapping to decide the charset
- Making the glyph check softer to compensate

## 4. Method

Reproduce both with a constructed mapping (the snippet above), fix the
collection, assert the subset covers what the job draws.

## 5. Invariants

The subset covers exactly what this job draws. A mapping the pipeline
accepts must not crash the step before it.

## 6. Proof

Both reproductions passing; a notice with an accent and curly quotes
building end to end; full unittest + corpus.

## 7. Closing note — 3 September 2026, closed

**Both halves already reproduced** by canary run 3 and confirmed directly
before touching anything:

```
null core           -> RAISES TypeError 'NoneType' object is not iterable
notice-only chars   -> rc 0 | missing from the subset: ['ó', '“', '”']
```

After the fix, the same script prints `null core -> rc 0` and
`missing from the subset: []`.

**Done bar, item by item.**

1. A `null` value is skipped rather than iterated. It means "covered by an
   override, never drawn as a plain value" (row 29), so there is nothing
   to harvest from it and the rest of the charset is exactly what it would
   have been with that core absent.
2. `notices[].text` is harvested. `‖` is discarded once at the end, so the
   notice's weight split is dropped the same way a translation's is.
3. The whole walk is now **`job_charset(conf)`** — one function, taking
   the mapping and returning the set, with a docstring that says it is the
   one place to add the next block and names the two that were missed this
   way. `prepare_font()` calls it and nothing else changed.
4. **Tests** (`JobCharsetTests`, 5): the null core skipped at unit level
   and through `prepare_font.main` (asserting the override's own parts are
   in the subset); the notice harvested and `‖` not; the printable floor
   on an empty mapping; and the end of the story — a job whose accents and
   curly quotes appear **only** in the notice, subsetted and then built
   through retypeset with the glyph check silent and the notice verbatim
   in the layer. Re-introducing both halves in place fails four of the
   five.
5. `references/fonts.md` says what the charset covers and that
   `job_charset` is where a new block goes. 219 tests, no skips, green
   locally; corpus table unchanged. `metadata.version` 45 → 46.

Not done, as the brief asked: nothing is added "just in case", the
charset still reads only the mapping, and the glyph check is untouched —
it is the thing that caught this, and it stays exactly as strict.
