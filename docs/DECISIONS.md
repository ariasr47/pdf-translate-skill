# DECISIONS

Rulings on this repo's behaviour, scope or method, so they outlive the
session that made them. See `AGENTS.md` Rule 3.

A decision is never edited to reflect new information. If a later finding
reverses one, **append a new row** that says so and leave the old row in
place — the history of "we used to think X" is part of the record.

## Format

`date | decision | why | what would reverse it`

- **date** — ISO, the day the ruling was made (or measured, for a finding
  that hardens into a ruling).
- **decision** — the ruling itself, stated as something an agent can act on
  without re-deriving it.
- **why** — the evidence or reasoning, in enough detail that a skeptic could
  check it without you.
- **what would reverse it** — the specific observation that would make this
  wrong. Not "if we learn more" — the actual falsifying condition.

## Worked example

| date | decision | why | what would reverse it |
|---|---|---|---|
| 2026-09-15 | The glyph-count shaping tell (unshaped-vs-shaped glyph count from `verify.py`) is valid **only** for conjunct-forming Indic scripts, and only on probe strings that actually contain a merging cluster. It must never be used to claim a mark-stacking script (Thai, Lao, Khmer, Hebrew+niqqud) or Arabic is "verified shaped." | Measured across five probes, PyMuPDF 1.28.0, `tests/fonts/`: Devanagari क्षत्रिय 8→4 glyphs (0.50) and हिन्दी 6→5 (0.83) show the tell; कमल 3→3 (1.00) shapes correctly but is indistinguishable from broken output; Arabic مكتبة 5→**8** glyphs (1.60) — shaping *adds* glyphs, so the same test direction is backwards; Hebrew שָׁלוֹם+niqqud 7→7 (1.00) — mark stacking never changes glyph count. Full table and the `insert_text(fontfile=...)` font-fallback trap that produced two false positives: `AGENTS.md`. | A probe string in one of the excluded scripts that reliably changes glyph count under correct shaping (and stays constant under a known-broken render) would reopen the question for that script specifically — it would not restore the tell as a general rule. |

## Open ledger

Add new rows above this line, newest last. Do not renumber or reorder
existing rows when appending.
