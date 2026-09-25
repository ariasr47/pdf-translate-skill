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
import unicodedata
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf

from pdf_translate import cjk_tell, han_forms
from tests import _instancing
from tests.test_han_forms import FONTS, JP_FACE, SC_FACE, _face

verify_mod = importlib.import_module('pdf_translate.verify')
from pdf_translate.verify import GATE_NAMES, run_verify, verify

# The han-forms references this module instances are the faces test_han_forms
# asks for next; built once for both (R-51).
setUpModule, tearDownModule = _instancing.install, _instancing.uninstall

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


JA = ['申請者は本日中にこの書類を提出してください。',
      '指定された欄に氏名と住所を記入してください。',
      '手続きには約二十営業日かかります。']
ZH = ['申请人必须在今天提交此表格。',
      '请在指定栏目中填写姓名和地址。',
      '办理时间约为二十个工作日。']
DATE, NAME = '2026年3月31日', '山田太郎'
KANA_NAME = 'やまだ たろう'
# A single Traditional sentence has no tell for Japanese or Traditional (請 須 are in both repertoires)
# and is ambiguous; the two-sentence text of the table, measured (1, 11, 0), names TC.
TC_PARA = TEXTS[8][1]
# A one-sentence Simplified echo into Japanese carries 2 tells (请 栏) — REVIEW; the table's
# paragraph 2 carries 16 — FAIL.
ZH_PARA = TEXTS[5][1]


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
        self.assertEqual(cjk_tell.strip_allowed('Nintendo\u30b9\u30a4\u30c3\u30c1\u767a\u58f2', {'nintendo\u30b9\u30a4\u30c3\u30c1'}), '\u767a\u58f2')


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
        cls.ja_zh_clean = job('ja-zh-clean', [(JA[0], ZH[0]), (JA[1], ZH[1]), (DATE, '2026年3月31日'), (NAME, NAME), (JA[2], ZH[2])],
                              cls.jp400, cls.sc400, 'zh-Hans')
        cls.ja_zh_kana = job('ja-zh-kana', [(JA[0], ZH[0]), (NAME, KANA_NAME), (JA[2], ZH[2])],
                             cls.jp400, cls.sc400, 'zh-Hans')
        cls.tc_ja = job('tc-ja', [(TC_PARA, JA[0]), (DATE, DATE)], cls.sc400, cls.jp400, 'ja')

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
        head = [l for l in lines if l.startswith('FAIL leak scan (CJK tell): 1 line(s) carry characters that cannot belong to a Simplified Chinese target — untranslated Japanese text, or a proper noun to allowlist with --allow:')]
        self.assertEqual(len(head), 1, lines)
        self.assertTrue(any(l.startswith('   p1: ' + JA[1][:20]) and '[14 tells:' in l for l in lines), lines)
        self.assertTrue(any(l == 'SKIP leak scan: source and output share the spaceless CJK family; judged by the CJK tell (leak-cjk) — a line of Han both languages share is invisible to the tell; lean on --translations and the visual pass' for l in lines), lines)
        self.assertFalse([l for l in lines if l.startswith('REVIEW leak scan: source and output share')], lines)
        self.assertNotIn('PASS no untranslated running text', lines)
        self.assertNotIn('PASS isolated source-script tokens: none', lines)
        v, g = self.gates(self.ja_zh_echo)
        self.assertEqual(g['leak-cjk'].status, 'FAIL', g['leak-cjk'])
        self.assertEqual([(f.page, f.where, f.text) for f in g['leak-cjk'].findings], [(1, 'line', JA[1])])
        self.assertEqual(g['leak-scan'].status, 'SKIP')
        self.assertNotIn('leak-running', g)
        self.assertNotIn('leak-isolated', g)

    def test_a_clean_chinese_delivery_passes_with_the_date_the_name_and_a_drifted_target(self):
        rc, lines = self.console(self.ja_zh_clean)
        self.assertIn('PASS leak scan (CJK tell): 5 line(s) hold only characters a Simplified Chinese target can carry; a line of Han both languages share is invisible to the tell', lines)
        v, g = self.gates(self.ja_zh_clean)
        self.assertEqual((g['leak-cjk'].status, g['leak-cjk'].findings), ('PASS', ()))
        self.assertNotIn('leak-cjk', [x.name for x in v.gates if x.status == 'FAIL'])

    def test_an_echoed_chinese_segment_in_a_japanese_delivery_fails(self):
        # The google/fonts Noto Sans JP lacks the Simplified-only glyphs (请 栏 东), so through the
        # pipeline an echo into it is refused at build (next test). A pan-CJK face draws it, and then
        # the tell must catch it — modelled with the SC face, which carries both scripts.
        def page_with(echo):
            # Landscape: the paragraph is 624 pt wide at 12 pt, and MuPDF's text layer holds
            # only what lies on the page.
            doc = pymupdf.open()
            page = doc.new_page(width=842, height=595)
            tw = pymupdf.TextWriter(page.rect)
            font = pymupdf.Font(fontfile=str(self.sc400))
            for i, text in enumerate((JA[0], echo, DATE, JA[2])):
                tw.append((72, 100 + 40 * i), text, font=font, fontsize=12)
            tw.write_text(page)
            return doc

        lines, status, findings = verify_mod.cjk_tell_report(page_with(ZH_PARA), 'JP', set(), [], set(), source='SC')
        self.assertEqual(status, 'FAIL', lines)
        self.assertTrue(lines[0].startswith('FAIL leak scan (CJK tell): 1 line(s) carry characters that cannot belong to a Japanese target — untranslated Simplified Chinese text, or a proper noun to allowlist with --allow:'), lines)
        # The finding carries the drawn line as MuPDF reads it back; a TextWriter page drawn
        # straight from the SC face drifts 理 to U+F9E4 (no retypeset to canonicalise ToUnicode),
        # so compare NFKC-folded — the same fold the tell applies.
        self.assertEqual([(f.page, f.where, unicodedata.normalize('NFKC', f.text)) for f in findings],
                         [(1, 'line', ZH_PARA)])
        # A one-sentence echo carries only 2 tells (请 栏): REVIEW, not FAIL — measured, and honest.
        lines, status, findings = verify_mod.cjk_tell_report(page_with(ZH[1]), 'JP', set(), [], set(), source='SC')
        self.assertEqual(status, 'REVIEW', lines)
        self.assertTrue(lines[0].startswith('REVIEW leak scan (CJK tell): 1 line(s) carry a few characters that cannot belong to a Japanese target'), lines)
        self.assertIn('[2 tells:', lines[1])
        self.assertEqual([f.text for f in findings], [ZH[1]])

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
        self.assertTrue(any(l.startswith('note: 1 source-language run(s) kept as the original /Title or an allowlisted phrase: ') for l in lines), lines)

    def test_a_single_allow_token_that_clears_a_whole_line_is_said_so(self):
        # A CJK sentence has no spaces, so a whole echoed line can be one --allow token. Allowed is
        # allowed, but the PASS line and the kept-runs note must say a line was cleared.
        v, g = self.gates(self.ja_zh_echo, allow=[JA[1]])
        self.assertEqual((g['leak-cjk'].status, g['leak-cjk'].findings), ('PASS', ()), g['leak-cjk'])
        _, lines = self.console(self.ja_zh_echo, allow=[JA[1]])
        self.assertIn('PASS leak scan (CJK tell): 5 line(s) hold only characters a Simplified Chinese target can carry (1 line(s) reduced by --allow); a line of Han both languages share is invisible to the tell', lines)
        self.assertTrue(any(l.startswith('note: 1 source-language run(s) kept as the original /Title or an allowlisted phrase: ') for l in lines), lines)

    def test_a_page_with_a_fail_line_and_a_review_line_is_fail_and_lists_both(self):
        doc = pymupdf.open()
        page = doc.new_page(width=842, height=595)
        tw = pymupdf.TextWriter(page.rect)
        font = pymupdf.Font(fontfile=str(self.sc400))
        for i, text in enumerate((JA[0], ZH_PARA, ZH[1])):
            tw.append((72, 100 + 40 * i), text, font=font, fontsize=12)
        tw.write_text(page)
        lines, status, findings = verify_mod.cjk_tell_report(doc, 'JP', set(), [], set(), source='SC')
        self.assertEqual(status, 'FAIL', lines)
        self.assertTrue(lines[0].startswith('FAIL leak scan (CJK tell): 2 line(s)'), lines)
        self.assertEqual(len(lines), 3, lines)
        self.assertEqual([unicodedata.normalize('NFKC', f.text) for f in findings], [ZH_PARA, ZH[1]])

    def test_a_traditional_echo_into_a_simplified_target_is_named_traditional(self):
        doc = pymupdf.open()
        page = doc.new_page(width=842, height=595)
        tw = pymupdf.TextWriter(page.rect)
        font = pymupdf.Font(fontfile=str(self.sc400))
        for i, text in enumerate((ZH[0], TC_PARA, DATE)):
            tw.append((72, 100 + 40 * i), text, font=font, fontsize=12)
        tw.write_text(page)
        lines, status, findings = verify_mod.cjk_tell_report(doc, 'SC', set(), [], set(), source='TC')
        self.assertEqual(status, 'FAIL', lines)
        self.assertIn('— untranslated Traditional Chinese text, or a proper noun to allowlist with --allow:', lines[0])
        # TC_PARA carries a full-width comma (U+FF0C), which NFKC folds too: compare both sides folded.
        self.assertEqual([unicodedata.normalize('NFKC', f.text) for f in findings],
                         [unicodedata.normalize('NFKC', TC_PARA)])

    def test_a_partial_allow_that_leaves_tells_is_still_noted(self):
        # --allow removes nine of the echoed line's fourteen tells (された, てください, に): the
        # line drops to REVIEW, and the kept-runs note says --allow touched it.
        allow = ['\u3055\u308c\u305f', '\u3066\u304f\u3060\u3055\u3044', '\u306b']
        v, g = self.gates(self.ja_zh_echo, allow=allow)
        self.assertEqual(g['leak-cjk'].status, 'REVIEW', g['leak-cjk'])
        self.assertEqual([f.text for f in g['leak-cjk'].findings], [JA[1]])
        _, lines = self.console(self.ja_zh_echo, allow=allow)
        self.assertTrue(any(l.startswith('note: 1 source-language run(s) kept as the original /Title or an allowlisted phrase: ') for l in lines), lines)

    def test_a_single_rare_character_is_review_not_fail(self):
        src, out, tr, segments = self.ja_zh_clean
        with pymupdf.open(out) as doc:
            page = doc[0]
            tw = pymupdf.TextWriter(page.rect)
            tw.append((72, 400), '镕', font=pymupdf.Font(fontfile=str(self.sc400)), fontsize=12)   # 镕: in no repertoire
            tw.write_text(page)
            rare = os.path.join(os.path.dirname(out), 'rare.pdf')
            doc.save(rare)
        v = run_verify(src, rare, translations=tr, segments=segments, min_ink=0.1)
        g = {x.name: x for x in v.gates}
        self.assertEqual(g['leak-cjk'].status, 'REVIEW', g['leak-cjk'])
        self.assertEqual([f.text for f in g['leak-cjk'].findings], ['镕'])

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


if __name__ == '__main__':
    unittest.main()
