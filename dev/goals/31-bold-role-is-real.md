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
