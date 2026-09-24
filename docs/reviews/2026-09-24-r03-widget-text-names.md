# R-03: widget text keyed by the fully qualified field name — 24 September 2026

**Assignment.** The product ranked this priority 1 of the review
assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`; the rule behind it is
`docs/DECISIONS.md`, 2026-09-24, and the finding is R-03 in
`docs/REVIEW-2026-09-24.md`. The product's acceptance criteria are:
- every widget's tooltip, value and options equal those of the same fully
  qualified field in the source;
- each page's barcode value equals that page's source value;
- a failing-then-passing test, Rule 1 with a rendered pixel comparison, the
  wild probe with a render diff, a version bump, and a notice to the app.

## The defect

Widget text (`/TU` tooltips, `/Opt` display labels, text `/V` and `/DV`)
was keyed by the widget's partial `/T`. XFA-derived government forms repeat
partial names under many parents: FL-300 has 28 partial-name collisions and
0 full-name collisions. So:

- **The scaffold kept the first one.** `widget_text_scaffold` kept only the
  first widget of each partial name, so the others never got an entry.
- **Strip copied it everywhere.** It then wrote that entry onto every widget
  sharing the partial name, or onto every widget sharing the base name
  without `[n]`. Fields announced another field's name, and page 1's
  PDF417 barcode payload overwrote every page.
- **The parity gate lost widgets.** `choice_exports` kept the *last* choice
  widget of each partial name. A changed export on an earlier same-named
  dropdown passed verify's `/Opt` parity.

## The change

`pdf_translate/strip_text.py`:
- **`field_full_name(annot)`** walks the `/Parent` chain and joins every
  `/T` with dots. It is cycle-safe.
- **`widget_text_scaffold`** keys each entry by full name.
- **`choice_exports`** keys by full name, and gives a second widget of the
  same field its own `(widget n)` key.
- **`resolve_widget_text_keys`** decides, before anything is written, which
  field each `--widget-text` key names:
  - a full name names that field alone;
  - a partial name, or its base, names a field only when it is unique;
  - an ambiguous partial name, or two keys for one field, is refused with
    the candidates' full names;
  - an entry is refused when the widgets sharing its full name differ in the
    text it would write;
  - only `/Widget` annotations take part, because a comment's `/T` is its
    author.
- **Unchanged:** captions and `--hide-buttons` keep partial names (F9/row
  35, not assigned).

Also changed:
- `references/widget-text.md` and `SKILL.md` step 2 describe the rule, and
  `docs/DECISIONS.md` records it;
- the version goes from 61 to 62.

## Red, then green

`tests.test_pipeline.WidgetTextFullNameTests` builds one constructed form
(`build_same_leaf_widgets_pdf`):
- two text fields named `Name[0]` under `Applicant[0]` and `Spouse[0]`;
- a unique `Applicant[0].Phone[0]`;
- two dropdowns named `Pick[0]` under `A[0]` and `B[0]`;
- a `PDF417BarCode1[0]` on each of three pages, under
  `form1[0].#pageSet[0].Page1[i]`, each with that page's value.

On `main` (`988b787`), all four tests failed (exit 1):
- **the scaffold:** `KeyError: 'Applicant[0].Name[0]'`;
- **the identity round trip:** refused, because the first `Pick[0]` entry
  was applied to the second dropdown (`options ['a1', 'a2'] are not export
  values of this field (['b1', 'b2'])`);
- **the ambiguous partial key:** no refusal;
- **`/Opt` parity:** `['Pick[0]'] != ['A[0].Pick[0]', 'B[0].Pick[0]']`.

With the change, they pass alongside the existing widget-text,
verify-report and results tests: 55 tests OK, exit 0. Two more tests
lock the guards the independent verification led to (below), which makes
57.

## Acceptance on the real forms

Every wild PDF with widgets: the scaffold authored with identity targets
(each entry's own source; blank sources left out, as an author deletes
them), then strip, then every widget compared with the source by full
name. "Before" is a `git archive` of `main`; "after" is this branch.

| form | fields | scaffold entries before → after | fields with another field's text, before → after | barcode pages wrong, before → after |
|---|---:|---:|---:|---:|
| cajc-fl100 | 158 | 141 → 148 | 1 → 0 | — |
| cajc-fl300 | 248 | 140 → 212 | 57 → 0 | — |
| fda-3500 | 239 | 221 → 233 | 9 → 0 | — |
| opm-sf15 | 37 | 26 → 34 | 4 → 0 | — |
| state-ds11 | 69 | 27 → 27 | 0 → 0 | — |
| uscis-g28 | 101 | 98 → 101 | 3 → 0 | 3/4 → 0/4 |
| uscis-i864 | 219 | 208 → 219 | 11 → 0 | 11/12 → 0/12 |
| uscis-i9 | 126 | 125 → 126 | 1 → 0 | — |
| uscis-n400 | 440 | 427 → 440 | 13 → 0 | 13/14 → 0/14 |
| irs-1040es, irs-w4, irs-w9 | 118, 48, 23 | 0 → 0 | 0 → 0 | — |

In total, **99 fields on 8 forms dropped to 0**, and **27 of 30 barcode
pages dropped to 0 of 30**. For example, on `main`, N-400 page 2's barcode
`N-400|01/20/25|2` became page 1's `…|1`.

The measurement also showed a limit of the identity check itself. The
USCIS and FDA dropdowns carry a blank display option, and an empty target
is refused by design, so an identity authoring must leave those out. That
is unchanged here.

## Suite, probe and Rule 1

**Suite.** CI's 22 modules on this branch, on macOS, ran 701 tests: main's 695
plus 6 new ones. There was 1 failure, and no errors or skips. The failure is
the macOS-only `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
which fails identically on `main` and not on Linux or Windows CI. The other
steps passed too: the canary's 15 tests OK, binary integrity's 3 OK, and
the eval fixtures built.

**The wild probe.** `dev/wild/probe.py` ran into a scratch directory,
diffed against the tracked `dev/wild/results.json`, and exited 0 on all 17
files. The only differences are `extract.widget_text` counts on 8 forms,
the new one-entry-per-field scaffold: FL-300 140 → 212, N-400 427 → 440,
and so on. Every verdict and segment count is identical.

**The render diff.** All 17 wild PDFs were stripped without widget text by
`main` and by this branch, and every page rendered at 72 dpi with
annotations: 449 pages, 0 differing.

**Rule 1.** Independent passes ran on a different model (Sonnet), each with
its own scripts, never this author's harness.
- **Acceptance.** Identity and marker authoring reproduced the before and
  after numbers above: 99 → 0 fields on 8 forms, and 27 → 0 barcode pages
  out of 30. Legacy partial keys still applied correctly: 1,346 of them
  across 8 forms. Every sampled ambiguous key was refused, naming every
  candidate.
- **Pixels.** At 150 dpi with annotations, `main` and this branch render
  identically (0.0) on page 1 of G-28, I-864 and N-400 and on every FL-300
  page. On USCIS pages 2 and later the ratio is 2.5e-5 to 9.7e-5, and every
  differing region lies inside that page's `PDF417BarCode1[0]` widget. That
  is exactly the value `main` got wrong.
  - FL-300's 57 corrections are tooltips, which do not render. A dropdown
    renders its export value, not its display half. So pixels alone cannot
    show this defect, and the acceptance check above compares the fields
    themselves.
- **Break it.** One new defect in the first version of this change:
  `field_full_name` joins with `.`, so a `/T` containing a dot spells the
  same full name as a nested field, and one entry overwrote both.
  - Two older gaps are closed by the same guards: distinct widgets that
    repeat one full name, and a comment whose `/T` (its author) matched a
    field.
  - The guards: an entry is refused when widgets sharing its full name
    differ in the text it writes, and only `/Widget` annotations take part.
- **Code review.** It found a dangling evidence pointer, a garbled sentence
  in `references/widget-text.md`, and three stray files a verifier had
  written into `pdf-translate/`. All are fixed, and the strays are in the
  Trash.
- **Re-check of the guards.** A second Sonnet pass rebuilt the three cases.
  Differing text is refused, with no output file and CLI exit 2. Identical
  text is applied. An entry that writes only fields where the widgets agree
  is applied. The comment is untouched. 57 targeted tests OK. Six real
  forms round-trip with every barcode page its own. Pass.

**Follow-ups found here, not assigned.**
- Pushbutton tooltips have no widget-text channel: the scaffold skips
  pushbuttons, and `--captions` covers only `/MK /CA`.
- A field whose widgets carry no `/T` of their own is invisible to the
  scaffold, and a correct full-name key for it is refused as unknown. This
  predates R-03.
- No form in the wild corpus has two same-named dropdowns, so the
  `(widget n)` key in `choice_exports` is exercised only by the constructed
  test.
- Captions and `--hide-buttons` keep partial names: F9/row 35.
