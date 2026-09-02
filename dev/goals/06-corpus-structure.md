# Objective: one new constructed structure class with a recorded verdict

> Hand this to a `/goal` session. Queue 01–05 were content gates.
> This is **documents**. Pick ONE of radio/dropdown, mixed rotation, or
> attachments. Do not implement OCR, glossary, or RTL work.

---

## 1. Compass (not done)

The seed corpus has color, tables, encryption, expansion, scan, columns,
pale blank, **uniform** `/Rotate 90`, RTL source, XObject text. It has
**no choice fields**. Constructed tests cover text / checkbox / pushbutton
only. `verify` field parity is name+type; a dropdown whose `/Opt` list is
stripped still PASSes if the widget remains. Record a born-digital form
whose structure *is* the dropdown (and a listbox — same PDF choice
family). Pymupdf cannot reliably create radio groups (bad xref); do not
fake radios as checkboxes.

## 2. Done when — closed bar

1. **Corpus.** `corpus/choice_fields.pdf`: running text + ComboBox with
   ≥3 choices + ListBox with ≥2 choices. `verdicts.json` + README:
   `translate`. Existing corpus harness: extract exit 0, ≥1 segment.
2. **Identity.** Import shipped strip / retypeset / verify. After a
   complete mapping of the running text, widget **count**, field **names**,
   **types** (ComboBox, ListBox), and **choice_values** match the original.
   Not FL-150.
3. **No regressions.** unittest + rest of corpus. No new verdict kind.
   No glossary.

## 3. Not done when

- Mixed rotation (already have uniform rotate; not this file)
- Embedded-file attachments
- Fake radio groups with garbage rects
- Changing field-parity to inspect `/Opt` in verify.py unless the test
  already drives the real widgets

## 4. Method

Tiny constructed PDF committed under `corpus/`. Builder can live in
tests so the file is reproducible.

## 5. Invariants

Provider-neutral, field names/types, no redaction.

## 6. Proof

Corpus table + in-repo strip→retypeset choice identity test.
