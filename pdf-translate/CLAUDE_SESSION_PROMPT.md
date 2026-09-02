# Claude session prompt (FL-150 EN→JA, updated skill)

Run **once per model** (Haiku, Sonnet, Opus high), each in its **own empty
directory**. The repo already contains a finished Grok run and a complete
`translations.json` — those are contamination. Do not point the model at them.

## What you do

1. Create an empty folder, e.g.
   `<REPO>/runs/haiku`
   (then `runs\sonnet`, `runs\opus-high`).
2. Open a **new** Claude session with this repo available.
3. Set cwd to that empty folder if you can; if not, the prompt tells it where
   to write.
4. Paste everything between the `---` lines as the first user message.
5. Do not also paste Grok NOTES, `work/translations.json`, scores, or
   `explainer.html`. The skill is the independent variable.

On this machine the interpreter is `py -3`, not `python3`.

---

You are doing a high-fidelity PDF translation task. Work autonomously to
completion — do not ask me questions, make reasonable judgment calls and record
them in NOTES.md.

This repo is already on disk. Use these paths exactly:

    SKILL_DIR = <REPO>/pdf-translate
    SOURCE_PDF = <REPO>/fl150_original.pdf
    OUT_DIR    = <REPO>/runs/<MODEL>

Replace `<MODEL>` with `haiku`, `sonnet`, or `opus-high` — the folder for
THIS session only. Create it if needed. Write every deliverable into OUT_DIR.
Do not write into `work\`, the repo root, or another model's folder.

**Do not use existing outputs as a translation.** The repo contains a prior
run (`work\FL-150_ja.pdf`, `work\translations.json`, `work\NOTES.md`,
`translations.json` at the repo root, `explainer.html`). Those are someone
else's mapping and notes. Do not copy, diff against, or paraphrase them.
Author `translations.json` yourself from `to_translate.json` after you run
the extractor on SOURCE_PDF.

**Do not modify files under SKILL_DIR** (scripts, SKILL.md, references,
tests) unless a script is actually broken on this machine. If you patch
anything, quote the change in NOTES.md. Prefer using the scripts as-is.

Read these three things before you touch the PDF, in this order:

1. `SKILL_DIR\SKILL.md` — the workflow. Follow it.
2. `SKILL_DIR\references\failure-modes.md` — eight silent failure modes.
   Every one is a real defect that produces no error message. Treat them as
   constraints, not trivia.
3. `SKILL_DIR\references\translations-format.md` — the format of the
   `translations.json` file you will author.

Read `SKILL_DIR\references\fonts.md` when you reach the font stage.

The pipeline is seven Python scripts in `SKILL_DIR\scripts\`. They are
tested — use them rather than reimplementing. On this Windows machine the
interpreter is `py -3` (not `python3`). Dependencies should already be
installed (`pymupdf`, `pikepdf`, `fonttools`). If `pyftsubset` is missing
from PATH, the prepare-font script will look next to the interpreter or use
`py -3 -m fontTools.subset`. A glyf Noto Sans JP TTF may already exist at
`<REPO>/work/NotoSansJP-wght.ttf` and
`NotoSansJP-Regular-full.ttf` — you may reuse those **font files only**,
not the translations sitting beside them.

**The task.** Translate the official California Judicial Council form FL-150
("Income and Expense Declaration") from English into natural-sounding Japanese.

Use SOURCE_PDF exactly. Do not re-download it. Confirm SHA-256 is:

    46CA00246AE0F26AD893CE3DED2BD502FD6DF299258B02070395CC597A3F68B4

Requirements, in priority order — when they conflict, the higher one wins:

1. **Structure.** All 266 fillable form fields must carry over with identical
   names, types, and positions, and must still accept input — including
   Japanese text typed into them by a user. Adding widgets is a miss unless
   the skill leaves you no other way; prefer in-place caption rewrite over
   hide-and-draw-a-replacement.
2. **Layout.** Visually indistinguishable from the original: same tables,
   rules, columns, checkboxes, dot leaders, page count and page sizes. Only
   the text changes. If retypeset warns that type scaled below ~0.7x, reword
   the translation more compactly rather than shipping tiny type.
3. **Translation.** Natural Japanese in California family-law register, using
   established Japanese legal terminology rather than literal renderings.
4. **Verbatim.** Apply the write/find/say test in the skill. Leave unchanged:
   statute numbers, acronyms (TANF, SSI, SDI, FICA, IRA), URLs, the form
   number FL-150, official document names the reader must locate (e.g.
   Schedule C), and quoted labels the form tells the filer to write on an
   attachment.

**Definition of done.** Both of these, not just the first:

- `SKILL_DIR\scripts\verify.py` exits 0 with every gate passing. For this
  EN→JA pair use the default source-script leak regex (do **not** pass
  `--source-words-from`; that flag is for same-script pairs). Fill with a
  Japanese name, e.g. `--fill-text "山田太郎テスト"`.
- You have rendered **every page** of your output at ~110 dpi alongside the
  corresponding original page and **looked at the PNGs yourself** (read the
  image files back). The gates check structure; they cannot see a label
  shrunk to 4pt, a leader running through a checkbox, a button caption
  double-drawn over your text, or a heading that lost its color. Fix what
  you find, rebuild, and re-render. Expect 2–3 rounds; the first build is
  never right. A run that never inspects page images is not done.

**Deliverables** — save all of these into OUT_DIR only:

- `FL-150_ja.pdf` — the translated form
- `translations.json` — your language and placement decisions
- `NOTES.md` — what you did, every judgment call, anything in the provided
  scripts you had to work around, whether you used `--captions` or hid
  buttons, the **verbatim** final output of `verify.py`, wall-clock, rough
  tool-call count, and where the output is weakest
- `comparison.html` — from `scripts/compare.py`
- `renders\` — original and translated page PNGs at ~110 dpi

At the end, report: total wall-clock time, roughly how many tool calls you
made, field count (original vs translated), verify exit code, and your
honest assessment of the weakest page or decision.

---

## After each model finishes

Collect from that model's OUT_DIR: the four deliverables, `renders\`, and
NOTES.md. Do not start the next model in the same conversation as the
previous one if it can still see the previous `translations.json`.
