# Objective (lane B): the extractor's warnings scale to a real document

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/extract_segments.py` (`main`), `SKILL.md` step 3 ("The
> extractor also prints warnings…" and the write/find/say bullets),
> `references/translations-format.md` (authoring order), the widget-text
> paragraph in `SKILL.md` step 2, and `dev/wild/ANALYSIS.md` §4. No gate
> changes. Not FL-150.

---

## 1. Compass (not done)

The authoring loop was designed on a four-page form. On the seventeen real
documents in `dev/wild/`, `extract_segments.main` printed:

| Document | Pages | Warnings | Per page | of which write/find/say |
|---|---|---|---|---|
| IRS W-9 | 6 | 205 | 34 | 89 |
| IRS 1040 instructions | 126 | 2,394 | 19 | 1,093 |
| GDPR | 88 | 637 | 7 | 0 |
| Medicare & You | 128 | 1,417 | 11 | 100 |
| all seventeen | 449 | 6,191 | 14 | 1,691 |

`SKILL.md` says write/find/say candidates are "halt-and-confirm, not
optional color" and the authoring order says "add overrides for every
extractor warning". At 1,093 halts on one booklet nobody confirms
anything; the list scrolls past and the one warning that mattered scrolls
with it. The kinds that need an action each are few (`inner-gap`: 24 in
the whole corpus); the kinds that need a *decision about a list* are the
bulk (merge candidates 2,484, `right-aligned` 1,485 before row 21,
write/find/say 1,691 — which stay verbatim by default and are guarded by
the identifier gate).

One more thing the corpus showed about authoring at scale: the USCIS
forms carry a visible text field `PDF417BarCode1[0]` whose `/V` is the 2D
barcode payload (`I-864|08/24/26|1`). The widget-text scaffold offers it
for translation with a `null` target, and a `null` target refuses the
build. The channel accepts an identity target; nothing tells the author
that this value is data and must be identity-mapped.

## 2. Done when — closed bar

1. **A digest, then the list.** `extract_segments.main` prints a per-kind
   count first, then at most N lines per kind (N configurable, default
   10), and points at where the full list lives (`segments.json` already
   carries every warning; say so, or write `warnings.json` beside it).
   Nothing is dropped from the JSON.
2. **The skill text scales.** Step 3 says what each kind wants:
   `inner-gap` → one override each; merge candidates → `propose-merges`,
   accept in bulk, delete the sibling-list entries; `right-aligned` →
   proposals for label columns only; write/find/say → confirm the *list*
   (they stay verbatim unless listed in `allow_translate`, and the gate
   fails a dropped one). "Halt-and-confirm" stays for the decision, not
   per line. The authoring order in `translations-format.md` matches.
3. **Data values are identity-mapped.** One sentence in the widget-text
   paragraph (step 2) and in `translations-format.md`: a `value` or
   `default` that is data — a barcode payload, an ID, a date stamp — gets
   its source string back as the target, never a translation; name the
   USCIS `PDF417BarCode1` case.
4. **A test locks the digest shape** on a constructed page with many
   warnings of one kind. Full unittest + corpus green. `metadata.version`
   bumped.

## 3. Not done when

- Silencing or dropping any warning kind
- Auto-accepting merges, overrides or `right` entries
- Changing the write/find/say gate or the widget-text refusal on `null`
- Heuristics that guess which `/V` strings are data (the author decides;
  the doc tells them how)

## 4. Method

Constructed page with 40 write/find/say hits; shipped `main`; assert the
digest and the cap. Then the prose.

## 5. Invariants

Provider-neutral. Warnings propose, authors decide. No glossary.

## 6. Proof

The digest on the fixture; the corpus probe re-run showing the new
output; full unittest + corpus.
