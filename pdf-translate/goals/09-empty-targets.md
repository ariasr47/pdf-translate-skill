# Objective: fail verify when a mapping value is empty or whitespace

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md`, `scripts/verify.py`
> (`collect_translation_targets`, `missing_translation_targets`),
> `references/translations-format.md`. Do not implement 08/10/11/12, a
> glossary, or OCR. Not FL-150.

---

## 1. Compass (not done)

`missing_translation_targets` skips strings with `len < 2`. Python
`"" in hay` is always true. Terra High mapped a real core to `""` and
`--translations` still PASSED: the page was missing the sentence and
the gate did not care. `from-cores` uses JSON `null` (retypeset already
refuses). Authored `""` / `" "` is a different hole.

## 2. Done when — closed bar

1. **Refuse.** With `--translations`, a non-skip, non-null translations
   value whose NBSP-normalized **strip** has length `< 2` is a **FAIL**,
   listed by core (e.g. `FAIL empty translation target: are living with
   me`). Same for merge `html` and override `parts[].text` that are
   empty/whitespace after strip. Do this *before* (or besides) the
   placement search so `""` cannot hide inside `len < 2` continue.
2. **Constructed LTR.** Complete mapping except one core `""` → FAIL
   naming that core. Same mapping with a real ≥2-character target →
   PASS (existing placement). `" "` and `"\u00a0"` fail the same way.
   Identity `"Name:": "Name:"` still PASS.
3. **Null is still retypeset’s job.** `from-cores` nulls fail retypeset,
   not this gate (verify never sees a successful PDF with nulls). Do not
   change `from-cores`.
4. **No regressions.** Omit `--translations` → unchanged. unittest +
   corpus green. 08 behaviour (if present) unchanged. No glossary.
5. **Docs.** `translations-format.md`: empty is not a translation; use
   `skip` to drop a span, not `""`.

## 3. Not done when

- Caption width, override markers, narrow-column warning
- Treating skip entries as empty failures
- Changing the placement length-1 skip for *non-empty* one-character
  targets (that rule stays)

## 4. Method

Unit test on a helper (empty-target list) plus one retypeset+verify
fixture. Import shipped `verify`.

## 5. Invariants

Provider-neutral. Missing cores still fail retypeset.

## 6. Proof

In-repo tests for `""`, `" "`, NBSP-only, and a happy ≥2 target. Full
unittest + corpus.
