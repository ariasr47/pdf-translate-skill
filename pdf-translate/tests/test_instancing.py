#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/_instancing.py hands a repeat the first result, and only when it
can be sure the repeat asked for the same thing (R-51). A mistake here would
not fail loudly: the modules that opt in would test the wrong font."""
import io
import os
import tempfile
import unittest

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from tests import _instancing
from tests.test_pipeline import small_variable_face


def _saved(font):
    font['head'].modified = 0
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


class InstancingMemoTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.face = small_variable_face(os.path.join(tmp.name, 'vf.ttf'))
        _instancing.install()
        self.addCleanup(_instancing.uninstall)
        self.addCleanup(_instancing._results.clear)
        _instancing._results.clear()

    def real(self, axes, **options):
        with TTFont(self.face) as font:
            return _saved(_instancing._REAL(font, axes, **options))

    def test_a_repeat_in_place_is_the_same_font_as_a_real_instance(self):
        for _ in range(2):
            with TTFont(self.face) as font:
                returned = instancer.instantiateVariableFont(font, {'wght': 700}, inplace=True)
                self.assertIs(returned, font)
                self.assertNotIn('fvar', font)
                self.assertEqual(_saved(font), self.real({'wght': 700}))
        self.assertEqual(len(_instancing._results), 1)

    def test_a_repeat_not_in_place_leaves_the_variable_font_alone(self):
        for _ in range(2):
            with TTFont(self.face) as font:
                result = instancer.instantiateVariableFont(font, {'wght': 700})
                self.assertIsNot(result, font)
                self.assertIn('fvar', font)
                self.assertEqual(_saved(result), self.real({'wght': 700}))

    def test_different_axes_or_options_are_different_instances(self):
        for axes, options in (({'wght': 400}, {}), ({'wght': 700}, {}),
                              ({'wght': 700}, {'updateFontNames': True})):
            with TTFont(self.face) as font:
                instancer.instantiateVariableFont(font, axes, inplace=True, **options)
                self.assertEqual(_saved(font), self.real(axes, **options), (axes, options))
        self.assertEqual(len(_instancing._results), 3)

    def test_a_table_only_read_is_still_the_file(self):
        for _ in range(2):
            with TTFont(self.face) as font:
                self.assertIn('wght', [axis.axisTag for axis in font['fvar'].axes])
                instancer.instantiateVariableFont(font, {'wght': 700}, inplace=True)
                self.assertEqual(_saved(font), self.real({'wght': 700}))
        self.assertEqual(len(_instancing._results), 1)

    def test_a_font_changed_in_memory_or_a_range_goes_to_the_instancer(self):
        with TTFont(self.face) as font:
            font['name'].names[0].string = 'changed in memory'
            instancer.instantiateVariableFont(font, {'wght': 700}, inplace=True)
        with TTFont(self.face) as font:
            font.setGlyphOrder(font.getGlyphOrder())
            font.tables.clear()
            instancer.instantiateVariableFont(font, {'wght': 700}, inplace=True)
        with TTFont(self.face) as font:
            instancer.instantiateVariableFont(font, {'wght': (400, 700)}, inplace=True)
            self.assertIn('fvar', font)
        self.assertEqual(_instancing._results, {})

    def test_arguments_it_cannot_read_reach_the_instancer_unchanged(self):
        with TTFont(self.face) as font:
            with self.assertRaises(TypeError) as real:
                _instancing._REAL(font)
            with self.assertRaises(TypeError) as memo:
                instancer.instantiateVariableFont(font)
        self.assertEqual(str(memo.exception), str(real.exception))
        self.assertEqual(_instancing._results, {})


if __name__ == '__main__':
    unittest.main()
