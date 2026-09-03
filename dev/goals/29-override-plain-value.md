# Objective: a core fully replaced by an override needs no plain translation

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/retypeset.py` (the coverage check for missing translations and
> the override branch), `scripts/verify.py` (`missing_translation_targets`,
> `collect_translation_targets`), `references/translations-format.md`
> (`overrides`), and `dev/canary/runs/2026-09-03-fable-5.1-fl100.md`.
> Not FL-150.

## 1. Compass (not done)

An override replaces its whole span with explicit parts. retypeset's
coverage check still demands a non-null translation for the core, and
verify's placement gate then wants that never-drawn value verbatim in the
layer — so the author writes a plain translation that exists only to
satisfy two checks, and on FL-100 `qa_check` then flagged the phantom
values for length and added numbers (13 warnings).

## 2. Done when — closed bar

1. A core every occurrence of which is covered by an override may be
   `null` (or absent) in `translations`: the coverage check counts the
   override as coverage.
2. verify's placement gate expects the override's part texts in the layer
   and not the plain value; the override-marker gate unchanged.
3. A core covered on one page and not another still needs its plain value
   for the uncovered occurrence, and the check names the page.
4. `translations-format.md` says so; `qa_check` does not flag a null
   override-covered core as untranslated.
5. Tests for 1–3; full unittest + corpus green; `metadata.version`
   bumped.

## 3. Not done when

- Letting a null translation through anywhere an override does not cover
- Weakening the override-marker gate

## 4. Proof

The fixture with one covered and one uncovered occurrence; full unittest
+ corpus.
