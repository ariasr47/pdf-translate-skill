# Intro prompt for the Grok CLI session

> **Superseded, 12 September 2026.** The 1–2 September bakeoff prompt for
> the Grok CLI on FL-150 English→Japanese, written against an earlier
> skill (seven scripts and eight failure modes; eleven and fourteen ship
> now). Kept as the record of how that bakeoff was run. A cold session of
> any provider starts from `AGENTS.md`; a model-fitness run is
> `dev/canary/README.md`, and `dev/canary/GPT6_PROMPT.md` is its
> unattended form.

Run this **once per model you want to test** (Grok 4.6, Grok 4.5), each in its
own empty working directory. Start the session with that directory as cwd, then
paste everything between the `---` lines as your first message.

Before you start, edit the two lines marked `SET THIS`.

---

You are doing a high-fidelity PDF translation task. Work autonomously to
completion — do not ask me questions, make reasonable judgment calls and record
them.

**Reference material.** A complete, tested pipeline is provided at:

    SKILL_DIR = /absolute/path/to/pdf-translate          <-- SET THIS

Read these three things before you touch the PDF, in this order:

1. `SKILL_DIR/SKILL.md` — the workflow. Follow it.
2. `SKILL_DIR/references/failure-modes.md` — eight silent failure modes. Every
   one is a real defect that produces no error message. Treat them as
   constraints, not trivia.
3. `SKILL_DIR/references/translations-format.md` — the format of the
   `translations.json` file you will author.

Read `SKILL_DIR/references/fonts.md` when you reach the font stage.

The pipeline is seven Python scripts in `SKILL_DIR/scripts/`. They are tested —
use them rather than reimplementing. Install dependencies first:
`pip install pymupdf pikepdf fonttools`. Network access is needed to download a
font.

**The task.** Translate the official California Judicial Council form FL-150
("Income and Expense Declaration") from English into natural-sounding Japanese.
The source PDF is at:

    SOURCE_PDF = /absolute/path/to/fl150_original.pdf     <-- SET THIS

Use that exact file. Do not re-download it — every run in this comparison must
start from identical bytes.

Requirements, in priority order — when they conflict, the higher one wins:

1. **Structure.** All 266 fillable form fields must carry over with identical
   names, types, and positions, and must still accept input — including
   Japanese text typed into them by a user.
2. **Layout.** Visually indistinguishable from the original: same tables,
   rules, columns, checkboxes, dot leaders, page count and page sizes. Only the
   text changes.
3. **Translation.** Natural Japanese in California family-law register, using
   established Japanese legal terminology rather than literal renderings. Where
   a translation is too long for its slot, reword it more compactly instead of
   shrinking the type.
4. **Verbatim.** Leave unchanged: statute numbers, acronyms (TANF, SSI, SDI,
   FICA, IRA), URLs, and the form number FL-150.

**Definition of done.** Both of these, not just the first:

- `SKILL_DIR/scripts/verify.py` exits 0 with every gate passing.
- You have rendered **every page** of your output at ~110 dpi alongside the
  corresponding original page and inspected them yourself. The gates check
  structure; they cannot see a label shrunk to 4pt, a leader running through a
  checkbox, a button caption double-drawn over your text, or a heading that
  lost its color. Fix what you find, rebuild, and re-render. Expect 2–3 rounds;
  the first build is never right.

**Deliverables** — save all four into your working directory:

- `FL-150_ja.pdf` — the translated form
- `translations.json` — your language and placement decisions
- `NOTES.md` — what you did, every judgment call, anything in the provided
  scripts you had to work around, and the **verbatim** final output of
  `verify.py`
- `comparison.html` — from `scripts/compare.py`

At the end, report: total wall-clock time, roughly how many tool calls you
made, and your honest assessment of where your output is weakest.

---

## After the run

Send back, per model:

- the four deliverables above
- the terminal transcript or log if your CLI saves one

These will be scored on the same rubric as the Claude configurations: field
parity (266), page geometry, Japanese coverage, English leakage, typed-Japanese
field round-trip, minimum type size, text/widget overlaps, and graphics-layer
integrity — all calibrated against a human-approved reference translation of
the same form.

## Note on fairness

The Claude results this will be compared against ran inside a mature agentic
harness with file, shell, and image-reading tools and long iterative loops.
For the comparison to say something about the *model* rather than the
*harness*, the Grok session needs the same abilities — in particular it must be
able to run shell commands, write files, and **view rendered PNG images**
(needed for the visual pass). If the Grok CLI cannot display images back to the
model, say so in NOTES.md: the visual-inspection step is where roughly half of
all defects are caught, and a run without it is not comparable.
