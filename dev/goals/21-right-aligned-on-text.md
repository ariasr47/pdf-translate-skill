# Objective: the `right-aligned` warning must not propose running text

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/extract_segments.py` (`right_alignment_warnings`), the
> `right-aligned` paragraphs in `SKILL.md` step 3 and
> `references/translations-format.md`, and `dev/wild/ANALYSIS.md` §2. Do
> not touch merge candidates (row 22) or build a verify gate. Not FL-150.

---

## 1. Compass (not done)

`right_alignment_warnings` proposes `right` for any group of segments on a
page that share a right edge (1.5 pt buckets) while their left edges
spread more than 4 pt. That is the shape of a right-aligned label column —
and also the shape of every justified paragraph with an indented first
line, every hanging-indent list, and every table of contents. On the
seventeen real documents in `dev/wild/`:

| Measure | Value |
|---|---|
| `right-aligned` groups | 1,485 |
| segments proposed for `right` | 11,507 |
| on the 126-page IRS booklet alone | 612 groups, 7,135 segments |
| on the 88-page GDPR | 109 groups, 1,938 segments |

The skill then tells the author to "put those cores in `right` or a
longer translation grows past the rule they sit against". Followed on a
justified paragraph, that right-anchors body lines — and the lines were
going to be merged into a paragraph anyway. The true class is small and
easy to see on the same corpus: FL-100's caption stack (`RESPONDENT:` /
`PETITIONER:`, `BRANCH NAME:` / `CITY AND ZIP CODE:` / `STREET ADDRESS:`),
tucked against a rule with each label's own width.

Discriminators measured on the corpus (`dev/wild/ANALYSIS.md` §2):

| Rule | Groups kept | Segments kept |
|---|---|---|
| today | 1,485 | 11,507 |
| A: fewer than 60% of members share one left edge | 860 | 2,617 |
| B: A, and no member wider than 200 pt | 375 | 948 |
| C: A, and no member belongs to a merge candidate | 410 | 954 |
| D: B and C | 294 | 702 |

Even D keeps hanging-indent body lines (W-9 page 4, I-9 page 1) and does
keep the FL-100 captions. So the fix is not one threshold; it is a rule
that says what a label column *is*: short members, each with its own
left edge, in a tight stack, not members of a column of running text.

## 2. Done when — closed bar

1. **Justified text does not propose `right`.** Constructed LTR fixture:
   a justified three-line paragraph (PyMuPDF `insert_textbox` with
   `TEXT_ALIGN_JUSTIFY`) whose first line is indented, plus a
   hanging-indent bullet list. `extract_segments` emits **zero**
   `right-aligned` warnings for those segments.
2. **Label columns still do.** The existing `build_right_aligned_pdf`
   fixture (`Total` / `Subtotal amount` / `Tax`) keeps its warning, and
   `test_extractor_proposes_right_aligned_cores` stays green unchanged.
3. **Measured on the wild corpus.** Re-run `dev/wild/probe.py` and put the
   new group and segment counts in this brief's closing note, with the
   FL-100 caption stack still proposed and the IRS booklet down by an
   order of magnitude. `RESULTS.md` is regenerated; the PDFs are not
   committed.
4. **The docs say what the warning is for.** `extract_segments.py` header,
   `SKILL.md` step 3 and `translations-format.md`: a label column tucked
   against a rule; running text is a merge, never a `right` entry.
5. **No regressions.** Full unittest + corpus green. `metadata.version`
   bumped.

## 3. Not done when

- Auto-realigning anything, or a verify gate for right-anchored runs
- Changing what `right` does in retypeset
- Using merge-candidate membership as the only test (row 22 changes that
  schema; keep this geometry-only and independent of it)
- Tuning a single threshold until the corpus number looks nice with no
  fixture that fails first

## 4. Method

Build the two fixtures; confirm the justified paragraph fires today (it
will); write the rule; confirm the label column still fires. Then the
corpus number, recorded, not targeted.

## 5. Invariants

Provider-neutral. Geometry-only. Warnings propose, authors decide. No
glossary.

## 6. Proof

Zero warnings on justified text and hanging indents; the label fixture
unchanged; the wild-corpus counts before and after; full unittest + corpus.
