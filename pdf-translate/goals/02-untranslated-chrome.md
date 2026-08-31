# Objective: fail verify when original button chrome still draws

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md`, `references/failure-modes.md` §6, then
> `corpus/verdicts.json`. Do not read `work/translations.json` as a
> solution. Do not implement a glossary, OCR, RTL, overflow scaling, or
> hide+redraw that adds widgets.

---

## 1. Compass (not done)

`--translations` now fails if authored *page* strings never landed.
Pushbutton labels live somewhere else: `/MK /CA`, drawn from the widget
appearance **above** the page. Strip does not delete them. Retypeset does
not rewrite them. `page.get_text()` still sees them (the appearance
stream). Verify today REVIEWs `Print` as an isolated token and PASSes.

You already have two honest fixes: `--captions` (rewrite CA, drop stale
`/AP`, field count exact) or `skip` in translations.json (leave the
button as UI chrome). Neither is required. This session makes “I
translated the page and left English Print on top” a **FAIL**.

## 2. Done when — closed bar

1. **Chrome.** With `--translations`, every visible original pushbutton
   caption (length ≥ 2, same normalize as placement) must be either
   **rewritten** (output CA differs and the original caption is gone from
   `get_text()`) or **declared** (`skip` contains that caption).
   Otherwise exit non-zero and **list the caption**. Constructed LTR
   form with a Print button, not FL-150:
   - `skip: ["Print"]`, no `--captions` → PASS (chrome left on purpose)
   - `skip: []`, no `--captions` → FAIL naming `Print`
   - `--captions PrintForm=Imprimir`, `skip: []` → PASS, field count
     identical to original, `Print` absent from `get_text()`
2. **No extra widgets.** Do not hide+draw a replacement. `--captions`
   already rewrites in place. Field parity stays the existing gate.
3. **No regressions.** Omit `--translations` → chrome gate does not run
   (fillable rebuild still PASS field / fill / ink / leak). unittest +
   `corpus/verdicts.json` still match. Scans `refuse+OCR`. Pale blank
   `skip-ink`. Missing cores still fail retypeset. No `--glossary`.
4. **Docs.** SKILL.md states: skip = leave chrome; otherwise `--captions`
   or verify fails. No vendor client. No Japanese-only branch.

## 3. Not done when

- Terminology/glossary, overflow 0.7×, `/ActualText`, RTL mirror, OCR
- Auto-feeding translations.json when the flag is omitted
- Treating isolated leak-scan tokens as this failure (Print is already
  REVIEW; this gate is the hard fail)

## 4. Method

Tiny constructed PDFs. Import shipped `verify` / `strip_text` /
`retypeset`. `get_text()` *does* include widget appearance captions —
assert that, do not reimplement a caption parser. Check CA change to
detect `--captions`; check `skip` for the leave-chrome path; FAIL if
the original caption is still in output `get_text()` (stale `/AP`).

## 5. Invariants

Field identity, no redaction, graphics untouched, provider-neutral.

## 6. Proof

In-repo tests for the three Print-button cases in (1). Unittest +
corpus. One fillable `pipeline.py rebuild` with `--translations` omitted
still PASSes the four older gates.
