# -*- coding: utf-8 -*-
"""Conjunct-shaping probe: a mechanical tell for scripts whose broken
conjuncts leave no code-point signal in the text layer.

The tell (AGENTS.md, measured facts): render a probe string that contains
a merging cluster twice off the SAME face — once glyph by glyph
(insert_text, no shaping) and once through the Story engine (HarfBuzz) —
and count drawn glyphs. Shaping merges the cluster, so the shaped count is
lower. Arabic goes the other way (shaping ADDS glyphs) and has its own
gate; Thai, Lao and Hebrew-with-niqqud never change count and are blind to
this tell, so they must never be reported as verified by it.

Every count here is read from page.get_texttrace(), one entry per drawn
glyph, and both arms assert which font actually drew the run, because
insert_text(fontfile=...) without fontname= silently falls back to
Helvetica and draws one middle dot per code point.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

SKILL = Path(__file__).resolve().parents[1]
FONTS = SKILL / 'tests' / 'fonts'
sys.path.insert(0, str(SKILL / 'scripts'))

from pdf_translate import shaping_probe  # noqa: E402

NOTO = {
    'Devanagari': 'NotoSansDevanagari-Regular.ttf',
    'Bengali': 'NotoSansBengali-Regular.ttf',
    'Tamil': 'NotoSansTamil-Regular.ttf',
    'Khmer': 'NotoSansKhmer-Regular.ttf',
    'Myanmar': 'NotoSansMyanmar-Regular.ttf',
    'Thai': 'NotoSansThai-Regular.ttf',
    'Hebrew': 'NotoSansHebrew-Regular.ttf',
}


def noto(script):
    path = FONTS / NOTO[script]
    if not path.is_file():
        raise unittest.SkipTest(f'{path.name} not fetched (tools/fetch_test_fonts.py)')
    return str(path)


def strip_gsub(src, dst):
    """A copy of the face that cannot shape: same glyphs, no GSUB table."""
    with TTFont(src) as font:
        del font['GSUB']
        font.save(dst)
    return dst


class ProbeTableTests(unittest.TestCase):
    def test_every_probe_row_shapes_on_its_noto_face(self):
        """The attestation: for each table row the naive arm draws one
        glyph per code point, the shaped arm draws the measured count, and
        both arms were drawn by the face we asked for."""
        for probe in shaping_probe.PROBES:
            with self.subTest(script=probe.script, probe=probe.text):
                results = shaping_probe.probe_font(noto(probe.script), scripts=[probe.script])
                self.assertEqual(len(results), 1, results)
                r = results[0]
                self.assertEqual(r.status, 'PASS', r)
                self.assertEqual(r.codepoints, len(probe.text))
                self.assertEqual(r.naive_glyphs, r.codepoints, r)
                self.assertEqual(r.shaped_glyphs, probe.expected_shaped, r)
                self.assertLess(r.shaped_glyphs, r.naive_glyphs)
                self.assertEqual(r.naive_font, r.expected_font, r)
                self.assertEqual(r.shaped_font, r.expected_font, r)

    def test_table_covers_the_conjunct_scripts_with_fetched_faces(self):
        scripts = {p.script for p in shaping_probe.PROBES}
        self.assertEqual(scripts, {'Devanagari', 'Bengali', 'Tamil', 'Khmer', 'Myanmar'})

    def test_arabic_is_not_probed_by_glyph_count(self):
        """Shaping ADDS glyphs in Arabic (5 -> 8). Gate 12 owns Arabic."""
        self.assertNotIn('Arabic', {p.script for p in shaping_probe.PROBES})
        self.assertNotIn('Arabic', shaping_probe.BLIND_SCRIPTS)

    def test_blind_scripts_are_reviewed_never_passed(self):
        """Mark stacking never changes the glyph count: a correct Thai or
        niqqud run and a broken one look identical to this tell."""
        for script in ('Thai', 'Hebrew niqqud'):
            self.assertIn(script, shaping_probe.BLIND_SCRIPTS)
        for script, face in (('Thai', 'Thai'), ('Hebrew niqqud', 'Hebrew')):
            with self.subTest(script=script):
                results = shaping_probe.probe_font(noto(face), scripts=[script])
                self.assertEqual(len(results), 1, results)
                self.assertEqual(results[0].status, 'REVIEW', results[0])
                self.assertNotEqual(results[0].status, 'PASS')
                self.assertIn('no glyph-count tell', results[0].reason)


class RedPathTests(unittest.TestCase):
    def test_gsub_stripped_face_fails_the_probe(self):
        """The red run: same face minus GSUB draws the conjunct probe
        unshaped (shaped == naive) and the probe says FAIL, naming counts."""
        with tempfile.TemporaryDirectory() as tmp:
            bad = strip_gsub(noto('Devanagari'), os.path.join(tmp, 'no-gsub.ttf'))
            results = shaping_probe.probe_font(bad, scripts=['Devanagari'])
            self.assertEqual(len(results), 1)
            r = results[0]
            self.assertEqual(r.status, 'FAIL', r)
            self.assertEqual(r.shaped_glyphs, r.naive_glyphs, r)
            self.assertEqual(r.naive_font, r.expected_font, r)
            self.assertIn('no conjunct formed', r.reason)

    def test_font_fallback_is_a_failure_not_a_pass(self):
        """AGENTS.md method warning: a run drawn by Helvetica must never be
        judged, whatever its counts say."""
        probe = shaping_probe.PROBES[0]
        face = 'NotoSansDevanagari-Regular'
        r = shaping_probe.judge(probe, naive_glyphs=8, shaped_glyphs=4,
                                naive_font='Helvetica', shaped_font=face,
                                expected_font=face)
        self.assertEqual(r.status, 'FAIL', r)
        self.assertIn('Helvetica', r.reason)
        r = shaping_probe.judge(probe, naive_glyphs=8, shaped_glyphs=4,
                                naive_font='NotoSansDevanagari-Regular',
                                shaped_font='Helvetica',
                                expected_font='NotoSansDevanagari-Regular')
        self.assertEqual(r.status, 'FAIL', r)
        self.assertIn('Helvetica', r.reason)

    def test_naive_arm_that_is_not_one_glyph_per_codepoint_fails(self):
        probe = shaping_probe.PROBES[0]
        face = 'NotoSansDevanagari-Regular'
        r = shaping_probe.judge(probe, naive_glyphs=6, shaped_glyphs=4,
                                naive_font=face, shaped_font=face,
                                expected_font=face)
        self.assertEqual(r.status, 'FAIL', r)


class CoverageTests(unittest.TestCase):
    def test_face_without_the_probe_glyphs_is_skipped_not_judged(self):
        """A Latin-only face cannot attest Devanagari; say so, do not fail."""
        latin = FONTS / 'NotoSans-Regular.ttf'
        if not latin.is_file():
            raise unittest.SkipTest('NotoSans-Regular.ttf not fetched')
        results = shaping_probe.probe_font(str(latin), scripts=['Devanagari'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, 'SKIP', results[0])
        self.assertIn('does not cover', results[0].reason)

    def test_scripts_in_text(self):
        self.assertEqual(shaping_probe.scripts_in('नमस्ते'), {'Devanagari'})
        self.assertEqual(shaping_probe.scripts_in('ខ្មែរ and ဗမာ'), {'Khmer', 'Myanmar'})
        self.assertEqual(shaping_probe.scripts_in('สวัสดี'), {'Thai'})
        self.assertEqual(shaping_probe.scripts_in('שָׁלוֹם'), {'Hebrew niqqud'})
        self.assertEqual(shaping_probe.scripts_in('שלום'), set())
        self.assertEqual(shaping_probe.scripts_in('مكتبة'), set())
        self.assertEqual(shaping_probe.scripts_in('ગુજરાતી'), {'Gujarati'})
        self.assertEqual(shaping_probe.scripts_in('Hello 123'), set())

    def test_conjunct_script_without_a_measured_probe_is_reviewed(self):
        """Gujarati is conjunct-forming, but no face was measured, so there
        is no expected count to attest against. Never PASS by assumption."""
        results = shaping_probe.probe_font(noto('Devanagari'), scripts=['Gujarati'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, 'REVIEW', results[0])
        self.assertIn('no probe measured', results[0].reason)


if __name__ == '__main__':
    unittest.main()
