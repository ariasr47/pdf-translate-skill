# Canary run 4 — 25 September 2026: Opus 5.5 beside Opus 5

Rodrigo asked for Opus 5.5 to be added to the canary and compared with
Opus 5. Opus 5's last canary was run 3, on 3 September, on skill v45. The
skill has changed by 32 versions since, so Opus 5 was run again on the
same skill, not compared with that record.

**The same for both models:**
- the `dev/canary/README.md` prompt, word for word, plus the same three
  environment sentences: the run directory, the venv interpreter, and no
  writes outside the run directory;
- the fixture, regenerated once (sha256 `c1a357be…e0e2`);
- the target, Spanish;
- the skill, a frozen `git archive` of `4793f38` at `metadata.version` 77,
  which is the tip of PRs #42 to #48. Checked unchanged between the two
  runs; the only stray files, bytecode from the evaluator's own scoring,
  were removed before Opus 5 started;
- the agent type, general-purpose, with isolated, empty run directories
  and no coaching.

**Different:**
- **The launcher.** Opus 5.5 ran through the Agent tool, inheriting the
  session's model. Opus 5 ran through a workflow agent pinned to
  `claude-opus-5`, because the Agent tool can only choose "opus" in
  general. Asked, it named itself "Opus 5, claude-opus-5".
- **Wall time is not comparable.** Both runs shared the machine with other
  work: R-50's A/B runs, and later its verification passes.

| | Identity | Lookup | Identifiers | Visual | Honest | Total | Cost |
|---|---|---|---|---|---|---|---|
| **Opus 5.5** | 1 | 1 | 1 | 1 | 1 | **5** | ~268k tok, 95 calls, 14.7 min |
| **Opus 5** | 1 | 1 | 1 | 1 | 1 | **5** (run 3 on v45: 5) | ~267k tok, 98 calls, 18.8 min |

## The objective half, measured by the evaluator

| | neutral verify | as invoked | identifiers | qa_check | build rounds |
|---|---|---|---|---|---|
| Opus 5.5 | exit 1: the kept school name | exit 0, 15 PASS, 2 REVIEW | 4/4 | 0 errors, 1 warning | 5 |
| Opus 5 | exit 1: the kept school name | exit 0, 15 PASS, 2 REVIEW | 4/4 | 0 errors, 1 warning | 4 |

Both kept 13 of 13 fields with the same names, types and rects. Both left
the `/Opt` exports unchanged, captioned the button "Imprimir", added a
Spanish information-only notice on page 1, and localized "Friday, May 8".

## What differed

**The rubric cannot tell them apart.** Both scored 5/5 with the same
objective results, at the same token cost within 1%.

The differences are in how they worked:
- **The quoted English title.** Opus 5.5 kept it by allowlisting it, and
  said so. Opus 5 worded the notice around it, so it needed no allowlist.
- **The leader-gap label.** Both arrived at "Importe adjunto". Opus 5 got
  there by measuring four candidates' widths against the source's
  77.26 pt; Opus 5.5 got there by rendering three candidates in turn.
- **Findings in the skill.** Opus 5.5 reported four problems in the skill's
  scripts, three reproduced here. Opus 5 avoided the worst of them before
  it could bite, noted a second, and made one observation that is not
  reproduced here.

## What it found

Three proposals are filed in `docs/REQUESTS-from-product.md`, 25 September:
1. **`pipeline.py init --widget-text` overwrites the authored
   `widget_text.json` with a fresh scaffold.** Opus 5.5 reported it; Opus 5
   avoided it by authoring into a separate file. Reproduced: 5 authored
   targets became 5 nulls.
2. **`/Lang` loses its region subtag.** `es-US` is written as `es`, while
   retypeset logs `es-US`. Both models noted it; reproduced.
3. **The mapping's `document` block is undocumented.** It feeds the review
   prompt's identity slots. Opus 5.5 reported it; confirmed in the code.

**Recorded, not reproduced:**
- Opus 5.5 saw page 1's ink ratio move between two builds that render
  pixel-identical.
- Opus 5 noted that `compliance.md`'s title-keep advice does not warn that
  a target word which is also a source word joins the run.

## Records

`2026-09-25-run4-opus-5.5.md` and `2026-09-25-run4-opus-5.md`.
