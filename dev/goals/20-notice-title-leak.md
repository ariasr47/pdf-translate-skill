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

---

## 7. Closing note — 2 September 2026, closed

**Reproduced first.** A constructed page with `/Title` and heading
`Field Trip Permission Slip`, one sentence, and the issuer line `Riverside
Elementary School`; translated to Spanish with the issuer's name kept, then
the compliance notice drawn at the foot of the output quoting the title as
a unit — the author's own step, since the skill has no notice channel.
Shipped `verify` before the fix:

```
FAIL untranslated running text (2):
   p1: Riverside Elementary School
   p1: Field Trip Permission Slip
```

Exactly the canary's two runs, from Fable's and Opus's deliveries.

**Done bar, item by item.**

1. **The title quoted as a unit is not a leak.** `verify` reads the
   original's `/Title` and hands it to the scan as a *kept phrase*: a run
   whose letters, lowercased, equal the title's is neither running nor
   isolated, in every branch (same-script words, Latin runs, non-Latin
   words, spaceless runs). Quotes, commas and case around it do not
   matter; a missing or extra word does. Kept runs are printed as a
   `note:` line, never silently dropped.
2. **The scan is not weaker.** A run that merely contains the title
   (`Field Trip Permission Slip Form`) is still running text; the
   untranslated sentence beside a notice still fails and names itself; the
   goal-15 and goal-08 leak fixtures are untouched and green. No
   threshold moved; a page with a notice is not exempt; `skip` exempts
   nothing.
3. **The proper-noun question, decided.** An issuer's multi-word name is a
   *translation decision*, not a fact the scan can know: the issuer's own
   parallel text may translate it (`Departamento de Vehículos
   Motorizados`) or keep it (`Riverside Elementary School`), and step 1's
   lookup is where that is settled. Allowlisting therefore stays the
   author's job — and it is now sayable in the author's terms:
   `--allow "Riverside Elementary School"` is a **phrase** that matches
   that run and nothing else, where the only option before was
   `--allow riverside,elementary,school`, three words that then passed
   anywhere on the page. (A phrase passed to `--allow` used to be accepted
   and silently match nothing.) Not done, by choice: exempting cores the
   author identity-mapped — that would make "map everything to itself"
   pass the scan, which is the shortcut the skill forbids.
4. **`compliance.md` says what to expect**: quote the title as one unit in
   the source language with target-language words around it; the scan
   keeps it and notes it; a title that is not the file's `/Title`, or an
   issuer's name, is allowlisted as a phrase and disclosed. `SKILL.md`
   step 6 says the same in one sentence; the verify docstring for gate 4
   carries the rule.
5. `NoticeTitleTests` (four tests): the notice passes with the note; the
   untranslated sentence fails beside it; the issuer name needs the
   phrase, and the phrase does not clear a different run of the same
   words; `scan_leaks` keeps a run equal to the title only. 166 tests, no
   skips, green locally; corpus unchanged. `metadata.version` 31 → 32.

**Not done, as the brief asked:** the three-word threshold is untouched;
nothing in `skip` is exempt; no capitalisation heuristic; the scan runs
on every page.

**Left on the record.** The skill still has no channel for adding the
notice itself; Fable wrote its own script and re-canonicalised the text
layer afterwards. That is a lane B candidate, not a row from this
sitting.
