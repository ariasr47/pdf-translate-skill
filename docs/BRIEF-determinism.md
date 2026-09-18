# Brief: determinism — C7, measured first (E8)

Date: 2026-09-18. Measured on `docs/32-design-canvas` (skill v56 + docs) with the repo venv,
PyMuPDF 1.28.2 / MuPDF 1.28.2, Python 3.14.0, Windows. Probe: `dev/probes/determinism_probe.py`
(log below). Scoped by `docs/REQUESTS-from-product.md` row C7 and the E3 design pass, which moved
C7's implementation to E8 on the grounds that its size was unknown until a probe ran. It has now run.

## 1. The problem, in one paragraph

C7 asks for "same inputs → byte-identical output PDF when the caller supplies a fixed timestamp
(and `/ID` is derived from content or supplied)". The request presupposes the fix — a timestamp
parameter — without anyone having measured what a run actually varies. `retypeset` takes no
timestamp today, calls `doc.ez_save(out)` with no arguments (`retypeset.py:1387`), and its metadata
pass (`apply_document_metadata`, `retypeset.py:354`) copies `doc.metadata`, pops only `format` and
`encryption`, and calls `set_metadata()`. Whether that produces varying bytes, and which, was never
established here. The whole of C7's cost turns on the answer.

## 2. Measured — do not re-derive, do not alter

One page, one core, the real pipeline (`strip_text` → `extract_segments` → `retypeset`), the
same job run five times across four comparisons:

| comparison | result |
| --- | --- |
| same output path, back to back | **identical**, 325,777 bytes |
| different output path, same instant | **identical** |
| same output path, 3 s later | differs — 29 bytes, **`/ID` only** |
| different output path, 3 s later | differs — 29 bytes, **`/ID` only** |

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

Every differing run lands inside the trailer's `/ID` array, at one offset near the end of the file:

```
      @325640 len=15  in /ID
        A b'4cc2be455ac3b640c3a4c2><a3f500e13f8340e87317a6e'
        B b'4cc2be455ac3b640c3a4c2><327ae3c449ea7d1872ac099'
```

The probe extracts the trailer's `/ID` pair per run, so this is read, not inferred from hex:

```
--- trailer /ID per run
    a  back to back              1c0dc29dc3b1c3a7c287c2a4c297c2b9  99871fb7db730e46902584a5dd925584
    b  same path, same instant   1c0dc29dc3b1c3a7c287c2a4c297c2b9  99871fb7db730e46902584a5dd925584
    c  other path, same instant  1c0dc29dc3b1c3a7c287c2a4c297c2b9  99871fb7db730e46902584a5dd925584
    d  same path, later          1c0dc29dc3b1c3a7c287c2a4c297c2b9  087ed44c74d82098928c8a469ed55294
    e  other path, later         1c0dc29dc3b1c3a7c287c2a4c297c2b9  087ed44c74d82098928c8a469ed55294
    element 1: 1 distinct value(s) across 5 runs
    element 2: 2 distinct value(s) across 5 runs
```

Two things fall out of that table. The **first** `/ID` element is stable across every run — the
conventional split is that it identifies the document and the second identifies the revision, so
MuPDF is already deriving the permanent half deterministically. And `d` and `e` wrote to *different
paths* at the same later instant and share an element 2, which is what proves the variation is the
clock and not the path.

## 3. What the measurements decide

1. **No timestamp parameter is needed.** `/CreationDate`, `/ModDate` and `/Producer` do not vary,
   because `apply_document_metadata` carries the *source's* values through rather than writing
   "now". C7's own phrasing — "when the caller supplies a fixed timestamp" — assumes a defect that
   is not there. Adding `timestamp=` would be new API for a problem this job does not have.
2. **The output path does not leak into the bytes.** Two runs at the same instant to different
   paths are identical. A consumer can write anywhere.
3. **The clock leaks, into `/ID`'s second element only.** 29–31 bytes at one offset.
4. **Content, fonts and structure are already deterministic.** 325,748 of 325,777 bytes are
   identical across every comparison, including the embedded font program and all content streams.
   This is the load-bearing result: whatever C7 costs, it is not a placement or a subsetting problem.

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
- **Not measured: a job with more furniture.** One page, one core, no form fields, no widgets, no
  merges, no overrides, no notices. The claim "only `/ID` varies" is established for this shape
  only. Re-run the probe against a corpus form before E8 closes — `pdf-translate/corpus/` has
  `choice_fields.pdf` and `dense_table.pdf` for exactly this. If a second key appears there, this
  brief's §3 is wrong and the design in §4 is insufficient.
- **Not measured: another platform.** Windows, one PyMuPDF build. Linux CI may differ.
