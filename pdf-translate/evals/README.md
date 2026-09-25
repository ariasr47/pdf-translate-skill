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
already requires the author to run `verify.py`, directly or through
`pipeline.py rebuild`, so a run with no `PASS field parity` line either
skipped the gate or failed it — the same verdict either way.

**The judgement half.** Two `llm` graders cover the axes the canary rubric
keeps for a person: the identity record (class, issuer, parallel text,
identifiers, written *before* any translation) and honest delivery (what
it says it did matches what it did, including anything that shrank).

**The visual pass stays human.** Nothing here looks at a render. That axis
is why the canary still exists; this suite is its objective half on demand,
not a replacement for it. Neither is it a leaderboard: no grader knows or
rewards which model produced the run.

## Status — written against the validator, never executed

**These case files have never been run.** `claude plugin eval` is early
access and is not enabled for this account: every form of the command,
`claude plugin eval init --bare` included, exits with "`plugin eval` is
currently in early access". The self-test is to run `claude plugin eval`
in an **empty directory** — "early access" means not enabled, "No eval
cases found" means it is.

What changed on 3 September: the schema below is no longer reconstructed
from error strings. It is read from the CLI's own Zod schema, which is
embedded in the 2.1.236 binary, and the three cases here were checked
against it field by field. That is much stronger than guessing, and it is
still not a green run.

**Case file** — unknown top-level keys are rejected:

| key | notes |
|---|---|
| `schema_version` | required; the binary's example is `"1.0"` and it carries a max it supports |
| `name` | **required**, non-empty |
| `description`, `tags`, `plugins` | optional |
| `context` | `scaffold_script`, `history_file`, `add_dirs` — the scaffold lives **here**, not at the top level |
| `execution` | `prompt` (or a `prompt.md` body), `max_turns` (≤200, default 10), `timeout_seconds` (≤3600, default 300), `model`, `allowed_tools`, `append_system_prompt`, `env` |
| `runs` | ≤50, default 3 |
| `graders` | at least one; names must be unique |

**Graders** — one `.md` per grader, and **each grader object is
`.strict()`**, so an unknown key is an error rather than ignored. The
grader's `name` comes from the filename. The body fills `criteria` for
`llm` and `baseline`, and `pattern` for `regex`, when the frontmatter has
not set it.

| type | keys |
|---|---|
| `regex` | `target` (not `focus`), `pattern`, `flags`, `match`, `weight`, `arm` |
| `llm` | `criteria`, `focus`, `weight`, `arm` |
| `baseline` | `baseline_file`, `criteria`, `weight`, `arm` |
| `tool_used` | `tool`, `input_match`, `min`, `max`, `weight`, `arm` |
| `tool_order` | `before`, `after`, `weight`, `arm` |
| `file_exists` | `path`, `exists`, `weight`, `arm` |

`target` and `focus` take `trace`, `last_message`, `files`, or
`{source: file, path: …}` — a bare string, not `{source: trace}`.
`match` is `contains`, `not_contains` or `count:N`. `arm` is `with-only`
or `both`.

Three things here were wrong before that reading and are now fixed: the
regex graders used `focus: {source: trace}` where the schema wants
`target: trace` and would have rejected the extra key outright;
`scaffold_script` sat at the top level instead of under `context`; and
every `case.yaml` was missing the required `name`.

**Enablement.** The gate is a server-side flag scoped to an
*organization*, not to a plan or an individual account, and there is no
documented public way to request it — it is not in the plugins reference
or on the beta/preview list. If your org has it, a current binary plus a
fresh session picks it up. Otherwise the route is Anthropic support.

Whoever gets it enabled: run
`claude plugin eval . --runs 1 --threshold 0.8 --scaffold --json report.json`,
fix whatever the real validator says, and commit the report —
`dev/goals/P4-eval-automation.md` is the open row.
