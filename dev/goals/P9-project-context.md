# Objective (lane B): project context any provider can pick up

> Hand this to a `/goal` session. Self-contained. Read `AGENTS.md`,
> `dev/STATUS.md`, `dev/DECISIONS.md`, `dev/goals/PROGRAM.md` (the loop
> and the P5 row), `dev/goals/HANDOVER.md` as it stood at commit
> `b157172`, and `docs/REVIEW-2026-09-02.md` §1 item 5. Not a gate;
> nothing under `pdf-translate/` changes.

---

## 1. Compass (not done)

A session from any provider, with no memory of prior work, should be able
to open the repository and know within two files what the product is,
what is locked, what is open, what to do next, and why the standing rules
exist.

Measured 12 September 2026, on `b157172`:

- **Nothing loads automatically for any provider.** No `AGENTS.md`, no
  `CLAUDE.md`, no project settings directory. The only automatic context
  was the machine-level notes and one Claude-only memory about the venv.
- **`HANDOVER.md`, the file every session was told to read first, was one
  commit stale.** The 4 September review commit touched `PROGRAM.md` and
  the review only; the handover had no mention of that review or of P8.
  Its §8 first message said "next sitting: canary run 4, do not invent a
  row" while `PROGRAM.md` said "P8 first". It stated the current test
  count as 225 in one place and 212 in another; the suite ran 225, exit
  0, no skips.
- **`docs/checklist.html`** also predated the review, and its ticks live
  in one browser's local storage.
- **The standing rules were restated across the record** instead of
  living in one place: "glossary" in 37 markdown files, "OCR" in 25, the
  one-sitting rule in 7, "winner model" in 6.
- **The two session prompts under `dev/`** described seven scripts and
  eight failure modes (eleven and fourteen ship), with Windows paths, for
  FL-150. The GPT 6 canary prompt was untracked since 5 September on a
  machine with no backup.

P5 (2 September) set this right by rule: the checklist tracks, PROGRAM
queues, HANDOVER cold-starts. It drifted in two days because
`HANDOVER.md` is a chronological narrative that every sitting must
hand-edit, and the last sitting did not. The fix is structure, not
another rule.

## 2. Done when — closed bar

1. **`AGENTS.md`** at the root: what the product is, the layout, the
   interpreter per OS (including the venv fact that lived only in Claude
   memory), the sitting loop, and the standing rules as one-liners that
   point at the ledger. Short enough to sit in every session's context.
2. **`CLAUDE.md`** at the root imports it (`@AGENTS.md`), so Claude Code
   and every other tool read the same text.
3. **`dev/STATUS.md`**: version, open rows with their state and what each
   needs, the next sitting in one line, open threads that are not rows,
   and the copy-paste first message. Rewritten at the end of every
   sitting, never appended. States no test count.
4. **`dev/DECISIONS.md`**: an append-only ledger, one dated and sourced
   entry per standing rule, rejection and parked item currently scattered
   across `PROGRAM.md`, `HANDOVER.md`, `IMPLEMENTATION.md`,
   `RECOMMENDATIONS.md` and the two reviews, with a status that can only
   be `active` or `superseded by`; plus the table of locked behaviours,
   one line per row with the brief that locked it.
5. **Nothing deleted.** `HANDOVER.md`, both session prompts and
   `checklist.html` carry the superseded or snapshot banner the
   repository already uses; `README.md`'s layout table names the new
   files and stops calling the checklist living.
6. **`PROGRAM.md`**: the loop gains the STATUS line; "how to start a
   session" points at `AGENTS.md`; this row is appended; P5's file
   assignment is superseded in the ledger, not edited.
7. **The GPT 6 canary prompt is committed**, in its own commit.
8. **`pdf-translate/` untouched**: `git diff --stat b157172 --
   pdf-translate/` is empty, `metadata.version` stays 47, the suite and
   `claude plugin validate . --strict` still pass.

## 3. Not done when

- A version bump, or any edit under `pdf-translate/`
- A per-provider context prompt (the canary prompts under `dev/canary/`
  are the only provider-specific text, and they are about fitness, not
  context)
- A wiki, a database, a generator, or anything outside the repository
- Moving or rewriting the dated reviews or the closed briefs
- A test count anywhere but the CI log

## 4. Method

Read the whole record; list every standing rule, rejection and parked
item with the file and date it first appears; write the four files; add
the banners; run the suite and the manifest validation; commit.

## 5. Invariants

One home per fact: `STATUS.md` alone says what is open; `DECISIONS.md`
alone says why a rule exists; `PROGRAM.md` alone holds the bars;
`AGENTS.md` points. Supersede, never rewrite.

## 6. Proof

A cold read of `AGENTS.md` then `STATUS.md` names P8 as the next sitting
and agrees with `PROGRAM.md`; no file but the CI log states a test
count; the `pdf-translate/` diff is empty; suite and validation green.

## 7. Closing note — 12 September 2026, closed

**The premise, restated from the measurement.** On `b157172` a session of
any provider loaded nothing, and one that read the handover as told would
have run canary 4 instead of P8. The record had the content; it had no
entry point, mixed current state with chronology, and kept the same rule
in dozens of places.

**Done bar, item by item.**

1. **`AGENTS.md`**: 97 lines, 783 words, wrapped at the repository's
   column. Over the 80-line target the recommendation set; the cost that
   matters is tokens, about a thousand by word count, roughly a sixth of
   what `SKILL.md` costs on invoke. What the product is, the layout, the
   interpreter per OS (the venv fact that lived only in Claude memory is
   now here), the sitting loop with the STATUS and DECISIONS steps, and
   nine one-line rules each pointing at its ledger entry.
2. **`CLAUDE.md`**: one sentence and `@AGENTS.md`.
3. **`dev/STATUS.md`**: 70 lines. Version, the three open items (P8 queued
   and next, P4 blocked with the blocker named, 32–52 waiting on P8 by
   D-25), four open threads that are not rows (canary 4 and the GPT 6
   prompt unrun; the `SKILL.md` description the 4 September review asked
   to narrow, undecided; the parked hypotheses; what nobody has verified),
   and the first message. No test count anywhere in it.
4. **`dev/DECISIONS.md`**: 26 ledger entries, D-01 to D-26, each dated and
   sourced; D-21 (P5's file assignment) is superseded by D-26 and its row
   is otherwise untouched. 49 locked-behaviour rows: 01–31, eleven from
   the audit roadmap, seven lane B rows, each naming the brief or audit
   section that locked it.
5. **Nothing deleted.** Superseded banner after the H1 of `HANDOVER.md`
   and both session prompts; a snapshot banner under the tracker's H1 in
   the audit page's own style; `README.md`'s layout table gained rows for
   the two root files, the two `dev/` files and the 4 September review,
   stopped calling the checklist living, and stopped pointing at the
   handover for a count.
6. **`PROGRAM.md`**: the loop gained the STATUS/DECISIONS line before
   STOP; "how to start a session" points at `AGENTS.md`; this row is
   appended as its own section; the *What is already locked* list is
   frozen, not edited.
7. **The GPT 6 canary prompt** is commit `ca2dd06`, on its own.
8. **`pdf-translate/` untouched**: `git diff --stat b157172 --
   pdf-translate/` is empty; `metadata.version` 47 and `plugin.json`
   47.0.0 unchanged; the suite after every edit: 225 tests, OK, exit 0,
   no skips, 31 s with the venv interpreter; `claude plugin validate .
   --strict` exit 0.

**Proof.** `grep` over `AGENTS.md`, `dev/STATUS.md` and `PROGRAM.md` for
what comes next returns P8 in every file and canary 4 in none of the live
text; `grep -E '[0-9]{2,3} tests'` over the five live files returns
nothing; every ledger row has seven pipes and every locked row four.

**Not done**, as the brief asked: no version bump, no edit under
`pdf-translate/`, nothing deleted, no per-provider context prompt, nothing
outside the repository. Not verified here: that a tool other than Claude
Code and Codex reads `AGENTS.md` by that name; any that does not gets the
same one-line pointer `CLAUDE.md` is.
