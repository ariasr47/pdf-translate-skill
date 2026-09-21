# Row 32 design canvas — the terminology loop

The design pass that goes before the build, per the working agreement's
"design before build" rule: row 32 adds a new authoring-workflow surface
(`pipeline.py review`, two generated files, a refusal in `finish`), so the
surfaces were drawn before any code was planned.

Brief: `dev/goals/32-terminology-loop.md`
Plan that came out of it: `docs/plans/2026-09-17-terminology-loop.md`

## What is here

Nine source files. Every `*.dc.html` is one artboard on a pan/zoom canvas;
`canvas.json` places them and picks the opening view.

| File | Artboard |
| --- | --- |
| `Main.dc.html` | the loop end to end, with the measured evidence beside it |
| `OpenQuestion.dc.html` | the three questions the brief does not answer, each costed |
| `ReviewCommand.dc.html` | `review --work` and `--ingest`, as consoles |
| `FinishRefusal.dc.html` | the three refusal cases and the `--no-review` escape |
| `ReviewPairs.dc.html` | the generated `review_pairs.md` |
| `ReviewPrompt.dc.html` | the generated `review_prompt.md`, slots highlighted |
| `TermsOfArt.dc.html` | the step-1 table and the five terminology failure modes |
| `Termbase.dc.html` | `glossary.csv`, the re-catch on the next job, the canary axis |

The seeded output (`terminology-loop.html`, ~2.5 MB) is **gitignored** — it
is a build artifact, mostly editor payload, and it re-seeds from these nine
files in one command.

## Rebuild it

Needs `node` (nvm-windows: prepend `C:\nvm4w\nodejs` to PATH if the tool
shell cannot find it) and the bundled `design` skill's base directory, which
the `/design` skill re-extracts on invocation.

```bash
node "<design skill base>/seed-canvas.mjs" \
  --template "<design skill base>/payload.template.html" \
  --out terminology-loop.html --title "Terminology Loop" \
  --artboard Main.dc.html --artboard OpenQuestion.dc.html \
  --artboard ReviewCommand.dc.html --artboard FinishRefusal.dc.html \
  --artboard ReviewPairs.dc.html --artboard ReviewPrompt.dc.html \
  --artboard TermsOfArt.dc.html --artboard Termbase.dc.html \
  --canvas canvas.json
```

Then `--check terminology-loop.html` must print `ok:` with the title and all
nine files. The result opens in a browser on its own, and was published as an
Artifact on 2026-09-17.

## Fidelity rules these artboards follow

Every console line is lifted from real source, never invented — the first
draft carried made-up job statistics and they were replaced with measured
ones. If you edit an artboard, keep this true:

- Finding lines use `qa_check.main`'s exact column shape (`qa_check.py:386`):
  `severity:5`, `kind:13`, `core[:48]!r`, then the detail. The 48 is a real
  truncation, not an ellipsis.
- Gate lines use `verify`'s `REVIEW <gate>: <detail>`.
- Commands are named by subcommand. Two spellings run: `python3
  scripts/pipeline.py …`, which is what `SKILL.md` documents and what the
  thin wrappers from PR #2 exist for, and `python3 -m pdf_translate.pipeline
  …`. The consoles use the package form. Only running the package module by
  path (`python3 pdf_translate/pipeline.py`) raises `ImportError`, since the
  modules import each other relatively — that is by design, not a defect.
- Job counts are the real FL-150 → ja job in `dev/jobs/fl150-ja-2026-09-17/`:
  **247 cores, 13 merges, 5 overrides, 1 notice**; **31 findings** (1 critical,
  6 major, 24 minor); **25 accepted / 6 rejected** by the file's own
  resolutions, and **11 accepted terminology**. The brief says 24/7 because
  one finding resolves as "accepted with a different fix". The file is the
  measurement.
- `overrides` in a mapping are positioned multi-part placements (`page`,
  `contains`, `parts` with `x`), not cores kept in the source language.
