# Objective: a weight the author asked for is either drawn or reported

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/retypeset.py` (the four font roles, `role()`, `_role_name()`,
> the `css` block, the `notices` loop's `bold_lead`),
> `references/retypeset.md` (Alignment and weight),
> `references/fonts.md`, and `dev/canary/runs/2026-09-03-run3-sonnet-5.md`.
> Not FL-150.

---

## 1. Compass (not done)

`fonts` takes four roles and each falls back to the nearest one the
mapping named. That fallback is right — a job with no italic face should
not fail — but it is **silent**, and the author then cannot tell a weight
they asked for from one they got.

Measured on canary run 3. Sonnet 5 wrote `"bold_lead": true` on its
compliance notice and pointed `fonts.bold` at the same subset file as
`fonts.regular`. The `<b>` markup resolved to the regular face, the
notice's lead-in rendered regular, nothing in retypeset's output
mentioned it, and the delivery's visual section called the page
pixel-faithful. Fable 5.1 hit the same thing on the same fixture, caught
it by eye, and fixed it by fetching a real bold face. Opus 5 had one from
the start. Side by side, two of the three notices are bold and one is
not.

This is row 25's shape, one level down: the pipeline quietly does
something the author then reports as if it had not happened.

## 2. Done when — closed bar

1. **retypeset says it once.** When a role a run actually used resolves
   to the same file as `regular` — bold, italic or bold-italic — it is
   named once after the build: `font roles: "bold" is the regular face;
   3 run(s) asked for it (notices[0], 2 inline)`. Not per run, not a
   warning per line.
2. **Only roles that were used.** A mapping with no bold anywhere says
   nothing. The check is about what was drawn, not what was configured.
3. **Not a failure.** A job with one face is legitimate and must still
   build; this is a line in the output, and it belongs in the delivery
   for the same reason `scale_report.json` does.
4. **The skill says to check it.** `references/fonts.md` and step 8's
   delivery bullet: name any role that fell back, as with a scaled run.
5. **Tests.** A notice with `bold_lead` and `fonts.bold` == `regular` →
   the line, naming the notice; the same with a distinct bold face → no
   line; an inline `<b>` run under a fallback → the line; a job with no
   bold at all → nothing. The existing role-fallback tests unchanged.
6. Full unittest + corpus green; `metadata.version` bumped.

## 3. Not done when

- Failing a build for a fallback
- Refusing to fall back, or fetching a face
- A line per run rather than one digest
- Guessing whether two different files are "really" the same weight
  (compare the resolved paths, nothing cleverer)

## 4. Method

The run-3 fixture with Sonnet's font block: reproduce the silent regular
lead-in, add the report, assert it names the notice and stays quiet when
a real bold face is given.

## 5. Invariants

Geometry proposes, the author decides — but the author has to be told
what was decided for them. Provider-neutral; no font is ever fetched.

## 6. Proof

The line on the fixture, its absence with a real bold face, and the
render showing the two apart; full unittest + corpus.

## 7. Closing note — 3 September 2026, closed

**Reproduced first, with Sonnet's own mapping shape.** The run-3 fixture,
a notice with `bold_lead: true`, and `fonts.bold` pointing at the same
file as `fonts.regular`:

| mapping | before | after |
|---|---|---|
| `bold` == `regular` | silent; the lead draws regular | `font roles: "bold" resolved to the regular face; 1 run(s) asked for it (notices[0])` |
| `bold` its own file | silent | silent |
| `bold` a symlink to `regular` | silent | reported |

**Done bar, item by item.**

1. **retypeset says it once**, after the build, beside the scaled-runs
   digest: the role, that it resolved to the regular face, how many runs
   asked, and their keys — deduplicated, capped at 100 characters with an
   ellipsis. One line per role, not per run.
2. **Only roles that were used.** `alias_roles` is computed once from the
   resolved paths; `role_asks` fills only when something actually selects
   that role. A job with no bold anywhere prints nothing even though
   `fonts.bold` is absent and therefore an alias — asserted.
3. **Not a failure.** A one-face job builds, exits 0 and gets the line —
   asserted directly.
4. **The skill says to check it.** `references/fonts.md` gained the rule
   and the sentence about resolved paths; step 8's delivery bullet names
   any role reported as the regular face beside `scale_report.json`.
   SKILL.md body 499 lines, unchanged.
5. **Tests** (`FontRoleFallbackTests`, 6): the notice case naming
   `notices[0]`; a distinct bold file silent; a **symlink** to the regular
   face reported, which is why `os.path.samefile` and not a string
   compare; an inline `<b>` run named by its core — the Story engine
   picks its face from the markup and not from `role()`, so that path is
   covered separately; a job that never asks for bold silent; and the
   line not being a failure.
6. 225 tests, no skips, green locally; corpus table unchanged.
   `metadata.version` 46 → 47.

Both mechanisms are covered, which is the part worth saying out loud:
`role()` records what it hands back (six call sites, each now passing its
core), and `note_markup()` records what the Story engine will resolve from
`<b>`/`<i>` in a merge, an inline line or a notice's `bold_lead`. A fix
that only covered `role()` would have missed the exact case that opened
this row.

Not done, as the brief asked: nothing fails for a fallback, nothing is
fetched, there is no line per run, and two different files are never
guessed to be "really" the same weight — only resolved paths are compared.
