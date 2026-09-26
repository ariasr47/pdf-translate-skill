# Right-to-left source runs: prototyped, then parked — 26 September 2026

**Ruling.** Rodrigo ruled right-to-left out of scope, because the web app
won't support it. The product agreed, per case (`docs/REQUESTS-from-product.md`,
26 September):
- **An RTL source into an LTR target:** parked. The defect stays pinned as
  an expected failure.
- **RTL targets:** none, now or planned. The library's RTL support stays as
  it is.
- **Full layout mirroring:** not wanted.

This record keeps the prototype's findings, so the work is not lost if the
scope changes.

## The defect

MuPDF reports a right-to-left line's origin near its right end. Retypeset
draws every run rightward from its origin, so an RTL-source line lands about
one line-width to the right. No verify gate reads positions.

Measured on `corpus/ar_source.pdf`, the corpus's only RTL source
(`rtl_source.pdf` has no RTL runs), with PyMuPDF 1.28.2 on v84:

| line | source | today, Arabic | prototype, Arabic | today, English | prototype, English |
|---|---|---|---|---|---|
| title | 60.9–147.6 | 140.6–239.9 | 48.3–147.6 | 140.6–273.8 | 33.5–147.6, at 10.3 pt |
| Name label | 61.0–83.8 | 81.3–106.6 | 58.5–83.8 | 81.3–118.3 | 46.7–83.8 |
| Address label | 61.0–90.9 | 88.5–120.1 | 59.3–90.9 | 88.5–137.3 | 42.1–90.9 |

Extents are in PDF points. In the prototype all six right edges match the
source's within 0.1 pt.

Two details explain the prototype's numbers:
- **The English title shrank.** It needs 133.2 pt at 12 pt, and the room to
  its left ends at the 32 pt page margin, so it is set at 10.3 pt (0.86×).
- **The Arabic title is wider.** It comes out 12.6 pt wider than the source,
  because the rebuild's face is wider than the source's.

## The prototype

It was built in a scratch copy, never in the repository. It reuses the
`right` anchoring of row 28 for runs whose source is right to left, in the
plain-run branch of `pdf_translate/retypeset.py`:

```diff
-            elif core in right:
+            elif core in right or is_rtl_text(core):
                 maxw = seg['bbox'][2] - left_limit(pno, seg, segs)
 ...
-            elif core in right and not rot:
+            elif (core in right or is_rtl_text(core)) and not rot:
                 x = max(0.0, seg['bbox'][2] - run_w)
```

`left_limit` already stops the leftward room at the nearest same-row segment
or widget rect, otherwise at the 32 pt margin.

## What a real build would need

This is the product's advice, recorded for a future scope change:
- **Where a line goes:** a run keeps its source's anchor and its source's
  room, whatever the target's direction. The leftward room stops at the
  nearest obstacle and takes the overflow path, never an overlap.
- **Which lines move:** key on the measured signal, MuPDF's origin at the
  line's right end, with the first strong character (UAX #9 P2/P3) as a
  cross-check. Where the two disagree, keep today's placement and record
  it. `is_rtl_text` alone is too broad: it would move an LTR line that
  holds one Hebrew word.
- **Tests:**
  - the pinned test checks the right edge, the reading start, for RTL runs,
    within 1.5 pt; MuPDF's RTL origin moves with the face, and the
    prototype's title was 2.2 pt off by that measure;
  - an RTL label with a field to its left and a translation long enough to
    reach it: no overlap, and a shrink or a refusal;
  - every LTR-source document in the corpus rebuilds with 0 changed bytes,
    with the trailer `/ID` masked.
- **Verification:** Rule 1 applies, because the fix changes layout.
- **Out of it:** mirror mode and rotated RTL lines.

## Mirroring, and why not

An LTR source into an RTL target would want its layout mirrored. The library
draws the target text right to left but keeps the layout left to right.
`"mirror": true` is an opt-in partial: it flips text and field and link
rects, while boxes, rules and images stay.

Full mirroring can flip vector graphics with one transform. Images,
signatures, stamps, barcodes and QR codes, charts, maps and arrows must not
flip, and that judgement is per document. A mirrored official form is also
no longer the issuer's layout. The product does not want it, and it reopens
only if Rodrigo adds an RTL target language.
