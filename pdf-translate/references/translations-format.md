# translations.json — the contract for retypeset.py

One JSON file carries every language decision. The scripts handle geometry;
this file is where your judgment lives.

```jsonc
{
  "fonts": {
    "regular": "font-sub.ttf",           // required; path relative to cwd
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
  "merges": [
    {
      "page": 0,
      "lines": ["I declare under penalty of perjury that the information ",
                 "on all pages is true and correct."],
      "html": "私は、記載した情報が真実かつ正確であることを宣言します。",
      "align": "left"            // left | center | right
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

Authoring order that works well:

1. Run the extractor (or `pipeline.py init` then `pipeline.py from-cores`).
   `from-cores` writes this file with a **null** per core — not a translation.
   Retypeset still fails until you replace those nulls. It will not overwrite
   without `--force`. Do not identity-map as a shortcut; that ships source
   text. Open `to_translate.json`. JSON `null` is “not yet authored”
   (retypeset refuses). `""` and whitespace-only values are not
   translations: `verify --translations` FAILs and names the core. Use
   `skip` to drop a span, not `""`.
2. Translate every core (they're deduplicated — typically far fewer than the
   segment count). Match the recon lookup in `SKILL.md` step 1; keep verbatim
   items verbatim by simply not translating differently (e.g.
   `"Form W-2": "Form W-2"`). Extractor write/find/say warnings are
   halt-and-confirm: a missing source token fails `--translations` unless
   that span is listed in `allow_translate`.
3. Scan `segments.json` for multi-line paragraphs (same block, consecutive
   y, sentence flows on) and declare merges for them.
4. Add overrides for every extractor warning.
5. Run retypeset; it fails listing anything you missed — iterate to zero.
6. After the first render pass, add `center` / `skip` entries (centre only
   what the source centres — never a caption flush with a rule) and shorten
   whatever failed the 0.7× scale gate (or add those cores to `allow_scale`).
