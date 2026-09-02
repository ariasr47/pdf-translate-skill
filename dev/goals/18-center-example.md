# Objective: `center` must stop recommending itself for signature captions

> Hand this to a `/goal` session. Self-contained. Read
> `references/translations-format.md` (the `center` block),
> `scripts/retypeset.py` (the `core in center` branch) and
> `dev/canary/runs/2026-09-02-haiku-4.5.md`. Do not build a verify gate.
> Do not touch `right`. Not FL-150.

---

## 1. Compass (not done)

`translations-format.md` offers `center` for *"column headers, titles,
signature captions"*. A signature caption sits **left-flush under a rule**;
centring it on the original bbox midpoint moves it. Haiku 4.5 read that
example, put `Signature of parent or guardian` and `Date` in `center`, and
shipped this:

| | original x0 | output x0 |
|---|---|---|
| signature caption | 72.0 (flush with the rule at 72) | **64.5** |
| date caption | 360.0 (flush with the rule at 360) | **357.2** |

The Spanish caption is wider, so centring pushed it out both sides and it
now overhangs the left end of its own rule by 7.5 pt. Every gate passed.
The model followed the documentation and got a worse page: **the example is
the defect.**

## 2. Done when — closed bar

1. **The example is corrected.** `center` is for a run whose source is
   centred *in its own box* — a column header over a column, a title over a
   page. Say plainly that a caption flush with a rule or a field is
   **left-anchored**, and that centring it moves it off the thing it labels.
   Name the failure so the next reader recognises it.
2. **SKILL.md agrees.** The alignment paragraph in step 5 says the same in
   one sentence.
3. **A test locks the geometry claim**, not the prose: a left-flush caption
   whose translation is wider, placed with `center`, ends up left of the
   source x0; placed without it, at the source x0. This is the measurement
   that makes the doc change true, and it will keep being true.
4. **No regressions.** Full unittest + corpus green.

## 3. Not done when

- A verify gate for centred runs (see §5)
- Changing what `center` *does*
- Auto-detecting alignment
- Touching `right` (it is correct; the extractor proposes it)

## 4. Method

Constructed LTR PDF: a rule from x=72, a caption at x=72 under it, a
translation ~15 pt wider. Drive shipped retypeset twice, with and without
`center`. Assert the x0s.

## 5. The softer question — decide, then stop

A `center`ed run that ends up **wider than its source bbox** now covers
space the source did not. For a genuine centred title that is correct and
wanted, so it can never be a hard gate. It could be an extractor warning,
or nothing. **Decide in one paragraph in this brief's closing note and do
not build it in this sitting.**

## 6. Invariants

Provider-neutral. Geometry-only. No glossary. Warnings propose, authors
decide.

## 7. Proof

The two x0 measurements, the corrected example, full unittest + corpus.

---

## 8. Closing note — 2 September 2026, closed

**Reproduced first.** A constructed 400×300 page: a rule from x=72 with
`Signature of parent or guardian` flush beneath it, a rule from x=300 with
`Date` beneath it, Helvetica 9 pt. Target Noto Sans 9 pt, driven through
the shipped `extract_segments` → `strip_text` → `retypeset`, once with an
empty `center` list and once with both captions in it:

| caption | source x0 | anchored left | in `center` |
|---|---|---|---|
| `Firma del padre, madre o tutor legal` (153.2 pt wide against 124.6) | 72.0 | **72.0** | **57.67** |
| `Fecha` (24.7 pt against 19.0) | 300.0 | **300.0** | **297.17** |

Both builds exit 0 from retypeset and pass `verify --translations`: the
centred caption hanging 14.3 pt off the left end of its own rule is a
silent PASS, exactly as the canary reported.

**Done bar, item by item.**

1. `references/translations-format.md`: the `center` block now says the
   list is for a run whose *source* is centred in its own box, says a
   caption flush with a rule or a field is left-anchored, and names the
   failure (a wider translation hangs off the left end of the rule it
   labels, and no gate sees it). Authoring-order step 6 says centre only
   what the source centres. The example core `"Total"` is gone from
   `center`, where it contradicted the `right` example beneath it.
2. `SKILL.md` step 5, alignment paragraph: one sentence saying the same.
   `references/failure-modes.md` §8 lists the failure among the defects
   only eyes catch.
3. `tests/test_pipeline.py`: `build_caption_pdf`, `span_edges`, and
   `AlignmentAndFontRoleTests.test_center_moves_a_left_flush_caption_off_its_rule`
   — asserts the translation is wider than the source, that the plain
   build lands each caption on its rule's x0 (±0.1), that the `center`ed
   build lands each more than 1 pt left of it, and that verify passes
   both. `write_mapping` grew a `center=` parameter beside `right=`.
4. Full unittest + corpus: 158 tests, no skips, green locally.
   `metadata.version` 29 → 30.

Not done, as the brief asked: no verify gate, no change to what `center`
does, no alignment detection, `right` untouched.

**§5, decided: nothing, for now.** The condition "a `center`ed run wider
than its source bbox" fires for nearly every correct centred title in an
expanding language pair (English to Spanish, French or German lengthens
most runs), so a note keyed to it would not separate the defect from the
intended case; it would be a line the author learns to ignore. The signal
that does separate them is what the run is anchored to — a rule or a
widget starting at the same x — and finding anchors is alignment
detection, which this program does not do (§3, and "warnings propose,
authors decide"). The extractor cannot see it at all: it does not know
translation widths. The fix that fits is the one shipped: an example that
no longer invites the mistake, a named failure, and the mandatory visual
pass. If the next canary walks a model into it again despite the
corrected text, that is the moment to reconsider, with a measurement.
