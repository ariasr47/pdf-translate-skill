# Typography preservation — additive API design

20 September 2026 · **written design for operator review**

Rodrigo approved the additive approach. This document proposes its details;
they are not implemented or approved merely by being written here. No delivery
version, app adoption, B1 work or implementation plan is implied.

## Decision in one minute

Keep existing mappings and calls working. Add an explicitly selected typography
format that preserves source style runs and binds translated runs to exact
occurrences. Use separate serif/sans font-role sets and reuse the existing
placement machinery where it can satisfy these requirements. One mapping reader
feeds placement, verification, QA and review so none silently loses the new data.

The first supported scope is horizontal, single-baseline, selectable page text
with one source size/color per segment. Source and target runs in the first
scope use Latin, Japanese or Simplified Chinese text; other scripts require a
later independently verified extension. Regular, bold, italic and bold-italic
within supported lines are included.
Recognized unsupported constructs refuse in this mode. This is an initial
coverage boundary, **not a reduction of the product's typography requirement**:
unsupported documents remain ineligible for migration under that promise.

Same source page count, original page assignment and first baseline are required.
No line wrapping, new boxes, continuation pages or neighbor movement is added.
Exact source font-file reuse is unnecessary. Correct language and meaningful
emphasis still require a reader; a style reference is not a semantic proof.

## Evidence and scope

The [capability disposition](../../reviews/2026-09-20-typography-capability.md)
and its independently authored fixture establish the existing gap. At the app's
reported v54 pin `9675c6196c14eb2a2d37d34e371391eb1955a386`, main v56
`a5629fbd6bc084f9ab849ae3db74992c15807fcc` and open-PR v58
`1d4f9707c4d9934fbc88d8f25576ac304b9bb139`, mixed spans lose their boundaries and
font class while retaining only aggregate bold/italic booleans. Occurrence IDs
exist, but translation/override selectors cannot address them unambiguously.

The local v61 edits do not add typography capability. PRs #12/#13 remain open;
their result adapters are useful design references, not adopted product APIs.
The app reports five compatibility failures; resolving or reproducing those in
the app is not part of this design. Product source was not consulted.

No OCR, vertical text, synthetic font reconstruction, general font matching,
new renderer, public service controls or full document reflow is introduced.
Legacy functionality remains available with its existing, narrower assurances.

## 1. Public surface and compatibility

Proposed additions:

| Surface | Proposed behavior |
| --- | --- |
| `run_extract(src, outdir, *, typography=False, gap=12.0, pages=None)` | Opt-in extraction adds source-font observations, style runs and extraction binding to its files/result. Default output retains the legacy shape. |
| `extract_segments(...)`, extractor CLI and `pipeline init` | Expose the same opt-in as a keyword / `--typography`; no second extraction implementation. |
| `MAPPING_FORMATS` | Export an immutable tuple including `legacy` and `typography-1` only when the corresponding workflow is implemented and verified. Consumers check availability before using the new format. |
| `run_prepare_font(..., font_class=None, font_role=None)` / font preparation CLI | Typography jobs select `font_class` and `font_role` explicitly (`--font-class`, `--font-role`); the shared reader supplies the matching target charset. Legacy defaults remain. |
| `run_retypeset(..., original=None)`, `run_verify`, `run_qa`, `run_review`, their CLI paths and pipeline wrappers | Read the explicit mapping format through one shared parser. Legacy calls remain valid; `original=` is required only for a typography build and exposed as `--original` by its CLI. Typography verification requires its mapping and extraction data. |
| `run_verify(..., typography=False)` / verify `--typography` | Explicitly request typography attestation even when context is missing. A `typography-1` mapping also selects the check automatically. |
| `pipeline from-cores` | For opt-in extraction, scaffold occurrence entries with unauthored targets in `translations.json`; never flatten to a core-only map or overwrite an authored file implicitly. |

These names are proposals, not callable additions today. A plain mapping with
no `format` remains legacy. A new mapping has `format: "typography-1"` and uses
the distinct root shape below. An unknown format, malformed new-format field or
mixed legacy/new root is an input error, never a request to try legacy behavior.

**Old-reader boundary:** do not hide the new data in an optional field of an
otherwise usable legacy mapping. An old retypesetter must not successfully draw
flattened fallback text. The new format has no root `translations` or `fonts`,
which the inspected old retypesetters require before drawing. Older QA/review
code can still ignore unfamiliar inputs, so this is not a universal old-reader
protection: the app and skill must check `MAPPING_FORMATS` on their actual runtime
before invoking any stage. No compatibility is claimed for new-format jobs run
with an old runtime. That boundary is tested explicitly.

The shared parser yields normalized occurrence/run records for the existing
stages. A small `mapping.py` owns format dispatch, validation and iteration;
`typography.py` owns style observations/class resolution and identity calculations.
Extraction and placement retain their current responsibilities. QA and review
consume the normalized records rather than each developing another parser.
There is no new registry, external service or consumer-policy layer.

## 2. Extraction: preserve evidence before grouping loses it

In opt-in mode, keep the existing grouping geometry but retain the ordered raw
spans that contributed to each segment. Add `occurrence_id` and `style_runs` to
that segment. Each style run records:

- `run_id`, `font_id`, its exact text and half-open Unicode-codepoint offsets
  into the segment's exact `text`, plus its source bbox and baseline;
- observed font name/flags and available embedded-font metadata through
  `font_id`; resolved `class` (`serif`, `sans`, or `unknown`), `bold` and `italic`
  (boolean or unresolved), with the evidence used;
- original size/color. Differences within a segment are retained as evidence
  but are outside this first placement scope and produce a named refusal.

Do not normalize away whitespace, combine differently styled spans, strip list
markers from this source representation or infer a class from a fuzzy font-name
match. Adjacent spans may coalesce only when font/style/size/color and baseline
agree; offsets must reconstruct the exact source segment text. A style boundary
inside a combining/shaping cluster is unsupported, not a safe split point.

Classification uses exact supported standard-face identities or consistent,
supported embedded-font metadata. Missing, contradictory or unrecognized facts
remain unresolved; an unset PDF serif flag alone does not prove sans. Store the
observations even when classification fails. An optional, job-specific
`source_font_resolutions` entry may resolve an unknown font's class/weight/slant
by its exact font ID, with a required explanation. It cannot silently override
already resolved observations. Such resolutions are explicitly caller-authored
and appear as REVIEW information in both the build record and reader checklist.
The library does not call a model to classify fonts.

Source fonts identified as decorative, monospaced without a known requested
class, vertical or otherwise outside the supported classification stay
unsupported until correctly resolved; they are not automatically made sans.
Synthetic emphasis drawn outside ordinary font/style metadata is not attested
by metadata extraction. Visual inspection remains necessary to detect it.

Each `source_font_resolutions` item has exactly `font_id`, `class`, `bold`,
`italic` and nonempty `reason`. Class is `serif` or `sans`; flags are booleans.
Duplicate/foreign font IDs or conflicts with resolved evidence are errors.
Font IDs are document-local PDF font-object references, scoped by the source
digest. If a span cannot be associated with exactly one font object, record an
unresolved observation rather than choosing a same-name font. Named standard
faces still require an unambiguous source association.

## 3. Exact occurrence identity and stale-input refusal

`occurrence_id` can reuse the segment's sequential ID as `s2`; `run_id` is
scoped beneath it, such as `s2/r1`. These are **identities within one extraction**,
not permanent identifiers across re-extraction. Repeated identical text gets
distinct IDs even on the same page. The page/bbox remains descriptive data, not
a substring or nearest-coordinate fallback selector.

The extraction stores the original PDF's SHA-256 and an `extraction_id`: SHA-256
of a defined canonical JSON representation containing that source digest,
typography schema revision, effective extraction options and all occurrence,
geometry, font-observation and style-run records. Canonical JSON uses sorted
keys, compact separators, UTF-8 and finite numbers; hashing excludes the digest
field itself and machine paths. IDs are an input-consistency check, not proof
against a malicious author or a source-revision migration mechanism.

Each mapping carries that exact `extraction_id`. The reader recomputes it from
the extraction data and rejects mismatches. The supplied source PDF is checked
against the source digest wherever the stage takes it. `run_retypeset` additionally
receives a proposed keyword-only `original=` for typography jobs so it can make
that check before using the stripped document; omission is an input error in
this mode. Recompute the stripped document from that source within the approved
workflow. Before placement, require the stripped document's page count, boxes,
rotations and field identities to agree with the source/extraction. Those checks
do not prove every graphic came from the source: arbitrary stripped-file
provenance is not attested by the source hash. The trusted strip step and the
independent source/final visual comparison remain necessary.

Changing a source, grouping option, occurrence order, source run or style
observation requires re-extraction/re-authoring. An ID must resolve exactly once
in the bound extraction. Missing, duplicated, foreign and stale IDs fail before
placement. No searching by repeated core, substring or approximate bbox.

## 4. Mapping: translated order, explicit source-style association

The following JSON is an **illustrative shape**, not a real job or implemented
API. `example-extraction-digest` would be rejected by the proposed validator;
an actual file uses the digest emitted by extraction. The complete mapping must
contain every eligible visible occurrence, not just this example entry.

Required root keys are `format`, `extraction_id`, `lang`, `font_sets`, `targets`
and `document_targets`; optional `source_font_resolutions` and `allow_scale`
default to empty arrays. Reject other keys in this format. `lang` must be a
supported target tag; `extraction_id` is a 64-character lowercase SHA-256 hex
string. Each target has exactly `occurrence_id` and `runs`; each target run has
exactly `text` and `source_runs`. Font-role values are file-path strings.
`allow_scale` entries have an `occurrence_id` and nonempty `reason`; duplicate,
foreign or unauthored occurrence IDs are invalid. These exceptions retain the
existing below-floor opt-in behavior only for the named occurrence.

```json
{
  "format": "typography-1",
  "extraction_id": "example-extraction-digest",
  "lang": "es",
  "font_sets": {
    "sans": {
      "regular": "fonts/sans-regular.ttf",
      "bold": "fonts/sans-bold.ttf"
    }
  },
  "source_font_resolutions": [],
  "targets": [
    {
      "occurrence_id": "s2",
      "runs": [
        {"text": "AHORA ", "source_runs": ["s2/r1"]},
        {"text": "pague", "source_runs": ["s2/r0"]}
      ]
    }
  ],
  "document_targets": {}
}
```

Here the source is regular `Pay ` followed by bold `NOW`; the target deliberately
puts the emphasized word first. The author supplies natural target text in its
final order. Each run's class/bold/italic comes from its named source run(s), not
from a new free-form style declaration or character offsets copied to the target.
The library cannot decide whether `AHORA` is the correct semantic counterpart;
review must examine that association.

Rules:

- `targets` is an array so duplicate occurrence entries can be rejected rather
  than overwritten by object-key parsing. Reject duplicate JSON keys everywhere.
- Every included visible occurrence appears exactly once. Uniform occurrences
  also get a run entry; a core translation cache may suggest text but cannot
  replace occurrence-specific authoring. Repeated text never implicitly shares
  emphasis or target selection.
- `source_runs` is a nonempty array of IDs from this occurrence. A target run
  can combine multiple source runs only when their resolved class/emphasis
  agree. One source run can inform several target runs, supporting reordering
  and expansion. Differently styled sources require separate target runs.
- Every source run containing non-whitespace text must be represented by a
  nonempty target run. Whitespace-only source runs need not be represented.
  Added target spacing attaches to a neighboring represented run. Empty targets,
  missing emphasis regions, foreign references and unresolved styles refuse.
  If natural translation cannot satisfy this association without distortion,
  report unsupported alignment; this first format has no silent omission waiver.
- Target text is plain text: markup, arbitrary CSS and the legacy `‖` control
  character are not a parallel styling mechanism. Literal `<`/`>` remain text.
  Preserve Unicode text without automatic compatibility normalization. A run
  boundary that would split a grapheme/shaping cluster refuses.
- `document_targets` retains core-keyed title/bookmark translations separately
  from visible occurrences; it cannot satisfy page-text coverage. Each original
  document title/bookmark requiring translation must resolve under existing
  metadata rules. No typography claim applies to viewer-rendered metadata.
- Font paths resolve beside the mapping. `font_sets` is keyed by `serif`/`sans`,
  with the four role names already used by the library. Only roles actually
  required must be supplied, but an absent role never falls back to regular or
  the other class in this mode. Each selected face must have the required glyphs
  and validated role/class; an unresolved target face refuses in this first
  format. Source-font resolutions do not override target-font checks. Exact
  font-file reuse and system-font fallback are not required or inferred.

## 5. Placement and the first supported boundary

The renderer consumes the normalized run sequence and exact occurrence geometry.
Retain the source page, baseline, direction, segment color and size. Baseline
comparison permits at most 0.05 pt of numeric/extraction rounding, not a planned
vertical shift. This tolerance is a proposed acceptance threshold, not a measured
result. Measure the
whole sequence with the actual selected fonts, advance runs together and shrink
the **whole occurrence uniformly** only under the existing 0.7 floor. Preserve
existing explicitly authored scale exceptions in this format by occurrence ID,
recording every applied exception; no core-keyed exception can affect a repeated
occurrence implicitly. No clipping, dropped target, synthesized emphasis or
automatic source-language substitution is permitted.

Reuse TextWriter/font/glyph/fit logic for eligible runs. Reuse Story only where
tests demonstrate the same baseline, no line break, chosen fonts and logical
text; the existing function's availability is not proof of that behavior.
No independently positioned word boxes or separate new renderer are proposed.

For typography mappings, `run_prepare_font` and its CLI gather the plain text
required by each class/role from target runs via the shared reader. Add an
explicit class/role selector for preparing one of those faces; a legacy default
cannot subset only the old core dictionary. Unsupported/missing selections
refuse, and subset paths are supplied back by the caller. Font downloads and
font-catalog management remain outside the runtime.

First-scope refusals include rotation/vertical writing, multiple baselines or
source sizes/colors in one segment, unsupported script/cluster behavior, and
legacy merge/override/notice placement in a typography job. List markers/dot
leaders or page chrome that require synthesized font placement also refuse in
the first scope; they cannot bypass style checking as legacy passthroughs.
Image/vector content stays untouched. Existing fillable-field geometry and
full-font handling remain their own checks; field typing fonts are not claimed
to preserve authored page-text styles.

This boundary makes the capability useful for eligible lines/documents without
claiming coverage of all invoices or forms. A document containing an unsupported
visible occurrence is not a fully supported typography job. No partial output
is labeled fully preserved. Page-level selective adoption is a separate product
decision and is not added here. B1 wrapping remains deferred.

## 6. Results, verification, QA and review

Use existing typed build exceptions and the existing findings/result conventions.
Include `occurrence_id`, `run_id` where known, zero-based source page, full source
text and a stable reason under `refusals["typography"]`. Proposed reasons:
`stale-extraction`, `unknown-occurrence`, `duplicate-occurrence`,
`invalid-style-reference`, `unresolved-source-style`, `missing-font-role`,
`unsupported-style-alignment` and `unsupported-typography-construct`.
Glyph/fit errors keep their existing categories with occurrence context added.
Extraction returns complete available evidence and warnings; a typography build
refuses unresolved input before publishing a new output.

A successful build records mapping/extraction digests and per-occurrence target
runs, chosen font identities, positions and any uniform scale. Extend the
existing build result and scale-report envelope; do not create a second generic
reporting system. A format change must follow the repo's version/schema rules
when implemented; no speculative release number is reserved by this design.

Verification needs original, final output, mapping and extraction data. It
compares page count and assignment, expected target text and actual output font
runs/geometry for each occurrence, allowing extractor span coalescing only when
the resulting styles match. It must not search the entire PDF for a target and
treat another occurrence as proof. Missing mapping/context produces an explicit
cannot-attest finding for a requested typography check, never a style PASS.
Unresolvable output font identity or geometry is REVIEW/cannot-attest, not an
inferred pass from a build record. Known discrepancies are FAIL. The build record
helps locate expected runs but is not independent proof of the drawn result.

QA sees concatenated plain target text per occurrence, keeping occurrence/run
context on findings; number, glossary and language checks must not receive a
Python object string or lose text by deduplicating cores. Consistency compares
wording separately from styles. Review presents source and target runs with
emphasis/class, source location and any authored font resolution. Repeated cores
remain separate rows. For these new-format jobs, reviewer input must identify
the mapping and extraction digests; mismatches cannot attest the current job.
General legacy review freshness remains A14; do not build a competing mechanism.

Structural verification remains advisory on the library surface, consistent with
the app's existing policy. It does not delete or withhold a successfully built
file. A build refusal and an advisory verification result are distinct. A03's
broader previous-output lifecycle issue remains open: a failed attempt must not
claim an older artifact as its successful result, but this design does not
silently choose a new global replacement/deletion policy.

For a typography job, `rebuild` passes the mapping, extraction and original
explicitly. The documented delivery workflow runs verification on the final file
after `field_fonts` or `finish`; this design does not quietly turn `finish` into
a new policy gate. Unknown/unsupported new-format inputs surface as errors from
all updated readers. New-format reviewer input carries `typography` with
`extraction_id` and `mapping_sha256`, the latter a SHA-256 of canonical parsed
mapping JSON under the same encoding rules. Missing/mismatched bindings are
review errors. Broader invalid-review delivery behavior remains A01 and is a
release-readiness prerequisite, not a second fix hidden in this design.

The skill's eventual workflow and examples must use the same format capability
check, occurrence authoring, final-file verification and review path. Supporting
only an internal Python call would not meet this repo's dual-use requirement.

## 7. Observable acceptance, not claims of completed testing

The following are requirements for future implementation. No new checks below
have run. Tests/probes are to be added under the existing test/corpus structure;
test filenames and implementation order belong to the later plan.

| Case | Required outcome | Verify by |
| --- | --- | --- |
| Existing mappings | Legacy calls, output/report semantics and intended CLI bytes remain unchanged, aside from an intentional version value. | Existing full suite and both CLI/verdict parity probes against a clean recorded base; account explicitly for version metadata. |
| Source styles | A Times/Helvetica fixture and regular-prefix/bold-or-italic-tail fixtures retain font evidence, exact text offsets and separate styles. | Inspect extraction JSON and assert raw source font identities before comparing. |
| Repeated text | Two identical cores with different emphasis on one page receive different target run sequences at the correct positions. | Extract/raster-inspect final PDF by occurrence; swap/duplicate IDs and require named refusals. |
| Reordered translation | Emphasized text can move before its regular context without emphasizing the regular words. | Authored bilingual fixture, actual output font-run inspection and independent reader/visual pass. |
| Families and four roles | Source serif/sans distinction and regular/bold/italic/bold-italic map to validated corresponding target faces, without role/class fallback. | Use known source/target fonts; assert actual output font identities and inspect final rasters. Include Latin and horizontal JA/zh-Hans with suitable class/role resources. Missing resources refuse. |
| Binding and coverage | Source/extraction edits, duplicate/missing/foreign IDs, omitted meaningful source style runs and conflicting resolutions cannot build. | Mutate each input independently; check typed reasons and absence of a new successful output/result. |
| Placement limits | Source page count, assignment and first baseline remain; full target stays in the permitted one-line space or build refuses at the floor. | Geometry checks plus independent final raster inspection; include long targets and repeated near-neighbor labels. No B1 recovery claim. |
| Unsupported constructs | Rotated, multi-size/color, unsupported-script, merge/leader/override cases report the specific construct; they do not quietly use the legacy path. | One positive refusal fixture per declared boundary, checked through both library and CLI routes. |
| QA/review/final verification | Every target occurrence reaches QA and the reader; stale typography review input is named; tampering with final fonts/emphasis fails or cannot be attested. | Same-text/different-style fixtures, mapping-digest change, then independently alter final PDF styling and rerun verification. |
| Old runtime / wrong format | Current new-format consumers reject unknown schemas; the inspected v54/v56 retypesetters cannot successfully draw a new-format file. Old QA limitations stay documented. | Run format capability checks and old-version subprocess cases; assert no new PDF from rejected build. |
| Both skill hosts | Installed skill instructions expose the capability and a bounded job produces the same expected artifacts under Claude/Codex. | Actual host traces and artifact inspection; discovery alone is not workflow acceptance. |

AGENTS.md Rule 1 requires a verification pass that did not write any future
rendering/font/layout changes, citing real commands and outputs. Glyph counts
alone cannot attest mark stacking or semantic emphasis. A passing mechanical
fixture does not establish arbitrary-document adoption.

## 8. Ownership and review boundary

Library: extraction evidence, format/identity validation, reusable placement,
results and QA/review/verification integration, corpus and skill documentation.
App: target/alias resolution, provision of suitable class/role font files,
translation orchestration, lifecycle and notices, consumer pin adoption and
migration evidence. The app's product roadmap remains canonical for product
priorities; this is one upstream capability, not a second app renderer project.

Written-design approval permits the implementation-planning stage. It does not
approve a plan that has not been written, a push/merge, another-repo edit, a
future release pin or a relaxed typography promise. A21 housekeeping and B1 are
not started by this design.
