# BRIEF — core-library step 1: make the scripts importable, change no behaviour

**For:** the agent doing this work in `C:\Dev\pdf-translate-skill`.
**Written:** 2026-09-15, from the product repo (`pdf-translator`), which will consume the result.
**Self-contained:** you do not need to read the product repo. Everything you need is below.

---

## 1. What you are doing, and why

This repo (`pdf-translate`, MIT, a Claude skill at version 48) translates PDFs while keeping layout
pixel-faithful and form fields working. A separate product repo (`pdf-translator`) independently
implements the same territory — roughly 6,845 lines of engine against this repo's 5,608 lines of
scripts. Two implementations of one problem, drifting apart weekly.

On 2026-09-14 the owner ruled that **this repo is the upstream**: it publishes a shared Python library,
and the product *imports* it instead of hand-porting it. The hand-port approach was formally retired.

There is also a hard structural reason the direction cannot flip: this repo is **MIT**, the product is
heading to **AGPL-3.0**. MIT code imports into AGPL freely; AGPL code cannot be absorbed back into MIT
without relicensing. So this repo stays upstream permanently.

**Step 1 is packaging only.** Product adoption is a later step in the other repo. Do not design for it.

## 2. The goal, precisely

Make the eleven scripts in `pdf-translate/scripts/` **importable as a library**, with **no behaviour
change**. Today they are CLI entry points with no package marker anywhere — no `pyproject.toml`, no
`setup.py`, no `scripts/__init__.py`.

Verified inventory, 2026-09-15:

| script | lines | territory |
|---|---|---|
| `retypeset.py` | 1397 | typesetting translated text back into the layout |
| `verify.py` | 1334 | verification gates |
| `extract_segments.py` | 811 | segment extraction |
| `strip_text.py` | 711 | selective text strip |
| `pipeline.py` | 399 | orchestration |
| `qa_check.py` | 373 | QA gates |
| `prepare_font.py` | 239 | font preparation |
| `field_fonts.py` | 134 | per-field font selection |
| `bilingual.py` | 85 | bilingual output |
| `compare.py` | 80 | comparison |
| `render_pages.py` | 45 | page rasterisation |

## 3. Acceptance — all three, or step 1 is not done

1. **Importable.** A consumer can import the strip / extract / retypeset / font / gate entry points and
   call them as functions, without CLI behaviour running as an import side effect.
2. **Every CLI behaves identically.** Same command names, flags, stdout/stderr contract and exit codes.
   `pdf-translate/SKILL.md` documents these invocations and real users run them. This is the bar that
   matters most.
3. **Every test green, before and after.** Capture the baseline BEFORE you touch anything.

## 4. The commands (verified against `.github/workflows/tests.yml`)

Tests are **`unittest`, not pytest**, and they are invoked **by module path from inside
`pdf-translate/`**:

```
cd pdf-translate
python -m pip install -r requirements.txt
python -m unittest tests.test_pipeline tests.test_corpus_verdicts -v
python -m unittest discover -s ../dev/canary -p test_score.py -v
```

There is a virtualenv at `pdf-translate.venv\Scripts\python.exe` if you prefer it to a fresh install.

**This is the single biggest risk in the whole job.** `python -m unittest tests.test_pipeline` resolves
`tests` as a top-level package relative to the current directory. Packaging changes module resolution.
If your refactor requires that invocation to change, **CI breaks**, and CI is the only thing proving
"no behaviour change". Either keep the invocation working exactly as-is, or update
`.github/workflows/tests.yml` in the same commit and say so loudly in your report.

Note also that `dev/canary` sits OUTSIDE `pdf-translate/` and is reached by relative path — check it
still resolves after any layout change.

## 5. Constraints

- **No behaviour change.** If you find a bug, write it down and leave it. A behaviour change destroys
  the only evidence that the packaging was safe — the before/after test comparison.
- **MIT stays.** Do not copy or import anything from the product repo. That code is heading to AGPL and
  pulling it in would relicense this repo by accident. Packaging only; no new logic.
- Python 3.10+, `pymupdf`, `pikepdf`, `fonttools`. `requirements.txt` pins deliberate upper bounds —
  PyMuPDF moves surfaces between minor releases and this pipeline reads several directly; pikepdf 9 and
  10 differ in behaviour this code depends on and **both are supported and exercised**. Do not raise a
  bound.
- `SKILL.md` documents paths relative to its own directory and tells callers to set
  `SK=/path/to/pdf-translate`. If packaging moves any documented path, `SKILL.md` changes in the same
  commit. A skill whose documented invocation has drifted from its code is broken for its users.

## 6. Branch — start here, not on `main`

Verified 2026-09-15: local and `origin` are identical on every branch, working tree clean.

- `codex/explicit-canary-delivery` -> `26e1f25` (2026-09-05) — **the newest state; branch from this**
- `main` -> `b157172` (2026-09-04) — one commit behind, **not merged**

Branching from `main` would start the refactor on a stale trunk and create a second divergence.
Merging the canary branch into `main` is the owner's decision — do not do it as part of this work.

A worktree exists at `runs/public-release-implementation-2026-09-05/checkout` holding
`codex/public-release-hardening`, currently at the same commit. It carries no divergent work, but do
not assume it is idle.

## 7. Shape of the library

The consumer will take **document transformation** and keep its own service layer (jobs, websockets,
providers, quotas, estimates) and its own placement logic. So the useful surface is roughly:

- strip -> extract -> retypeset as stages, each callable independently
- font preparation and per-field font selection
- the verify / QA gates as functions returning structured verdicts, rather than printing and exiting

That last one is the only place where "importable" implies a real design choice: a gate that prints and
calls `sys.exit` cannot be used as a library. Return a verdict object; let the CLI wrapper print it and
choose the exit code. **Do not add consumer-specific hooks** — the consumer will adapt to whatever
shape is honest here.

## 8. Do not lose these

`pdf-translate/corpus/`, `pdf-translate/evals/` and `pdf-translate/tests/` are this repo's real
advantage: document-level verification on actual forms. `evals/permission-slip-japanese` matters
specifically — the product shipped Japanese support on 2026-09-14 without consulting it, and that gap
is the clearest evidence so far that the two codebases have drifted. Keep all of it working.

## 9. Hand back

Report, so the result can flow into the product's step 2:

- baseline test numbers and post-refactor test numbers
- the import surface you settled on, and why
- every CLI you verified, and how you verified it behaves identically
- whether `.github/workflows/tests.yml` had to change, and whether `SKILL.md` did
- anything that looked like a bug, which you deliberately did not fix