# Objective: a notice may name the form it translates

> Hand this to a `/goal` session. Self-contained. Read
> `references/compliance.md` §1, `scripts/verify.py` (`scan_leaks`,
> `collect_identifier_spans`, `missing_identifier_spans`) and
> `dev/canary/runs/2026-09-02-fable-5.1.md`. Do not weaken the leak scan
> generally. Not FL-150.

---

## 1. Compass (not done)

Two things this skill says disagree with each other.

`compliance.md` tells the author that a court/government/consent document
needs a target-language notice, and that the notice must name the form:
*"This is an unofficial translation of {form number / title}"*. Naming the
source title in the source language is right — the reader has to know which
form this is.

`verify.py`'s leak scan then reads that title as three or more consecutive
source-language words and FAILs:

```
FAIL untranslated running text (1):
   p1: Field Trip Permission Slip
```

Fable 5.1 hit this on a correct build, resolved it with
`--allow field,trip,permission,slip`, and disclosed it. Opus 5 hit the same
class on `Riverside Elementary School`. **Two of three models had to
allowlist a multi-word name on a two-page fixture.** The skill instructs a
thing and then fails it.

## 2. Done when — closed bar

1. **A title quoted in the output is not a leak.** The document's own
   `/Title` (and the source-language title as it appears in the original's
   text) is a write/find/say identifier by the skill's own rule — the reader
   must locate that form. `verify` already exempts `Form`/`Schedule` names;
   extend the same reasoning, from the ORIGINAL's title, not from an
   arbitrary allowlist.
2. **The scan does not get generally weaker.** An untranslated *sentence*
   still fails. Prove it: the existing leak fixtures must keep failing, and
   a new test must show a three-word run that is NOT the title still fails.
3. **Decide the proper-noun question and write it down.** A multi-word
   issuer name (`Riverside Elementary School`) is a different case from the
   title: it is not in `/Title`. Either handle it (the extractor can already
   see it as a repeated untranslated core mapped to itself) or state in one
   paragraph why allowlisting stays the author's job. Do not half-do it.
4. **`compliance.md` says what to expect.** Whatever the gate ends up doing,
   the reference tells the author what will happen when the notice lands.
5. **No regressions.** Full unittest + corpus green.

## 3. Not done when

- Raising the three-word threshold
- Exempting anything an author passes in `skip`
- Treating every capitalised run as a proper noun
- Silencing the scan on pages that contain a notice

## 4. Method

Constructed LTR PDF with a `/Title`, translated, plus a notice line quoting
that title. Drive shipped verify with and without the fix. Then a second
fixture whose page carries an untranslated sentence that is not the title —
it must still fail.

## 5. Invariants

Provider-neutral. The leak scan follows the SOURCE document's script. No
glossary. A refusal must stay possible.

## 6. Proof

Notice-with-title passes; untranslated sentence still fails; existing leak
fixtures unchanged. Full unittest + corpus.
