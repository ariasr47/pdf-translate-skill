# Canary run 3 — 3 September 2026

Same one-line prompt as runs 1 and 2 (`dev/canary/README.md`), plus the
same three environment sentences: the work directory, the venv
interpreter on this Mac, and no writes outside the directory (with a
`DELIVERY.md` requested). Isolated directories, run in parallel, no
coaching. Fixture: `dev/canary/fixtures/permission_form.pdf`, 2 pages,
regenerated. Target: Spanish, as in run 2. Skill at `metadata.version`
**45** — the first canary on rows 24–29 and on P7's notice channel.

Axis 3 and the gates machine-checked with `dev/canary/score.py` and a
neutral `verify.py`; the rest read from each run's delivery, notes and
renders, with my own look at every page.

| | Identity | Lookup | Identifiers | Visual | Honest | Total | Cost |
|---|---|---|---|---|---|---|---|
| **Opus 5** | 1 | 1 | 1 | 1 | 1 | **5** (run 2: 5) | 177k tok, 67 calls, 12 min |
| **Sonnet 5** | 1 | 1 | 1 | 1 | 1 | **5** (run 2: 4) | 169k tok, 74 calls, 12 min |
| **Fable 5.1** | 1 | 1 | 1 | 1 | 1 | **5** (run 2: 5) | 190k tok, 52 calls, 12 min |

Three runs, ~536k tokens, twelve minutes each in parallel. Haiku 4.5 was
not run: run 2 scored it 0/5 with every miss in text P3 had not moved, so
it is a canary subject, not an author, and re-measuring it costs money to
learn nothing.

## What this run was for: did P7 land?

**Yes, and it is the clearest result of the three canaries so far.**

| | run 2 | run 3 |
|---|---|---|
| wrote their own notice script | 4 of 5 | **0 of 3** |
| used `notices` in `translations.json` | 0 (Opus put the text in `translations` so the subset covered it) | **3 of 3** |
| used `merges[].box` | 0 — the key did not exist; three runs shrank or declined the merge | **3 of 3** |
| shipped something below source size | 2 (0.81×, 0.91×), unmentioned | **0** — `scale_report.json` is `[]` in all three |
| null core where an override covers it | 0 — the key was rejected | 2 of 3 |

Rows 24–29 and P7 all held. Nobody hit a ligature, nobody hard-wrapped a
paragraph at the source's line breaks, nobody shrank a right-anchored
label, and the quoted `/Title` was a kept note in all three
(`note: 1 source-language run(s) kept…`).

## Gates, measured independently

Neutral `verify.py` on each deliverable, then again as each run invoked it:

| | neutral | as invoked | identifiers | qa_check |
|---|---|---|---|---|
| Opus 5 | exit 1 — the disclosed school name | **exit 0** | 4/4 | 0 err, 1 warn |
| Sonnet 5 | exit 1 — the same name, twice | **exit 0** | 4/4 | 0 err, 1 warn |
| Fable 5.1 | **exit 0**, 15 PASS | exit 0 | 4/4 | 0 err, 0 warn |

Opus and Sonnet kept `Riverside Elementary School` and passed
`--allow "Riverside Elementary School"`, disclosing it. Fable translated
the issuer's name to *Escuela Primaria Riverside* and quoted the English
title bilingually in the notice, so it needed no allowlist — a different
judgment, defensible, and disclosed.

## What it found

**Two defects, both in code written the same day, and one of them found
by two models independently.**

1. **`prepare_font.py` does not know about rows 29 or P7** (row 30).
   `chars.update(v)` raises `TypeError: 'NoneType' object is not
   iterable` on a `null` core — the very thing row 29 made legal — and
   the charset never reads `notices[].text`, so a character used only in
   the notice is missing from the subset and retypeset then FAILs the
   glyph check. Reproduced directly: a null core raises; a notice
   containing `ó` and curly quotes subsets without them. Opus worked
   around it with a hand-built charset file; Fable rewrote its notice with
   straight quotes.
2. **A bold lead-in is silently regular when `fonts.bold` is the regular
   face** (row 31). Sonnet asked for `bold_lead: true` and pointed
   `fonts.bold` at the same subset as `fonts.regular`; the notice's lead
   rendered regular and nothing said so. Fable hit the same thing, caught
   it by eye and added a real bold face. Visible in the page-1 renders
   side by side.

Also noted, not a row: `retypeset.py`'s docstring says document metadata
retargets "/Lang (and dc:language in XMP)", but a source with no XMP
packet gets none created — correct behaviour, imprecise sentence. Opus
raised it; checked and true.

## Per-run records

`2026-09-03-run3-opus-5.md`, `-sonnet-5.md`, `-fable-5.1.md`.
