# Wild corpus — analysis, 2 September 2026 (evening)

What the seventeen real documents in `SOURCES.md` said when the shipped
`strip_text` and `extract_segments` ran over them, one subprocess each, no
translation (`probe.py`; the regenerable table is `RESULTS.md`). Lane B row
P1 of the 2 September review. Interpreter `pdf-translate/.venv/bin/python`
3.14.6, PyMuPDF 1.28.2, pikepdf 10.12.0, on the macOS box.

Contents

1. The verdicts were right
2. Row 21 — `right-aligned` proposes running text
3. Row 22 — merge candidates carry no `kind`
4. Lane B row P6 — warnings do not scale
5. Hypotheses answered, and not
6. Smaller observations
7. What to run next

## 1. The verdicts were right

| Measure | Value |
|---|---|
| Files / pages | 17 / 449 |
| Verdicts | 17 × `translate`; 0 refusals, 0 crashes, 0 timeouts |
| Hybrid-XFA forms (AcroForm + `/XFA`) | 8 (W-9, W-4, FL-100, FL-300, SF-15, G-28, I-864, N-400) |
| Forms carrying `/Perms /UR3` | 10 |
| Forms carrying document JavaScript | 10 |
| Segments / unique cores | 60,670 / 25,948 |
| Widget-text scaffold entries (tooltips, options, values) | 1,413 |
| Strip / extract wall clock, all files | 19.7 s / 57.2 s |
| Slowest file | the 126-page IRS booklet, 37 s end to end |

Every verdict is defensible: all seventeen are born-digital, so none
should refuse. Nothing in the set exercises the refusal paths (scans, OCR
layers); the corpus in `pdf-translate/corpus/` already does.

**Strip left no page text anywhere.** Six stripped files still return
characters from `page.get_text()`; deleting every annotation on a copy
drops each of them to zero, so what remains is appearance text: pushbutton
captions (`Print this form`, `Save this form`, `Clear this form`, `Reset
Form`, and on the Judicial Council forms a caption per related-form link —
`FL-160`, `FL-305`, `Attachment 9b.`), checkbox values (`Off`), and on FDA
3500 page 7 a read-only text field carrying 790 characters of
instructions. Strip's own gate (re-read without annotation appearances)
agrees. Widgets survive strip in every file (count identical before and
after).

**Page 1 before and after strip, all seventeen, by eye** (contact sheets in
`work/renders/`): rules, boxes, coloured bands, seals, barcodes, the
photographs on the Medicare cover and the compass on the IRS cover all
stay; every glyph goes. The eight hybrid-XFA forms render their AcroForm
layer complete once the XFA layer is removed. No Acrobat is on this
machine, so whether Acrobat's XFA rendering differed from the AcroForm
layer is still unmeasured — the same limit the 1 September audit recorded.

## 2. Row 21 — `right-aligned` proposes running text

`right_alignment_warnings` flags segments that share a right edge (1.5 pt
buckets) while their left edges spread more than 4 pt. On real documents
that is the shape of justified paragraphs with indented first lines,
hanging-indent lists and tables of contents far more often than of label
columns:

| File | Groups | Segments proposed for `right` |
|---|---|---|
| IRS 1040 instructions (126 pp, three justified columns) | 612 | 7,135 |
| GDPR (88 pp, two justified columns) | 109 | 1,938 |
| Medicare & You | 312 | 762 |
| arXiv paper | 37 | 517 |
| all seventeen | **1,485** | **11,507** |

Samples of what is proposed: GDPR page 1, twelve body lines at x0 94 ending
at 529.87 — every line of a justified column; the IRS booklet's table of
contents (`What's New . . .`, `Do You Have To File? . . .`); W-9 page 1,
`Enter your TIN in the appropriate box` paired with `Date`. The true class
is there too and is small: FL-100's caption stack (`RESPONDENT:` /
`PETITIONER:`; `BRANCH NAME:` / `CITY AND ZIP CODE:` / `STREET ADDRESS:` /
`MAILING ADDRESS:`), short labels tucked against a rule, each with its own
left edge.

Discriminators tried on the corpus (`TOL` 1.5 pt):

| Rule | Groups kept | Segments kept |
|---|---|---|
| today | 1,485 | 11,507 |
| A: fewer than 60% of members share one left edge | 860 | 2,617 |
| B: A, and no member wider than 200 pt | 375 | 948 |
| C: A, and no member is part of a merge candidate | 410 | 954 |
| D: B and C | 294 | 702 |

D keeps the FL-100 captions and still keeps hanging-indent body lines on
W-9 page 4 and I-9 page 1. No single threshold does it; the rule has to
say what a label column is. The brief (`dev/goals/21-right-aligned-on-text.md`)
asks for fixtures that fail first — a justified paragraph, a hanging
indent — and the corpus count after, recorded not targeted.

The skill text makes this matter: step 3 tells the author to put those
cores in `right`. On body text that is wrong twice over — the lines are a
merge, and right-anchoring them would move them.

## 3. Row 22 — merge candidates carry no `kind`

Every warning kind names itself except the paragraph proposals from
`merge_candidate_warnings`, which carry `page`, `ids`, `why`, `lines` and
no `kind`. `propose_merges` therefore selects on `kind in (None,
'narrow-column')`, `extract_segments.main` prints them untagged, and the
first version of `probe.py`, keyed on `kind`, counted 2,484 of them as
something else until a person read one (GDPR 528, Medicare 976, IRS
booklet 365, arXiv 76, W-9 48). Paragraph mode itself is alive and well —
those counts are the proof. The brief
(`dev/goals/22-merge-candidate-kind.md`) is fifteen minutes plus a
backward-compatibility test for stale work directories.

## 4. Lane B row P6 — warnings do not scale

`extract_segments.main` printed 6,191 warning lines over the seventeen
files, one per finding:

| Kind | Count | What the skill asks of the author |
|---|---|---|
| merge-candidate | 2,484 | accept in bulk via `propose-merges`, delete sibling-list entries |
| write-find-say | 1,691 | "halt-and-confirm, not optional color" — each one |
| right-aligned | 1,485 | list the cores in `right` (row 21) |
| narrow-column | 431 | one decision per stack |
| image-region | 76 | look at each |
| inner-gap | 24 | one `overrides` entry each |

The only kind that genuinely needs an entry each is the smallest. The
IRS booklet alone prints 1,093 write/find/say hits (every `Form 1040`,
`Schedule A`, `Pub. 501`): they stay verbatim by default and the
identifier gate fails a dropped one, so the right instruction is "confirm
the list", not 1,093 halts. The brief (`dev/goals/P6-warnings-at-scale.md`)
is a per-kind digest before the list, skill text that says what each kind
wants, and one sentence about data values (below). No kind is silenced.

## 5. Hypotheses answered, and not

From the review's §4:

- **H-B hybrid XFA — answered for the AcroForm layer.** Eight forms;
  after XFA removal the AcroForm layer renders complete on page 1 and
  every widget survives. Not answered: whether Acrobat drew the XFA layer
  differently (no Acrobat here). The DS-11 fetched is the State
  Department's flat AcroForm variant (`ds11_pdf.pdf`, 84 fields, no XFA),
  and Canada's dynamic-XFA IMM forms could not be fetched, so the
  "Please wait" class is still unmeasured.
- **H-D scale — answered.** 126 pages in 37 s; 449 pages in 77 s total.
  The invisible-text oracle is not the bottleneck it was feared to be.
- **H-A visible annotation text — unmeasured.** None of the seventeen
  files carries a single non-widget annotation. Government forms use
  widgets for everything, including link-buttons to other forms.
- **H-C real fonts — narrower than feared.** Only Type1, TrueType and
  Type0 in all seventeen files (the GDPR is 207 Type0 fonts; the booklet
  617 Type0 and 198 Type1). No Type3, no outlined text.
- **H-E compaction — untouched**; canary run 2's job.

## 6. Smaller observations

- **Barcode fields are data.** I-864 and N-400 carry a visible text field
  `PDF417BarCode1[0]` whose `/V` is the 2D-barcode payload
  (`I-864|08/24/26|1`). The widget-text scaffold lists its `value` and
  `default` with `null` targets, and `null` refuses the build; the channel
  accepts an identity target, but nothing tells the author to use one.
  No file has a *hidden* widget carrying a value. Folded into P6.
- **Chrome at scale.** A Judicial Council form carries ten to twenty
  pushbutton captions (form-number links plus Print/Save/Clear). The
  chrome gate will want a `skip` or `--captions` decision for each on a
  real translation; form-number captions are also write/find/say
  identifiers. Unmeasured here because nothing was translated — the
  natural next probe (§7).
- **Widget text is big.** 1,413 scaffold entries across the corpus — 427
  on N-400 alone, mostly tooltips that repeat the page text. Authoring
  them is real work the four-page fixture never showed.
- **A blank page is not a refusal.** Medicare & You page 127 has no text,
  no image, no drawing and no ink; extract produced no segments and did
  not refuse. Correct.
- **`/Perms /UR3` and document JavaScript** are the norm on US government
  forms (10 of 17). Strip deletes `/Perms` and reports it; field names
  are preserved, so the scripts keep working. As designed.

## 7. What to run next

Not rows yet:

1. **One real form end to end.** Author a mapping for FL-100 or the W-9
   (not FL-150) and run retypeset and verify: that measures the chrome
   gate, the caption-width gate and the widget-text channel at real scale,
   which this probe could not. Canary run 2 could use a real form as its
   fixture for exactly this reason.
2. **A dynamic-XFA file** (Canada IMM 5257, fetched by hand in a browser)
   to see whether the "Please wait" placeholder page is refused or
   translated.
3. **A file with FreeText or Stamp annotations** for H-A; none was found
   in the wild set.

---

## 8. After row 21 — `right-aligned` proposes only tucked columns

The rule that shipped: a group sharing a right edge with spread left
edges is proposed only when at least half its members sit within **one
em** of something to their right — a rule, a widget, or the next segment
on the row. Measured first (§2 above gave the shape; this gave the
signal): at one em the proposals fall from 1,485 groups to 158 and every
caption stack on FL-100 survives; at two ems the IRS booklet's column
gutters come back (354 groups). `RESULTS.md` and `results.json` are
regenerated with the shipped extractor.

| File | Groups before | after | Segments before | after |
|---|---|---|---|---|
| IRS 1040 instructions | 612 | 61 | 7,135 | 388 |
| GDPR | 109 | 7 | 1,938 | 14 |
| Medicare & You | 312 | 12 | 762 | 28 |
| Judicial Council FL-100 | 17 | 9 | 39 | 21 |
| all seventeen | **1,485** | **158** | **11,507** | **642** |

Every other warning kind, every segment count and every verdict is
unchanged on all seventeen files; extraction time is 57.8 s against 57.2 s
(the obstacle pass reads widgets and drawings once per page).

## 9. After row 23 — the body offset is measured, not computed

Every marker segment with a body (952 across the seventeen files) now
carries `body_dx`, read from the source's characters. Its median
difference from Helvetica's advance for `marker + gap` — the drift
retypeset shipped until now — is 0.00 pt on the Helvetica-metric forms
(W-9, W-4, SF-15, FDA 3500), +1.27 on Medicare & You, +2.22 on I-9,
+2.42 on 1040-ES, +3.88 on the IRS booklet, +4.92 on FL-300 and −1.79 on
the GDPR. Counts and verdicts unchanged; extraction 57.8 → 61.7 s.

## 10. The corpus caught a reproducibility wart in strip's report

Re-running the probe on 3 September (row 26 had touched the extractor)
showed one difference against the committed `results.json`: the two
page-17 `form_xobjects_stripped` entries of the IRS 1040 instructions,
`/I2` and `/I3`, swapped. Same page, same block counts, same depth; every
verdict, segment count and warning count on all seventeen files
identical.

The cause is not this corpus and not the extractor. `strip_xobjects()`
walked `dict(res['/XObject']).items()`, and pikepdf's dictionary
iteration runs through a hash-randomized structure:

```bash
for seed in 0 1 12345; do PYTHONHASHSEED=$seed pdf-translate/.venv/bin/python -c "
import pikepdf; pdf=pikepdf.open('dev/wild/files/irs-i1040gi.pdf')
print(list(dict(pdf.pages[17].obj['/Resources']['/XObject']).keys()))"; done
```

prints `['/I1','/I2','/I3']`, `['/I1','/I3','/I2']`, `['/I1','/I2','/I3']`.

Two consequences, both diagnostic-only — the same set of objects is
stripped either way and no output byte moves. The report's order floated,
and where two names point at one object, `seen` skips whichever is
reached second, so the recorded **name** floated too. On a constructed
page with four names and an alias, five seeds produced five different
orders and one of them reported the alias `/Xd` instead of `/Xa`.

The traversal is now sorted by name, which pins both halves;
`StripReportOrderTests` runs strip in subprocesses under four
`PYTHONHASHSEED` values and asserts one identical report (it fails on
every seed with the sort removed). The baseline in `results.json` and
`RESULTS.md` was regenerated from the deterministic run — that is the
only reason those files change in this commit, apart from timings.
