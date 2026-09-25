# Widget text and pushbutton chrome — the channel beside page text

Contents: captions (`--captions`, `--hide-buttons`) · tooltips, dropdown
labels and defaults (`widget_text.json`, `--widget-text`) · export values
stay · values that are data · what the visual pass shows for a dropdown.

Strip-and-retypeset touches page text. Everything a form draws from its
annotation dictionaries — captions, tooltips, dropdown labels, field
defaults — never reaches a content stream and needs this channel. Without
it a "fully translated" form still shows the source language on every
hover, in every dropdown and on every button.

## Pushbutton captions

Prefer `--captions captions.json` (field-name → caption) at strip time to
rewrite `/MK /CA` in place and drop stale `/AP` streams, so the widget
count stays exact and viewers do not keep drawing the source-language
caption. The new caption must fit the widget: verify `--translations`
fails a caption wider than the button minus a 2 pt pad each side, so
prefer short chrome (`Print` / `OK`) over a sentence in a tiny button.
Hide (`--hide-buttons`) only when the button should disappear; hiding plus
a drawn replacement adds widgets unless you are replacing, not
duplicating. Never hide a button and draw a second widget. A caption you
neither rewrote nor listed in `skip` fails verify's chrome gate.

## Tooltips, dropdown labels and defaults

Tooltips (`/TU`), dropdown labels (`/Opt`) and text-field defaults (`/V`,
`/DV`) live in the annotation dictionaries. `extract_segments.py` writes
the `widget_text.json` scaffold (an empty object when the PDF has none);
author each `target`, then pass it back with `strip_text.py --widget-text`
(or `pipeline.py init … --widget-text`). A `null` target is a refusal, not
a skip — author it or delete the key.

Extract never writes a fresh scaffold over a `widget_text.json` that holds
authored text: a non-null target, a string shorthand, or a file that is not
JSON. It keeps the file, says so, and sets `widget_text_kept` on the
result. A file whose every target is still null is refreshed, so a work
directory reused for another PDF gets that PDF's scaffold. Delete the file
to get a fresh one.

**Keys are full field names.**
- The scaffold names each field by its fully qualified name: every `/T` up
  the `/Parent` chain, joined with dots, such as
  `form1[0].#pageSet[0].Page1[1].PDF417BarCode1[0]`. XFA-derived forms
  repeat a partial name such as `Name[0]` under many parents. Keyed by the
  partial name, one field's tooltip or value used to land on all of them.
- A mapping keyed by a partial name, as scaffolds before v62 wrote, still
  applies when that name belongs to exactly one field. When it belongs to
  several, strip refuses and lists their full names.
- Two keys that name the same field are refused.
- When distinct widgets share one full name but not their text, one entry
  is refused rather than copied onto all of them. This happens on a
  malformed form that repeats a name, or with a `/T` containing a dot that
  spells a nested field's name. Delete the key to leave those widgets as
  they are.
- Captions (`--captions`) and `--hide-buttons` still take the partial
  name.

**Export values stay.** An `/Opt` entry becomes `[export, display]` and
only the display half is translated, so `/V` and everything the form
submits keep working. A spec that asks to translate a choice field's `/V`
is refused; verify's `/Opt` parity gate fails any output whose export
values moved.

**Values that are data.** A `value` or `default` that is data gets its
source string back as the target, never a translation. That covers a
2D-barcode payload, an ID and a date stamp. USCIS forms carry a
`PDF417BarCode1` on every page, each with its own payload
(`I-864|08/24/26|2` on page 2), and each is its own scaffold entry. A
`null` target refuses the build, and a translation corrupts what the
form submits. Nothing guesses which values are data; you decide, and the
scaffold takes the identity target.

## What the visual pass shows for a dropdown

Expect a rendered dropdown to still show the **export** value: MuPDF's
appearance generator draws `/V` verbatim, while a conforming viewer shows
the translated display half. The file is right; check one dropdown in a
real viewer rather than translating the export.
