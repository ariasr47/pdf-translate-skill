# The canary — is this model fit to author `translations.json`?

Not a gate. Not part of the pipeline. The scripts already refuse structural
failures; nothing in them can tell a plausible wrong term from the right one.
The canary answers a different question: **does this model do the three things
the skill asks a human-or-model author to do?**

Run it on a different day from any gate, and never put a winner in
`SKILL.md`. The point is to know which models to trust as the author, not to
turn the skill into a leaderboard.

## Fixtures

Generated, never committed:

```bash
python3 dev/canary/make_fixture.py
```

Two pages, chosen so one document exercises all five axes at once:

- **page 1** — the school permission slip from `evals/make_fixtures.py`:
  twelve fillable fields, a dropdown with export values, tooltips, dot
  leaders, a `$12.00` fee and a `Print` pushbutton.
- **page 2** — write/find/say payload: a quoted `"Attachment A"`, a
  `Schedule Q`, a URL, `8 1/2-by-11-inch` paper and `Form RS-14`. These are
  exactly the shapes `extract_segments.write_find_say_hits` looks for, so
  axis 3 is machine-checkable rather than a matter of opinion.

`garden_flyer.pdf` is built alongside it and is the non-form alternative
(white-on-colour banner, a price, a URL, two wrapped paragraphs).

## The prompt (identical for every model)

```
Translate {fixture} into {target language}, keeping the layout and every
form field working. Use the pdf-translate skill at {path}.
```

Nothing more. Telling the model what to look for is what the skill text is
for; if it has to be said again in the prompt, the skill text is the thing
to fix.

## Scoring

Five axes, 0 or 1 each. Record the evidence, not the impression.

| # | Axis | 1 point when |
|---|---|---|
| 1 | **Identity record** | All four facts written down before any translation: class, issuer, parallel text (URL, `none`, or `not searched`), identifiers. |
| 2 | **Lookup** | It actually searched for a published translation of this document class, and said what it found — including `none`. A model that skipped the step and did not say so scores 0. |
| 3 | **Identifiers kept** | `Attachment A`, `Schedule Q`, the URL, `$`, and the paper size survive in the source language, or are bilingual `target (Source)`. Transliteration scores 0. |
| 4 | **Visual pass** | It rendered pages and looked at them, and the delivery names something it found that way. Claiming a visual pass without a finding scores 0. |
| 5 | **Honest delivery** | The summary names its judgment calls: `allow_scale` cores, what happened to `/Perms` and encryption, that the file is no longer tagged, that the output is a working copy and not a certified translation. |

Also record, without scoring: how many rebuild rounds it took, whether
`qa_check.py` findings were addressed or ignored, and whether it invented a
glossary (it should not).

### The objective half

```bash
python3 dev/canary/score.py dev/canary/fixtures/permission_form.pdf RUNDIR [...]
```

Axes 1, 2, 4 and 5 are judgements a person makes by reading the delivery.
Axis 3 is not, and neither is "did the thing they produced pass the gates".
`score.py` finds each run's output, runs `verify.py` and `qa_check.py`
against it, and reports every write/find/say span from the original as kept
or lost. Run it before scoring, so the arguable half is the only part
anyone has to argue about.

The same five checks are also written as graders in
`pdf-translate/evals/` (three cases for `claude plugin eval`), so the
objective half can be run on demand against the plugin without spawning a
canary by hand. That suite is the objective half **only**: the visual pass
has no grader and never will, and the identity-record and honest-delivery
axes go to an LLM judge there rather than to you. The canary is still the
whole rubric, and it is what opens rows. Those cases have not been executed
yet — `claude plugin eval` is in early access and is not enabled on this
machine; `pdf-translate/evals/README.md` says exactly what that leaves
unverified.

## Reporting

Write `dev/canary/runs/<date>-<model>.md` with the five scores, the evidence
line for each, and the final `translations.json`. Do not summarise across
runs into a ranking inside the skill; the file is for whoever is choosing an
author today.

## What a failure means

A model that scores 0 on axes 1–3 is not a model to hand this skill. That is
a staffing conclusion, not a reason to add a gate: a gate whose only purpose
is to launder a weak author's output makes the pipeline worse for everyone
else.
