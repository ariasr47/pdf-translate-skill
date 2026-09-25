# Verify gate 22: widget text left in the source language — 25 September 2026

**Assignment.** The gap was found while building the `widget_text`
overwrite fix (v79), and was filed as a proposal at the app's suggestion.
The product advised medium priority, REVIEW not FAIL, and Rodrigo assigned
it after `/Lang`. It ships as v81, stacked on #51 (v80).

## The gap

Tooltips (`/TU`), dropdown display labels and text-field values and
defaults live in annotation dictionaries. No content stream carries them,
so the leak scan cannot see them. `verify.py` read `/Opt` only for export
parity, and never read `/TU`. So a strip without `--widget-text`, such as a
bare re-run of `pipeline.py init`, shipped them in the source language and
no gate said so.

## What changed

**Gate 22, `widget-text`,** always runs, right after `/Opt` export parity.
`GATE_NAMES` lists it after `opt-export-parity`.
- **What it compares:** each field's strings in the output against the
  original's, by full field name and, for a dropdown, by export value. It
  uses `strip_text.widget_text_scaffold` on both files.
- **What is reported:** a string that has a letter in it and is unchanged
  is REVIEW, one finding per string. `where` is the field's full name, and
  `text` is `tooltip: …`, `value: …`, `default: …` or `option EXPORT: …`.
- **What is kept on purpose, and silent.** The widget-text mapping marks it.
  That mapping is `--widget-text PATH` (`widget_text=` a path or a dict in
  the library), else the `widget_text.json` beside `--translations`, found
  the way `segments.json` is. A string is a keep when:
  - its field has no key in the mapping;
  - the field's entry leaves that slot out;
  - the slot's target equals its source.

  A null target is not a decision, so an unauthored scaffold excuses
  nothing. Keys resolve the way strip resolves them; a mapping strip would
  refuse is not used, and the REVIEW says why.
- **Verdicts:**
  - silent when no field carries widget text with a letter in it;
  - PASS names how many strings were checked;
  - never FAIL.
- **`pipeline.py rebuild`** protects `--widget-text` as an input, as it
  does `--translations`. Its default verify already finds the mapping
  beside the work directory's `translations.json`.

**Docs:**
- `verify.py`'s gate list;
- `references/gates.md`: a new section, the name list, the findings
  table and the flags. Its "twenty-one gates" sentences are superseded;
- SKILL.md's one-line rules;
- `references/widget-text.md`;
- the README's stage list.

## Red, then green

`tests/test_widget_text_gate.py` has 9 tests. 8 fail on `eb14a4c` (v80), and
the ninth guards the silent case.
1. **The request's acceptance.** `corpus/choice_fields.pdf` stripped
   without `--widget-text` is REVIEW, with its 5 labels named by field.
2. **Translated labels** pass.
3. **Color's key deleted** in the mapping passes.
4. **A target equal to its source** (`Blue` → `Blue`) passes.
5. **The mapping beside `translations.json`:**
   - a null scaffold there is REVIEW;
   - an empty authored mapping there (every key deleted) passes.
6. **Tooltips and text values** are reported, and so are dropdown labels.
7. **Strings with no letter in them** (`2026`, `#12`) are not counted
   beside a translated tooltip: PASS, 1 string.
8. **A PDF with no widget text** records no gate.
9. **The name order** in `GATE_NAMES`.

## On real deliveries

Canary run 4's two deliveries, run through the gate's function with each
run's own files:
- **Opus 5.5:** 11 strings checked, none left.
- **Opus 5:** 11 strings checked.
  - It kept "Kindergarten" on purpose, with a target equal to its source,
    in a separate `widget_text_es.json`.
  - By default verify reads the null scaffold beside its mapping, so that
    one label is REVIEW.
  - With `--widget-text widget_text_es.json` it is silent.

That is the gate working as designed: the keep is visible only in the file
the author used.

## Suite

CI's commands on macOS, on this change:
- **Suite:** 789 tests (780 on v80, plus these 9), with 0 ResourceWarnings.
  The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  failing with the same assertion as on v80, and there is item 3's
  expected failure.
- **Canary, repository tests and eval fixtures:** all exit 0.

Rule 1 does not apply: nothing here renders, shapes, lays out or touches a
font.
