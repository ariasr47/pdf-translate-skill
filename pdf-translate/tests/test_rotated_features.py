#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A rotated run refuses, by name, the horizontal-only features asked of it.

A run whose line is not horizontal in PDF space is drawn along its own
direction, and several mapping features are horizontal ideas: `right` and
`center` were silently ignored on it, an override placed its parts at
horizontal x positions (or all at the origin), inline markup was drawn as
literal `<b>` tags, and a merge laid its lines out as a horizontal box. Each
is something the author asked for and can take back, so the build refuses
it by name before drawing anything.
"""
import importlib
import json
import os
import tempfile
import unittest

import pymupdf

from pdf_translate import run_extract, run_retypeset, run_strip
from pdf_translate.results import MappingError
from tests.test_pipeline import find_test_font

retypeset = importlib.import_module('pdf_translate.retypeset')

SIDE = 'FOR OFFICE USE ONLY'
SIDE_ES = 'SOLO PARA USO OFICIAL'
FLAT = 'Applicant name'
FLAT_ES = 'Nombre del solicitante'


class RotatedFeatureTests(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        src = os.path.join(self.tmp, 'orig.pdf')
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=400)
            page.insert_text((360, 340), SIDE, fontsize=10, rotate=90)
            page.insert_text((40, 60), FLAT, fontsize=10)
            doc.save(src)
        self.src = src
        self.stripped = os.path.join(self.tmp, 'stripped.pdf')
        run_strip(src, self.stripped)
        self.segments = run_extract(src, self.tmp).segments_path
        self.out = os.path.join(self.tmp, 'out.pdf')

    def _build(self, **extra):
        font = str(find_test_font())
        conf = {'fonts': {'regular': font},
                'translations': {SIDE: SIDE_ES, FLAT: FLAT_ES},
                'merges': [], 'overrides': [], 'center': [], 'skip': []}
        conf.update(extra)
        mapping = os.path.join(self.tmp, 'translations.json')
        with open(mapping, 'w', encoding='utf-8') as f:
            json.dump(conf, f, ensure_ascii=False)
        return run_retypeset(self.stripped, self.segments, mapping, self.out,
                             scale_report=None)

    def _refused(self, **extra):
        with self.assertRaises(MappingError) as caught:
            self._build(**extra)
        self.assertFalse(os.path.exists(self.out), 'a refused build wrote its output')
        return caught.exception

    def test_the_fixture_has_one_rotated_and_one_flat_line(self):
        with open(self.segments, encoding='utf-8') as f:
            segs = json.load(f)['segments']
        dirs = {s['core']: retypeset.is_rotated(*retypeset.seg_dir(s)) for s in segs}
        self.assertEqual(dirs, {SIDE: True, FLAT: False})

    def test_a_plain_rotated_run_still_builds(self):
        result = self._build()
        self.assertTrue(os.path.exists(result.output))

    def test_each_feature_is_refused_by_name(self):
        cases = {
            'right': {'right': [SIDE]},
            'center': {'center': [SIDE]},
            'override': {'overrides': [{'page': 0, 'contains': SIDE,
                                        'parts': [{'text': 'SOLO PARA'},
                                                  {'text': 'USO OFICIAL', 'x': 200}]}]},
            'inline markup': {'translations': {SIDE: 'SOLO PARA <b>USO</b> OFICIAL',
                                               FLAT: FLAT_ES}},
        }
        for feature, extra in cases.items():
            with self.subTest(feature=feature):
                exc = self._refused(**extra)
                self.assertEqual(exc.refusals.get('rotated_features'),
                                 [{'page': 0, 'core': SIDE, 'feature': feature}])
                self.assertIn(feature, exc.console_line)
                self.assertIn(SIDE, exc.console_line)

    def test_a_merge_that_takes_in_a_rotated_line_is_refused(self):
        exc = self._refused(merges=[{'page': 0, 'lines': [SIDE], 'html': SIDE_ES}])
        self.assertEqual(exc.refusals.get('rotated_features'),
                         [{'page': 0, 'core': SIDE, 'feature': 'merge'}])

    def test_every_feature_is_listed_at_once(self):
        exc = self._refused(right=[SIDE], center=[SIDE])
        self.assertEqual(
            sorted(r['feature'] for r in exc.refusals['rotated_features']),
            ['center', 'right'])

    def test_the_same_features_on_a_flat_line_still_build(self):
        result = self._build(right=[FLAT],
                             translations={SIDE: SIDE_ES,
                                           FLAT: 'Nombre del <b>solicitante</b>'})
        self.assertTrue(os.path.exists(result.output))


class RotatedLeaderTests(unittest.TestCase):
    """Dot leaders are refilled only along a horizontal line. On a rotated
    line they are dropped, and the currency sign after them (the tail) used
    to be dropped with them. It is content: it is kept, and the dropped
    leaders are reported in the result, not only on the console."""

    def _job(self, rotate):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = os.path.join(tmp.name, 'orig.pdf')
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=400)
            page.insert_text((360, 340) if rotate else (40, 60),
                             'Total ........................ $', fontsize=10, rotate=rotate)
            doc.save(src)
        stripped = os.path.join(tmp.name, 'stripped.pdf')
        run_strip(src, stripped)
        segments = run_extract(src, tmp.name).segments_path
        mapping = os.path.join(tmp.name, 'translations.json')
        with open(mapping, 'w', encoding='utf-8') as f:
            json.dump({'fonts': {'regular': str(find_test_font())},
                       'translations': {'Total': 'Total'}, 'merges': [], 'overrides': [],
                       'center': [], 'skip': []}, f)
        out = os.path.join(tmp.name, 'out.pdf')
        result = run_retypeset(stripped, segments, mapping, out, scale_report=None)
        with pymupdf.open(out) as doc:
            text = doc[0].get_text()
        return result, text

    def test_the_fixture_is_a_rotated_leader_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            with pymupdf.open() as doc:
                doc.new_page(width=400, height=400).insert_text(
                    (360, 340), 'Total ........................ $', fontsize=10, rotate=90)
                doc.save(src)
            seg = run_extract(src, tmp).segments[0]
            self.assertEqual((seg['core'], seg['tail']), ('Total', '$'))
            self.assertTrue(seg['dots'])
            self.assertTrue(retypeset.is_rotated(*retypeset.seg_dir(seg)))

    def test_a_rotated_line_keeps_its_tail_and_reports_the_leaders(self):
        result, text = self._job(90)
        self.assertIn('Total $', ' '.join(text.split()))
        self.assertNotIn('...', text)
        self.assertEqual(result.warnings,
                         ({'kind': 'leaders_dropped', 'page': 0, 'core': 'Total'},))
        self.assertEqual(result.to_dict()['warnings'], [
            {'kind': 'leaders_dropped', 'page': 0, 'core': 'Total'}])

    def test_a_horizontal_leader_line_is_unchanged(self):
        result, text = self._job(0)
        self.assertIn('...', text)
        self.assertIn('$', text)
        self.assertEqual(result.warnings, ())


if __name__ == '__main__':
    unittest.main()
