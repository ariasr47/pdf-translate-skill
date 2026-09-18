# E3 design canvas — the consumer surface

The design pass that goes before the build, per "design before build": E3
turns the eleven stages into a library a service calls, which is a new
user-facing surface, so it was drawn before any code was planned.

Contract: `docs/REQUESTS-from-product.md` rows C1–C10 and the E3 epic row
Inventory it builds on: `docs/E3-surface-inventory-2026-09-17.md` (read-only, against `main` @ v54)

## What is here

Nine source files. Every `*.dc.html` is one artboard; `canvas.json` places
them and picks the opening view.

| File | Artboard |
| --- | --- |
| `Main.dc.html` | what a consumer writes, and C1–C10 measured at v56 |
| `DecideFirst.dc.html` | the three questions measurement cannot settle |
| `Logging.dc.html` | stages log, the CLI prints — C1 + C10 + parity in one move |
| `Results.dc.html` | the result family, and the `scale_report.json` problem |
| `ProgressCancel.dc.html` | C4, and why it is nearly free |
| `Hazards.dc.html` | four concurrency and determinism hazards, in severity order |
| `Exceptions.dc.html` | what raises and what is returned, per ruling R5 |
| `ConsumerGuide.dc.html` | the shape of `references/consumer-guide.md` |

The seeded output (`consumer-surface.html`, ~2.5 MB) is **gitignored** — a
build artifact that re-seeds from these nine files in one command.

## Rebuild it

Needs `node` (nvm-windows: prepend `C:\nvm4w\nodejs` to PATH if a tool shell
cannot find it) and the bundled `design` skill's base directory, which
`/design` re-extracts on invocation.

```bash
node "<design skill base>/seed-canvas.mjs" \
  --template "<design skill base>/payload.template.html" \
  --out consumer-surface.html --title "Consumer Surface" \
  --artboard Main.dc.html --artboard DecideFirst.dc.html \
  --artboard Logging.dc.html --artboard Results.dc.html \
  --artboard ProgressCancel.dc.html --artboard Hazards.dc.html \
  --artboard Exceptions.dc.html --artboard ConsumerGuide.dc.html \
  --canvas canvas.json
```

Then `--check consumer-surface.html` must print `ok:` with all nine files.

## Measurements these artboards assert, and where they came from

Taken at **v56** (`fix/cjk-job-gates`), not from the v54 inventory — v55 and
v56 touched `verify.py` and `retypeset.py`. If you edit an artboard, keep
these true or re-measure:

- **172 `print(` sites** in `pdf_translate/*.py`; **141** of them in the ten
  stage modules, the other 31 in `pipeline.py`, which is the orchestrator and
  not a stage. Per module: verify 70, retypeset 32, pipeline 31,
  prepare_font 12, extract_segments 11, field_fonts 4, bilingual 4,
  qa_check 3, strip_text 2, render_pages 2, compare 1.
- **`verify.py:2124`** — `run_verify` is silent via `with
  redirect_stdout(io.StringIO()):`, a process-wide `sys.stdout` swap.
- **`retypeset.py:622`** — `def retypeset(stripped, segf, trf, out):`, four
  positional parameters, no progress, no cancel, no timestamp.
- **`retypeset.py:862`** — `arch = pymupdf.Archive('.')`, a live cwd
  dependency handed to every `insert_htmlbox` call.
- **`retypeset.py:1379`** — `scale_report.json` written to
  `dirname(abspath(out))` under a fixed name, non-atomically, as a bare JSON
  list with no envelope.
- **`retypeset.py:1387`** — `doc.ez_save(out)`, the single save, after both
  loops. This is why a cancel between pages cannot leave a partial file.
- **`tests/test_pipeline.py`** — 351 `redirect_stdout`/`StringIO` idioms and
  282 `assertIn(` calls; the suite is 9,896 lines.
- `strip_text()` and `extract_segments()` **already return** rich dicts. C3's
  status note says they are "printed, not returned"; measured, they are both.
  Correct the note when E3 lands rather than repeating it.
- Determinism is **unmeasured**, not known-broken. No probe has run. The
  Hazards artboard says so and says not to write C7's code from it.
