# R-33: `field_fonts` keeps a field's colour and size — 25 September 2026

**Assignment.** R-33 is the next of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-33 in
`docs/REVIEW-2026-09-24.md`, and the assigned behaviour reads
"`field_fonts` keeps a field's colour and size".

R-33 is a drawing item, so its bar is the shared one plus Rule 1 with a
rendered pixel comparison. It ships as v70, on #39's branch.

## The defect

`field_fonts` points every text and choice field's `/DA` (default
appearance) at the embedded field font. It did that by writing a new string,
`/TransFF <size> Tf 0 g`:
- **The colour became black.** Every field lost whatever colour its form
  set.
- **The size was read only from a `/DA` that begins with the font
  operator.** `1 0 0 rg /Helv 14 Tf` came out at size 0, which a viewer
  auto-sizes.
- **A widget with no `/DA` of its own** is drawn with its parent field's or
  the form's. It was given size 0 and black.

## Reproduced before building

Run on the 17 wild PDFs at v69, `field_fonts` changed 162 fields. Each
field's effective `/DA` was compared before and after.

| form | text and choice fields | changed | how |
|---|---:|---:|---|
| IRS 1040-ES | 110 | 110 | navy (`0.000 0.000 0.502 rg`) to black |
| IRS W-4 | 43 | 43 | navy to black |
| USCIS G-28 | 78 | 1 | red (`1.000 0.000 0.000 rg`) to black |
| USCIS I-864 | 178 | 3 | red to black |
| USCIS N-400 | 242 | 3 | red to black |
| USCIS I-9 | 122 | 2 | `/HeBo 10 Tf 0 g`, inherited, to `/TransFF 0 Tf 0 g` |

The first five rows are the review's 153 navy and 7 red fields. The I-9
widgets have no `/DA` of their own, so their size was lost on a real form,
not only on the review's constructed case. No other wild form changed.

**Rendered.** A constructed form holds four filled text fields. Under
NeedAppearances, MuPDF draws each value from its `/DA`. The table gives the
most frequent ink colour and the height of the ink, at 144 dpi:

| field | its `/DA` | source | v69 after `field_fonts` |
|---|---|---|---|
| navy | `/Helv 14 Tf 0 0 0.5 rg` | (0,0,127), 21 px | **(0,0,0)**, 21 px |
| red_first | `1 0 0 rg /Helv 14 Tf` | (255,0,0), 21 px | **(0,0,0), 38 px** |
| kid | none; its parent's is `/Helv 14 Tf 0 0.5 0 rg` | (0,127,0), 21 px | **(0,0,0), 38 px** |
| plain | `/Helv 12 Tf 0 g` | (0,0,0), 18 px | (0,0,0), 18 px |

## The change

`pdf_translate/field_fonts.py`:
- **`field_da(da, name)` swaps only the font name** in front of the `Tf`
  operator. The size, the colour and every other operator stay, where the
  form put them.
- **With no `Tf`,** the font goes first at size 0.
- **With no fill colour,** ` 0 g` is appended, which is what a viewer
  assumes anyway.
- **`inherited_da(obj, form_da)`** takes a widget's own `/DA`, else its
  nearest ancestor's, else the form's default. So a widget without one gets
  the appearance it was actually drawn with.
- **The form-level `/DA`** goes through the same function.

**Unchanged output for the common cases.** `/Helv 12 Tf 0 g`, `/Helv 12 Tf`
and a missing `/DA` still give `/TransFF 12 Tf 0 g`, `/TransFF 12 Tf 0 g` and
`/TransFF 0 Tf 0 g`, as before. On all 13 wild PDFs that have a form, the
form-level `/DA` comes out byte-identical to v69's.

**Docs:**
- `references/fonts.md`, the field-input paragraph;
- SKILL.md, the field step;
- `field_fonts`' docstring.

**Records:** a `docs/DECISIONS.md` row, and the quick-wins row in
`docs/REQUESTS-from-product.md`. The version goes from 69 to 70.

## Red, then green

`tests.test_pipeline.FieldAppearanceKeptTests` builds the four-field form
above and runs `field_fonts`. It then checks:
- **Each field's exact `/DA`:**
  - navy: `/TransFF 14 Tf 0 0 0.5 rg`;
  - red_first: `1 0 0 rg /TransFF 14 Tf`;
  - the kid's parent and the kid: `/TransFF 14 Tf 0 0.5 0 rg`;
  - plain: `/TransFF 12 Tf 0 g`;
  - the form: `/TransFF 0 Tf 0 g`.
- **The rendering:** each field's ink colour and height must equal the
  source form's.

**Red.** On `d1f8a30` (v69), with this test copied in, the kid got
`/TransFF 0 Tf 0 g`, and the rendering differs as in the table above.
**Green.** On the branch all four fields render in the source's colour and
at its height.
With the other field-font and choice-field classes, 13 tests pass.

**The wild forms after the fix:** 0 of the 1,210 text and choice fields
change colour or size.

## Suite

These are CI's commands, run on macOS on the final code, which includes the
Rule 1 fixes below:

| step | result |
|---|---|
| suite | 739 tests: 1 failure, 1 expected failure |
| canary | 15, OK |
| repository | 6, OK |
| eval fixtures | exit 0 |

- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.
- Before the Rule 1 fixes, the same run gave 737 tests with the same
  outcome.

**The app's route** calls no `field_fonts`, so v70 changes nothing there
today.

## Rule 1

An independent pass on a different model (Sonnet) worked from `git archive`
copies of `d1f8a30` (v69) and `7a61a15` (v70). It used its own forms, its
own parser for the effective `/DA`, and its own renders. Verdict: PASS, with
two minor findings, both now fixed, and two notes.

**What held:**
- **The wild forms.** Its own count of the 1,210 text and choice fields on
  the 13 wild forms with an AcroForm:
  - v69 changes 162: colour on 110 + 43 + 1 + 3 + 3, and size on 2 on the
    I-9;
  - v70 changes 0;
  - the form-level `/DA` is byte-identical on all 13.
- **Rendered on real fields.** It filled a navy IRS 1040-ES field and a red
  G-28 signature field by setting `/V` directly, then rendered them at
  144 dpi.
  - On v70 each draws the source's ink, (0,0,128) and (255,0,0), at the same
    height.
  - On v69 each draws the same glyphs, the same pixel count, in (0,0,0).
- **A 10-field constructed form.** It held navy, colour-first, inherited,
  CMYK and combo-box fields, a field whose `/DA` comes from the form, and a
  field whose `/FT` is on its parent. All keep their size and colour on v70.
  The checkbox and radio fields are left alone on both trees.
- **Tests.** On v69, only `FieldAppearanceKeptTests` fails; on v70 all 13
  pass. `test_verify_report` confirms v70 in all five places.

**The findings, both minor and both latent.** No wild form triggers either.
- **A chain of direct objects was cut short.** `inherited_da` keyed its
  cycle guard on `objgen`, which is `(0, 0)` for every direct (non-indirect)
  object. So a direct widget under a direct parent fell back to the form's
  `/DA` instead of the parent's. Only indirect objects are tracked now: they
  are the only ones that can form a cycle, and a real indirect cycle still
  ends at the form's `/DA`.
- **Only the first `Tf` was swapped.** In a `/DA` with two `Tf` operators the
  second kept `/Helv`, and a viewer draws with the last one. Every `Tf` is
  swapped now.
- `test_a_chain_of_direct_objects_is_followed` and
  `test_every_font_operator_is_swapped` failed on `7a61a15` and pass now.
  The wild forms still change 0 of 1,210 fields.

**The notes:**
- **The test's colour helper** takes the most frequent colour in a field. On
  a busy real form, the field's border can outnumber the ink. It is sound on
  the test's blank page, and its docstring now says so.
- **A field whose `/FT` is set only two or more levels up is skipped
  entirely,** on v69 as on v70, because the type lookup looks one level up.
  This was reproduced here: a text field typed only on its grandparent gets
  no `/DA` and stays on `/Helv`. It predates R-33 and no wild form is built
  that way, so it is filed as a proposal (the last REQUESTS row).
