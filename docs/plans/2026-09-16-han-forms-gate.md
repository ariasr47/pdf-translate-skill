# Gate 20 `han-forms` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `verify` gains gate 20, `han-forms`: on every page that draws CJK text, each embedded face is rendered off its own font program and compared pixel for pixel with the Noto reference of the language's convention and with the other convention's, both instanced at the face's weight — PASS when the face draws its own convention's forms of 直 骨 海, FAIL when it draws the other's, REVIEW when it cannot be judged, one `Finding` per face per page — and `prepare_font` adds the four probe characters to every CJK subset and refuses a job whose face draws the wrong convention. Console output for every non-CJK job stays byte-identical. Version 53 → 54.

**Architecture:** Everything rests on the measurement in `docs/BRIEF-han-forms-gate.md` §2 (do not re-derive): within one Noto family a face against its own reference at equal weight reads 0.000 on every probe and 0.17–0.51 against the other region; weight alone reads 0.51–0.55, as large as region, so references are instanced at the delivered face's OS/2 weight; re-rendering the embedded program is exact (0.000), so the gate judges the face the way gate 18 does (`conjunct_shaping_report`: `doc.extract_font`, once per xref), not the page's pixels; 東 is drawn the same in both conventions, so a face that differs from both references on 東 is not a Noto face and is REVIEW, never matched to the nearer reference. A new module `pdf_translate/han_forms.py` owns the measurement (render, diff ratio, weight, instanced-and-cached references, the judge); `verify.py` owns the report and the record site; `prepare_font.py` adds the probes and judges early.

**Tech Stack:** Python 3.10+ (CI) / 3.14 (this machine), `unittest`, PyMuPDF 1.28, fontTools (`varLib.instancer`, `ttLib`). No new dependencies.

## Global Constraints

- Work on branch `feat/han-forms-gate`, which already exists and carries the probe and the brief. It is stacked on `fix/stale-verify-report` (PR #7, v53), itself on `feat/kinsoku-gate` (PR #6, v52). Never commit to `main`. Never push, merge or delete: the operator does those.
- Run every test from `C:\Dev\pdf-translate-skill\pdf-translate` with the repo venv and UTF-8: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest …`. Tests are `unittest`, invoked by module path, never pytest. Capture long runs to a log file and grep `^Ran |^OK|^FAILED` — Git-Bash `| tail` scrambles unittest output.
- TDD: write the test, run it, watch it fail for the expected reason, then write the minimal code. A test that passes on first run is wrong, with one named exception: Task 5 is documentation and has no red.
- **The measured table is the spec.** Thresholds are exact values: `OWN_MAX = 0.02`, `OTHER_MIN = 0.10`, `MIN_SEPARATING = 2` (of the three probes 直 骨 海); the control is 東. Geometry is the probe's: 48 pt, origin (40, 120) on a 200 pt square page, 4× zoom, grey, ink = sample < 128; diff ratio = pixels that are ink in one raster and not the other, over the pixels that are ink in either. Tests reproduce the brief's rows within 0.02.
- **Console output and exit codes of every CLI must not change for a job whose output has no CJK text.** `dev/probes/verdict_parity_runner.py` over its nine jobs (none CJK) must diff empty against `main`. A CJK job gains exactly the `han-forms` line(s).
- The gate prints only when a page draws CJK text (`verify.script_of(ch) == 'CJK'` for some letter) **and** `lang` is missing or names a CJK convention. `lang` comes from `--translations` (`lang`), else the output's `/Lang` (`doc.language`). No `lang` anywhere → REVIEW. A `lang` that is not Japanese, Chinese or Korean (`es`) → the gate prints nothing: the page's CJK is not the target's script, and the leak gates own it.
- `Finding.page` is 1-based. `Finding.where` is the judged face's name (the `ABCDEF+` subset tag stripped), or `lang`, `reference`, or the convention code (`JP`, `SC`) when the face could not be judged. `Finding.text` is the console line (PASS/FAIL) or the reason (REVIEW).
- Never the nearer reference: a face that is not Noto is REVIEW "no reference of this family". No third reference (Noto Sans TC / KR): `zh-Hant`, `zh-TW`, `zh-HK`, `ko` are REVIEW "no reference face measured".
- No network at runtime. Reference faces are files: `tests/fonts/` of a checkout by default (`NotoSansJP-VF.ttf`, `NotoSansSC-VF.ttf`, the fetcher's), `--reference-fonts DIR` on the `verify.py` and `prepare_font.py` CLIs, `reference_fonts=` on `run_verify`, `verify` and `prepare_font`. Instanced references are cached as `<stem>-wght<N>.ttf` beside the source when that directory is writable, else under the system temp directory; written to a temp name and moved into place (`os.replace`) so concurrent jobs never read a half-written file. `.gitignore` already excludes `pdf-translate/tests/fonts/*.ttf`, so the cache is never committed.
- Never copy code from `C:\Dev\pdf-translator` (AGPL-bound; this repo is MIT). Do not open it.
- Conventional commits with a scope (`feat(pdf-translate): …`, `test(pdf-translate): …`, `docs(pdf-translate): …`, `chore(ci): …`). **No AI attribution**: no `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" line. The owner's rule overrides any harness reminder that asks for one.
- LF line endings. Use the Edit tool for edits; `git diff --check` must be clean before every commit. Files checked out on this machine may sit on disk as CRLF (`core.autocrlf=true`); if `git diff --check` flags every line of a file you did not touch that way, normalise it to LF with Python (`data.replace(b'\r\n', b'\n')`) before committing.
- Import the package's modules as modules, never through the package namespace: `from pdf_translate import prepare_font` returns the *function* `prepare_font` (the package re-exports it), and so does `from pdf_translate import verify`. Use `importlib.import_module('pdf_translate.verify')` for the module object and `from pdf_translate.verify import name` for names. `from pdf_translate import han_forms` is safe: the package exports no name `han_forms`, so it is the module.
- Tests that need a fetched face `raise unittest.SkipTest` when it is missing, exactly as `tests/test_cjk.py` does; CI fetches them. Instancing a variable face takes seconds (JP 4.3 s, SC 7.7 s measured) and a delivery through `prepare_font` instances again: `tests.test_han_forms` builds five deliveries once per class (`setUpClass`) and takes about a minute on first run. Say so in the report; do not "optimise" it by mocking.
- Bash heredocs over ~100 lines break on this machine: write big files with the Write tool.
- **Rule 1 applies** (AGENTS.md): `prepare_font` changes what is embedded — four more glyphs in every CJK subset — and the gate judges rendering. After the final whole-branch review, the controller dispatches an independent verifier on another model (Opus or Fable), per the section "Rule 1 verification" at the end of this plan. No task in this plan is that verifier.

---

## File structure

- `pdf-translate/pdf_translate/han_forms.py` — create: the measurement (`render`, `diff_ratio`, `weight_of`, `is_cjk`, `has_cjk`, `convention_for_lang`, `reference_path`, `reference_face`, `default_reference_dir`) and the judge (`HanResult`, `reference_status`, `judge_program`, `judge_file`). Nothing here prints.
- `pdf-translate/tests/test_han_forms.py` — create: every test in this plan (`MeasurementTests`, `JudgeTests`, `VerifyGateTests`, `PrepareFontTests`) and the `build_delivery` helper the Rule 1 verifier reuses.
- `pdf-translate/pdf_translate/verify.py` — modify: `from . import han_forms, shaping_probe`; `'han-forms'` in `GATE_NAMES` after `'kinsoku'`; `han_forms_report(doc, lang, reference_dir=None)` after `kinsoku_report`; the record site after the kinsoku block; `reference_fonts=None` on `_execute_verify`, `run_verify`, `verify`; `--reference-fonts` in `main`; the module docstring's numbered list.
- `pdf-translate/pdf_translate/prepare_font.py` — modify: `from . import han_forms, shaping_probe`; `reference_fonts=None` on `prepare_font`; the probes added to a CJK charset; the early judge; `--reference-fonts` in `main`.
- `.github/workflows/tests.yml` — modify: the suite line gains `tests.test_han_forms`.
- `pdf-translate/SKILL.md`, `.claude-plugin/plugin.json`, `pdf-translate/pyproject.toml`, `pdf-translate/pdf_translate/__init__.py`, `pdf-translate/tests/test_verify_report.py` (lockstep literal) — version 54.
- `pdf-translate/references/gates.md`, `pdf-translate/references/fonts.md`, `pdf-translate/README.md`, `docs/DECISIONS.md`, `docs/reviews/2026-09-16-han-forms-gate.md` — docs and evidence. Tasks 1, 3 and 4 append their red and green runs to the evidence doc as they go; Task 5 completes it.

Test file header, created in Task 1 and extended by the tasks that say so:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate 20, han-forms: the face that drew a CJK page uses the forms its
language expects. The measured table in docs/BRIEF-han-forms-gate.md §2 is
reproduced first, so the thresholds rest on numbers this suite checks; then
the judge on font programs, the verify gate on deliveries built through the
pipeline, and prepare_font's probe glyphs and early refusal."""
import importlib
import io
import json
import os
import shutil
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pymupdf

from pdf_translate import han_forms

verify_mod = importlib.import_module('pdf_translate.verify')

FONTS = Path(__file__).resolve().parents[1] / 'tests' / 'fonts'
JP_FACE = FONTS / 'NotoSansJP-VF.ttf'
SC_FACE = FONTS / 'NotoSansSC-VF.ttf'
LATIN_FACE = FONTS / 'NotoSans-Regular.ttf'

TARGET = '\u76f4\u9aa8\u6d77\u6771\u4eac'          # 直骨海東京 — carries the probes
PLAIN = '\u7533\u8acb\u66f8\u3092\u63d0\u51fa'     # 申請書を提出 — no probe character


def _face(path):
    if not path.is_file():
        raise unittest.SkipTest(f'{path.name} not fetched (tools/fetch_test_fonts.py)')
    return path


def _font(path):
    return pymupdf.Font(fontfile=str(_face(path)))
```

---

### Task 1: the measurement — `han_forms.py` core, the brief's table reproduced

**Files:**
- Create: `pdf-translate/pdf_translate/han_forms.py`
- Create: `pdf-translate/tests/test_han_forms.py`
- Create: `docs/reviews/2026-09-16-han-forms-gate.md`

**Interfaces:**
- Consumes: nothing new. `verify.SCRIPT_RANGES['CJK']` is mirrored (verify will import this module, so this module cannot import verify).
- Produces: `HAN_PROBES = '直骨海'`, `HAN_CONTROL = '東'`, `HAN_CHARS = HAN_PROBES + HAN_CONTROL`, `OWN_MAX`, `OTHER_MIN`, `MIN_SEPARATING`, `CONVENTIONS`, `OTHER`, `CJK_RANGES`, `is_cjk(ch) -> bool`, `has_cjk(text) -> bool`, `convention_for_lang(lang) -> 'JP'|'SC'|'TC'|'KR'|None`, `default_reference_dir() -> Path`, `reference_path(convention, reference_dir) -> Path|None`, `reference_face(convention, weight, reference_dir) -> Path|None`, `render(font, ch) -> (bytes, w, h)`, `diff_ratio(a, b) -> float`, `weight_of(program: bytes) -> int|None`.

- [ ] **Step 1: Write the failing tests**

Create `pdf-translate/tests/test_han_forms.py` with the header above, then:

```python
class MeasurementTests(unittest.TestCase):
    """docs/BRIEF-han-forms-gate.md §2, reproduced within 0.02."""

    def setUp(self):
        self.jp, self.sc = _font(JP_FACE), _font(SC_FACE)

    def ratio(self, font_a, font_b, ch):
        return han_forms.diff_ratio(han_forms.render(font_a, ch), han_forms.render(font_b, ch))

    def test_a_face_against_itself_is_zero(self):
        for ch in han_forms.HAN_CHARS:
            self.assertEqual(self.ratio(self.jp, self.jp, ch), 0.0, ch)
            self.assertEqual(self.ratio(self.sc, self.sc, ch), 0.0, ch)

    def test_the_regions_separate_on_the_probes_and_agree_on_the_control(self):
        # Row 1 of the table: Noto JP vs Noto SC, both at the default instance (Thin).
        expected = {'\u76f4': 0.507, '\u9aa8': 0.217, '\u6d77': 0.364, '\u6771': 0.000}
        for ch, want in expected.items():
            self.assertAlmostEqual(self.ratio(self.jp, self.sc, ch), want, delta=0.02, msg=ch)

    def test_references_instanced_at_400_reproduce_the_table_and_are_cached(self):
        jp400 = han_forms.reference_face('JP', 400, FONTS)
        sc400 = han_forms.reference_face('SC', 400, FONTS)
        self.assertEqual((jp400.name, sc400.name),
                         ('NotoSansJP-VF-wght400.ttf', 'NotoSansSC-VF-wght400.ttf'))
        t0 = time.perf_counter()
        self.assertEqual(han_forms.reference_face('JP', 400, FONTS), jp400)
        self.assertLess(time.perf_counter() - t0, 1.0, 'a cached instance must not be instanced again')
        a, b = pymupdf.Font(fontfile=str(jp400)), pymupdf.Font(fontfile=str(sc400))
        # Row 4 of the table: region only, both at wght 400.
        expected = {'\u76f4': 0.454, '\u9aa8': 0.171, '\u6d77': 0.212, '\u6771': 0.000}
        for ch, want in expected.items():
            self.assertAlmostEqual(self.ratio(a, b, ch), want, delta=0.02, msg=ch)
        self.assertEqual(han_forms.weight_of(jp400.read_bytes()), 400)

    def test_weight_alone_is_as_large_a_difference_as_region(self):
        # Row 3 of the table: JP 400 vs JP 100 on 直 — why references are instanced at the
        # delivered weight instead of compared at the variable font's default.
        jp400 = pymupdf.Font(fontfile=str(han_forms.reference_face('JP', 400, FONTS)))
        self.assertAlmostEqual(self.ratio(jp400, self.jp, '\u76f4'), 0.523, delta=0.02)

    def test_no_reference_without_the_file_the_convention_or_the_axis(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(han_forms.reference_face('JP', 400, tmp))
        self.assertIsNone(han_forms.reference_face('TC', 400, FONTS))
        self.assertIsNone(han_forms.reference_face('JP', 950, FONTS))   # the wght axis ends at 900

    def test_convention_for_lang(self):
        cases = {'ja': 'JP', 'ja-JP': 'JP', 'JA': 'JP', 'zh': 'SC', 'zh-Hans': 'SC', 'zh-CN': 'SC',
                 'zh-SG': 'SC', 'zh_Hans_CN': 'SC', 'zh-Hant': 'TC', 'zh-TW': 'TC', 'zh-HK': 'TC',
                 'zh-MO': 'TC', 'ko': 'KR', 'ko-KR': 'KR', 'es': None, 'en-US': None, '': None,
                 None: None}
        for lang, want in cases.items():
            self.assertEqual(han_forms.convention_for_lang(lang), want, lang)

    def test_is_cjk_agrees_with_verify(self):
        sample = '\u76f4\u9aa8\u6d77\u6771 \u3072\u3089\u304c\u306a \u30ab\u30bf\u30ab\u30ca \uff76\uff80\uff76\uff85 \ud55c\uad6d\uc5b4 Latin 123 \u3002\u3001\u300c\u300d\u30fb\u30fc'
        for ch in sample:
            self.assertEqual(han_forms.is_cjk(ch), verify_mod.script_of(ch) == 'CJK', f'U+{ord(ch):04X}')
        self.assertTrue(han_forms.has_cjk('x\u6771y'))
        self.assertFalse(han_forms.has_cjk('\ud55c\uad6d\uc5b4 only'))
        self.assertFalse(han_forms.has_cjk(''))
        self.assertFalse(han_forms.has_cjk(None))

    def test_diff_ratio_edge_cases(self):
        blank = (bytes([255]) * 16, 4, 4)
        ink = (bytes([0]) * 16, 4, 4)
        self.assertEqual(han_forms.diff_ratio(blank, blank), 0.0)
        self.assertEqual(han_forms.diff_ratio(ink, ink), 0.0)
        self.assertEqual(han_forms.diff_ratio(ink, blank), 1.0)
        self.assertEqual(han_forms.diff_ratio(ink, (bytes([0]) * 9, 3, 3)), 1.0)
        half = (bytes([0]) * 8 + bytes([255]) * 8, 4, 4)
        self.assertEqual(han_forms.diff_ratio(ink, half), 0.5)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms -v 2>&1 | grep -E "^(Ran |OK|FAILED|ERROR|ImportError|ModuleNotFoundError)"`
Expected: `ModuleNotFoundError: No module named 'pdf_translate.han_forms'` (the import at the top of the test module fails; no test runs).

- [ ] **Step 3: Write the module**

Create `pdf-translate/pdf_translate/han_forms.py`:

```python
# -*- coding: utf-8 -*-
"""Gate 20, han-forms: the face that drew a CJK page uses the forms its
language expects.

Han unification gives 直 骨 海 one code point each; a Japanese face and a
Simplified Chinese face draw them differently, and a reader sees the wrong
region at once. This skill never selects a face — the caller does — so the
delivered document is judged: every embedded face on a page that draws CJK
text is rendered off its own font program (the way gate 18 re-probes a
conjunct face) and compared pixel for pixel with the Noto reference of the
language's convention and with the other convention's, both instanced at
the embedded face's weight.

Measured (docs/BRIEF-han-forms-gate.md; PyMuPDF 1.28.2, the fetched Noto
Sans JP / SC variable faces): a face against its own reference at equal
weight reads 0.000 on every probe; against the other region 0.17–0.51;
weight alone (400 vs 100) reads 0.51–0.55, as large as region, which is why
references are instanced at the delivered weight. 東 is drawn the same in
both conventions: a face that differs from both references on 東 is not a
Noto face and is REVIEW, never matched to the nearer reference.

Nothing here reads the network or prints. The reference faces are files the
caller provides: tests/fonts/ in a checkout, a directory of its own in a
service (verify --reference-fonts DIR, run_verify(reference_fonts=DIR)).
"""
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pymupdf

HAN_PROBES = '\u76f4\u9aa8\u6d77'       # 直 骨 海 — drawn differently in JP and SC
HAN_CONTROL = '\u6771'                   # 東 — the same in both: the family check
HAN_CHARS = HAN_PROBES + HAN_CONTROL     # what prepare_font adds to every CJK subset

OWN_MAX = 0.02          # a face equals its own reference (measured 0.000)
OTHER_MIN = 0.10        # and differs from the other region (measured 0.17–0.51)
MIN_SEPARATING = 2      # probes, of the three, that must separate

# convention -> (display name, reference file in the reference directory; None
# when no reference has been measured for it)
CONVENTIONS = {
    'JP': ('Japanese', 'NotoSansJP-VF.ttf'),
    'SC': ('Simplified Chinese', 'NotoSansSC-VF.ttf'),
    'TC': ('Traditional Chinese', None),
    'KR': ('Korean', None),
}
OTHER = {'JP': 'SC', 'SC': 'JP'}

# verify.SCRIPT_RANGES['CJK'], repeated here because verify imports this
# module; tests.test_han_forms pins the two against each other.
CJK_RANGES = ((0x3040, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
              (0xF900, 0xFAFF), (0xFF66, 0xFF9F), (0x20000, 0x2FA1F))

RENDER_SIZE, RENDER_ZOOM, RENDER_ORIGIN, RENDER_PAGE = 48, 4, (40, 120), 200


def is_cjk(ch):
    """The test verify.script_of makes for 'CJK': a letter in the Han, kana
    or half-width kana blocks. Punctuation (。、「) is not."""
    if not unicodedata.category(ch).startswith('L'):
        return False
    o = ord(ch)
    return any(a <= o <= b for a, b in CJK_RANGES)


def has_cjk(text):
    return any(is_cjk(ch) for ch in text or '')


def convention_for_lang(lang):
    """'JP', 'SC', 'TC' or 'KR' for a BCP 47 tag (ja, zh-Hans, zh-TW, ko…);
    None for any other language or no language."""
    tags = [t for t in (lang or '').strip().lower().replace('_', '-').split('-') if t]
    if not tags:
        return None
    if tags[0] == 'ja':
        return 'JP'
    if tags[0] == 'ko':
        return 'KR'
    if tags[0] == 'zh':
        if 'hant' in tags[1:] or any(t in ('tw', 'hk', 'mo') for t in tags[1:]):
            return 'TC'
        return 'SC'
    return None


def default_reference_dir():
    """tests/fonts/ of a checkout — the fetcher's faces. An installed package
    has no such directory; a consumer passes its own."""
    return Path(__file__).resolve().parents[1] / 'tests' / 'fonts'


def _dir(reference_dir):
    return Path(reference_dir) if reference_dir is not None else default_reference_dir()


def reference_path(convention, reference_dir=None):
    """The convention's variable reference face in the directory, or None."""
    _, filename = CONVENTIONS.get(convention, (None, None))
    if not filename:
        return None
    path = _dir(reference_dir) / filename
    return path if path.is_file() else None


def reference_face(convention, weight, reference_dir=None):
    """Path of the convention's reference instanced at weight, or None when the
    convention has no reference, the file is missing, or the wght axis does
    not reach the weight.

    Instancing takes seconds (JP 4.3 s, SC 7.7 s measured), so the instance is
    cached as <stem>-wght<weight>.ttf beside the source when that directory
    can be written, else under the system temp directory. It is written to a
    temp name and moved into place: a concurrent job never reads a
    half-written file, and two writers produce the same bytes.
    """
    src = reference_path(convention, reference_dir)
    if src is None:
        return None
    weight = int(weight)
    name = f'{src.stem}-wght{weight}.ttf'
    for cache_dir in (src.parent, Path(tempfile.gettempdir()) / 'pdf-translate-han-forms'):
        cached = cache_dir / name
        if cached.is_file():
            return cached
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=name + '.', suffix='.tmp', dir=str(cache_dir))
        except OSError:
            continue
        os.close(fd)
        try:
            _instance(src, weight, tmp)
            os.replace(tmp, cached)
            return cached
        except OSError:
            _discard(tmp)
            continue
        except Exception:       # not a variable font, or the axis does not reach the weight
            _discard(tmp)
            return None
    return None


def _discard(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _instance(src, weight, out):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    font = TTFont(str(src))
    axes = {a.axisTag: a for a in font['fvar'].axes} if 'fvar' in font else {}
    wght = axes.get('wght')
    if wght is None or not wght.minValue <= weight <= wght.maxValue:
        raise ValueError(f'{src.name} has no wght axis reaching {weight}')
    instancer.instantiateVariableFont(font, {'wght': weight}, inplace=True)
    font.save(out)


def render(font, ch):
    """Grey raster (samples, width, height) of one character drawn with a
    pymupdf.Font at the geometry the table was measured at."""
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=RENDER_PAGE, height=RENDER_PAGE)
        tw = pymupdf.TextWriter(page.rect)
        tw.append(RENDER_ORIGIN, ch, font=font, fontsize=RENDER_SIZE)
        tw.write_text(page)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(RENDER_ZOOM, RENDER_ZOOM),
                              colorspace=pymupdf.csGRAY, alpha=False)
        return bytes(pix.samples), pix.width, pix.height
    finally:
        doc.close()


_INK = bytes(1 if v < 128 else 0 for v in range(256))


def diff_ratio(a, b):
    """Pixels that are ink in one raster and not the other, over the pixels
    that are ink in either: 0.0 for identical rasters, 1.0 for rasters of
    different size. The samples become one bit per pixel (ink or not) packed
    into an int, so the union and the difference are two bit counts."""
    if a[1:] != b[1:]:
        return 1.0
    ma = int.from_bytes(a[0].translate(_INK), 'big')
    mb = int.from_bytes(b[0].translate(_INK), 'big')
    union = (ma | mb).bit_count()
    return (ma ^ mb).bit_count() / union if union else 0.0


def weight_of(program):
    """OS/2 usWeightClass of a font program held in memory, or None when it
    cannot be read (a bare CFF program, a Type 3 face)."""
    try:
        from fontTools.ttLib import TTFont
        with TTFont(BytesIO(program), lazy=True) as font:
            return int(font['OS/2'].usWeightClass)
    except Exception:
        return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms -v 2>&1 | grep -E "^(test_|Ran |OK|FAILED)"`
Expected: 8 tests, `OK`. The first run instances JP and SC at 400 (about 12 s) and leaves `NotoSansJP-VF-wght400.ttf` and `NotoSansSC-VF-wght400.ttf` in `tests/fonts/` (ignored by git: `git status --short tests/fonts` prints nothing). If a ratio misses its row by more than 0.02, the geometry differs from the probe's — compare `render` with `dev/probes/han_forms_probe.py`'s `render`; do not widen the delta.

- [ ] **Step 5: Start the evidence doc**

Create `docs/reviews/2026-09-16-han-forms-gate.md`:

```markdown
# Gate 20 `han-forms` — evidence (v54)

Branch `feat/han-forms-gate`, stacked on `fix/stale-verify-report` (PR #7, v53) and `feat/kinsoku-gate`
(PR #6, v52). Spec: `docs/BRIEF-han-forms-gate.md` (measured 2026-09-16 with
`dev/probes/han_forms_probe.py`); the product's request 2b, reframed by
`docs/reviews/2026-09-16-cjk-request-assessment.md` §3 item 3 and accepted by its ruling R4.
A rendering change (`prepare_font` embeds four more glyphs; the gate judges rasters): AGENTS.md
Rule 1 applies — see the last section.

## Task 1 — the measurement, red then green

Red (the module does not exist):

```
<paste the grep line from Step 2>
```

Green (the brief's rows 1, 3 and 4 within 0.02; the cache; the classifier pinned to verify's):

```
<paste the Ran/OK lines from Step 4, with the test names>
```
```

Replace the two `<paste …>` markers with the real output of Steps 2 and 4 — the doc must never contain a placeholder.

- [ ] **Step 6: Commit**

```bash
git add pdf-translate/pdf_translate/han_forms.py pdf-translate/tests/test_han_forms.py docs/reviews/2026-09-16-han-forms-gate.md
git diff --cached --check
git commit -m "feat(pdf-translate): han_forms measures a face against the Noto JP/SC references at its own weight"
```

---

### Task 2: the judge — `HanResult`, `reference_status`, `judge_program`, `judge_file`

**Files:**
- Modify: `pdf-translate/pdf_translate/han_forms.py` (append)
- Modify: `pdf-translate/tests/test_han_forms.py` (append `JudgeTests` and the `_subset` helper)

**Interfaces:**
- Consumes: Task 1's functions and constants; `shaping_probe.font_psname(fontfile)`.
- Produces: `HanResult(status, face, convention, weight, ratios, reason)` with `.line()`; `reference_status(convention, reference_dir=None) -> (bool, reason)`; `judge_program(program: bytes, convention, reference_dir=None, face='') -> HanResult`; `judge_file(fontfile, convention, reference_dir=None) -> HanResult`. Statuses: `PASS`, `FAIL`, `REVIEW`, `SKIP` (SKIP = the face carries too few probes to be judged; the report, Task 3, turns a page with only SKIPs into "cannot attest").

Console line shapes (pinned by the tests):
- `PASS han-forms Japanese: NotoSansJP-Regular draws Japanese forms (直 0.000/0.454, 骨 0.000/0.171, 海 0.000/0.212 vs Japanese/Simplified Chinese at wght 400)`
- `FAIL han-forms Japanese: NotoSansSC-Regular draws Simplified Chinese forms (直 0.454/0.000, … vs Japanese/Simplified Chinese at wght 400)`
- `REVIEW han-forms Japanese: <reason>` and, with no convention, `REVIEW han-forms: <reason>`

- [ ] **Step 1: Write the failing tests**

Append to `pdf-translate/tests/test_han_forms.py`, above the `if __name__` block:

```python
def _subset(src, text, out):
    """A subset of src carrying only text (fontTools), for a program that lacks probes."""
    from fontTools import subset
    options = subset.Options()
    font = subset.load_font(str(src), options)
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    subset.save_font(font, str(out), options)


class JudgeTests(unittest.TestCase):
    """judge_program on the references themselves, a Latin face, a probe-less
    subset and another family. Status and line shape."""

    @classmethod
    def setUpClass(cls):
        _face(JP_FACE), _face(SC_FACE)
        cls.jp400 = han_forms.reference_face('JP', 400, FONTS).read_bytes()
        cls.sc400 = han_forms.reference_face('SC', 400, FONTS).read_bytes()

    def test_the_japanese_reference_draws_japanese_forms(self):
        r = han_forms.judge_program(self.jp400, 'JP', FONTS, face='NotoSansJP-Regular')
        self.assertEqual(r.status, 'PASS', r)
        self.assertEqual(r.weight, 400)
        self.assertEqual([ch for ch, _, _ in r.ratios], list(han_forms.HAN_PROBES))
        self.assertTrue(all(own <= 0.02 and other >= 0.10 for _, own, other in r.ratios), r.ratios)
        self.assertTrue(r.line().startswith(
            'PASS han-forms Japanese: NotoSansJP-Regular draws Japanese forms (\u76f4 0.000/'), r.line())
        self.assertTrue(r.line().endswith(' vs Japanese/Simplified Chinese at wght 400)'), r.line())

    def test_the_japanese_reference_fails_a_simplified_chinese_job(self):
        r = han_forms.judge_program(self.jp400, 'SC', FONTS, face='NotoSansJP-Regular')
        self.assertEqual(r.status, 'FAIL', r)
        self.assertTrue(r.line().startswith(
            'FAIL han-forms Simplified Chinese: NotoSansJP-Regular draws Japanese forms ('), r.line())
        self.assertTrue(r.line().endswith(' vs Simplified Chinese/Japanese at wght 400)'), r.line())

    def test_the_chinese_reference_both_ways(self):
        self.assertEqual(han_forms.judge_program(self.sc400, 'SC', FONTS).status, 'PASS')
        self.assertEqual(han_forms.judge_program(self.sc400, 'JP', FONTS).status, 'FAIL')

    def test_a_latin_face_is_skipped(self):
        r = han_forms.judge_program(_face(LATIN_FACE).read_bytes(), 'JP', FONTS, face='NotoSans-Regular')
        self.assertEqual(r.status, 'SKIP', r)
        self.assertIn('NotoSans-Regular does not carry the probes', r.reason)

    def test_fewer_than_two_probes_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'thin.ttf')
            _subset(han_forms.reference_face('JP', 400, FONTS), '\u76f4\u6771', out)   # 直 東 only
            r = han_forms.judge_file(out, 'JP', FONTS)
        self.assertEqual(r.status, 'SKIP', r)

    def test_another_family_is_review_not_the_nearer_reference(self):
        # MuPDF's bundled CJK face (Droid Sans Fallback) carries the probes but is not Noto:
        # 東, identical in JP and SC, differs from both references.
        r = han_forms.judge_program(pymupdf.Font('cjk').buffer, 'JP', FONTS, face='DroidSansFallback')
        self.assertEqual(r.status, 'REVIEW', r)
        self.assertIn('no reference of this family', r.reason)
        self.assertEqual(r.line(), f'REVIEW han-forms Japanese: {r.reason}')

    def test_document_level_reasons(self):
        r = han_forms.judge_program(self.jp400, None, FONTS)
        self.assertEqual(r.status, 'REVIEW', r)
        self.assertIn('no "lang" names the convention', r.reason)
        self.assertEqual(r.line(), f'REVIEW han-forms: {r.reason}')
        r = han_forms.judge_program(self.jp400, 'TC', FONTS)
        self.assertEqual(r.status, 'REVIEW', r)
        self.assertIn('no reference face measured for Traditional Chinese', r.reason)
        with tempfile.TemporaryDirectory() as tmp:
            r = han_forms.judge_program(self.jp400, 'JP', tmp)
        self.assertEqual(r.status, 'REVIEW', r)
        self.assertIn('reference faces not found in', r.reason)
        self.assertIn('NotoSansJP-VF.ttf, NotoSansSC-VF.ttf', r.reason)
        self.assertEqual(han_forms.reference_status('JP', FONTS), (True, ''))
        self.assertFalse(han_forms.reference_status('KR', FONTS)[0])

    def test_judge_file_names_the_face_from_its_program(self):
        r = han_forms.judge_file(han_forms.reference_face('JP', 400, FONTS), 'JP', FONTS)
        self.assertEqual(r.status, 'PASS', r)
        self.assertTrue(r.face.startswith('NotoSansJP'), r.face)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms.JudgeTests -v 2>&1 | grep -E "^(test_|Ran |OK|FAILED|AttributeError)"`
Expected: every test `ERROR` with `AttributeError: module 'pdf_translate.han_forms' has no attribute 'judge_program'` (or `judge_file` / `reference_status`).

- [ ] **Step 3: Write the judge**

Append to `pdf-translate/pdf_translate/han_forms.py`:

```python
@dataclass(frozen=True)
class HanResult:
    """One face judged against one convention. status is PASS, FAIL, REVIEW
    or SKIP; SKIP means the face carries too few of the probes to be judged
    (a Latin face on a CJK page), and the report turns a page with nothing
    but SKIPs into "cannot attest"."""
    status: str
    face: str
    convention: str      # 'JP' / 'SC' / 'TC' / 'KR', or '' when no lang named one
    weight: int | None
    ratios: tuple        # ((char, own, other), …) for the probes judged
    reason: str

    def line(self):
        """One report line in verify's PASS/FAIL/REVIEW style."""
        want = CONVENTIONS[self.convention][0] if self.convention in CONVENTIONS else ''
        head = f'{self.status} han-forms{" " + want if want else ""}'
        if self.status in ('PASS', 'FAIL'):
            other = CONVENTIONS[OTHER[self.convention]][0]
            cells = ', '.join(f'{ch} {own:.3f}/{oth:.3f}' for ch, own, oth in self.ratios)
            drawn = want if self.status == 'PASS' else other
            return (f'{head}: {self.face} draws {drawn} forms '
                    f'({cells} vs {want}/{other} at wght {self.weight})')
        return f'{head}: {self.reason}'


def reference_status(convention, reference_dir=None):
    """(True, '') when the convention can be judged with the faces in the
    directory; else (False, reason) — the document-level REVIEW reasons."""
    if convention not in CONVENTIONS:
        return False, ('no "lang" names the convention; pass lang in translations.json '
                       '(ja, zh-Hans, …) so the delivered faces can be judged')
    name, filename = CONVENTIONS[convention]
    if filename is None:
        return False, (f'no reference face measured for {name}; the gate judges Japanese '
                       f'and Simplified Chinese')
    ref_dir = _dir(reference_dir)
    missing = [CONVENTIONS[c][1] for c in (convention, OTHER[convention])
               if not (ref_dir / CONVENTIONS[c][1]).is_file()]
    if missing:
        return False, (f'reference faces not found in {ref_dir} ({", ".join(missing)}); '
                       f'fetch them (tools/fetch_test_fonts.py) or pass --reference-fonts DIR')
    return True, ''


def judge_program(program, convention, reference_dir=None, face=''):
    """Judge a font program (bytes) against the convention's reference and the
    other convention's, both instanced at the program's own weight."""
    ref_dir = _dir(reference_dir)
    face = face or ''
    ok, reason = reference_status(convention, ref_dir)
    if not ok:
        return HanResult('REVIEW', face, convention if convention in CONVENTIONS else '',
                         None, (), reason)
    try:
        font = pymupdf.Font(fontbuffer=program)
    except Exception as exc:
        return HanResult('REVIEW', face, convention, None, (),
                         f'could not load the embedded font {face}: {exc}')
    face = face or font.name
    present = [ch for ch in HAN_PROBES if font.has_glyph(ord(ch))]
    if len(present) < MIN_SEPARATING or not font.has_glyph(ord(HAN_CONTROL)):
        return HanResult('SKIP', face, convention, None, (),
                         f'{face} does not carry the probes "{HAN_CHARS}"')
    weight = weight_of(program)
    if weight is None:
        return HanResult('REVIEW', face, convention, None, (),
                         f'cannot read the weight (OS/2) of {face}; not a TrueType or '
                         f'OpenType program')
    own_ref = reference_face(convention, weight, ref_dir)
    other_ref = reference_face(OTHER[convention], weight, ref_dir)
    if own_ref is None or other_ref is None:
        return HanResult('REVIEW', face, convention, weight, (),
                         f'the reference faces cannot be instanced at wght {weight} for {face}')
    own_font = pymupdf.Font(fontfile=str(own_ref))
    other_font = pymupdf.Font(fontfile=str(other_ref))

    def pair(ch):
        mine = render(font, ch)
        return diff_ratio(mine, render(own_font, ch)), diff_ratio(mine, render(other_font, ch))

    c_own, c_other = pair(HAN_CONTROL)
    if c_own > OWN_MAX or c_other > OWN_MAX:
        return HanResult('REVIEW', face, convention, weight, ((HAN_CONTROL, c_own, c_other),),
                         f'no reference of this family: {face} differs from both Noto references '
                         f'on {HAN_CONTROL} ({c_own:.3f}/{c_other:.3f}), which is drawn the same '
                         f'in both conventions; check a render with a reader of the language')
    ratios = tuple((ch, *pair(ch)) for ch in present)
    own_wins = sum(own <= OWN_MAX and other >= OTHER_MIN for _, own, other in ratios)
    other_wins = sum(other <= OWN_MAX and own >= OTHER_MIN for _, own, other in ratios)
    if own_wins >= MIN_SEPARATING and not other_wins:
        return HanResult('PASS', face, convention, weight, ratios, '')
    if other_wins >= MIN_SEPARATING and not own_wins:
        return HanResult('FAIL', face, convention, weight, ratios, '')
    cells = ', '.join(f'{ch} {own:.3f}/{other:.3f}' for ch, own, other in ratios)
    return HanResult('REVIEW', face, convention, weight, ratios,
                     f'inconclusive for {face} ({cells} vs own/other at wght {weight}); '
                     f'check a render with a reader of the language')


def judge_file(fontfile, convention, reference_dir=None):
    """judge_program for a font file (prepare_font's subset)."""
    from .shaping_probe import font_psname
    with open(fontfile, 'rb') as f:
        program = f.read()
    return judge_program(program, convention, reference_dir,
                         face=font_psname(fontfile) or os.path.basename(str(fontfile)))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms -v 2>&1 | grep -E "^(test_|Ran |OK|FAILED)"`
Expected: 16 tests, `OK`. If `test_another_family_is_review_not_the_nearer_reference` comes back with the reason `cannot read the weight`, `pymupdf.Font('cjk').buffer` is not a TrueType program on this build — report it as BLOCKED with the reason text; do not change the test to the weaker reason.

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/pdf_translate/han_forms.py pdf-translate/tests/test_han_forms.py
git diff --cached --check
git commit -m "feat(pdf-translate): han_forms judges a font program — PASS its own convention, FAIL the other, REVIEW when it cannot say"
```

---

### Task 3: gate 20 in `verify`, `reference_fonts` plumbing, parity against `main`

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (import line 154; `GATE_NAMES` ~line 269; after `kinsoku_report`; the record site after the kinsoku block ~line 1532; `_execute_verify` ~1304, `run_verify` ~1765, `verify` ~1787, `main` ~1846; the module docstring's list)
- Modify: `pdf-translate/tests/test_han_forms.py` (imports, `build_delivery`, `VerifyGateTests`)
- Modify: `docs/reviews/2026-09-16-han-forms-gate.md` (append)

**Interfaces:**
- Consumes: `han_forms.judge_program`, `han_forms.reference_status`, `han_forms.convention_for_lang`, `han_forms.CONVENTIONS`, `han_forms.HAN_CHARS`; verify's `_has_cjk`, `page_search_text`, `Finding`, `record`.
- Produces: `verify.han_forms_report(doc, lang, reference_dir=None) -> (lines, status, findings)`; `'han-forms'` in `GATE_NAMES`; `reference_fonts=None` on `_execute_verify`, `run_verify`, `verify`; `--reference-fonts DIR` on the CLI. `tests.test_han_forms.build_delivery(tmp, face, target, lang, instance='wght=400', prepare_lang=None) -> (orig, out, translations, subset)`.

- [ ] **Step 1: Write the failing tests**

In `pdf-translate/tests/test_han_forms.py`, add after `verify_mod = …`:

```python
from pdf_translate.verify import GATE_NAMES, run_verify, verify
```

(`han_forms_report` is reached through `verify_mod`.) Add after `_font`:

```python
def build_delivery(tmp, face, target, lang, instance='wght=400', prepare_lang=None):
    """A real delivery: orig -> extract -> strip -> prepare_font(face, instance)
    -> retypeset. prepare_font sees a mapping with prepare_lang (None: no lang,
    so its own han-forms check stays quiet); retypeset sees lang, which it
    writes as /Lang. Returns (orig, out, translations, subset)."""
    from tests.test_pipeline import (SOURCE_SENTENCE, build_plain_pdf, extract_segments,
                                     prepare_font, retypeset, strip_text, write_mapping)
    src, stripped, out = (os.path.join(tmp, n) for n in ('orig.pdf', 'stripped.pdf', 'out.pdf'))
    tr, subset = os.path.join(tmp, 'translations.json'), os.path.join(tmp, 'subset.ttf')
    build_plain_pdf(src)
    extract_segments.extract_segments(src, outdir=tmp)
    strip_text.strip_text(src, stripped)
    write_mapping(tr, {SOURCE_SENTENCE: target}, Path(face), lang=prepare_lang)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = prepare_font.prepare_font(str(face), tr, subset, instance=instance)
    assert rc == 0, buf.getvalue()
    write_mapping(tr, {SOURCE_SENTENCE: target}, Path(subset), lang=lang)
    with redirect_stdout(buf):
        rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
    assert rc == 0, buf.getvalue()
    return src, out, tr, subset


def _with_lang(job, lang, name):
    """The same delivery judged under another mapping lang (or none)."""
    src, out, tr, subset = job
    tr2 = os.path.join(os.path.dirname(tr), name)
    with open(tr, encoding='utf-8') as f:
        data = json.load(f)
    data.pop('lang', None)
    if lang is not None:
        data['lang'] = lang
    with open(tr2, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return src, out, tr2, subset
```

Append the class above the `if __name__` block:

```python
class VerifyGateTests(unittest.TestCase):
    """Gate 20 on deliveries built through the pipeline. Five deliveries, once
    per class; about a minute on first run (prepare_font instances the
    variable face for each)."""

    @classmethod
    def setUpClass(cls):
        _face(JP_FACE), _face(SC_FACE)
        cls.tmp = tempfile.TemporaryDirectory()

        def job(name, **kw):
            d = os.path.join(cls.tmp.name, name)
            os.mkdir(d)
            return build_delivery(d, **kw)

        cls.ja_jp = job('ja-jp', face=JP_FACE, target=TARGET, lang='ja')
        cls.ja_sc = job('ja-sc', face=SC_FACE, target=TARGET, lang='ja')
        cls.nolang = job('nolang', face=JP_FACE, target=TARGET, lang=None)
        cls.plain = job('plain', face=JP_FACE, target=PLAIN, lang='ja')
        cls.bold = job('bold', face=JP_FACE, target=TARGET, lang='ja', instance='wght=700')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def console(self, job, **kw):
        src, out, tr, _ = job
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = verify(src, out, translations=tr, min_ink=0.1, **kw)
        return rc, buf.getvalue().splitlines()

    def gate(self, job, **kw):
        src, out, tr, _ = job
        v = run_verify(src, out, translations=tr, min_ink=0.1, **kw)
        found = [g for g in v.gates if g.name == 'han-forms']
        return v.exit_code, (found[0] if found else None)

    def test_the_gate_is_named_after_kinsoku(self):
        self.assertEqual(GATE_NAMES[GATE_NAMES.index('kinsoku') + 1], 'han-forms')

    def test_a_japanese_delivery_in_the_japanese_face_passes(self):
        rc, lines = self.console(self.ja_jp)
        self.assertEqual(rc, 0, lines)
        line = [l for l in lines if l.startswith('PASS han-forms Japanese: ')]
        self.assertEqual(len(line), 1, lines)
        self.assertIn('draws Japanese forms', line[0])
        self.assertIn('at wght 400) [page 1]', line[0])
        rc, gate = self.gate(self.ja_jp)
        self.assertEqual((rc, gate.status), (0, 'PASS'), gate)
        self.assertEqual(len(gate.findings), 1, gate)
        self.assertEqual(gate.findings[0].page, 1)
        # MuPDF names the embedded face with spaces ('Noto Sans JP Regular'), as test_cjk found.
        self.assertTrue(gate.findings[0].where.replace(' ', '').startswith('NotoSansJP'), gate.findings[0])
        self.assertTrue(gate.findings[0].text.startswith('PASS han-forms Japanese: '), gate.findings[0])

    def test_a_japanese_delivery_in_the_chinese_face_fails(self):
        rc, lines = self.console(self.ja_sc)
        self.assertEqual(rc, 1, lines)
        line = [l for l in lines if l.startswith('FAIL han-forms Japanese: ')]
        self.assertEqual(len(line), 1, lines)
        self.assertIn('draws Simplified Chinese forms', line[0])
        self.assertIn('[page 1] — a reader of the language sees the other region', line[0])
        rc, gate = self.gate(self.ja_sc)
        self.assertEqual((rc, gate.status), (1, 'FAIL'), gate)
        self.assertTrue(gate.findings[0].where.replace(' ', '').startswith('NotoSansSC'), gate.findings[0])
        self.assertTrue(gate.findings[0].text.startswith('FAIL han-forms Japanese: '), gate.findings[0])
        self.assertNotIn('[page', gate.findings[0].text)

    def test_the_mapping_lang_names_the_convention(self):
        # The Japanese-face output judged as a Simplified Chinese job: the mapping's lang wins
        # over /Lang. (The mapping's zh-Hans also disagrees with the output's /Lang ja, which the
        # metadata gate FAILs on its own, so the exit code is asserted through the FAIL names.)
        src, out, tr, _ = _with_lang(self.ja_jp, 'zh-Hans', 'zh.json')
        v = run_verify(src, out, translations=tr, min_ink=0.1)
        gate = [g for g in v.gates if g.name == 'han-forms'][0]
        self.assertEqual((v.exit_code, gate.status), (1, 'FAIL'), gate)
        self.assertIn('han-forms', [g.name for g in v.gates if g.status == 'FAIL'])
        self.assertTrue(gate.findings[0].text.startswith('FAIL han-forms Simplified Chinese: '),
                        gate.findings[0].text)

    def test_without_translations_the_output_lang_is_used(self):
        src, out, _, _ = self.ja_jp
        v = run_verify(src, out, min_ink=0.1)
        gate = [g for g in v.gates if g.name == 'han-forms'][0]
        self.assertEqual(gate.status, 'PASS', gate)

    def test_no_lang_anywhere_is_review(self):
        rc, gate = self.gate(self.nolang)
        self.assertEqual((rc, gate.status), (0, 'REVIEW'), gate)
        self.assertEqual(gate.findings[0].where, 'lang')
        self.assertIn('no "lang" names the convention', gate.findings[0].text)
        _, lines = self.console(self.nolang)
        self.assertTrue(any(l.startswith('REVIEW han-forms: no "lang" names the convention')
                            and l.endswith('[page 1]') for l in lines), lines)

    def test_a_non_cjk_lang_on_a_cjk_page_prints_nothing(self):
        # The page's CJK is not the target's script (a leak, a notice): the leak gates own it.
        rc, gate = self.gate(_with_lang(self.ja_jp, 'es', 'es.json'))
        self.assertIsNone(gate)
        _, lines = self.console(_with_lang(self.ja_jp, 'es', 'es.json'))
        self.assertFalse([l for l in lines if 'han-forms' in l], lines)

    def test_a_subset_without_the_probes_is_review_cannot_attest(self):
        rc, gate = self.gate(self.plain)
        self.assertEqual((rc, gate.status), (0, 'REVIEW'), gate)
        self.assertEqual(gate.findings[0].where, 'JP')
        self.assertIn('cannot attest: no embedded face carries the probes', gate.findings[0].text)
        _, lines = self.console(self.plain)
        self.assertTrue(any(l.startswith('REVIEW han-forms Japanese: cannot attest [page 1]: '
                                         'no embedded face carries the probes "\u76f4\u9aa8\u6d77\u6771"')
                            for l in lines), lines)

    def test_a_bold_delivery_is_judged_at_its_own_weight(self):
        rc, gate = self.gate(self.bold)
        self.assertEqual((rc, gate.status), (0, 'PASS'), gate)
        self.assertIn('at wght 700', gate.findings[0].text)

    def test_missing_reference_faces_are_review(self):
        with tempfile.TemporaryDirectory() as empty:
            rc, gate = self.gate(self.ja_jp, reference_fonts=empty)
        self.assertEqual((rc, gate.status), (0, 'REVIEW'), gate)
        self.assertEqual(gate.findings[0].where, 'reference')
        self.assertIn('reference faces not found in', gate.findings[0].text)

    def test_traditional_chinese_has_no_reference_yet(self):
        src, out, tr, _ = _with_lang(self.ja_jp, 'zh-Hant', 'hant.json')
        v = run_verify(src, out, translations=tr, min_ink=0.1)
        gate = [g for g in v.gates if g.name == 'han-forms'][0]
        self.assertEqual(gate.status, 'REVIEW', gate)
        self.assertEqual(gate.findings[0].where, 'reference')
        self.assertIn('no reference face measured for Traditional Chinese', gate.findings[0].text)
        # The mapping's zh-Hant disagrees with the output's /Lang ja, which the metadata gate
        # FAILs on its own; han-forms must not be among the FAILs (a REVIEW never exits 1).
        self.assertEqual([g.name for g in v.gates if g.status == 'FAIL'], ['metadata'], v.gates)

    def test_the_cli_takes_reference_fonts(self):
        src, out, tr, _ = self.ja_jp
        with tempfile.TemporaryDirectory() as empty:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify_mod.main([src, out, '--translations', tr, '--min-ink', '0.1',
                                      '--reference-fonts', empty])
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertIn('REVIEW han-forms Japanese: reference faces not found in', buf.getvalue())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms.VerifyGateTests -v > "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task3-red.log" 2>&1; grep -E "^(test_|Ran |OK|FAILED|ERROR)" "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task3-red.log"`
Expected: `test_the_gate_is_named_after_kinsoku` fails with `IndexError` or `ValueError: 'han-forms'…`; `test_a_japanese_delivery_in_the_chinese_face_fails` fails with `1 != 0`-style assertions (the SC delivery verifies exit 0 today: nothing judges the face); the PASS/REVIEW tests fail with `AttributeError: 'NoneType' object has no attribute 'status'` (no gate named han-forms); `test_missing_reference_faces_are_review` and `test_the_cli_takes_reference_fonts` fail with `TypeError: … unexpected keyword argument 'reference_fonts'` / the REVIEW line missing. Every test of the class must be red for one of those reasons. **The red for the SC delivery is the gate's whole point: keep its output for the evidence doc.**

- [ ] **Step 3: Write the gate**

In `pdf-translate/pdf_translate/verify.py`:

(a) The import (line 154): `from . import shaping_probe` → `from . import han_forms, shaping_probe`.

(b) `GATE_NAMES`: `'arabic-letterforms', 'conjunct-shaping', 'kinsoku',` → `'arabic-letterforms', 'conjunct-shaping', 'kinsoku', 'han-forms',`.

(c) After `kinsoku_report` (before `_execute_verify`), add:

```python
def han_forms_report(doc, lang, reference_dir=None):
    """(lines, status, findings) for gate 20: every embedded face on a page that
    draws CJK text is judged by han_forms.judge_program against the Noto
    reference of lang's convention and the other's, at the face's weight.

    Each face is judged once (per xref) and reported once with the pages it
    is on. status is FAIL if any face draws the other convention, else REVIEW
    if anything could not be judged, else PASS; None when no page draws CJK
    text or lang names a language with no Han convention (the page's CJK is
    then not the target's script — the leak gates own it).
    """
    cjk_pages = [page for page in doc if _has_cjk(page_search_text(page))]
    if not cjk_pages:
        return [], None, []
    convention = han_forms.convention_for_lang(lang)
    if lang and not convention:
        return [], None, []

    def pages_of(nums):
        return 'page ' + ', '.join(str(n) for n in sorted(set(nums)))

    all_pages = [p.number + 1 for p in cjk_pages]
    ok, reason = han_forms.reference_status(convention, reference_dir)
    if not ok:
        name = han_forms.CONVENTIONS[convention][0] if convention else ''
        head = f'REVIEW han-forms{" " + name if name else ""}'
        where = 'lang' if not convention else 'reference'
        return ([f'{head}: {reason} [{pages_of(all_pages)}]'], 'REVIEW',
                [Finding(p, where, reason) for p in all_pages])

    name = han_forms.CONVENTIONS[convention][0]
    fonts = {}       # xref -> (name, program bytes or None)
    judged = {}      # xref -> [HanResult, pages]
    unattested = []  # pages where no face carries the probes
    for page in cjk_pages:
        attested = False
        for entry in page.get_fonts(full=True):
            xref = entry[0]
            if xref not in fonts:
                try:
                    info = doc.extract_font(xref)
                    fonts[xref] = (re.sub(r'^[A-Z]{6}\+', '', info[0] or ''), info[3] or None)
                except Exception:
                    fonts[xref] = (str(entry[3]), None)
            face, program = fonts[xref]
            if not program:
                continue
            if xref not in judged:
                judged[xref] = [han_forms.judge_program(program, convention, reference_dir,
                                                        face=face), []]
            result, pages = judged[xref]
            if result.status == 'SKIP':
                continue
            attested = True
            pages.append(page.number + 1)
        if not attested:
            unattested.append(page.number + 1)

    lines, statuses, findings = [], [], []
    for xref, (result, pages) in sorted(judged.items()):
        if result.status == 'SKIP' or not pages:
            continue
        line = f'{result.line()} [{pages_of(pages)}]'
        if result.status == 'FAIL':
            line += (' — a reader of the language sees the other region\'s shapes; rebuild '
                     'with a face of the language (references/fonts.md)')
        lines.append(line)
        statuses.append(result.status)
        text = result.line() if result.status in ('PASS', 'FAIL') else result.reason
        findings.extend(Finding(p, result.face, text) for p in sorted(set(pages)))
    if unattested:
        reason = (f'no embedded face carries the probes "{han_forms.HAN_CHARS}"; rebuild the '
                  f'subset with prepare_font.py, which adds them, or check a render with a '
                  f'reader of the language')
        lines.append(f'REVIEW han-forms {name}: cannot attest [{pages_of(unattested)}]: {reason}')
        statuses.append('REVIEW')
        findings.extend(Finding(p, convention, f'cannot attest: {reason}') for p in unattested)
    if 'FAIL' in statuses:
        status = 'FAIL'
    elif 'REVIEW' in statuses:
        status = 'REVIEW'
    elif 'PASS' in statuses:
        status = 'PASS'
    else:
        status = None
    return lines, status, findings
```

(d) The record site. Directly after the kinsoku block in `_execute_verify` (the `record('kinsoku', …)` call), add:

```python
    lang = ''
    if translations:
        with open(translations, encoding='utf-8') as f:
            lang = (json.load(f).get('lang') or '').strip()
    if not lang:
        try:
            lang = (jc.language or '').strip()
        except Exception:
            lang = ''
    han_lines, han_status, han_findings = han_forms_report(jc, lang, reference_fonts)
    for line in han_lines:
        print(line)
    if han_status == 'FAIL':
        fail = 1
    if han_status:
        record('han-forms', han_status, findings=han_findings)
```

(e) Signatures. `_execute_verify(…, segments=None, fail_on_review=False)` → `_execute_verify(…, segments=None, fail_on_review=False, reference_fonts=None)`. The same trailing parameter on `run_verify` and `verify`, and both pass `reference_fonts=reference_fonts` through to `_execute_verify`. In `main`, add `reference_fonts=_arg(argv, '--reference-fonts', None),` to the `_execute_verify(...)` call, after `fail_on_review=…`.

(f) The module docstring: find the `19. kinsoku` entry (`grep -n "^19\. kinsoku" pdf_translate/verify.py`; it follows the `18. conjunct shaping` entry) and add after it, same indentation:

```
20. han forms     on a page that draws Japanese or Chinese text, every
                  embedded face is rendered off its font program and
                  compared, pixel for pixel, with the Noto reference of the
                  language's convention (lang: ja -> Japanese; zh, zh-Hans
                  -> Simplified Chinese) and with the other convention's,
                  both instanced at the face's weight. Own reference 0.000
                  and the other >= 0.10 on two of 直 骨 海: PASS; the
                  reverse: FAIL. No lang, no reference for the convention
                  (zh-Hant, ko), a face without the probe glyphs, a family
                  that is not Noto, or no reference directory: REVIEW,
                  never a guess. Silent when no page draws CJK text or lang
                  is not a CJK language. --reference-fonts DIR names the
                  references (default: tests/fonts of a checkout).
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms -v > "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task3-green.log" 2>&1; grep -E "^(test_|Ran |OK|FAILED|ERROR)" "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task3-green.log"`
Expected: 28 tests, `OK`. The 700-weight references are instanced on first run (about 12 s more).

- [ ] **Step 5: Console parity against `main` on the nine non-CJK jobs**

From the repo root, with `S=C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/parity` (it exists from the kinsoku build; refresh `main`'s archive anyway):

```
rm -rf "$S/main"; mkdir -p "$S/main" "$S/jobs"
git archive main pdf-translate/pdf_translate | tar -x -C "$S/main"
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_fixtures.py "$S/jobs"
PYTHONPATH="$S/main/pdf-translate" PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_runner.py "$S/jobs" > "$S/console_main.txt" 2> "$S/verdict_main.txt"
PYTHONPATH="C:/Dev/pdf-translate-skill/pdf-translate" PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_runner.py "$S/jobs" > "$S/console_han.txt" 2> "$S/verdict_han.txt"
head -1 "$S/verdict_main.txt"; head -1 "$S/verdict_han.txt"
diff "$S/console_main.txt" "$S/console_han.txt" && echo CONSOLE IDENTICAL
diff <(grep -v '^# package' "$S/verdict_main.txt") <(grep -v '^# package' "$S/verdict_han.txt") && echo VERDICTS IDENTICAL
```

Expected: the two `# package:` lines name different directories; `CONSOLE IDENTICAL`; `VERDICTS IDENTICAL`. `main` is v51 and this branch is v54 (kinsoku + the stale-report fix + this): the kinsoku gate prints nothing on these nine jobs and the report fix changes no console line, so the diff must still be empty. Keep the output for the evidence doc.

- [ ] **Step 6: The full suite as CI runs it**

From `pdf-translate/`: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report tests.test_cjk tests.test_han_forms > "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-suite-task3.log" 2>&1; grep -E "^(Ran |OK|FAILED|ERROR:|FAIL:)" "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-suite-task3.log"`

Expected: `OK` (possibly `OK (skipped=N)`); 323 + 28 = 351 tests. Two places can go red and are legitimate to touch:
- `tests.test_import_surface.VerdictCompletenessTests` counts printed gate lines against recorded entries on a Japanese job: the new line records exactly one entry, so it stays green. If it goes red, the record site prints and records differently — fix the code, not the test.
- A test in `tests/test_cjk.py` or `tests/test_pipeline.py` that runs `verify` on a CJK page drawn with MuPDF's bundled face and asserts the exact set of REVIEW lines or gate names now sees a `REVIEW han-forms` line too (no `lang`, or another family). Extend that test's expectation to include the new line; never loosen it to "contains".

- [ ] **Step 7: Evidence**

Append to `docs/reviews/2026-09-16-han-forms-gate.md`:

```markdown
## Task 3 — the gate, red then green

Red: before the gate exists, a Japanese job delivered in the Simplified Chinese face verifies
clean (nothing judges the face):

```
<the lines for test_a_japanese_delivery_in_the_chinese_face_fails and
test_the_gate_is_named_after_kinsoku from han-task3-red.log>
```

Green:

```
<the Ran/OK lines and test names from han-task3-green.log>
```

Console parity, nine non-CJK jobs against `main` (v51):

```
<the two # package lines, CONSOLE IDENTICAL, VERDICTS IDENTICAL>
```

Suite as CI runs it, seven modules: `<Ran N tests … OK>`.
```

Replace every `<…>` with the real output.

- [ ] **Step 8: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_han_forms.py docs/reviews/2026-09-16-han-forms-gate.md
git diff --cached --check
git commit -m "feat(pdf-translate): gate 20 han-forms — a Japanese or Chinese page is drawn with a face of its own convention"
```

---

### Task 4: `prepare_font` adds the probes to every CJK subset and refuses the wrong convention early

**Files:**
- Modify: `pdf-translate/pdf_translate/prepare_font.py` (import line 41; signature line 122; the charset block lines 148–155; before the final `print(f'OK: …')` line 244; `main`)
- Modify: `pdf-translate/tests/test_han_forms.py` (append `PrepareFontTests`; the `plain` fixture in `VerifyGateTests.setUpClass`)
- Modify: `docs/reviews/2026-09-16-han-forms-gate.md` (append)

**Interfaces:**
- Consumes: `han_forms.has_cjk`, `han_forms.HAN_CHARS`, `han_forms.convention_for_lang`, `han_forms.reference_status`, `han_forms.judge_file`, `han_forms.CONVENTIONS`.
- Produces: `prepare_font(font_in, trf, font_out, instance=None, sample=None, allow_restricted=False, reference_fonts=None)`; `--reference-fonts DIR` on the CLI. A CJK subset carries 直骨海東. With `lang` naming Japanese or Simplified Chinese and both reference faces present, a subset that draws the other convention makes `prepare_font` print the FAIL line and return 1; PASS prints the line and continues; no `lang`, a convention without a reference, or missing references: nothing printed.

- [ ] **Step 1: Write the failing tests**

Append to `pdf-translate/tests/test_han_forms.py`, above the `if __name__` block:

```python
class PrepareFontTests(unittest.TestCase):
    """prepare_font adds the probes to a CJK subset and judges it early when
    lang names a convention and the references are present."""

    def prepare(self, face, target, lang, instance='wght=400', **kw):
        from tests.test_pipeline import SOURCE_SENTENCE, prepare_font, write_mapping
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        tr, out = os.path.join(tmp, 'translations.json'), os.path.join(tmp, 'subset.ttf')
        write_mapping(tr, {SOURCE_SENTENCE: target}, Path(face), lang=lang)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = prepare_font.prepare_font(str(face), tr, out, instance=instance, **kw)
        return rc, buf.getvalue(), out

    def test_a_cjk_subset_carries_the_probes(self):
        rc, log, out = self.prepare(_face(JP_FACE), PLAIN, None)
        self.assertEqual(rc, 0, log)
        font = pymupdf.Font(fontfile=out)
        for ch in han_forms.HAN_CHARS:
            self.assertTrue(font.has_glyph(ord(ch)), f'U+{ord(ch):04X} missing from the subset')

    def test_a_latin_subset_is_left_alone(self):
        rc, log, out = self.prepare(_face(LATIN_FACE), 'El solicitante debe presentar este formulario hoy.',
                                    'es', instance=None)
        self.assertEqual(rc, 0, log)
        font = pymupdf.Font(fontfile=out)
        self.assertFalse(any(font.has_glyph(ord(ch)) for ch in han_forms.HAN_CHARS))
        self.assertNotIn('han-forms', log)

    def test_a_japanese_job_with_the_chinese_face_is_refused(self):
        rc, log, _ = self.prepare(_face(SC_FACE), TARGET, 'ja')
        self.assertEqual(rc, 1, log)
        self.assertIn('FAIL han-forms Japanese: ', log)
        self.assertIn('draws Simplified Chinese forms', log)
        self.assertIn('Use a Japanese face', log)

    def test_a_japanese_job_with_the_japanese_face_passes(self):
        rc, log, _ = self.prepare(_face(JP_FACE), TARGET, 'ja')
        self.assertEqual(rc, 0, log)
        self.assertIn('PASS han-forms Japanese: ', log)
        self.assertIn('draws Japanese forms', log)

    def test_without_lang_or_references_prepare_font_stays_quiet(self):
        rc, log, _ = self.prepare(_face(JP_FACE), TARGET, None)
        self.assertEqual(rc, 0, log)
        self.assertNotIn('han-forms', log)
        with tempfile.TemporaryDirectory() as empty:
            rc, log, _ = self.prepare(_face(JP_FACE), TARGET, 'ja', reference_fonts=empty)
        self.assertEqual(rc, 0, log)
        self.assertNotIn('han-forms', log)
        rc, log, _ = self.prepare(_face(JP_FACE), TARGET, 'zh-Hant')
        self.assertEqual(rc, 0, log)
        self.assertNotIn('han-forms', log)

    def test_the_cli_takes_reference_fonts(self):
        from tests.test_pipeline import SOURCE_SENTENCE, prepare_font, write_mapping
        with tempfile.TemporaryDirectory() as tmp:
            tr, out = os.path.join(tmp, 'translations.json'), os.path.join(tmp, 'subset.ttf')
            write_mapping(tr, {SOURCE_SENTENCE: TARGET}, _face(SC_FACE), lang='ja')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.main([str(SC_FACE), tr, out, '--instance', 'wght=400',
                                        '--reference-fonts', tmp])
            self.assertEqual(rc, 0, buf.getvalue())      # no references there: nothing judged
            self.assertNotIn('han-forms', buf.getvalue())
            with redirect_stdout(buf):
                rc = prepare_font.main([str(SC_FACE), tr, out, '--instance', 'wght=400',
                                        '--reference-fonts', str(FONTS)])
            self.assertEqual(rc, 1, buf.getvalue())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms.PrepareFontTests -v > "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task4-red.log" 2>&1; grep -E "^(test_|Ran |OK|FAILED|ERROR)" "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task4-red.log"`
Expected: `test_a_cjk_subset_carries_the_probes` fails on `U+76F4 missing from the subset` (the brief §2 "Not drawn", now a test); `test_a_japanese_job_with_the_chinese_face_is_refused` fails with `1 != 0`; `test_a_japanese_job_with_the_japanese_face_passes` fails on the missing PASS line; the `reference_fonts` tests error with `TypeError: … unexpected keyword argument`; `test_a_latin_subset_is_left_alone` and the quiet test pass already (they pin what must not change) — that is expected for those two only.

- [ ] **Step 3: Write the change**

In `pdf-translate/pdf_translate/prepare_font.py`:

(a) Line 41: `from . import shaping_probe` → `from . import han_forms, shaping_probe`.

(b) The signature: `allow_restricted=False):` → `allow_restricted=False, reference_fonts=None):`.

(c) The charset block. After `chars = job_charset(conf)` and before the gate-18 loop, add `cjk_job = han_forms.has_cjk(''.join(chars))`; after the gate-18 loop (`chars.update(probe.text)`), add:

```python
    if cjk_job:
        # Gate 20 renders these four off the embedded program; a Japanese or
        # Chinese subset without them is REVIEW "cannot attest" (measured: a
        # subset built from a target with no probe character lacks 直).
        chars.update(han_forms.HAN_CHARS)
```

(d) Before the final `print(f'OK: {font_out} …')`, after the gate-18 `if job_scripts:` block, add:

```python
    if cjk_job:
        # Ask the subset now what verify will ask the embedded program later
        # (gate 20), so a job set with the wrong region's face stops here.
        convention = han_forms.convention_for_lang(conf.get('lang'))
        if convention and han_forms.reference_status(convention, reference_fonts)[0]:
            result = han_forms.judge_file(font_out, convention, reference_fonts)
            print(result.line())
            if result.status == 'FAIL':
                want = han_forms.CONVENTIONS[convention][0]
                print(f'FAIL: {font_out} draws the other region\'s Han forms; a {want} reader '
                      f'sees the wrong shapes for {han_forms.HAN_PROBES}. Use a {want} face '
                      f'(references/fonts.md).')
                return 1
```

(e) `main`: after `sample = …`, add

```python
    reference_fonts = (argv[argv.index('--reference-fonts') + 1]
                       if '--reference-fonts' in argv else None)
```

and pass `reference_fonts=reference_fonts` to `prepare_font(...)`.

(f) The module docstring (top of the file) gains one sentence where it describes what the subset carries: "A Japanese or Chinese subset also carries 直 骨 海 東, which verify's han-forms gate renders off the embedded program; with `lang` and the reference faces present (`--reference-fonts DIR`, default `tests/fonts/`), the subset is judged here first and a face of the wrong convention is refused."

- [ ] **Step 4: The `plain` fixture keeps lacking the probes**

`VerifyGateTests.test_a_subset_without_the_probes_is_review_cannot_attest` built its delivery from a target with no probe character; `prepare_font` now adds them anyway. In `VerifyGateTests.setUpClass`, replace

```python
        cls.plain = job('plain', face=JP_FACE, target=PLAIN, lang='ja')
```

with

```python
        # A subset built before this version, or by another tool: no probe glyphs.
        with mock.patch.object(han_forms, 'HAN_CHARS', ''):
            cls.plain = job('plain', face=JP_FACE, target=PLAIN, lang='ja')
```

(`prepare_font` reads `han_forms.HAN_CHARS` at call time, so the patch holds; `build_delivery` passes no `prepare_lang`, so the early judge stays quiet.)

- [ ] **Step 5: Run the tests to verify they pass**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_han_forms -v > "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task4-green.log" 2>&1; grep -E "^(test_|Ran |OK|FAILED|ERROR)" "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/han-task4-green.log"`
Expected: 34 tests, `OK`.

Then the seven-module suite exactly as in Task 3 Step 6 (log to `han-suite-task4.log`). Expected `OK`, 357 tests. `tests/test_pipeline.py` and `tests/test_cjk.py` build CJK subsets through `prepare_font` with other faces; a test that asserts the `OK: … N chars` count on a CJK job now counts four more — extend that expectation.

- [ ] **Step 6: Evidence**

Append to `docs/reviews/2026-09-16-han-forms-gate.md`:

```markdown
## Task 4 — prepare_font, red then green

Red: a subset built from 申請書を提出 lacks 直 (the brief's "not drawn"), and a Japanese job set
with the Simplified Chinese face is prepared without complaint:

```
<the lines for test_a_cjk_subset_carries_the_probes and
test_a_japanese_job_with_the_chinese_face_is_refused from han-task4-red.log>
```

Green:

```
<the Ran/OK lines and test names from han-task4-green.log>
```

Suite, seven modules: `<Ran N tests … OK>`.
```

- [ ] **Step 7: Commit**

```bash
git add pdf-translate/pdf_translate/prepare_font.py pdf-translate/tests/test_han_forms.py docs/reviews/2026-09-16-han-forms-gate.md
git diff --cached --check
git commit -m "feat(pdf-translate): prepare_font adds 直骨海東 to every CJK subset and refuses a face of the wrong convention"
```

---

### Task 5: docs, version 54, CI

**Files:**
- Modify: `.github/workflows/tests.yml:49` (suite line)
- Modify: `pdf-translate/SKILL.md` (`version: "53"` → `"54"`; a bullet after the Kinsoku bullet in the gate list, ~line 447)
- Modify: `.claude-plugin/plugin.json` (`"53.0.0"` → `"54.0.0"`), `pdf-translate/pyproject.toml` (`version = "53.0.0"` → `"54.0.0"`), `pdf-translate/pdf_translate/__init__.py` (`__version__ = '53'` → `'54'`; the docstring's import example gains nothing — `han_forms` is reached as a module), `pdf-translate/tests/test_verify_report.py:648` (`'53'` → `'54'`)
- Modify: `pdf-translate/README.md:107` (`nineteen structural gates` → `twenty structural gates`)
- Modify: `pdf-translate/references/gates.md` (the "Always on" table after the kinsoku row; the name list in "As a library"; the consumer paragraph; the `where`/`text` table; the Flags paragraph)
- Modify: `pdf-translate/references/fonts.md` (the CJK section, one paragraph)
- Modify: `docs/DECISIONS.md` (one row, appended to the table)
- Modify: `docs/reviews/2026-09-16-han-forms-gate.md` (the docs section; the Rule 1 heading)

- [ ] **Step 1: Version 54 in five places and the lockstep test**

Make the five edits listed above, then run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_verify_report.VersionLockstepTests -v 2>&1 | grep -E "^(Ran |OK|FAILED)"`
Expected: `OK`. (Edit the literal to `'54'` first and watch it fail against the four sources still at 53, then bump them — that is this task's red.)

- [ ] **Step 2: The suite line**

`.github/workflows/tests.yml` line 49: append ` tests.test_han_forms` after `tests.test_cjk`. The font cache key stays `noto-fonts-v3`: no new face is fetched.

- [ ] **Step 3: SKILL.md**

After the Kinsoku bullet (the one beginning `- **Kinsoku** (always on):`), add:

```markdown
- **Han forms** (always on): on a page that draws Japanese or Chinese text,
  every embedded face is rendered off its own font program and compared with
  the Noto reference of the language's convention (`lang` ja → Japanese;
  zh, zh-Hans → Simplified Chinese) and with the other's, at the face's
  weight: a face that draws the other region's forms of 直 骨 海 FAILs. No
  `lang`, a face without the probe glyphs (build faces with `prepare_font`,
  which adds them), a family that is not Noto, zh-Hant or ko (no reference
  measured yet), or no reference faces (`--reference-fonts DIR`; default
  `tests/fonts/`) is REVIEW, never a guess. `prepare_font` makes the same
  check at build time when `lang` and the references are present, and
  refuses a face of the wrong convention.
```

- [ ] **Step 4: gates.md**

(a) "Always on" table, after the kinsoku row:

```markdown
| han-forms | on a page that draws CJK text, every embedded face with a font program is rendered off that program and compared pixel for pixel with the Noto reference of `lang`'s convention (ja → Noto Sans JP; zh, zh-Hans, zh-CN, zh-SG → Noto Sans SC) and with the other convention's, both instanced at the face's OS/2 weight. PASS: ≤ 0.02 against its own reference and ≥ 0.10 against the other on at least two of 直 骨 海; FAIL: the reverse — the face draws the other region's forms. REVIEW, never a guess: no `lang` (mapping or `/Lang`); zh-Hant, ko (no reference measured); a face without the probe glyphs (cannot attest; `prepare_font` adds them); a face that differs from both references on 東, which is the same in both conventions (not a Noto family — no nearer-reference guess); reference faces not found (`--reference-fonts DIR`, default `tests/fonts/`); an inconclusive spread. Silent when `lang` is not a CJK language: the page's CJK is then a leak, and those gates own it |
```

(b) The name list in "As a library": `arabic-letterforms, conjunct-shaping, kinsoku, leak-scan,` → `arabic-letterforms, conjunct-shaping, kinsoku, han-forms, leak-scan,`.

(c) The consumer paragraph: replace `A consumer removes three REVIEWs on its own: always pass \`lang\` in the mapping (\`metadata-lang\`), build faces with \`prepare_font\`, which adds the probe glyphs gate 18 needs (\`conjunct-shaping\` "cannot attest"), and never split a target by hand across source lines — declare a merge (\`kinsoku\`).` with:

```
A consumer removes four REVIEWs on its own: always pass `lang` in the mapping
(`metadata-lang`, and `han-forms` "no lang"), build faces with `prepare_font`,
which adds the probe glyphs gates 18 and 20 need (`conjunct-shaping` and
`han-forms` "cannot attest"), set Japanese and Chinese in Noto Sans JP / SC and
ship the two reference faces (`reference_fonts=DIR`; `han-forms` "no reference"),
and never split a target by hand across source lines — declare a merge
(`kinsoku`).
```

(d) The `where`/`text` table, after the kinsoku row:

```markdown
| han-forms | the face's PostScript name (subset tag stripped); `lang`, `reference` or the convention code (`JP`, `SC`) when the face could not be judged | the PASS/FAIL line with the ratios, or the reason |
```

(e) Flags: `\`--report verify_report.json\`, \`--fail-on-review\`.` → `` `--report verify_report.json`, `--fail-on-review`, `--reference-fonts DIR` (the Noto Sans JP / SC variable faces gate 20 compares against; default `tests/fonts/` of a checkout — an installed package has none, so a service passes its own). ``

- [ ] **Step 5: fonts.md**

In the CJK section (heading `## CJK (Japanese, Chinese Simplified/Traditional, Korean)`), add at its end:

```markdown
`verify`'s `han-forms` gate (20) compares the delivered face with the Noto
Sans JP and SC references at the same weight, exactly. Use the same builds
for the job's face and for the references — the google/fonts variable TTFs
that `tools/fetch_test_fonts.py` fetches — or a legitimately Japanese face
can read above the 0.02 match bound and come back REVIEW instead of PASS. A
service ships the two reference faces beside its job faces and passes their
directory (`--reference-fonts DIR` / `reference_fonts=`).
```

- [ ] **Step 6: README.md**

Line 107: `verify.py                     nineteen structural gates` → `verify.py                     twenty structural gates`.

- [ ] **Step 7: DECISIONS.md**

Append this row to the "Open ledger" table, after the stale-report row (before the closing note):

```markdown
| 2026-09-16 | Gate 20 `han-forms`: on a page that draws CJK text, every embedded face is rendered off its own font program and compared pixel for pixel with the Noto reference of the language's convention (`lang` ja → Noto Sans JP; zh, zh-Hans, zh-CN, zh-SG → Noto Sans SC) and with the other convention's, both instanced at the face's OS/2 weight; PASS when the face reads ≤ 0.02 against its own reference and ≥ 0.10 against the other on at least two of 直 骨 海, FAIL on the reverse, REVIEW otherwise — no `lang`, a convention without a measured reference (zh-Hant, ko), a face without the probe glyphs, a face that differs from both references on 東 (not a Noto family), no reference directory, or an inconclusive spread. Never the nearer reference. `prepare_font` adds 直骨海東 to every CJK subset and, with `lang` and the references present, refuses a face of the other convention. References default to `tests/fonts/`, overridable with `--reference-fonts DIR` / `reference_fonts=`; instanced copies are cached beside them. Silent when `lang` is not a CJK language. Version 53 → 54. | Measured (`dev/probes/han_forms_probe.py`, `docs/BRIEF-han-forms-gate.md`, PyMuPDF 1.28.2, the google/fonts Noto Sans JP / SC variable faces): own face 0.000 on every probe; JP vs SC at equal weight 直 0.454, 骨 0.171, 海 0.212, 東 0.000; weight alone (JP 400 vs 100) 0.51–0.55, as large as region, so references must be instanced at the delivered weight; a delivery's embedded subset re-rendered reads 0.000 against its own reference, exactly as gate 18 re-probes a face, so the face is judged and not the page; Yu Gothic and Microsoft YaHei read 0.56–0.82 against both references (no reference of their family); a subset built from a target with no probe character lacks 直. The product ships both reference faces (its ruling R4) so PASS is reachable in production. Tests reproduce the table within 0.02 (`tests/test_han_forms.py`); console output of non-CJK jobs is byte-identical (parity runner, nine jobs). | A Noto release whose JP and SC builds converge on a probe (the table test would show it); a Noto delivery that reads above 0.02 against its own reference at its weight (a build mismatch between the job's face and the reference — that would argue for shipping the references with the faces, not for loosening the bound); or a target language whose convention needs a third reference (zh-Hant, ko), which adds a face to the fetcher and a measured row, not a rule change. |
```

- [ ] **Step 8: The evidence doc's docs section and the Rule 1 heading**

Append to `docs/reviews/2026-09-16-han-forms-gate.md`:

```markdown
## Docs and version

`SKILL.md` gate bullet; `references/gates.md` row, name list, consumer paragraph, `where`/`text`
row, flag; `references/fonts.md` on matching builds; `README.md` twenty gates; `docs/DECISIONS.md`
row with the measured table; version 53 → 54 in SKILL.md, plugin.json, pyproject.toml,
`__version__` and the lockstep literal; `tests.test_han_forms` on the CI suite line.

## Rule 1 verification

Appended by the independent verifier's pass, on another model, after the whole-branch review —
not by the implementer of any task. Until that section is here, this gate is not verified.
```

- [ ] **Step 9: The suite once more, then commit**

The seven-module suite as in Task 3 Step 6 (log to `han-suite-task5.log`): expected `OK`, 357.

```bash
git add .github/workflows/tests.yml pdf-translate/SKILL.md .claude-plugin/plugin.json pdf-translate/pyproject.toml pdf-translate/pdf_translate/__init__.py pdf-translate/tests/test_verify_report.py pdf-translate/README.md pdf-translate/references/gates.md pdf-translate/references/fonts.md docs/DECISIONS.md docs/reviews/2026-09-16-han-forms-gate.md
git diff --cached --check
git commit -m "docs(pdf-translate): gate 20 han-forms in SKILL.md, gates.md, fonts.md and README; DECISIONS row; version 54"
```

---

## After the tasks

1. **Final whole-branch review** (superpowers:subagent-driven-development, most capable model): `scripts/review-package $(git merge-base fix/stale-verify-report HEAD) HEAD`. Minor findings recorded in the ledger go to this reviewer for triage.
2. **Rule 1 verification** — below. Its report is appended to the evidence doc; a "not verified" verdict is a fix wave, not a note.
3. The controller reports to the operator: the branch, the suite line, the parity result, the verifier's verdict, the evidence doc. Push and PR are the operator's.

## Rule 1 verification

Dispatched by the controller on Opus or Fable, **never** on the model that implemented the tasks, after the final review is clean. The verifier does not start from the implementation; it starts from the runs. It:

1. Runs `tests.test_han_forms` and the seven-module suite, and pastes the `Ran … OK` lines.
2. Writes the script below to its scratchpad (not the repo) and runs it from `pdf-translate/` with `PYTHONUTF8=1` and the venv. It builds a Japanese job with the Japanese face and one with the Simplified Chinese face, verifies both, prints the `han-forms` lines and exit codes, and renders 直 from each delivered page at 600 dpi to a PNG. Expected: `exit 0` with `PASS han-forms Japanese: … draws Japanese forms` for the JP job; `exit 1` with `FAIL han-forms Japanese: … draws Simplified Chinese forms` for the SC job.
3. **Looks at both PNGs** (the Read tool shows images) and says, in its own words, which form each shows. The tell: in the Japanese form of 直 the lowest stroke is a vertical that turns right into a hook (乚) under the 目; in the Simplified Chinese form the lowest stroke is a flat horizontal line under a closed 目-like box. The verdict must agree with the gate's lines; if the eye and the gate disagree, the gate is wrong, whatever the ratios say.
4. Re-runs the parity commands of Task 3 Step 5 and pastes the two `IDENTICAL` lines.
5. Reads the evidence doc's red/green claims against its own runs.
6. Appends its section (`## Rule 1 verification`, replacing the placeholder sentence) with every command and output, the two PNG descriptions, and one verdict: **verified** or **not verified** with the items.

```python
# verifier_han_forms.py — from pdf-translate/, PYTHONUTF8=1, the venv
import io, sys, tempfile
from contextlib import redirect_stdout
from pathlib import Path
import pymupdf
sys.path.insert(0, '.')
from tests.test_han_forms import JP_FACE, SC_FACE, TARGET, build_delivery
from pdf_translate.verify import verify

work = Path(tempfile.mkdtemp(prefix='han-forms-verify-'))
for name, face in (('jp', JP_FACE), ('sc', SC_FACE)):
    d = work / name
    d.mkdir()
    src, out, tr, subset = build_delivery(str(d), face=face, target=TARGET, lang='ja')
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = verify(src, out, translations=tr, min_ink=0.1)
    print(f'== {name} face, lang ja: exit {rc}')
    print('\n'.join(l for l in buf.getvalue().splitlines() if 'han-forms' in l))
    doc = pymupdf.open(out)
    page = doc[0]
    for block in page.get_text('rawdict')['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                for c in span['chars']:
                    if c['c'] == '\u76f4':
                        pix = page.get_pixmap(matrix=pymupdf.Matrix(600 / 72, 600 / 72),
                                              clip=pymupdf.Rect(c['bbox']))
                        png = work / f'{name}-U76F4-600dpi.png'
                        pix.save(str(png))
                        print('render:', png)
    doc.close()
print('work:', work)
```

## Self-review

- Spec coverage (brief §4 design and §4 acceptance): the measurement core and the table within 0.02 → Task 1; the judge with PASS/FAIL/REVIEW and the never-the-nearer rule → Task 2; the gate on deliveries built through the pipeline (JP PASS, SC FAIL, no probes REVIEW, no `lang` REVIEW, another family REVIEW, wght 700 PASS at its own weight, `--reference-fonts`) → Tasks 2–3; console parity → Task 3 Step 5; `FindingsInvariantTests` → the suite in Task 3 Step 6; `prepare_font` probes and early refusal → Task 4; version 54, gates.md, SKILL.md, DECISIONS, evidence → Task 5; Rule 1 → the section above. The brief's "delivery in Yu Gothic → REVIEW (skipped off Windows)" is covered platform-independently by the bundled Droid face in Task 2, which is the same case (a family with no reference).
- Placeholders: the evidence doc's `<…>` markers are instructions to paste real output and each step says so; no code step lacks its code.
- Type consistency: `HanResult.ratios` is a tuple of `(char, own, other)` in Tasks 2 and 3; `judge_program(program, convention, reference_dir=None, face='')` is called with those names in Tasks 3 and 4; `reference_status` returns `(bool, str)` everywhere; `build_delivery` returns `(orig, out, translations, subset)` in Task 3 and the verifier script; `Finding.where` values are the face name, `lang`, `reference`, or the convention code, as the constraints say.

## Amendments after the whole-branch review

Task sections above are unchanged; the fix wave (evidence:
`docs/reviews/2026-09-16-han-forms-gate.md` §"Fix wave after the whole-branch review") amended
this design as follows.

- `han_forms_report`'s signature changed from `(doc, lang, reference_dir=None)` to
  `(doc, mapping_lang, output_lang, reference_dir=None)`; the record site in `_execute_verify`
  passes the mapping's `lang` and the output's `/Lang` separately instead of folding them into one.
- Attribution rule: a face is judged for a page only if it drew CJK glyphs on that page, matched by
  name (`han_forms.font_key`, `verify._cjk_drawing_fonts`) to the page's spans; an embedded face
  that drew none neither fails the page nor attests it (`han_forms.py` Task 2/3's `judge_program`
  enumeration judged every embedded face regardless of what it drew, which is what let a leftover
  or bystander face flip the verdict).
- `/Lang` rule: a non-CJK `/Lang` with no mapping `lang` is now REVIEW ("the output declares /Lang
  … while the page draws CJK text"), not silence — the original design (`han_forms_report(doc,
  lang, reference_dir=None)`, Task 3) treated any non-CJK `lang` the same whether it came from the
  mapping or a stale `/Lang` carried over from the source.
- Wording: the 東 family-REVIEW reason (`judge_program`) gained "— not a Noto face, or not the same
  build or weight as the references (references/fonts.md)"; the "cannot attest" reason gained
  "that drew the page's CJK text" to match the new attribution rule.
- New tests: `tests/test_han_forms.py` `AttributionTests` (4, `han_forms.font_key` +
  `verify_mod.han_forms_report`'s new signature), `VerifyGateTests.test_a_chinese_source_translated_to_japanese_passes`
  (a real zh → ja delivery, `build_cjk_source`/`build_delivery(source=...)`),
  `VerifyGateTests.test_a_stale_non_cjk_output_lang_is_review_not_silence`, and
  `PrepareFontTests.test_another_family_is_reviewed_not_refused` — 34 + 7 = 41 in the module,
  357 + 7 = 364 in the seven-module suite.
