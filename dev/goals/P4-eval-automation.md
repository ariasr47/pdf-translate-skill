# Objective (lane B): the canary's objective half runs itself

> Hand this to a `/goal` session. Self-contained. Read
> `dev/canary/README.md` and `dev/canary/score.py`, `pdf-translate/evals/`
> (`evals.json`, `make_fixtures.py`), `docs/REVIEW-2026-09-02.md` §5 P4,
> and `claude plugin eval --help`. Not FL-150.

---

## 1. Compass (not done)

The canary is the only thing that has ever told us whether the skill
works — both runs produced every row in lane A — and it is entirely
manual: spawn the runs, read the deliveries, run `score.py` by hand,
write a record per run. `pdf-translate/evals/evals.json` describes three
jobs in a format nothing executes; `make_fixtures.py` builds their PDFs.

`claude plugin eval` (2.1.236) runs `evals/**/case.yaml` against the
plugin, with graders, an LLM judge, a no-plugin baseline arm, a JSON and
HTML report and a `--threshold` exit code. The objective half of the
canary rubric — do the gates pass, did the identifiers survive, does
`qa_check` come back clean — is exactly what a grader can decide.

## 2. Done when — closed bar

1. **Three cases** under `pdf-translate/evals/`, one directory each, from
   the three jobs in `evals.json`: the permission slip to Japanese, the
   same slip to Spanish, the flyer to French. Each is a `case.yaml` with
   `schema_version`, the user prompt written the way a requester would
   write it (uncoached — the same discipline as the canary's one-line
   prompt), and a `scaffold_script` that generates the fixtures with
   `make_fixtures.py` so nothing binary is committed.
2. **Graders for the objective half**, one `.md` each, asserting the same
   five things `score.py` reports: `verify` exit 0 with field parity,
   `/Opt` export parity, write/find/say identifiers kept, the authored
   translations present, and `qa_check` with no errors. If the harness
   cannot invoke `score.py` itself, say so in the closing note and assert
   the same five from what the run leaves behind.
3. **An LLM grader for the two judgement axes** the canary rubric keeps
   for a person: the identity record (class, issuer, parallel text,
   identifiers — written before any translation) and honest delivery
   (what it says it did matches what it did, including anything that
   shrank or was left in the source language). The visual pass stays
   human and is named as such.
4. **One report committed** under `dev/canary/runs/` as
   `eval-<date>.json`, produced by a real run, with the command and the
   cost in the closing note. `--threshold` documents the bar.
5. `dev/canary/README.md` says how the two halves relate: the eval is the
   objective half on demand, the canary is still the whole rubric.
6. Full unittest + corpus green; `metadata.version` bumped only if the
   shipped skill changed.

## 3. Not done when

- Running it in CI on every push (cost)
- Naming a winner model anywhere
- Scoring the visual pass by machine
- Coaching the prompt so a model passes
- Committing fixtures or run outputs

## 4. Method

Convert `evals.json`'s three jobs to cases; write the graders; run
`claude plugin eval . --runs 1 --json` once; commit the report.

## 5. Invariants

The eval measures, it does not teach. No winner. The canary rubric is
unchanged; this automates the half that was never a judgement.

## 6. Proof

The report on disk, the threshold exit code, and the closing note's
account of what the run cost and what it found.

## 7. Blocked — 3 September 2026, NOT closed

**`claude plugin eval` is in early access and is not enabled for this
account.** Every form of the command exits with the same line before it
parses anything:

```
$ claude plugin eval . --case permission-slip-japanese --runs 1
`plugin eval` is currently in early access
$ claude plugin eval init --bare
`plugin eval` is currently in early access
```

`--help` works, so the flag surface is real and matches this bar
(`--runs`, `--json`, `--threshold`, `--ablation`, `--eval-dir`,
`--scaffold`, `--allow-tools`, `--judge-model`, `--max-cost-usd`). The
gate is an account-level grant; there is no local switch, and looking for
one to force would be circumventing an access control rather than doing
the row.

So bar item 4 — a real run and a committed report — is **not done and
cannot be done here**, and items 1–3 are written but **unverified**: the
harness never parsed them.

**What was done.**

- **This brief**, which did not exist. Half of the sitting was writing the
  bar down from `docs/REVIEW-2026-09-02.md` §5 and the canary rubric.
- **Three cases** (`pdf-translate/evals/permission-slip-japanese`,
  `-spanish`, `garden-flyer-french`), each a `case.yaml` with the
  uncoached requester prompt from `evals.json`, `runs: 1`, a
  `scaffold_script` that builds the fixtures so nothing binary is
  committed, and `max_turns` / `timeout_seconds` sized for a job that
  takes a canary run 15–20 minutes.
- **Graders**, five or seven per case: four `regex` graders over the trace
  for the objective half (`PASS field parity`, `PASS authored
  translations present`, `PASS /Opt export parity` on the two form cases,
  `PASS write/find/say identifiers`) plus one `not_contains` for
  `FAIL untranslated running text`, and two `llm` graders for the identity
  record and honest delivery. Weighted 2 except the leak check.
- **`pdf-translate/evals/README.md`** — how to run it, what each grader
  decides, and a *Status — not yet executed* section that says plainly the
  files have never been parsed and lists which schema facts came from the
  binary's own validation strings rather than from a green run.
- **`dev/canary/README.md`** now says how the two halves relate: the eval
  is the objective half on demand, the canary is still the whole rubric
  and is what opens rows.

**Why the graders do not call `score.py`.** The harness's grader types are
`regex | tool_order | tool_used | file_exists | llm | baseline` — none of
them runs a script, and `scaffold_script` runs *before* the case. So the
five objective checks are asserted from the run's own trace instead. That
is sound rather than a workaround: the skill's workflow already requires
the author to run `pipeline.py verify`, so a run with no `PASS field
parity` line either skipped that gate or failed it, and the verdict is the
same either way. Said out loud in `evals/README.md` as bar item 2 asks.

**Verified, and not:**

- `claude plugin validate . --strict` exits 0 with the cases in place, and
  `plugin details` still reports ~164 always-on tokens and ~6.6k
  on-invoke — the suite adds nothing to what ships into a session.
- 212 tests, no skips, green; corpus table unchanged.
- `metadata.version` **not** bumped: no shipped behaviour changed.
- **Nothing has run the cases.** No report exists, `--threshold` has never
  been exercised, and the YAML may not parse on first contact.

**To finish this row** someone needs `plugin eval` enabled on their
account. Then: `claude plugin eval . --runs 1 --threshold 0.8 --scaffold
--json report.json`, fix whatever the validator says, commit the report as
`dev/canary/runs/eval-<date>.json`, and record the cost. Only then is P4
closed.

## 8. Schema corrected against the validator — 3 September 2026, still open

The row is still blocked, but the artifacts are much less speculative than
§7 left them.

The 2.1.236 binary embeds the CLI's own Zod schema for `case.yaml` and
`graders/*.md`, not just the error strings §7 was reconstructed from.
Reading it found **three real errors** in the files written that morning:

1. Every regex grader used `focus: {source: trace}`. The schema's key is
   **`target`**, it takes a bare `trace` | `last_message` | `files` (or
   `{source: file, path}`), and each grader object is **`.strict()`** —
   so the unknown key would have been rejected outright rather than
   ignored. `focus` is the `llm` grader's key, which is where the
   confusion came from.
2. `scaffold_script` was top-level; it belongs under `context`.
3. Every `case.yaml` was missing `name`, which is required and non-empty.

Also learned, and now in `evals/README.md`: a grader's `name` comes from
its filename (so the files here are fine); the body fills `criteria` for
`llm`/`baseline` and `pattern` for `regex` only when frontmatter has not;
grader names must be unique within a case; `max_turns` ≤ 200,
`timeout_seconds` ≤ 3600, `runs` ≤ 50.

All three cases now check clean against those field lists. That is not a
green run and the README says so — nothing has parsed them.

**Enablement, answered.** The gate is a server-side flag scoped to an
**organization**, not to a plan or an individual account. There is no
documented public request path: `plugin eval` is absent from the plugins
reference and from the beta/research-preview list. The self-test is
`claude plugin eval` in an empty directory — "currently in early access"
means not enabled, "No eval cases found" means it is. Confirmed here on
2.1.236: still gated. The route is Anthropic support, asking for the org
to be enabled.
