# Objective: a wrong term of art cannot reach a delivery without a second reader, and every reviewed job makes the next one checkable

> Hand this to a `/goal` session. Self-contained. Read `pdf-translate/SKILL.md`
> steps 1, 3 and 8, `references/review.md`, `references/compliance.md`,
> `pdf-translate/pdf_translate/qa_check.py` (the `--glossary` path),
> `dev/jobs/fl150-ja-2026-09-17/` (the job: mapping, `review.json`,
> `NOTES.md`), and the `docs/DECISIONS.md` rows of 2026-09-17.
> **P0 — top of the order once PRs #10 and #11 have merged.** This is a
> new authoring-workflow surface: design canvas in `docs/` first, then a
> plan, then Sonnet lanes.

---

## 1. Compass (not done)

Measured on the first FL-150 → Japanese job run on the current skill
(17 September 2026, skill v56). `verify` exited 0 and `qa_check` reported
0 errors on a build that carried 世帯主 for "head of household" — in Japan
the registered household head, usually the married breadwinner; in US tax
law a status reserved for the unmarried, so a married reader ticks the
wrong box on a sworn form — and 相手方の親 for "the other parent", which
reads as the respondent's parent. Neither is visible to any gate, and no
gate could see them: the page was right and the strings were present.

They were caught only because a person asked for a review after delivery:
an independent MQM pass (Opus, given only the pairs and the renders) found
31 items — 1 critical, 6 major, 24 minor — of which 24 were accepted and 7
rejected on measurement; a human read of page 1 agreed with every accepted
item. The keep/translate rules produced zero findings: that half of the
skill already generalises and is enforced by three gates.

The misses are categories, not page facts, and they transfer to every
language pair:

1. **Legal-status homonyms** — a target word that names a *different*
   status in the target country (世帯主 / head of household).
2. **Party-role words reused inside compounds** — 相手方 was already
   "Respondent", so 相手方の親 grew a possessive reading; 他方の親 does not.
3. **Verbs of legal acts by object** — "executed" (an order) became 締結,
   a contract verb.
4. **Head nouns narrower than their examples** — 光熱費 excludes the water
   and trash its own parenthetical lists (水道光熱費).
5. **Label sets mixing patterns** — 月額／週額／時給; a set shares one
   pattern (月給／週給／時給).

Two things are missing from the skill, not from the model: nothing forces
a per-term lookup before authoring, and the reviser step in `review.md` is
a deliverable the workflow can run late or skip. The reviser is not
perfect either — two of its seven top findings were wrong on the facts —
so the loop has to measure the reviewer as well as the author.

## 2. Done when — closed bar

1. **`pipeline.py review --work DIR`** writes `review_pairs.md` (every
   authored pair, merges, overrides, notices) and `review_prompt.md` (the
   MQM prompt from `references/review.md` with the identity facts filled
   from `NOTES.md` / `segments.json`); **`--ingest review.json`** validates
   the schema and prints the open findings.
2. **`pipeline.py finish` refuses** while `review.json` is absent or any
   finding is `open`. `--no-review` is the only way past; it prints one
   REVIEW line that the delivery must carry.
3. **`references/terminology-failure-modes.md`**, the twin of
   `failure-modes.md`: the five categories above, each with the FL-150
   instance and the rule, named in `SKILL.md` step 1. Step 1's identity
   record gains a **terms-of-art table** (term, established rendering,
   source) for every status, role, benefit programme and verb of legal act
   on the page, written before authoring and checked by the reviser.
4. **A termbase per document class and language**: `--ingest` appends
   every accepted terminology finding as `(source term, target term)` to
   `glossary.csv` beside the job; the existing `qa_check --glossary`
   enforces it on the next job of that class. The skill ships no glossary
   (MIT stance, `SKILL.md`); the product keeps them (E11, shared oracle).
5. **The canary scores terminology**: `dev/canary/score.py` gains an axis
   fed by `review.json` — accepted findings per 1,000 source words, and
   the reviewer's false-positive rate — so the curve is measured.
6. Tests for 1, 2 and 4 (red first); docs; `metadata.version` bump.

## 3. Not done when

- a model is fine-tuned, or a global glossary is shipped inside the skill;
- the reviser is presented as replacing the human sign-off for court,
  government, medical or legal filings (`review.md` §2 stands);
- `finish` can pass an open finding without the REVIEW line in the
  delivery;
- the terms-of-art table is optional prose rather than a slot the reviser
  reads.

## 4. Proof

Re-run the FL-150 job from `dev/jobs/fl150-ja-2026-09-17/` with the loop:
`finish` refuses before `review.json` exists and passes after every
finding is resolved; the `glossary.csv` produced from its `review.json`
makes `qa_check` flag 世帯主 on a fresh mapping that reintroduces it.
