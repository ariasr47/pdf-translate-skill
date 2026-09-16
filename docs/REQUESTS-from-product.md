# Requests from product

This is the product repo's (`pdf-translator`) inbox to this skill. When the
product finds a behaviour here it wishes this library had, it goes in the
table below — not as a patch, not as a diff, not as pasted code.

**A request describes BEHAVIOUR. It never pastes code.** `pdf-translator` is
heading to AGPL-3.0; this repo is MIT. Code flows downstream from here to
there, never back — see `AGENTS.md`'s licence section. A request that
arrives as a code snippet, a diff, or "here's roughly how we did it" gets
rewritten as a behaviour description before anyone acts on it, or it gets
refused. Describe the input, the observable output, and why it matters;
this repo's own tests and corpus are what any implementation is checked
against.

## Format

`date | what the product needs | why | status`

- **date** — ISO, when the request was filed.
- **what the product needs** — a behaviour, stated as an outcome ("given X,
  produce Y"), not an implementation.
- **why** — the concrete case that surfaced the gap.
- **status** — `open`, `accepted` (being built independently here),
  `declined` (with a one-line reason), or `done` (with the version/commit
  that shipped it).

## Requests

| date | what the product needs | why | status |
|---|---|---|---|
| _(none yet)_ | | | |

Add new rows at the bottom. Do not delete a row when its status changes —
update the status column in place so the history of what was asked for
stays readable.
