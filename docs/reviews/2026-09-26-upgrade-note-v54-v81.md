# The v54 → v81 upgrade note — 26 September 2026

**Assignment.** The product requested it on 26 September as the first of its
ordered items: the app adopts v81 as one change within days, right after its
engine-boundary build lands. Rodrigo assigned it the same day. It ships as
v82, docs only, stacked on #54.

**Deliverables:**
- `pdf-translate/references/upgrading.md`: every change a Python consumer
  sees from v54 (`9675c61`, the app's pin) to v81 (`0d58202`). Each gives the
  version it first shipped in, whether it moves output bytes, and what to do.
- A test that the note has a section for the current version, so every
  later version appends one.
- Links from SKILL.md's reference list and from the consumer guide.
- A `v81.0.0` tag at `0d58202`, the repository's first tag. It is created
  locally, and its push waits for Rodrigo's approval.

## How the note was built

190 non-merge commits and about 6,000 changed lines of `pdf_translate/` lie
between the two commits. The research ran as a workflow of four agents:
- **Three read-only researchers,** one per version range (v55–v63, v64–v72,
  v73–v81).
  - Each listed every consumer-visible change that first shipped in its
    range.
  - Each read the version from `pyproject.toml` at the introducing commit.
  - Each cited a commit and a `file:line` in the v81 tree, or an evidence
    document.
  - Several ran probes on archive copies of older trees, for example a v63
    and a v81 build of `corpus/rotated.pdf`.
- **One adversarial verifier.** It tried to refute each entry against the
  code, and looked for changes nobody had listed. It also checked the
  product's 14-item list.

**Results:**
- **50 entries:**
  - 40 confirmed;
  - 10 corrected, with the corrections applied in the note.
- **2 dropped,** because a v54 → v81 consumer cannot see them:
  - a crash in an unreleased branch commit, fixed before its PR merged;
  - a ResourceWarning in `run_review`, which did not exist at v54.
- **1 change nobody had listed** was added: `qa_check` reading typography-1
  mappings (v59).
- **The product's 14 items** are all confirmed at the versions it gave. The
  one caveat is `requires-python`: it landed under 58.0.0, but only 59 is
  guaranteed to carry it.

The entries, the verifier's verdicts and the researchers' skip notes are in
`docs/reviews/data/2026-09-26-upgrade-note/verified-entries.json`.

## One finding in shipped code

**The verifier found a behaviour change v80's records missed, and it was
reproduced here.** Legacy verify's `/Lang` rule is "the mapping's `lang`
starts with the stored tag". v80 reads the stored tag whole, not through
PyMuPDF's shortening getter:

| mapping `lang` | stored `/Lang` | v79 | v81 |
|---|---|---|---|
| `es` | `es-US` | pass | FAIL |
| `es-US` | `es` | pass | pass |
| `es` | `es` | pass | pass |
| `es` | `fr` | FAIL | FAIL |

The verifier also measured `fr-CA` against a stored `fr-FR`: pass on v72,
FAIL on v81.

v80's DECISIONS row says the legacy comparison is unchanged. That is true
for a stored tag that is shorter than the mapping's, and false for one that
is longer or has a different region. The product had asked for the
comparison to stay unchanged.

**How far it reaches:** a v80+ build always stores its own mapping's exact
tag. So the change bites only a file whose `/Lang` was set some other way,
and the app runs no library verify. The note states it under "A known
issue". It is filed on the `/Lang` row for a fix, placed after this note.

## The tag

`v81.0.0` is an annotated tag at `0d58202` (`main`, v81), as the product
asked. It is the repository's first tag.

## Suite

CI's commands on macOS, on this change:
- **Suite:** 791 tests (789 on v81, plus the 2 new docs tests), with 0
  ResourceWarnings. The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is item 3's expected failure.
- **Canary, repository tests and eval fixtures:** all exit 0.
- **The current-version test** fails at v81, whose note section is v82, and
  passes at v82.
