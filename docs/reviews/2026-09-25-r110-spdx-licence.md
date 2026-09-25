# R-110: the package licence is an SPDX expression — 25 September 2026

**Assignment.** R-110 is the next of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-110 in
`docs/REVIEW-2026-09-24.md`, and the assigned behaviour reads "SPDX licence
form in `pyproject.toml`".

It ships as v73, stacked on #42 (R-42, v72). The bump follows the bar's
rule: a version bump for every shipped change. The built package's metadata
changes, unlike the CI-only R-69 and R-97.

## The defect

`pyproject.toml` declared `license = {text = "MIT"}`, the TOML-table form.
setuptools deprecates it, and warns on every build step:

> `project.license` as a TOML table is deprecated … By 2027-Feb-18, you
> need to update your project and remove deprecated calls

The replacement is PEP 639's `license = "<SPDX expression>"` with
`license-files`, which setuptools accepts from version 77. The build
requirement said `setuptools>=61`.

**Reproduced before building.** The build was run with `uv build --offline`,
using only the local cache, which holds setuptools 84.0.0; nothing was
downloaded. It emitted 4 `SetuptoolsDeprecationWarning` lines, and the
wheel's metadata read `License: MIT`.

## The change

`pdf-translate/pyproject.toml`:
- `license = "MIT"` and `license-files = ["LICENSE"]`;
- the build requires `setuptools>=77`.

The package has no licence classifier; PEP 639 forbids one beside an
expression.

**Records:** the quick-wins row in `docs/REQUESTS-from-product.md`. The
version goes from 72 to 73. No DECISIONS row: this follows the packaging
standard and makes no ruling on the library's behaviour.

## Red, then green

`tests.test_verify_report.PackagingMetadataTests` reads `pyproject.toml`
with `tomllib`. It requires:
- the SPDX string;
- `license-files` naming an existing `LICENSE`;
- `setuptools>=77`;
- no `License ::` classifier.

**Red:** `{'text': 'MIT'} != 'MIT'`. **Green:** the module's 32 tests pass.

**The built package**, from the same offline build:

| | v72 | v73 |
|---|---|---|
| deprecation warnings | 4 | 0 |
| licence field | `License: MIT` | `License-Expression: MIT` |
| `License-File` | `LICENSE` | `LICENSE` |
| wheel files | 29 | the same 29 |
| sdist files | 56 | the same 56 |

- The bundled `LICENSE` is byte-identical.
- Only three wheel files differ: `METADATA` (the licence field and version),
  `RECORD` (their hashes) and `pdf_translate/__init__.py` (the version).

## Suite

These are CI's commands, run on macOS on `d23a202`:

| step | result |
|---|---|
| suite | 745 tests: 1 failure, 1 expected failure |
| canary | 15, OK |
| repository | 6, OK |
| eval fixtures | exit 0 |

- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.
- No independent pass ran. This is packaging metadata, not rendering,
  shaping, fonts or layout, and the build artifacts above are the evidence.

## The app's route

The app's session checked on 25 September. v73 builds there at adoption,
and nothing reads the licence field.
- **How it installs the library.** `apps/api/pyproject.toml` pins
  pdf-translate as a uv git source (`[tool.uv.sources]`, v54's revision,
  subdirectory `pdf-translate`). CI installs it with a locked `uv sync`, and
  the image with `uv sync --frozen --no-dev`.
- **Nothing blocks the new build requirement.** No `no-build-isolation`,
  build constraint or extra build setting appears anywhere. So uv builds the
  git source in an isolated environment and fetches `setuptools>=77`.
- **Nothing reads `License` metadata.** There is no SBOM or licence-listing
  step.
