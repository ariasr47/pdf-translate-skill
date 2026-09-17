# Gate 21 `leak-cjk` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When source and output share the spaceless CJK family, `verify` no longer prints one blind REVIEW: gate 21 `leak-cjk` scans every drawn line of the output for characters that cannot belong to the target language (kana in a Chinese target; Han outside the target's repertoire), FAILs a line with six or more, REVIEWs a line with one to five, PASSes otherwise, with one `Finding` per line — and the old REVIEW line stays only when the tell cannot run. Version 54 → 55.

**Architecture:** The measurement is `docs/BRIEF-cjk-leak-tell.md` (do not re-derive): the brief's verbatim rule is blind to an echoed segment by construction; a repertoire tell (cp932 for Japanese, GB 2312 for Simplified Chinese, Big5 for Traditional Chinese, kana for both Chinese targets) has zero false tells on eleven own-language texts and finds the echo with 14 tells; NFKC folding is required because source ToUnicode drift (U+F98E 年, U+F92C 郎) reaches the output through an authored mapping; TC → JP is weak and stays REVIEW. A new module `pdf_translate/cjk_tell.py` owns the tell (no printing, no data files); `verify.py` owns the report at the existing `same_spaceless` branch and the record site. The target convention comes from the mapping's `lang` through `han_forms.convention_for_lang`; the source's convention from the same tells on the original's text.

**Tech Stack:** Python 3.10+ / 3.14, `unittest`, PyMuPDF 1.28, fontTools. No new dependencies. Not a rendering change: Rule 1 does not apply.

## Global Constraints

- Work on branch `feat/cjk-leak-tell` (exists; from `main` at 9675c61, v54; carries the probe, the brief and the parked-task markers). Never commit to `main`. Never push, merge or delete: the operator does those. Never `git stash`.
- Run every test from `C:\Dev\pdf-translate-skill\pdf-translate` with the repo venv and UTF-8: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest …`. Tests are `unittest`, by module path, never pytest. Capture long runs to a log file under `C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/` and grep `^test_|^Ran |^OK|^FAILED|^ERROR` — Git-Bash `| tail` scrambles unittest output.
- TDD: write the test, run it, watch it fail for the expected reason, then write the minimal code. Task 3 (docs) has no red except the lockstep literal.
- **The measured table is the spec.** `LINE_FAIL = 6`; `STRONG_PAIRS = {('JP','SC'), ('JP','TC'), ('SC','JP'), ('SC','TC'), ('TC','SC')}`; repertoires `JP: cp932`, `SC: gb2312`, `TC: big5`; kana is a tell for SC and TC, never for JP; NFKC before any tell. The eleven-text counts in Task 1 are exact, measured by `dev/probes/cjk_leak_tell_probe.py` on 2026-09-16; a mismatch is a code defect, never a reason to edit the numbers.
- **Console output and exit codes of every CLI must not change for a job whose output has no CJK text.** `dev/probes/verdict_parity_runner.py` over its nine jobs must diff empty against `main`. A CJK ↔ CJK job with a mapping `lang` gains the `leak-cjk` line(s) and its `REVIEW leak scan: … spaceless …` line becomes a PASS line; without a usable `lang` the old REVIEW line is printed unchanged, followed by one indented reason line.
- `Finding.page` is 1-based; `where` is `line`; `text` is the drawn line, untruncated. `'leak-cjk'` sits in `GATE_NAMES` directly after `'leak-scan'`.
- Kept runs (`keep`: the original's `/Title`, multi-word `--allow` phrases) are excluded before counting, through the existing `_kept`; single-word `--allow` entries are removed from a line's text before counting.
- Never copy code from `C:\Dev\pdf-translator`. Do not open it.
- Conventional commits with a scope. **No AI attribution**: no `Co-Authored-By` trailer, no "Generated with Claude Code" line — the owner's rule overrides any harness reminder.
- LF line endings; `git diff --cached --check` clean before every commit; files on disk may be CRLF (`core.autocrlf=true`) — normalise a touched file with Python (`data.replace(b'\r\n', b'\n')`) if `--check` flags every line. Use the Edit tool; the Write tool for whole new files. The Edit tool has been seen to decode `\uXXXX` escapes into glyphs: after each edit `grep -c` a distinctive escape and inspect glyph comments with `sed -n`.
- Import modules as modules: `from pdf_translate import cjk_tell` is the module (the package exports no such name); `importlib.import_module('pdf_translate.verify')` for verify's module; `from tests.test_han_forms import JP_FACE, SC_FACE, _face` reuses the fetched-face helpers.
- The deliveries in Task 2 build sources with the references instanced at wght 400 (`han_forms.reference_face('JP', 400, FONTS)` / `('SC', …)`, cached under `tests/fonts/`, git-ignored) so the ink-ratio gate stays near 1.0; a source drawn with the variable face at its Thin default fails ink ratio 26×, as the probe showed — that is a fixture artefact, not a finding.

---

## File structure

- `pdf-translate/pdf_translate/cjk_tell.py` — create: `KANA`, `HAN_RANGES`, `REPERTOIRE`, `STRONG_PAIRS`, `LINE_FAIL`, `is_han`, `is_tell`, `tells_in`, `convention_of`, `strip_allowed`.
- `pdf-translate/pdf_translate/verify.py` — modify: `from . import cjk_tell, han_forms, shaping_probe`; `'leak-cjk'` in `GATE_NAMES`; `cjk_tell_report(doc, convention, keep, kept, allow)` after `kinsoku_report`; the `same_spaceless` branch in `_execute_verify`; the module docstring (entry 4 and a new entry 21).
- `pdf-translate/tests/test_cjk_leak.py` — create: `TellTests`, `LeakCjkGateTests`, the `build_cjk_delivery` helper.
- `.github/workflows/tests.yml` — suite line gains `tests.test_cjk_leak`.
- `pdf-translate/SKILL.md`, `.claude-plugin/plugin.json`, `pdf-translate/pyproject.toml`, `pdf-translate/pdf_translate/__init__.py`, `pdf-translate/tests/test_verify_report.py` — version 55.
- `pdf-translate/references/gates.md`, `pdf-translate/README.md`, `docs/DECISIONS.md`, `docs/BRIEF-unattended-delivery.md` (Task F header), `docs/REQUESTS-from-product.md` (E2 row), `docs/reviews/2026-09-16-leak-cjk-gate.md` — docs and evidence.

---

### Task 1: the tell — `cjk_tell.py`, the measured table reproduced

**Files:**
- Create: `pdf-translate/pdf_translate/cjk_tell.py`
- Create: `pdf-translate/tests/test_cjk_leak.py`
- Create: `docs/reviews/2026-09-16-leak-cjk-gate.md`

**Interfaces:**
- Produces: `REPERTOIRE = {'JP': ('Japanese', 'cp932'), 'SC': ('Simplified Chinese', 'gb2312'), 'TC': ('Traditional Chinese', 'big5')}`, `STRONG_PAIRS`, `LINE_FAIL = 6`, `is_han(ch) -> bool`, `is_tell(ch, convention) -> bool`, `tells_in(text, convention) -> list[str]` (NFKC first), `convention_of(text) -> 'JP'|'SC'|'TC'|None`, `strip_allowed(text, allow) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `pdf-translate/tests/test_cjk_leak.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate 21, leak-cjk: when source and output share the spaceless CJK family,
characters that cannot belong to the target language are the leak. The
measured table in docs/BRIEF-cjk-leak-tell.md §2 is reproduced first — the
counts are exact — then the gate on deliveries built through the pipeline."""
import importlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf

from pdf_translate import cjk_tell, han_forms
from tests.test_han_forms import FONTS, JP_FACE, SC_FACE, _face

verify_mod = importlib.import_module('pdf_translate.verify')

# The eleven texts of the brief, with (tells for a ja target, for zh-Hans, for zh-Hant), exact.
TEXTS = [
    ('ja form paragraph 1', '申請者は本日中にこの書類を提出しなければなりません。指定された欄に氏名と住所を正確に記入し、署名欄に署名してください。記入漏れのある書類は返送されます。', (0, 49, 39), 'JP'),
    ('ja form paragraph 2', 'この申請書は在留許可の延長を申請するためのものです。有効なパスポートの写し、最近撮影した写真二枚、および手数料の支払い証明を添付してください。手続きには約二十営業日かかります。', (0, 56, 51), 'JP'),
    ('ja kinsoku paragraph', 'データー、翻訳「テスト」の結果。ページーレイアウトは、ちょっとした「工夫」で、きっちり保たれます。', (0, 35, 34), 'JP'),
    ('ja kanji-only line', '東京都千代田区霞が関一丁目 国税庁 所得税確定申告書', (0, 6, 7), 'JP'),
    ('zh-Hans form paragraph 1', '申请人必须在今天提交此表格。请在指定栏目中准确填写您的姓名和地址，并在签名处签字。未按要求填写的表格将被退回。', (9, 0, 10), 'SC'),
    ('zh-Hans form paragraph 2', '本申请表用于申请居留许可的延期。请附上有效护照复印件、两张近期照片和缴费凭证。办理时间约为二十个工作日。', (16, 0, 17), 'SC'),
    ('zh-Hans form paragraph 3', '如有疑问，请拨打服务热线或访问我们的网站。工作时间为周一至周五上午九点至下午五点。', (12, 0, 14), 'SC'),
    ('zh-Hans shared-form sentence', '日本国东京都 2026年3月31日 山田太郎 电话 03-1234-5678', (3, 0, 4), 'SC'),
    ('zh-Hant form sentence', '申請人必須在今天提交此表格。請在指定欄位中準確填寫您的姓名和地址，並在簽名處簽字。', (1, 11, 0), 'TC'),
    ('mixed: zh-Hans with a kana name', '申请人：やまだ たろう（山田太郎），出生于1990年。', (1, 6, 7), None),
]


class TellTests(unittest.TestCase):

    def counts(self, text):
        return tuple(len(cjk_tell.tells_in(text, c)) for c in ('JP', 'SC', 'TC'))

    def test_the_measured_table(self):
        for label, text, expected, _ in TEXTS:
            self.assertEqual(self.counts(text), expected, label)

    def test_the_corpus_japanese_document(self):
        corpus = FONTS.parents[1] / 'corpus' / 'ja_source.pdf'
        if not corpus.is_file():
            raise unittest.SkipTest('corpus/ja_source.pdf missing')
        with pymupdf.open(str(corpus)) as doc:
            text = '\n'.join(p.get_text() for p in doc)
        self.assertEqual(self.counts(text), (0, 13, 10))
        self.assertEqual(cjk_tell.convention_of(text), 'JP')

    def test_convention_of(self):
        for label, text, _, convention in TEXTS:
            self.assertEqual(cjk_tell.convention_of(text), convention, label)
        self.assertIsNone(cjk_tell.convention_of('日本 2026'))       # shared Han only: ambiguous
        self.assertIsNone(cjk_tell.convention_of('Latin only 123'))
        self.assertIsNone(cjk_tell.convention_of(''))
        self.assertIsNone(cjk_tell.convention_of(None))

    def test_single_characters(self):
        for ch in '\u8bf7\u4e66\u4e1c\u95e8':                     # 请 书 东 门: Simplified only
            self.assertTrue(cjk_tell.is_tell(ch, 'JP'), ch)
            self.assertFalse(cjk_tell.is_tell(ch, 'SC'), ch)
        for ch in '\u6c17\u56f3\u685c':                           # 気 図 桜: Japanese only
            self.assertTrue(cjk_tell.is_tell(ch, 'SC'), ch)
            self.assertFalse(cjk_tell.is_tell(ch, 'JP'), ch)
        for ch in '\u56fd\u4f1a\u5b66':                           # 国 会 学: shinjitai = simplified
            self.assertFalse(cjk_tell.is_tell(ch, 'JP') or cjk_tell.is_tell(ch, 'SC'), ch)
        for ch in '\u6771\u8acb\u5beb':                           # 東 請 寫: Japanese and Traditional
            self.assertTrue(cjk_tell.is_tell(ch, 'SC'), ch)
            self.assertFalse(cjk_tell.is_tell(ch, 'JP') or cjk_tell.is_tell(ch, 'TC'), ch)
        self.assertTrue(all(cjk_tell.is_tell('\u9555', c) for c in ('JP', 'SC', 'TC')))   # 镕: in none
        self.assertTrue(cjk_tell.is_tell('\u3042', 'SC') and cjk_tell.is_tell('\u30ab', 'TC'))
        self.assertFalse(cjk_tell.is_tell('\u3042', 'JP'))
        self.assertFalse(cjk_tell.is_tell('A', 'SC') or cjk_tell.is_tell('1', 'JP') or cjk_tell.is_tell('\u3002', 'SC'))
        self.assertFalse(cjk_tell.is_tell('\u8bf7', 'KR'))         # no repertoire: never a tell

    def test_compatibility_ideographs_fold_before_the_tell(self):
        # Source ToUnicode drift: U+F98E for 年, U+F92C for 郎 (audit finding H4), carried by an
        # authored mapping into the output. Raw they are tells; folded they are not.
        self.assertTrue(cjk_tell.is_tell('\uf98e', 'SC') and cjk_tell.is_tell('\uf92c', 'SC'))
        self.assertEqual(cjk_tell.tells_in('2026\uf98e3\u670831\u65e5', 'SC'), [])
        self.assertEqual(cjk_tell.tells_in('\u5c71\u7530\u592a\uf92c', 'SC'), [])
        self.assertEqual(cjk_tell.tells_in('\u5c71\u7530\u592a\uf92c', 'JP'), [])

    def test_tells_in_keeps_order_and_repeats(self):
        self.assertEqual(''.join(cjk_tell.tells_in('\u3055\u308c\u305f\u6b04\u306b', 'SC')),
                         '\u3055\u308c\u305f\u6b04\u306b')
        self.assertEqual(cjk_tell.tells_in('', 'SC'), [])
        self.assertEqual(cjk_tell.tells_in(None, 'SC'), [])

    def test_strong_pairs_and_the_weak_one(self):
        self.assertIn(('JP', 'SC'), cjk_tell.STRONG_PAIRS)
        self.assertIn(('SC', 'JP'), cjk_tell.STRONG_PAIRS)
        self.assertNotIn(('TC', 'JP'), cjk_tell.STRONG_PAIRS)
        self.assertEqual(cjk_tell.LINE_FAIL, 6)

    def test_strip_allowed(self):
        self.assertEqual(cjk_tell.strip_allowed('\u7533\u8bf7\u4eba\uff1a\u30b9\u30df\u30b9', {'\u30b9\u30df\u30b9'}),
                         '\u7533\u8bf7\u4eba\uff1a')
        self.assertEqual(cjk_tell.strip_allowed('abc', set()), 'abc')
        self.assertEqual(cjk_tell.strip_allowed('abc', None), 'abc')


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk_leak -v 2>&1 | grep -E "^(Ran |OK|FAILED|ERROR|ImportError|ModuleNotFoundError)"`
Expected: `ImportError: cannot import name 'cjk_tell' from 'pdf_translate'` (no test runs).

- [ ] **Step 3: Write the module**

Create `pdf-translate/pdf_translate/cjk_tell.py`:

```python
# -*- coding: utf-8 -*-
"""Gate 21, leak-cjk: when source and output share the spaceless CJK family,
characters that cannot belong to the target language are the leak.

retypeset refuses a segment the mapping omits, so the leak that reaches a
delivered document is an echo — the translator returns the source as the
target, and the mapping says target == source, as it does for a date or a
name. A verbatim rule cannot see that; a script tell can. Measured
(docs/BRIEF-cjk-leak-tell.md, dev/probes/cjk_leak_tell_probe.py, 2026-09-16):
zero tells on eleven own-language texts including corpus/ja_source.pdf,
3–56 on the other language's texts, 14 on an echoed segment in a real
ja → zh-Hans delivery.

The tells are encoding repertoires — cp932 (JIS X 0208 + Microsoft
extensions) for Japanese, GB 2312 for Simplified Chinese, Big5 for
Traditional Chinese — plus kana for either Chinese target. No data files.
NFKC first: a source PDF's ToUnicode drifts to compatibility ideographs
(U+F98E 年, U+F92C 郎) and an authored mapping carries them into the output.
Nothing here prints.
"""
import re
import unicodedata

KANA = re.compile(r'[\u3041-\u309f\u30a0-\u30ff\u31f0-\u31ff\uff66-\uff9f]')
HAN_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x2FA1F))

# convention -> (display name, the encoding whose repertoire the language's Han must fit)
REPERTOIRE = {
    'JP': ('Japanese', 'cp932'),
    'SC': ('Simplified Chinese', 'gb2312'),
    'TC': ('Traditional Chinese', 'big5'),
}
# (source convention, target convention) pairs the tell separates. TC -> JP is
# weak — JIS X 0208 carries most traditional forms (one tell in 38 letters) —
# and stays REVIEW.
STRONG_PAIRS = frozenset({('JP', 'SC'), ('JP', 'TC'), ('SC', 'JP'), ('SC', 'TC'), ('TC', 'SC')})
# Tells in one drawn line: an echoed sentence carries 9–56; a kana name 6; a
# rare name character outside every repertoire 1.
LINE_FAIL = 6


def is_han(ch):
    o = ord(ch)
    return any(a <= o <= b for a, b in HAN_RANGES)


def _encodable(ch, enc):
    try:
        ch.encode(enc)
        return True
    except UnicodeEncodeError:
        return False


def is_tell(ch, convention):
    """True when ch cannot belong to a text of the convention: kana in a
    Chinese one, or Han outside the convention's repertoire. Never for a
    convention without a repertoire (KR), digits, Latin or punctuation."""
    if convention not in REPERTOIRE:
        return False
    if convention != 'JP' and KANA.match(ch):
        return True
    return is_han(ch) and not _encodable(ch, REPERTOIRE[convention][1])


def tells_in(text, convention):
    """The characters of text (NFKC-folded first) that cannot belong to the
    convention, in order, repeats kept."""
    folded = unicodedata.normalize('NFKC', text or '')
    return [ch for ch in folded if is_tell(ch, convention)]


def convention_of(text):
    """The one convention whose repertoire holds every letter of text; None
    when the text has no CJK letters, or none or several conventions fit
    (shared Han only: ambiguous)."""
    folded = unicodedata.normalize('NFKC', text or '')
    letters = [ch for ch in folded if is_han(ch) or KANA.match(ch)]
    if not letters:
        return None
    fits = [c for c in REPERTOIRE if not any(is_tell(ch, c) for ch in letters)]
    return fits[0] if len(fits) == 1 else None


def strip_allowed(text, allow):
    """text with every allowlisted token removed, so its characters are not counted."""
    for token in sorted(allow or (), key=len, reverse=True):
        if token:
            text = text.replace(token, '')
    return text
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk_leak -v 2>&1 | grep -E "^(test_|Ran |OK|FAILED|ERROR)"`
Expected: 8 tests, `OK`. If a count in `test_the_measured_table` misses, compare `tells_in` with the probe's `measure` (`dev/probes/cjk_leak_tell_probe.py`); never edit the numbers.

- [ ] **Step 5: Start the evidence doc**

Create `docs/reviews/2026-09-16-leak-cjk-gate.md`:

```markdown
# Gate 21 `leak-cjk` — evidence (v55)

Branch `feat/cjk-leak-tell` from `main` (v54). Spec: `docs/BRIEF-cjk-leak-tell.md` (measured 2026-09-16 with
`dev/probes/cjk_leak_tell_probe.py`); task F of `docs/BRIEF-unattended-delivery.md`; the product's work order E2.
Not a rendering change: AGENTS.md Rule 1 does not apply; reviewed on another model.

## Task 1 — the tell, red then green

Red (the module does not exist):

```
<paste the grep line from Step 2>
```

Green (the eleven-text table exact, the corpus document, the drift fold, the pairs):

```
<paste the Ran/OK lines from Step 4, with the test names>
```
```

Replace the two `<paste …>` markers with real output.

- [ ] **Step 6: Commit**

```bash
git add pdf-translate/pdf_translate/cjk_tell.py pdf-translate/tests/test_cjk_leak.py docs/reviews/2026-09-16-leak-cjk-gate.md
git diff --cached --check
git commit -m "feat(pdf-translate): cjk_tell — characters that cannot belong to a Japanese or Chinese target, by repertoire"
```

---

### Task 2: gate 21 in `verify`, deliveries, parity

**Files:**
- Modify: `pdf-translate/pdf_translate/verify.py` (import; `GATE_NAMES`; `cjk_tell_report` after `kinsoku_report`; the `same_spaceless` branch in `_execute_verify`; docstring)
- Modify: `pdf-translate/tests/test_cjk_leak.py` (imports, `build_cjk_delivery`, `LeakCjkGateTests`)
- Modify: `docs/reviews/2026-09-16-leak-cjk-gate.md` (append)

**Interfaces:**
- Consumes: `cjk_tell.*`; `han_forms.convention_for_lang`; verify's `_page_lines`, `_kept`, `Finding`, `record`, and the locals `same_spaceless`, `src_script`, `mapping_lang`, `keep`, `kept`, `allow`, `o_text`, `jc`, `fail`.
- Produces: `verify.cjk_tell_report(doc, convention, keep, kept, allow) -> (lines, status, findings)`; `'leak-cjk'` in `GATE_NAMES` after `'leak-scan'`; `tests.test_cjk_leak.build_cjk_delivery(tmp, lines, src_face, out_face, lang) -> (orig, out, translations, segments)`.

Console shapes (pinned by the tests):
- `FAIL leak scan (CJK tell): 1 line(s) carry characters that cannot belong to a Simplified Chinese target — untranslated Japanese text:` then `   p1: <line[:60]>  [14 tells: <tells[:12]>]`
- `REVIEW leak scan (CJK tell): 1 line(s) carry a few characters that cannot belong to a Simplified Chinese target (a name in kana, a rare character — allowlist with --allow):` then the lines
- `PASS leak scan (CJK tell): 5 line(s) hold only characters a Simplified Chinese target can carry`
- when the tell runs, in place of the old REVIEW: `PASS leak scan: source and output share the spaceless CJK family; judged by the CJK tell (leak-cjk)`
- when it cannot: the old line `REVIEW leak scan: source and output share the spaceless CJK family; the scan cannot tell them apart. Rely on --translations and the visual pass.` unchanged, followed by `   (CJK tell not applied: <reason>)` where the reason is one of `no lang in the mapping`, `lang "<value>" names no Han convention`, `the source's convention is not clear`, `the pair Traditional Chinese -> Japanese is not separable by repertoire (measured)`.

- [ ] **Step 1: Write the failing tests**

In `pdf-translate/tests/test_cjk_leak.py`, add after `verify_mod = …`:

```python
from pdf_translate.verify import GATE_NAMES, run_verify, verify
```

Add after `TEXTS`:

```python
def build_cjk_delivery(tmp, lines, src_face, out_face, lang):
    """A real delivery from a multi-line CJK original: each (source, target) in
    lines is one drawn line; target None means an echo (the target is the
    extracted source text, as an echoing translator would return it). The
    mapping is keyed on the EXTRACTED segment texts, never on what was typed —
    a source PDF's ToUnicode drifts. prepare_font sees no lang (its han-forms
    check stays quiet); retypeset writes lang as /Lang. Returns
    (orig, out, translations, segments)."""
    from tests.test_pipeline import extract_segments, prepare_font, retypeset, strip_text, write_mapping
    src, stripped, out = (os.path.join(tmp, n) for n in ('orig.pdf', 'stripped.pdf', 'out.pdf'))
    tr, subset, segments = (os.path.join(tmp, n) for n in ('translations.json', 'subset.ttf', 'segments.json'))
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    tw = pymupdf.TextWriter(page.rect)
    font = pymupdf.Font(fontfile=str(src_face))
    for i, (source, _) in enumerate(lines):
        tw.append((72, 100 + 40 * i), source, font=font, fontsize=12)
    tw.write_text(page)
    doc.save(src)
    doc.close()
    extract_segments.extract_segments(src, outdir=tmp)
    with open(segments, encoding='utf-8') as f:
        seg_texts = [s['text'] for s in json.load(f)['segments']]
    assert len(seg_texts) == len(lines), seg_texts
    mapping = {seg: (seg if target is None else target) for seg, (_, target) in zip(seg_texts, lines)}
    strip_text.strip_text(src, stripped)
    write_mapping(tr, mapping, Path(out_face))
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = prepare_font.prepare_font(str(out_face), tr, subset, instance=None)
    assert rc == 0, buf.getvalue()
    write_mapping(tr, mapping, Path(subset), lang=lang)
    with redirect_stdout(buf):
        rc = retypeset.retypeset(stripped, segments, tr, out)
    assert rc == 0, buf.getvalue()
    return src, out, tr, segments


JA = ['\u7533\u8acb\u8005\u306f\u672c\u65e5\u4e2d\u306b\u3053\u306e\u66f8\u985e\u3092\u63d0\u51fa\u3057\u3066\u304f\u3060\u3055\u3044\u3002',   # 申請者は本日中にこの書類を提出してください。
      '\u6307\u5b9a\u3055\u308c\u305f\u6b04\u306b\u6c0f\u540d\u3068\u4f4f\u6240\u3092\u8a18\u5165\u3057\u3066\u304f\u3060\u3055\u3044\u3002',   # 指定された欄に氏名と住所を記入してください。
      '\u624b\u7d9a\u304d\u306b\u306f\u7d04\u4e8c\u5341\u55b6\u696d\u65e5\u304b\u304b\u308a\u307e\u3059\u3002']                                # 手続きには約二十営業日かかります。
ZH = ['\u7533\u8bf7\u4eba\u5fc5\u987b\u5728\u4eca\u5929\u63d0\u4ea4\u6b64\u8868\u683c\u3002',                   # 申请人必须在今天提交此表格。
      '\u8bf7\u5728\u6307\u5b9a\u680f\u76ee\u4e2d\u586b\u5199\u59d3\u540d\u548c\u5730\u5740\u3002',             # 请在指定栏目中填写姓名和地址。
      '\u529e\u7406\u65f6\u95f4\u7ea6\u4e3a\u4e8c\u5341\u4e2a\u5de5\u4f5c\u65e5\u3002']                         # 办理时间约为二十个工作日。
DATE, NAME = '2026\u5e743\u670831\u65e5', '\u5c71\u7530\u592a\u90ce'                                          # 2026年3月31日, 山田太郎
KANA_NAME = '\u3084\u307e\u3060 \u305f\u308d\u3046'                                                            # やまだ たろう
TC_LINE = '\u7533\u8acb\u4eba\u5fc5\u9808\u5728\u4eca\u5929\u63d0\u4ea4\u6b64\u8868\u683c\u3002'                 # 申請人必須在今天提交此表格。
```

Append the class above the `if __name__` block:

```python
class LeakCjkGateTests(unittest.TestCase):
    """Gate 21 on deliveries built through the pipeline (sources drawn with the
    references instanced at wght 400, so the ink-ratio gate stays near 1)."""

    @classmethod
    def setUpClass(cls):
        _face(JP_FACE)
        _face(SC_FACE)
        cls.jp400 = han_forms.reference_face('JP', 400, FONTS)
        cls.sc400 = han_forms.reference_face('SC', 400, FONTS)
        cls.tmp = tempfile.TemporaryDirectory()

        def job(name, lines, src_face, out_face, lang):
            d = os.path.join(cls.tmp.name, name)
            os.mkdir(d)
            return build_cjk_delivery(d, lines, src_face, out_face, lang)

        cls.ja_zh_echo = job('ja-zh-echo', [(JA[0], ZH[0]), (JA[1], None), (DATE, DATE), (NAME, NAME), (JA[2], ZH[2])],
                             cls.jp400, cls.sc400, 'zh-Hans')
        cls.ja_zh_clean = job('ja-zh-clean', [(JA[0], ZH[0]), (JA[1], ZH[1]), (DATE, '2026\uf98e3\u670831\u65e5'), (NAME, NAME), (JA[2], ZH[2])],
                              cls.jp400, cls.sc400, 'zh-Hans')
        cls.ja_zh_kana = job('ja-zh-kana', [(JA[0], ZH[0]), (NAME, KANA_NAME), (JA[2], ZH[2])],
                             cls.jp400, cls.sc400, 'zh-Hans')
        cls.tc_ja = job('tc-ja', [(TC_LINE, JA[0]), (DATE, DATE)], cls.sc400, cls.jp400, 'ja')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def console(self, job, **kw):
        src, out, tr, segments = job
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = verify(src, out, translations=tr, segments=segments, min_ink=0.1, **kw)
        return rc, buf.getvalue().splitlines()

    def gates(self, job, **kw):
        src, out, tr, segments = job
        v = run_verify(src, out, translations=tr, segments=segments, min_ink=0.1, **kw)
        return v, {g.name: g for g in v.gates}

    def test_the_gate_is_named_after_leak_scan(self):
        self.assertEqual(GATE_NAMES[GATE_NAMES.index('leak-scan') + 1], 'leak-cjk')

    def test_an_echoed_japanese_segment_in_a_chinese_delivery_fails(self):
        rc, lines = self.console(self.ja_zh_echo)
        self.assertEqual(rc, 1, lines)
        head = [l for l in lines if l.startswith('FAIL leak scan (CJK tell): 1 line(s) carry characters that cannot belong to a Simplified Chinese target')]
        self.assertEqual(len(head), 1, lines)
        self.assertTrue(any(l.startswith('   p1: ' + JA[1][:20]) and '[14 tells:' in l for l in lines), lines)
        self.assertTrue(any(l == 'PASS leak scan: source and output share the spaceless CJK family; judged by the CJK tell (leak-cjk)' for l in lines), lines)
        self.assertFalse([l for l in lines if l.startswith('REVIEW leak scan: source and output share')], lines)
        v, g = self.gates(self.ja_zh_echo)
        self.assertEqual(g['leak-cjk'].status, 'FAIL', g['leak-cjk'])
        self.assertEqual([(f.page, f.where, f.text) for f in g['leak-cjk'].findings], [(1, 'line', JA[1])])
        self.assertEqual(g['leak-scan'].status, 'PASS')

    def test_a_clean_chinese_delivery_passes_with_the_date_the_name_and_a_drifted_target(self):
        rc, lines = self.console(self.ja_zh_clean)
        self.assertTrue(any(l.startswith('PASS leak scan (CJK tell): 5 line(s) hold only characters a Simplified Chinese target can carry') for l in lines), lines)
        v, g = self.gates(self.ja_zh_clean)
        self.assertEqual((g['leak-cjk'].status, g['leak-cjk'].findings), ('PASS', ()))
        self.assertNotIn('leak-cjk', [x.name for x in v.gates if x.status == 'FAIL'])

    def test_an_echoed_chinese_segment_in_a_japanese_delivery_fails(self):
        # The google/fonts Noto Sans JP lacks the Simplified-only glyphs (请 栏 东), so through the
        # pipeline an echo into it is refused at build (next test). A pan-CJK face draws it, and then
        # the tell must catch it — modelled with the SC face, which carries both scripts.
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)
        tw = pymupdf.TextWriter(page.rect)
        font = pymupdf.Font(fontfile=str(self.sc400))
        for i, text in enumerate((JA[0], ZH[1], DATE, JA[2])):
            tw.append((72, 100 + 40 * i), text, font=font, fontsize=12)
        tw.write_text(page)
        lines, status, findings = verify_mod.cjk_tell_report(doc, 'JP', set(), [], set())
        self.assertEqual(status, 'FAIL', lines)
        self.assertTrue(lines[0].startswith('FAIL leak scan (CJK tell): 1 line(s) carry characters that cannot belong to a Japanese target'), lines)
        self.assertEqual([(f.page, f.where, f.text) for f in findings], [(1, 'line', ZH[1])])

    def test_an_echoed_chinese_segment_into_the_japanese_face_is_refused_at_build(self):
        # retypeset's glyph guard refuses the job before verify could see it: Noto Sans JP has no
        # 请 (U+8BF7) or 栏 (U+680F). The gate covers faces that can draw both scripts.
        d = os.path.join(self.tmp.name, 'zh-ja-refused')
        os.mkdir(d)
        with self.assertRaises(AssertionError) as cm:
            build_cjk_delivery(d, [(ZH[0], JA[0]), (ZH[1], None)], self.sc400, self.jp400, 'ja')
        self.assertIn('cannot draw', str(cm.exception))
        self.assertIn('U+8BF7', str(cm.exception))

    def test_a_kana_name_fails_at_six_and_is_allowlisted_as_a_phrase(self):
        v, g = self.gates(self.ja_zh_kana)
        self.assertEqual(g['leak-cjk'].status, 'FAIL', g['leak-cjk'])
        self.assertEqual([f.text for f in g['leak-cjk'].findings], [KANA_NAME])
        v, g = self.gates(self.ja_zh_kana, allow=[KANA_NAME])
        self.assertEqual((g['leak-cjk'].status, g['leak-cjk'].findings), ('PASS', ()), g['leak-cjk'])
        _, lines = self.console(self.ja_zh_kana, allow=[KANA_NAME])
        self.assertTrue(any(l.startswith('note: 1 source-language run(s) kept') or 'kept' in l for l in lines), lines)

    def test_a_single_rare_character_is_review_not_fail(self):
        src, out, tr, segments = self.ja_zh_clean
        with pymupdf.open(out) as doc:
            page = doc[0]
            tw = pymupdf.TextWriter(page.rect)
            tw.append((72, 400), '\u9555', font=pymupdf.Font(fontfile=str(self.sc400)), fontsize=12)   # 镕: in no repertoire
            tw.write_text(page)
            rare = os.path.join(os.path.dirname(out), 'rare.pdf')
            doc.save(rare)
        v = run_verify(src, rare, translations=tr, segments=segments, min_ink=0.1)
        g = {x.name: x for x in v.gates}
        self.assertEqual(g['leak-cjk'].status, 'REVIEW', g['leak-cjk'])
        self.assertEqual([f.text for f in g['leak-cjk'].findings], ['\u9555'])

    def test_without_a_mapping_lang_the_old_review_line_stays(self):
        src, out, tr, segments = self.ja_zh_echo
        with open(tr, encoding='utf-8') as f:
            data = json.load(f)
        data.pop('lang', None)
        nolang = os.path.join(os.path.dirname(tr), 'nolang.json')
        with open(nolang, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        rc, lines = self.console((src, out, nolang, segments))
        self.assertIn('REVIEW leak scan: source and output share the spaceless CJK family; the scan cannot tell them apart. Rely on --translations and the visual pass.', lines)
        self.assertIn('   (CJK tell not applied: no lang in the mapping)', lines)
        v, g = self.gates((src, out, nolang, segments))
        self.assertNotIn('leak-cjk', g)
        self.assertEqual(g['leak-scan'].status, 'REVIEW')

    def test_a_traditional_source_into_japanese_is_the_weak_pair(self):
        rc, lines = self.console(self.tc_ja)
        self.assertIn('   (CJK tell not applied: the pair Traditional Chinese -> Japanese is not separable by repertoire (measured))', lines)
        v, g = self.gates(self.tc_ja)
        self.assertNotIn('leak-cjk', g)
        self.assertEqual(g['leak-scan'].status, 'REVIEW')

    def test_a_non_cjk_delivery_is_untouched(self):
        # The gate is inside the same_spaceless branch: a Latin job records nothing under leak-cjk.
        from tests.test_han_forms import build_delivery
        d = os.path.join(self.tmp.name, 'latin')
        os.mkdir(d)
        src, out, tr, _ = build_delivery(d, face=_face(FONTS / 'NotoSans-Regular.ttf'),
                                         target='El solicitante debe presentar este formulario hoy.',
                                         lang='es', instance=None)
        v, g = self.gates((src, out, tr, None))
        self.assertNotIn('leak-cjk', g)
```

(`self.gates((src, out, tr, None))` passes `segments=None`; `run_verify` accepts it.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONUTF8=1 C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe -m unittest tests.test_cjk_leak.LeakCjkGateTests -v > "C:/Users/rodri/AppData/Local/Temp/claude/C--Dev-pdf-translate-skill/f71acf3b-389c-49ff-881b-f6d3f7417505/scratchpad/leak-task2-red.log" 2>&1; grep -E "^(test_|Ran |OK|FAILED|ERROR)" ".../leak-task2-red.log"` (same path).
Expected: the fixtures build (about a minute); `test_the_gate_is_named_after_leak_scan` fails (`ValueError`/`IndexError`); the echo tests fail on exit code `0 != 1` and the missing FAIL line — **the echo verifying clean today is the point; keep that output**; the PASS, kana, rare and weak-pair tests fail with `KeyError: 'leak-cjk'`; the no-lang test fails on the missing reason line; the Latin test passes already (it pins what must not change) — expected for that one only. If `build_cjk_delivery` asserts on the segment count, print the extracted texts and report NEEDS_CONTEXT.

- [ ] **Step 3: Write the gate**

In `pdf-translate/pdf_translate/verify.py`:

(a) The import line: `from . import han_forms, shaping_probe` → `from . import cjk_tell, han_forms, shaping_probe`.

(b) `GATE_NAMES`: `'leak-scan', 'leak-running', 'leak-isolated',` → `'leak-scan', 'leak-cjk', 'leak-running', 'leak-isolated',`.

(c) After `kinsoku_report` (before `han_forms_report`), add:

```python
def cjk_tell_report(doc, convention, keep, kept, allow):
    """(lines, status, findings) for gate 21: every drawn line of the output
    that carries characters which cannot belong to the target convention
    (cjk_tell.tells_in). Kept runs (the original's /Title, multi-word --allow
    phrases) are skipped; single --allow tokens are removed before counting.
    A line with cjk_tell.LINE_FAIL or more tells is FAIL (an echoed sentence
    carries 9–56), one to five REVIEW (a name in kana, a rare character);
    status FAIL > REVIEW > PASS; one Finding(page, 'line', text) per line."""
    name = cjk_tell.REPERTOIRE[convention][0]
    hits, judged = [], 0
    for page in doc:
        for text, *_ in _page_lines(page):
            if _kept(text, keep, kept, 'CJK'):
                continue
            judged += 1
            tells = cjk_tell.tells_in(cjk_tell.strip_allowed(text, allow), convention)
            if tells:
                hits.append((page.number + 1, text, tells))
    if not hits:
        return ([f'PASS leak scan (CJK tell): {judged} line(s) hold only characters a {name} '
                 f'target can carry'], 'PASS', [])
    worst = max(len(t) for _, _, t in hits)
    if worst >= cjk_tell.LINE_FAIL:
        other = {'JP': 'Chinese', 'SC': 'Japanese', 'TC': 'Japanese or Simplified Chinese'}
        head = (f'FAIL leak scan (CJK tell): {len(hits)} line(s) carry characters that cannot '
                f'belong to a {name} target — untranslated {other[convention]} text:')
        status = 'FAIL'
    else:
        head = (f'REVIEW leak scan (CJK tell): {len(hits)} line(s) carry a few characters that '
                f'cannot belong to a {name} target (a name in kana, a rare character — allowlist '
                f'with --allow):')
        status = 'REVIEW'
    lines = [head]
    for pno, text, tells in hits[:20]:
        lines.append(f'   p{pno}: {text[:60]}  [{len(tells)} tells: {"".join(tells)[:12]}]')
    return lines, status, [Finding(pno, 'line', text) for pno, text, _ in hits]
```

Note: `other[convention]` for `'JP'` reads `Chinese` because a JP target's tells are Han outside the Japanese repertoire — Simplified or Traditional.

(d) In `_execute_verify`, replace the `same_spaceless` branch

```python
    if same_spaceless:
        print(f'REVIEW leak scan: source and output share the spaceless {src_script} '
              f'family; the scan cannot tell them apart. Rely on --translations and '
              f'the visual pass.')
        record('leak-scan', 'REVIEW',
               f'source and output share the spaceless {src_script} family',
               findings=[Finding(None, 'script', src_script)])
```

with

```python
    if same_spaceless:
        target_conv = han_forms.convention_for_lang(mapping_lang)
        source_conv = cjk_tell.convention_of(o_text)
        if not mapping_lang:
            why = 'no lang in the mapping'
        elif target_conv not in cjk_tell.REPERTOIRE:
            why = f'lang "{mapping_lang}" names no Han convention'
        elif source_conv is None:
            why = 'the source\'s convention is not clear'
        elif (source_conv, target_conv) not in cjk_tell.STRONG_PAIRS:
            why = (f'the pair {cjk_tell.REPERTOIRE[source_conv][0]} -> '
                   f'{cjk_tell.REPERTOIRE[target_conv][0]} is not separable by repertoire (measured)')
        else:
            why = None
        if why is None:
            tell_lines, tell_status, tell_findings = cjk_tell_report(jc, target_conv, keep, kept, allow)
            for line in tell_lines:
                print(line)
            if tell_status == 'FAIL':
                fail = 1
            record('leak-cjk', tell_status, f'{len(tell_findings)} line(s)' if tell_findings else '',
                   findings=tell_findings)
            print(f'PASS leak scan: source and output share the spaceless {src_script} family; '
                  f'judged by the CJK tell (leak-cjk)')
            record('leak-scan', 'PASS', 'judged by leak-cjk')
        else:
            print(f'REVIEW leak scan: source and output share the spaceless {src_script} '
                  f'family; the scan cannot tell them apart. Rely on --translations and '
                  f'the visual pass.')
            print(f'   (CJK tell not applied: {why})')
            record('leak-scan', 'REVIEW',
                   f'source and output share the spaceless {src_script} family',
                   findings=[Finding(None, 'script', src_script)])
```

`mapping_lang`, `keep`, `kept`, `allow`, `o_text` and `jc` are all in scope at that point (`mapping_lang` is set just above for the han-forms block). Note `allow` there is the set of single-word entries (lower-cased; CJK has no case), and `keep` the phrases — exactly what `strip_allowed` and `_kept` need.

(e) The module docstring: in entry `4. leak scan`, replace `A shared spaceless family (zh->ja) gets one REVIEW line, not a gate.` with `A shared spaceless family (zh->ja) is judged by gate 21 when the mapping's lang names the target; else one REVIEW line.` and add after the `20. han forms` entry, same indentation:

```
21. leak-cjk      when source and output share the spaceless CJK family and
                  the mapping's lang names a Han convention (ja, zh-Hans,
                  zh-Hant), every drawn line is scanned for characters that
                  cannot belong to that target — kana in a Chinese one, Han
                  outside its repertoire (cp932 / GB 2312 / Big5), NFKC
                  first. Six or more in a line FAIL (an echoed sentence),
                  one to five REVIEW (a name in kana, a rare character —
                  allowlist with --allow). The source's convention is read
                  the same way; Traditional Chinese -> Japanese is not
                  separable and keeps the REVIEW line. Kept runs and the
                  original's /Title are skipped.
```

- [ ] **Step 4: Run the tests to verify they pass**

Run the module (log to `leak-task2-green.log`): expected 8 + 9 = 17 tests, `OK`.

- [ ] **Step 5: Console parity against `main` on the nine non-CJK jobs**

Exactly the commands of `docs/plans/2026-09-16-han-forms-gate.md` Task 3 Step 5 (from the repo root; `$S` = the scratchpad `parity` directory; refresh `main`'s archive; runner outputs to `console_leak.txt` / `verdict_leak.txt`). Expected: two different `# package:` lines, `CONSOLE IDENTICAL`, `VERDICTS IDENTICAL`.

- [ ] **Step 6: The full suite as CI runs it**

From `pdf-translate/`: `… -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report tests.test_cjk tests.test_han_forms tests.test_cjk_leak` (log to `leak-suite-task2.log`). Expected `OK`, 370 + 17 = 387. A pre-existing test that asserts the exact old REVIEW line on a CJK ↔ CJK job without `lang` now also sees the indented reason line — extend its expectation; never loosen it to "contains". If `tests.test_import_surface.VerdictCompletenessTests` goes red, the record site prints and records differently — fix the code.

- [ ] **Step 7: Evidence**

Append to the evidence doc a `## Task 2 — the gate, red then green` section: the red lines for the two echo tests (the echo verifying clean today), the green `Ran`/`OK` with names, the parity lines, the suite line. No `<…>` placeholder may remain.

- [ ] **Step 8: Commit**

```bash
git add pdf-translate/pdf_translate/verify.py pdf-translate/tests/test_cjk_leak.py docs/reviews/2026-09-16-leak-cjk-gate.md
git diff --cached --check
git commit -m "feat(pdf-translate): gate 21 leak-cjk — characters that cannot belong to the target language are the leak in a CJK-to-CJK job"
```

---

### Task 3: docs, version 55, CI

**Files:**
- Modify: `.github/workflows/tests.yml` (suite line gains ` tests.test_cjk_leak` after ` tests.test_han_forms`)
- Modify: version 54 → 55 in `pdf-translate/SKILL.md` (`version: "55"`), `.claude-plugin/plugin.json` (`55.0.0`), `pdf-translate/pyproject.toml` (`55.0.0`), `pdf-translate/pdf_translate/__init__.py` (`'55'`), `pdf-translate/tests/test_verify_report.py` (lockstep literal `'55'`; red first at '55' against the four sources)
- Modify: `pdf-translate/README.md` (`twenty structural gates` → `twenty-one structural gates`)
- Modify: `pdf-translate/SKILL.md` — the Leak scan bullet: replace `ZH↔JA: one REVIEW line, no gate; lean on \`--translations\` and the visual pass.` with `ZH↔JA: when the mapping's \`lang\` names the target, gate 21 scans every drawn line for characters that cannot belong to it (kana in a Chinese target; Han outside its repertoire) — six or more in a line FAIL, fewer REVIEW, a name in kana allowlisted with \`--allow\`; without \`lang\`, or for a Traditional Chinese source into Japanese, one REVIEW line remains.`
- Modify: `pdf-translate/references/gates.md` — (a) in "The leak scan", replace `When both sides share a spaceless family (ZH↔JA) the scan prints one REVIEW line and cannot gate; lean on \`--translations\` and the visual pass.` with: `When both sides share a spaceless family (ZH↔JA) and the mapping's \`lang\` names a Han convention, gate 21 \`leak-cjk\` judges every drawn line by the characters that cannot belong to the target — kana in a Chinese target, Han outside its repertoire (cp932 for Japanese, GB 2312 for Simplified, Big5 for Traditional Chinese), NFKC-folded first because a source's ToUnicode drift travels through an authored mapping. Six or more in a line FAIL (an echoed, untranslated sentence carries nine to fifty); one to five REVIEW (a name in kana, a rare character — \`--allow\` the name). The source's convention is read the same way and only measured pairs are judged; a Traditional Chinese source into Japanese is not separable by repertoire and keeps the one REVIEW line, as does a job with no \`lang\`. Measured: \`docs/BRIEF-cjk-leak-tell.md\`.`; (b) the name list: `leak-scan, leak-running,` → `leak-scan, leak-cjk, leak-running,`; (c) the `where`/`text` table, after the leak-scan row: `| leak-cjk | \`line\` | the drawn line |`; (d) the leak-scan row's `text` cell: `the spaceless family source and output share (\`CJK\`)` stays — add ` (REVIEW only when the tell cannot run; PASS \`judged by leak-cjk\` otherwise)`.
- Modify: `docs/DECISIONS.md` — append after the han-forms row:

```markdown
| 2026-09-16 | Gate 21 `leak-cjk`: when source and output share the spaceless CJK family and the mapping's `lang` names a Han convention, every drawn line of the output is scanned for characters that cannot belong to the target — kana in a Chinese target; Han outside the target's repertoire, cp932 for Japanese, GB 2312 for Simplified Chinese, Big5 for Traditional Chinese — after NFKC folding; six or more in a line FAIL, one to five REVIEW, one `Finding(page, 'line', text)` per line; kept runs and single `--allow` tokens excluded. The source's convention is read with the same tells and only measured pairs are judged (JP→SC, JP→TC, SC→JP, SC→TC, TC→SC); TC→JP, no `lang`, or an unclear source keep the old one-line REVIEW with the reason. The brief's verbatim rule is not built. Version 54 → 55. | Task F said "measure first": `dev/probes/cjk_leak_tell_probe.py`, `docs/BRIEF-cjk-leak-tell.md` (PyMuPDF 1.28.2). `retypeset` refuses an omitted segment, so the leak that ships is an echo (target == source), which a verbatim rule cannot see by construction — measured on a real ja → zh-Hans delivery, it found nothing. The repertoire tell has zero false tells on eleven own-language texts including `corpus/ja_source.pdf` and 3–56 on the other language's; it found the echoed line with 14 tells; raw it also flagged a date and a name whose 年 and 郎 the source's ToUnicode had drifted to U+F98E and U+F92C — NFKC folds them. TC → JP measured one tell in 38 letters (JIS X 0208 carries most traditional forms): weak, so REVIEW. Into a Japanese face from google/fonts an echoed Simplified sentence never reaches verify — Noto Sans JP lacks 请 栏 东 and `retypeset`'s glyph guard refuses the job (`test_an_echoed_chinese_segment_into_the_japanese_face_is_refused_at_build`); the gate's ja-target direction covers faces that draw both scripts (a pan-CJK Noto Sans CJK). Console output of non-CJK jobs is byte-identical (parity runner, nine jobs). | A Japanese or Chinese document of the target language that carries six or more repertoire tells in one drawn line for a legitimate reason other than a kana name (that would argue for a higher bound or a wider repertoire, measured on that document); a source whose convention the tells cannot name in practice (mixed-region documents), which would argue for taking the source convention from a declared source `lang` instead; or a measured tell for TC → JP. |
```

- Modify: `docs/BRIEF-unattended-delivery.md` — the Task F header gains ` (built as gate 21, v55 — see docs/BRIEF-cjk-leak-tell.md)`.
- Modify: `docs/REQUESTS-from-product.md` — the E2 row's status: replace `— push and PR are the operator's; task F open.` with `— merged 2026-09-16 (PR #8); task F built as gate 21 \`leak-cjk\` (v55, \`feat/cjk-leak-tell\`, measured in \`docs/BRIEF-cjk-leak-tell.md\`: the verbatim rule is blind to an echo, a repertoire tell is not) — push and PR are the operator's.`
- Modify: `docs/reviews/2026-09-16-leak-cjk-gate.md` — append `## Docs and version` (one paragraph naming the edits) and `## Review` (left for the reviewer's verdict line — the controller fills it after the whole-branch review).

Steps: the lockstep red then green; each edit at its anchor (grep first; report NEEDS_CONTEXT if an anchor is missing); the eight-module suite once more (expect 387 OK); commit `docs(pdf-translate): gate 21 leak-cjk in SKILL.md, gates.md and README; DECISIONS row; task F closed; version 55`.

---

## After the tasks

1. Whole-branch review on the most capable model (`scripts/review-package $(git merge-base main HEAD) HEAD`), Minor findings from the task reviews handed to it for triage. Not a rendering change: no Rule 1 verifier; the reviewer's real-run re-check of the echo cases is the independent pass.
2. The controller fills `## Review` in the evidence doc, reports to the operator; push and PR are the operator's.

## Self-review

- Spec coverage (brief §4 design, §4 acceptance): the table exact → Task 1; the judge, deliveries (echo both ways, clean with a drifted target, kana name and `--allow`, rare character REVIEW, no `lang`, weak pair, Latin untouched), parity, the findings invariant → Task 2; docs, version 55, the E2 and Task F status lines → Task 3. The brief's "a zh-Hant source into ja → the old REVIEW with the weak-pair reason" → `test_a_traditional_source_into_japanese_is_the_weak_pair`.
- Placeholders: the evidence doc's `<paste …>` markers are instructions to paste real output; no code step lacks its code.
- Type consistency: `tells_in` returns a list of characters (Tasks 1–2); `cjk_tell_report(doc, convention, keep, kept, allow)` matches its one call site; `build_cjk_delivery` returns `(orig, out, translations, segments)` and the tests unpack four; `Finding(page, 'line', text)` as the constraints say.
