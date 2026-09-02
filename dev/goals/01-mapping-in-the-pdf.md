# Objective: fail verify when authored translations never appear on the page

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md`, `references/failure-modes.md`, then
> `corpus/verdicts.json`. Do not read `work/translations.json` as a
> solution. Do not implement a glossary, OCR, RTL ActualText, or layout
> mirroring.

---

## 1. Compass (not done)

Retypeset already fails if a core is missing from `translations.json`.
Verify can still PASS a file whose pages never received those target
strings (you pointed verify at the stripped PDF, a failed write, NBSP
mismatch, etc.). This session closes **placement**: the mapping you
authored is actually in the output text layer. It does not judge whether
the Japanese is the right legal term.

## 2. Done when — closed bar

1. **Round-trip.** `verify.py` accepts `--translations translations.json`.
   After retypeset, every non-passthrough **target** string (length ≥ 2,
   whitespace/NBSP normalized) must appear in `page.get_text()` of the
   output. Missing ones → exit non-zero, listed. Constructed LTR form
   (not FL-150): complete mapping on a retypeset PDF → PASS; the same
   mapping against the **stripped** PDF → FAIL naming a missing target.
2. **No glossary.** Do not add `--glossary`, domain term lists, or
   FL-150-specific Japanese in verify. Wrong-word quality is the mapping
   author’s job (and a reason not to use a weak model), not a skill
   dictionary.
3. **No regressions.** Existing unittest + `corpus/verdicts.json` still
   match. Scans `refuse+OCR`. Pale blank `skip-ink`. Fillable constructed
   form still PASS field / fill / ink / leak. Omit `--translations` →
   current verify behaviour unchanged.
4. **Docs.** SKILL.md documents `--translations`. No vendor client. No
   Japanese-only branch.

## 3. Not done when

- Terminology/glossary gates
- `/ActualText` or RTL mirroring
- OCR, bakeoff, auto-merge

## 4. Method

Tiny constructed PDFs. Import shipped `verify` / `retypeset`. Keep
`pipeline.py rebuild` working.

## 5. Invariants

Field identity, no redaction, graphics untouched, glyf + rasterization
assert, missing cores still fail retypeset, provider-neutral.

## 6. Proof

In-repo test for (1). Unittest + corpus log. One `pipeline.py rebuild` on
a fillable form with `--translations` omitted still PASSes the four
existing gates.
