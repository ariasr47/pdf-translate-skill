# Extract keeps an authored widget_text.json — 25 September 2026

**Assignment.** Canary run 4 found the defect, and it was filed as a proposal
on 25 September. The product advised doing it first after R-50, and Rodrigo
assigned it in this session. It ships as v79, stacked on #49 (v78).

## The defect, reproduced

SKILL.md and `pipeline.py`'s usage both say:
1. run `init` bare to get the `widget_text.json` scaffold;
2. author the targets;
3. run `init` again with `--widget-text`.

The second run passed the file to strip, which applied it. Extract then
wrote a fresh scaffold to `WORK/widget_text.json`, the file just applied.

On `corpus/choice_fields.pdf`, on `ef03a75` (v78):
- 5 targets were authored in place: 3 `Fruit` labels and 2 `Color` labels;
- `init --widget-text WORK/widget_text.json` exited 0;
- `stripped.pdf` carried all 5 labels;
- `widget_text.json` then held 5 nulls.

What that costs an author:
- **Re-applying the emptied file** is refused: "Fruit: option Apple target
  is null". The work is lost, loudly.
- **A bare re-run of `init`** exits 0 and ships the English labels. No
  verify gate reads tooltips or display labels, so nothing says so. That
  gap is filed as its own proposal.

## What changed

- `strip_text.widget_text_is_authored(path)` is true when the file holds
  any string a scaffold does not write:
  - a scaffold's only strings are each entry's `type` and each slot's
    `source` and `export`, and every `target` is null;
  - so a non-null target counts as authored, and so does a string shorthand
    such as `{"options": {"Apple": "Manzana"}}`;
  - a file that is not JSON counts too, since someone was writing it;
  - a missing file does not.
- `extract_segments` checks that before writing. If the file is authored,
  it writes nothing over it, and the result carries
  `widget_text_kept: True`. `ExtractResult.widget_text_kept` defaults to
  `False`.
- The console prints `kept …/widget_text.json: it holds authored widget
  text, so no fresh scaffold was written over it (delete it for one)`
  instead of the "author each target" line.
- The result's `widget_text` is still the fresh scaffold of this PDF.

**Unchanged:**
- A file whose every target is null is refreshed, so a work directory
  reused for another PDF gets that PDF's scaffold.
- The app's call shape writes only such scaffolds, so it is byte for byte
  as before. The app's session checked its code read-only: it never writes
  a `widget_text.json`, and reads the extract result only by `cores`,
  `segments` and `warnings`.

**Docs:** SKILL.md, `references/widget-text.md`,
`references/consumer-guide.md` and `pipeline.py`'s usage.

## Red, then green

`tests/test_widget_text_authored.py` has 6 tests:
1. **The acceptance.** On `corpus/choice_fields.pdf`,
   `init --widget-text WORK/widget_text.json` leaves the file
   byte-identical, the console says "kept", and `stripped.pdf`'s `/Opt`
   carries all 5 authored labels.
2. **A bare re-run** keeps a shorthand-authored file.
3. **A file that is not JSON** is kept, and `run_extract` reports
   `widget_text_kept`.
4. **An unauthored scaffold of another PDF** is replaced by this PDF's
   scaffold.
5. **Extracting twice** writes a byte-identical scaffold.
6. **The result** still carries the fresh scaffold when the file is kept.

On `ef03a75`, 1 to 3 fail on the file's bytes. 4 to 6 fail on the missing
`widget_text_kept`; 4 and 5 already hold otherwise.

## Suite

CI's commands on macOS, on this change:
- **Suite:** 774 tests (768 on v78, plus these 6), with 0 ResourceWarnings.
  The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is item 3's expected failure.
- **Canary, repository tests and eval fixtures:** all exit 0.

Rule 1 does not apply: nothing here renders, shapes, lays out or touches a
font.
