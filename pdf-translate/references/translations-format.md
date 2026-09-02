# translations.json — the contract for retypeset.py

One JSON file carries every language decision. The scripts handle geometry;
this file is where your judgment lives.

```jsonc
{
  "fonts": {
    "regular": "font-sub.ttf",      // required; path relative to cwd
    "bold": "font-sub-bold.ttf"     // optional; falls back to regular
  },

  // core string (from to_translate.json) -> translation.
  // Keys are the NORMALIZED cores: markers (a., (1)) and trailing
  // dot-leaders/$ already stripped by the extractor, so one entry covers
  // every occurrence across all pages.
  "translations": {
    "NAME:": "氏名：",
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
  "merges": [
    {
      "page": 0,
      "lines": ["I declare under penalty of perjury that the information ",
                 "on all pages is true and correct."],
      "html": "私は、記載した情報が真実かつ正確であることを宣言します。",
      "align": "left"            // left | center | right
    }
  ],

  // Cores whose translation should be re-centered on the original bbox
  // midpoint (column headers, titles, signature captions). Without this a
  // shorter translation sits visibly left of center.
  "center": ["CASE NUMBER:", "Total"],

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
  // baseline. Get x values from the original's span positions.
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
6. After the first render pass, add `center` / `skip` entries and shorten
   whatever failed the 0.7× scale gate (or add those cores to `allow_scale`).
