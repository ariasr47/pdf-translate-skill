# Objective: warn when stacked cores share a skinny column

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md` (narrow-column note from session 0),
> `scripts/extract_segments.py` `merge_candidate_warnings`. Do not
> implement verify gates 08–11, auto-merge, glossary, or OCR. Not FL-150.

---

## 1. Compass (not done)

Pay-stub boxes are many short English cores, same x, stacked y, bbox
width ~one word. Authors translate each line-break independently and
the box turns to crumbs. Merge-candidate warnings look for *open
sentences*. A list of short labels never triggers them. This session
**warns**. It does not merge.

## 2. Done when — closed bar

1. **Warn.** `extract_segments` emits `kind: narrow-column` when ≥3
   non-passthrough cores on one page share:
   - `|x0 - x0_ref| < 4` (same left),
   - bbox width `< 90` pt,
   - adjacent y (gap `< 2.2 × size`, same idea as merge candidates).
   Warning lists `page`, `ids`, `lines`. Printed with the other
   warnings. **Never auto-merge.**
2. **Constructed LTR.** A 70-pt-wide column of 5 one-word lines → at
   least one `narrow-column` warning covering those ids. A normal
   paragraph wider than 90 pt → no such warning. Sibling list items
   with width ≥ 90 pt must not be swallowed (that is why we warn, not
   merge).
3. **No regressions.** Existing extract tests still see inner-gap and
   write/find/say warnings. unittest + corpus green. Verify unchanged.
4. **Docs.** SKILL.md already says look; point at this warning as the
   yell. `extract_segments.py` header comment lists the new kind.

## 3. Not done when

- Auto-merge by x
- A verify FAIL for skinny columns
- Changing merge-candidate logic as a substitute
- Bakeoff

## 4. Method

Tiny constructed PDF. Import shipped `extract_segments`. Assert warning
shape in unittest.

## 5. Invariants

Provider-neutral. Geometry-only. No glossary.

## 6. Proof

Warning present on the skinny fixture, absent on a wide paragraph. Full
unittest + corpus. Verify exit codes unchanged.
