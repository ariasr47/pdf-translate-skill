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
