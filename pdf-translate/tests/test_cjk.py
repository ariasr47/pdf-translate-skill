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


class KinsokuSetTests(unittest.TestCase):

    def test_members_from_the_public_classes(self):
        # cl-06 。 cl-07 、 cl-02 」） cl-10 ー and half-width ｰ, cl-11 ぁッ and
        # half-width ｧ, half-width ｡ ｣, cl-04 ？
        for ch in '。、」）ーｰぁッｧ｡｣？':
            self.assertIn(ch, verify_mod.KINSOKU_LINE_START, f'U+{ord(ch):04X}')
        # cl-01 「（【 and half-width ｢
        for ch in '「（【｢':
            self.assertIn(ch, verify_mod.KINSOKU_LINE_END, f'U+{ord(ch):04X}')

    def test_the_two_sets_are_disjoint(self):
        self.assertEqual(verify_mod.KINSOKU_LINE_START & verify_mod.KINSOKU_LINE_END,
                         frozenset())

    def test_ordinary_letters_are_in_neither(self):
        for ch in 'あ漢アA1':
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
        split_lines_page(doc, ['ー'], y=100)
        split_lines_page(doc, ['）該当なし'], y=100)
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))
        self.assertEqual(lines, ['PASS kinsoku: 2 CJK line(s) break within the rules'])

    def test_first_and_last_lines_of_a_block_are_exempt(self):
        # A block whose first line starts with 。 had no break before it;
        # one whose last line ends with 「 had none after it.
        doc = pymupdf.open()
        split_lines_page(doc, ['。氏名', '住所を書く', '記入欄「'])
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
        split_lines_page(doc, ['申立人は', 'Form 1040', '。氏名と住所'])
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual(status, 'FAIL')
        self.assertEqual([(f.where, f.text) for f in findings],
                         [('line-start', '。氏名と住所')])
        self.assertEqual(lines[0].split(':')[0], 'FAIL kinsoku')

    def test_a_line_of_only_punctuation_is_judged_like_any_other(self):
        # A hand split can leave a bracket or a full stop alone on a line. It
        # carries no letter, so it is judged by its block, not by itself.
        doc = pymupdf.open()
        split_lines_page(doc, ['\u3042\u308b\u6587\u7ae0\u3067\u3059', '\u300c', '\u7d9a\u304f\u6587\u7ae0'])
        split_lines_page(doc, ['\u3042\u308b\u6587\u7ae0', '\u3002', '\u7d9a\u304f'])
        lines, status, findings = kinsoku_report(doc)
        self.assertEqual(status, 'FAIL')
        self.assertEqual([(f.page, f.where, f.text) for f in findings],
                         [(1, 'line-end', '\u300c'), (2, 'line-start', '\u3002')])

    def test_a_block_without_any_cjk_letter_is_never_judged(self):
        # Latin lines ending in a curly opening quote are not Japanese
        # typography's business, whatever face drew them.
        doc = pymupdf.open()
        split_lines_page(doc, ['He said \u201c', 'hello.\u201d'])
        self.assertEqual(kinsoku_report(doc), ([], None, []))

    def test_the_gate_consults_the_sets(self):
        # Remove the two members the fixture breaks and the fixture passes:
        # the gate judges by the sets, not by a hard-coded character.
        doc = pymupdf.open()
        split_lines_page(doc, SPLIT_BAD)
        start = verify_mod.KINSOKU_LINE_START - {'。'}
        end = verify_mod.KINSOKU_LINE_END - {'「'}
        with mock.patch.object(verify_mod, 'KINSOKU_LINE_START', start), \
                mock.patch.object(verify_mod, 'KINSOKU_LINE_END', end):
            lines, status, findings = kinsoku_report(doc)
        self.assertEqual((status, findings), ('PASS', []))


if __name__ == '__main__':
    unittest.main()
