# Objective: the leak scan follows the source document's script, not Latin

> Hand this to a `/goal` session. Self-contained. Read
> `pdf-translate/SKILL.md` step 6, `scripts/verify.py` (`scan_leaks`,
> `source_words_from_segments`, gate 4), then `corpus/verdicts.json`. Do
> not implement RTL shaping, widget text, a glossary, or OCR. Not FL-150.

---

## 1. Compass (not done)

Gate 4 looks for Latin words (`[A-Za-z]{4,}`). For a Japanese, Chinese,
Arabic, Russian or Greek source translated into English or Spanish, the
regex matches the *translation*: a correct JA→EN output FAILs
"untranslated running text". `--source-words-from` does not help: it
harvests Latin tokens from the source, finds none, and falls back to the
same regex. And a Japanese source left untranslated in an Arabic target
matches nothing, so it PASSes. The description says any language to any
language; the gate only agrees when the source is Latin. This session
keys the scan to the script the source document is written in.

## 2. Done when — closed bar

1. **Detection.** `verify.py` detects the dominant script of the
   original's text layer (letters only; Han + kana count as one family
   `CJK`) and of the output, and prints both. `--source-regex` still
   overrides the isolated-token regex.
2. **Different scripts (JA→EN, AR→EN, RU→ES, EN→JA…).** Runs of the
   *source* script in the output are the leaks: for space-delimited
   scripts, three or more consecutive source-script words (≥ 4 letters
   for Latin, ≥ 2 otherwise) FAIL, one or two are REVIEW; for spaceless
   scripts (CJK, Thai, Lao, Khmer, Myanmar) a run of six or more
   source-script characters FAILs, shorter runs are REVIEW. Latin-source
   behaviour is byte-for-byte what it is today.
3. **Same script.** When source and output share a space-delimited script
   the scan uses the document's own words automatically (harvested from
   the original, script-aware); `--source-words-from` is still accepted
   and preferred when given. When they share a spaceless family the scan
   prints one REVIEW line saying it cannot separate them and does not
   FAIL on that basis.
4. **Constructed, not FL-150.** A Japanese source (bundled `cjk` font)
   translated to English → verify PASS with no flags; the same output
   with one Japanese line left untranslated → FAIL naming the run; a
   two-character leftover → REVIEW only. An Arabic source → English (skip
   if no Arabic-capable TTF) → PASS; three Arabic words left → FAIL.
5. **Corpus.** `corpus/ja_source.pdf` and `corpus/ar_source.pdf` with
   verdict `translate` (extract exits 0, strip clean, not an OCR layer).
6. **No regressions.** unittest + corpus green; `LeakScanTests`
   unchanged; EN→JA canary flags (`--fill-text`, `--translations`,
   `--allow`) behave as before.
7. **Docs.** `SKILL.md` step 6: the scan follows the source script;
   `--source-words-from` is optional for same-script pairs; spaceless
   same-family pairs get a REVIEW, not a gate.

## 3. Not done when

- A `regex`/ICU dependency for script properties (a range table is enough)
- Per-language stop-word lists or a glossary
- Transliteration detection
- RTL shaping, widget text, OCR

## 4. Method

Tiny constructed PDFs: Japanese source via `pymupdf.Font('cjk')` (bundled
Droid Sans Fallback), English output via the test TTF; Arabic source via
the HarfBuzz path with a system TTF, `SkipTest` when none. Import shipped
`verify` and drive `verify.verify(src, out)` with no flags.

## 5. Invariants

Latin-source results identical to today; field / fill / ink / placement /
chrome / identifier / empty / caption / invisible gates untouched;
provider-neutral.

## 6. Proof

In-repo tests for detection, different-script FAIL/REVIEW/PASS, same-script
auto mode, Arabic (skippable). Corpus rows. Full unittest + corpus.
