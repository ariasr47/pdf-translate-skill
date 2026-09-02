# Objective: fail verify when an override drops sibling `d.` or `$`

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md` overrides paragraph,
> `scripts/extract_segments.py` (marker / tail / inner-gap),
> `references/translations-format.md` overrides. Do not implement
> 08/09/10/12, glossary, or OCR. Not FL-150.

---

## 1. Compass (not done)

Inner-gap rows look like `d. Label      [widget]     .... $`. Extract
strips the marker (`d.`) and tail (`$`) into segment fields; an override
replaces the whole span with `parts`. Terra/Luna Extra High dropped
`d.` on the TANF line; Claude v2 kept it. Placement still PASSES
because the remaining Japanese landed. This session checks the override
against the source span’s marker and tail.

## 2. Done when — closed bar

1. **Keep.** With `--translations`, for every override: find original
   segments on that page whose `text` contains `override.contains`. If
   the matched segment has a non-empty `marker`, some `parts[].text`
   must contain that marker (stripped). If it has a non-empty `tail`
   (the `$` after dots), some part must contain that tail. Else FAIL
   listing `contains` + the missing token (`d.` or `$`).
2. **Constructed LTR.** One inner-gap line `d. Public aid      [cb] .... $`
   (extractor already warns inner-gap). Override parts that include
   `d.` and `$` → PASS. Same override with only the translated label →
   FAIL naming the dropped token(s).
3. **No auto-fix.** Do not rewrite parts. Do not auto-merge. The author
   fixes the JSON.
4. **No regressions.** Overrides on spans without marker/tail unchanged.
   Omit `--translations` → gate does not run. unittest + corpus green.
   Existing inner-gap fillable fixture still PASSes if its override
   (if any) already keeps markers — do not “fix” it by dropping `$`.
5. **Docs.** SKILL.md + translations-format.md: override parts keep
   source marker and `$`.

## 3. Not done when

- Caption width, empty targets, identifier gate
- Auto-inserting `d.` in retypeset
- Warning-only (this sitting is a FAIL)

## 4. Method

Tiny constructed PDF with a real inner-gap (six-plus spaces + checkbox).
Import shipped extract + retypeset + verify. Need `segments.json` at
verify time: either load `--translations` plus `segments.json` beside
it, or pass the original PDF and re-extract in the test. Prefer: test
builds segments via shipped `extract_segments`, then verify reads
`translations.json` and that `segments.json` from the same work dir
(`--segments` flag **or** default `segments.json` next to the mapping).
If you add `--segments`, omit it → this gate does not run (same pattern
as `--translations`).

## 5. Invariants

Provider-neutral. Inner-gap still needs an override; this only checks
the override you wrote.

## 6. Proof

PASS with `d.`+`$`; FAIL listing each drop. Full unittest + corpus.
