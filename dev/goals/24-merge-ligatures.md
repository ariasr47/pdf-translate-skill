# Objective: a merged paragraph's text layer says what the author wrote

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/retypeset.py` (`place_story_line`, `place_shaped`, the merge
> loop around `insert_htmlbox`, `canonicalize_text_layer`),
> `scripts/verify.py` (`drifted_characters`, `DRIFT_RANGES`), and
> `dev/canary/runs/2026-09-03-sonnet-5.md` and `-opus-5.md`. Not FL-150.

---

## 1. Compass (not done)

The Story engine shapes Latin text too: with a font that carries a `liga`
table (Noto Sans, most OFL faces) it substitutes the `fi`, `fl`, `ffi`
ligature glyphs. The text layer then carries **U+FB01** for "fi" (full
font) or **U+007F** (a subset that lost the ligature's code point), so
"oficina" and "firma" are not in the layer verbatim:

| Path | What the layer holds | Placement gate | Canonical-layer gate |
|---|---|---|---|
| merge through `insert_htmlbox`, full Noto Sans | U+FB01 ×5 on a constructed paragraph | FAIL (correct output) | PASS (not in the drift list) |
| merge, subset font (Opus) | U+007F | FAIL under `--translations`; **silent without it** | PASS |
| single line through TextWriter | no ligature | — | — |

Two models found it independently on the same evening; one reworded
("administración" for "oficina"), one stripped `liga` from the font before
subsetting. Any EN→ES/FR/DE/PT job with a merged paragraph hits it. The
same applies to the inline-markup path (`place_story_line`), which is the
Story engine too.

## 2. Done when — closed bar

1. **The layer holds the authored code points.** Either the Story CSS
   disables discretionary and standard ligatures for these runs
   (`font-variant-ligatures: none` / `font-feature-settings: "liga" 0,
   "clig" 0` — test which MuPDF honours), or `canonicalize_text_layer`
   maps each ligature glyph to its component code points (a `bfrange`
   cannot do this; a `bfchar` with a multi-code-point destination can).
   Pick the one that leaves "oficina" verbatim in `get_text()` of a merged
   paragraph and of an inline-markup line, and say why.
2. **The gate names the class.** U+FB00–FB06 and U+007F join the
   canonical-layer drift list, so a build that still ships a ligature
   FAILs loudly with the code point, with or without `--translations`.
3. **Tests.** A constructed merge containing "oficina" and "firma": the
   layer verbatim, placement PASS, canonical PASS; the same with a subset
   font from `prepare_font`; an inline `<b>` line with "fi"; and a
   hand-built PDF whose layer carries U+FB01 that the gate must FAIL.
4. **Shaped scripts unchanged**: the Arabic, Indic and Thai fixtures do
   not move (their ligatures are the point, and `/ActualText` carries the
   logical string).
5. Full unittest + corpus green; `metadata.version` bumped.

## 3. Not done when

- Stripping features from the user's font file on disk (Opus's
  workaround) — the pipeline must not rewrite fonts it was handed
- Disabling shaping for scripts that need it
- Rewording advice in the skill text as the fix

## 4. Method

Constructed paragraph with "oficina"; reproduce the U+FB01 layer; try the
CSS switch first (smallest change), fall back to the CMap.

## 5. Invariants

The text layer reports what the author wrote. Provider-neutral. Shaped
scripts keep shaping.

## 6. Proof

`get_text()` of the merged paragraph equals the authored html's plain
text; the drift gate fails a hand-built ligature; full unittest + corpus.

## 7. Closing note — 3 September 2026, closed

**Reproduced first, and the CSS route was measured out.** A constructed
merge of the wrapped-paragraph fixture with "oficina" and "firma" in it:
retypeset exits 0, `get_text()` returns `oﬁcina … ﬁrma oﬁcial`, four
U+FB01, and `verify --translations` FAILs a correct paragraph. Both CSS
switches the brief names were tried first on MuPDF 1.28.2 —
`font-variant-ligatures: none` and `font-feature-settings: "liga" 0,
"clig" 0` — and **neither is honoured**: the layer is byte-identical with
them, without them and in the plain case. So the fix is the CMap.

**Done bar, item by item.**

1. **The layer holds the authored code points.** `ligature_gid_map()`
   reads the ligature substitutions out of the font's **GSUB** table and
   maps each ligature glyph id to its component code points; the
   `/ToUnicode` override block now emits a UTF-16BE destination string per
   entry, which a `bfchar` allows and a `bfrange` cannot. `authored_gid_map`
   folds those in after the per-character pass, so a ligature never
   overwrites a real character's mapping. Values are now the authored text
   rather than a code point — the two tests that asserted the int form say
   `' '` and `'-'` instead.

   **GSUB and not cmap, measured:** on the subset `prepare_font` builds
   for this job, `pymupdf.Font(subset).has_glyph(0xFB01)` is `0` — the
   subsetter keeps the `liga` lookup and the ligature outline but drops
   the ligature's own code point from the cmap, because the authored text
   never contained it. A cmap-based lookup finds nothing exactly in the
   case that had no other witness. GSUB finds gid 118 → `fi`.

   Only ligatures whose components are all in the authored characters are
   mapped: on this job the whole block is `{ff, fi, fl, ffi, ffl}`.

2. **The gate names the class.** `DRIFT_RANGES` gains `(0x007F, 0x007F)`
   and `(0xFB00, 0xFB06)`. The drift gate is always on, so a build that
   still ships a ligature FAILs with `U+FB01` printed, with or without
   `--translations` — both branches asserted.

3. **Tests** (`StoryLigatureTests`, 5): the merge with the full font —
   layer verbatim, placement PASS, canonical PASS; the same merge with a
   `prepare_font` subset, asserting first that the subset's cmap has no
   U+FB01 so the test proves the GSUB path; an inline `<b>oficina</b>`
   line through `place_story_line`; a hand-built layer carrying U+FB01
   that the gate must FAIL in both branches; and the map itself — empty
   for text with no ligature components, empty for a missing file.

4. **Shaped scripts unchanged.** The Arabic, Indic and Thai fixtures all
   pass untouched. Ligature substitution in those scripts is read the same
   way, which maps a lam-alef to its two logical characters — the same
   answer `/ActualText` already gives.

5. 181 tests, no skips, green locally; corpus table unchanged.
   `metadata.version` 37 → 38.

Not done, as the brief asked: nothing is written to the font file on disk;
shaping is not disabled for any script; the skill text is not the fix —
`gates.md` and `failure-modes.md` gained a paragraph each describing what
the gate now covers, which is documentation of a gate, not advice in place
of one.
