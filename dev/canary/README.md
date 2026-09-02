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
python3 pdf-translate/evals/make_fixtures.py --outdir dev/canary/fixtures
```

`permission_form.pdf` is the interesting one: it carries a `$12.00` fee, a
`Print` pushbutton caption, a dropdown with export values, tooltips, dot
leaders and a signature rule. `garden_flyer.pdf` adds white-on-colour text,
a URL, a price and two wrapped paragraphs.

For the identifier axis, add a page with quoted and form-name payload — the
same shapes `extract_segments.write_find_say_hits` looks for:

> Write "Attachment A" at the top.
> Please attach Schedule Q.

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
