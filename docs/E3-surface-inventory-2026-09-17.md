# E3 surface inventory — pdf_translate, main @ v54 (2026-09-17)

Package root: `C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\`
Read-only research; nothing edited. Line numbers are as of this checkout
(`git log -1` = `9675c61`, branch `main`).

Consumer contract reference: `C:\Dev\pdf-translate-skill\docs\REQUESTS-from-product.md`
rows C1–C10 (read in full). Where a finding below confirms or contradicts a
C-row's own "today" note, that is called out explicitly.

---

## 1–2. Per-module table

Columns: function \| signature \| returns \| reads beyond args \| writes \|
prints \| exits \| module state.

### strip_text.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `strip_text` (541) | `strip_text(src, dst, hide_buttons=None, captions=None, widget_text=None, keep_encryption=False)` | `report` dict (658) | none beyond `src`/`dst` (re-opens `dst` at 642 only to read back applied encryption bits) | `dst`; deletes `dst` (`os.remove`, 654) if leftover text survives strip | **0** inside the function | none | none (raises `WidgetTextError`, class at 331, on an unauthored/broken widget-text mapping) |
| `main` (667) | `main(argv=None)` | int (0 / 1 / 2) | `--captions`/`--widget-text` JSON named by argv | — | 2 (both via `_say` at 660, which itself wraps `print`); one FAIL line at 705 prints leftover **document text** (`item['text']`) | none directly; `if __name__=='__main__': raise SystemExit(main())` at 711 | none |

`tempfile.TemporaryDirectory()` at 294 (inside `invisible_text_pages`) — random name, not fixed. Module constants (256–258, 393) are frozen, never mutated.

### extract_segments.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `extract_segments` (520) | `extract_segments(src, outdir='.', gap=12.0, pages=None)` | dict: `segments, warnings, cores, document, pages, unextractable_pages, invisible_text_pages, segments_path, to_translate_path, widget_text, widget_text_path` (708–720) | only `src` (opened 3×: main pass, `doc_for_images`, and via `invisible_text_pages(src)`/`document_strings(src)` in `strip_text`) | creates `outdir` (522); writes fixed names `segments.json`, `to_translate.json`, `widget_text.json` into it (694–707) | **0** inside the function | none | none — scan/invisible-text refusal is *returned as data* (`unextractable_pages`, `invisible_text_pages`), not raised |
| `print_warning_digest` (742) | `(warnings, max_per_kind=10)` | None | — | — | 5 | — | — |
| `main` (768) | `main(argv=None)` | int | `--outdir`/`--gap`/`--pages`/`--max-per-kind` from argv | — | 6 | none | — |

Default `outdir='.'` makes the *default* call cwd-dependent (caller can override, but the signature's own default is not). No `lru_cache`/global/tempfile in this module.

### prepare_font.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `prepare_font` (126) | `prepare_font(font_in, trf, font_out, instance=None, sample=None, allow_restricted=False, reference_fonts=None)` | **int** (0 / 1) — no dataclass, no exception | `trf` (named); when `reference_fonts is None` and the job is CJK, falls through `han_forms.reference_status`/`default_reference_dir()` (han_forms.py:109-112) to **`<package>/../tests/fonts/`**, a file the caller never named | `font_out`; fixed sidecars `font_out+'.chars.txt'` (200) and, if `instance`, `font_out+'.instanced.ttf'` (197) — plain writes, no temp+replace | **12, all inside `prepare_font()` itself** (135–268) | none | none |
| `main` (272) | `main(argv=None)` | int | — | — | **0** (main only forwards to `prepare_font`) | none | — |

Confirms the C1 row's own "today" note (prepare_font "10 print sites") almost exactly — measured count here is 12, all inside the function body, not gated behind a verbosity flag.

### retypeset.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `retypeset` (598) | `retypeset(stripped, segf, trf, out)` | **int** (0 / 1) — scale info only reaches disk, never the return value | font paths resolved relative to `trf`'s directory (documented); `pymupdf.Archive('.')` at **838** — an HTML archive rooted at **cwd**, passed as `archive=arch` into every `insert_htmlbox` call (1211, 1215, 1237, 1272) | `out` via single `doc.ez_save(out)` at **1363**; `scale_report.json` (fixed name, constant `SCALE_REPORT` at 90) beside `out`'s directory, via **plain `open(...,'w')`** at 1355–1361 — no temp file, no atomic replace, no stale-removal | **32, effectively all inside `retypeset()`** (main only parses argv) | none | none — every refusal path (`missing`, bad merge/box, overflow, glyph misses, rotated+shaped) is `print(...); return 1`, never an exception |
| `main` (1387) | `main(argv=None)` | int | — | — | 0 | — | — |

**Per-page loop:** `for pno, page in enumerate(doc):` **912–1217**; a second per-merge-job loop **1218–~1280**. No callback/generator parameter, no cancellation check anywhere in either loop — the whole multi-page placement is one uninterruptible synchronous pass. `doc.ez_save(out)` (1363) is the *only* save, strictly after both loops finish, so a `return 1` refusal never leaves a partial `out` file — but nothing today can observe progress or abort mid-run (C4: confirmed "nothing today").

**Determinism:** `apply_document_metadata` (354–413) sets `/Lang`, XMP `dc:language`, `/Title`, TOC titles, and clears an orphaned `/StructTreeRoot` — it never touches `/ModDate`, `/CreationDate`, `/Producer` or `/ID`, and `retypeset()` takes no timestamp argument; `doc.ez_save(out)` is called with no options. Confirms C7's "today" note exactly.

Module constants only (`SCALE_MIN`, `NOTICE_SIZE`, `SCALE_REPORT`, regex tables) — none mutated at runtime.

### verify.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `_execute_verify` (1476) | `(orig, trans, fill_text=…, allow=None, min_ink=0.4, source_regex=None, source_words_from=None, allow_extra_prefix=None, translations=None, segments=None, fail_on_review=False, reference_fonts=None)` | `(rc, gates)` | `translations`/`segments`/`source_words_from`/`reference_fonts` — all caller-named | `tempfile.mkstemp(suffix='.pdf')` at **1580** (fill-roundtrip probe copy — random name) | bulk of the module's **67** print( sites (gate PASS/FAIL/REVIEW/SKIP lines) | none | — |
| `run_verify` (1955) | same args | `VerifyVerdict` (dataclass, 298) | — | — | **0 observable** — wraps the call in `with redirect_stdout(io.StringIO()):` (1960) | none | — |
| `verify` (1979) | same args | int | — | — | **not suppressed** — calls `_execute_verify` directly, so it still prints every gate line | none | — |
| `write_report` (2017) | `(verdict, path)` | None | — | `tempfile.mkstemp(prefix='.verify_report-', suffix='.tmp', dir=…)` (2025) + `os.replace` — atomic, whole-or-nothing | 1 (only on `OSError`) | none | — |
| `_remove_stale_report` (1993) | `(path)` | bool | — | removes any existing file at `path` (chmod read-write first, 2005) | 1 (only on failure) | none | — |
| `main` (2040) | `main(argv=None)` | int | `--translations`/`--segments`/`--reference-fonts` from argv | writes `--report PATH` via `write_report` | 1 (`elapsed …s`) | none | — |

`GATE_NAMES` (286) is a frozen tuple — the closed, ordered gate list; not mutated. `run_verify`'s silence is achieved by **swapping process-global `sys.stdout`** for the duration of the call (contextlib `redirect_stdout`) — see §3/C5 note below.

### qa_check.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `qa_check` (295) | `(translations_path, segments_path=None, glossary_path=None)` | `list[dict]` findings | `segments_path`/`glossary_path` — both caller-named, both optional | none | **0** | none | — |
| `run_qa` (348) | same args | `QAVerdict` (dataclass, 327) | — | — | **0** | none | — |
| `main` (365) | `main(argv=None)` | int | — | — | 3 total in module, all via `_say`/`main` | none | — |

Already fully compliant with C1/C10 among the stage modules — the only one with zero prints in *both* the plain and the "run_" entry point, and no stdout-redirect hack needed.

### field_fonts.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `field_fonts` (35) | `(inp, font, out, name='TransFF')` | int (**always 0**) — can re-raise a non-Windows-lock `OSError` from temp cleanup (113–116) | none | fixed-name temp `out + '.tmp_withfont.pdf'` (37) beside `out` — **not** `tempfile` module, **not** randomized; then `out` itself | **4, all inside the function** (50, 114, 117, 120) | none | — |
| `main` (125) | `main(argv=None)` | int | — | — | 0 | — | — |

Two concurrent jobs targeting the same `out` collide on the fixed temp path.

### render_pages.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `render_pages` (18) | `(orig, trans, outdir, dpi=110)` | `list[str]` of written PNG paths (31) — already returns data | none | creates `outdir`; fixed names `{orig,out}_p{n}.png` per page | **1, inside the function** (30) | none | — |
| `main` (34) | `main(argv=None)` | int | — | — | 1 | — | — |

### compare.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `compare` (19) | `(orig, trans, html_path, labels=None, lang='en')` | int (**always 0**) | none | `html_path` only | **1, inside the function** (63) | none | — |
| `main` (67) | `main(argv=None)` | int | — | — | 0 | — | — |

### bilingual.py

| function | signature | returns | reads beyond args | writes | prints | exits | module state |
|---|---|---|---|---|---|---|---|
| `has_fields` (27) | `(path)` | bool | none | none | 0 | none | — |
| `interleave` (35) | `(original, translated, out, target_first=False)` | int — page count of the written doc | none | `out` (`dst.save(out, garbage=3, deflate=True)`, 52) | **0** | none | — |
| `main` (60) | `main(argv=None)` | int | — | — | 4 | none | — |

The "two widgets, same field name" refusal (66–74) lives **only in `main()`** — `interleave()` itself performs no such check, so a library caller must call `has_fields()` twice and decide, exactly as the CLI does.

### pipeline.py (orchestrator, not a stage)

| function | calls | fixed paths it uses |
|---|---|---|
| `cmd_init` (72) | `strip_text()` (library) **then** `extract_main()` (CLI `main`, imported as `extract_main` at 61) | `<work>/stripped.pdf` |
| `cmd_from_cores`/`scaffold_from_cores` (120,160) | file I/O only | `<work>/translations.json` |
| `cmd_propose_merges`/`propose_merges` (168,245) | file I/O only | `<work>/merges_proposed.json` |
| `cmd_qa` (305) | `qa_main()` (CLI `main`, imported at 68) | `<work>/translations.json`, `<work>/segments.json` |
| `cmd_rebuild` (319) | `retypeset()` (library, 337) **then** `verify_main()` (CLI `main`, imported at 69) | `<work>/stripped.pdf`, `<work>/segments.json`, `<work>/translations.json`; appends **fixed** `--report <work>/verify_report.json` when the caller didn't pass `--report` (343–344) |
| `cmd_render` (350) | `render_pages()` (library) | — |
| `cmd_finish` (359) | `field_fonts()` then `compare()` (both library) | — |
| `main` (370) | dispatches to the above, plus `bilingual_main()` (CLI `main`, imported at 67) for the `bilingual` subcommand | — |

31 prints, all in `cmd_*`/`main`. No module-level mutable state, no `os.chdir` anywhere in the file. `pipeline.py` mixes calling true library functions (`strip_text`, `retypeset`, `field_fonts`, `compare`, `render_pages`) with calling other stages' **CLI `main()`s** (`extract_segments.main`, `qa_check.main`, `verify.main`, `bilingual.main`) — the latter parse a constructed `argv` list and print to real stdout; there is no path through `pipeline.py` that reaches `extract_segments()`, `qa_check()`/`run_qa()`, `verify()`/`run_verify()`, or `interleave()` directly.

### shaping_probe.py / han_forms.py (pure libraries, no CLI)

Both: no `main()`, no `if __name__`, **0** `print(`, **0** `sys.exit`, **0** `os.chdir` (confirmed by grep). `han_forms.reference_face()` (128–164) is the one shared-cache surface: it writes an instanced reference font to `<src.parent>/<stem>-wght<weight>.ttf` or, if that directory isn't writable, to `Path(tempfile.gettempdir())/'pdf-translate-han-forms'/...` — via `tempfile.mkstemp` + `os.replace` (atomic, safe under races) but with **no lock** and a location the caller doesn't choose when the first directory fails. `shaping_probe.probe_font_bytes` (317–320) uses `tempfile.mkstemp(prefix='probe-')` — random name, fine.

---

## 3. How refusal is signalled today

- **Typed exception:** only one exists in the whole package — `strip_text.WidgetTextError` (strip_text.py:331), raised by `strip_text()` itself and by `apply_widget_text`/the unauthored-widget-text check (617–622). Every CLI that can hit it (`strip_text.main`, `pipeline.cmd_init`) catches it and converts to `print('FAIL widget text: …'); return 2`.
- **Everything else** — `extract_segments`, `prepare_font`, `retypeset`, `field_fonts`, `compare`, `bilingual.interleave` — signals refusal by **return code alone** (0 pass / 1 or 2 fail) plus, in the corresponding `main()`, a printed `FAIL:`/`!!`/`NOTE:` line. `extract_segments()` goes one step further and returns the refusal *reasons as data* (`unextractable_pages`, `invisible_text_pages`) without raising or printing — only `main()` turns that into a FAIL print + rc.
- `verify`/`run_verify`/`qa_check`/`run_qa` never raise for a normal FAIL/REVIEW outcome — that's expressed in `VerifyVerdict.exit_code`/`.ok` and `QAVerdict.exit_code`/`.ok`. No custom exception classes exist for verify/QA outcomes (confirmed by grep — the only `class …Error` / `raise` of a custom type anywhere under `pdf_translate/` is `WidgetTextError`).
- No module anywhere calls `sys.exit` directly; every CLI's `if __name__ == '__main__': raise SystemExit(main())` is the sole exit point, and it only runs under the script guard, never on import or on a library call.

## 4. retypeset — loop, save, metadata, cancellation

- Per-page placement loop: **retypeset.py:912–1217** (`for pno, page in enumerate(doc):`).
- Per-merge-job loop: **retypeset.py:1218–~1280** (separate pass, after the per-page loop, using the same `doc`).
- Save: **one** call, `doc.ez_save(out)` at **retypeset.py:1363**, after both loops and after `apply_document_metadata` (1324) and the `scale_report.json` write (1355–1361).
- Metadata/determinism: `apply_document_metadata` (354–413) touches `/Lang`, XMP `dc:language`, `/Title`, TOC, `/StructTreeRoot`/`MarkInfo` — never `/ModDate`, `/CreationDate`, `/Producer`, or `/ID`; no timestamp parameter exists on `retypeset()`; `ez_save` is called with no arguments.
- Callback/abort: **none**. No parameter accepts a progress callback or generator; no cooperative-cancellation check inside either loop. A refusal (`return 1`) always happens before `ez_save`, so refusal paths never leave a partial `out` — but there is no supported way to stop a long run early, and no per-page signal a caller could observe even to show a progress bar.
- `pymupdf.Archive('.')` at **retypeset.py:838** is a live cwd dependency: it is the archive object passed to every `insert_htmlbox` call in both loops (1211, 1215, 1237, 1272), so any relative resource reference inside authored HTML would resolve against the *process's* cwd, not against `trf`'s directory or any caller-supplied root.

## 5. verify — run_verify / verify / main / report writer

Confirmed already library-shaped, with one asymmetry:
- `run_verify` (verify.py:1955) returns a `VerifyVerdict` and is silent **by construction** — it wraps `_execute_verify` in `with redirect_stdout(io.StringIO()):` (1960), i.e. it suppresses prints by swapping `sys.stdout` process-wide for the call's duration, not by the underlying gates being print-free.
- `verify` (verify.py:1979) calls `_execute_verify` **without** that wrapper, so it still prints every gate line — `run_verify` and `verify` are not just "silent vs. CLI wrapper", they differ from each other at the library level too.
- `write_report` (2017) is whole-or-nothing: `tempfile.mkstemp` beside the target + `os.replace`; on any `OSError` it prints and falls back to `_remove_stale_report`. `main()` (2040) calls `_remove_stale_report(report)` *before* running when `--report` is given, "the only report that can exist is this run's" (2047 comment) — this is E1's fix (v53), confirmed still in place.
- `pipeline.py rebuild` (`cmd_rebuild`, pipeline.py:319–347) writes to the **fixed path** `<work>/verify_report.json` (343–344) whenever the caller didn't already pass `--report`, calling `verify.main` (the CLI entry, not `verify()`/`run_verify()`) with that flag appended.
- **`scale_report.json` (retypeset.py) has none of `write_report`'s protections** — no temp file, no atomic replace, no stale-removal, no schema field — it's a plain `open(path,'w')` write beside `out`. This is the one place E1's "written whole or not at all" invariant was applied to verify's report but not carried over to retypeset's.

## 6. pipeline.py — orchestration and work-dir conventions

See the table in §1–2 above. Summary: `pipeline.py` calls the true library functions for `strip_text`/`retypeset`/`field_fonts`/`compare`/`render_pages`, but reaches `extract_segments`, `qa_check`, `verify`, and `bilingual.interleave` **only through their CLI `main()`s** (built argv lists, real prints, real return-code semantics) — never through `extract_segments()`, `qa_check()`/`run_qa()`, `verify()`/`run_verify()`, or `interleave()` directly. Work-dir convention: a single `--work DIR` holds fixed-name files that later subcommands assume are already there — `stripped.pdf`, `segments.json`, `to_translate.json`, `translations.json`, `widget_text.json`, `merges_proposed.json`, and (only for `rebuild`) `verify_report.json`. `retypeset`'s `scale_report.json`, by contrast, lands beside the **output** file (`os.path.dirname(os.path.abspath(out))`), not inside `--work` — so it is *not* one of the work-dir's fixed names, and two jobs whose `out` files share a directory will race on it.

## 7. Tests that pin the library surface

- **`tests/test_import_surface.py`** — `PackageImportTests.test_import_has_no_cli_side_effects` (58–75) asserts `import pdf_translate` prints nothing and exposes `strip_text, extract_segments, retypeset, prepare_font, field_fonts, render_pages, compare, interleave, verify, qa_check, run_verify, run_qa` as callables; `test_submodules_are_importable_without_scripts_on_path` (77–90) asserts the package doesn't need the historical `scripts/` sys.path hack. `VerifyVerdictTests` (93–143) asserts `run_verify` prints nothing (`buf.getvalue() == ''`) while `verify` still prints `'PASS field parity'`, and that a FAIL is `exit_code == 1`, never a `SystemExit`. `CliPathTests` (418–487) pins that all **11** `CLI_SCRIPTS` (`bilingual, compare, extract_segments, field_fonts, pipeline, prepare_font, qa_check, render_pages, retypeset, strip_text, verify` — 27–39) still exist under `scripts/`, that `pipeline.py`/`qa_check.py` print usage and exit 2 on no args, that help text survives a legacy cp1252 console, and — importantly — that the CLIs *not* in `USAGE_CLIS` (i.e. 8 of the 11) exit 1 with a raw `Traceback` on missing args (453–461), not a clean usage message. **No byte-identical CLI-vs-wrapper parity runner exists yet** — the "eleven CLIs byte-identical" acceptance criterion in E3 is still open; this file only pins existence/behavior, not byte equality against `pdf_translate.<module>.main()`.
- **`tests/test_verify_report.py`** — `ReportAndPolicyTests` (516–632) pins: `--report` output equals `run_verify(...).to_dict()`; an unwritable report path keeps `rc` unchanged and prints `could not write`; a stale report at a since-made-read-only path is either removed or overwritten to describe the new run, never left describing the old one (556–586, the literal E1 regression test); `--fail-on-review` flips REVIEW-only runs to exit 1 in both the CLI and `run_verify(..., fail_on_review=True)`; `pipeline.py rebuild` writes `schema:1` into `<work>/verify_report.json`. `VersionLockstepTests.test_four_version_sources_agree` (635–649) is the "four-way lockstep": `SKILL.md`'s `version:`, `.claude-plugin/plugin.json`'s `version`, `pyproject.toml`'s `version`, and `pdf_translate.__version__` must all agree (currently `"54"`/`"54.0.0"`) — a version string check, not a console-parity check.
- **`tests/test_pipeline.py`** (315 KB, the largest test file) — grepped for stdout-capture idioms: **351** occurrences of `redirect_stdout`/`StringIO` and **282** `assertIn(` calls. This file's dominant pattern is capturing a stage's `main()` console output and asserting on literal printed strings (e.g. `'PASS field parity'` recurs at lines 1242, 3438, 3493, 3926, 4281, 4348, 4416, 4546). **This is the test suite most constrained by a "silent by default" change** — any move to make `retypeset`/`prepare_font`/`field_fonts`/`extract_segments`/`compare` quiet by default (per C1/C10) either needs a verbosity switch these ~350 call sites can opt into, or a large-scale rewrite of this file to assert on returned data instead of console text.

## 8. references/ docs and README

- **`references/gates.md` §"As a library" (142–182)** — already accurately describes `run_verify`: same args as the CLI, prints nothing, returns `VerifyVerdict` with `exit_code`/`gates`, one `GateResult` per `GATE_NAMES` entry, findings as `Finding(page, where, text)` tuples; documents the `--report`/`pipeline.py rebuild` fixed-path behavior, the temp-file-then-move write, and the stale-report removal — all confirmed against the code in §5 above. A `gate → where/text` reference table follows (184–203).
- **`references/translations-format.md`** (1–30 read) — already states the BCP-47 requirement for `"lang"` near the top (line 16) **with the explicit "not a display name" example** product's PR review asked for: `// A tag, not a display name: "ja", never "Japanese" or "日本語". ISO 639-2 ("jpn") is accepted.` (line 21) — this specific E3 acceptance item is already satisfied, just not yet inside a dedicated consumer guide.
- **`references/fonts.md`** (32–42 read) — already names the two Han-forms reference files by their exact required names, `NotoSansJP-VF.ttf` and `NotoSansSC-VF.ttf` (line 38), and documents `--reference-fonts DIR`/`reference_fonts=` and the `reference faces not found` message when absent — also already satisfies that specific E3 acceptance item.
- **No consumer guide exists yet.** `references/` today holds `compliance.md, failure-modes.md, fonts.md, gates.md, retypeset.md, review.md, translations-format.md, widget-text.md` — none is the "engineer with zero context runs one document end to end from Python and reads every output file" document E3 calls for; the BCP-47 and reference-font-name content it must fold in already lives in `translations-format.md`/`fonts.md` and can be pointed to rather than re-derived.
- **README.md** documents the CLI paths as `python3 $SK/scripts/<name>.py …` (lines 48–65) for all stage scripts plus `pipeline.py rebuild`/`render`. `scripts/*.py` (checked `scripts/strip_text.py`) are thin wrappers: they insert the repo root onto `sys.path`, reconfigure stdout/stderr to UTF-8 only under `if __name__=='__main__'`, and `raise SystemExit(pdf_translate.<module>.main())` — confirming `pdf_translate/__init__.py`'s docstring claim that "the skill's documented CLI paths remain `scripts/*.py`; those are thin wrappers" is accurate.

---

## Supporting facts (C8/C9 cross-checks)

- `pyproject.toml`: `requires-python = ">=3.10"`, `pymupdf>=1.24,<1.30`, `version = "54.0.0"` — matches C8's "today" note exactly.
- `corpus/verdicts.json`: confirmed a flat `{filename: verdict-string}` map with **no version/schema field** — matches C8/E11's "today" note exactly.
- No network-capable import (`requests`, `urllib.request`, `socket`, `httpx`) anywhere under `pdf_translate/*.py` — confirms C9 "holds today".
- No `os.chdir` anywhere under `pdf_translate/*.py` (grep, whole package) — confirms C5's "today" note.
