# Objective: every run that ships smaller than the source is reported

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/retypeset.py` (`consider_ratio`, `SCALE_MIN`, every
> `consider_ratio(` call), `SKILL.md` step 8 (name `allow_scale` cores in
> the delivery), `references/retypeset.md`, and the run-2 records for
> Sonnet and Opus. Not FL-150.

---

## 1. Compass (not done)

`consider_ratio` returns silently for any ratio at or above 0.7×. A
segment or merge scaled to 0.71×–0.99× is placed, passes every gate, and
is mentioned nowhere: not in retypeset's output, not in verify's. On the
canary fixture the merged intro paragraph shipped at **0.81×** (Sonnet)
and **0.91×** (Opus); both deliveries state that nothing shrank, Opus's
checklist ticks "no over-shrunk text — allow_scale is EMPTY", and the
skill's own rule — name every core that ships as smaller type — cannot be
followed, because the author is never told.

## 2. Done when — closed bar

1. **retypeset reports the band.** Every run (single line, dot-leader
   label, shaped run, merge, override part) that ends below 1.0× is
   printed once, with its ratio and the core or merge key, in a digest
   after the build: `scaled runs (N): p1 0.81× "Please complete this
   form…"`. Below 0.7× stays a FAIL exactly as today.
2. **The report is on disk.** retypeset writes `scale_report.json` beside
   the output (or into the mapping's work dir): `[{page, key, ratio}]`,
   so `verify` and a delivery can read it without re-running.
3. **verify surfaces it.** With `--translations`, verify prints a REVIEW
   line listing runs below 1.0× from that file (SKIP with a note when the
   file is absent — older builds must still verify). No new FAIL.
4. **The skill says what to do with it.** Step 5: "runs between 0.7× and
   1.0× are listed; reword them or name them in the delivery." Step 8's
   delivery bullet: name every scaled run, not only `allow_scale` cores.
   `references/retypeset.md` matches.
5. **Tests.** A constructed line that fits only at 0.85×: the digest line,
   the JSON entry, verify's REVIEW line; a full-size build has none of
   them; the 0.7× FAIL unchanged.
6. Full unittest + corpus green; `metadata.version` bumped.

## 3. Not done when

- Moving the 0.7× floor in either direction
- Failing a run for being between 0.7× and 1.0×
- Rounding "0.98×" away: report anything the engine or the fit scaled

## 4. Method

Constructed fixture with one over-long label and one merge that needs the
band; assert the printed digest, the file, and verify's line.

## 5. Invariants

Gates cannot see meaning; they must at least say what they did. The
author decides, told.

## 6. Proof

The digest and the file on the fixture; verify's REVIEW line; full
unittest + corpus.
