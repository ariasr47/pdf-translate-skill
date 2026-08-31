# Objective: fail retypeset when type shrinks below 0.7× unless opted in

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md`, `references/translations-format.md`, then
> `corpus/verdicts.json`. Do not read `work/translations.json` as a
> solution. Do not implement a glossary, OCR, RTL, or chrome work.

---

## 1. Compass (not done)

Retypeset already **notes** `scaled to 0.33x — consider a shorter
translation` and still writes the PDF. Verify PASSes. A 4pt (or smaller
htmlbox) label ships. v1 shipped 3.01pt because `insert_htmlbox(...,
scale_low=0)` has no floor; the 4.0pt clamp is only the single-line
path. The note is not a gate. This session makes undersized type a
**FAIL**, with an explicit mapping opt-in for the rare cell that must
stay tiny.

## 2. Done when — closed bar

1. **Refuse.** `retypeset.py` exit non-zero and **does not save** when any
   placed run scales below **0.7×** vs its original size, listing page +
   ratio + core (or merge first line). Paths that already shrink must all
   count: ordinary line, dot-leader label, override `max_width`, merge
   `insert_htmlbox`. Threshold is the existing note’s `fs2 < fs * 0.7`
   (strict `<`). Constructed LTR, not FL-150: a long target squeezed
   before a widget → FAIL naming the core; the same mapping with that
   core in `allow_scale` → PASS and the file is written.
2. **Opt-in.** `allow_scale` in translations.json (list of cores / merge
   first lines / override `contains`). Opted-in undersize still prints a
   note, still ships. No per-domain dictionary of “too small.”
3. **No regressions.** Existing unittest + corpus. Fillable constructed
   form still retypeset 0 and PASS field/fill/ink/leak. Missing cores
   still fail retypeset. Chrome/placement `--translations` behaviour
   unchanged. No `--glossary`.
4. **Docs.** SKILL.md + translations-format.md: the note is now a fail;
   `allow_scale` is how you accept tiny type.

## 3. Not done when

- Glossary, chrome, `/ActualText`, RTL, OCR, verify-only backstop
- Changing the 0.7 number, or an absolute pt floor as the gate
- Auto-rewording

## 4. Method

Tiny constructed PDFs. Import shipped `retypeset`. Do not save on
overflow (same as missing cores). Existing fillable fixture does not
scale below 0.7× (probed min 9pt) — do not “fix” it by widening.

## 5. Invariants

Field identity, no redaction, graphics untouched, provider-neutral.

## 6. Proof

In-repo tests for squeeze FAIL / allow_scale PASS. Unittest + corpus.
One fillable rebuild without overflow still PASSes the four older gates.
