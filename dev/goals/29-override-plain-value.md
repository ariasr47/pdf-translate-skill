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

## 5. Closing note — 3 September 2026, closed

**Reproduced first, before and after on the same fixture.** The inner-gap
row `d. Public aid  [cb] .... $` with an override that places `d. Ayuda`
and `.... $`, and the core mapped to `null`:

| | retypeset |
|---|---|
| before | `FAIL: 1 untranslated segments: p0: Public aid` |
| after | exit 0, `d. Ayuda` in the layer, verify 0 |

The author's only way out was a plain value that is never drawn, which is
what `qa_check` then graded on FL-100 — 13 warnings about length and added
numbers on strings no reader would ever see.

**Done bar, item by item.**

1. The coverage check counts an override as coverage. `over_by_page` is
   built once, before the check, and a small `override_for(pno, text)`
   answers the same question the placement loop already asked — the two
   now share it, so "covered" cannot drift between them.
2. verify's placement gate needed no change: `collect_translation_targets`
   already skips a `None` value and already collects override part texts,
   so with the core null it demands `d. Ayuda` and `.... $` and not the
   plain value. Asserted directly.
3. A core covered on one page and not another still fails, naming the
   page: a two-page fixture with the override on page 0 only fails with
   `p1` and not `p0`, and no file is written.
4. `qa_check` already drops null values before grading, so a null covered
   core produces no findings — asserted rather than assumed.
   `translations-format.md` says so in the `overrides` block and in the
   authoring order; `SKILL.md` step 4's null rule names the exception.
5. **Tests** (`OverridePlainValueTests`, 5) for 1–4 plus the guard: a null
   with no override covering it still FAILs and names the core. 205 tests,
   no skips, green locally; corpus table unchanged. `metadata.version`
   42 → 43.

Not done, as the brief asked: a null is legal only where an override
covers it — nowhere else — and the override-marker gate is untouched
(`PASS override parts keep markers and tails` is asserted on the null
build).
