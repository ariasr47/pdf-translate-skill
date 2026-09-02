# Objective: opt-in mirror of x/alignment for RTL (not the default)

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md`, `references/fonts.md`. Do not implement a
> glossary, OCR, or claim full RTL. Do not change the default (04) path.

---

## 1. Compass (not done)

04 put logical Arabic/Hebrew in `/ActualText`. The page is still an
English skeleton: labels at the original left origin. A native RTL
reader wants the run on the other side. Flipping **graphics** would
mirror logos and rules; flipping **fields** changes rects. This session
is an **opt-in**: `mirror: true` in translations.json. Default stays 04.

## 2. Done when — closed bar

1. **Default.** No `mirror` key: RTL text bbox still on the original
   LTR side (x0 ~ 72). Existing 04 tests stay green.
2. **Opt-in.** `mirror: true`: each run’s left edge is
   `page_width - original_left - run_width` (so the original origin
   maps to the mirrored right edge). Pushbutton/text/checkbox **rects**
   and link rects flip the same way. Field **names and types** unchanged.
   Graphics/vectors in the content stream are **not** cm-flipped.
3. **Text layer.** Authored Arabic/Hebrew still in ActualText.
   `verify --translations` still PASSes. Constructed LTR source, not
   FL-150.
4. **Docs.** SKILL + fonts.md + translations-format: default is not
   mirrored; `mirror` is opt-in; look at PNGs; do not claim full RTL
   (images/rules stay). No glossary.

## 3. Not done when

- Default-on mirroring
- Mirroring drawings/images
- PDF/UA, `/StructTreeRoot`, overflow/chrome/OCR work

## 4. Method

`mirror` boolean on the mapping. Width budget (`right_limit`) still uses
**original** widget positions (snapshot before flipping annots). Flip
annots after text is placed. Tiny constructed PDF with a left label and
a right field.

## 5. Invariants

Without `mirror`: field rects identical. With `mirror`: names/types
identical, rects are the horizontal flip. Provider-neutral.

## 6. Proof

In-repo tests for default vs `mirror: true`. Unittest + corpus green.
