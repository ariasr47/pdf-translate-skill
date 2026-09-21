# translations.json — the contract for retypeset.py

One JSON file carries every language decision. The scripts handle geometry;
this file is where your judgment lives.

> This page describes the `legacy` format, which is the default and is
> unchanged. A job that needs the source's serif/sans class and its within-line
> bold/italic preserved uses the opt-in `typography-1` format instead — see
> `references/typography.md`. Ask the engine first:
> `'typography-1' in getattr(pdf_translate, 'MAPPING_FORMATS', ())`.

```jsonc
{
  "fonts": {
    "regular": "font-sub.ttf",           // required; relative to this JSON file
    "bold": "font-sub-bold.ttf",         // optional; falls back to regular
    "italic": "font-sub-italic.ttf",     // optional; falls back to regular
    "bold_italic": "font-sub-bi.ttf"     // optional; falls back to bold,
                                         // then italic, then regular
  },

  // BCP-47 tag of the TARGET language. retypeset writes it to /Lang and to
  // dc:language in XMP; screen readers, hyphenation and search all read it,
  // and without it the output still declares the source language. verify
  // REVIEWs a mapping with no "lang" and FAILs an output whose /Lang does
  // not match this.
  // A tag, not a display name: "ja", never "Japanese" or "日本語". ISO 639-2 ("jpn") is accepted.
  "lang": "es-MX",

  // core string (from to_translate.json) -> translation.
  // Keys are the NORMALIZED cores: markers (a., (1)) and trailing
  // dot-leaders/$ already stripped by the extractor, so one entry covers
  // every occurrence across all pages. The document /Title and every
  // outline (bookmark) title are cores too; they are not page text, so
  // retypeset writes them to the metadata and the outline instead, and
  // the placement gate does not look for them in the text layer.
  "translations": {
    "NAME:": "氏名：",
    // A single-line target may carry inline <b>/<i> (or <strong>/<em>),
    // the way a merge's html can; it is then placed through the Story
    // engine against the four font roles. Only those four tags count as
    // markup, so a translation that really contains "<" is left alone.
    "Read the notice.": "Lea el <b>aviso</b> con <i>atencion</i>.",
    // '‖' splits a bold lead-in from a regular remainder, for lines that
    // mix weights (bold heading + regular parenthetical):
    "Employment (Give information on your current job.)":
      "雇用‖（現在の仕事について記入してください。）"
  },

  // Wrapped paragraphs translated as ONE unit and re-flowed in-place.
  // Identify each by page + the EXACT text of its member lines (from
  // segments.json), in order. html supports <b> and <br>. The box
  // auto-shrinks to fit; retypeset FAILS below 0.7× unless allow_scale
  // lists the merge's first line (or the merge has "allow_scale": true).
  // `pipeline.py propose-merges --work . --accept` fills this list from
  // the extractor's wrapped-paragraph candidates (warning kind
  // "merge-candidate"), each with html null.
  // A null html FAILs retypeset exactly like a null translation: an
  // accepted proposal is not a translated paragraph.
  // "box": [x0, y0, x1, y1] in the ORIGINAL page's coordinates replaces
  // the union of the member lines as the rect the paragraph re-flows
  // into — for a paragraph whose target needs one more line than the
  // source and has empty space below it. Absent or null: unchanged.
  // Nothing computes a box for you: a rect that grows into a rule or a
  // field is worse than a shrink, and only you can see the page. It is
  // used exactly as given (a union bbox gets a little slop; your rect
  // does not), it may overlap anything you decide it may, and the render
  // is the check — no gate judges a box. Every other gate still counts:
  // the 0.7× floor inside your rect, the placement gate, the canonical
  // layer.
  "merges": [
    {
      "page": 0,
      "lines": ["I declare under penalty of perjury that the information ",
                 "on all pages is true and correct."],
      "html": "私は、記載した情報が真実かつ正確であることを宣言します。",
      "align": "left",           // left | center | right
      "box": null                // your rect, or null for the union bbox
    }
  ],

  // Cores whose SOURCE is centred in its own box — a column header over
  // its column, a title over the page — re-centred on the original bbox
  // midpoint. Without this a shorter translation sits visibly left of
  // center. NOT for a caption flush with a rule or a field ("Signature",
  // "Date" under a signature line): that caption is left-anchored, and
  // centring a wider translation on the old midpoint pushes it out both
  // sides, so it hangs off the left end of the rule it labels. No gate
  // sees a centred caption off its rule; only the render does. Leave
  // those cores out of this list.
  "center": ["CASE NUMBER:", "INSTRUCTIONS"],

  // Cores anchored on the original bbox RIGHT edge instead of the left:
  // amount columns, right-hand labels tucked against a rule. Without this
  // a longer translation grows rightward past that edge. The extractor
  // proposes candidates as `right-aligned` warnings (segments that share a
  // right edge while their left edges differ AND sit within one em of a
  // rule, a field or the next segment; justified text is a merge, not a
  // column); nothing realigns itself.
  "right": ["Total", "Subtotal"],

  // Exact segment texts to drop entirely — e.g. page text duplicated by a
  // widget caption that renders on top of it (failure-modes.md #6).
  // Use skip to drop a span. Do not map a core to "" — that is not a
  // translation; verify --translations FAILs and names the core.
  "skip": ["Print this form"],

  // Cores (or merge first lines / override "contains") allowed to scale
  // below 0.7×. Without this, retypeset FAILS and does not save.
  "allow_scale": ["very long column header"],

  // Source write/find/say spans (quoted payload, Form/Schedule/Attachment/
  // Exhibit names) the author *meant* to translate. verify --translations
  // otherwise FAILs if those tokens are missing from the output. Omit the
  // key: same as []. Record why in NOTES; scripts do not read NOTES.
  // "allow_translate": ["Attachment A"],

  // Opt-in RTL *layout*: flip text x and field/link rects. Default omitted
  // = LTR skeleton (04). Graphics are not mirrored. Look at the renders.
  // "mirror": true,

  // Manual placements for segments the extractor flagged (in-span gaps —
  // phrases separated by wide spaces with widgets between them). Matched by
  // substring; each part is placed at an explicit x on the original
  // baseline. Get x values from the original's span positions. Parts
  // replace the WHOLE span: keep the list marker ("d.") and the tail after
  // the leaders ("$") in some part, or verify --translations fails naming
  // the dropped token (it reads segments.json beside this file).
  // Because the parts replace the span, the core's own entry in
  // "translations" may be null wherever an override covers every
  // occurrence of it: the plain value would never be drawn, and writing
  // one only to satisfy the coverage check gave qa_check a phantom string
  // to grade. An occurrence on a page no override covers still needs its
  // plain value, and retypeset names that page.
  // The target-language compliance notice, when the document class needs
  // one (references/compliance.md §1). The ONLY text here that is not the
  // translation of an existing string. Placed by retypeset with the job's
  // fonts into the box YOU chose from a render — nothing computes it and
  // no gate judges it — through the same glyph check, canonical layer,
  // scale report and placement gate as every other run. No page is added.
  // "‖" splits a bold lead-in from the rest when "bold_lead" is true;
  // "size" defaults to 8. Pages are 0-based. A null or empty text, a page
  // outside the document and an empty or inverted box are refused by name
  // before anything is drawn.
  // "notices": [
  //   {"page": 0, "text": "Traducción solo informativa.‖Esta es una
  //    traducción no oficial de FL-100 …", "box": [40, 700, 560, 745],
  //    "size": 7, "bold_lead": true}
  // ],

  "overrides": [
    {
      "page": 1,
      "contains": "All other property,",
      "parts": [
        {"text": "その他の全財産", "x": 66.0},
        {"text": "（推定額）", "x": 296.7, "max_width": 210}
      ]
    }
  ]
}
```

Font paths are relative to the directory containing `translations.json`;
absolute paths also work. This rule is the same for direct `retypeset.py`
and `pipeline.py rebuild`. Existing caller-relative font paths are accepted
with a compatibility note only when the mapping-relative file is absent.
Prefer mapping-relative paths so a job can be moved or rebuilt from any
directory. Command-line paths, including verification flags passed to
`rebuild`, remain relative to the caller's working directory.

Authoring order that works well:

1. Run the extractor (or `pipeline.py init` then `pipeline.py from-cores`).
   `from-cores` writes this file with a **null** per core — not a translation.
   Retypeset still fails until you replace those nulls. It will not overwrite
   without `--force`. Do not identity-map as a shortcut; that ships source
   text. Open `to_translate.json`. JSON `null` is “not yet authored”
   (retypeset refuses — except on a core every occurrence of which an
   override covers, where nothing would be drawn from it anyway).
   `""` and whitespace-only values are not
   translations: `verify --translations` FAILs and names the core. Use
   `skip` to drop a span, not `""`.
2. Translate every core (they're deduplicated — typically far fewer than the
   segment count). Match the recon lookup in `SKILL.md` step 1; keep verbatim
   items verbatim by simply not translating differently (e.g.
   `"Form W-2": "Form W-2"`). Extractor write/find/say warnings are a
   list to confirm, not a halt each: every span stays verbatim, a missing
   source token fails `--translations`, and `allow_translate` names the
   few you decided to translate. In `widget_text.json`, a value that is
   data (a barcode payload, an ID) gets its source string back as the
   target.
3. Scan `segments.json` for multi-line paragraphs (same block, consecutive
   y, sentence flows on) and declare merges for them.
4. Add one `overrides` entry per `inner-gap` warning. The other kinds
   are decisions about a list: `merge-candidate` → `propose-merges`,
   `right-aligned` → `right`, `narrow-column` → one merge or one
   override, `image-region` → look.
5. Run retypeset; it fails listing anything you missed — iterate to zero.
6. After the first render pass, add `center` / `skip` entries (centre only
   what the source centres — never a caption flush with a rule) and shorten
   whatever failed the 0.7× scale gate (or add those cores to `allow_scale`).

## The expansion band

Expansion depends on how *short* the string is, not just on the language
pair — and a form is made of short labels. The W3C/IBM band for
translation out of English:

| Source length (characters) | Expect up to |
|---|---|
| 1–10 | 300% |
| 11–20 | 200% |
| 21–30 | 180% |
| 31–50 | 160% |
| 51–70 | 140% |
| over 70 | 130% |

So "City" may need three times its width while a paragraph needs a third
more; EN→JA usually shrinks instead. `qa_check.py` flags targets outside
the band. Retypeset fails a segment scaled below 0.7×: reword first, and
use `allow_scale` last — every core listed there ships as smaller type,
so name them in the delivery.
