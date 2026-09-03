# Eval cases — the canary's objective half, on demand

Three cases for `claude plugin eval`, one directory each, from the three
jobs `evals.json` has always described:

| Case | Fixture | What it exercises |
|---|---|---|
| `permission-slip-japanese/` | `permission_form.pdf` | a fillable form, CJK, a dropdown with export values, dot leaders |
| `permission-slip-spanish/` | `permission_form.pdf` | the same form with a target that expands 15–25% |
| `garden-flyer-french/` | `garden_flyer.pdf` | a non-form: colour, white-on-blue, two wrapped paragraphs to merge |

```bash
python3 evals/make_fixtures.py --outdir evals/fixtures   # or --scaffold does it
claude plugin eval . --runs 1 --threshold 0.8 --scaffold --json report.json
```

Fixtures are generated, never committed; each case's `scaffold_script`
builds them, which is why the run needs `--scaffold`.

## What the graders decide, and what they do not

**The objective half.** `dev/canary/score.py` reports five things about a
run: `verify` exit 0 with field parity, `/Opt` export parity, write/find/say
identifiers kept, the authored translations present, and `qa_check` errors.
The `regex` graders here assert the same five — but from the run's own
trace, not by invoking `score.py`. The harness's grader types are
`regex | tool_order | tool_used | file_exists | llm | baseline`; none of
them runs a script. Reading the trace works because the skill's workflow
already requires the author to run `pipeline.py verify`, so a run with no
`PASS field parity` line either skipped the gate or failed it — the same
verdict either way.

**The judgement half.** Two `llm` graders cover the axes the canary rubric
keeps for a person: the identity record (class, issuer, parallel text,
identifiers, written *before* any translation) and honest delivery (what
it says it did matches what it did, including anything that shrank).

**The visual pass stays human.** Nothing here looks at a render. That axis
is why the canary still exists; this suite is its objective half on demand,
not a replacement for it. Neither is it a leaderboard: no grader knows or
rewards which model produced the run.

## Status — not yet executed

**These case files have never been run.** `claude plugin eval` is in early
access and is not enabled for this account (`claude plugin eval …` exits
with "`plugin eval` is currently in early access", and so does
`claude plugin eval init --bare`), so the schema below is what the shipped
binary's own validation strings describe, not what a green run proved:

- `case.yaml` requires `schema_version`; `execution.prompt` is required
  unless a `prompt.md` supplies it; `context.history_file` needs a prompt.
- Graders are `graders/*.md` with frontmatter `type:` from the six above,
  plus `weight`; `regex` takes `pattern`, `match: contains | not_contains
  | count:N` and `focus: {source: trace | last_message | files | file,
  path: …}`; an `llm` grader's body is its criteria.
- `--ablation with-without` adds a no-plugin baseline arm and is the
  default whenever a plugin resolves; graders marked with-only are then a
  plugin-fired indicator rather than part of the score.

The first person with access should run it, fix whatever the validator
says, and record the result — `dev/goals/P4-eval-automation.md` is the
open row and its bar wants one report committed under `dev/canary/runs/`.
