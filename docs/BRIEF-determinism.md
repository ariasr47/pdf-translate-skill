# Brief: determinism — C7, measured first (E8)

Date: 2026-09-18. Measured on `docs/32-design-canvas` (skill v56 + docs) with the repo venv,
PyMuPDF 1.28.2 / MuPDF 1.28.2, Python 3.14.0, Windows. Probe: `dev/probes/determinism_probe.py`
(log below). Scoped by `docs/REQUESTS-from-product.md` row C7 and the E3 design pass, which moved
C7's implementation to E8 on the grounds that its size was unknown until a probe ran. It has now run.

Amended the same day, after a second pass over two corpus fixtures closed the "one page, no
furniture" gap this brief had left open, and corrected the *method* behind one of its claims. See
§2.2 and §3 item 2: the conclusion did not move, but the evidence under it did, from a coincidence
to a controlled test.

## 1. The problem, in one paragraph

C7 asks for "same inputs → byte-identical output PDF when the caller supplies a fixed timestamp
(and `/ID` is derived from content or supplied)". The request presupposes the fix — a timestamp
parameter — without anyone having measured what a run actually varies. `retypeset` takes no
timestamp today, calls `doc.ez_save(out)` with no arguments (`retypeset.py:1387`), and its metadata
pass (`apply_document_metadata`, `retypeset.py:354`) copies `doc.metadata`, pops only `format` and
`encryption`, and calls `set_metadata()`. Whether that produces varying bytes, and which, was never
established here. The whole of C7's cost turns on the answer.

## 2. Measured — do not re-derive, do not alter

### 2.1 Three shapes, one answer

The real pipeline (`strip_text` → `extract_segments` → `retypeset`), the same job run five times
across four comparisons, over three sources chosen so that the two things most likely to carry a
second varying key — **form widgets** and **many cores** — are each represented:

| source | shape | size | same path, back to back | different path, same tick | 3 s later |
| --- | --- | --- | --- | --- | --- |
| synthetic one-pager | 1 core, 0 widgets | 325,777 B | **identical** | **identical** | differs — 30 B, `/ID` only |
| `corpus/choice_fields.pdf` | 1 core, **3 widgets** | 326,937 B | **identical** | **identical** | differs — 30 B, `/ID` only |
| `corpus/dense_table.pdf` | **25 cores**, 0 widgets | 387,705 B | **identical** | **identical** | differs — 29 B, `/ID` only |

`choice_fields.pdf` is the combobox-plus-listbox fixture whose `/Opt` must survive strip;
`dense_table.pdf` is the tight-cell table with no auto-merge. Between them they add widget
appearance streams and 25× the placement work, and neither adds a varying byte.

The `/ID` table is identical in kind for all three — element 1 stable across five runs, element 2
taking two values, changing only with the clock:

```
--- trailer /ID per run            (corpus/choice_fields.pdf)
    a  back to back              c3b9c3af0dc3980b11c29c65c2a5c383  6c701e4aed306ba15b0e8cfcebb176e0
    b  same path, same instant   c3b9c3af0dc3980b11c29c65c2a5c383  6c701e4aed306ba15b0e8cfcebb176e0
    c  other path, same instant  c3b9c3af0dc3980b11c29c65c2a5c383  6c701e4aed306ba15b0e8cfcebb176e0
    d  same path, later          c3b9c3af0dc3980b11c29c65c2a5c383  c599df28c65cd58816453cad34a07704
    e  other path, later         c3b9c3af0dc3980b11c29c65c2a5c383  c599df28c65cd58816453cad34a07704
    element 1: 1 distinct value(s) across 5 runs
    element 2: 2 distinct value(s) across 5 runs
```

### 2.2 The path test, done properly

The first pass read "different output path, same instant ⇒ identical" as proof that the output path
does not reach the bytes. That reasoning was not sound. Run `c` happens *after* run `b`; if the
clock ticks in that gap, a path-leak and a clock-leak leave exactly the same evidence, and the
conclusion rests on the tick having fallen somewhere else. On the first `choice_fields` run it did
not fall somewhere else, and the probe duly reported a path leak that was not there.

The fix is to stop assuming an instant and start measuring one. `/ID`'s second element *is* the tick
counter, so: alternate two output paths many times, group runs by their element 2, and compare bytes
only **inside** a tick that happens to hold both paths. That is a controlled experiment the clock
cannot confound.

```
--- path vs clock discriminator (8 X/Y pairs, back to back)
    16 runs in 0.80s, 2 distinct /ID element 2 value(s)
    2 tick(s) contain BOTH output paths
      tick c599df28c65cd588…  x == y: True
      tick 1d978479d372e390…  x == y: True
    => the OUTPUT PATH is not in the bytes.
```

All three sources return `x == y: True` in every tick that held both paths. The path is clean, and
now it is clean *by measurement*.

```
=== verdict
    varies. keys touched: /ID
    ONLY /ID. Content streams, fonts and the /Info dates are
    already byte-identical — apply_document_metadata carries
    the source's /CreationDate, /ModDate and /Producer
    through unchanged, so no timestamp parameter is needed
    for them.
    The output PATH does not leak; the CLOCK does. Pinning or
    deriving /ID is the whole of C7 for this path.
```

### 2.3 Where the bytes differ

Every differing run lands inside the trailer's `/ID` array, at one offset near the end of the file —
the byte counts in §2.1 vary between 29 and 30 only because the differing hex run starts a character
earlier or later, not because more of the file moved:

```
      @325640 len=15  in /ID
        A b'4cc2be455ac3b640c3a4c2><a3f500e13f8340e87317a6e'
        B b'4cc2be455ac3b640c3a4c2><327ae3c449ea7d1872ac099'
```

The probe reads the trailer's `/ID` pair per run, so §2.1's table is read, not inferred from hex.
One thing falls out of it: the **first** `/ID` element is stable across every run on every source.
The conventional split is that the first element identifies the document and the second identifies
the revision, so MuPDF is already deriving the permanent half deterministically — only the revision
half is being generated fresh.

## 3. What the measurements decide

1. **No timestamp parameter is needed.** `/CreationDate`, `/ModDate` and `/Producer` do not vary,
   because `apply_document_metadata` carries the *source's* values through rather than writing
   "now". C7's own phrasing — "when the caller supplies a fixed timestamp" — assumes a defect that
   is not there. Adding `timestamp=` would be new API for a problem this job does not have.
2. **The output path does not leak into the bytes.** Two runs to different paths *inside one clock
   tick* are byte-identical, on all three sources (§2.2). A consumer can write anywhere. Note the
   method: the first pass inferred this from a pair of runs it merely assumed were simultaneous,
   which is not the same claim and would have been wrong roughly as often as a tick fell between
   them.
3. **The clock leaks, into `/ID`'s second element only.** 29–30 bytes at one offset.
4. **Content, fonts and structure are already deterministic.** 325,748 of 325,777 bytes on the
   synthetic job, and the same picture on both corpus fixtures, are identical across every
   comparison — the embedded font program, all content streams, and on `choice_fields.pdf` the
   widget appearance streams too. This is the load-bearing result: whatever C7 costs, it is not a
   placement, a subsetting, or a form-field problem.
5. **Furniture does not change the answer.** Adding three form widgets, or 25× the cores, adds no
   varying byte. The claim is no longer shape-specific in any way this repo's corpus can detect.

So C7 reduces to one sentence: **pin or derive the second `/ID` element.** That is a parameter and a
test, not an epic.

## 4. Design

- `run_retypeset(..., doc_id=None)` — when given, written verbatim as both `/ID` elements; when
  `None`, today's behaviour. A caller wanting content-derived identity passes the sha256 of the
  inputs it already has; the library does not invent a derivation policy, because "derived from
  content" means different things to a caller who does and does not count the mapping.
- The loud `retypeset()` does not take it and does not change.
- The test is the probe's third case, pinned: same job, same `doc_id`, runs separated in time,
  `sha256` equal. That is E8's "the C7 determinism test gates".
- E8's benchmark table gains an "identical across runs" column so a regression is visible without
  reading a test name.

## 5. Not doing, on purpose

- **No `timestamp=` parameter.** Measured unnecessary (§3.1). If a future source PDF carries no
  dates at all and MuPDF invents them, that is a different measurement and a different brief.
- **No change to `apply_document_metadata`.** It is doing the right thing and is the reason the
  dates are stable.
- **No default `doc_id`.** Deriving one silently would change every existing output's bytes for
  every current caller, which is a break with no request behind it.
- **Measured after all: a job with more furniture.** This bullet used to say the opposite, and
  named the two fixtures to try. Both have now been run (§2.1): `choice_fields.pdf` for widgets and
  `dense_table.pdf` for many cores. No second key appeared, so §3 stands and §4 is sufficient.
- **Still not measured: multi-page, merges, overrides, notices.** All three sources are single-page,
  and the corpus mapping used here is identity with no merges or overrides. Nothing suggests these
  matter — they change *which* bytes are written, not *whether* the writer consults the clock — but
  no run has demonstrated it.
- **Still not measured: another platform.** Windows, one PyMuPDF build (1.28.2 / MuPDF 1.28.2).
  Linux CI may differ, and the machine's system Python carries PyMuPDF 1.28.0 / MuPDF **1.29.0**, a
  different MuPDF entirely — use `pdf-translate.venv` to reproduce any of this.
- **Not measured: whether a pinned `doc_id` actually pins the bytes.** §4 designs it; no run has
  confirmed MuPDF honours a caller-set `/ID` through `ez_save`. That is E8's first red test, not an
  assumption to build on.

## 6. Reproduce

From the repo root, with `pdf-translate.venv` (not the system Python — see §5):

```
PYTHONUTF8=1 ./pdf-translate.venv/Scripts/python.exe dev/probes/determinism_probe.py
PYTHONUTF8=1 ./pdf-translate.venv/Scripts/python.exe dev/probes/determinism_probe.py --source corpus/choice_fields.pdf
PYTHONUTF8=1 ./pdf-translate.venv/Scripts/python.exe dev/probes/determinism_probe.py --source corpus/dense_table.pdf
```

`--source` is resolved relative to `pdf-translate/`, translates every core to itself, and prints the
source's shape (pages, cores, widgets, annotations) so a future run's claim is scoped to something
stated rather than assumed. `--work DIR` relocates the scratch job; `--gap N` sets the sleep.
