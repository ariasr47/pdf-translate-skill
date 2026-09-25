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
from pdf_translate.verify import GATE_NAMES, run_verify, verify
from tests import _instancing

# Deliveries and prepare_font runs here instance the same few CJK faces again
# and again; each distinct instance is built once (R-51).
setUpModule, tearDownModule = _instancing.install, _instancing.uninstall

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


def build_cjk_source(path, text, fontfile):
    """An original whose one line of CJK text is drawn with fontfile (embedded)."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    tw = pymupdf.TextWriter(page.rect)
    tw.append((72, 100), text, font=pymupdf.Font(fontfile=str(fontfile)), fontsize=12)
    tw.write_text(page)
    doc.save(path)
    doc.close()


def build_delivery(tmp, face, target, lang, instance='wght=400', prepare_lang=None, source=None):
    """A real delivery: orig -> extract -> strip -> prepare_font(face, instance)
    -> retypeset. prepare_font sees a mapping with prepare_lang (None: no lang,
    so its own han-forms check stays quiet); retypeset sees lang, which it
    writes as /Lang. source=(text, fontfile), when given, builds the original
    with text drawn in fontfile (build_cjk_source) instead of the plain Latin
    fixture, and text is the mapping key instead of SOURCE_SENTENCE. Returns
    (orig, out, translations, subset)."""
    from tests.test_pipeline import (SOURCE_SENTENCE, build_plain_pdf, extract_segments,
                                     prepare_font, retypeset, strip_text, write_mapping)
    src, stripped, out = (os.path.join(tmp, n) for n in ('orig.pdf', 'stripped.pdf', 'out.pdf'))
    tr, subset = os.path.join(tmp, 'translations.json'), os.path.join(tmp, 'subset.ttf')
    if source:
        core, src_fontfile = source
        build_cjk_source(src, core, src_fontfile)
    else:
        core = SOURCE_SENTENCE
        build_plain_pdf(src)
    extract_segments.extract_segments(src, outdir=tmp)
    strip_text.strip_text(src, stripped)
    write_mapping(tr, {core: target}, Path(face), lang=prepare_lang)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = prepare_font.prepare_font(str(face), tr, subset, instance=instance)
    assert rc == 0, buf.getvalue()
    write_mapping(tr, {core: target}, Path(subset), lang=lang)
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
                 None: None, 'jpn': 'JP', 'zho': 'SC', 'kor': 'KR', 'Japanese': None,
                 '日本語': None}
        for lang, want in cases.items():
            self.assertEqual(han_forms.convention_for_lang(lang), want, lang)

    def test_is_language_tag(self):
        for tag in ('ja', 'ja-JP', 'zh-Hans', 'zh_Hans_CN', 'es-MX', 'jpn', 'en-US-x-private'):
            self.assertTrue(han_forms.is_language_tag(tag), tag)
        for bad in ('Japanese', '日本語', 'j', 'ja-', '-ja', 'ja--JP', '', None, 'Japanese (JP)'):
            self.assertFalse(han_forms.is_language_tag(bad), bad)

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


def _subset(src, text, out):
    """A subset of src carrying only text (fontTools), for a program that lacks probes."""
    from fontTools import subset
    options = subset.Options()
    font = subset.load_font(str(src), options)
    try:
        subsetter = subset.Subsetter(options)
        subsetter.populate(text=text)
        subsetter.subset(font)
        subset.save_font(font, str(out), options)
    finally:
        font.close()


class JudgeTests(unittest.TestCase):
    """judge_program on the references themselves, a Latin face, a probe-less
    subset and another family. Status and line shape."""

    @classmethod
    def setUpClass(cls):
        _face(JP_FACE)
        _face(SC_FACE)
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


class VerifyGateTests(unittest.TestCase):
    """Gate 20 on deliveries built through the pipeline. Five deliveries, once
    per class; about a minute on first run (prepare_font instances the
    variable face for each)."""

    @classmethod
    def setUpClass(cls):
        _face(JP_FACE)
        _face(SC_FACE)
        cls.tmp = tempfile.TemporaryDirectory()

        def job(name, **kw):
            d = os.path.join(cls.tmp.name, name)
            os.mkdir(d)
            return build_delivery(d, **kw)

        cls.ja_jp = job('ja-jp', face=JP_FACE, target=TARGET, lang='ja')
        cls.ja_sc = job('ja-sc', face=SC_FACE, target=TARGET, lang='ja')
        cls.nolang = job('nolang', face=JP_FACE, target=TARGET, lang=None)
        # A subset built before this version, or by another tool: no probe glyphs.
        with mock.patch.object(han_forms, 'HAN_CHARS', ''):
            cls.plain = job('plain', face=JP_FACE, target=PLAIN, lang='ja')
        cls.bold = job('bold', face=JP_FACE, target=TARGET, lang='ja', instance='wght=700')
        # strip_text leaves the source's Simplified Chinese face in the page resources.
        cls.zh_ja = job('zh-ja', face=JP_FACE, target=TARGET, lang='ja',
                        source=('\u7533\u8bf7\u4e66', SC_FACE))

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

    def test_a_chinese_source_translated_to_japanese_passes(self):
        # strip_text leaves the source's Simplified Chinese face in the page resources.
        src, out, tr, _ = self.zh_ja
        with pymupdf.open(out) as doc:
            names = {f[3] for f in doc[0].get_fonts(full=True)}
        self.assertTrue(any('SC' in n.replace(' ', '') for n in names), names)
        rc, gate = self.gate(self.zh_ja)
        self.assertEqual(gate.status, 'PASS', gate)
        self.assertFalse([g for g in [gate] if g.status == 'FAIL'])
        _, lines = self.console(self.zh_ja)
        self.assertFalse([l for l in lines if l.startswith('FAIL han-forms')], lines)

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

    def test_a_lang_that_is_not_a_tag_is_review_not_silence(self):
        # A display name is what a consumer's workbench most often holds; it must not pass unnoticed.
        for label in ('Japanese', '日本語'):
            src, out, tr, _ = _with_lang(self.ja_jp, label, 'label.json')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            gate = [g for g in v.gates if g.name == 'han-forms'][0]
            self.assertEqual(gate.status, 'REVIEW', (label, gate))
            self.assertEqual(gate.findings[0].where, 'lang')
            self.assertIn(f'lang "{label}" is not a language tag', gate.findings[0].text)
        _, lines = self.console(_with_lang(self.ja_jp, 'Japanese', 'label.json'))
        self.assertTrue(any(l.startswith('REVIEW han-forms: lang "Japanese" is not a language tag') for l in lines), lines)

    def test_a_stale_non_cjk_output_lang_is_review_not_silence(self):
        # No mapping; the output's /Lang says en (the original's, never updated) while the page draws Japanese.
        src, out, _, _ = self.ja_jp
        stale = os.path.join(os.path.dirname(out), 'stale-lang.pdf')
        with pymupdf.open(out) as doc:
            doc.set_language('en')
            doc.save(stale)
        v = run_verify(src, stale, min_ink=0.1)
        gate = [g for g in v.gates if g.name == 'han-forms'][0]
        self.assertEqual(gate.status, 'REVIEW', gate)
        self.assertEqual(gate.findings[0].where, 'lang')
        self.assertIn('/Lang "en"', gate.findings[0].text)

    def test_a_subset_without_the_probes_is_review_cannot_attest(self):
        rc, gate = self.gate(self.plain)
        self.assertEqual((rc, gate.status), (0, 'REVIEW'), gate)
        self.assertEqual(gate.findings[0].where, 'JP')
        self.assertIn('cannot attest:', gate.findings[0].text)
        self.assertIn('carries none of the probes "\u76f4\u9aa8\u6d77\u6771"', gate.findings[0].text)
        _, lines = self.console(self.plain)
        self.assertTrue(any(l.startswith('REVIEW han-forms Japanese: cannot attest [page 1]: ')
                            for l in lines), lines)
        self.assertTrue(any('carries none of the probes "\u76f4\u9aa8\u6d77\u6771"' in l
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


def _without_timestamp(path):
    """A font's bytes with head.modified zeroed: the one field two builds of
    the same subset differ in."""
    from fontTools.ttLib import TTFont
    with TTFont(path) as font:
        font['head'].modified = 0
        buffer = io.BytesIO()
        font.save(buffer)
    return buffer.getvalue()


class InstancingTests(unittest.TestCase):
    """R-51: a face this module instances is built once, however many tests
    ask for it, and the subset prepare_font writes from it is the same."""

    def prepare(self):
        from tests.test_pipeline import SOURCE_SENTENCE, prepare_font, write_mapping
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        tr, out = os.path.join(tmp, 'translations.json'), os.path.join(tmp, 'subset.ttf')
        write_mapping(tr, {SOURCE_SENTENCE: TARGET}, _face(JP_FACE), lang=None)
        with redirect_stdout(io.StringIO()):
            rc = prepare_font.prepare_font(str(JP_FACE), tr, out, instance='wght=400')
        self.assertEqual(rc, 0)
        return out

    def test_a_repeated_instance_runs_the_instancer_at_most_once(self):
        from fontTools.varLib import instancer
        runs = []
        real = instancer.instantiateFvar

        def counted(*args, **kwargs):
            runs.append(args[1])
            return real(*args, **kwargs)

        # instantiateFvar runs once inside every real instancing, whatever
        # wraps instantiateVariableFont; an earlier test may already have
        # built this instance, so none is as right as one.
        with mock.patch.object(instancer, 'instantiateFvar', counted):
            first, second = self.prepare(), self.prepare()
        self.assertLessEqual(len(runs), 1, runs)
        self.assertEqual(_without_timestamp(first), _without_timestamp(second))


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

    def test_another_family_is_reviewed_not_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            droid = os.path.join(tmp, 'droid.ttf')
            with open(droid, 'wb') as f:
                f.write(pymupdf.Font('cjk').buffer)
            rc, log, _ = self.prepare(Path(droid), TARGET, 'ja', instance=None)
        self.assertEqual(rc, 0, log)
        self.assertIn('REVIEW han-forms Japanese: no reference of this family', log)
        self.assertIn('OK:', log)


def _page_with(drawn, latin_face=None, unused_face=None):
    """A page whose CJK text is drawn by `drawn`; optionally another face that
    draws only Latin, and another that is embedded but draws nothing (what
    strip_text leaves behind from the source document)."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    tw = pymupdf.TextWriter(page.rect)
    tw.append((60, 100), PLAIN, font=pymupdf.Font(fontfile=str(drawn)), fontsize=12)
    if latin_face:
        tw.append((60, 140), 'Hello', font=pymupdf.Font(fontfile=str(latin_face)), fontsize=12)
    tw.write_text(page)
    if unused_face:
        page.insert_font(fontname='Leftover', fontfile=str(unused_face))
    return doc


class AttributionTests(unittest.TestCase):
    """Only the faces that drew the page's CJK glyphs are judged; a face that is
    embedded but drew none neither fails the page nor attests it (the final
    review's Critical 1, reproduced both ways)."""

    @classmethod
    def setUpClass(cls):
        _face(JP_FACE)
        _face(SC_FACE)
        cls.jp400 = han_forms.reference_face('JP', 400, FONTS)
        cls.sc400 = han_forms.reference_face('SC', 400, FONTS)

    def report(self, doc, lang='ja'):
        return verify_mod.han_forms_report(doc, lang, '', FONTS)

    def test_an_unused_chinese_face_does_not_fail_a_japanese_page(self):
        # The source's face survives strip_text in the resources; the Japanese face drew every glyph.
        doc = _page_with(drawn=self.jp400, unused_face=self.sc400)
        names = {f[3] for f in doc[0].get_fonts(full=True)}
        self.assertEqual(len(names), 2, names)
        lines, status, findings = self.report(doc)
        self.assertEqual(status, 'PASS', lines)
        self.assertFalse([l for l in lines if l.startswith('FAIL')], lines)
        self.assertEqual(len(findings), 1, findings)
        self.assertTrue(han_forms.font_key(findings[0].where).startswith('notosansjp'), findings)

    def test_a_chinese_face_that_drew_only_latin_does_not_fail_a_japanese_page(self):
        doc = _page_with(drawn=self.jp400, latin_face=self.sc400)
        lines, status, findings = self.report(doc)
        self.assertEqual(status, 'PASS', lines)
        self.assertFalse([l for l in lines if l.startswith('FAIL')], lines)

    def test_a_probeless_face_that_drew_the_japanese_cannot_hide_behind_another_face(self):
        with tempfile.TemporaryDirectory() as tmp:
            thin = os.path.join(tmp, 'sc-no-probes.ttf')
            _subset(self.sc400, PLAIN, thin)
            doc = _page_with(drawn=thin, latin_face=self.jp400)
            lines, status, findings = self.report(doc)
        self.assertEqual(status, 'REVIEW', lines)
        self.assertFalse([l for l in lines if l.startswith('PASS')], lines)
        self.assertTrue(any('cannot attest' in l for l in lines), lines)
        self.assertEqual(findings[0].where, 'JP', findings)

    def test_a_chinese_face_that_drew_the_japanese_fails_even_beside_a_japanese_face(self):
        doc = _page_with(drawn=self.sc400, latin_face=self.jp400)
        lines, status, findings = self.report(doc)
        self.assertEqual(status, 'FAIL', lines)
        self.assertEqual(len([l for l in lines if l.startswith('FAIL')]), 1, lines)
        self.assertFalse([l for l in lines if l.startswith('PASS')], lines)

    def test_a_probeless_drawing_face_is_reported_even_when_another_face_attests(self):
        # 申請書を提出 in a probe-less Chinese subset, 直骨海東京 in the Japanese face: the
        # Japanese face passes, and the Chinese one must still surface.
        with tempfile.TemporaryDirectory() as tmp:
            thin = os.path.join(tmp, 'sc-no-probes.ttf')
            _subset(self.sc400, PLAIN, thin)
            doc = pymupdf.open()
            page = doc.new_page(width=595, height=842)
            tw = pymupdf.TextWriter(page.rect)
            tw.append((60, 100), PLAIN, font=pymupdf.Font(fontfile=thin), fontsize=12)
            tw.append((60, 140), TARGET, font=pymupdf.Font(fontfile=str(self.jp400)), fontsize=12)
            tw.write_text(page)
            lines, status, findings = self.report(doc)
        self.assertEqual(status, 'REVIEW', lines)
        self.assertTrue(any(l.startswith('PASS han-forms Japanese: ') for l in lines), lines)
        self.assertTrue(any('cannot attest' in l and 'carries none of the probes' in l for l in lines), lines)
        self.assertIn('JP', [f.where for f in findings])

    def test_an_unnamed_span_font_is_cannot_attest_not_silence(self):
        doc = _page_with(drawn=self.jp400)
        with mock.patch.object(verify_mod, '_cjk_drawing_fonts', return_value=(True, set())):
            lines, status, findings = self.report(doc)
        self.assertEqual(status, 'REVIEW', lines)
        self.assertTrue(any('cannot attest' in l and 'an unnamed font' in l for l in lines), lines)
        self.assertEqual(findings[0].where, 'JP')

    def test_a_span_without_a_font_name_contributes_the_unnamed_key(self):
        # MuPDF names every span it draws; a nameless one must still count as a CJK drawer.
        class FakePage:
            def get_text(self, kind):
                return {'blocks': [{'lines': [{'spans': [
                    {'font': '', 'chars': [{'c': '申'}]},
                    {'font': 'NotoSansJP-Regular', 'chars': [{'c': '請'}]},
                    {'font': 'Helvetica', 'chars': [{'c': 'a'}]},
                ]}]}]}
        draws, keys = verify_mod._cjk_drawing_fonts(FakePage())
        self.assertTrue(draws)
        self.assertEqual(keys, {'notosansjpregular', 'an unnamed font'})

    def test_an_unnamed_drawer_beside_a_named_face_is_reported(self):
        doc = _page_with(drawn=self.jp400)
        _, keys = verify_mod._cjk_drawing_fonts(doc[0])
        with mock.patch.object(verify_mod, '_cjk_drawing_fonts',
                               return_value=(True, keys | {'an unnamed font'})):
            lines, status, findings = self.report(doc)
        self.assertEqual(status, 'REVIEW', lines)
        self.assertTrue(any(l.startswith('PASS han-forms Japanese: ') for l in lines), lines)
        self.assertTrue(any('cannot attest' in l and 'an unnamed font' in l for l in lines), lines)


if __name__ == '__main__':
    unittest.main()
