# Objective (lane B): `SKILL.md` under 500 lines, by moving and not deleting

> Hand this to a `/goal` session. Self-contained. Read
> `docs/REVIEW-2026-09-02.md` §1 (item 3), §3.2 and §5 (P3); the Anthropic
> skill best-practices page (body under 500 lines; references one level
> deep); the Agent Skills spec (instructions under about 5,000 tokens).
> Do not touch the frontmatter `description`. Do not add Claude Code-only
> frontmatter fields. Delete no rule. Not FL-150.

---

## 1. Compass (not done)

`SKILL.md` is 595 lines (573 in the body), 4,833 words and about 7,600
tokens on invoke as `claude plugin details` measures it, against
Anthropic's "under 500 lines" and the spec's "under about 5,000 tokens".
It has grown with every row since the 1 September audit measured 340
lines, because every gate wrote its paragraph into the workflow.

The cost is mechanical, not stylistic: after a context compaction Claude
Code re-attaches only the **first 5,000 tokens** of an invoked skill. On a
long job the tail — verify, field fonts, deliver — is what disappears,
and those are the steps that decide whether a file ships.

The canary showed the skill text moves model behaviour, so nothing may
be lost. Detail moves into `references/`, one level deep, each file with
a contents line; the workflow keeps the commands, the rules in one
sentence each, and the pointer.

## 2. Done when — closed bar

1. **Body under 500 lines**, measured with the frontmatter excluded, and
   the on-invoke estimate from `claude --plugin-dir . plugin details
   pdf-translate` recorded before and after (target: about 5,000).
2. **Moved, not deleted.** Step 2's encryption, usage-rights and
   certification paragraph → `references/compliance.md` (a new section);
   step 2's captions and widget-text paragraphs → `references/widget-text.md`;
   step 6's gate-by-gate prose (leak scan, `--translations`, canonical text
   layer, chrome, `/Opt` parity, identifiers, override markers) →
   `references/gates.md`; the expansion table → `translations-format.md`.
   Each moved rule is still stated in the workflow in one sentence with
   the pointer. The visual-pass rule, the identity record, the
   write/find/say bullets and every "never" stay in `SKILL.md` verbatim.
3. **References are one level deep** from `SKILL.md`, listed in its
   References section with when to read each; every reference over 100
   lines opens with a contents line.
4. **Frontmatter unchanged** except `metadata.version`; six spec fields,
   nothing Claude Code-only.
5. **Suite green**, corpus unchanged, `plugin.json` bumped with
   `metadata.version`. Canary run 2 (C2) follows this sitting and is the
   proof the shorter text still steers: it must score no lower than run 1
   on the same fixture.

## 3. Not done when

- Removing or softening any rule, refusal or "never"
- Rewriting the description or adding `when_to_use`, `paths`, `context`
- Summarising a moved paragraph so loosely that a reader of `SKILL.md`
  alone would do the wrong thing (the one-sentence rule must be correct
  on its own; the reference adds the why and the how)
- Running the canary in the same sitting

## 4. Method

Count first. Cut the three regions into their references with a
contents line; leave one sentence and a pointer each; count again; run
the suite; record both counts and both token estimates.

## 5. Invariants

Provider-neutral. Spec-clean frontmatter. Every rule has one home.

## 6. Proof

Line and token counts before and after; the diff shows moves, not
deletions; suite green; C2 next.

---

## 7. Closing note — 2 September 2026, closed

| Measure | Before | After |
|---|---|---|
| `SKILL.md` lines (total / body) | 595 / 573 | 515 / **493** |
| words | 4,833 | 4,016 |
| on-invoke tokens (`claude plugin details`) | ~7.6k | ~6.4k |
| always-on tokens | ~160 | ~160 |
| `references/` lines | ~730 | 1,035 |

**Moved, not deleted — five regions, each leaving one-line rules and a
pointer:**

1. Step 2's captions, widget-text and dropdown paragraphs →
   `references/widget-text.md` (new, 53 lines, contents line).
2. Step 2's encryption, usage-rights and certification paragraph →
   `references/compliance.md` §4.
3. Step 3's expansion table → `references/translations-format.md`, "The
   expansion band".
4. Step 6's gate-by-gate prose → `references/gates.md` (new, 113 lines,
   contents line, plus a table of every always-on gate that the workflow
   never had).
5. The Requirements section's shaping paragraph → `references/fonts.md`
   (new last section; contents line added), and step 5's mechanics —
   glyph coverage, alignment and weight, document metadata, rotated
   lines, the two failure modes — → `references/retypeset.md` (new, 60
   lines).

What stayed verbatim: the identity record, lookup, the write/find/say
bullets, the visual-pass paragraph, every refusal and every "never", the
delivery section. Each moved rule is still stated in the workflow in a
sentence that is correct on its own. The References section lists every
file with when to read it; all are one level deep.

**Frontmatter:** unchanged except `metadata.version` 36 → 37;
`plugin.json` 37.0.0. `claude plugin validate . --strict` passes; 176
tests, no skips, green locally; corpus untouched (no script changed).

**The honest residual.** The token target was "about 5,000" and the body
is about 6,400. Getting there would mean moving step 3's language
decisions or step 8's delivery rules, which are the paragraphs the canary
showed steer a model, or deleting rules — both outside this bar. After a
compaction Claude Code re-attaches the first 5,000 tokens, so the last
fifth of the body (field fonts, deliver, references) is still what a long
session loses. Canary run 2 (next) includes one deliberately long session
to see whether that tail matters in practice; if it does, moving step 8's
delivery prose into `review.md` is the next cut.
