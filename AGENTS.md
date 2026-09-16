# AGENTS.md — pdf-translate (skill repo)

*For any agent working in this repo. Read `pdf-translate/SKILL.md` first if
you have not — this file adds three rules on top of it, nothing else.*

This repo is the upstream: an MIT-licensed, provider-neutral PDF translation
library, published as both a Claude skill and (per
`docs/BRIEF-core-library-step1.md`) an importable package. It has no council,
no gates, no contracts, no manifests — that machinery belongs to consumers,
not to a public library. Do not add any of it here. Three rules, and nothing
more.

## Licence — read this before importing anything

**This repo is MIT. The consuming product (`pdf-translator`) is heading to
AGPL-3.0.** MIT code may flow downstream into that product freely. The
reverse is a licence violation: AGPL-3.0 code copied into this MIT repo
would either relicense the repo by accident or ship under a licence the
copyright holder never granted.

- **Never copy code from `C:\Dev\pdf-translator` into this repo** — not a
  function, not a snippet, not "just the algorithm, rewritten a little."
- If something in the product looks useful here, it is a *behaviour*, not a
  patch. File it in `docs/REQUESTS-from-product.md`, describing what the
  behaviour should do and why. Reimplement it independently against this
  repo's own tests and corpus.
- This applies in both directions of trust: an agent that has read the
  product's source is not a safe channel for its code, even paraphrased.

## Rule 1 — Independent verification

Any change to rendering, shaping, fonts or layout must be verified by a pass
that did **not** write the code — ideally on a different model — and that
pass must cite a real run: a command and its output. A code reading is not
verification.

This is not process for its own sake. `verify.py`'s own comment on why the
shaping gate exists says it plainly:

> Devanagari and Thai have none: the shaper writes glyph ids, so a broken
> conjunct and a correct one look the same in the text layer.

A session that writes shaping code and then judges its own output has no
independent signal — it is reading the same glyph ids it just wrote, and a
broken conjunct is invisible from that seat. Someone (or something) else has
to run it and look.

## Rule 2 — Acceptance criteria are observable outcomes with a verify-by method

Every acceptance criterion states what a run produces and how to check it —
never an intention.

- Bad: "handles Devanagari correctly."
- Good: "for probe string क्षत्रिय rendered through the Story engine, glyph
  count (4) is less than codepoint count (8) — verify by
  `docs/reference/probes/probe-shaping-tell.py` in the pdf-translator repo."

### Measured facts (shaping-tell), 2026-09-15 — do not re-derive, do not alter

PyMuPDF 1.28.0, fonts from this skill's own `tests/fonts/`:

| probe | script | codepoints | unshaped glyphs | shaped glyphs | ratio |
|---|---|---:|---:|---:|---:|
| क्षत्रिय | Devanagari (conjunct) | 8 | 8 | 4 | 0.50 |
| हिन्दी | Devanagari (conjunct) | 6 | 6 | 5 | 0.83 |
| कमल | Devanagari (no conjunct) | 3 | 3 | 3 | 1.00 |
| مكتبة | Arabic | 5 | 5 | **8** | **1.60** |
| שָׁלוֹם | Hebrew + niqqud | 7 | 7 | 7 | 1.00 |

The glyph-count tell works for **conjunct-forming Indic scripts only**, and
only on probe strings known to contain a merging cluster (कमल shapes
correctly but is indistinguishable from broken output — 1.00 either way). It
is **backwards** for Arabic, where shaping *adds* glyphs (isolated
presentation forms split, ratio > 1). It is **blind** to mark-stacking
scripts — Thai, Lao, Khmer, Hebrew+niqqud — where marks stack onto a base
glyph without changing the count. Those scripts have no cheap mechanical
tell; they need reference rasters or human review. A breadth sweep must
never report a mark-stacking script as "verified" on glyph count alone.

**Method warning.** `insert_text(fontfile=...)` **without** `fontname=`
silently falls back to Helvetica and draws U+00B7 (a middle dot) per
codepoint. It produced a convincing, entirely meaningless "shaped
correctly" result twice before this was caught. Any shaping check must
assert which font actually drew the run, not just that *a* run was drawn.

## Rule 3 — Decisions outlive the session

Every ruling on this repo's behaviour, scope or method gets a row in
`docs/DECISIONS.md`: date, decision, why, what would reverse it. A chat
thread is not memory here — the file is. See that file for the format and a
worked example (the shaping-tell narrowing above, as a decision).

## Out of scope, on purpose

No SPEC.md, no INTERFACE_CONTRACT.md, no council roles, no build gates, no
QA receipts. This is a library with tests, a corpus, and three rules. If a
task seems to need more ceremony than that, it belongs in the product repo,
not here.
