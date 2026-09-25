#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R-50: prepare_font instances the job's subset, not the whole variable face,
gives the subset the whole-face order gave, and leaves nothing beside it."""
import importlib
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from tests.test_han_forms import JP_FACE, TARGET, _face
from tests.test_pipeline import SOURCE_SENTENCE, small_variable_face, write_mapping

prepare_font = importlib.import_module('pdf_translate.prepare_font')


def _without_timestamp(path):
    with TTFont(path) as font:
        font.recalcTimestamp = False
        font['head'].modified = 0
        buffer = io.BytesIO()
        font.save(buffer)
    return buffer.getvalue()


class SubsetBeforeInstancingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def prepare(self, face, target, instance, name='job'):
        job = self.tmp / name
        job.mkdir()
        tr, out = job / 'translations.json', job / 'subset.ttf'
        write_mapping(str(tr), {SOURCE_SENTENCE: target}, Path(face))
        with redirect_stdout(io.StringIO()):
            rc = prepare_font.prepare_font(str(face), str(tr), str(out), instance=instance)
        self.assertEqual(rc, 0)
        return job, out

    def test_the_instancer_sees_only_the_jobs_glyphs(self):
        seen = []
        real = instancer.instantiateVariableFont

        def counted(varfont, *args, **kwargs):
            seen.append(len(varfont.getGlyphOrder()))
            return real(varfont, *args, **kwargs)

        with TTFont(str(_face(JP_FACE))) as whole:
            whole_glyphs = len(whole.getGlyphOrder())
        with mock.patch.object(instancer, 'instantiateVariableFont', counted):
            self.prepare(JP_FACE, TARGET, 'wght=400')
        self.assertEqual(len(seen), 1, seen)
        # The job's characters, the probe glyphs and every glyph any layout
        # feature reaches from them (vertical forms included): a few hundred,
        # where the face has more than 17,000.
        self.assertGreater(whole_glyphs, 17000)
        self.assertLess(seen[0], whole_glyphs / 20)

    def test_nothing_is_left_beside_the_output(self):
        face = small_variable_face(str(self.tmp / 'vf.ttf'))
        for instance in ('wght=700', None):
            with self.subTest(instance=instance):
                job, _ = self.prepare(face, '山田 12', instance, name=f'job-{instance}')
                self.assertEqual(sorted(os.listdir(job)), ['subset.ttf', 'translations.json'])

    def test_the_subset_draws_what_instancing_the_whole_face_drew(self):
        """Not byte for byte: the old order saved the whole instanced face,
        which recalculated head's bounding box, hhea's extents and the like
        over every glyph, and the subset kept them. The new order computes
        them over the job's glyphs. Everything that draws is the same."""
        face = small_variable_face(str(self.tmp / 'vf.ttf'))
        summary = {'head', 'hhea', 'vhea', 'OS/2', 'GPOS'}
        line_fields = {'hhea': ('ascent', 'descent', 'lineGap'),
                       'OS/2': ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'usWinAscent',
                                'usWinDescent', 'usWeightClass', 'fsSelection'),
                       'head': ('unitsPerEm', 'macStyle')}
        text = '山田太郎 Name 0'
        for wght in (400, 700):
            with self.subTest(wght=wght):
                _, first = self.prepare(face, text, f'wght={wght}', name=f'subset-{wght}')
                # The order before R-50: instance the whole face, then subset.
                with mock.patch.object(prepare_font, '_variable_subset',
                                       lambda font_in, chars: TTFont(font_in)):
                    _, whole = self.prepare(face, text, f'wght={wght}', name=f'whole-{wght}')
                with TTFont(first) as a, TTFont(whole) as b:
                    self.assertEqual(a.getGlyphOrder(), b.getGlyphOrder())
                    tags = set(a.reader.keys()) | set(b.reader.keys())
                    differ = {t for t in tags if t not in a.reader or t not in b.reader
                              or a.reader[t] != b.reader[t]}
                    self.assertLessEqual(differ, summary)
                    for table, fields in line_fields.items():
                        for field in fields:
                            self.assertEqual(getattr(a[table], field), getattr(b[table], field),
                                             f'{table}.{field}')
                self.assertEqual(self.render(first, text), self.render(whole, text))

    def render(self, font_path, text):
        """The text drawn glyph by glyph and through the Story engine, which
        applies GPOS kerning, as raw pixels."""
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page(width=300, height=120)
        font = pymupdf.Font(fontfile=str(font_path))
        writer = pymupdf.TextWriter(page.rect)
        writer.append((10, 30), text, font=font, fontsize=20)
        writer.write_text(page)
        archive = pymupdf.Archive(str(Path(font_path).parent))
        css = f'@font-face {{font-family: F; src: url({Path(font_path).name});}} p {{font-family: F; font-size: 20px;}}'
        page.insert_htmlbox(pymupdf.Rect(10, 50, 290, 110), f'<p>{text}</p>', css=css, archive=archive)
        # Both lines must be drawn by the subset: a fallback face would make
        # the two renders agree without comparing anything.
        spans = [s for b in page.get_text('dict')['blocks'] for l in b.get('lines', []) for s in l['spans']]
        self.assertEqual(len(spans), 2, spans)
        self.assertTrue(all('NotoSansJP' in s['font'] for s in spans), [s['font'] for s in spans])
        samples = page.get_pixmap(dpi=144).samples
        doc.close()
        return samples


if __name__ == '__main__':
    unittest.main()
