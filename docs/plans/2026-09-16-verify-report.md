# Per-document verify report — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** every outcome `verify` prints reaches a consumer as data — one `GateResult` per printed line, each carrying its `Finding`s (page, where, text) — written as JSON by `--report`, with `--fail-on-review` for unattended use; console output and exit codes unchanged.

**Architecture:** `pdf_translate/verify.py` already records one `GateResult(name, status, message)` per printed outcome (PR #4). This plan adds a frozen `Finding` dataclass, a `findings` tuple on `GateResult`, `to_dict()` on both result types, and passes the items each gate already prints (`for x in items[:N]: print('   …')`) into `record(...)`. The CLI gains `--report PATH` and `--fail-on-review`; `pipeline.py rebuild` writes the report into its work dir. Spec: `docs/BRIEF-unattended-delivery.md` §4 task A and B.

**Tech Stack:** Python 3.10+ (CI) / 3.14 (this machine), `unittest`, PyMuPDF 1.28, fontTools. No new dependencies.

## Global Constraints

- Work on branch `feat/verify-report`, created from `docs/brief-unattended-delivery` (which carries the brief and this plan on top of `main` at v50): `git checkout -b feat/verify-report docs/brief-unattended-delivery`. Never commit to `main`. Never push, merge or delete: the operator does those.
- Run every test from `C:\Dev\pdf-translate-skill\pdf-translate` with the repo venv and UTF-8: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest …`. Tests are `unittest`, invoked by module path, never pytest.
- TDD: write the test, run it, watch it fail for the expected reason, then write the minimal code. A test that passes on first run is wrong.
- **Console output and exit codes of every CLI must not change**, with exactly one exception (Task 4): `REVIEW isolated source-script tokens: none` becomes `PASS isolated source-script tokens: none`. `dev/probes/verdict_parity_runner.py` is the check.
- `Finding.page` is 1-based or `None`. `Finding.where` names the thing (field name, font PostScript name, script, `lang`, `U+00A0`, `0.85x`, `page`, `token`, `run`, `target`, `identifier`). `Finding.text` is the run, caption, token or detail, **untruncated** (the console keeps its `[:10]` / `[:20]` / `[:30]` limits; the report does not).
- Names in `verify.GATE_NAMES` do not change. `record(name, status, message='', findings=())` is the only way a gate lands in the verdict.
- Never copy code from `C:\Dev\pdf-translator` (AGPL-bound; this repo is MIT). Do not open it.
- Conventional commits with a scope (`feat(pdf-translate): …`, `test(pdf-translate): …`, `docs(pdf-translate): …`). **No AI attribution**: no `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" line.
- LF line endings. Use the Edit tool for edits; `git diff --check` must be clean before every commit.
- Windows: `py -3` is 3.14 with PyMuPDF 1.28.0; the venv above has 1.28.2. Use the venv. Bash heredocs over ~100 lines break: write big files with the Write tool.
- The fetched test faces live in `pdf-translate/tests/fonts/` (`python tools/fetch_test_fonts.py` fetches them; never commit them). Tests that need a face `raise unittest.SkipTest` when it is missing, exactly as `tests/test_shaping_probe.py` does.

---

## File structure

- `pdf-translate/pdf_translate/verify.py` — modify: `Finding`, `GateResult.findings`, `to_dict()`s, `VerifyVerdict.original/output`, `record(... findings)`, findings at every gate site, `conjunct_shaping_report` returns findings, `fail_on_review`, `main()` builds the verdict and writes `--report`.
- `pdf-translate/pdf_translate/__init__.py` — modify: `__version__`, export `Finding`.
- `pdf-translate/pdf_translate/pipeline.py` — modify: `cmd_rebuild` passes `--report <work>/verify_report.json`.
- `pdf-translate/tests/test_verify_report.py` — create: every test in this plan.
- `pdf-translate/tests/test_import_surface.py` — modify one assertion (Task 4).
- `dev/probes/verdict_parity_runner.py` — modify: print findings counts.
- `.github/workflows/tests.yml` — modify: suite line, 4-way version lockstep.
- `pdf-translate/SKILL.md`, `.claude-plugin/plugin.json`, `pdf-translate/pyproject.toml` — version 51.
- `pdf-translate/references/gates.md`, `docs/DECISIONS.md`, `docs/reviews/2026-09-16-verify-report.md` — docs.

Test file header, used by every task (create it in Task 1):

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every outcome verify prints reaches a consumer as data: GateResult.findings,
VerifyVerdict.to_dict(), --report and --fail-on-review. Spec:
docs/BRIEF-unattended-delivery.md, task A and B."""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf

from tests.test_import_surface import _gates, _job, _tiny_pdf

SKILL = Path(__file__).resolve().parents[1]
FONTS = SKILL / 'tests' / 'fonts'
CORPUS = SKILL / 'corpus'
RTL_FONT = FONTS / 'NotoNaskhArabic-Regular.ttf'
AR_PHRASE = 'السلام عليكم ورحمة الله'


def _gate(verdict, name):
    hits = [g for g in verdict.gates if g.name == name]
    assert len(hits) == 1, f'{name}: {[g.name for g in verdict.gates]}'
    return hits[0]


def _findings(verdict, name):
    return [(f.page, f.where, f.text) for f in _gate(verdict, name).findings]


def _arabic_glyph_by_glyph(path):
    """An output page whose Arabic was drawn by TextWriter: no shaping, no /ActualText.
    Raises SkipTest when the Naskh face is not fetched."""
    if not RTL_FONT.is_file():
        raise unittest.SkipTest(f'{RTL_FONT.name} not fetched (tools/fetch_test_fonts.py)')
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=612, height=792)
        tw = pymupdf.TextWriter(page.rect)
        tw.append((72, 80), AR_PHRASE, font=pymupdf.Font(fontfile=str(RTL_FONT)),
                  fontsize=12, right_to_left=True)
        tw.write_text(page)
        doc.save(path)
    finally:
        doc.close()
```

`_job(tmp, source=…, target=…, lang=…, declare=…, overrides=…, segments=…, scale_report=…)` builds `orig.pdf`, `out.pdf`, `translations.json` (and `segments.json` / `scale_report.json` beside them) and returns `(src, out, tr)`. `_gates(verdict)` returns `{name: status}` and asserts no name is recorded twice. Both live in `tests/test_import_surface.py`.

---

### Task 1: `Finding`, `findings`, `to_dict()`

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (the `GateResult` / `GATE_NAMES` / `VerifyVerdict` block near line 184, `record()` inside `_execute_verify`, `run_verify`)
- Modify: `pdf-translate/pdf_translate/__init__.py`
- Create: `pdf-translate/tests/test_verify_report.py`

**Interfaces:**
- Produces: `Finding(page: int | None, where: str, text: str)` frozen dataclass with `to_dict()`; `GateResult(name, status, message='', findings=())` with `to_dict()`; `VerifyVerdict(exit_code, gates, original='', output='')` with `to_dict()` → `{'schema': 1, 'version': pdf_translate.__version__, 'original', 'output', 'exit_code', 'gates': [...]}`; `record(name, status, message='', findings=())`; `pdf_translate.__version__ == '50'` (Task 7 bumps it).

- [ ] **Step 1: Write the failing tests** (create the file with the header above, then this class)

```python
class FindingShapeTests(unittest.TestCase):
    def test_finding_gate_result_and_verdict_serialise(self):
        import pdf_translate
        from pdf_translate.verify import Finding, GateResult, VerifyVerdict
        f = Finding(page=2, where='ApplicantName', text='missing')
        self.assertEqual(f.to_dict(), {'page': 2, 'where': 'ApplicantName', 'text': 'missing'})
        g = GateResult(name='field-parity', status='FAIL', message='1', findings=(f,))
        self.assertEqual(g.to_dict(), {
            'name': 'field-parity', 'status': 'FAIL', 'message': '1',
            'findings': [{'page': 2, 'where': 'ApplicantName', 'text': 'missing'}]})
        self.assertEqual(GateResult(name='x', status='PASS').findings, ())
        v = VerifyVerdict(exit_code=1, gates=(g,), original='a.pdf', output='b.pdf')
        d = v.to_dict()
        self.assertEqual(d['schema'], 1)
        self.assertEqual(d['version'], pdf_translate.__version__)
        self.assertEqual((d['original'], d['output'], d['exit_code']), ('a.pdf', 'b.pdf', 1))
        self.assertEqual(d['gates'], [g.to_dict()])
        json.dumps(d)   # must be JSON-serialisable as is

    def test_run_verify_fills_original_and_output(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual((v.original, v.output), (src, out))
            self.assertTrue(all(isinstance(g.findings, tuple) for g in v.gates))
            self.assertEqual(v.to_dict()['gates'][0]['name'], 'field-parity')
```

- [ ] **Step 2: Run, watch it fail**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_verify_report.FindingShapeTests -v`
Expected: `ImportError: cannot import name 'Finding'` (errors=2).

- [ ] **Step 3: Implement**

In `verify.py`, replace the `GateResult` class and `VerifyVerdict` class with:

```python
@dataclass(frozen=True)
class Finding:
    """Where a gate outcome points: a 1-based page or None, the thing it
    names (field, font, script, token, …) and the run or detail, untruncated."""
    page: object
    where: str
    text: str

    def to_dict(self):
        return {'page': self.page, 'where': self.where, 'text': self.text}


@dataclass(frozen=True)
class GateResult:
    """One named gate: status is PASS, FAIL, SKIP, or REVIEW."""
    name: str
    status: str
    message: str = ''
    findings: tuple = ()

    def to_dict(self):
        return {'name': self.name, 'status': self.status, 'message': self.message,
                'findings': [f.to_dict() for f in self.findings]}
```

(keep `GATE_NAMES` between them as it is) and

```python
@dataclass(frozen=True)
class VerifyVerdict:
    """Structured result of the structural gates. Does not print or exit."""
    exit_code: int
    gates: tuple
    original: str = ''
    output: str = ''

    @property
    def ok(self):
        return self.exit_code == 0

    def to_dict(self):
        from . import __version__
        return {'schema': 1, 'version': __version__,
                'original': self.original, 'output': self.output,
                'exit_code': self.exit_code,
                'gates': [g.to_dict() for g in self.gates]}
```

In `_execute_verify`, change `record`:

```python
    def record(name, status, message='', findings=()):
        gates.append(GateResult(name=name, status=status, message=message,
                                findings=tuple(findings)))
```

In `run_verify`, return `VerifyVerdict(exit_code=rc, gates=tuple(gates), original=orig, output=trans)`.

In `__init__.py`: add `__version__ = '50'` as the first statement after the docstring, change the verify import line to `from .verify import GATE_NAMES, Finding, GateResult, VerifyVerdict, run_verify, verify`, and add `'Finding',` to `__all__` (alphabetical, after `'GateResult'`).

- [ ] **Step 4: Run, watch it pass; run the two neighbours**

Run: `… -m unittest tests.test_verify_report.FindingShapeTests tests.test_import_surface -v`
Expected: all OK (the import-surface suite has 18 tests).

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/pdf_translate/__init__.py pdf-translate/tests/test_verify_report.py
git diff --cached --check
git commit -m "feat(pdf-translate): Finding, GateResult.findings and to_dict() on the verify verdict"
```

---

### Task 2: findings for the form and page gates

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (`_execute_verify`: the field-parity, /Opt, fill round-trip, extractable/ink, invisible-text and canonical-text blocks)
- Test: `pdf-translate/tests/test_verify_report.py`

**Interfaces:**
- Consumes: `record(name, status, message, findings)`, `Finding` from Task 1.
- Produces findings: `field-parity` → `Finding(None, label, name)` per bad field (`label` ∈ missing / type-mismatch / unexpected-extra); `opt-export-parity` → `Finding(None, field, f'{old} -> {new}')`; `fill-roundtrip` FAIL → `Finding(None, field, 'text value did not survive save and reopen')` and/or `Finding(None, field, 'checkbox did not survive save and reopen')`; `extractable-text` → `Finding(page, 'page', f'images={n}, ink={ink} px')`; `ink-ratio` → one finding per page: `Finding(page, 'page', f'ink ratio {ratio:.2f}')` or `Finding(page, 'page', f'negligible ink: {do} px')` for SKIP pages; `visible-text` → `Finding(page, 'page', f'stripping the text changes {fraction:.1%} of its span area')`; `canonical-text` → `Finding(None, f'U+{ord(ch):04X}', f'{unicodedata.name(ch, "?")} x{n}')` per drifted character, all of them.

- [ ] **Step 1: Write the failing tests**

```python
class FormAndPageGateFindingsTests(unittest.TestCase):
    def test_missing_field_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            doc = pymupdf.open()
            try:
                page = doc.new_page()
                page.insert_text((72, 72), 'Alpha source sentence here.')
                w = pymupdf.Widget()
                w.field_name = 'ApplicantName'
                w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
                w.rect = pymupdf.Rect(72, 100, 280, 118)
                page.add_widget(w)
                doc.save(src)
            finally:
                doc.close()
            _tiny_pdf(out, 'Alpha source sentence here.')
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'field-parity').status, 'FAIL')
            self.assertEqual(_findings(v, 'field-parity'), [(None, 'missing', 'ApplicantName')])

    def test_changed_opt_export_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            doc = pymupdf.open()
            try:
                page = doc.new_page()
                page.insert_text((72, 72), 'Choose one.')
                w = pymupdf.Widget()
                w.field_name = 'Choice'
                w.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
                w.rect = pymupdf.Rect(72, 100, 280, 118)
                w.choice_values = [['a', 'Apple'], ['b', 'Banana']]
                page.add_widget(w)
                doc.save(src)
            finally:
                doc.close()
            doc = pymupdf.open(src)
            try:
                for w in doc[0].widgets():
                    w.choice_values = [['x', 'Apple'], ['b', 'Banana']]
                    w.update()
                doc.save(out)
            finally:
                doc.close()
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'opt-export-parity').status, 'FAIL')
            (page, where, text), = _findings(v, 'opt-export-parity')
            self.assertEqual((page, where), (None, 'Choice'))
            self.assertIn('->', text)

    def test_ink_ratio_reports_every_page(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            (page, where, text), = _findings(v, 'ink-ratio')
            self.assertEqual((page, where), (1, 'page'))
            self.assertTrue(text.startswith('ink ratio '), text)

    def test_scan_page_is_named(self):
        from pdf_translate.verify import run_verify
        pdf = str(CORPUS / 'image_only.pdf')
        v = run_verify(pdf, pdf)
        self.assertEqual(_gate(v, 'extractable-text').status, 'FAIL')
        (page, where, text), = _findings(v, 'extractable-text')
        self.assertEqual((page, where), (1, 'page'))
        self.assertIn('images=', text)

    def test_ocr_layer_page_is_named(self):
        from pdf_translate.verify import run_verify
        pdf = str(CORPUS / 'ocr_layer.pdf')
        v = run_verify(pdf, pdf)
        self.assertEqual(_gate(v, 'visible-text').status, 'FAIL')
        page, where, text = _findings(v, 'visible-text')[0]
        self.assertEqual((page, where), (1, 'page'))
        self.assertIn('span area', text)

    def test_drifted_code_point_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            _tiny_pdf(out, 'Hola\u00a0mundo.')
            if '\u00a0' not in pymupdf.open(out)[0].get_text():
                raise unittest.SkipTest('the renderer folded NBSP; fixture cannot drift')
            Path(tr).write_text(json.dumps({'translations': {'Hello world.': 'Hola mundo.'}, 'skip': []}),
                                encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_gate(v, 'canonical-text').status, 'FAIL')
            self.assertEqual(_findings(v, 'canonical-text'), [(None, 'U+00A0', 'NO-BREAK SPACE x1')])
```

- [ ] **Step 2: Run, watch it fail**

Run: `… -m unittest tests.test_verify_report.FormAndPageGateFindingsTests -v`
Expected: every test fails on an empty findings list (`[] != [...]` or `ValueError: not enough values to unpack`). If `test_changed_opt_export_is_named` errors inside PyMuPDF on `choice_values`, set the pairs as `[('a', 'Apple'), ('b', 'Banana')]` tuples instead; if it still errors, the fixture is wrong, not the gate — ask before changing the assertion.

- [ ] **Step 3: Implement**, in `_execute_verify`, each block becoming:

```python
    parity = []
    for label, bad in [('missing', missing), ('type-mismatch', mismatch),
                       ('unexpected-extra', extra)]:
        if bad:
            print(f'FAIL field {label}:', sorted(bad)[:10])
            fail = 1
            parity.extend(Finding(None, label, name) for name in sorted(bad))
    if not (missing or mismatch or extra):
        print('PASS field parity')
        record('field-parity', 'PASS')
    else:
        record('field-parity', 'FAIL', findings=parity)
```

```python
        record('opt-export-parity', 'FAIL',
               f'{len(drifted)} choice field(s) changed',
               findings=[Finding(None, name, f'{oopt.get(name)} -> {jopt.get(name)}')
                         for name in drifted])
```

```python
            ok = got_t and got_cb
            print(('PASS' if ok else 'FAIL') + ' fill round-trip')
            fail |= (0 if ok else 1)
            broken = []
            if not got_t:
                broken.append(Finding(None, ttarget, 'text value did not survive save and reopen'))
            if not got_cb:
                broken.append(Finding(None, cbtarget, 'checkbox did not survive save and reopen'))
            record('fill-roundtrip', 'PASS' if ok else 'FAIL', findings=broken)
```

In the page loop, collect `scans = []` and `inks = []`:

```python
            scans.append(Finding(i + 1, 'page', f'images={nimg}, ink={ink(o[i])} px'))
```
after the extractable `print`, and
```python
            inks.append(Finding(i + 1, 'page', f'negligible ink: {do} px'))
```
after the SKIP print, and
```python
        inks.append(Finding(i + 1, 'page', f'ink ratio {ratio:.2f}'))
```
after the PASS/FAIL ratio print; then `record('extractable-text', 'FAIL', findings=scans)` and `record('ink-ratio', ink_status, findings=inks)`.

```python
    invisible = invisible_text_pages(orig)
    for pno, fraction in invisible:
        print(...)   # unchanged
        fail = 1
    if not invisible:
        print('PASS text layer is visible')
        record('visible-text', 'PASS')
    else:
        record('visible-text', 'FAIL', findings=[
            Finding(pno + 1, 'page', f'stripping the text changes {fraction:.1%} of its span area')
            for pno, fraction in invisible])
```

```python
        record('canonical-text', 'FAIL', f'{len(drift)} character(s)', findings=[
            Finding(None, f'U+{ord(ch):04X}', f'{unicodedata.name(ch, "?")} x{n}')
            for ch, n in drift])
```

- [ ] **Step 4: Run, watch it pass; then the parity check**

Run: `… -m unittest tests.test_verify_report -v` → OK.
Run the console parity check (from the repo root, `C:\Dev\pdf-translate-skill`):

```bash
git worktree add --detach /tmp/main-verify main
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_fixtures.py /tmp/f1fx
PYTHONUTF8=1 PYTHONPATH=/tmp/main-verify/pdf-translate C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_runner.py /tmp/f1fx > /tmp/main.txt 2>/dev/null
PYTHONUTF8=1 PYTHONPATH=pdf-translate C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_runner.py /tmp/f1fx > /tmp/branch.txt 2>/dev/null
diff /tmp/main.txt /tmp/branch.txt && echo IDENTICAL
git worktree remove /tmp/main-verify
```
Expected: `IDENTICAL`. (Use a path under your scratchpad instead of `/tmp` if `/tmp` is not writable.)

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_verify_report.py
git diff --cached --check
git commit -m "feat(pdf-translate): findings for the field, /Opt, fill, ink, text-layer and canonical gates"
```

---

### Task 3: findings for the script gates (Arabic letterforms, conjunct shaping)

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (`conjunct_shaping_report`, the Arabic block and the shaping block in `_execute_verify`)
- Test: `pdf-translate/tests/test_verify_report.py`

**Interfaces:**
- Produces: `conjunct_shaping_report(doc) -> (lines, status, findings)` (three values; update its only caller); `arabic-letterforms` FAIL → `Finding(page, 'page', f'{n} joining letters in isolated form, none connected')`; `conjunct-shaping` → one finding per page per judged (script, face): `Finding(page, result.expected_font or name, result.line())`; per unattested script: `Finding(page, script, f'cannot attest: no embedded face carries the probe "{probe.text}"')`; per review: `Finding(page, script, review_reason)`.

- [ ] **Step 1: Write the failing tests**

```python
class ScriptGateFindingsTests(unittest.TestCase):
    def test_unshaped_arabic_page_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            _tiny_pdf(src, 'Peace be upon you and mercy')
            _arabic_glyph_by_glyph(bad)
            v = run_verify(src, bad, min_ink=0.05)
            self.assertEqual(_gate(v, 'arabic-letterforms').status, 'FAIL')
            (page, where, text), = _findings(v, 'arabic-letterforms')
            self.assertEqual((page, where), (1, 'page'))
            self.assertIn('isolated form', text)

    def test_broken_conjunct_face_is_named(self):
        from pdf_translate.verify import run_verify
        from tests.test_shaping_probe import DV_TARGET, build_source_pdf, draw_story_output, noto, strip_gsub
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            build_source_pdf(src)
            no_gsub = strip_gsub(noto('Devanagari'), os.path.join(tmp, 'no-gsub.ttf'))
            draw_story_output(bad, DV_TARGET, no_gsub)
            v = run_verify(src, bad, min_ink=0.1)
            self.assertEqual(_gate(v, 'conjunct-shaping').status, 'FAIL')
            (page, where, text), = _findings(v, 'conjunct-shaping')
            self.assertEqual(page, 1)
            self.assertEqual(where, 'NotoSansDevanagari-Regular')
            self.assertIn('क्षत्रिय', text)
            self.assertIn('8 -> 8', text)
```

- [ ] **Step 2: Run, watch it fail**

Run: `… -m unittest tests.test_verify_report.ScriptGateFindingsTests -v`
Expected: both fail with `ValueError: not enough values to unpack (expected 1, got 0)`. (`noto()` raises SkipTest when the Devanagari face is missing; fetch the faces first.)

- [ ] **Step 3: Implement**

In `conjunct_shaping_report`, build `findings = []` alongside `lines` and return three values:

```python
    lines, statuses, findings = [], [], []
    for (script, xref), (result, pages) in sorted(judged.items()):
        if result is None or result.status == 'SKIP' or not pages:
            continue
        line = f'{result.line()} [{pages_of(pages)}]'
        if result.status == 'FAIL':
            line += ' — every conjunct drawn with this face is broken; do not ship'
        lines.append(line)
        statuses.append(result.status)
        face = result.expected_font or fonts[xref][0]
        findings.extend(Finding(p, face, result.line()) for p in sorted(set(pages)))
    for script, pages in sorted(unattested.items()):
        probe = shaping_probe.PROBE_FOR[script]
        lines.append(...)   # unchanged
        statuses.append('REVIEW')
        findings.extend(Finding(p, script, f'cannot attest: no embedded face carries the probe "{probe.text}"')
                        for p in sorted(set(pages)))
    for script, pages in sorted(reviews.items()):
        reason = shaping_probe.review_reason(script)
        lines.append(f'REVIEW conjunct shaping {script}: {reason} [{pages_of(pages)}]')
        statuses.append('REVIEW')
        findings.extend(Finding(p, script, reason) for p in sorted(set(pages)))
    ...
    return lines, status, findings
```

and update the docstring's first line to `(lines, status, findings)`. In `_execute_verify`:

```python
    if unshaped:
        record('arabic-letterforms', 'FAIL', f'{len(unshaped)} page(s)', findings=[
            Finding(pno + 1, 'page', f'{n} joining letters in isolated form, none connected')
            for pno, n in unshaped])
```

```python
    shaping_lines, shaping_status, shaping_findings = conjunct_shaping_report(jc)
    ...
    if shaping_status:
        record('conjunct-shaping', shaping_status, findings=shaping_findings)
```

- [ ] **Step 4: Run, watch it pass; also `tests.test_shaping_probe`** (it calls the report through `verify`, 19 tests, OK).

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_verify_report.py
git diff --cached --check
git commit -m "feat(pdf-translate): findings for the Arabic letterform and conjunct shaping gates"
```

---

### Task 4: findings for the leak gates, and "none" is PASS

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (the `running` / `isolated` block in `_execute_verify`)
- Modify: `pdf-translate/tests/test_import_surface.py` (one assertion in `test_trivial_job_records_every_printed_outcome`)
- Test: `pdf-translate/tests/test_verify_report.py`

**Interfaces:**
- Produces: `leak-running` FAIL → `Finding(page, 'run', phrase)` per (page, phrase), all of them; `leak-isolated` REVIEW → `Finding(page, 'token', word)` per distinct (page, word); when there are none the line is `PASS isolated source-script tokens: none` and the record is `('leak-isolated', 'PASS', 'none')`. This is the one deliberate console change in the whole plan.

- [ ] **Step 1: Write the failing tests**

```python
class LeakGateFindingsTests(unittest.TestCase):
    SOURCE = 'Alpha bravo charlie delta echo.'

    def test_running_text_names_page_and_phrase(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, source=self.SOURCE, target=self.SOURCE)
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'leak-running').status, 'FAIL')
            page, where, text = _findings(v, 'leak-running')[0]
            self.assertEqual((page, where), (1, 'run'))
            self.assertIn('bravo', text.lower())

    def test_isolated_token_is_named_and_none_is_pass(self):
        from pdf_translate.verify import run_verify, verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, source=self.SOURCE, target='Hola mundo alpha.')
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'leak-isolated').status, 'REVIEW')
            self.assertEqual(_findings(v, 'leak-isolated'), [(1, 'token', 'alpha')])
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, source=self.SOURCE, target='Hola mundo.')
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'leak-isolated').status, 'PASS')
            self.assertEqual(_findings(v, 'leak-isolated'), [])
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify(src, out, min_ink=0.1)
            self.assertIn('PASS isolated source-script tokens: none', buf.getvalue())
            self.assertNotIn('REVIEW isolated source-script tokens', buf.getvalue())
```

In `tests/test_import_surface.py`, change `self.assertEqual(gates.get('leak-isolated'), 'REVIEW', gates)` to `self.assertEqual(gates.get('leak-isolated'), 'PASS', gates)`.

- [ ] **Step 2: Run, watch it fail**

Run: `… -m unittest tests.test_verify_report.LeakGateFindingsTests tests.test_import_surface.VerdictCompletenessTests -v`
Expected: the two new tests fail on empty findings / `'REVIEW' != 'PASS'`; the import-surface test fails `'REVIEW' != 'PASS'`. If `test_isolated_token_is_named_and_none_is_pass` fails because the scan reports no token, the harvested word list needs 4-letter words: keep the SOURCE as given (every word has ≥ 4 letters) and check `scan_leaks` returns lowercase — adjust `'alpha'` to match what the console prints, never the other way round.

- [ ] **Step 3: Implement**

```python
    if running:
        print(f'FAIL untranslated running text ({len(running)}):')
        for pg, ph in running[:10]:
            print(f'   p{pg}: {ph}')
        fail = 1
        record('leak-running', 'FAIL', f'{len(running)}',
               findings=[Finding(pg, 'run', ph) for pg, ph in running])
    else:
        print('PASS no untranslated running text')
        record('leak-running', 'PASS')

    if isolated:
        uniq = sorted({w for _, w in isolated})
        print(f'REVIEW isolated source-script tokens ({len(uniq)}) - expected for '
              f'form names, statutes and proper nouns; confirm each is deliberate:')
        print('   ' + ', '.join(uniq[:20]))
        record('leak-isolated', 'REVIEW', f'{len(uniq)}',
               findings=[Finding(pg, 'token', w) for pg, w in sorted(set(isolated))])
    else:
        print('PASS isolated source-script tokens: none')
        record('leak-isolated', 'PASS', 'none')
```

- [ ] **Step 4: Run, watch it pass**; then `… -m unittest tests.test_pipeline -v 2>&1 | tail -3` must still end `OK` (its isolated-token test asserts the REVIEW line on a job that *has* tokens, which is unchanged).

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_verify_report.py pdf-translate/tests/test_import_surface.py
git diff --cached --check
git commit -m "feat(pdf-translate): findings for the leak gates; no isolated tokens is PASS, not REVIEW"
```

---

### Task 5: findings for the `--translations` gates

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (the `if translations:` block of `_execute_verify`)
- Test: `pdf-translate/tests/test_verify_report.py`

**Interfaces:**
- Produces: `empty-targets` → `Finding(None, 'target', t)`; `placement` → `Finding(None, 'target', t)`; `shaped-actualtext` → `Finding(None, 'target', t)`; `button-captions` → `Finding(None, name, cap)`; `caption-width` → `Finding(None, name, cap)`; `override-markers` → `Finding(None, contains, token)`; `metadata` → `Finding(None, what, detail)`; `scaled-runs` REVIEW → `Finding(int(r['page']) + 1, f'{float(r.get("ratio", 1)):.2f}x', str(r.get('key') or ''))` (the report file is 0-based; findings are 1-based); `identifiers` → `Finding(None, 'identifier', t)`. All lists complete, no `[:N]`.

- [ ] **Step 1: Write the failing tests**

```python
class TranslationGateFindingsTests(unittest.TestCase):
    def test_empty_target_and_missing_placement_name_the_target(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            _tiny_pdf(out, 'Adios.')
            Path(tr).write_text(json.dumps({'translations': {'Hello world.': 'Hola mundo.', 'Other': '   '},
                                            'skip': []}), encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'empty-targets'), [(None, 'target', 'Other')])
            self.assertEqual(_findings(v, 'placement'), [(None, 'target', 'Hola mundo.')])

    def test_findings_are_not_truncated_like_the_console(self):
        from pdf_translate.verify import run_verify, verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            _tiny_pdf(out, 'Adios.')
            targets = {f'Source line {i:02d}': f'Target line {i:02d}' for i in range(35)}
            Path(tr).write_text(json.dumps({'translations': targets, 'skip': []}), encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(len(_findings(v, 'placement')), 35)
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify(src, out, translations=tr, min_ink=0.1)
            printed = [ln for ln in buf.getvalue().splitlines() if ln.startswith('   Target line ')]
            self.assertEqual(len(printed), 30)   # the console's [:30] limit, unchanged

    def test_glyph_by_glyph_target_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Peace be upon you and mercy')
            Path(tr).write_text(json.dumps({'translations': {'Peace be upon you and mercy': AR_PHRASE},
                                            'skip': []}, ensure_ascii=False), encoding='utf-8')
            _arabic_glyph_by_glyph(bad)
            v = run_verify(src, bad, translations=tr, min_ink=0.05)
            self.assertEqual(_findings(v, 'shaped-actualtext'), [(None, 'target', AR_PHRASE)])

    def test_vanished_identifier_is_named(self):
        from pdf_translate.verify import run_verify
        from tests.test_pipeline import QUOTE_LINE, SCHED_LINE, VANISH_IDENT_TR, build_identifier_pdf
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_identifier_pdf(src)
            doc = pymupdf.open()
            try:
                page = doc.new_page(width=612, height=792)
                page.insert_text((72, 80), VANISH_IDENT_TR[QUOTE_LINE], fontsize=12)
                page.insert_text((72, 110), VANISH_IDENT_TR[SCHED_LINE], fontsize=12)
                doc.save(out)
            finally:
                doc.close()
            Path(tr).write_text(json.dumps({'translations': VANISH_IDENT_TR, 'skip': []},
                                           ensure_ascii=False), encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_gate(v, 'identifiers').status, 'FAIL')
            names = [text for _, where, text in _findings(v, 'identifiers') if where == 'identifier']
            self.assertIn('Attachment A', names)

    def test_metadata_scaled_runs_and_override_markers_are_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, lang='es',
                                scale_report=[{'page': 0, 'ratio': 0.85, 'key': 'Hello world.'}])
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            (page, where, text), = _findings(v, 'metadata')
            self.assertEqual((page, where), (None, 'lang'))
            self.assertIn('"es"', text)
            self.assertEqual(_findings(v, 'scaled-runs'), [(1, '0.85x', 'Hello world.')])
        segments = [{'page': 0, 'text': 'd. Hello world.        .... $', 'marker': 'd.',
                     'core': 'Hello world.', 'dots': '....', 'tail': '$'}]
        drop = [{'page': 0, 'contains': 'Hello world.',
                 'parts': [{'text': 'Hola mundo.', 'x': 72.0}]}]
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, overrides=drop, segments=segments)
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'override-markers'),
                             [(None, 'Hello world.', 'd.'), (None, 'Hello world.', '$')])

    def test_button_caption_gates_name_field_and_caption(self):
        from pdf_translate.verify import run_verify
        from tests.test_pipeline import (LONG_CAPTION, NARROW_BTN, SHORT_CAPTION, SOURCE_SENTENCE,
                                         TARGET_SENTENCE, build_narrow_button_pdf)
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_narrow_button_pdf(src)
            shutil.copy(src, out)   # caption still SHORT_CAPTION in the output
            Path(tr).write_text(json.dumps({'translations': {SOURCE_SENTENCE: TARGET_SENTENCE,
                                                             SHORT_CAPTION: 'Aceptar'}, 'skip': []}),
                                encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'button-captions'), [(None, NARROW_BTN, SHORT_CAPTION)])
            self.assertEqual(_gate(v, 'caption-width').status, 'PASS')
            doc = pymupdf.open(src)
            try:
                for w in doc[0].widgets():
                    if w.field_name == NARROW_BTN:
                        w.button_caption = LONG_CAPTION
                        w.update()
                doc.save(out)
            finally:
                doc.close()
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'caption-width'), [(None, NARROW_BTN, LONG_CAPTION)])
```

- [ ] **Step 2: Run, watch it fail** (`… -m unittest tests.test_verify_report.TranslationGateFindingsTests -v`): every test fails on `[] != [...]`. If `test_button_caption_gates_name_field_and_caption` fails on the *status* of `button-captions` (the gate does not see the leftover), print the console log for that job and read `leftover_button_captions` before touching the assertion; the finding shape is what this task owns, the gate's semantics are not.

- [ ] **Step 3: Implement** — each `record(... 'FAIL' ...)` in the `if translations:` block gains `findings=`:

```python
            record('empty-targets', 'FAIL', f'{len(blanks)}',
                   findings=[Finding(None, 'target', t) for t in blanks])
            record('placement', 'FAIL', f'{len(missing)}',
                   findings=[Finding(None, 'target', t) for t in missing])
            record('shaped-actualtext', 'FAIL', f'{len(unmarked)}',
                   findings=[Finding(None, 'target', t) for t in unmarked])
            record('button-captions', 'FAIL', f'{len(leftover)}',
                   findings=[Finding(None, name, cap) for name, cap in leftover])
            record('caption-width', 'FAIL', f'{len(clipped)}',
                   findings=[Finding(None, name, cap) for name, cap in clipped])
            record('override-markers', 'FAIL', f'{len(misses)}',
                   findings=[Finding(None, contains, token) for contains, token in misses])
            record('metadata', 'FAIL', ', '.join(what for what, _ in meta_misses),
                   findings=[Finding(None, what, detail) for what, detail in meta_misses])
            record('scaled-runs', 'REVIEW', f'{len(report)}', findings=[
                Finding((int(r.get('page', 0)) + 1), f'{float(r.get("ratio", 1)):.2f}x',
                        str(r.get('key') or '')) for r in report])
            record('identifiers', 'FAIL', f'{len(missing_ids)}',
                   findings=[Finding(None, 'identifier', t) for t in missing_ids])
```

- [ ] **Step 4: Run, watch it pass; run the parity check from Task 2 step 4 again** → `IDENTICAL` except the one `isolated source-script tokens: none` line per job, which now reads PASS (nine jobs → nine differing lines, nothing else). Record that diff output; Task 7's evidence doc quotes it.

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_verify_report.py
git diff --cached --check
git commit -m "feat(pdf-translate): findings for every --translations gate"
```

---

### Task 6: `--report`, `--fail-on-review`, pipeline wiring, parity runner

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (`_execute_verify` signature and tail, `run_verify`, `verify`, `main`)
- Modify: `pdf-translate/pdf_translate/pipeline.py` (`cmd_rebuild`)
- Modify: `dev/probes/verdict_parity_runner.py`
- Test: `pdf-translate/tests/test_verify_report.py`

**Interfaces:**
- Produces: `_execute_verify(..., fail_on_review=False)`, `run_verify(..., fail_on_review=False)`, `verify(..., fail_on_review=False)`; `main(argv)` accepts `--report PATH` (writes `verdict.to_dict()` as JSON, `ensure_ascii=False`, `indent=1`; on `OSError` prints `  (could not write PATH: exc)` and keeps the exit code) and `--fail-on-review`; `write_report(verdict, path)` helper. With `fail_on_review` and no FAIL but at least one REVIEW, `_execute_verify` prints `FAIL: {n} REVIEW line(s) with --fail-on-review` and returns 1.

- [ ] **Step 1: Write the failing tests**

```python
class ReportAndPolicyTests(unittest.TestCase):
    def _console(self, argv):
        from pdf_translate.verify import main
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(argv)
        lines = [ln for ln in buf.getvalue().splitlines() if not ln.startswith('elapsed ')]
        return rc, lines

    def test_report_flag_writes_the_verdict_and_leaves_the_console_alone(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, lang='es')
            report = os.path.join(tmp, 'verify_report.json')
            base = [src, out, '--translations', tr, '--min-ink', '0.1']
            rc_plain, plain = self._console(base)
            rc_rep, with_report = self._console(base + ['--report', report])
            self.assertEqual((rc_plain, rc_rep), (1, 1))
            self.assertEqual(plain, with_report)
            data = json.loads(Path(report).read_text(encoding='utf-8'))
            expected = run_verify(src, out, translations=tr, min_ink=0.1).to_dict()
            self.assertEqual(data, expected)
            self.assertEqual(data['schema'], 1)
            self.assertEqual((data['original'], data['output']), (src, out))
            names = [g['name'] for g in data['gates']]
            self.assertIn('metadata', names)
            meta = next(g for g in data['gates'] if g['name'] == 'metadata')
            self.assertEqual(meta['findings'][0]['where'], 'lang')

    def test_unwritable_report_path_keeps_the_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            rc, lines = self._console([src, out, '--translations', tr, '--min-ink', '0.1',
                                       '--report', os.path.join(tmp, 'no-such-dir', 'r.json')])
            self.assertEqual(rc, 0)
            self.assertTrue(any('could not write' in ln for ln in lines), lines)

    def test_fail_on_review_turns_review_into_exit_1(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)   # no lang -> metadata-lang REVIEW, no FAIL
            base = [src, out, '--translations', tr, '--min-ink', '0.1']
            self.assertEqual(self._console(base)[0], 0)
            rc, lines = self._console(base + ['--fail-on-review'])
            self.assertEqual(rc, 1)
            self.assertTrue(any(ln.startswith('FAIL: ') and 'REVIEW' in ln for ln in lines), lines)
            self.assertEqual(run_verify(src, out, translations=tr, min_ink=0.1).exit_code, 0)
            self.assertEqual(run_verify(src, out, translations=tr, min_ink=0.1,
                                        fail_on_review=True).exit_code, 1)

    def test_pipeline_rebuild_writes_the_report_into_the_work_dir(self):
        from pdf_translate.extract_segments import extract_segments
        from pdf_translate.pipeline import main as pipeline_main
        from pdf_translate.strip_text import strip_text
        latin = FONTS / 'NotoSans-Regular.ttf'
        if not latin.is_file():
            raise unittest.SkipTest('NotoSans-Regular.ttf not fetched (tools/fetch_test_fonts.py)')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            font = str(latin)
            Path(tr).write_text(json.dumps({
                'fonts': {'regular': font, 'bold': font, 'italic': font, 'bold_italic': font},
                'translations': {'Hello world.': 'Hola mundo.'}, 'lang': 'es',
                'merges': [], 'overrides': [], 'center': [], 'skip': []}), encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                strip_text(src, os.path.join(tmp, 'stripped.pdf'))
                extract_segments(src, outdir=tmp)
                rc = pipeline_main(['rebuild', '--work', tmp, src, out, '--min-ink', '0.1',
                                    '--translations', tr])
            self.assertEqual(rc, 0)
            data = json.loads(Path(tmp, 'verify_report.json').read_text(encoding='utf-8'))
            self.assertEqual(data['schema'], 1)
            self.assertEqual(data['exit_code'], 0)
```

- [ ] **Step 2: Run, watch it fail** (`… -m unittest tests.test_verify_report.ReportAndPolicyTests -v`): `--report` is ignored today, so the JSON file is missing (`FileNotFoundError`); `--fail-on-review` is ignored (`1 != 0`); `run_verify(..., fail_on_review=True)` is a `TypeError`; the pipeline test fails on the missing file. Check `pipeline.main` exists with that name (`grep -n "^def main" pdf_translate/pipeline.py`); if it is named differently, use that name in the test.

- [ ] **Step 3: Implement**

`_execute_verify`: add `fail_on_review=False` as the last parameter; replace the final `return (1 if fail else 0, gates)` with:

```python
    rc = 1 if fail else 0
    if fail_on_review and rc == 0:
        reviews = sum(1 for g in gates if g.status == 'REVIEW')
        if reviews:
            print(f'FAIL: {reviews} REVIEW line(s) with --fail-on-review')
            rc = 1
    return rc, gates
```

`run_verify` and `verify`: add `fail_on_review=False` and pass it through. Add after `run_verify`:

```python
def write_report(verdict, path):
    """verdict.to_dict() as JSON at path; a failure is printed, never raised."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(verdict.to_dict(), f, ensure_ascii=False, indent=1)
    except OSError as exc:
        print(f'  (could not write {path}: {exc})')
```

`main`: call `_execute_verify` instead of `verify` so the gates are in hand:

```python
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    orig, trans = argv[0], argv[1]
    allow = [w for w in (_arg(argv, '--allow', '') or '').split(',') if w]
    t0 = time.perf_counter()
    rc, gates = _execute_verify(
        orig, trans,
        fill_text=_arg(argv, '--fill-text', 'Test value 123'),
        allow=allow,
        min_ink=float(_arg(argv, '--min-ink', '0.4')),
        source_regex=_arg(argv, '--source-regex', None),
        source_words_from=_arg(argv, '--source-words-from', None),
        allow_extra_prefix=_arg(argv, '--allow-extra-prefix', None),
        translations=_arg(argv, '--translations', None),
        segments=_arg(argv, '--segments', None),
        fail_on_review='--fail-on-review' in argv,
    )
    report = _arg(argv, '--report', None)
    if report:
        write_report(VerifyVerdict(exit_code=rc, gates=tuple(gates),
                                   original=orig, output=trans), report)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return rc
```

Add `--report PATH` and `--fail-on-review` to the Usage block in the module docstring, one line: `[--report verify_report.json] [--fail-on-review]`.

`pipeline.py` `cmd_rebuild`: replace `rc = verify_main([orig, out] + extra)` with

```python
    if '--report' not in extra:
        extra = extra + ['--report', os.path.join(work, 'verify_report.json')]
    rc = verify_main([orig, out] + extra)
```

`dev/probes/verdict_parity_runner.py`: change the stderr summary line to
`print(f'--- verdict exit={v.exit_code} gates={len(v.gates)} findings={sum(len(g.findings) for g in v.gates)}', file=sys.stderr)`.

- [ ] **Step 4: Run, watch it pass; then the whole suite as CI runs it**

Run: `… -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report 2>&1 | tail -3`
Expected: `Ran 28x tests … OK` (266 before this plan plus the new ones), no failures, no errors.

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/pdf_translate/pipeline.py dev/probes/verdict_parity_runner.py pdf-translate/tests/test_verify_report.py
git diff --cached --check
git commit -m "feat(pdf-translate): --report writes the verdict as JSON; --fail-on-review for unattended runs"
```

---

### Task 7: version 51, CI, docs, evidence

**Files:**
- Modify: `pdf-translate/SKILL.md` (`version: "50"` → `"51"`, plus one sentence in the verify step), `.claude-plugin/plugin.json` (`"51.0.0"`), `pdf-translate/pyproject.toml` (`version = "51.0.0"`), `pdf-translate/pdf_translate/__init__.py` (`__version__ = '51'`)
- Modify: `.github/workflows/tests.yml` (suite line; lockstep check)
- Modify: `pdf-translate/references/gates.md` ("As a library" section), `docs/DECISIONS.md` (one row above "Add new rows above this line")
- Create: `docs/reviews/2026-09-16-verify-report.md`

**Interfaces:** none new. The lockstep check must fail if any of the four version sources disagree.

- [ ] **Step 1: Write the failing test** (a version-lockstep test that runs locally; CI keeps its own check too)

```python
class VersionLockstepTests(unittest.TestCase):
    def test_four_version_sources_agree(self):
        import re
        import pdf_translate
        root = SKILL.parent
        skill = re.search(r'^\s+version:\s*"(\d+)"', (SKILL / 'SKILL.md').read_text(encoding='utf-8'),
                          re.M).group(1)
        plugin = json.loads((root / '.claude-plugin' / 'plugin.json').read_text(encoding='utf-8'))['version']
        pyproject = re.search(r'^version\s*=\s*"([\d.]+)"', (SKILL / 'pyproject.toml').read_text(encoding='utf-8'),
                              re.M).group(1)
        self.assertEqual(plugin, f'{skill}.0.0')
        self.assertEqual(pyproject, plugin)
        self.assertEqual(pdf_translate.__version__, skill)
        self.assertEqual(skill, '51')
```

- [ ] **Step 2: Run, watch it fail**: `'50' != '51'`.

- [ ] **Step 3: Implement**

Bump the four files. In `.github/workflows/tests.yml`: the suite line becomes `python -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report -v`; replace the body of the "Plugin version matches metadata.version" step with:

```yaml
          python - <<'PY'
          import json, re
          plugin = json.load(open('.claude-plugin/plugin.json'))['version']
          text = open('pdf-translate/SKILL.md', encoding='utf-8').read()
          skill = re.search(r'^\s+version:\s*"(\d+)"', text, re.M).group(1)
          pyproject = re.search(r'^version\s*=\s*"([\d.]+)"', open('pdf-translate/pyproject.toml', encoding='utf-8').read(), re.M).group(1)
          init = re.search(r"^__version__\s*=\s*'(\d+)'", open('pdf-translate/pdf_translate/__init__.py', encoding='utf-8').read(), re.M).group(1)
          assert plugin == f'{skill}.0.0', f'plugin.json {plugin} vs metadata.version {skill}'
          assert pyproject == plugin, f'pyproject {pyproject} vs plugin.json {plugin}'
          assert init == skill, f'__version__ {init} vs metadata.version {skill}'
          print('plugin', plugin, '== metadata.version', skill, '== pyproject', pyproject, '== __version__', init)
          PY
```

and rename that step `Version sources agree (plugin, SKILL.md, pyproject, __version__)`.

`references/gates.md`, "As a library": append this paragraph after the existing one:

> Each `GateResult` carries `findings`, a tuple of `Finding(page, where, text)`: the page (1-based, or `None` for document-level gates), the thing the finding names (a field, a font's PostScript name, a script, `lang`, a `U+XXXX` code point, a `0.85x` scale) and the run, caption, token or detail, untruncated — the console prints the first ten to thirty, the verdict keeps them all. `verify.py … --report PATH` writes `verdict.to_dict()` as JSON (`schema` 1, the skill `version`, both paths, `exit_code`, `gates`); `pipeline.py rebuild` writes it to `<work>/verify_report.json`. `--fail-on-review` (CLI) or `fail_on_review=True` (library) turns a run with REVIEW lines and no FAIL into exit 1, for pipelines with nobody to read the REVIEW. Both are off by default. A consumer removes two REVIEWs on its own: always pass `lang` in the mapping (`metadata-lang`), and build faces with `prepare_font`, which adds the probe glyphs gate 18 needs (`conjunct-shaping` "cannot attest").

`SKILL.md`, in the verify invocation block near line 405, add the optional flag to the command (`[--report verify_report.json]`) and one sentence after it: "`--report` writes every gate and its findings as JSON; the pipeline's `rebuild` writes it into the work dir."

`docs/DECISIONS.md`, one row above "Add new rows above this line":

```
| 2026-09-16 | Every printed gate outcome carries its findings — `Finding(page, where, text)`, untruncated — in `VerifyVerdict.gates`; `--report PATH` writes `verdict.to_dict()` (schema 1) and `pipeline.py rebuild` writes it into the work dir; `--fail-on-review` / `fail_on_review=True` exits 1 on REVIEW without FAIL; both off by default. `isolated source-script tokens: none` is PASS, not REVIEW. Version 50 → 51; `pdf_translate.__version__` joins the lockstep check. | `docs/BRIEF-unattended-delivery.md`: in production nobody reads the console, so a REVIEW was indistinguishable from PASS at delivery and a FAIL carried no location. The locations were already printed; the verdict now keeps them all. The "none" line was a REVIEW that fired on every job. Console output is otherwise byte-identical (`dev/probes/verdict_parity_runner.py`, nine jobs). | A consumer that needs the console's truncation mirrored in the report, or a schema change — bump `schema` rather than editing version 1 in place. |
```

`docs/reviews/2026-09-16-verify-report.md`: write the evidence — the parity diff from Task 5 step 4 (nine identical jobs apart from the one PASS line each), the suite line and count, the canary line (`python -m unittest discover -s ../dev/canary -p test_score.py`), the list of tests written first and their red output, and the JSON of one real report (`meta-fail` from `dev/probes/verdict_parity_fixtures.py`) as the sample a consumer will see.

- [ ] **Step 4: Run everything**

```bash
PYTHONUTF8=1 …/python.exe -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report 2>&1 | tail -3
PYTHONUTF8=1 …/python.exe -m unittest discover -s ../dev/canary -p test_score.py 2>&1 | tail -3
git diff --check
```
Expected: both `OK`; `git diff --check` silent.

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/SKILL.md .claude-plugin/plugin.json pdf-translate/pyproject.toml pdf-translate/pdf_translate/__init__.py .github/workflows/tests.yml pdf-translate/references/gates.md docs/DECISIONS.md docs/reviews/2026-09-16-verify-report.md pdf-translate/tests/test_verify_report.py
git diff --cached --check
git commit -m "docs(pdf-translate): findings and --report in gates.md and SKILL.md; DECISIONS row; evidence; version 51"
```

Hand back: the branch name, the last commit, the suite and canary lines with counts, the parity diff summary, and the path of the evidence doc. Do not push.
