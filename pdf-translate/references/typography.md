# Typography preservation (`typography-1`)

A translated PDF built the legacy way carries one font role per segment. A
source line that reads **Please pay NOW** — regular sans, then bold — comes back
as one flat run, and the emphasis the author wrote is gone. `typography-1` is an
opt-in mapping format that keeps the source's serif-versus-sans class and its
within-line bold/italic, and binds each authored run to the exact source
occurrence it came from.

It is additive. `legacy` mappings read and build exactly as before; nothing in
this file changes a job that does not ask for it.

## Ask before you author

An engine too old to read the format refuses at build time, after the authoring
is done. Ask first:

```python
import pdf_translate

formats = getattr(pdf_translate, 'MAPPING_FORMATS', ())
if 'typography-1' not in formats:
    raise RuntimeError('This installed engine does not support typography-1')
```

`getattr`'s default matters: an engine from before the export has no such
attribute, and you want `()` rather than an `AttributeError` you cannot tell
apart from a broken install.

`MAPPING_FORMATS` describes **implemented format support**. It is not a claim
that the skill is ready for public release, and not a promise that a given
document will succeed — see [What refuses](#what-refuses).

## The support boundary

First scope, and everything outside it refuses rather than degrades:

- Horizontal, single-baseline page text, left to right.
- Latin, Japanese and Simplified Chinese.
- One source size and one colour per segment.
- **Exactly the source page count**, and every target stays on its source page.
- The source's first baseline does not move.

Widget and comment appearance text is not page text: it is read separately and
is not given typography, though its paint still counts as possible occlusion.

## 1. Extract, with the evidence kept

```python
from pdf_translate import run_extract

run_extract('original.pdf', 'work/', typography=True)
```

`segments.json` gains `typography`, and every segment gains an `occurrence_id`
and its `style_runs`. This is the actual extraction of a one-page fixture whose
source line is bold-tailed Helvetica:

```json
{
  "id": 0, "page": 0, "size": 12.0, "color": 179,
  "text": "Please pay NOW",
  "occurrence_id": "s0",
  "style_runs": [
    {
      "run_id": "s0/r0", "font_id": "f6", "candidates": ["f6"],
      "text": "Please pay ", "offsets": [0, 11],
      "class": "sans", "bold": false, "italic": false,
      "evidence": {"span_font": "Helvetica", "span_flags": 0,
                   "span_alpha": 255, "span_char_flags": 16,
                   "font_observation": "f6"},
      "unresolved": []
    },
    {
      "run_id": "s0/r1", "font_id": "f8", "candidates": ["f8"],
      "text": "NOW", "offsets": [11, 14],
      "class": "sans", "bold": true, "italic": false
    }
  ]
}
```

`offsets` index into the segment's own `text`, so a run is locatable without
re-measuring. `class`, `bold` and `italic` are read from the actual embedded
font program, not from the span flag — a real Noto Sans face reports
`span_flags=4` while its PANOSE class says sans, so the flag is kept as
evidence and is never the authority.

### Source-font uncertainty is reported, never guessed

`font_id` is `null` when more than one actual source resource matches a span.
Every candidate stays in `candidates`, and `unresolved` names why:

- `ambiguous-font-resource` — several resources match; you must say which.
- `missing-font-resource` — no resource could be associated at all.

An authored resolution cannot invent an association the source does not have.
Supply one in `source_font_resolutions` when you know the answer; if you do not,
the run stays unresolved and final verification returns REVIEW rather than PASS.

## 2. Author against occurrences, not against text

Two identical source strings are two occurrences. The old mapping keyed on text,
so asking for one of them selected the first match — that is the limitation this
format removes.

This is a real, verified mapping. Its two occurrences carry the same words in
different families, and each target **reorders** the emphasis, putting the bold
word first:

```json
{
  "format": "typography-1",
  "extraction_id": "62e62e82ed4bd423c1f700b14e02b664786fb052174b50961cd7905ce405f320",
  "lang": "es",
  "font_sets": {
    "sans":  {"regular": "selected/sans-regular.ttf",
              "bold": "selected/sans-bold.ttf"},
    "serif": {"regular": "selected/serif-regular.ttf",
              "bold_italic": "selected/serif-bold_italic.ttf"}
  },
  "source_font_resolutions": [],
  "allow_scale": [],
  "document_targets": {"Payment form": "Formulario de pago"},
  "targets": [
    {"occurrence_id": "s0",
     "runs": [{"text": "AHORA ", "source_runs": ["s0/r1"]},
              {"text": "pague",  "source_runs": ["s0/r0"]}]},
    {"occurrence_id": "s1",
     "runs": [{"text": "AHORA ", "source_runs": ["s1/r1"]},
              {"text": "pague",  "source_runs": ["s1/r0"]}]}
  ]
}
```

`extraction_id` binds the mapping to the extraction it was authored against. A
mapping written for a different extraction is refused, not silently retargeted.
`source_runs` is what carries the style: the target run inherits the class and
emphasis of the source runs it names, wherever you place it in the line.

`document_targets` is the metadata channel — title and outline. Those are exact
source/target pairs with no page ID, because a document title has no occurrence;
page findings that happen to share its wording still carry occurrence IDs.

## 3. Prepare one face per class and role

```python
from pdf_translate import run_prepare_font

run_prepare_font('NotoSans-Bold.ttf', 'translations.json',
                 'work/selected/sans-bold.ttf',
                 font_class='sans', font_role='bold',
                 reference_fonts='tests/fonts')
```

Roles are `regular`, `bold`, `italic`, `bold_italic`. The subset is built from
the characters that class and role actually draw, and preparation refuses a face
whose real metadata does not match the role it is being asked to fill — a
variable face is instanced through `instantiateVariableFont(updateFontNames=True)`
so the style metadata and the outlines move together. A face lacking usable STAT
or name evidence refuses rather than claim a role it cannot prove.

## 4. Build, with the original in hand

```python
from pdf_translate import run_retypeset

built = run_retypeset('work/stripped.pdf', 'work/segments.json',
                      'translations.json', 'work/out.pdf',
                      original='original.pdf')
assert built.pages == 1
```

`original=` is required for a typography build: the original is re-read so the
source digest, page geometry and drawing state can be verified rather than
trusted. Placement measures per-glyph outlines with a `BoundsPen` and checks
proposed boxes against their neighbours — including other *translated* runs,
because an italic `f` can reach into a preceding run that passed its own check.

## 5. Verify against the delivered file

```python
from pdf_translate import run_verify

verdict = run_verify('original.pdf', 'work/final.pdf',
                     translations='translations.json',
                     segments='work/segments.json', typography=True)
gate = next(g for g in verdict.gates if g.name == 'typography')
```

The gate reads the **final PDF's own glyphs and font programs**, not the build's
intentions. On the mapping above:

```json
{"name": "typography", "status": "PASS",
 "message": "2 occurrences checked from actual final glyphs and font programs.",
 "findings": []}
```

PASS means every occurrence's class and emphasis were confirmed from the file.
REVIEW means something could not be attested — an unresolved source resource, a
subset whose coverage cannot be proven, possible occlusion. FAIL means the file
contradicts the mapping. An ambiguity is never promoted to PASS.

### What the schema numbers mean

Only one file changes shape, and only for a typography build. `scale_report.json`
stays at **schema 1** for a legacy job and becomes **schema 2**, carrying an
extra `typography` block, when the build had typography. The verify report and
the extraction's own `typography` record are both schema 1 — their first
version, not a break. Legacy serialization is untouched, so a reader written
before any of this keeps working on the jobs it already understood.

## QA and review keep the occurrences

`run_qa` and `run_review` carry the same occurrence and run bindings, so a
reviser sees which occurrence a finding belongs to instead of a deduplicated
core. Repeated cores are never collapsed. Metadata findings use the document
channel; page findings carry occurrence and run IDs where the wording alone
would be ambiguous.

## What refuses

These are explicit first-scope refusals, not preserved behaviour. The build
refuses before replacing an existing PDF or report:

| Construct | Why |
| --- | --- |
| Source clipping, or text inside a Form XObject | A clip cannot be proven not to cut the glyph |
| Non-uniform transforms, shear, stroke, transparency, soft masks, unusual blending | The delivered shape would not be the shape that was measured |
| Non-default page `UserUnit` | The physical page size is not what the raw boxes say |
| A face where two authored characters share one glyph | One CMap per glyph cannot preserve both |
| A source font role that the supplied face does not actually have | Better a typed refusal than a silent wrong role |

A refusal from the source-content check names the occurrence it is about: in
`refusals['typography']`, `occurrence_id` and `source_text` are those of the
segment that holds where the offending text starts. A whole-page construct,
such as `UserUnit`, or offending text that no segment holds, carries the
`page` with no occurrence.

Possible occlusion and unresolved clipping in the **final** file are REVIEW, not
FAIL: the file may be correct, but this cannot attest that it is.

## What is not verified

- **CJK italic and bold-italic have no measured positive cases.** No suitable
  real face was available. Supplying an upright regular face in their place
  produces a typed wrong-role refusal in all eight negative cells; none is
  relabelled or synthesised. Treat those cells as unknown, not as working.
- Language and emphasis *semantics* — whether the translation emphasises the
  right word — need a qualified reader. No gate here judges that.
- Public-release readiness is separate and still open; see the blockers in
  `docs/REQUESTS-from-product.md`.
