# Seed corpus

Every PDF here has exactly one expected verdict:

| File | Verdict | Notes |
|---|---|---|
| `choice_fields.pdf` | `translate` | combobox (dropdown) + listbox; `/Opt` must survive strip |
| `colored.pdf` | `translate` | white-on-dark + coloured spans |
| `dense_table.pdf` | `translate` | tight cells, no auto-merge |
| `encrypted.pdf` | `translate` | empty user password |
| `expansion.pdf` | `translate` | short labels |
| `image_only.pdf` | `refuse+OCR` | raster, no text layer |
| `multicolumn.pdf` | `translate` | two columns |
| `nested_xobject.pdf` | `translate` | text two Form XObjects deep; page `/Resources` inherited from `/Pages`; strip must leave no page text |
| `pale_blank.pdf` | `skip-ink` | negligible dark pixels, not a scan |
| `rotated.pdf` | `translate` | `/Rotate 90` |
| `rtl_source.pdf` | `translate` | LTR English source (layout not mirrored) |
| `xobject_text.pdf` | `translate` | text inside a Form XObject |

`verdicts.json` is the machine-readable copy of this table.

- `translate` — `extract_segments` exits 0 with at least one segment.
- `refuse+OCR` — extract and verify exit non-zero; the message names OCR.
- `skip-ink` — verify does not FAIL the ink-ratio gate (it SKIPs).

A photographed court-notice scan is not stored here (large). Tests construct an equivalent raster-only page; it must verdict `refuse+OCR` like `image_only.pdf`.
