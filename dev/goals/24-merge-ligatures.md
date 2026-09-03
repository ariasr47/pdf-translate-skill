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
