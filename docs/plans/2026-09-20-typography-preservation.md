# Typography preservation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve source font class and meaningful within-line emphasis in eligible translated PDFs, with exact occurrence association and independently checked output.

**Architecture:** Add an opt-in extraction representation and strict mapping reader. Feed its ordered runs into the existing placement machinery, and feed the same authored content into QA/review while verification independently inspects the final PDF. Keep legacy calls and serialization unchanged when typography is not selected.

**Tech Stack:** Existing Python 3.10+, PyMuPDF, fontTools, pikepdf and unittest; no new runtime dependency or renderer. The inspected local interpreter has PyMuPDF/MuPDF 1.28.2/1.28.2; the declared wider dependency range is not a new support claim.

**Spec:** [Approved additive design](../design/typography-preservation/DESIGN.md), approved by Rodrigo on 20 September 2026 after design commit `ef52e5f`. Rodrigo subsequently approved this plan and native execution. Work is underway; completed tasks and actual checks are recorded in [the execution evidence](../reviews/2026-09-20-typography-implementation.md) and the local execution ledger.

## Global constraints

- “Same source page count, original page assignment and first baseline are required.”
- “No line wrapping, new boxes, continuation pages or neighbor movement is added.”
- “Exact source font-file reuse is unnecessary.”
- “The first supported scope is horizontal, single-baseline, selectable page text with one source size/color per segment.”
- “Source and target runs in the first scope use Latin, Japanese or Simplified Chinese text; other scripts require a later independently verified extension.”
- “Baseline comparison permits at most 0.05 pt of numeric/extraction rounding, not a planned vertical shift.”
- Preserve the existing `0.7` scale floor and only the explicitly authored occurrence-specific exceptions defined in the design.
- “A plain mapping with no `format` remains legacy.” Unknown formats never fall back to legacy.
- “Reject duplicate JSON keys everywhere.” This rule applies to the new format; do not silently tighten legacy parsing in this feature.
- “Structural verification remains advisory on the library surface, consistent with the app's existing policy.” A failed build is distinct from a built PDF with a FAIL/REVIEW verdict.
- Preserve Python `>=3.10` and existing dependency declarations during this feature. A05 owns proving/correcting the wider version range.
- The MIT library is the implementation owner. Never open or copy from `C:\Dev\pdf-translator`. No app edits, messages, new product roadmap, B1 work, PR #12/#13 edits, push, merge or release are part of execution approval.
- Rendering/font/layout changes require an independent pass citing real commands, outputs and inspected rasters under AGENTS.md Rule 1. The writer's tests alone cannot complete this work.
- Keep all current uncommitted work intact. Use scoped conventional local commits without attribution trailers; never stash or commit unrelated changes.

## Review focus

These five cases are easy to miss in the happy path. Their owning tasks below include explicit tests.

1. Two PDF font resources share a name but refer to different programs: retain exact resource identity or report unresolved association (Task 1).
2. A mapping is moved, the process changes directory, or a chosen font is replaced: resolve beside the mapping and inspect the actual file/program (Tasks 2–3).
3. Extraction selects one page of a longer source: permit inspection/scaffolding but refuse a whole-document typography build, including a source with a trailing blank page (Tasks 2, 4–5).
4. Literal markup-like text, decomposed accents, variation selectors and whitespace cross a run boundary: preserve plain text and refuse unsafe splitting/unsupported shaping (Tasks 2, 4).
5. A cancelled/failed run encounters a prior successful PDF/report/review: never report that artifact as the new success; preserve A03/A14 ownership and require current typography bindings (Tasks 4, 6–7).

## Execution base, evidence and dependencies

The read-only planning recheck found `codex/b1-design-canvas` at `ef52e5f40d2bd2a8e751f3882574e1f8f27ec97a`, parent runtime `1d4f9707c4d9934fbc88d8f25576ac304b9bb139` (v58). Remote main is `a5629fbd6bc084f9ab849ae3db74992c15807fcc`; PR #12 is OPEN at `abc47674019aaed8f61b716b83e3d289e38d1f1c`, PR #13 OPEN at `1d4f970`. These are observations, not future assumptions. Current working files include uncommitted v61 documentation/metadata and earlier audit/B1 changes.

At execution, create a separate `codex/typography-preservation` branch/worktree from the recorded clean design base using the worktree skill. Copy only this approved plan and approval-status documentation into that checkout if they are still uncommitted; record their hashes. Do not copy the dirty runtime or silently incorporate other backlog fixes. This depends on v58 APIs in local ancestry without modifying their open PRs. A later integration onto merged main must be explicitly reviewed; this plan does not merge the stack.

Before Task 1, record the worktree commit, installed package location, interpreter/backend versions, dependency inventory and test-font hashes under its own ignored `runs/typography/`. Run the full baseline suite and both existing parity probes once. Preserve stdout, stderr and exit codes separately. A failing baseline is investigated and recorded before attributing it to typography; it is not fixed as a hidden extra task.

Use the repo venv, not system Python. From the implementation checkout's `pdf-translate/`, initialize PowerShell:

```powershell
$env:PYTHONUTF8 = '1'
$typoPython = 'C:\Dev\pdf-translate-skill\pdf-translate.venv\Scripts\python.exe'
$typoRoot = (Get-Item -LiteralPath '..').FullName
$env:PYTHONPATH = (Get-Location).Path
& $typoPython -m unittest discover -s tests -t .
& $typoPython -m unittest discover -s ../dev/canary -p test_score.py
```

For each implementation task: run its named test module red, inspect the failure reason, implement, rerun green, then run affected existing tests. Before a stage-changing commit, run both parity probes against the preserved clean base as required by the handover. The CLI probe takes separate fresh directories and the **same absolute font file**; the verdict probe uses the same fixture directory and each checkout's `PYTHONPATH`. Compare both console and verdict output, excluding only existing runner normalization and a separately documented intentional version value. Do not regenerate expected behavior from the candidate output.

```powershell
& $typoPython ../dev/probes/cli_parity_runner.py ../runs/typography/parity-candidate --font C:/Dev/pdf-translate-skill/pdf-translate/tests/fonts/NotoSans-Regular.ttf
& $typoPython ../dev/probes/verdict_parity_fixtures.py ../runs/typography/verdict-jobs
& $typoPython ../dev/probes/verdict_parity_runner.py ../runs/typography/verdict-jobs
```

Use fresh task-specific parity directories on subsequent runs; run fixture generation once per comparison. Running only the three commands on one checkout is **not** a parity comparison.

A01 invalid-review delivery is a separate release-readiness prerequisite; do not fix it here or call this feature publicly ready while it remains open. A03 previous-artifact lifecycle, A04 process validation, A05 dependency bounds, A06 legacy rebuild defaults, A14 legacy review freshness and E10 packaging/licensing keep their existing backlog ownership. This plan only implements the new format's explicit context and binding. A21 and B1 remain unstarted.

## File structure and dependency order

Paths below are relative to the repository root. New implementation files listed here do not exist yet.

| File | Responsibility | Task |
| --- | --- | --- |
| `pdf-translate/pdf_translate/typography.py` | Source font observations, canonical extraction identity, exact style records; pure validation helpers, no renderer | 1–2 |
| `pdf-translate/pdf_translate/mapping.py` | One format dispatcher and normalized mapping, strict new-format shape/association checks | 2 |
| `pdf-translate/pdf_translate/extract_segments.py` | Retain raw spans before existing grouping discards styles; opt-in files/result | 1 |
| `pdf-translate/pdf_translate/prepare_font.py` | Per-class/role charset, inspect and subset the selected face | 3 |
| `pdf-translate/pdf_translate/retypeset.py` | Preflight and place ordered runs using existing TextWriter/fit/font facilities | 4 |
| `pdf-translate/pdf_translate/results.py` | Optional typography extraction/build payloads with legacy serialization unchanged | 1, 4 |
| `pdf-translate/pdf_translate/typography_verify.py` | Read actual final-PDF runs, font evidence and occurrence geometry | 5 |
| `pdf-translate/pdf_translate/verify.py` | Select the new check and adapt it into existing findings/verdicts | 5 |
| `pdf-translate/pdf_translate/qa_check.py`, `review.py` | Per-occurrence plain text, styled reader pairs and bound reviewer input | 6 |
| `pdf-translate/pdf_translate/pipeline.py` | Carry opt-in/context through commands; reject incompatible helpers | 7 |
| `pdf-translate/pdf_translate/__init__.py` | Publish capability only after its complete workflow has passed | 9 |
| `pdf-translate/tests/typography_fixtures.py` | Synthetic source/target jobs with independently known expected styles | 1–4 |
| `pdf-translate/tests/test_typography_{extract,mapping,fonts,retypeset,verify,review,pipeline,acceptance}.py` | Corresponding regression suites; unittest discovery | 1–8 |
| `pdf-translate/tools/fetch_test_fonts.py`, `tests/fonts/README.md` | Additional reproducible font fixtures with upstream/license references | 3 |
| `dev/probes/typography_acceptance.py` | Retained CLI/Python fixture jobs, rasters and measured acceptance output | 8 |
| `.github/workflows/tests.yml` | Explicit new modules if CI still enumerates them, font preparation and support matrix | 8–9 |
| `pdf-translate/references/typography.md` | New-format authoring and support boundary, linked from existing workflow docs | 9 |
| `pdf-translate/{SKILL.md,README.md,pyproject.toml}`, `.claude-plugin/plugin.json`, root `README.md`, `references/{translations-format,consumer-guide,gates}.md` | Capability discovery, runnable examples, eventual lockstep version | 9 |
| `docs/reviews/2026-09-20-typography-implementation.md` | Execution evidence when work actually starts; record real run dates and exact commits | 8–9 |

Dependency order: **1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9**. This is one cross-stage format change, not independent product projects. Do not dispatch neighboring implementers concurrently against evolving interfaces. Internal APIs below are implementation choices for plan review; public signatures follow the approved design.

### Task 1: Preserve source evidence and bind an extraction

**Files:** create `pdf-translate/pdf_translate/typography.py`, `tests/typography_fixtures.py`, `tests/test_typography_extract.py`; modify `extract_segments.py:526`, grouping at `:557`, output at `:731`, CLI at `:810`, and `results.py:179`. Function anchors, not line numbers, remain authoritative after edits.

**Interfaces produced:** `canonical_digest(value) -> str`; `observe_fonts(doc) -> dict`; `source_runs(group_spans, occurrence_id, font_observations) -> list[dict]`; `bind_extraction(payload) -> dict`. `run_extract(src, outdir, *, typography=False, gap=12.0, pages=None)` and `extract_segments(src, outdir='.', gap=12.0, pages=None, *, typography=False)` use the same implementation. Append an optional `typography` payload to `ExtractResult`; omit it from `to_dict()` when absent so legacy result keys do not change.

New extraction root `typography` contains `schema=1`, `source_sha256`, `extraction_id`, `options` (effective gap and sorted selected pages), `page_geometry` (every source page's media/crop boxes and rotation), `fonts` and field identities. Segment `style_runs` contain exact text, `[start,end]` codepoint offsets, bbox/origin, size/color, `font_id`, `run_id`, `class`, `bold`, `italic`, evidence and unresolved reasons. `occurrence_id` is `s` plus its existing integer `id`; each raw contributing run gets `/r0`, `/r1`, in source order. Retain leading/trailing whitespace spans in typography mode without changing legacy grouping. Keep marker/dot information as evidence even though those jobs will refuse placement.

- [ ] Add the following fixture builder and extraction regression. Explicit `fontname` avoids the Helvetica fallback trap. No PDF rendering assertion may start from unverified source fonts.

```python
# tests/typography_fixtures.py
from pathlib import Path
import pymupdf

def make_source(path):
    path = Path(path)
    with pymupdf.open() as doc:
        page = doc.new_page(width=400, height=240)
        for y, prefix, tail in [(60, 'helv', 'hebo'), (120, 'tiro', 'tibi')]:
            page.insert_text((30, y), 'Pay ', fontname=prefix, fontsize=12)
            x = 30 + pymupdf.get_text_length('Pay ', fontname=prefix, fontsize=12)
            page.insert_text((x, y), 'NOW', fontname=tail, fontsize=12)
        doc.save(path)
    return path
```

```python
# tests/test_typography_extract.py
import json
import tempfile
import unittest
from pathlib import Path
import pymupdf
from pdf_translate import run_extract
from tests.typography_fixtures import make_source

class ExtractionTests(unittest.TestCase):
    def test_repeated_text_retains_different_source_styles(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = make_source(Path(tmp) / 'original.pdf')
            with pymupdf.open(src) as doc:
                names = {s['font'] for b in doc[0].get_text('dict')['blocks']
                         if b['type'] == 0 for line in b['lines'] for s in line['spans']}
                self.assertEqual(names, {'Helvetica', 'Helvetica-Bold',
                                         'Times-Roman', 'Times-BoldItalic'})
            result = run_extract(str(src), tmp, typography=True)
            data = json.loads(Path(result.segments_path).read_text(encoding='utf-8'))
            first, second = data['segments']
            self.assertEqual((first['text'], second['text']), ('Pay NOW', 'Pay NOW'))
            self.assertNotEqual(first['occurrence_id'], second['occurrence_id'])
            self.assertEqual([r['bold'] for r in first['style_runs']], [False, True])
            self.assertEqual([r['class'] for r in second['style_runs']], ['serif', 'serif'])
            for seg in data['segments']:
                self.assertEqual(''.join(r['text'] for r in seg['style_runs']), seg['text'])
                for run in seg['style_runs']:
                    a, b = run['offsets']
                    self.assertEqual(seg['text'][a:b], run['text'])
```

- [ ] Run `& $typoPython -m unittest tests.test_typography_extract -v`; require failure from the absent opt-in/style evidence, not a font fixture error.
- [ ] Capture each span before `g['bold']`/`g['italic']` aggregation. Resolve actual font objects through page/Form resources; never key solely by the span's font name. If association is not unique, keep the observation unresolved and issue a warning. Use exact Base14 identities for Times/Helvetica variants; resolve supported embedded faces only when available OS/2/PANOSE/head/post/PDF observations agree. Do not infer sans from an unset PDF serif flag. Normalize subset prefixes only as supporting evidence, never as proof that two resources are the same.
- [ ] Implement canonical hashing with the exact byte convention below. Hash an explicitly assembled payload of source digest, schema, effective options, document/field/page facts, ordered segments and font observations; exclude paths, output filenames, timestamps, warnings and the `extraction_id` itself. Do not hash just a selected handful of styles. Reject NaN/Infinity when reading as well as writing.

```python
import hashlib
import json

def canonical_digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()
```

- [ ] Extend the same module with cases that change one source byte, gap, page selection, occurrence order, style or geometry and require a changed digest; moving the same files must not change it. Add exact-font-name collision and absent/contradictory font metadata fixtures, leading/trailing whitespace, rotated and mixed-size/color records. Unresolved extraction returns evidence/warnings rather than erasing the run. Default-mode JSON and result serialization must match the clean baseline.
- [ ] Run the module and `tests.test_pipeline.ExtractTests`, then required parity checks. Commit only this task's files as `feat(extract): retain bound typography source runs`.

### Task 2: Parse one strict occurrence mapping

**Files:** create `pdf-translate/pdf_translate/mapping.py`, `tests/test_typography_mapping.py`; extend `typography.py` and `tests/typography_fixtures.py`.

**Interfaces:** `load_mapping(path, segments_path=None) -> MappingDocument`, resolving default extraction beside the mapping; `parse_mapping(text, *, extraction=None, mapping_dir=None) -> MappingDocument` for pure tests. A legacy mapping returns `format='legacy'`, `legacy` holding the unchanged dictionary, with no new strict validation. New records use these frozen types; nested input dictionaries must be copied so caller mutation cannot change parsed output.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class StyledRun:
    text: str
    source_runs: tuple[str, ...]
    font_class: str
    font_role: str

@dataclass(frozen=True)
class OccurrenceTarget:
    occurrence_id: str
    page: int
    source_text: str
    runs: tuple[StyledRun, ...]

@dataclass(frozen=True)
class MappingDocument:
    format: str
    legacy: dict | None
    lang: str
    extraction_id: str
    mapping_sha256: str
    targets: tuple[OccurrenceTarget, ...]
    document_targets: dict
    font_sets: dict
    allow_scale: dict
    source_font_resolutions: tuple[dict, ...]
    extraction: dict | None

def role_name(bold, italic):
    return 'bold_italic' if bold and italic else (
        'bold' if bold else ('italic' if italic else 'regular'))
```

The serialized role key is **`bold_italic`**, as the existing mapping scaffold and font lookup use. Existing `_role_name` returns the display label `bold-italic`; do not reuse that display spelling as a new mapping key.

- [ ] Add the following pure red test plus a complete valid mapping assembled from Task 1's extraction. Define `make_mapping(extraction, font_sets)` in the fixture module: one target per segment; each run initially copies its exact source text and `run_id`; metadata title/outline entries are copied explicitly into `document_targets`; `lang='en'`, exact extraction digest, empty resolutions/scale exceptions. Return the dictionary, not an already parsed production object.

```python
# tests/typography_fixtures.py
from copy import deepcopy

def make_mapping(extraction, font_sets):
    document = extraction.get('document') or {}
    metadata = [document.get('title', '')] + list(document.get('outline') or [])
    return {
        'format': 'typography-1',
        'extraction_id': extraction['typography']['extraction_id'],
        'lang': 'en', 'font_sets': deepcopy(font_sets),
        'source_font_resolutions': [], 'allow_scale': [],
        'document_targets': {text: text for text in metadata if text},
        'targets': [
            {'occurrence_id': seg['occurrence_id'],
             'runs': [{'text': run['text'], 'source_runs': [run['run_id']]}
                      for run in seg['style_runs']]}
            for seg in extraction['segments']
        ],
    }
```

```python
import unittest
from pdf_translate.mapping import parse_mapping
from pdf_translate.results import MappingError

class MappingShapeTests(unittest.TestCase):
    def test_duplicate_format_is_not_last_key_wins(self):
        with self.assertRaises(MappingError) as caught:
            parse_mapping('{"format":"legacy","format":"typography-1"}')
        self.assertEqual(caught.exception.refusals['typography'][0]['reason'],
                         'invalid-style-reference')
```

- [ ] Run `& $typoPython -m unittest tests.test_typography_mapping -v` and confirm the missing reader is the red signal.
- [ ] Detect format with a pair-preserving JSON loader before dictionary construction. Preserve ordinary no-format legacy behavior; duplicate/unknown `format` must never smuggle a new job through that branch. For an explicit `format`, accept only `typography-1`; the public capability name `legacy` describes the absent-format path. Enforce the design's exact root/nested keys, booleans (not integers), lowercase 64-hex digest, finite numbers, nonempty text/reasons, serif/sans classes and four roles. Retain original parsed JSON for its canonical mapping digest, before resolving relative font paths. Reject absolute-path rewrites only when hashing extraction, not valid absolute font paths.
- [ ] Recompute extraction identity, index occurrences/runs/font IDs with duplicate rejection, apply unknown-only authored font resolutions, then create the normalized ordered targets. No substring/core/bbox fallback. Every meaningful source run must be represented; multi-source target runs require the same resolved style. Missing visible occurrences fail even when legacy `passthrough` is true. A selected subset of source pages cannot make a whole-document build valid; preserve that fact for Task 4's explicit refusal. Metadata coverage is separate.
- [ ] Test each mutation independently: duplicate/foreign/missing occurrence; cross-occurrence run; omitted bold tail; wrong digest; unknown/mixed root; duplicate/foreign/conflicting resolution; nonexistent or duplicate scale-exception ID; empty target; plain `<b>literal</b>` retained literally; `‖` rejected as unsupported input; reordered target runs accepted; same text with different styles accepted. Use stable `refusals['typography']` entries with `reason`, `occurrence_id`, `run_id`, zero-based `page` and full `source_text`, with `None` for unavailable context. Shape errors use `invalid-style-reference`; binding failures use `stale-extraction`; coverage failures use `unknown-occurrence` with a specific detail; semantic support failures use `unsupported-style-alignment`.
- [ ] Reject newlines, bidi controls, unsafe grapheme boundaries and unsupported-script/cluster behavior without normalizing text. For the first TextWriter path, combining marks/variation sequences requiring unproven positioning may refuse as `unsupported-typography-construct`, even within a run. Include `e` + combining acute split across runs and a Han ideograph + variation selector. UAX #29 defines the boundary issue; a regex that splits codepoints is not a grapheme implementation. Keep ordinary supported Latin/kana/Han punctuation and spaces intact; test locale tags against the existing Han-convention resolver rather than treating any tag as proof of the actual script.
- [ ] Rerun the parser tests, extraction tests and legacy-reader fixtures. Commit as `feat(mapping): validate occurrence typography mappings`.

### Task 3: Resolve and subset exact class/role fonts

**Files:** modify `pdf-translate/pdf_translate/prepare_font.py:101,153,323`, `typography.py`; create `tests/test_typography_fonts.py`; update `tools/fetch_test_fonts.py` and `tests/fonts/README.md` only for the new fixture resources.

**Interfaces:** append keyword-only `font_class=None, font_role=None` to both font-preparation entry points, preserving every existing positional parameter. New `typography.inspect_font(path) -> dict` returns observed class/weight/slant, evidence, file SHA-256 and unresolved reasons. New `mapping.charset_for(document, font_class, font_role) -> set[str]` yields only the selected targets' plain text. `load_mapping` supplies adjacent `segments.json`; no new mandatory extraction argument is added to legacy calls. Font roles are `regular`, `bold`, `italic`, `bold_italic`.

- [ ] Write a red test that reads `charset_for` from a valid fixture mapping with bold `AHORA` and regular `pague`, requiring the bold set to equal `set('AHORA')`. Add a missing-selector test on the real wrapper:

```python
from pdf_translate import run_prepare_font
from pdf_translate.results import FontError

# Within a unittest test method, mapping_path comes from make_mapping and
# font_path is the fixture's verified Noto Sans regular file.
with self.assertRaises(FontError) as caught:
    run_prepare_font(str(font_path), str(mapping_path), str(output_path),
                     font_class='sans')
self.assertEqual(caught.exception.reason, 'missing-font-role')
self.assertFalse(output_path.exists())
```

- [ ] Run `& $typoPython -m unittest tests.test_typography_fonts -v`; confirm the new selector/charset behavior fails before implementation.
- [ ] Resolve font paths beside the mapping, inspect actual font files before use and reject unresolved/wrong classes or roles. Source resolutions cannot authorize a target face. Keep existing embedding checks and preparation options. Select charset via the shared reader, then run the existing subsetting/raster/canonical probe process. Subset only the requested face; return the existing `FontResult` and let the caller write its resulting path into the mapping.
- [ ] Use consistent supported metadata, not a guessed family name: family/PANOSE class, weight and fsSelection/head/post slant observations. Missing class evidence is unresolved, not sans. Reject inconsistent bold/slant evidence or uninstantiated variable target faces at placement. Preparation may accept a variable source with existing `instance=`: instantiate it before validating its concrete target role, then subset it. After subsetting, verify that role/class evidence still resolves. Do not fix a target font by flipping metadata bits to make a test pass.
- [ ] Prepare real Latin serif/sans regular, bold, italic and bold-italic resources; JA/zh-Hans serif/sans regular and bold; for CJK italic/bold-italic, positive acceptance requires genuine suitable faces, otherwise explicitly test refusal and report the unmeasured positive cell. Extend the existing fetcher with verified upstream Noto static/variable TTF URLs pinned to inspected commits and record hashes/licenses. Do not use fake italic transforms, proprietary system fonts, or relabeled regular fonts. No font binaries are committed. Network failure or absent required fixtures is an acceptance failure, not a silent SKIP.
- [ ] Run tests for wrong role, wrong class, replaced file at the same path, absent glyphs, read-only mapping, relative paths from another working directory and separate font subsets whose charsets differ. Planning inspected three present regular sans fonts: each had `sFamilyClass=0`, PANOSE `(bFamilyType=2,bSerifStyle=11)`, weight 400. This is why relying solely on `sFamilyClass` would reject the current resources. It is not proof for uninspected roles.
- [ ] Rerun this module and affected existing font tests/parity. Commit as `feat(fonts): prepare typography faces by class and role`.

### Task 4: Place complete occurrences without reflow

**Files:** modify `pdf-translate/pdf_translate/retypeset.py:697`, `results.py:205`; create `tests/test_typography_retypeset.py`; extend fixture helpers.

**Interfaces:** append `original=None` to `run_retypeset`'s existing keyword-only arguments and add keyword-only `original=None` to its loud wrapper. Dispatch by `MappingDocument.format` before reading root `translations`. Add private `_run_typography(stripped, document, out, *, original, progress, cancel, scale_report, resource_root) -> RetypesetResult` in the existing renderer. Existing `_DEFAULT` scale-report sentinel remains. Add optional `typography` payload to `RetypesetResult` and omit its key when absent. Keep old report envelope schema 1 for legacy; use schema 2 for typography with existing `runs` plus a `typography` block. Readers must explicitly accept those two envelopes.

- [ ] Extend the fixture module with `make_job(work, font_sets) -> dict`: create `original.pdf` via `make_source`, call `run_strip` to `stripped.pdf`, call typography extraction, write `make_mapping` to `translations.json`, and return Paths under keys `original`, `stripped`, `segments`, `mapping`, `output`. Fixture helpers never derive expected fonts/styles from renderer output. Add a reordered mapping with the first bold run `AHORA ` referencing `s0/r1`, then regular `pague` referencing `s0/r0`.

```python
# tests/typography_fixtures.py
import json
from pdf_translate import run_extract, run_strip

def make_job(work, font_sets):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    source = make_source(work / 'original.pdf')
    stripped = work / 'stripped.pdf'
    run_strip(str(source), str(stripped))
    extracted = run_extract(str(source), str(work), typography=True)
    segments = Path(extracted.segments_path)
    data = json.loads(segments.read_text(encoding='utf-8'))
    mapping = work / 'translations.json'
    mapping.write_text(json.dumps(make_mapping(data, font_sets), ensure_ascii=False),
                       encoding='utf-8')
    return {'original': source, 'stripped': stripped, 'segments': segments,
            'mapping': mapping, 'output': work / 'out.pdf'}
```
- [ ] Add the following regression (in a test method with that job), then run `& $typoPython -m unittest tests.test_typography_retypeset -v` and inspect its red signal.

```python
from pdf_translate import run_retypeset
from pdf_translate.results import MappingError

before = b'prior output marker'
job['output'].write_bytes(before)
with self.assertRaises(MappingError) as caught:
    run_retypeset(str(job['stripped']), str(job['segments']),
                 str(job['mapping']), str(job['output']))
self.assertEqual(caught.exception.refusals['typography'][0]['reason'],
                 'stale-extraction')
self.assertEqual(job['output'].read_bytes(), before)
```

- [ ] Preflight the original digest, extraction binding, complete source-page selection, all font faces/glyphs, associations and document metadata before publication. Compare stripped/source page count, MediaBox/CropBox/rotation and field identities; do not remove source pages that lack translated segments. Reject aliased output/input paths. Source hash does not prove arbitrary stripped graphics; retain the trusted strip + independent visual comparison requirement.
- [ ] Factor existing right-limit/obstacle and glyph/fit helpers into small reusable functions within `retypeset.py`; retain their legacy calculations. For each occurrence compute actual-font widths for the whole ordered sequence at the source size; use the original baseline and available one-line width, uniformly scale all its runs, reject below 0.7 absent its exact ID exception. Use glyph bounds as well as advances to catch italic overhang at crop/obstacle edges. Refuse a row that cannot be safely measured; never enlarge the page or move neighbors.

```python
# Core calculation inside the new path; font_for holds already validated faces.
widths = [font_for[(r.font_class, r.font_role)].text_length(
              r.text, fontsize=source_size) for r in target.runs]
total = sum(widths)
ratio = min(1.0, available_width / total) if total > 0 else 1.0
x = source_x
writer = pymupdf.TextWriter(page.rect)
for run, width in zip(target.runs, widths):
    writer.append((x, source_baseline), run.text,
                  font=font_for[(run.font_class, run.font_role)],
                  fontsize=source_size * ratio)
    x += width * ratio
writer.write_text(page, color=source_color)
```

This loop belongs inside validated preflight/placement, not a standalone replacement renderer. Do not route through HTML or call `fill_textbox`. First scope uses TextWriter; a future Story path needs the design's independent no-wrap/baseline/font/text proof before enabling it. Reject mixed source sizes/colors/baselines, rotation, unsupported clusters/scripts, markers/dot leaders/chrome needing synthesized placement, and new-format merges/overrides/notices. Keep image/vector content and field geometry unchanged.

- [ ] Apply existing metadata retargeting with `document_targets`. Canonicalize the text layer using **every selected class/role face and every placed run**, not only legacy regular/bold. Store per-occurrence source location, target texts/references, selected face identities/digests, actual placed origins, size/scale and authored resolution/scale reasons in the existing result/report. No build record can later stand in for reading the PDF. Complete all refusal checks before saving a new file; cancellation returns `output=None` and `cancelled=True`. Do not return a previous artifact's path as success or delete it under a new global policy. For the optional result data, omit only `typography=None` in serialization; do not introduce a general omission rule that changes old empty/false fields.
- [ ] Test success on the two repeated labels; exact page count including trailing blank pages; changed original; incompatible stripped boxes/rotation/fields; a long target; one occurrence's scale exception not affecting its duplicate; each declared unsupported construct; progress/cancellation; `scale_report=None`; same paths as source; no-new-output on refusal with both absent and existing output. Assert current result serialization remains identical for legacy jobs. Inspect fresh final runs' fonts and baselines and compare source images after strip/rebuild.
- [ ] Run this module, relevant existing placement/metadata/canonical-text tests and both parity probes. Commit as `feat(retypeset): preserve occurrence typography in one line`.

### Task 5: Verify the actual final typography

**Files:** create `pdf-translate/pdf_translate/typography_verify.py`, `tests/test_typography_verify.py`; modify `verify.py:515,1623,2135,2168,2240` and `GATE_NAMES`.

**Interfaces:** `typography_verify.inspect_output(original, final, document) -> GateResult`, returning name `typography`; extend `run_verify`, `verify`, `_execute_verify` with trailing `typography=False` and CLI `--typography`. `MappingDocument` supplies expected targets and source evidence. `scale_report_for` accepts legacy schema 1 and typography schema 2 explicitly; unknown schemas remain errors/diagnostics.

- [ ] Add this missing-context red test and a positive actual-PDF fixture; run `& $typoPython -m unittest tests.test_typography_verify -v`.

```python
from pdf_translate import run_verify

verdict = run_verify(str(job['original']), str(job['output']), typography=True)
check = next(g for g in verdict.gates if g.name == 'typography')
self.assertEqual(check.status, 'REVIEW')
self.assertIn('cannot attest', check.message.lower())
self.assertTrue(job['output'].exists())
```

- [ ] Load mapping/context once through the shared reader. New format auto-selects typography even without the flag. Explicit request without enough context produces REVIEW/cannot-attest; invalid new-format input is an input failure, not SKIP. Preserve default legacy gate/console sequences; append the new name without pretending it is a new general process gate. Use existing one-based `Finding.page` with `where` naming the occurrence/run; typed build refusals remain zero-based as designed.
- [ ] Independently read the final PDF's text trace/raw spans, font resource/program evidence, glyph bounds and origins. Match by source page and expected baseline/ordered advances plus text, not whole-document string presence. Assign a drawn character/run to at most one occurrence; ambiguous duplicates/overlapping geometry cannot attest. Adjacent equal-style output spans may coalesce, differing styles may not. Measure baseline difference at 0.05 pt, page count/assignment, one-line bounds, text coverage, color/size and whole-occurrence uniform scaling; record any below-floor approved exception.
- [ ] Validate actual drawn class/role from the final embedded program; compare selected-face identity for used glyphs even after subsetting. Full-file SHA is not a subset identity: compare supported used-glyph outlines/advances in normalized font units and consistent font metadata. If the embedded format cannot be resolved, REVIEW/cannot-attest; a demonstrable wrong class/role/font or shifted/missing target is FAIL. Never trust the claimed role name, a `/BaseFont` label alone, or the renderer's report. Source resolutions remain visible REVIEW information even if geometry is correct. Keep input ambiguity distinct from actual output mismatch.
- [ ] Build tampered PDFs independently in the fixture helper using explicit TextWriter fonts/positions: same text at the wrong repeated occurrence, swapped bold/regular, wrong serif/sans, all text on the wrong page, baseline +1 pt, extra/missing blank page, clipped italic end. Retain an untouched original build report beside each; verifier must still FAIL or explicitly cannot-attest. Add unknown output-font identity, coalesced equal-style spans, explicit missing mapping/extraction and final font embedding after `field_fonts`.
- [ ] Verify failure remains advisory (file exists; verdict has FAIL, no deletion), and REVIEW honors existing `fail_on_review`. Run this module, `tests.test_verify_report`, `tests.test_consumer_contract`, and both parity probes. Commit as `feat(verify): inspect final occurrence typography`.

### Task 6: Carry occurrences through QA and reviewer input

**Files:** modify `pdf-translate/pdf_translate/qa_check.py:299`, `review.py:66,189,256,497`; create `tests/test_typography_review.py`.

**Interfaces:** existing `run_qa(translations_path, segments_path=None, glossary_path=None)` and `run_review(work, ingest=None, notes=None, generate=True)` remain unchanged. New mapping input goes through `load_mapping`; QA findings add occurrence/run/page context for new jobs only. Review input adds required root `typography={extraction_id,mapping_sha256}` for typography jobs, and optional exact `occurrence_id`/`source_runs` on findings. Ambiguous repeated-core findings require those IDs; preserve legacy review schema and termbase rules.

- [ ] Add two identical source strings at different positions with different target numbers/styles. The number check must produce both occurrence IDs; consistency compares wording separately from style. Do not deduplicate through a dictionary keyed by source. Write the stale-binding test below in a real fixture work directory, then run `& $typoPython -m unittest tests.test_typography_review -v`.

```python
import json
from pdf_translate import run_review

review_path = work / 'review.json'
review_path.write_text(json.dumps({
    'reviewer': {'name': 'Fixture reviewer'}, 'findings': [],
    'typography': {'extraction_id': extraction_id, 'mapping_sha256': '0' * 64}
}), encoding='utf-8')
verdict = run_review(str(work), ingest='review.json', generate=False)
self.assertTrue(verdict.errors)
self.assertTrue(any('mapping' in error.lower() for error in verdict.errors))
self.assertFalse(verdict.wrote)
```

- [ ] Iterate each target with `''.join(run.text for run in target.runs)` for pair/number/language/glossary checks. Adapt consistency aggregation to a sequence of source/target/occurrence records so repeated cores survive; keep the existing dictionary adapter for legacy callers. Style differences alone are not terminology inconsistency. Mark findings with full source and exact IDs, not serialized run-object representations.
- [ ] Generate one source/target row per occurrence with page/location, class/role labels, visible run boundaries, source associations and authored font-resolution explanations. Escape Markdown table characters and literal HTML in the reader artifact while leaving translation text untouched. Include current digests in the generated reviewer template. Extend `ReviewFinding`/`validate` to preserve and validate the new optional occurrence/run identifiers; omit them for legacy serialization. Reject missing/mismatched bindings before accepting findings or appending a termbase; a same-core finding without an ID cannot attest two differently styled occurrences. Valid explicit `term`/`term_target` rules stay strict.
- [ ] Test same-text/different-style rows, special `<`/`>`/pipe text, stale extraction and mapping hashes, missing binding, wrong occurrence, duplicate source-run references, reordered emphasis and wrong reviewer associations. `generate=False` remains read-only; snapshot the work directory to check that no pairs, prompts or termbase changed. Do not change general `finish` handling of invalid review here; A01 is still the prerequisite.
- [ ] Run this module, `tests.test_review`, affected QA tests and parity. Commit as `feat(review): retain typography associations through QA`.

### Task 7: Connect the CLI and pipeline without alternate readers

**Files:** modify `pdf-translate/pdf_translate/pipeline.py:100,159,207,303,393,439`, relevant `_main` functions in `extract_segments.py`, `prepare_font.py`, `retypeset.py`, `verify.py`; create `tests/test_typography_pipeline.py`. Thin `scripts/*.py` wrappers should remain thin and need no second implementation.

**Interfaces:** `pipeline init --typography`; extractor `--typography`; font preparation `--font-class serif|sans --font-role regular|bold|italic|bold_italic`; retypesetter `--original`; verifier `--typography`. `pipeline from-cores --work DIR` detects extraction mode; `pipeline rebuild ORIGINAL OUT --work DIR` passes source/mapping/extraction automatically only for new-format jobs. Existing legacy rebuild correction remains A06.

- [ ] Add a subprocess test of the supported command sequence below; first test the unauthored scaffold, then populate it explicitly using the fixture mapping. Run `& $typoPython -m unittest tests.test_typography_pipeline -v` red before editing wrappers.

```powershell
& $typoPython scripts/pipeline.py init ../runs/typography/job/original.pdf --work ../runs/typography/job --typography
& $typoPython scripts/pipeline.py from-cores --work ../runs/typography/job
& $typoPython scripts/pipeline.py rebuild ../runs/typography/job/original.pdf ../runs/typography/job/out.pdf --work ../runs/typography/job
```

- [ ] In opt-in extraction, include an extraction reference/digest in `to_translate.json` for scaffolding. Resolve its adjacent `segments.json`, verify its digest and emit **every occurrence** with `runs=[]`, empty font sets, an unauthored language and null required document targets. This deliberately incomplete template must refuse build until authored. Keep the existing no-overwrite behavior unless `--force` is explicit. Do not insert plausible translations or legacy fallbacks.
- [ ] Carry flags through the existing wrappers, selecting the new path via the shared reader. Reject missing flag values with a named usage error. On typography rebuild, original/mapping/segments are fixed to that work directory's bound inputs; conflicting forwarded verification flags refuse rather than override them. Forward a target-script fill value explicitly in delivery examples and verify the actual final artifact after field-font embedding/finish.
- [ ] Audit every mapping reader using the search below. Adapt text/metadata collection inside verify to the normalized new targets instead of passing a synthetic `translations` dictionary that collapses duplicates. `propose-merges` and `merge-mappings` cannot operate losslessly on this first format: reject any typography/unknown-format input before writing and leave all inputs/outputs unchanged. Handle mixed legacy/new inputs the same way. Unknown-format errors must not become a success with zero pairs or zero glyphs in QA/review/font preparation.

```powershell
rg -n "json.load|json.loads|translations|fonts" pdf_translate
```

- [ ] Test CLI/library error equivalence, missing original, duplicate/unknown mapping format, stale extraction, all incompatible helpers, no-overwrite scaffold, conflicting rebuild flags and refusal with a prior PDF/report present. Tests must inspect both exit codes and produced files, not only log messages. `finish` remains packaging plus its existing review policy; no new automatic verifier policy is hidden inside it.
- [ ] Run this module and `tests.test_pipeline`, then both parity probes. Commit as `feat(pipeline): carry typography context across commands`.

### Task 8: Prove the supported matrix independently

**Files:** create `pdf-translate/tests/test_typography_acceptance.py`, `dev/probes/typography_acceptance.py` and actual-run evidence in `docs/reviews/2026-09-20-typography-implementation.md`; modify `.github/workflows/tests.yml` to include new tests if its module list is still explicit.

**Interfaces:** the probe takes `--work DIR --fonts DIR`, refuses a nonempty output directory and emits original/final PDF pairs, sanitized mapping/extraction/result/verifier JSON and source/final PNGs. Its summary lists case, source/target language, expected class/role, actual inspected class/role, page/baseline/fit result, selected font hashes and command exit codes. No fabricated coverage percentage. Probe cases call the documented library/CLI functions; they do not introduce a new runtime entry point.

- [ ] Add an acceptance test that builds Task 1's repeated-label fixture in the new mode, runs final verification, requires the `typography` result to be PASS when every resource/evidence is resolvable, and checks that the source and output each have exactly one page. Add an unresolved-source-resolution case whose expected result is REVIEW, not PASS.

```python
from pdf_translate import run_retypeset, run_verify

built = run_retypeset(str(job['stripped']), str(job['segments']),
                     str(job['mapping']), str(job['output']),
                     original=str(job['original']))
self.assertEqual(built.pages, 1)
verdict = run_verify(str(job['original']), str(job['output']),
                     translations=str(job['mapping']), segments=str(job['segments']),
                     typography=True)
self.assertEqual(next(g for g in verdict.gates if g.name == 'typography').status,
                 'PASS')
```

- [ ] Run `& $typoPython -m unittest tests.test_typography_acceptance -v`; a positive path must fail for an actual unsupported requirement if work is incomplete, not be converted to SKIP. Add the complete design acceptance matrix: Latin all four roles in both classes; horizontal JA/zh-Hans class and available-role success plus missing-role refusal; bilingual reordered emphasis; duplicate/foreign/stale IDs; original/source-style changes; narrow one-line limits; every declared unsupported construct; final-PDF tampering; source/final page geometry and fields.
- [ ] Add old-runtime subprocess cases against the recorded v54 `9675c6196c14eb2a2d37d34e371391eb1955a386` and v56 `a5629fbd6bc084f9ab849ae3db74992c15807fcc` library snapshots. Run new-format mappings without adding legacy root keys, assert nonzero build status and no fresh PDF, then assert the consumer capability check refuses before old QA/review. Old reader rejection alone is not a capability check. Use clean in-repo snapshots/worktrees, never the product checkout.
- [ ] A verifier who did not write extraction/font/placement code runs the probe and selected tests on the actual candidate, inspects source/final rasters, font identities and exact commands/outputs, and records defects. The independent pass must include duplicate labels, italic overhang, CJK localization and the reordered phrase; a qualified reader still needs to judge language/emphasis semantics. Do not use glyph count as proof of semantic emphasis or mark positioning.

```powershell
& $typoPython ../dev/probes/typography_acceptance.py --work ../runs/typography/independent --fonts tests/fonts
& $typoPython -m unittest tests.test_typography_acceptance tests.test_typography_verify -v
```

- [ ] Run full library discovery, canary and both parity comparisons on the actual candidate; record counts, skips, versions and exact SHA. Run configured Windows/Linux and Python support jobs when available; unavailable CI/host resources remain explicitly unverified. Fix feature defects, repeat affected checks, and obtain independent reruns of changed rendering/font/layout behavior. Commit tests/probe/evidence as `test(typography): verify occurrence style preservation` only after actual evidence exists.

### Task 9: Publish the capability to both skill hosts

**Files:** modify `pdf-translate/pdf_translate/__init__.py`, all four version sources, `tests/test_verify_report.py::VersionLockstepTests`, `pdf-translate/SKILL.md`, both READMEs, `references/{translations-format,consumer-guide,gates}.md`; create `references/typography.md`. Update the existing request inbox, decisions, handover and implementation evidence. No second roadmap.

**Interfaces:** export immutable `MAPPING_FORMATS`. Until the complete new-format workflow is verified, its value is `('legacy',)`; add `typography-1` only when the capability checks above have passed. The tuple describes implemented format support, not public-release readiness or arbitrary-document quality. CJK role combinations without suitable real fonts remain refused, with their unverified positive cells disclosed.

- [ ] Add a failing import/discovery test and an example that tests the installed runtime, not a checkout version string:

```python
import pdf_translate

formats = getattr(pdf_translate, 'MAPPING_FORMATS', ())
if 'typography-1' not in formats:
    raise RuntimeError('This installed engine does not support typography-1')
```

- [ ] Run the new capability test before exporting. Once Task 8's supported paths are verified, export the tuple and document extraction, source-font uncertainty, occurrence authoring, class/role font preparation, QA/review bindings and final-file verification. Show repeated-core/reordered-emphasis examples and the same-page/one-baseline support boundary. Copy runnable examples from verified probe artifacts; do not write an imaginary API example.
- [ ] Bump versions only when implementation is ready to be exposed, applying the existing four-source lockstep policy to the then-current reconciled version. Do not reserve v59/v62 now or overwrite local v61 work in another checkout. Stage internal commits as unpublished development until that version is selected. Keep legacy serialization/schema 1; document typography report schema 2 and new optional result data. No speculative dependency floor, public-ready or app-adopted claim.
- [ ] Validate actual installable artifacts and run one bounded typography workflow in **Claude and Codex** with the source fixture, authored targets and genuine fonts. Record actual host/runtime/package paths, command traces, produced files, final verification and independent image inspection. Skill discovery or frontmatter validation alone does not satisfy this check. Use task-local installation directories; if a host is unavailable, preserve that unverified status and do not call dual-host acceptance complete. No cross-repo installation or app pin changes without separate authorization.
- [ ] Run the documented examples from the installed artifacts, the version-lockstep test and final full suite/parity when the version/docs integration changes require it. Link the exact candidate commit and evidence from the request inbox; keep A01 and other public-readiness blockers visibly open. Commit as `docs(skill): expose verified typography workflow`. Stop at a local reviewed branch; ask separately before any push/merge/release.

## Design coverage and plan self-review

| Approved design requirement | Task(s) | Required evidence |
| --- | --- | --- |
| §1 additive public surface, old-reader boundary | 2, 7–9 | Legacy parity; real old-version refusal; installed capability check |
| §2 exact source observations/offsets/resolutions | 1–3 | Known source font resources; exact reconstruction; ambiguous metadata cases |
| §3 source/extraction identity and stripped structure | 1–2, 4 | One-input mutations; moved paths; complete pages and field identities |
| §4 reordered runs, coverage, strict shape, metadata and fonts | 2–4, 6 | Repeats, duplicate keys, omitted emphasis, separate title/outline, charset/role checks |
| §5 one-line placement and explicit refusals | 4, 8 | Whole-run scale, baseline/page/obstacle bounds, positive refusal fixtures |
| §6 results, actual final verification, QA/review, lifecycle boundaries | 4–7 | Schema/legacy parity, tampered PDFs, current bindings, no stale success |
| §7 real independent and dual-host acceptance | 8–9 | Independent commands/rasters/reader pass and both host traces |
| §8 ownership, B1 deferral and approval boundary | All | Scoped diff and linked state; no app implementation or adoption claim |

Self-review performed while writing this plan: checked source function anchors, public call compatibility, role-key spelling, default extraction lookup for font preparation, all mapping readers including helper commands, optional result serialization, partial-page refusal, source/output evidence separation and backlog boundaries. Code blocks are implementation/test instructions, **not executed production changes or passing test evidence**. Remaining resource uncertainty is explicit: genuine font coverage, independent human language review and actual host availability are execution acceptance requirements.

One **source-only** planning check did run: the `make_source` block above generated one page with two `Pay NOW` lines and exactly the four asserted Times/Helvetica font identities. Saved source: `runs/typography-plan-2026-09-20/source-fixture.pdf`. This validates the proposed source fixture, not typography extraction, translation or preservation. Python blocks were syntax-checked; those checks do not execute the future APIs.

Primary references checked during planning: [OpenType OS/2 metadata](https://learn.microsoft.com/en-us/typography/opentype/spec/os2) informs conservative metadata handling; [PyMuPDF TextWriter](https://pymupdf.readthedocs.io/en/latest/textwriter.html) and [page text tracing](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_texttrace) inform placement/inspection; [Unicode text segmentation](https://www.unicode.org/reports/tr29/) defines why codepoint boundaries alone cannot prove safe clusters. These references do not replace testing the installed backend or qualify an unsupported font/script as accepted.

## Execution choice after plan review

**Recommended: native execution with an independent final rendering reviewer.** The nine tasks depend closely on the same occurrence/format interfaces, so keeping implementation in one session reduces repeated context and interface drift. An independent real-run rendering/font/layout review still applies; use a qualified reader for language semantics and obtain per-change reruns if that review finds defects.

Alternative: a fresh implementing subagent and reviewer for each task, sequentially, followed by the whole-branch independent acceptance pass. This costs more fresh context but gives earlier independent review at each boundary. Neither choice authorizes a push, merge, app edit or release. Review this plan and select the execution method before any implementation begins.
