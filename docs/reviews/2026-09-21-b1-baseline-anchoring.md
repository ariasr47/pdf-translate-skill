# B1 blocker 1 — the first baseline can be preserved exactly

**Measured 21 September 2026** against library **v60** (`b20fadd`), PyMuPDF
1.28.0, Python 3.14.0. Probe: `dev/probes/b1_anchor_probe.py`, evidence under
`runs/b1-anchor-02/results.json`. The library was **not modified**.

The [19 September recovery probe](2026-09-19-b1-recovery-probe.md) recorded
blocker 1: *"baseline anchoring is not supplied by an authored box alone"* —
all six successful candidates shifted the first baseline, −2.481 to +0.502 pt.
It explicitly did not claim preservation was impossible.

**It is possible, exactly.** All six cases now land on the source baseline with
a delta of **0.0000 pt**, with line count, engine scale, output size, page count
and horizontal origin unchanged, and with identical verify-gate outcomes.

## Why the baseline moved

`insert_htmlbox` fills a rect from its top, so the first baseline lands wherever
the authored box top happens to be. Nothing in the merge path relates that top
to the source baseline.

The library already solves this for a *single* Story line
(`retypeset.py:271`, `place_story_line`): `top = baseline - SHAPED_BASELINE * fs`
with `SHAPED_BASELINE = 0.8`, measured at line-height 1. The merge path uses the
document's own leading instead, so the offset gains CSS half-leading:

```
first_baseline_offset = fs_effective * (SHAPED_BASELINE + (line_height - 1) / 2)
line_leading          = fs_effective * line_height
```

**Both are exact.** Over 107 unshrunk model points — font size 8/9/10/11/12/14/18
px, line-height 1.0/1.18/1.3/1.5, one and three lines, Latin and CJK faces —
the largest residual against the closed form is **0.0000 pt** for the offset and
**0.0000 pt** for the leading.

> The model only became exact after it mirrored the library's own CSS. A first
> run omitted `body {margin: 0; padding: 0}` and passed an unquoted font URL;
> that produced a constant 1.0 pt error and made MuPDF silently substitute a
> default face for every CJK point. Both are recorded here because either
> mistake would look like a property of the engine rather than of the probe.

## The six cases, anchored

Method: build once with the authored box, measure the residual, then translate
the same box vertically by that residual. **Width and height are unchanged**, so
line breaking and engine scale cannot change — only the anchor moves.

| Case | Source size | Shift applied | Baseline delta before → after | Lines | Effective size / source |
| --- | --- | --- | --- | --- | --- |
| left-column-tail | 9.0 pt | +0.168 pt | −0.1680 → **0.0000** | 3 → 3 | 0.9778 |
| right-column-tail | 9.0 pt | +0.168 pt | −0.1680 → **0.0000** | 4 → 4 | 0.9778 |
| banner | 20.0 pt | +2.481 pt | −2.4807 → **0.0000** | 3 → 3 | 0.8719 |
| blue-tail | 10.0 pt | +1.278 pt | −1.2780 → **0.0000** | 3 → 3 | 0.9800 |
| cjk-tail | 11.0 pt | +0.388 pt | −0.3880 → **0.0000** | 3 → 3 | 0.9818 |
| two-page-room | 12.0 pt | −0.502 pt | +0.5020 → **0.0000** | 5 → 5 | 0.9833 |

Every required correction is **under 2.5 pt**. Horizontal origin delta is 0.0 in
all six; page count is unchanged; engine output size is byte-identical before
and after.

**Verify is unchanged.** Running `run_verify` on both builds of all six cases
returns the same exit code and the same non-passing gate list for each case
(`leak-*` and `scaled-runs` fire on both, being artifacts of the probe's
identity-mapped diagnostic payload and the merge shrink). Anchoring introduces
no new gate finding.

## What a build-free prediction costs

Applying the closed form directly — computing the box top from the source
baseline with no trial build — lands **5 of 6** at 0.0000 pt. It misses the
banner by −1.9247 pt, and the reason is precise rather than mysterious: the
engine shrank that case from a 19.6 px CSS size to 17.437 px, and the closed
form needs the *effective* size, not the requested one. Recomputed with 17.437
it reproduces the measured offset to four decimals.

So the offset law is exact, but the effective size is only known after layout.
One trial build, or one feedback correction, closes it.

## What this does not establish

- **Both refusals stay refused.** `table-cell` and `last-page-full` refuse
  before any placement, as they did on 19 September. Anchoring does not rescue
  a fit that cannot fit.
- **Not a recovery rate.** Eight constructed and seed occurrences are a stress
  sample. This says nothing about the share of real jobs B1 would recover, which
  still awaits a genuine fit-refusal case.
- **The moved box can cross its authorization.** The banner's rectangle ends at
  y=110.481 after the shift, past the dark banner that ends at y=110, although
  painted ink stops at y=105.5 — 4.5 pt inside. Span bounds are not ink, as the
  19 September probe established. An implementation must decide which boundary
  the caller's authorization constrains.
- **Line height was 1.18 in every case.** A one-member merge has no second
  source baseline to measure leading from, so `retypeset` falls back to 1.18.
  Multi-member merges derive it from the source and are untested here.
- **This is a caller-side computation.** No library change was made, proposed or
  verified. That an author can compute the anchored box today is the finding.

## What it means for B1

The approved direction requires *"preserve the first source baseline and the
occurrence's horizontal anchor"*, and *"if the box cannot accommodate that
anchor, report the conflict rather than move it"*. Both halves are now measured:
the anchor is achievable to 0.0000 pt, and the conflict case is a containment
check against a box whose top is determined, not authored.

With blocker 2 closed by PR #15 and blocker 3 by the `typography-1` occurrence
addressing in PR #17, **all three measured engineering blockers from the
19 September probe are now answered.** What remains for B1 is not engineering:
it is a genuine fit-refusal case, for which v60's capture hook is the collection
mechanism.
