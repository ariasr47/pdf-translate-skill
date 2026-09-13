# Status — pdf-translate

**As of 12 September 2026**, written on top of commit `b157172` at the end
of lane B row P9. This file states the current state and nothing else. It
is **rewritten, not appended**, at the end of every sitting (D-26).
History lives in git, in the briefs' closing notes under `dev/goals/`, in
`dev/canary/runs/` and in the dated reviews under `docs/`.

## Shipped

| | |
|---|---|
| `pdf-translate/SKILL.md` `metadata.version` | 47 |
| `.claude-plugin/plugin.json` | 47.0.0 |
| Suite | `python -m unittest tests.test_pipeline tests.test_corpus_verdicts` from `pdf-translate/` with the venv interpreter (`AGENTS.md`). Must finish with no skips. The count is what it prints; the badge in `README.md` is CI. |
| Install | `/plugin marketplace add ariasr47/pdf-translate-skill`, then `/plugin install pdf-translate@pdf-translate-skill`. Proven from GitHub on 3 September. |

## Open

| Row | Lane | State | What it needs |
|---|---|---|---|
| **P8** — identity end to end over the wild corpus | B | **Queued, next** | One sitting. `dev/wild/e2e.py`, the instrument in `docs/REVIEW-2026-09-04.md` appendix A, over all seventeen files at expansion 1.0 with a metric-compatible face, writing `dev/wild/E2E.md` and `e2e.json`; then the loop line that re-runs it whenever strip, extract or retypeset change. The bar is the last section of `dev/goals/PROGRAM.md`; there is no brief file yet, so write `dev/goals/P8-identity-e2e.md` first. Not a fix for anything the table finds. |
| P4 — eval automation | B | **Blocked** | `claude plugin eval` is in early access and not enabled for this account (an organisation-scoped flag with no public request path). Three cases and their graders exist under `pdf-translate/evals/`, checked field by field against the CLI's own schema, never parsed. When enabled: `claude plugin eval . --runs 1 --threshold 0.8 --scaffold --json report.json`, fix what the validator says, commit the report under `dev/canary/runs/`. `dev/goals/P4-eval-automation.md` §7–8. |
| 32–52 — candidate rows from the 4 September review | A | **Waiting on P8**, by decision (D-25) | Each has a fixture and a closed bar in `docs/REVIEW-2026-09-04.md` §5; P8's table is what they are measured against. Order there: 32, 33, 34, 35, 36, then 38–39, 40–43, 44–46, then the small ones. |

Nothing else is open. Rows 01–31, the September audit roadmap, and lane B's
P1, P2, P3, P5, P6, P7 and P9 are closed, each with a closing note in its
brief or a row in `dev/goals/PROGRAM.md`.

## Next sitting

**P8.** Read `AGENTS.md`, this file, then `docs/REVIEW-2026-09-04.md` §2
and appendix A, and the last section of `dev/goals/PROGRAM.md`. Write the
brief, then do it. Not a canary; not a fix.

## Open threads that are not rows

- **Canary run 4** has not run; runs 1–3 are in `dev/canary/runs/` (run 3:
  Opus 5, Sonnet 5 and Fable 5.1, each 5/5). The unattended GPT 6 prompt
  (`dev/canary/GPT6_PROMPT.md`) exists and has not been run by anyone.
- **The description in `SKILL.md`** promises any born-digital PDF, pixel-
  faithful, and names manuals and brochures. The 4 September review §1
  measured that on dense flow documents into an expanding language the
  pipeline is a shrink-to-fit engine with no vertical outlet, and asked for
  the claim to be narrowed. Nobody has decided; row 52 (skill text) does
  not cover it.
- **Hypotheses parked in `docs/REVIEW-2026-09-04.md` §5**, to measure
  before any becomes a row: hidden-layer text (H-F), text as clip in the
  wild (H-G), the I-9's invisible `Tr 3` blocks (H-H), font family mapping
  (H-I), cross-page paragraphs (H-J). Context compaction (H-E) is untouched
  since 2 September.
- **Nobody has verified** Acrobat's rendering of the hybrid-XFA forms, a
  real dynamic-XFA file, or a real signed file; the related findings rest
  on constructed fixtures (`docs/REVIEW-2026-09-04.md` §6).

## First message for a cold session (copy this)

```
Read AGENTS.md, then dev/STATUS.md. Work in the repository root.
Interpreter: pdf-translate/.venv/bin/python on this Mac
(pdf-translate\.venv\Scripts\python.exe on Windows). Set PYTHONUTF8=1.

Everything is committed. The next sitting is P8: the bar is the last
section of dev/goals/PROGRAM.md, the instrument is docs/REVIEW-2026-09-04.md
appendix A. Write dev/goals/P8-identity-e2e.md first. Do not invent a
row, do not mix in a canary, no glossary, not FL-150 as a fixture.

When the bar is green: full unittest + corpus, bump metadata.version only
if pdf-translate/ changed, rewrite dev/STATUS.md, commit, stop.
```
