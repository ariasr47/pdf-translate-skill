# pdf-translate: research, audit findings, and what closing the gates taught us

Written 1–2 September 2026. Covers the deep review of the `pdf-translate` skill
(commit `ad52f1d` plus the then-uncommitted gates 08–10), the research into
comparable tools and professional practice, the twelve defects verified by
probing the shipped scripts, and everything discovered while closing program
gates 13–16 and row 11 afterwards. The interactive versions of the audit and the
tracker live beside this file as `audit-2026-09-01.html` and `checklist.html`.

> **Superseded, evening of 2 September:** the canary ran, rows 18–20 came
> out of it, 18 is closed, and the roadmap was re-groomed into two lanes —
> see §15 and `REVIEW-2026-09-02.md`. The paragraph below is the state at
> midday.

**Status, end of 2 September 2026.** Every defect in section 4 is fixed, and
every row of the roadmap in `checklist.html` is closed — program rows 12 and
17, findings H1, H2, H4/H5, M1–M5, the translation-quality layer
(`qa_check.py`, `references/review.md`, `references/compliance.md`, the
expansion table, the per-job glossary input), paragraph mode with page
slices and a bilingual reading copy, the three small guards, and the
packaging work. The suite is 154 tests, about 25 seconds, green on this
machine. One item remains and it is not a code change: nobody has run the
canary (`dev/canary/`).

Contents

1. Verdict
2. Method and environment
3. Scorecard, then and now
4. Verified defects, with status
5. Research: comparable tools and skills
6. Research: translation practice
7. Research: PDF practice
8. Gaps against best practice
9. Skill-authoring quality
10. Discoveries made while closing gates 13–16 and row 11
11. Commits since the audit
12. What is next
13. Working notes for this machine
14. Sources

---

## 1. Verdict

The skill is unusually disciplined for an agent skill. It edits PDFs at the
content-stream level (strip the text, re-typeset at the original baselines),
treats field identity as a hard invariant, refuses rather than guesses, ships
constructed-fixture tests that import the shipped scripts, keeps a corpus with
recorded verdicts, and has bakeoff evidence that its prose moved model behaviour
across three vendors. Nothing else surveyed preserves fillable forms at all.

At the time of the audit the gates still passed wrong output in classes the
skill claimed to cover: Arabic and Devanagari came out unshaped while the docs
said shaping worked; OCR'd scans, the exact input the skill told users to
produce, double-printed and passed every gate; any non-Latin source language
made the leak gate fail correct output; rotated labels were laid flat; nested
XObject text survived stripping; widget text was mis-extracted or never
translated.

Strategically it is a form localizer rather than the document translator its
description promises: the per-line, hand-declared-merge model does not scale to
manuals, and there is no translation-quality layer (no linguistic QA checks, no
reviser step, no way to accept an issuer's glossary), which is where BabelDOC,
DeepL and professional practice invest most.

Since then gates 13–16 and row 11 closed all three critical findings and one
high one, the installed plugin copy was synced, and the suite grew from 57 to
84 tests. Seven findings remain open and are re-probed below.

## 2. Method and environment

- Read every file in `pdf-translate/` (skill, references, scripts, tests,
  corpus, goals, program, recommendations, handover), the root notes, the
  bakeoff harness and results, and one competing model's run notes.
- Ran the suite: 57 tests in 14 s at the start; 84 tests in about 23 s now.
  Python 3.14.0, PyMuPDF 1.28.0, pikepdf 10.12.0, fontTools 4.63.0, Windows 11.
- Fifteen probes drove the shipped `strip_text`, `extract_segments`,
  `retypeset`, `prepare_font` and `verify` on constructed PDFs: page rotation,
  rotated text lines, widget tooltips and options, nested and inherited
  XObjects, metadata and tags, encryption, italic and right alignment, an OCR'd
  scan, Arabic, Hebrew, Thai and Devanagari through TextWriter and through the
  Story engine, a Japanese-to-English job through every verify mode, a code
  point round-trip study with full and subset fonts, usage-rights signatures,
  and the text layers of four real FL-150 outputs.
- Compared the installed plugin copy with the repository (it was v1).
- Limits: no Acrobat on the machine, so the usage-rights banner and
  NeedAppearances rendering are inferred from structure; glyph-form judgments
  rest on code points and renders, not on a native reader; Windows system
  fonts (Arial, Nirmala UI, Leelawadee UI) plus the repo's Noto Sans JP were
  used.

## 3. Scorecard, then and now

| Dimension | 1 Sep | 2 Sep | Why |
|---|---|---|---|
| Architecture and invariants | Strong | Strong | Content-stream strip, retypeset at original baselines, field names, types and rects untouched, no redaction, glyf-only fonts with a rasterization assert. |
| Structural gates | Good | Good | Thirteen verify gates plus a strip gate and two extract refusals; still blind to rotated lines, widget text, code-point drift and metadata. |
| Tests and corpus | Strong | Strong | 84 constructed-fixture tests import the shipped scripts; 15-file corpus with verdicts. No CI; evals reference fixtures that are not in the repo. |
| Skill text | Good | Good | Precise and honest; repetitive (write/find/say in three places); description summarizes mechanics. |
| Script reach | Weak | Good | Arabic and Indic are shaped through the Story engine (gate 16); the leak scan follows the source script (gate 15). Vertical CJK still out. |
| Document reach | Fair | Fair | Forms excellent; nested XObjects stripped and OCR layers refused (13, 14). Rotated text lines, widget text, outlines, metadata, signatures, encryption open. |
| Long documents | Weak | Weak | No paragraph mode; merges declared by hand line by line. |
| Translation QA | Missing | Missing | No LQA checks, no reviser step, no job-level glossary. |
| Delivery and compliance | Weak | Weak | No informational-only notice for court forms, no certification template, metadata still `en-US`. |
| Packaging and hygiene | Fair | Fair | Frontmatter valid and now versioned; installed copy synced. Dev material still inside the skill dir; no license; no CI. |

## 4. Verified defects, with status

Severity reflects silent-pass risk: how confidently the pipeline shipped wrong
output. "Fixed" means the probe that produced the finding now shows the refusal
or the correct output.

### C1. Arabic and Devanagari drawn without shaping. Fixed, gate 16 (`66790fa`)

Every single-line run went through `TextWriter.append`, which does no
complex-script shaping. Arabic letters came out as isolated presentation forms
(`FE8D FEDD FEB1…`, unjoined); Devanagari conjuncts were drawn as consonant plus
halant. The Story engine (`insert_htmlbox`, HarfBuzz), which merges already
used, produced `FEDF FEB3 FEFC` (initial and medial forms, lam-alef ligature)
and correct conjuncts. `fonts.md`, the edge-case notes and goal 04 all said
shaping worked; the RTL tests only checked the ActualText round-trip.

Fix: runs whose target script needs shaping (Arabic family, Indic, Thai, Lao,
Khmer, Myanmar, Tibetan) are placed with `insert_htmlbox` one line tall, rect
top 0.8 × size above the baseline (measured, font-independent), the engine's
scale feeding the 0.7× gate, logical string in `/ActualText`. Hebrew stays on
TextWriter (direction only). Verify gate 12 reads the drawn glyph forms and
fails Arabic that came out as isolated forms. Pipeline renders were checked by
eye; the FL-150 rebuild text layer is identical on all four pages.

**15 September update.** The by-eye check now has a mechanical successor
for conjunct-forming scripts: gate 18 (`pdf_translate/shaping_probe.py`)
renders a known cluster off the embedded face glyph by glyph and through
the Story engine and fails a face whose count does not drop (Devanagari
क्षत्रिय 8 → 4; Bengali, Tamil, Khmer, Myanmar likewise). Thai, Lao and
Hebrew niqqud have no count tell and stay a human check. Evidence and the
red run: `docs/reviews/2026-09-15-conjunct-shaping-gate.md`.

### C2. OCR'd scans pass every gate and ship double-printed. Fixed, gate 14 (`b504da2`)

An OCR'd PDF is an image plus an invisible text layer (render mode 3). The
text was extractable, so the image-only refusal never fired; strip removed the
invisible text; retypeset drew the translation over the scanned pixels; the
ink ratio (2.13) stayed under the 3.0 ceiling. This was the input the skill's
own advice ("OCR first") led users to produce.

Fix: `strip_text.invisible_text_pages()` strips a temporary copy and compares
72-dpi renders; if removing the text changes under 3% of the page's text-span
area, the text was invisible and extract and verify refuse. Measured margins:
visible pages 0.25–0.38, the OCR layer 0.00; extract on the four-page FL-150
takes 0.31 s including the oracle. "OCR first" was removed from every doc and
message: scans are out of scope with or without an OCR layer.

### C3. Leak gate inverted for every non-Latin source. Fixed, gate 15 (`6613f35`)

The leak scan looked for Latin words. For a Japanese, Chinese, Arabic, Russian
or Greek source, the translation was what it matched: a correct JA→EN output
failed "untranslated running text". `--source-words-from` harvested Latin
tokens, found none, and fell back to the same regex. Conversely, untranslated
Japanese in an Arabic target matched nothing and passed.

Fix: a Unicode range table detects the source script from the original's text
layer; the target script is judged from output lines that do not also occur
in the source (verbatim or as the same bag of letters, because a large
leftover would otherwise disguise the job). Different scripts: runs of the
source script in the output are leaks (three or more words, or six or more
characters of a spaceless script). Same space-delimited script: the document's
own words, harvested automatically. Shared spaceless family (ZH↔JA): one REVIEW
line, no gate. Latin-source behaviour is byte-for-byte unchanged; two real
FL-150 outputs reproduce the recorded results exactly.

### H1. Rotated text lines re-typeset horizontally. Fixed 2 Sep

**Closed.** Segments carry `line["dir"]`; a rotated line is never gap-split;
retypeset writes the run horizontally and morphs it about its own origin, so
origin, bbox and direction come back identical to the source. The width
budget runs along the direction. A rotated run whose target needs shaping is
refused rather than drawn flat, because the Story engine places shaped text
upright. Corpus `rotated_text.pdf`.

The extractor keeps origin, bbox and size but not the line direction. A label
written at 90° is placed flat at its origin. Page-level `/Rotate` is fine
(probe P1: origins identical in unrotated space). Fix: record `line["dir"]`,
place with `TextWriter.write_text(morph=…)`, add a `rotated_text.pdf` corpus
fixture. Re-checked 2 Sep: source direction (0,−1) still comes out (1,0).

### H2. Widget appearance text leaks into extraction; tooltips and options never translated. Fixed 2 Sep (goal 17)

**Closed.** Extraction reads `page.get_displaylist(annots=False)`, so field
values and the current dropdown selection never become cores.
`extract_segments` writes a `widget_text.json` scaffold and
`strip_text --widget-text` applies it; a null target is a refusal, not a
skip. An `/Opt` entry becomes `[export, display]` and a spec that would
translate a choice `/V` is refused. An always-on verify gate compares export
values against the original.

`get_text()` includes annotation appearance streams. A text field's default
value and a combo box's current value appear in `to_translate.json` as page
text, get translated, and are drawn beneath the widget, whose appearance still
shows the source value. Meanwhile `/TU` tooltips, the other `/Opt` choices and
`/DV` defaults are never extracted. Fix path verified: extract from
`page.get_displaylist(annots=False).get_textpage()` (yields only page text),
then a widget-text channel next to `--captions` with an `/Opt` parity gate.

### H3. Nested Form XObject and inherited-resource text survived strip. Fixed, gate 13 (`2175a0b`)

The walker read the page's own `/Resources`, one level deep. Text two XObjects
deep, or on a page whose resources were inherited from the `/Pages` node, was
left in place while the report said `form_xobjects_stripped: []`; extraction
saw that text, so the translation was drawn on top of the surviving source.
Fix: recursive walk with a visited set, `/Parent` inheritance, and a gate: the
stripped file is re-read with annotation appearances excluded and any page
text left is a FAIL that deletes the file. Corpus `nested_xobject.pdf`; the
corpus harness strips every `translate` fixture.

### H4. Text-layer code-point drift. Fixed 2 Sep

**Closed.** After saving, retypeset rewrites `/ToUnicode` for the glyphs it
placed to the code points the author wrote — a CMap is executed in order, so
an appended `bfchar` block overrides an earlier `bfrange`, and where two
authored characters share a glyph the lower code point wins (the canonical
one in every drift pair). An always-on gate fails any drift-prone character
that is in neither the original nor the mapping. The placement gate now
compares verbatim; the fold survives only where the *source* side can drift
and we cannot rewrite it (identifier spans read out of the original, and
whitespace-only authored values).

MuPDF builds each embedded font's `ToUnicode` by reverse-mapping the font's
cmap. When several code points share a glyph, the wrong one can be reported:
spaces as U+00A0, hyphens as U+00AD, common kanji as CJK Compatibility
Ideographs (立→U+F9F7, 年→U+F98E, 行→U+FA08, 見→U+FA0A, 金→U+F90A, 料→U+F9BE).
With the full Noto Sans JP font, `verify --translations` failed a correct
申立人 sentence. Subsetting masks it (the four FL-150 outputs contain zero
drifted characters), but `field_fonts.py` embeds the full font and the docs
allow skipping subsetting. The soft-hyphen case surfaced again on 2 Sep in the
repo's own tests (see section 10) and is folded now; the root cause is not
fixed. Fix: post-process `ToUnicode` with pikepdf to the authored code points
or emit `/ActualText` per run, and add a canonical-text-layer gate.

### M1. Right-aligned text re-anchored left. Fixed 2 Sep

**Closed.** A `right` list anchors a core on the original bbox right edge,
and the extractor proposes candidates (`right-aligned` warnings: segments
sharing a right edge while their left edges differ). Nothing realigns
itself.

Only `center` exists; a right-aligned label grows rightward past its original
right edge (`Total` at 540 → `Gesamt` ending at 555.3). Fix: a `right` list,
proposed by the extractor from aligned right edges.

### M2. Italic, serif and mixed inline styles dropped. Fixed 2 Sep

**Closed.** `fonts` takes `regular`, `bold`, `italic` and `bold_italic`, each
falling back to the nearest role the mapping named; pass-through runs pick
the matching base-14 face. A single-line target may carry inline
`<b>`/`<i>`/`<strong>`/`<em>` and is placed through the Story engine. The
markup pattern is deliberately narrow, so a translation that really contains
`<` is left alone.

The extractor records `italic`, but retypeset has only regular and bold slots
and one family for the whole document; Times Italic becomes upright Arial. Fix:
font roles per family from span flags, inline `<b>`/`<i>` for single lines.

### M3. Encryption dropped; usage-rights signature left invalid. Fixed 2 Sep

**Closed.** strip reports encryption, permission bits and `/Perms`; always
deletes `/Perms` and says what was there; flags a certified source
(`/DocMDP`) so the delivery can state the translation is not certified; and
takes `--keep-encryption`, which re-applies the permission bits with an empty
owner password and reads back what the writer actually granted. Signature
fields are left alone — removing a widget would break field parity.

An encrypted source comes out unencrypted with permissions removed and no
message. FL-150 carries `/Perms /UR3` (Adobe Reader extensions signature); the
outputs still carry it although the content changed, which triggers Reader's
"extended features are no longer available" banner. No bakeoff run was opened
in Acrobat. Fix: report at recon, delete `/Perms` at strip, optional
re-encryption, DocMDP warning.

### M4. Output metadata still describes the source. Fixed 2 Sep

**Closed.** `segments.json` carries a `document` block (source `/Lang`,
`/Title`, outline titles, tagged state); the title and every outline title
are cores. retypeset writes the mapping's `lang` to `/Lang` and
`dc:language`, translates `/Title` and the outline, and removes the orphaned
`/StructTreeRoot` with `/MarkInfo /Marked false`. A verify gate fails a stale
one and REVIEWs a mapping with no `lang`; the placement gate skips
document-only cores, which are metadata rather than page text.

Every FL-150 output keeps `/Lang en-US`, the English `/Title`, and an orphaned
`/StructTreeRoot` with `/MarkInfo /Marked true`. Fix: set `/Lang` and XMP
language, treat `/Title` as a core, translate outline titles, remove the
orphaned tree until tags can be rebuilt.

### M5. No per-character glyph coverage check. Fixed 2 Sep

**Closed.** Every character of every placed run is checked against the exact
font object that will draw it — translated parts, override parts, list
markers, dot-leader tails, pass-through Helvetica runs and merge HTML. A miss
FAILs and names the code points; nothing is saved.

MuPDF substitutes its fallback font mid-string when the chosen font lacks a
glyph, and draws a box when the fallback lacks it too; retypeset returned 0.
`prepare_font`'s rasterization assert samples at most twelve characters. Fix:
`font.has_glyph` for every character of every run against the exact font.

### L1. The installed plugin copy was v1. Fixed 2 Sep

The `anthropic-skills:pdf-translate` copy had nine failure modes against
twelve, no `pipeline.py`, none of gates 01–16. It was replaced with the
gate-16 tree (dev material excluded), the manifest description was refreshed,
`metadata.version: "16"` was added to the frontmatter, and the v1 copy was
backed up. The installed copy passes the full suite and is diff-identical to
the repo outside dev material.

### L2. Documentation drift and unrunnable evals. Fixed 2 Sep

Failure-mode counts agree. `evals/make_fixtures.py` builds the
`permission_form.pdf` and `garden_flyer.pdf` the eval prompts referenced but
the repo never had — generated rather than committed, so the content of each
eval is readable as code — and the expected outputs now describe what the
current gates actually check. The frontmatter description keeps its triggers
and drops the pipeline mechanics; the "YAML block is optional" paragraph
moved to the README.

## 5. Research: comparable tools and skills

**BabelDOC / PDFMathTranslate (pdf2zh).** The reference implementation for
layout-preserving PDF translation. Parses pages into a paragraph-level
intermediate representation (DocLayout-YOLO layout analysis), masks formulas as
placeholders, reflows translations with an iterative scale search (decrement
0.05 or 0.10 until the paragraph fits), extracts a document-level glossary and
injects it into the prompt for consistency, emits mono and dual (bilingual)
output, detects scanned pages and offers an OCR masking workaround, accepts
glossary CSVs and a translation cache. Reported BIoU 50.0% on a 200-page
benchmark versus DeepL's 19.8%; 1.63 s per page. The paper does not address
AcroForms, links, bookmarks or tagged PDF. Limitations it states: reliance on
upstream layout detection, local misalignment on dense pages, vertical-script
transitions.

**Other agent skills.** haoyiyin/pdf-translate and yinsang0910-star are thin
wrappers over pdf2zh (mono and dual output, no forms, "use OCR first").
wshuyi/translate-pdf-skill extracts spans with PyMuPDF, translates each, and
removes the original text with a transparent redaction, which deletes any
overlapping widget, the exact failure this skill's design guards against.
Overdue-Lin rebuilds the page in LaTeX from an image (nothing pixel-identical
survives). deusyu/translate-book converts to Markdown via Calibre, splits into
chunks, runs parallel subagents with a frequency-ranked term table and
neighbour context, and validates merges by SHA-256 manifests; no layout.

**DeepL document translation.** Segments pages into semantic elements and
measures an average bounding-box overlap ratio; ranks constraints (page
boundary, element position, relative font sizes, absolute consistency) and
tunes font size per element in half-point steps; PDFs are captured through an
OCR-style pipeline. Forms are not addressed.

**Summary.** Nobody else preserves form fields, and nobody else has per-job
gates. Everybody else has paragraphs, glossaries and bilingual output. The two
halves are complementary and the second half is tooling this repo can add
without touching its invariants.

## 6. Research: translation practice

- **ISO 17100** requires translation with the translator's own check, revision
  by a second person who compares source and target, and optional review and
  proofreading. The translator's self-check does not replace revision.
- **Judicial Council of California Translation Protocol (July 2016).**
  Translators should be ATA-certified with a legal specialization or
  equivalently qualified; the reviewer "must compare the source text with the
  translation"; standardized glossaries are "critical"; automatic machine
  translation "should not be used as the sole mechanism" and, where used,
  "clear disclaimer language must be provided" in the user's language; plain
  language; formatting may include a bilingual layout. California courts state
  that official filings must be in English and that translated forms are for
  reference.
- **NCSC, Guide to Translation of Legal Materials (2011).** Keep form numbers,
  court names, statute citations and proper nouns in English; label translated
  forms as informational only; translate, edit by a second translator, then
  proofread; develop glossaries; keep the original layout.
- **USCIS, 8 CFR 103.2(b)(3).** Foreign-language documents need a full English
  translation plus the translator's certification of completeness, accuracy
  and competence. No licensing or notarization is required.
- **Quality estimation.** GEMBA-MQM shows an LLM with a fixed few-shot,
  language-agnostic prompt can mark MQM error spans without a reference
  translation (96.5% system-level accuracy on WMT 2023). That is the shape of a
  provider-neutral reviser pass: a prompt template and a schema, run by any
  model, attached as `review.json`.
- **Automatic QA tools (Xbench, Verifika).** Standard checks: untranslated
  segments (target identical to source), numeric mismatches, inconsistent
  translations of the same source, term mismatches, unpaired brackets, tag and
  placeholder parity, double spaces, punctuation. None of this needs a
  glossary shipped with the skill.
- **Text expansion (W3C, IBM figures).** English strings under ten characters
  expand 200–300%, 11–20 characters 180–200%, only above 70 characters about
  130%; Chinese and Korean often contract; Thai needs about 150% of the
  vertical space. The skill's "EN→DE grows about 30%" is the paragraph figure
  and is wrong for the labels forms are made of.
- **Agentic translation (Andrew Ng's translation-agent).** Translate, reflect
  with concrete suggestions, improve: the reflection step is the reviser step
  in prompt form.

## 7. Research: PDF practice

- **Fonts.** MuPDF renders subsetted CFF/OTF CJK as nothing; only glyf-flavored
  TrueType is reliable, which the skill already enforces with a rasterization
  assert. OpenType `fsType` embedding bits (installable 0, editable 8, preview
  4, restricted 2, no-subsetting 0x0100) govern whether a font may be embedded
  and subset at all; the skill embeds whatever TTF it is given and its tests
  use Arial.
- **ToUnicode.** MuPDF generates ToUnicode by reverse-mapping the font cmap;
  glyphs reachable from several code points can be reported as the wrong one
  (finding H4). Subsetting hides it only when the duplicate code points are
  not in the subset.
- **ActualText.** The right place for the logical string of a shaped or
  bidirectional run. The Story engine draws into a Form XObject and appends
  only `q /fzFrmN Do Q` to the page, so the marked-content span must wrap that
  invocation, and MuPDF honours it through the `Do`.
- **Complex scripts.** PyMuPDF's own recipes say `insert_text`, `insert_textbox`
  and TextWriter must not be used for Arabic, Persian, Hebrew, Devanagari and
  similar; the Story engine (HarfBuzz) is the supported path.
- **Rotation.** PyMuPDF extraction coordinates and insertion coordinates are
  both in unrotated page space, so page rotation is safe; text-line direction
  is a separate property that must be carried explicitly.
- **Accessibility.** WCAG PDF16 expects `/Lang` in the catalog to match the
  document language; a structure tree whose tags point at removed content is
  worse than none.
- **Signatures and encryption.** Any content edit invalidates approval,
  certification (DocMDP) and usage-rights (UR3) signatures; Reader shows a
  banner for the last. Re-saving with PyMuPDF's `ez_save` drops encryption.
- **Tagged PDF and inheritance.** pikepdf (QPDF) pushes inherited page
  attributes onto pages both on open and on save; fixtures that need true
  inheritance have to be built with PyMuPDF xref surgery.

## 8. Gaps against best practice

1. **A translation-quality layer.** Linguistic QA checks on
   `translations.json` (numbers and dates, identical-to-source for
   non-identifier cores, variant consistency, unpaired brackets and quotes,
   punctuation parity, length ratios against the expansion table); a reviser
   step as a required deliverable with an optional MQM-typology judge template
   and `review.json`; job-level `glossary.csv` input with a consistency gate,
   never shipped with the skill. The program's "no glossary" rule is right
   about shipping dictionaries and wrong to treat every quality mechanism as
   one.
2. **Compliance and delivery.** A target-language "informational only; file
   the English form" notice for court and government classes; a certification
   statement template a human signs; a sentence in SKILL.md that the output is
   a working copy, not a certified translation.
3. **Long documents and paragraphs.** Block-based merge proposals the author
   accepts in bulk, the existing scale search, page partitioning, bilingual
   output. This is what would make the "manuals and brochures" claim true.
4. **Expansion guidance.** Replace the 30% figure with the length-dependent
   table and make the extractor's length warnings use it.
5. **Untranslatable surfaces.** Raster images with text and outlined text
   (list image regions for review); outline titles, page labels, annotation
   contents, document metadata; choice-field `/DA` in `field_fonts.py`;
   vertical CJK; Thai line breaking inside merges.
6. **Fonts.** Read `OS/2.fsType` in `prepare_font.py` and refuse restricted
   fonts.

## 9. Skill-authoring quality

- Frontmatter is valid against the agentskills.io specification (kebab-case
  name matching the directory, 804 of 1,024 description characters, only
  allowed keys) and now carries `metadata.version`. `license` and
  `compatibility` are still missing; there is no LICENSE file in the repo.
- The description mixes triggers with mechanics ("strip-and-retypeset
  pipeline (never overlay, never redaction)"). Anthropic's guide wants what
  plus when; the writing-skills tests found workflow summaries in descriptions
  get followed instead of the body. Keep the triggers, move the mechanics.
- The body (about 340 lines, 2,500 words) is loaded whole. Write/find/say is
  explained in step 3, step 6, `translations-format.md` and `failure-modes.md`;
  the repo's own rule is "one home per fact". *Partly addressed:* the
  reviewer checklist in `references/review.md` is copyable and is now a
  required deliverable.
- Degrees of freedom are well chosen: exact commands for the fragile pipeline,
  judgment for language. Delivery is the one place a template would help.
  *Fixed:* `references/review.md` and `references/compliance.md` are the
  delivery templates.
- The goal loop (constructed fixture, failing test, one gate per sitting) is
  close to TDD for process documentation and is the repo's strongest asset.
  The bakeoff harness exists in three duplicated copies plus a damaged zip.
- Tests depended on system fonts and, until 2 Sep, on a gitignored font (see
  section 10). *Fixed:* `tools/fetch_test_fonts.py` pulls OFL Noto faces into
  `tests/fonts/` and the helpers prefer them, and GitHub Actions runs the
  suite on Linux and Windows.
- `goals/`, three session prompts and four HTML explainers shipped inside the
  skill directory; `requirements.txt` had no upper bounds. *Fixed:* dev
  material moved to a repo-level `dev/`, and the requirement ranges are
  bounded above.

## 10. Discoveries made while closing gates 13–16 and row 11

Each of these was found by the program's own rule: a gate that passes bad
output, or fails good output, is the bug.

- **PyMuPDF's `show_pdf_page` nests two XObject levels per shown page.** The
  old one-level walker therefore missed even a single letterhead. (Gate 13)
- **pikepdf pushes inherited page attributes onto pages on open and on
  save.** An inherited-resources fixture cannot be built with pikepdf; PyMuPDF
  xref surgery is needed. The `/Parent` walk in strip is a safety net; the
  leftover-text gate is the proof. (Gate 13)
- **`insert_htmlbox` positions a single line deterministically.** With
  `line-height: 1` the baseline sits 0.8 × size below the rect top for every
  font tried, and the run starts at the rect's left edge; a rect 1.25 × size
  tall wraps only once the engine has scaled below the 0.7× gate. (Gate 16)
- **`/ActualText` never reached Story output.** The wrapper looked for
  `BT…ET`, but Story output is an XObject invocation; RTL merges carried no
  logical text. The span now wraps the invocation stream. (Gate 16)
- **MuPDF's CSS parser eats backslashes.** A Windows font path in `@font-face`
  silently fell back to a font without the target script; merges were affected
  too. CSS gets POSIX paths now. (Gate 16)
- **The text layer of shaped Indic runs is glyph ids**, not code points, so a
  glyph-form gate from code points is only possible for Arabic (presentation
  forms); for Indic, `/ActualText` is the reliable layer. (Gate 16)
- **The suite was green because of a gitignored font.** `find_test_font()`
  preferred a Noto file under `work/`; anywhere else it fell back to Arial,
  whose cmap makes MuPDF report a soft hyphen for `W-2`, and three placement
  and identifier tests failed. Finding H4 in the repo's own tests. The fold
  now covers U+00AD and system fonts come first. (Sync, `80e40b5`, `c96319e`)
- **The fill round-trip gate failed every form without a text field.** A
  checkbox-only fixture built for row 11 exposed it: "no text widget to fill"
  was treated as a failure, so consent sheets with only tick boxes could never
  pass verify. (Row 11, `ce5fa85`)
- **The suite doubled in wall-clock** (14 s to about 23 s) because the
  invisible-text oracle strips and renders inside both extract and verify.
  Acceptable, and a reason to set up CI.

## 11. Commits since the audit

| Commit | What |
|---|---|
| `2175a0b` | Gates 08–13 and the any-PDF skill text |
| `b504da2` | Gate 14, OCR'd-scan refusal |
| `6613f35` | Gate 15, script-aware leak scan (committed by another session) |
| `13b04be` | Ignore the ChatGPT session prompt and bakeoff artifacts |
| `66790fa` | Gate 16, shaped scripts through the Story engine |
| `be1080a` | `metadata.version` in the frontmatter |
| `80e40b5` | Fold soft hyphens; test font no longer depends on a gitignored file |
| `c96319e` | Hyphen round-trip test accepts Arial's soft hyphen |
| `ce5fa85` | Row 11, override parts keep marker and tail; fill gate fixed for checkbox-only forms |
| `bf6103e` | Row 12, narrow-column warning; the skill-text leftovers |
| `c297ac2` | Goal 17, widget-text channel and `/Opt` parity gate (H2) |
| `9d162de` | Rotated lines keep their angle (H1); corpus `rotated_text.pdf` |
| `97716d6` | Canonical text layer, `/ToUnicode` rewritten to the authored code points (H4/H5) |
| `e8c63c5` | Per-character glyph coverage in retypeset (M5) |
| `94834aa` | Encryption, usage rights and DocMDP (M3) |
| `fe32df6` | Document metadata retargeted; orphaned structure tree removed (M4) |
| `23e9183` | Right alignment and the four font roles (M1/M2) |
| `e9ba43f` | Shaped-script leftovers: leaders on shaped labels, an `/ActualText` gate for Indic |
| `9d92bf4` | `qa_check.py`, the reviser step, compliance wording, the expansion table |
| `5726a8d` | Paragraph mode, page slices, bilingual reading copy |
| `c7f6cd4` | Three small guards: image regions, choice-field `/DA`, `OS/2.fsType` |
| `896f7d3` | Hygiene: dev material out of the skill, MIT licence, pinned ranges, CI |

## 12. What is next

The roadmap above is closed. What is left is one item and two standing
obligations.

1. **The canary has not been run.** `dev/canary/README.md` carries the
   fixtures command, the prompt and the five-axis rubric (identity record,
   lookup, identifiers kept, visual pass, honest delivery). One strong and
   one weak model, on a different day from any gate, with no winner written
   into `SKILL.md`.
2. **Re-sync the installed copy.** It matched the gate-16 tree; it is behind
   again. `metadata.version` is the tell.
3. **Do not invent the next program row.** Wait for a new silent-PASS class —
   gates green, output wrong — then one constructed fixture, one sitting.
   Still out of scope unless the user reverses it: a shipped glossary, OCR
   implementation, a semantic term checker, a winner in `SKILL.md`, FL-150
   as gold.

Two deviations from the roadmap as written, both deliberate:

- The audit proposed closing the Indic shaping hole with a **reference render
  comparison**. What shipped is a deterministic signal instead: retypeset
  marks every Story-engine run with `/ActualText`, so a shaping-script target
  that no mark carries was drawn glyph by glyph. Cheaper, and it cannot
  disagree with itself across renderers.
- The audit proposed **vendoring** an OFL font for CI. What shipped is
  `tools/fetch_test_fonts.py` plus a workflow that runs it: no binaries in
  the repository, and the licence stays with the upstream project. The URLs
  are branch-tip rather than commit pins, and the script says so rather than
  carrying a SHA nobody verified.

## 13. Working notes for this machine

- The interpreter is `py -3`; bare `python` is the Store alias.
- Printing CJK or Arabic from Python in a shell needs `PYTHONUTF8=1`.
- The suite: `py -3 -m unittest tests.test_pipeline tests.test_corpus_verdicts`
  from `pdf-translate/`.
- The installed skill copy lives under
  `%APPDATA%\Claude\local-agent-mode-sessions\skills-plugin\…\skills\pdf-translate`;
  re-sync it after each gate and refresh the manifest entry's description.
  Dev material now lives in `dev/`, outside the skill, so the copy is the
  whole of `pdf-translate/` minus `tests/fonts/*.ttf` and
  `evals/fixtures/`. `metadata.version` tells you when it lags.
- `work/` and `runs/` are ignored job artifacts; never let them decide a test.

## 14. Sources

- BabelDOC paper: https://arxiv.org/html/2605.10845v1
- BabelDOC CLI: https://github.com/funstory-ai/BabelDOC
- PDFMathTranslate-next: https://github.com/PDFMathTranslate/PDFMathTranslate-next
- Agent skills surveyed: https://github.com/haoyiyin/pdf-translate ,
  https://github.com/yinsang0910-star/pdf-translate-skill ,
  https://github.com/wshuyi/translate-pdf-skill ,
  https://github.com/Overdue-Lin/pdf-translate-skill ,
  https://github.com/deusyu/translate-book
- DeepL, improving document translation: https://www.deepl.com/en/blog/tech/improving-document-translation
- Agent Skills specification: https://agentskills.io/specification
- Anthropic skill authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- PyMuPDF TextWriter: https://pymupdf.readthedocs.io/en/latest/textwriter.html
- PyMuPDF text recipes (complex scripts): https://pymupdf.readthedocs.io/en/latest/recipes-text.html
- GEMBA-MQM: https://arxiv.org/abs/2310.13988
- ApSIC Xbench QA features: https://docs.xbench.net/user-guide/work-qa-features/
- Nimdzi on automatic translation QA: https://www.nimdzi.com/translation-quality-assurance-tools/
- ISO 17100:2015: https://www.iso.org/standard/59149.html
- Judicial Council of California Translation Protocol: https://courts.ca.gov/sites/default/files/courts/default/2024-12/lap-translation-protocol.pdf
- California Courts self-help (filings in English): https://selfhelp.courts.ca.gov/ask-interpreter
- NCSC, Guide to Translation of Legal Materials: https://niwaplibrary.wcl.american.edu/wp-content/uploads/Guide-to-Translation-of-Legal-Materials.pdf
- 8 CFR 103.2(b)(3): https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-103/subpart-A/section-103.2
- W3C, Text size in translation: https://www.w3.org/International/articles/article-text-size.en.html
- WCAG PDF16 (`/Lang`): https://www.w3.org/TR/WCAG20-TECHS/PDF16.html
- Fonts in PDF files (embedding, subsetting, fsType): https://www.prepressure.com/pdf/basics/fonts
- iText on PDF certification and DocMDP: https://itextpdf.com/blog/itext-news-technical-notes/attacks-pdf-certification-and-what-you-can-do-about-them
- andrewyng/translation-agent: https://github.com/andrewyng/translation-agent

## 15. Update, evening of 2 September 2026

Supersedes §12. The canary ran the same day on the two-page fixture with
Opus 5, Fable 5.1 and Haiku 4.5 (`dev/canary/runs/`): 5, 5 and 3 out of 5,
no structural escapes, three defects found by models rather than invented
— rows 18, 19 and 20 in `dev/goals/PROGRAM.md`. Row 18 (the `center`
example) closed in the evening; a fourth defect, the placement gate
failing a wrapped merge, was fixed the same day as the canary. The
installed copy is still behind (version 16 against 30).

The deep review in `REVIEW-2026-09-02.md` then re-groomed the roadmap: lane
A keeps the canary rule (19, 20, then canary run 2); lane B adds product
rows with the same discipline — a measured wild corpus of public PDFs,
plugin packaging (`claude plugin validate --strict` already passes a
root-as-plugin manifest in a scratch copy, and `claude --plugin-dir` lists
the skill from it at about 7,300 tokens on invoke), `SKILL.md` back under 500
lines, and an automated eval built on `claude plugin eval` with the
canary's `score.py` as grader. The hypotheses the wild corpus should test
(visible annotation text, hybrid XFA, real fonts, scale, compaction) are
listed there; none is a row until a real file shows it.
