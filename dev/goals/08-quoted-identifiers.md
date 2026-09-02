# Objective: fail verify when write/find/say names vanish from the page

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md`, `scripts/extract_segments.py`
> (`write_find_say_hits`), `scripts/verify.py` (`--translations`),
> `corpus/verdicts.json`. Do not read `work/translations.json` as a
> solution. Do not implement a glossary, OCR, empty-target, caption-width,
> or override-marker work. Not FL-150.

---

## 1. Compass (not done)

The extractor already **warns** on quoted strings and `Form` / `Schedule`
/ `Attachment` / `Exhibit` names. Authors still translate them. Placement
(01) then PASSES because the *translated* target landed. The clerk cannot
find `"Attachment A"` or `Schedule Q`. This session makes those source
tokens a **FAIL** unless the mapping opts out.

## 2. Done when — closed bar

1. **Survive.** With `--translations`, every `write_find_say_hits` span
   from the **original** page text (`quoted` and `form-name` kinds) must
   appear in the output text layer (`page_search_text`, same normalize as
   placement). Missing ones → exit non-zero, **list the span**. Import
   `extract_segments.write_find_say_hits` — do not fork the regexes.
2. **Constructed LTR, not FL-150.** One page containing both:
   - `Write "Attachment A" at the top.`
   - `Please attach Schedule Q.`
   Cases:
   - Target keeps both tokens (instruction may change language) → PASS.
   - Target translates the payload (`Anexo A` / `Anexo Q`) so the source
     tokens are gone → FAIL naming `Attachment A` and/or `Schedule Q`.
3. **Opt-out.** `allow_translate` in `translations.json`: a list of
   source spans the author *meant* to translate. Those spans are not
   required in the output. Omit the key → same as `[]`. Record why in
   NOTES (scripts do not read NOTES).
4. **No regressions.** Omit `--translations` → this gate does not run.
   unittest + corpus green. Scans `refuse+OCR`. Placement, chrome, 0.7×
   unchanged. No `--glossary`. No Japanese-only branch.
5. **Docs.** `SKILL.md` + `translations-format.md`: extractor warning is
   halt-and-confirm; missing source token fails unless `allow_translate`.

## 3. Not done when

- Empty targets (09), caption width (10), override `d.`/`$` (11)
- Narrow-column auto-merge
- URL/email hits as a hard fail (quoted + form-name only this sitting)
- A glossary of form names
- Bakeoff in this session

## 4. Method

Tiny constructed PDF in the unittest. Import shipped `extract_segments`
and `verify`. Drive strip → extract → retypeset → `verify(...,
translations=...)`.

## 5. Invariants

Field identity, no redaction, graphics untouched, provider-neutral.

## 6. Proof

In-repo tests for (2) PASS / FAIL / `allow_translate`. Full
`tests.test_pipeline`. Corpus table unchanged.
