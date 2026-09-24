# Non-Japanese adoption: library typography disposition

20 September 2026 · requirements/evidence response; no implementation authorized

**Blocked on a library capability gap for the stated typography requirement.**
No delivered, documented API examined preserves both source serif/sans class
and meaningful within-line bold/italic distinctions end to end. Four role files
and successful core placement do not establish that capability. The product's
requirement stays intact; exact reuse of original font files is not needed.
This gap is separate from B1 wrapping and is not restricted to a target language.

## 1. APIs and availability

| State | Exact revision | Available entry points and disposition |
| --- | --- | --- |
| App-reported installed v54; source independently inspected here | `9675c6196c14eb2a2d37d34e371391eb1955a386` | `pdf_translate.extract_segments(src, outdir='.', gap=12.0, pages=None)` and `pdf_translate.retypeset(stripped, segf, trf, out)`. Four font roles and authored inline emphasis are documented; the full requirement is unsupported. |
| Current remote default branch, v56 | `a5629fbd6bc084f9ab849ae3db74992c15807fcc` | Same entry points and same extraction behavior. Available from Git; not evidence that the app adopted it. |
| Committed v58 on open PR #13, stacked on #12 | `1d4f9707c4d9934fbc88d8f25576ac304b9bb139` | Adds `run_extract(src, outdir, *, gap=12.0, pages=None)` and `run_retypeset(stripped, segf, trf, out, *, progress=None, cancel=None, scale_report=..., resource_root=None)`. These adapters add structured results/refusals and job controls, not retained source-style runs or family classes. |
| Current local working tree | HEAD above, uncommitted metadata v61 | Recent documentation corrections only for this capability; extraction and retypesetting files are byte-identical to HEAD. No additional available typography API. |

Read-only GitHub checks found PR #12 OPEN at
`abc47674019aaed8f61b716b83e3d289e38d1f1c`, PR #13 OPEN at the v58 revision above,
and no GitHub releases or tags. No newer adoption, delivery pin or release is
implied. The app's installed pin and route selection are its reported state;
this session did not inspect the product installation or source.

What exists is useful but narrower: the mapping documents one global set of
`regular`, `bold`, `italic`, `bold_italic` font files. Uniform segments select a
role; caller-authored `<b>/<i>` or `<strong>/<em>`, the bold-lead separator `‖`,
and explicit override parts can request some target emphasis. Those are manual
presentation controls. They do not recover discarded source span boundaries or
provide automatic semantic alignment of translated emphasis. They also do not
provide separate source-class families for mixed serif/sans content.

## 2. Source-style and occurrence association

Extraction does emit per-segment `id`, `page`, `bbox` and `origin`. It is
incorrect to say that no occurrence information exists. However:

- Nearby source spans are grouped without a style-boundary split; bold/italic
  are ORed across the group. The serialized segment lacks the original styled
  span sequence and font/family class. The ID is sequential in that extraction,
  not a documented identity stable across different extraction inputs/options.
- `translations` maps normalized **core text** to one target string, reused for
  every occurrence. Each occurrence retains its own aggregate geometry/booleans,
  but there is no target-run association to original source style spans and no
  documented translation selector by segment ID.
- Overrides match **page + substring** and use the first matching override for
  each matching segment. Identical text repeated on the same page is not
  disambiguated by its ID/bbox. Explicit part positions do not change selection.
- Merges match **page + ordered line text**, scanning for matches; they likewise
  do not expose an occurrence-ID selector. They are not a solution to this
  typography requirement or authorization to resume B1.

The source for this disposition is the library itself: grouping and segment
serialization in [extract_segments.py](../../pdf-translate/pdf_translate/extract_segments.py),
core deduplication in the same module, role/inline/override/merge handling in
[retypeset.py](../../pdf-translate/pdf_translate/retypeset.py), and the documented
[translations format](../../pdf-translate/references/translations-format.md).
At committed v58, relevant anchors are extraction lines 583–657 and 720–744;
placement lines 788–796, 854–860, 903–912, 1144–1176 and 1206–1263. The mapping
document is unchanged across the three inspected commits.

## 3. Missing capability and present reporting

The missing end-to-end information is **source family class and ordered style
runs, associated with an unambiguous occurrence, carried into authored target
runs and consumed by placement**. Translation can reorder words, so copying
source character offsets or splitting into independent word translations is not
an adequate substitute for an explicit association. Unknown/ambiguous source
class or style association needs an observable unsupported result; it must not
be silently described as preserved.

Today there is no dedicated extraction warning, build refusal or verification
finding for these general typography losses. Existing missing-glyph/fit/mapping
refusals and font-role fallback notices cover different conditions. The
verifier's script-specific shaping/Han-form checks are not general serif/sans or
source-emphasis parity checks. Later structured exception APIs do not create a
new refusal for a capability the implementation does not check.

### Independent fixture evidence

A one-page PDF authored here contains a Times-Roman heading, a Helvetica label,
and two occurrences of `Pay NOW`: one with only `NOW` oblique and one with only
`NOW` bold. Raw source extraction asserted the actual four font names before
checking the library output. No product PDF, code or probe was accessed.

Ran from the repository root with the existing environment (PyMuPDF 1.28.2):

```powershell
$env:PYTHONUTF8='1'
& '.\pdf-translate.venv\Scripts\python.exe' dev/probes/typography_capability_probe.py --work runs/typography-capability-2026-09-20
```

Exit 0, identical observations in all three Git snapshots:

```text
4 occurrence IDs, 3 unique cores
2 mixed lines flattened to whole-segment italic/bold flags
No family or original-span records; 0 extraction warnings
extract_segments function AST identical across all three commits
```

[Saved source/segment evidence](data/2026-09-20-typography-capability.json) and
[probe](../../dev/probes/typography_capability_probe.py) make the result inspectable.
Snapshots and source PDF remain under ignored `runs/`. Use a new `--work` folder
inside `runs/` for another run; the probe refuses to reuse an evidence directory.
This is an extraction/representation test, not a translated-output visual test,
customer-corpus acceptance or new regression claim. It independently establishes
why the ordinary pipeline lacks the information needed for the requirement.
The app's eight-page/25-core successes, rendered typography observations and five
compatibility failures remain app-reported evidence, not reverified results here.

## 4. Smallest prerequisite and ownership

**Library-owned prerequisite:** one bounded end-to-end typography capability
that retains source class/style runs, permits target runs to refer to the exact
source occurrence, and places the selected class and emphasis without silent
loss. Its acceptance must distinguish identical repeated text with different
styles, regular prefixes with emphasized tails, and serif/sans segments; an
unknown or ambiguous association must be explicitly reported. Existing placement
can be assessed for reuse when that work is authorized. Extraction metadata alone
would not close the prerequisite. No schema, new renderer, implementation plan
or delivery revision is proposed as already accepted here.

**App-owned integration:** target/alias resolution, target-specific font files
for the supported classes/roles, translation orchestration using the eventual
style/occurrence representation, lifecycle and notices, pin adoption and migration
evidence, including its five compatibility failures. Selecting four global role
files cannot by itself supply the missing library behavior. The app should not
build a second extractor/renderer to compensate for this reusable capability gap.

Current APIs can run bounded probes for suitable documents; they do not justify
unrestricted non-Japanese routing under the unchanged typography promise. No
additional product data packet is needed for this disposition. Prioritize the
library prerequisite with Rodrigo before implementation; B1 stays separately
deferred. This response sends no message and makes no app-task assignment.
