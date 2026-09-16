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
