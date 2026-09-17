# The verify gates — what each reads, what fails, and why

Contents: the always-on gates · the leak scan · what `--translations`
adds (placement, canonical text layer, chrome and caption width,
identifiers, override markers) · `/Opt` export parity · document metadata
· shaped scripts · flags.

`verify.py` runs after every build; exit 0 means every gate passed. The
gates check the **file** — structure, placement, the text layer. None of
them can read: a plausible wrong term passes every one, which is why the
visual pass and the reviewer checklist exist. `python3 scripts/verify.py
original.pdf out.pdf --fill-text "…" --source-words-from segments.json
--translations translations.json`.

## Always on

| Gate | Fails when |
|---|---|
| field parity | the set of (fully-qualified name, type) differs from the original; extra fields only with `--allow-extra-prefix` |
| fill round-trip | a text value in the target script, or a checkbox, does not survive save and reopen (SKIPped when the PDF has no fields) |
| ink density | a page's dark-pixel ratio against the original leaves `[--min-ink, 3×]`; SKIPped when the original has negligible ink |
| text layer | a page has visible ink or an image but no extractable text: a scan, out of scope |
| invisible text | stripping a page changes under 3% of its text-span pixels: an OCR layer over a scan, or text under an image — a refusal, not a fix |
| leak scan | untranslated running text in the source script (below) |
| unshaped Arabic | a page whose Arabic letters are all isolated presentation forms was drawn letter by letter |
| conjunct shaping | an embedded face used on a page that draws Devanagari, Bengali, Tamil, Khmer or Myanmar does not lose glyphs when its probe cluster (क्षत्रिय, 8 → 4) is rendered through the Story engine: no usable GSUB, so every conjunct drawn with it is broken. A face without the probe glyphs is REVIEW (cannot attest; `prepare_font` adds them). Thai, Lao and Hebrew niqqud are REVIEW, never PASS |
| kinsoku | REVIEW, never FAIL: a drawn line of CJK text begins with a character JIS X 4051 / JLREQ forbids at line start (closing brackets, hyphens, dividing punctuation, middle dots, full stops, commas, iteration marks, the prolonged sound mark, small kana; half-width forms included) or ends with an opening bracket. The set includes the small kana counters ゎ ゕ ゖ ヮ ヵ ヶ and the half-width prolonged sound mark ｰ (U+FF70), which some layout engines allow at line start; a REVIEW on one of them is that known difference, not a defect. Lines are grouped into stacks by geometry — one under another, up to about two and a half times the line height (three times the font size) — so a stack's first line is never a line-start violation and its last never a line-end one; a single-character line (ー for "none", a bracket after a field) and a bullet (・ ･) that begins two or more lines are values, not breaks. The Story engine never does this to a merge; a target split by hand across source lines does, and a form label can look the same — hence REVIEW. Horizontal text only; prefix and postfix abbreviations (￥ ％ °) are not covered |
| han-forms | on a page that draws CJK text, every embedded face with a font program is rendered off that program and compared pixel for pixel with the Noto reference of `lang`'s convention (ja → Noto Sans JP; zh, zh-Hans, zh-CN, zh-SG → Noto Sans SC) and with the other convention's, both instanced at the face's OS/2 weight. Only the faces that drew CJK glyphs on the page are judged; a face embedded but unused — the source's face `strip_text` leaves behind — neither fails nor attests. A drawing face that carries no probes, or is not an embedded program, is cannot-attest for that page even when another drawing face passes. PASS: ≤ 0.02 against its own reference and ≥ 0.10 against the other on at least two of 直 骨 海; FAIL: the reverse — the face draws the other region's forms. REVIEW, never a guess: no `lang`; a mapping `lang` that is not a language tag (a display name such as `Japanese`); a non-CJK `/Lang` with no mapping `lang` (the original's, never updated); zh-Hant, ko (no reference measured); a face without the probe glyphs (cannot attest; `prepare_font` adds them); a face that differs from both references on 東, which is the same in both conventions (not a Noto family — no nearer-reference guess); reference faces not found (`--reference-fonts DIR`, default `tests/fonts/`); an inconclusive spread. Silent when the mapping's `lang` is a well-formed tag of a non-CJK language: the page's CJK is then a leak, and those gates own it |
| `/Opt` export parity | the export half of a choice entry differs from the original's, in value or order |
| canonical text layer | the output reports NBSP, soft hyphen, U+2010/U+2011, a CJK compatibility ideograph or a Latin ligature (U+FB00–FB06, U+007F) that is in neither the original nor the mapping (`/ToUnicode` drift) |

## The leak scan

The scan follows the **source document's script**, detected from its
text layer and printed (`leak scan: source script CJK; output script
Latin`). When the output is in another script, surviving runs of the
source script are the leaks: three or more consecutive words, or six or
more characters of a spaceless script (CJK, Thai, Khmer…), FAIL; shorter
leftovers are REVIEW, because official form names (Schedule C, Form W-2),
statutes and proper nouns are supposed to survive translation intact.
When both sides share a space-delimited script (EN→ES/FR/DE, RU→UK) the
scan uses *this document's own* source words, harvested from the original
automatically; `--source-words-from segments.json` is still accepted and
preferred when you pass it. Expect a few false positives (proper nouns,
words spelled the same in both languages) and allowlist them
deliberately: a multi-word entry (`--allow "Riverside Elementary School"`)
matches that run as a unit and nothing else, and the original's `/Title`
quoted as a unit — the compliance notice names the form — is kept, never
counted (kept runs are printed as a note). A longer run that merely
contains either is still a leak. When both sides share a spaceless family
(ZH↔JA) and the mapping's `lang` names a Han convention, gate 21
`leak-cjk` judges every drawn line by the characters that cannot belong
to the target — kana in a Chinese target, Han outside its repertoire
(cp932 for Japanese, GB 2312 for Simplified, Big5 for Traditional
Chinese), NFKC-folded first because a source's ToUnicode drift travels
through an authored mapping. Six or more in a line FAIL (an echoed,
untranslated sentence carries nine to fifty-six); one to five REVIEW (a name
in kana, a rare character — `--allow` the name). The source's convention
is read the same way and only measured pairs are judged; a Traditional
Chinese source into Japanese is not separable by repertoire and keeps the
one REVIEW line, as does a job with no `lang`. The tell cannot see a line
of Han both languages share (住所氏名, 令和七年, 个人所得税): such a line is
PASS for the tell and the PASS line says so — `--translations` and the
visual pass remain the check for those, and `leak-scan` records SKIP
`judged by leak-cjk`, never PASS, on such a job. A CJK ↔ CJK job whose tell finds nothing therefore no longer trips
`--fail-on-review` on the old spaceless REVIEW (v54 exited 1 there); only what the tell sees can. Measured:
`docs/BRIEF-cjk-leak-tell.md`.

## What `--translations translations.json` adds

**Placement.** Every authored non-passthrough **target** (length ≥ 2) must
appear **verbatim** in the output text layer, apart from wrapping
whitespace — a stripped file or a failed write fails here. Missing targets
are listed. Empty and whitespace-only targets fail and are named. This
does not judge whether the wording is the right term.

**Canonical text layer.** The comparison is verbatim because retypeset
canonicalizes the text layer. MuPDF builds an embedded font's `/ToUnicode`
by reverse-mapping its cmap, so the space glyph comes back as NBSP, the
hyphen as U+00AD or U+2010, and common kanji as CJK Compatibility
Ideographs (立 as U+F9F7): the page looks perfect while the words in it
cannot be searched, copied or matched. After saving, retypeset rewrites
`/ToUnicode` for the glyphs it placed to the code points you authored, and
the always-on gate FAILs any of those characters that are in neither the
original nor your mapping.

The Story engine shapes Latin too. HarfBuzz applies `liga`/`clig`, so a
merged paragraph or an inline-markup line draws "oficina" with the fi
glyph; MuPDF honours neither `font-variant-ligatures` nor
`font-feature-settings`, so the substitution cannot be switched off from
the CSS. retypeset reads the ligatures out of the font's GSUB table — the
subset that `prepare_font` builds keeps the substitution but drops
U+FB01 from the cmap, which is why cmap cannot find them — and maps each
ligature glyph to its component code points, so the layer says "oficina".
Nothing is done to the font file itself.

**Pushbutton chrome and caption width.** Captions live in `/MK /CA` and
draw on top of the page; `get_text()` still sees them. Either rewrite them
in place with `--captions` at strip time (field count stays exact), or put
the caption in `skip` and leave the button as UI chrome. If the original
caption is still in the output and you did neither, verify fails and lists
it. Do not hide a button and draw a second widget. Captions must **fit the
widget rect**: the gate FAILs if Helvetica `text_length` of the output
`/CA` is wider than the button minus a 2 pt pad each side. Prefer short
chrome (`Print` / `OK`) over a sentence in a tiny button.

**Write/find/say identifiers.** Quoted strings and `Form` / `Schedule` /
`Attachment` / `Exhibit` names from the original page must still appear in
the output text layer. Missing ones FAIL and are listed. If you meant to
translate a span, list it in `allow_translate` and record why in NOTES
(scripts do not read NOTES). URLs and emails are reported, not failed.

**Override markers.** An override replaces its whole span, so its parts
must still carry the source segment's list marker and tail (`d.`, `$`).
The gate needs `segments.json` beside `translations.json` or `--segments`,
and SKIPs rather than fails without one.

**Document metadata.** `/Lang` must match the mapping's `lang`; a
translated `/Title` and translated outline titles must be in the output;
the orphaned `/StructTreeRoot` must be gone. No `lang` in the mapping is a
REVIEW line, not a failure.

**Shaped marks.** Every target whose script needs shaping (Arabic family,
Indic, Thai, Lao, Khmer, Myanmar, Tibetan) must appear in an `/ActualText`
span; retypeset marks every Story-engine run that way, so a shaped target
without one was drawn glyph by glyph.

**Conjunct shaping** (always on, gate 18). The shaped-marks gate proves
who drew the run; this one proves the face can form conjuncts at all. A
broken conjunct leaves no code-point tell (the shaper writes glyph ids),
but the glyph *count* moves: a cluster string rendered glyph by glyph and
again through the Story engine off the same face loses glyphs when the
face's GSUB works (Devanagari क्षत्रिय 8 → 4, Bengali ক্ষ 3 → 1, Tamil
க்ஷ 3 → 1, Khmer ខ្មែរ 5 → 4, Myanmar သင်္ဘော 7 → 5; Noto faces). verify
extracts every embedded font program on a page that draws one of those
scripts and runs that probe off it, once per (script, face) — every
face on the page that covers the probe, not only the one that drew the
run, so an embedded-but-unused broken face also fails; both arms
must name the same face, because `insert_text` without `fontname=` falls
back to Helvetica and looks exactly like an unshaped run. No loss is a
FAIL — every conjunct drawn with that face is broken; do not ship. A
face that lacks the probe glyphs is REVIEW (cannot attest): rebuild the
subset with `prepare_font`, which adds them. Scripts with no count tell —
Thai, Lao, Hebrew niqqud (marks stack; Thai sara am even adds a glyph) —
are REVIEW, never PASS: a rendered sample checked by a reader is the
check. Conjunct scripts with no measured probe (Gujarati, Telugu, …) are
REVIEW until `shaping_probe.PROBES` gains a measured row. Arabic stays
with the unshaped-Arabic gate; there, shaping *adds* glyphs.

## `/Opt` export parity

Checked always, like field parity: the export half of every dropdown entry
must be byte-identical to the original's, in the same order. Translate the
display half (`references/widget-text.md`), never the export — the export
is what the form submits.

## As a library

`pdf_translate.verify.run_verify(...)` takes the same arguments as the
CLI, prints nothing, and returns a `VerifyVerdict`: `exit_code` and
`gates`, one `GateResult(name, status, message)` per PASS/FAIL/REVIEW/SKIP
line the CLI would print, same status, same order. Names are the closed
list `verify.GATE_NAMES`: field-parity, opt-export-parity, fill-roundtrip,
extractable-text, ink-ratio, visible-text, canonical-text,
arabic-letterforms, conjunct-shaping, kinsoku, han-forms, leak-scan, leak-cjk, leak-running,
leak-isolated, empty-targets, placement, shaped-actualtext,
button-captions, caption-width, override-markers, metadata,
metadata-lang, scaled-runs, identifiers. A gate that prints nothing for a
job — no fields, no Arabic, no `--translations` — records nothing, so an
`exit_code` of 1 always has at least one FAIL entry to explain it — unless
`fail_on_review` is true in the report, which is the other way a run exits 1.

Each `GateResult` carries `findings`, a tuple of `Finding(page, where,
text)`: the page (1-based, or `None` for document-level gates), the thing
the finding names (a field, a font's PostScript name, a script, `lang`, a
`U+XXXX` code point, a `0.85x` scale) and the run, caption, token or
detail, untruncated — the console prints the first ten to thirty, the
verdict keeps them all. `verify.py … --report PATH` writes
`verdict.to_dict()` as JSON (`schema` 1, the skill `version`, both paths,
`exit_code`, `gates`); `pipeline.py rebuild` writes it to
`<work>/verify_report.json`. The report is written whole or not at all —
a temp file beside the path, moved into place — and any report from an
earlier run at that path is removed before the gates run, so a report that
exists describes the last run; a refused write is printed and does not
change the exit code. Best effort: when the directory itself cannot be
written (a read-only mount), neither the removal nor the write can happen,
the console says the file there does not describe this run, and a consumer
should treat the report as absent. `--fail-on-review` (CLI) or
`fail_on_review=True` (library) turns a run with REVIEW lines and no FAIL
into exit 1, for pipelines with nobody to read the REVIEW. Both are off by
default. A consumer removes four REVIEWs on its own: always pass `lang` in the mapping
(`metadata-lang`, and `han-forms` "no lang"), build faces with `prepare_font`,
which adds the probe glyphs gates 18 and 20 need (`conjunct-shaping` and
`han-forms` "cannot attest"), set Japanese and Chinese in Noto Sans JP / SC and
ship the two reference faces (`reference_fonts=DIR`; `han-forms` "no reference"),
and never split a target by hand across source lines — declare a merge
(`kinsoku`).

| gate | `where` | `text` |
|---|---|---|
| field-parity | `missing` / `type-mismatch` / `unexpected-extra` | the field name |
| opt-export-parity | the field name | `old -> new` |
| fill-roundtrip | the field name | what did not survive save and reopen |
| extractable-text, ink-ratio, visible-text, arabic-letterforms | `page` | the detail (`PASS ink ratio 1.05`, `images=1, ink=200 px`, …) |
| canonical-text | `U+XXXX` | the character name and count |
| conjunct-shaping | the face's PostScript name, or the script when it could not be judged | the probe line, or the reason |
| kinsoku | `line-start` / `line-end` | the drawn line |
| han-forms | the face's PostScript name (subset tag stripped); `lang`, `reference` or the convention code (`JP`, `SC`) when the face could not be judged | the PASS/FAIL line with the ratios, or the reason |
| leak-scan | `script` | the spaceless family source and output share (`CJK`) (REVIEW when the tell cannot run; SKIP `judged by leak-cjk` when it ran) |
| leak-cjk | `line` | the drawn line |
| leak-running | `run` | the phrase |
| leak-isolated | `token` | the token |
| empty-targets, placement, shaped-actualtext | `target` | the target string |
| button-captions, caption-width | the field name | the caption |
| override-markers | the override's `contains` | the missing marker or tail |
| metadata | `lang` / `title` / `outline` / `struct-tree` | the detail |
| metadata-lang | `lang` | `translations.json has no "lang"` |
| scaled-runs | the ratio, `0.85x` | the run's key |
| identifiers | `identifier` | the span |

`page` is 1-based where the gate knows the page and `None` otherwise.

## Flags

`--fill-text` (a value in the target script for the round-trip),
`--allow WORD,"Multi Word Name"` (leak-scan allowlist; a phrase matches a
whole run), `--source-words-from segments.json`, `--translations
translations.json`, `--segments segments.json`, `--allow-extra-prefix`,
`--min-ink`, `--report verify_report.json`, `--fail-on-review`, `--reference-fonts DIR` (the
`NotoSansJP-VF.ttf` and `NotoSansSC-VF.ttf` faces gate 20 compares against; default `tests/fonts/`
of a checkout — an installed package has none, so a service passes its own; with
`--fail-on-review`, a CJK job exits 1 until they are shipped). Omit
`--translations`: the always-on gates run unchanged.
