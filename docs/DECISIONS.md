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

| date | decision | why | what would reverse it |
|---|---|---|---|
| 2026-09-15 | Khmer **is** probed by glyph count, on the coeng cluster ខ្មែរ only; it is not a mark-stacking blind script. | Measured on this machine, PyMuPDF 1.28.2, Noto Sans Khmer: ខ្មែរ 5 → 4 glyphs (0.80); the 15 September brief's own table read the same (Khmer coeng 0.80). The worked-example row above listed Khmer among the blind scripts by analogy, not by measurement; `AGENTS.md`'s prose was corrected the same day and its measured table was not touched. | A Khmer face that shapes ខ្មែរ correctly yet draws 5 glyphs, or a GSUB-less render of it that still draws 4. |
| 2026-09-15 | Myanmar has a probe: သင်္ဘော (kinzi + stacked bha), 7 → 5. | Measured, Noto Sans Myanmar: သင်္ဘော 7 → 5 (0.71), မန္တလေး 7 → 6 (0.86). The word tested before, မြန်မာ, has no stack and reads 6 → 6 — uninformative, not a finding. | A Myanmar face that stacks correctly at 7 glyphs, or a GSUB-less render that still draws 5. |
| 2026-09-15 | Thai stays REVIEW; no probe. | ป้า 3 → 3; กำไร 4 → **5** — sara am decomposes under shaping, so a "shaped < naive" rule would fail correct Thai. Lao is treated the same by structure, unmeasured. | A Thai (or Lao) cluster that reliably loses glyphs under correct shaping and keeps them under a known-broken render. |
| 2026-09-15 | Gate 18 attests the **face**, not the document text. `prepare_font` adds the script's probe cluster to the subset and probes the subset it wrote; `verify` extracts every embedded font program on a page that draws a conjunct-forming script and re-probes it, once per (script, face). A face that lacks the probe glyphs is REVIEW, not PASS; blind and unmeasured scripts are REVIEW, never PASS; a Helvetica fallback on either arm is FAIL whatever the counts. | The document's own words may contain no merging cluster (कमल), so only a known probe has an expected count. MuPDF embeds the whole font program from `insert_htmlbox` (243,520 bytes in, 243,520 out, GSUB intact — measured), so the embedded face can be re-rendered. A pyftsubset subset keeps the Indic GSUB lookups for retained glyphs (subset probe 8 → 4, measured). Real run, red and green: `docs/reviews/2026-09-15-conjunct-shaping-gate.md`. | MuPDF starting to subset embedded fonts at save (the probe glyphs would vanish and every page would degrade to REVIEW), or a face that passes its probe yet draws a document conjunct broken — that would show the probe is not representative for that face. |
| 2026-09-15 | Skill version 48 → 49 (plugin 49.0.0, pyproject 49.0.0); `tests.test_shaping_probe` joins the CI suite line; the font cache key moves to `noto-fonts-v2`. | A new always-on gate changes what `verify` reports, so installed copies must be told; five new test faces must be cached, not re-fetched per run. | A ruling that gates do not bump the version. |
| 2026-09-15 | Gate 18 judges **every** embedded face on a page that draws a conjunct-forming script and covers the probe, not only the face that drew the visible run. A broken face that is embedded but unused therefore FAILs the page. Accepted as conservative. | Found by the independent verification pass (Sonnet 5) with a constructed page: a good face draws क्षत्रिय, a GSUB-less face is embedded unused → FAIL; the reverse (broken face draws, good face unused) is also FAIL, so no false PASS is possible. Attributing glyph runs to faces per run would need texttrace-to-xref matching that MuPDF does not expose directly; a GSUB-less face embedded on such a page is a defect waiting for the next run assigned to it, and the FAIL line names the face. | A real job where a face legitimately sits on a page drawing that script without ever drawing it — for example a field-input face that ends up in page resources — showing up as a spurious FAIL in practice. |
| 2026-09-15 | `VerifyVerdict.gates` mirrors the console: every PASS/FAIL/REVIEW/SKIP line `verify` prints is one `GateResult` with the same status, under a stable name from `verify.GATE_NAMES`; a gate that prints nothing for a job (no fields, no Arabic, no `--translations`) records nothing. Version 49 → 50. | PR #2 review F1: twelve gates recorded, eight only printed — unshaped Arabic, `/ActualText`, caption width, override markers, document metadata and its `lang` REVIEW, scaled runs, the two leak REVIEWs — so a consumer reading the verdict could see every entry PASS beside `exit_code == 1`. Printed output and exit codes are untouched (the diff is `record()` calls only); `tests.test_import_surface.VerdictCompletenessTests` counts printed gate lines against recorded entries on a real job and drives each of the eight through FAIL, PASS, REVIEW or SKIP. The version bumps because the library surface a consumer pins on changed. | A consumer that needs an entry for every gate on every job — a SKIP for "no Arabic on this page" — which would trade the line-for-line mirror for a fixed-length verdict. |
| 2026-09-16 | Every printed gate outcome carries its findings — `Finding(page, where, text)`, untruncated — in `VerifyVerdict.gates`; `--report PATH` writes `verdict.to_dict()` (schema 1, which records `fail_on_review` so an exit 1 without a FAIL gate is explained) and `pipeline.py rebuild` writes it into the work dir; `--fail-on-review` / `fail_on_review=True` exits 1 on REVIEW without FAIL; both off by default. `isolated source-script tokens: none` is PASS, not REVIEW. Every gate that is FAIL or REVIEW carries at least one finding (`tests.test_verify_report.FindingsInvariantTests`, over every kind of job the suite builds), and `run_verify` records absolute paths exactly as the CLI does. Version 50 → 51; `pdf_translate.__version__` joins the lockstep check. | `docs/BRIEF-unattended-delivery.md`: in production nobody reads the console, so a REVIEW was indistinguishable from PASS at delivery and a FAIL carried no location. The locations were already printed; the verdict now keeps them all. The "none" line was a REVIEW that fired on every job. Console output is otherwise byte-identical (`dev/probes/verdict_parity_runner.py`, nine jobs). | A consumer that needs the console's truncation mirrored in the report, or a schema change — bump `schema` rather than editing version 1 in place. |

Add new rows above this line, newest last. Do not renumber or reorder
existing rows when appending.
