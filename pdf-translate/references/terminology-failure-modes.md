# Terminology failure modes — every one of these passes every gate

Contents: five ways a term of art goes wrong, each with the instance that
shipped it and the rule that catches it.

These are the twin of `failure-modes.md`, and they are worse. A silent layout
failure is at least visible in a rendered page. These are invisible
*everywhere*: the page is right, the string is present, the script is correct,
the numbers match, `verify.py` exits 0 and `qa_check.py` reports no error. The
translation is fluent, plausible, and wrong.

All five were hit on one document — the first California FL-150 (Income and
Expense Declaration) into Japanese. One of them is critical: a reader would
have ticked a box declaring a tax filing status they did not use, on a form
signed under penalty of perjury. It was caught by a second reader, after
delivery. Nothing else could have caught it.

The categories are what transfer; the instances are only evidence. Read them
as questions to ask about *your* document, in any pair.

## 1. Legal-status homonyms

**The instance.** "Head of household" → 世帯主. In Japanese, 世帯主 is the
person registered as head of a 住民票 household — normally the married person
living with their spouse. The US filing status is available only to someone
who is *unmarried* (or treated as unmarried). A married Japanese reader who is
their household's 世帯主 reads the box as describing them and ticks it. The
established rendering in Japanese-language US tax material is 特定世帯主.

The trap is reinforced by its neighbours: 独身 / 既婚・個別申告 /
既婚・合算申告 all state a marital status, and 世帯主 is the only one that
does not — so it reads as the option for "I am the head of my household",
which is exactly what it must not mean.

> **Rule.** A status the reader ticks **about themselves** is looked up in the
> target country's own law before it is translated. The source country's
> concept and the target country's same-sounding concept are different
> objects; a word that names both names neither.

## 2. Party-role words reused inside compounds

**The instance.** 相手方 was already fixed as RESPONDENT, the opposing party.
"The other parent" then became 相手方の親 — which parses as "the respondent's
parent", a different person entirely, and one who may also be in the case.

> **Rule.** A term already bound to a party never appears inside a compound
> that names someone else. Once a role word is committed, it is reserved:
> build the other term from different material (here, 他方の親).

## 3. Verbs of legal acts, chosen by object

**The instance.** An order or judgment "executed" before a date became 締結 —
the verb for concluding a *contract* between parties. A court order is not
concluded between parties; it is entered, made or served.

> **Rule.** The verb follows what is being acted on. Check the object class
> first — contract, order, statute, instrument — then pick the verb that
> class takes in the target language. A verb that is right for one object and
> wrong for another is the most fluent kind of error there is.

## 4. Head nouns narrower than their own examples

**The instance.** "Utilities (gas, electric, water, trash)" → 光熱費（ガス、
電気、水道、ごみ）. 光熱費 covers light and heat. It excludes the water and the
trash that its own parenthetical goes on to list. The head noun contradicts
its own examples. 水道光熱費 covers them.

> **Rule.** A head noun is checked against the examples in its own
> parenthetical. If any listed example falls outside the head noun you chose,
> the head noun is wrong — not the list.

## 5. Label sets mixing patterns

**The instance.** A pay-basis choice rendered 月額／週額／時給 — 額 ("amount")
twice, then 給 ("pay"). A reader scanning a column of choices reads the
pattern before the words, and a break in the pattern reads as a difference in
meaning. The set was rewritten 月給／週給／時給, the pattern Japanese forms use.

> **Rule.** Labels offered as a choice are authored **together** and read as a
> column, not translated one at a time in the order the extractor found them.
> One set, one pattern.

## What to do about all five

1. **Write the terms-of-art table before authoring** (`SKILL.md` step 1, fact
   5). One row for every status, role, benefit programme and verb of legal act
   on the page: term, established rendering, and the source you got it from.
   "No established rendering found" is a legitimate row, and a flag.
2. **Have a second reader.** `pipeline.py review --work DIR` writes the pairs
   file and the prompt; the reviser returns `review.json`; `review --ingest`
   reads it back and `finish` refuses until every finding is resolved. None of
   these five would have been found by a script, and every one of them was
   found by a reader.
3. **Let the termbase carry it forward.** Accepted terminology findings with a
   named `term` and `term_target` are appended to the job's `glossary.csv`, and
   `qa_check.py --glossary` gates the next job of that class on them. A term
   of art that has been got wrong once should not be available to get wrong
   again.
