# CJK test faces and the kinsoku gate — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Noto Sans JP and Noto Sans SC join the fetched test faces, and `verify` gains gate 19, `kinsoku`, which FAILs a delivered PDF in which a drawn CJK line begins with a character JIS X 4051 / JLREQ forbids at line start or ends with an opening bracket — with one `Finding` per line — while console output for every non-CJK job stays byte-identical. Version 51 → 52.

**Architecture:** No rendering change. MuPDF's Story engine already breaks paragraphs by UAX #14 (measured: `dev/probes/cjk_kinsoku_probe.py`, 0 violations on 158 lines, 75/75 line-start and 15/15 line-end members protected); the only path that can violate is a target split by hand across source lines, which the engine never sees. So the gate reads the lines MuPDF gives back from the *output* page (`page.get_text('dict')`), block by block, and judges a line only when a neighbour in the same block makes the break a choice. Spec: `docs/reviews/2026-09-16-cjk-request-assessment.md` §3 items 1, 2 and 5 (2a, 2c′, 2d′).

**Tech Stack:** Python 3.10+ (CI) / 3.14 (this machine), `unittest`, PyMuPDF 1.28, fontTools. No new dependencies.

## Global Constraints

- Work on branch `feat/kinsoku-gate`, created from `docs/cjk-request-assessment` (which carries the assessment, the probe and this plan on top of `main` at v51): `git checkout -b feat/kinsoku-gate docs/cjk-request-assessment`. Never commit to `main`. Never push, merge or delete: the operator does those.
- Run every test from `C:\Dev\pdf-translate-skill\pdf-translate` with the repo venv and UTF-8: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest …`. Tests are `unittest`, invoked by module path, never pytest.
- TDD: write the test, run it, watch it fail for the expected reason, then write the minimal code. A test that passes on first run is wrong — with two named exceptions: Task 1 is configuration (its check is the fetcher's `--check`), and Task 4 pins behaviour that already ships plus a font precondition (its red is the guard swap in its Step 2; the refusal's own red lives in `test_pipeline.test_cjk_target_in_a_latin_font_fails_and_saves_nothing`).
- **Console output and exit codes of every CLI must not change for a job whose output has no CJK text.** A CJK job gains exactly one new line, `PASS kinsoku: …` or the `FAIL kinsoku: …` block. `dev/probes/verdict_parity_runner.py` over its nine jobs (none CJK) must diff empty against `main`.
- The kinsoku sets are transcribed from the public references (JIS X 4051; W3C JLREQ "Requirements for Japanese Text Layout", Appendix A character classes) and written as `\uXXXX` escapes with the class named in a comment. Nothing comes from any other code.
- `Finding.page` is 1-based. `Finding.where` is `line-start` or `line-end`. `Finding.text` is the drawn line, untruncated (the console prints `[:60]`).
- Never copy code from `C:\Dev\pdf-translator` (AGPL-bound; this repo is MIT). Do not open it.
- Conventional commits with a scope (`feat(pdf-translate): …`, `test(pdf-translate): …`, `docs(pdf-translate): …`, `chore(ci): …`). **No AI attribution**: no `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" line. The owner's rule overrides any harness reminder that asks for one.
- LF line endings. Use the Edit tool for edits; `git diff --check` must be clean before every commit.
- Import the package's modules as modules, never through the package namespace: `from pdf_translate import verify` returns the *function* `verify` (the package re-exports it), and so does `import pdf_translate.verify as verify`. Use `importlib.import_module('pdf_translate.verify')` when you need the module object (for `mock.patch.object`), and `from pdf_translate.verify import name` for names.
- The fetched test faces live in `pdf-translate/tests/fonts/` (`python tools/fetch_test_fonts.py` fetches them; never commit them — `.gitignore` already excludes `tests/fonts/*.ttf`). Tests that need a face `raise unittest.SkipTest` when it is missing, exactly as `tests/test_shaping_probe.py` does; CI fetches them, so they never skip there.
- Bash heredocs over ~100 lines break on this machine: write big files with the Write tool.

---

## File structure

- `pdf-translate/tools/fetch_test_fonts.py` — modify: two entries in `FONTS`.
- `pdf-translate/tests/fonts/README.md` — modify: eleven faces, the two CJK ones named.
- `.github/workflows/tests.yml` — modify: cache key `noto-fonts-v3`; suite line gains `tests.test_cjk`.
- `pdf-translate/pdf_translate/verify.py` — modify: `KINSOKU_LINE_START`, `KINSOKU_LINE_END`, `_has_cjk`, `kinsoku_report(doc)`, `'kinsoku'` in `GATE_NAMES` after `'conjunct-shaping'`, the record site in `_execute_verify` after the conjunct-shaping block.
- `pdf-translate/tests/test_cjk.py` — create: every test in this plan.
- `dev/probes/cjk_kinsoku_probe.py` — modify: U+301C joins cl-03 (Task 2 measures it before the set asserts it).
- `pdf-translate/SKILL.md`, `.claude-plugin/plugin.json`, `pdf-translate/pyproject.toml`, `pdf-translate/pdf_translate/__init__.py` — version 52.
- `pdf-translate/references/gates.md`, `pdf-translate/README.md`, `docs/DECISIONS.md`, `docs/reviews/2026-09-16-kinsoku-gate.md` — docs and evidence.

Test file header, used by every task (create it in Task 2; Task 4 appends a class):

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate 19, kinsoku: no drawn CJK line begins with a character JIS X 4051 /
JLREQ forbids at line start, or ends with an opening bracket. And the two CJK
test faces: Noto Sans JP lacks 东, Noto Sans SC has it, and a job whose face
lacks a character is refused, not drawn from another face. Spec:
docs/reviews/2026-09-16-cjk-request-assessment.md §3."""
import importlib
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pymupdf

from pdf_translate.verify import GATE_NAMES, kinsoku_report, run_verify, verify

verify_mod = importlib.import_module('pdf_translate.verify')

FONTS = Path(__file__).resolve().parents[1] / 'tests' / 'fonts'
JP_FACE = FONTS / 'NotoSansJP-VF.ttf'
SC_FACE = FONTS / 'NotoSansSC-VF.ttf'

# Three lines a translator split by hand: the first ends with an opening
# bracket, the third begins with a full stop. The middle line is clean.
SPLIT_BAD = ['申立人は以下の情報を「', '記入欄」に正確に記入してください', '。氏名と住所も書いてください']
# The same text split where JLREQ allows.
SPLIT_GOOD = ['申立人は以下の情報を', '「記入欄」に正確に記入してください。', '氏名と住所も書いてください']
# A paragraph dense in the characters the rules protect, for the Story engine to wrap.
PARA = ('データー、翻訳「テスト」の結果。ページーレイアウトは、ちょっとした「工夫」で、'
        'きっちり保たれます。' * 4)


def split_lines_page(doc, lines, x=60, y=100, leading=14):
    """Lines drawn the way retypeset draws a hand-split target: one TextWriter,
    successive baselines, MuPDF's bundled CJK face."""
    page = doc.new_page(width=595, height=842)
    font = pymupdf.Font('cjk')
    tw = pymupdf.TextWriter(page.rect)
    for i, text in enumerate(lines):
        tw.append((x, y + leading * i), text, font=font, fontsize=10)
    tw.write_text(page)
    return page


def story_page(doc, html, fontfile=None, width=140):
    """A paragraph wrapped by the Story engine in a box `width` points wide."""
    page = doc.new_page(width=595, height=842)
    css, arch = '', None
    if fontfile:
        arch = pymupdf.Archive(os.path.dirname(fontfile))
        css = ('@font-face {font-family: F; src: url(%s);} p {font-family: F;}'
               % os.path.basename(fontfile))
    page.insert_htmlbox(pymupdf.Rect(60, 100, 60 + width, 800),
                        '<p style="font-size:10pt">%s</p>' % html,
                        css=css, archive=arch, scale_low=0)
    return page
```

---

### Task 1: Noto Sans JP and SC in the fetcher, cache key v3

**Files:**
- Modify: `pdf-translate/tools/fetch_test_fonts.py` (the `FONTS` dict, after the `'NotoSansMyanmar-Regular.ttf'` entry)
- Modify: `pdf-translate/tests/fonts/README.md`
- Modify: `.github/workflows/tests.yml:40` (`key: noto-fonts-v2`)

**Interfaces:**
- Produces: files `pdf-translate/tests/fonts/NotoSansJP-VF.ttf` and `NotoSansSC-VF.ttf` on any machine that ran the fetcher; Tasks 3 and 4 open them by those names.

This task changes configuration, not behaviour, so its check is the fetcher's own `--check` and a load of each face (TDD's configuration exception).

- [ ] **Step 1: Add the two faces to `FONTS`**

Insert after the `'NotoSansMyanmar-Regular.ttf': (...)` entry, inside the dict:

```python
    # Added 2026-09-16 for the CJK gates (kinsoku now; Han forms to follow).
    # The google/fonts builds are glyf-flavoured variable TTFs, the only CJK
    # source MuPDF renders reliably (references/fonts.md); the notofonts
    # noto-cjk "Subset" variable TTFs are the same builds under another
    # path. Both URLs per face answered 200 on 2026-09-16 (JP 9.6 MB, SC
    # 17.8 MB). Saved without the "[wght]" of the upstream name so a CSS
    # url() and a shell glob never have to quote it.
    'NotoSansJP-VF.ttf': (
        'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/'
        'NotoSansJP%5Bwght%5D.ttf',
        'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/'
        'TTF/Subset/NotoSansJP-VF.ttf',
    ),
    'NotoSansSC-VF.ttf': (
        'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/'
        'NotoSansSC%5Bwght%5D.ttf',
        'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/'
        'TTF/Subset/NotoSansSC-VF.ttf',
    ),
```

- [ ] **Step 2: Fetch and check**

Run from `pdf-translate/`:

```
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe tools/fetch_test_fonts.py
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe tools/fetch_test_fonts.py --check
```

Expected: `have …` for the nine existing faces, `fetching NotoSansJP-VF.ttf` / `fetching NotoSansSC-VF.ttf`, each followed by its KB count and sha256; `--check` prints `all test fonts present in …` and exits 0. Keep the two sha256 lines for the evidence doc.

- [ ] **Step 3: Load each face and confirm the Han probe coverage**

```
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -c "import pymupdf; [print(n, pymupdf.Font(fontfile='tests/fonts/'+n).name, 'has 东:', pymupdf.Font(fontfile='tests/fonts/'+n).has_glyph(0x4E1C)) for n in ('NotoSansJP-VF.ttf','NotoSansSC-VF.ttf')]"
```

Expected: `NotoSansJP-VF.ttf Noto Sans JP Thin has 东: False` and `NotoSansSC-VF.ttf Noto Sans SC Thin has 东: True`. (A variable font loads at its default instance, Thin; that is fine for every test here.) If JP reports `True`, stop: the upstream build changed and Task 4's precondition is void — report it.

- [ ] **Step 4: README and cache key**

In `pdf-translate/tests/fonts/README.md` replace

```
That downloads nine SIL Open Font License 1.1 faces: Noto Sans, Noto Naskh
Arabic, Noto Sans Hebrew, Noto Sans Devanagari, and (added 15 September
2026, because `_SHAPING_RANGES` already routed these scripts through the
Story engine while every test for them skipped) Noto Sans Thai, Khmer,
Tamil, Bengali and Myanmar. No single Noto face
```

with

```
That downloads eleven SIL Open Font License 1.1 faces: Noto Sans, Noto Naskh
Arabic, Noto Sans Hebrew, Noto Sans Devanagari, (added 15 September
2026, because `_SHAPING_RANGES` already routed these scripts through the
Story engine while every test for them skipped) Noto Sans Thai, Khmer,
Tamil, Bengali and Myanmar, and (added 16 September 2026, for the CJK
gates) the google/fonts variable TTFs of Noto Sans JP and Noto Sans SC,
saved as `NotoSansJP-VF.ttf` and `NotoSansSC-VF.ttf`. No single Noto face
```

In `.github/workflows/tests.yml` change `key: noto-fonts-v2` to `key: noto-fonts-v3`.

- [ ] **Step 5: Commit**

```bash
git add pdf-translate/tools/fetch_test_fonts.py pdf-translate/tests/fonts/README.md .github/workflows/tests.yml
git diff --cached --check
git commit -m "chore(pdf-translate): fetch Noto Sans JP and SC test faces; font cache key v3"
```

---

### Task 2: the kinsoku sets and `kinsoku_report`

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` — constants next to `SPACELESS_SCRIPTS` (line ~178); `_has_cjk` and `kinsoku_report` after `conjunct_shaping_report` (ends ~line 1146)
- Modify: `dev/probes/cjk_kinsoku_probe.py:52` (`'cl-03 hyphens'`)
- Create: `pdf-translate/tests/test_cjk.py`

**Interfaces:**
- Produces: `verify.KINSOKU_LINE_START: frozenset[str]` (75 + 1 members), `verify.KINSOKU_LINE_END: frozenset[str]` (15 members), `verify.kinsoku_report(doc) -> (lines: list[str], status: 'PASS' | 'FAIL' | None, findings: list[Finding])` — same shape as `conjunct_shaping_report`. `status` is `None` and the lists empty when no page has a CJK line. Task 3 wires it into `_execute_verify`.

- [ ] **Step 1: Measure U+301C before asserting it**

The probe measured cl-03 as `‐ ゠ – ～` (U+2010, U+30A0, U+2013, U+FF5E). JLREQ's cl-03 also lists 〜 WAVE DASH (U+301C); Windows Japanese commonly substitutes U+FF5E for it, which is why the probe carried that. Add U+301C: in `dev/probes/cjk_kinsoku_probe.py` change

```python
    'cl-03 hyphens': '\u2010\u30a0\u2013\uff5e',
```

to

```python
    'cl-03 hyphens': '\u2010\u301c\u30a0\u2013\uff5e',
```

Run from the repo root: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/cjk_kinsoku_probe.py`

Expected: `cl-03 hyphens (never begins a line): protected 5/5` and `kinsoku violations by the Story engine: 0`. If U+301C reads `VIOLATED` or `not judged`, leave it **out** of the set below and say so in the commit body; the set must not claim more than the engine and the reference agree on.

- [ ] **Step 2: Write the failing tests**

Create `pdf-translate/tests/test_cjk.py` with the header from "File structure" above, then:

```python
class KinsokuSetTests(unittest.TestCase):

    def test_members_from_the_public_classes(self):
        # cl-06 。 cl-07 、 cl-02 」） cl-10 ー and half-width ｰ, cl-11 ぁッ and
        # half-width ｧ, half-width ｡ ｣, cl-04 ？
        for ch in '\u3002\u3001\u300d\uff09\u30fc\uff70\u3041\u30c3\uff67\uff61\uff63\uff1f':
            self.assertIn(ch, verify_mod.KINSOKU_LINE_START, f'U+{ord(ch):04X}')
        # cl-01 「（【 and half-width ｢
        for ch in '\u300c\uff08\u3010\uff62':
            self.assertIn(ch, verify_mod.KINSOKU_LINE_END, f'U+{ord(ch):04X}')

    def test_the_two_sets_are_disjoint(self):
        self.assertEqual(verify_mod.KINSOKU_LINE_START & verify_mod.KINSOKU_LINE_END,
                         frozenset())

    def test_ordinary_letters_are_in_neither(self):
        for ch in '\u3042\u6f22\u30a2A1':
            self.assertNotIn(ch, verify_mod.KINSOKU_LINE_START)
            self.assertNotIn(ch, verify_mod.KINSOKU_LINE_END)


class KinsokuReportTests(unittest.TestCase):

    def test_hand_split_lines_fail_with_a_finding_per_broken_line(self):
        doc = pymupdf.open()
        split_lines_page(doc, SPLIT_BAD)
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual(status, 'FAIL')
        self.assertEqual([(f.page, f.where, f.text) for f in findings],
                         [(1, 'line-end', SPLIT_BAD[0]), (1, 'line-start', SPLIT_BAD[2])])
        self.assertTrue(lines[0].startswith('FAIL kinsoku: 2 CJK line(s)'), lines)
        self.assertEqual(lines[1], f'   p1 line-end: {SPLIT_BAD[0]}')
        self.assertEqual(lines[2], f'   p1 line-start: {SPLIT_BAD[2]}')

    def test_hand_split_lines_that_respect_the_rules_pass(self):
        doc = pymupdf.open()
        split_lines_page(doc, SPLIT_GOOD)
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))
        self.assertEqual(lines, ['PASS kinsoku: 3 CJK line(s) break within the rules'])

    def test_the_story_engine_paragraph_passes(self):
        doc = pymupdf.open()
        story_page(doc, PARA)
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))
        self.assertRegex(lines[0], r'^PASS kinsoku: \d+ CJK line\(s\) break within the rules$')
        # The engine really wrapped it: several lines, not one.
        self.assertGreater(int(lines[0].split()[2]), 3, lines)

    def test_a_lone_label_is_not_a_break(self):
        # A block's only line has no break before or after it: a dash used
        # as "none", a closing bracket after a checkbox, are labels, not
        # violations.
        doc = pymupdf.open()
        split_lines_page(doc, ['\u30fc'], y=100)
        split_lines_page(doc, ['\uff09\u8a72\u5f53\u306a\u3057'], y=100)
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))
        self.assertEqual(lines, ['PASS kinsoku: 2 CJK line(s) break within the rules'])

    def test_first_and_last_lines_of_a_block_are_exempt(self):
        # A block whose first line starts with 。 had no break before it;
        # one whose last line ends with 「 had none after it.
        doc = pymupdf.open()
        split_lines_page(doc, ['\u3002\u6c0f\u540d', '\u4f4f\u6240\u3092\u66f8\u304f', '\u8a18\u5165\u6b04\u300c'])
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))

    def test_pages_without_cjk_print_nothing(self):
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), 'Hello world.')
        page.insert_text((72, 90), '(continued)')
        self.assertEqual(kinsoku_report(doc), ([], None, []))

    def test_a_latin_line_inside_a_cjk_block_keeps_the_neighbours(self):
        # Adjacency is judged on every line of the block; only CJK lines are
        # judged for the rule. The Latin middle line neither hides the break
        # before the third line nor is itself judged.
        doc = pymupdf.open()
        split_lines_page(doc, ['\u7533\u7acb\u4eba\u306f', 'Form 1040', '\u3002\u6c0f\u540d\u3068\u4f4f\u6240'])
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual(status, 'FAIL')
        self.assertEqual([(f.where, f.text) for f in findings],
                         [('line-start', '\u3002\u6c0f\u540d\u3068\u4f4f\u6240')])
        self.assertEqual(lines[0].split(':')[0], 'FAIL kinsoku')

    def test_the_gate_consults_the_sets(self):
        # Remove the two members the fixture breaks and the fixture passes:
        # the gate judges by the sets, not by a hard-coded character.
        doc = pymupdf.open()
        split_lines_page(doc, SPLIT_BAD)
        start = verify_mod.KINSOKU_LINE_START - {'\u3002'}
        end = verify_mod.KINSOKU_LINE_END - {'\u300c'}
        with mock.patch.object(verify_mod, 'KINSOKU_LINE_START', start), \
                mock.patch.object(verify_mod, 'KINSOKU_LINE_END', end):
            lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))
```

- [ ] **Step 3: Run the tests to verify they fail**

Run from `pdf-translate/`: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk -v`

Expected: the module fails to import — `ImportError: cannot import name 'kinsoku_report' from 'pdf_translate.verify'`. That is the red for every test above. Do not proceed until you have seen it.

- [ ] **Step 4: Add the sets to `verify.py`**

Directly after `SPACELESS_SCRIPTS = {...}` (line ~178):

```python
# JIS X 4051 / W3C JLREQ ("Requirements for Japanese Text Layout", Appendix A
# character classes) line-breaking prohibitions, transcribed from those
# public references and from nothing else. Chinese layout (GB/T 15834)
# forbids the same punctuation at the same positions, so the gate judges
# every CJK line, not only Japanese ones. The Story engine breaks by UAX #14
# and never violates these (measured: dev/probes/cjk_kinsoku_probe.py); a
# target split by hand across source lines can.
#
# Characters that may not BEGIN a line:
KINSOKU_LINE_START = frozenset(
    # cl-02 closing brackets 」』）］｝〉》】〕〙〗’”｠ and half-width ｣
    '\u300d\u300f\uff09\uff3d\uff5d\u3009\u300b\u3011\u3015\u3019\u3017'
    '\u2019\u201d\uff60\uff63'
    # cl-03 hyphens ‐ 〜 ゠ – and the full-width tilde ～ Windows writes for 〜
    '\u2010\u301c\u30a0\u2013\uff5e'
    # cl-04 dividing punctuation ？！‼⁇⁈⁉
    '\uff1f\uff01\u203c\u2047\u2048\u2049'
    # cl-05 middle dots ・：；
    '\u30fb\uff1a\uff1b'
    # cl-06 full stops 。． and half-width ｡
    '\u3002\uff0e\uff61'
    # cl-07 commas 、， and half-width ､
    '\u3001\uff0c\uff64'
    # cl-09 iteration marks 々〻ゝゞヽヾ
    '\u3005\u303b\u309d\u309e\u30fd\u30fe'
    # cl-10 prolonged sound mark ー and half-width ｰ
    '\u30fc\uff70'
    # cl-11 small kana ぁぃぅぇぉっゃゅょゎゕゖ, ァィゥェォッャュョヮヵヶ, half-width ｧ..ｯ
    '\u3041\u3043\u3045\u3047\u3049\u3063\u3083\u3085\u3087\u308e\u3095\u3096'
    '\u30a1\u30a3\u30a5\u30a7\u30a9\u30c3\u30e3\u30e5\u30e7\u30ee\u30f5\u30f6'
    '\uff67\uff68\uff69\uff6a\uff6b\uff6c\uff6d\uff6e\uff6f'
)
# ... and that may not END one: cl-01 opening brackets 「『（［｛〈《【〔〘〖‘“｟
# and half-width ｢
KINSOKU_LINE_END = frozenset(
    '\u300c\u300e\uff08\uff3b\uff5b\u3008\u300a\u3010\u3014\u3018\u3016'
    '\u2018\u201c\uff5f\uff62'
)
```

(If Step 1 excluded U+301C, drop `\u301c` from the cl-03 line and amend the comment.)

- [ ] **Step 5: Add `_has_cjk` and `kinsoku_report`**

Directly after `conjunct_shaping_report` (the function that ends by returning `lines, status, findings`, ~line 1146):

```python
def _has_cjk(text):
    return any(script_of(ch) == 'CJK' for ch in text)


def kinsoku_report(doc):
    """(lines, status, findings) for gate 19: no drawn CJK line begins with a
    character JIS X 4051 / JLREQ forbids at line start, or ends with one it
    forbids at line end.

    Judged on the lines MuPDF reads back from each page, block by block. A
    line that begins with closing punctuation, a small kana or the prolonged
    sound mark is a violation only when a line of the same block sits above
    it — the break before it was a choice; a line that ends with an opening
    bracket only when one sits below it. A block's lone line is a label or
    one segment, not a break. Adjacency counts every line of the block; the
    rule is applied to the CJK ones. status is FAIL if any line violates,
    PASS if CJK lines were judged and none did, None when no page has one.
    """
    findings, judged = [], 0
    for page in doc:
        for block in page.get_text('dict').get('blocks', []):
            texts = []
            for ln in block.get('lines', []):
                text = ''.join(sp.get('text', '') for sp in ln.get('spans', ())).strip()
                if text:
                    texts.append(text)
            last = len(texts) - 1
            for i, text in enumerate(texts):
                if not _has_cjk(text):
                    continue
                judged += 1
                if i < last and text[-1] in KINSOKU_LINE_END:
                    findings.append(Finding(page.number + 1, 'line-end', text))
                if i > 0 and text[0] in KINSOKU_LINE_START:
                    findings.append(Finding(page.number + 1, 'line-start', text))
    if not judged:
        return [], None, []
    if findings:
        lines = [f'FAIL kinsoku: {len(findings)} CJK line(s) break a line-breaking rule '
                 f'(JIS X 4051 / JLREQ): closing punctuation, a small kana or the prolonged '
                 f'sound mark begins a line, or an opening bracket ends one. Declare the '
                 f'paragraph as a merge instead of splitting the target by hand:']
        for f in findings[:20]:
            lines.append(f'   p{f.page} {f.where}: {f.text[:60]}')
        return lines, 'FAIL', findings
    return [f'PASS kinsoku: {judged} CJK line(s) break within the rules'], 'PASS', []
```

Note the order inside one line: `line-end` is appended before `line-start`, so a line that breaks both rules reports `line-end` first; the fixture's two violations sit on different lines and come out in page order.

- [ ] **Step 6: Run the tests to verify they pass**

`PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk -v`

Expected: `Ran 11 tests … OK`. If `test_a_lone_label_is_not_a_break` fails because MuPDF put the two labels in one block, draw the second at `y=300` instead of `y=100` (they are meant to be far apart) — that is a fixture fix, not a code fix. If `test_hand_split_lines_fail…` finds the three lines in separate blocks, report it: the block rule is the design and was measured to hold at 14 pt leading.

- [ ] **Step 7: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_cjk.py dev/probes/cjk_kinsoku_probe.py
git diff --cached --check
git commit -m "feat(pdf-translate): kinsoku_report judges drawn CJK lines against the JLREQ line-start and line-end sets"
```

---

### Task 3: gate 19 in `verify`, parity against `main`

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py:212-220` (`GATE_NAMES`) and the block after `record('conjunct-shaping', …)` (~line 1373)
- Modify: `pdf-translate/tests/test_cjk.py` (append a class)

**Interfaces:**
- Consumes: `kinsoku_report(doc)` from Task 2.
- Produces: gate name `'kinsoku'` in `GATE_NAMES` immediately after `'conjunct-shaping'`; one printed line/block per CJK job; `GateResult('kinsoku', status, message, findings)` with `message == f'{n} line(s)'` on FAIL and `''` on PASS.

- [ ] **Step 1: Write the failing tests**

Append to `pdf-translate/tests/test_cjk.py`:

```python
class KinsokuVerifyTests(unittest.TestCase):
    """The gate through run_verify and the CLI: recorded, printed once, exit 1."""

    def _job(self, tmp, out_lines):
        orig = os.path.join(tmp, 'orig.pdf')
        out = os.path.join(tmp, 'out.pdf')
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)
        for i, text in enumerate(SPLIT_GOOD):
            page.insert_text((60, 100 + 14 * i), text, fontname='japan', fontsize=10)
        doc.save(orig)
        doc.close()
        doc = pymupdf.open()
        split_lines_page(doc, out_lines)
        doc.save(out)
        doc.close()
        return orig, out

    def test_the_gate_has_a_name(self):
        self.assertIn('kinsoku', GATE_NAMES)
        self.assertEqual(GATE_NAMES.index('kinsoku'), GATE_NAMES.index('conjunct-shaping') + 1)

    def test_a_broken_delivery_records_kinsoku_fail_and_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig, out = self._job(tmp, SPLIT_BAD)
            v = run_verify(orig, out, min_ink=0.1)
            gate = {g.name: g for g in v.gates}['kinsoku']
            self.assertEqual(gate.status, 'FAIL')
            self.assertEqual(gate.message, '2 line(s)')
            self.assertEqual([(f.page, f.where, f.text) for f in gate.findings],
                             [(1, 'line-end', SPLIT_BAD[0]), (1, 'line-start', SPLIT_BAD[2])])
            self.assertEqual(v.exit_code, 1)

    def test_a_clean_delivery_records_kinsoku_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig, out = self._job(tmp, SPLIT_GOOD)
            v = run_verify(orig, out, min_ink=0.1)
            gate = {g.name: g for g in v.gates}['kinsoku']
            self.assertEqual((gate.status, gate.message, gate.findings), ('PASS', '', ()))

    def test_the_console_prints_the_gate_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig, out = self._job(tmp, SPLIT_BAD)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify(orig, out, min_ink=0.1)
            printed = buf.getvalue().splitlines()
            heads = [ln for ln in printed if ln.startswith(('FAIL kinsoku', 'PASS kinsoku'))]
            self.assertEqual(len(heads), 1, printed)
            self.assertIn(f'   p1 line-start: {SPLIT_BAD[2]}', printed)
            self.assertEqual(rc, 1)

    def test_a_latin_job_prints_no_kinsoku_line_and_records_none(self):
        from tests.test_import_surface import _job
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify(src, out, translations=tr)
            self.assertNotIn('kinsoku', buf.getvalue())
            v = run_verify(src, out, translations=tr)
            self.assertNotIn('kinsoku', [g.name for g in v.gates])
```

- [ ] **Step 2: Run the tests to verify they fail**

`PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk.KinsokuVerifyTests -v`

Expected: `test_the_gate_has_a_name` fails with `AssertionError: 'kinsoku' not found in (...)`; the two `run_verify` tests fail with `KeyError: 'kinsoku'`; the console test fails with `AssertionError: 0 != 1`; the Latin job test passes already (nothing prints today) — that one is a guard, not a red, and is allowed to.

- [ ] **Step 3: Name the gate and wire it in**

In `GATE_NAMES` change

```python
    'arabic-letterforms', 'conjunct-shaping',
```

to

```python
    'arabic-letterforms', 'conjunct-shaping', 'kinsoku',
```

In `_execute_verify`, directly after

```python
    if shaping_status:
        record('conjunct-shaping', shaping_status, findings=shaping_findings)
```

add

```python
    kinsoku_lines, kinsoku_status, kinsoku_findings = kinsoku_report(jc)
    for line in kinsoku_lines:
        print(line)
    if kinsoku_status == 'FAIL':
        fail = 1
    if kinsoku_status:
        record('kinsoku', kinsoku_status,
               f'{len(kinsoku_findings)} line(s)' if kinsoku_status == 'FAIL' else '',
               findings=kinsoku_findings)
```

- [ ] **Step 4: Run the tests to verify they pass**

`PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk -v`

Expected: `Ran 16 tests … OK`.

- [ ] **Step 5: Console parity against `main` on the nine non-CJK jobs**

From the repo root, with `S=C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/parity` (create it):

```
mkdir -p "$S/main" "$S/jobs"
git archive main pdf-translate/pdf_translate | tar -x -C "$S/main"
PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_fixtures.py "$S/jobs"
PYTHONPATH="$S/main/pdf-translate" PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_runner.py "$S/jobs" > "$S/console_main.txt" 2> "$S/verdict_main.txt"
PYTHONPATH="C:/Dev/pdf-translate-skill/pdf-translate" PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe dev/probes/verdict_parity_runner.py "$S/jobs" > "$S/console_branch.txt" 2> "$S/verdict_branch.txt"
head -1 "$S/verdict_main.txt"; head -1 "$S/verdict_branch.txt"
diff "$S/console_main.txt" "$S/console_branch.txt" && echo CONSOLE IDENTICAL
diff <(grep -v '^# package' "$S/verdict_main.txt") <(grep -v '^# package' "$S/verdict_branch.txt") && echo VERDICTS IDENTICAL
```

Expected: the two `# package:` lines name different directories (the archive's and the checkout's — this proves the runner did not import the same package twice); `CONSOLE IDENTICAL`; `VERDICTS IDENTICAL`. Keep the output for the evidence doc. If `verdict_parity_runner.py` fails against `main`'s package on `findings`, that is the known pre-v51 guard and does not apply: `main` is v51.

- [ ] **Step 6: The full suite as CI runs it**

From `pdf-translate/`: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report tests.test_cjk 2>&1 | tail -5`

Expected: `OK` (possibly `OK (skipped=N)`); the run count is 295 + 16 = 311 minus nothing. `tests.test_import_surface.VerdictCompletenessTests` counts printed gate lines against recorded entries on a Japanese job: the new line records exactly one entry, so it stays green. If it goes red, the record site prints and records differently — fix the code, not the test.

- [ ] **Step 7: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_cjk.py
git diff --cached --check
git commit -m "feat(pdf-translate): gate 19 kinsoku — a drawn CJK line may not begin with closing punctuation or end with an opener"
```

---

### Task 4: the CJK faces under test — Noto Sans JP paragraph, and 东 refused, not borrowed

**Files:**
- Modify: `pdf-translate/tests/test_cjk.py` (append two classes)

**Interfaces:**
- Consumes: `tests/fonts/NotoSansJP-VF.ttf`, `NotoSansSC-VF.ttf` (Task 1); `story_page` (test header); `tests.test_pipeline`'s `build_plain_pdf`, `write_mapping`, `SOURCE_SENTENCE`, and its module objects `extract_segments`, `strip_text`, `retypeset` (it imports the scripts by path; use the same objects so the refusal test runs the same code as `test_cjk_target_in_a_latin_font_fails_and_saves_nothing`).

- [ ] **Step 1: Write the tests**

Append to `pdf-translate/tests/test_cjk.py`:

```python
def _face(path):
    if not path.is_file():
        raise unittest.SkipTest(f'{path.name} not fetched (tools/fetch_test_fonts.py)')
    return str(path)


class NotoSansJpTests(unittest.TestCase):
    """The fetched Japanese face, through the Story engine."""

    def test_a_noto_sans_jp_paragraph_breaks_within_the_rules(self):
        jp = _face(JP_FACE)
        doc = pymupdf.open()
        page = story_page(doc, PARA, fontfile=jp)
        self.assertTrue(any('NotoSansJP' in f[3] for f in page.get_fonts()),
                        page.get_fonts())
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))
        self.assertGreater(int(lines[0].split()[2]), 3, lines)


class CjkFaceTests(unittest.TestCase):
    """2d: a character the selected face cannot draw is refused, never drawn
    from another face. The precondition is asserted so a font update cannot
    make the test pass for the wrong reason."""

    def setUp(self):
        self.jp = _face(JP_FACE)
        self.sc = _face(SC_FACE)

    def test_the_japanese_face_lacks_east_and_the_chinese_face_has_it(self):
        jp = pymupdf.Font(fontfile=self.jp)
        sc = pymupdf.Font(fontfile=self.sc)
        self.assertFalse(jp.has_glyph(0x4E1C), 'Noto Sans JP now carries 东: 2d needs a new separator')
        self.assertTrue(sc.has_glyph(0x4E1C))
        for cp in (0x76F4, 0x9AA8, 0x6D77, 0x6771):   # 直 骨 海 東
            self.assertTrue(jp.has_glyph(cp) and sc.has_glyph(cp), f'U+{cp:04X}')

    def test_a_character_the_japanese_face_lacks_is_refused_not_borrowed(self):
        from tests.test_pipeline import (SOURCE_SENTENCE, build_plain_pdf, extract_segments,
                                         retypeset, strip_text, write_mapping)
        self.assertFalse(pymupdf.Font(fontfile=self.jp).has_glyph(0x4E1C))
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: '\u6771\u4eac \u4e1c'}, Path(self.jp))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('the chosen font cannot draw', log)
            self.assertIn('U+4E1C', log)
            self.assertFalse(os.path.exists(out), msg=log)
            # Control: the same job without 东 is drawn, and only by the JP face.
            write_mapping(tr, {SOURCE_SENTENCE: '\u6771\u4eac'}, Path(self.jp))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            with pymupdf.open(out) as done:
                names = [f[3] for page in done for f in page.get_fonts()]
            self.assertTrue(names and all('NotoSansJP' in n for n in names), names)
```

- [ ] **Step 2: Run them — the faces are fetched, so nothing skips**

`PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk.NotoSansJpTests tests.test_cjk.CjkFaceTests -v`

Expected: `Ran 3 tests … OK`. These pin behaviour that exists (the refusal) and a precondition (the cmap), so they pass on first run by design; the red for the refusal lives in `test_pipeline.test_cjk_target_in_a_latin_font_fails_and_saves_nothing` already. If the control's font names include anything other than `NotoSansJP` (a Helvetica for a marker, say), print `names` and report it rather than loosening the assertion — it would mean the JP face did not draw the whole line.

To see the precondition guard bite, temporarily swap `self.jp` for `self.sc` in the first assertion and watch `assertFalse` fail with the message; then restore it.

- [ ] **Step 3: Commit**

```bash
git add pdf-translate/tests/test_cjk.py
git diff --cached --check
git commit -m "test(pdf-translate): Noto Sans JP paragraph passes kinsoku; a glyph the JP face lacks is refused, never borrowed"
```

---

### Task 5: docs, version 52, CI suite line, DECISIONS, evidence

**Files:**
- Modify: `pdf-translate/SKILL.md` (frontmatter `version: "51"`; the gate bullets after **Conjunct shaping** ~line 440; the **Narrow columns** bullet ~line 288)
- Modify: `pdf-translate/references/gates.md` (Always on table ~line 25; the `GATE_NAMES` list ~line 146; the `where`/`text` table ~line 176)
- Modify: `pdf-translate/README.md:107` (`eighteen structural gates`)
- Modify: `.claude-plugin/plugin.json`, `pdf-translate/pyproject.toml`, `pdf-translate/pdf_translate/__init__.py` (version)
- Modify: `.github/workflows/tests.yml:49` (suite line)
- Modify: `docs/DECISIONS.md` (append one row)
- Create: `docs/reviews/2026-09-16-kinsoku-gate.md`

**Interfaces:** none; `tests.test_verify_report.VersionLockstepTests` reads the four version sources and CI's "Version sources agree" step reads them too.

- [ ] **Step 1: Version 52 in the four sources**

- `pdf-translate/SKILL.md` frontmatter: `version: "51"` → `version: "52"`.
- `.claude-plugin/plugin.json`: `"version": "51.0.0"` → `"version": "52.0.0"`.
- `pdf-translate/pyproject.toml`: `version = "51.0.0"` → `version = "52.0.0"`.
- `pdf-translate/pdf_translate/__init__.py`: `__version__ = '51'` → `__version__ = '52'`.

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_verify_report.VersionLockstepTests -v` — expected OK.

- [ ] **Step 2: SKILL.md**

After the **Conjunct shaping** bullet (the one ending `Thai, Lao and Hebrew niqqud are REVIEW, never PASS.`) add:

```markdown
- **Kinsoku** (always on): no drawn CJK line begins with closing
  punctuation, a small kana or the prolonged sound mark, or ends with an
  opening bracket (JIS X 4051 / JLREQ; half-width forms included). The
  Story engine never breaks a merge that way; a target split by hand
  across source lines can, and FAILs with the line named.
```

In the **Narrow columns** bullet, after `the target's word order rarely breaks where the source's did.` append (same paragraph):

```markdown
  In Japanese or Chinese a hand split also breaks kinsoku — a line may
  not begin with 。、」 or ー — and `verify` fails it (gate 19).
```

- [ ] **Step 3: gates.md**

Always on table: after the `| conjunct shaping | … |` row add

```markdown
| kinsoku | a drawn CJK line begins with a character JIS X 4051 / JLREQ forbids at line start (closing brackets, hyphens, dividing punctuation, middle dots, full stops, commas, iteration marks, the prolonged sound mark, small kana; half-width forms included) or ends with an opening bracket. Judged block by block on the lines MuPDF reads back; a block's first line is never a line-start violation and its last never a line-end one. The Story engine never does this to a merge; a target split by hand across source lines can |
```

In the "As a library" paragraph change `arabic-letterforms, conjunct-shaping, leak-scan,` to `arabic-letterforms, conjunct-shaping, kinsoku, leak-scan,`.

In the `where`/`text` table, after the `| conjunct-shaping | … |` row add

```markdown
| kinsoku | `line-start` / `line-end` | the drawn line |
```

- [ ] **Step 4: README, CI suite line**

`pdf-translate/README.md:107`: `eighteen structural gates` → `nineteen structural gates`.

`.github/workflows/tests.yml` suite line: append ` tests.test_cjk` before ` -v`, giving
`run: python -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report tests.test_cjk -v`.

- [ ] **Step 5: DECISIONS row**

Append to the "Open ledger" table in `docs/DECISIONS.md`:

```markdown
| 2026-09-16 | Gate 19 `kinsoku`: no drawn CJK line begins with a JIS X 4051 / JLREQ line-start member (closing brackets, hyphens, dividing punctuation, middle dots, full stops, commas, iteration marks, the prolonged sound mark, small kana, and their half-width forms) or ends with an opening bracket, judged block by block on the lines MuPDF reads back, a block's first and last line exempt; FAIL with one finding per line. No engine work. Test faces Noto Sans JP and SC join the fetcher (`NotoSansJP-VF.ttf`, `NotoSansSC-VF.ttf`, google/fonts builds). Version 51 → 52. | The product asked for kinsoku; measured first (`dev/probes/cjk_kinsoku_probe.py`, PyMuPDF 1.28.2, Noto Sans JP 2.04): the Story engine breaks by UAX #14 — 158 laid lines, 0 violations, against 38 + 8 for a naive breaker; 75/75 line-start and 15/15 line-end members protected. The only path that can violate is a target split by hand across source lines, which the engine never sees, so the gate reads the delivered lines. The sets are transcribed from the public references and nothing else. Console output of non-CJK jobs is byte-identical (parity runner, nine jobs). | A Story-engine release that breaks a member wrongly (the probe would show it), or a real delivery in which a block's inner line legitimately begins with a member — that would reopen the adjacency rule, not the sets. |
```

- [ ] **Step 6: Evidence doc**

Create `docs/reviews/2026-09-16-kinsoku-gate.md`:

```markdown
# Gate 19 `kinsoku` and the CJK test faces — evidence (v52)

Branch `feat/kinsoku-gate` on `main` at `c28ada9`. Plan:
`docs/plans/2026-09-16-cjk-faces-and-kinsoku-gate.md`. Assessment that
scoped it: `docs/reviews/2026-09-16-cjk-request-assessment.md`.

Not a rendering change: AGENTS.md Rule 1 does not apply. The evidence is
the measurement, the red and green runs, the parity diff and the suite.

## Faces fetched (Task 1)

<paste the two `fetching …` blocks with KB and sha256, and the `--check` line>

## Measurement (Task 2, Step 1)

<paste the probe's full output after U+301C joined cl-03>

## Red, then green

<paste the ImportError from Task 2 Step 3 (first lines), then `Ran 11 tests … OK`;
the four failures from Task 3 Step 2, then `Ran 16 tests … OK`>

## Parity against `main` (Task 3, Step 5)

<paste the two `# package:` lines and the two IDENTICAL lines>

## Suite (Task 3, Step 6 and after Task 5)

<paste the last three lines of the full-suite run>
```

Fill every `<paste …>` from the runs you actually made — none may remain.

- [ ] **Step 7: Full suite, diff check, commit**

From `pdf-translate/`: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report tests.test_cjk 2>&1 | tail -3`

Expected: `OK`. Then:

```bash
git add pdf-translate/SKILL.md .claude-plugin/plugin.json pdf-translate/pyproject.toml pdf-translate/pdf_translate/__init__.py pdf-translate/references/gates.md pdf-translate/README.md .github/workflows/tests.yml docs/DECISIONS.md docs/reviews/2026-09-16-kinsoku-gate.md
git diff --cached --check
git commit -m "docs(pdf-translate): gate 19 kinsoku in SKILL.md, gates.md and README; DECISIONS row; evidence; version 52"
```

---

## Self-review

- Spec coverage: 2a → Task 1; 2c′ (gate over drawn lines, red with author-split lines, green with a merge, DECISIONS row, SKILL.md sentence, version 52) → Tasks 2, 3, 5; 2d′ (precondition + refusal, no placeholder) → Task 4; parity → Task 3 Step 5; evidence → Task 5 Step 6.
- Placeholders: the evidence doc's `<paste …>` markers are instructions to the implementer to paste real output, and Step 6 says none may remain.
- Names: `kinsoku_report`, `KINSOKU_LINE_START`, `KINSOKU_LINE_END`, `_has_cjk`, gate name `'kinsoku'`, `where` values `line-start` / `line-end`, faces `NotoSansJP-VF.ttf` / `NotoSansSC-VF.ttf` — used identically in every task.
