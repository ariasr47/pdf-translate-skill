"""One-line builds preserve source pages/baselines and refuse unsafe placement."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest

import pymupdf
from fontTools.ttLib import TTFont

from pdf_translate import run_extract, run_retypeset, run_strip
from pdf_translate.results import GlyphError, MappingError, PdfTranslateError, RetypesetResult
from pdf_translate.typography import bind_extraction
from tests.typography_fixtures import latin_font_sets, make_job, make_mapping, raw_spans


class TypographyRetypesetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.job = make_job(self.work)

    def build(self, **kwargs):
        kwargs.setdefault('original', str(self.job['original']))
        return run_retypeset(*(str(self.job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                             **kwargs)

    def update_mapping(self, change):
        path = self.job['mapping']
        conf = json.loads(path.read_text(encoding='utf-8'))
        change(conf)
        path.write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')

    def reextract(self, pages=None):
        run_strip(str(self.job['original']), str(self.job['stripped']))
        run_extract(str(self.job['original']), str(self.work), typography=True, pages=pages)
        extraction = json.loads(self.job['segments'].read_text(encoding='utf-8'))
        self.job['mapping'].write_text(json.dumps(make_mapping(extraction, latin_font_sets())), encoding='utf-8')

    def mutate_pdf(self, key, change):
        path = self.job[key]
        with pymupdf.open(path) as doc:
            change(doc)
            data = doc.tobytes()
        path.write_bytes(data)

    def refuses(self, reason, **kwargs):
        self.job['output'].write_bytes(b'prior successful output')
        with self.assertRaises(PdfTranslateError) as caught:
            self.build(**kwargs)
        self.assertEqual(caught.exception.refusals['typography'][0]['reason'], reason)
        self.assertEqual(self.job['output'].read_bytes(), b'prior successful output')
        self.assertFalse((self.work / 'scale_report.json').exists())
        return caught.exception

    def test_original_is_required_and_prior_output_is_preserved(self):
        self.job['output'].write_bytes(b'prior output marker')
        with self.assertRaises(MappingError) as caught:
            run_retypeset(*(str(self.job[k]) for k in ('stripped', 'segments', 'mapping', 'output')))
        self.assertEqual(caught.exception.refusals['typography'][0]['reason'], 'stale-extraction')
        self.assertEqual(self.job['output'].read_bytes(), b'prior output marker')

    def test_reordered_runs_preserve_each_repeated_occurrence_and_baseline(self):
        def reorder(conf):
            conf['lang'] = 'es'
            conf['targets'][0]['runs'] = [{'text': 'AHORA ', 'source_runs': ['s0/r1']},
                                          {'text': 'pague', 'source_runs': ['s0/r0']}]
        self.update_mapping(reorder)
        result = self.build()
        self.assertEqual((result.pages, result.placed, result.cancelled), (1, 2, False))
        spans = raw_spans(self.job['output'])
        self.assertEqual([s['text'] for s in spans], ['AHORA ', 'pague', 'Pay ', 'NOW'])
        self.assertEqual([s['font'] for s in spans],
                         ['NotoSans-Bold', 'NotoSans-Regular', 'NotoSerif-Regular', 'NotoSerif-BoldItalic'])
        for span, y in zip(spans, [60, 60, 120, 120]):
            self.assertAlmostEqual(span['origin'][1], y, delta=0.05)
            self.assertAlmostEqual(span['size'], 12, delta=0.05)
        record = result.typography
        self.assertEqual([r['occurrence_id'] for r in record['occurrences']], ['s0', 's1'])
        self.assertEqual(record['occurrences'][0]['runs'][0]['source_runs'], ['s0/r1'])
        self.assertEqual(len(record['fonts']), 4)
        report = json.loads((self.work / 'scale_report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['schema'], 2)
        self.assertEqual(report['typography'], record)
        self.assertEqual(report['runs'], [])

    def test_trailing_blank_pages_are_retained_and_reported_as_progress(self):
        self.mutate_pdf('original', lambda d: d.new_page(width=400, height=240))
        self.reextract()
        progress = []
        result = self.build(progress=lambda done, total: progress.append((done, total)))
        with pymupdf.open(self.job['output']) as doc:
            self.assertEqual(doc.page_count, 2)
            self.assertEqual(doc[1].get_text(), '')
        self.assertEqual(result.pages, 2)
        self.assertEqual(progress, [(1, 2), (2, 2)])

    def content_refusal(self, change):
        self.mutate_pdf('original', change)
        self.reextract()
        return self.refuses('unsupported-typography-construct').refusals['typography'][0]

    def test_a_content_refusal_names_the_occurrence_it_is_about(self):
        """R-42: a source-content refusal named the page's first occurrence,
        whatever text was actually covered, sheared, clipped or transparent."""
        covered = self.content_refusal(lambda d: d[0].draw_rect(
            pymupdf.Rect(28, 106, 120, 124), fill=(1, 1, 1), color=None, overlay=True))
        self.assertEqual((covered['detail'], covered['page'], covered['occurrence_id']),
                         ('Later page or annotation paint may cover source glyphs.', 0, 's1'))

    def test_a_sheared_line_is_named_not_the_first_line(self):
        def shear(doc):
            doc[0].insert_text((30, 200), 'Slanted words', fontname='helv', fontsize=12,
                               morph=(pymupdf.Point(30, 200), pymupdf.Matrix(1, 0, -0.3, 1, 0, 0)))
        sheared = self.content_refusal(shear)
        extraction = json.loads(self.job['segments'].read_text(encoding='utf-8'))
        named = next(s for s in extraction['segments'] if s['occurrence_id'] == sheared['occurrence_id'])
        self.assertEqual((sheared['detail'], named['text']),
                         ('Text uses shear, rotation or nonuniform scaling.', 'Slanted words'))
        self.assertEqual(sheared['source_text'], 'Slanted words')

    def test_a_page_level_content_refusal_names_the_page_and_no_occurrence(self):
        def user_unit(doc):
            doc.xref_set_key(doc[0].xref, 'UserUnit', '2')
        page_level = self.content_refusal(user_unit)
        self.assertEqual((page_level['page'], page_level['occurrence_id'], page_level['source_text']),
                         (0, None, None))

    def test_a_malformed_crop_box_leaves_the_position_unknown(self):
        """The crop only places the offending text, so a /CropBox that is not
        four numbers must not fail the check that v71 passed (R-42's review)."""
        from pdf_translate.typography_content import inspect_content
        for box in ('[0 0 100]', '[]', '[0 0 /A 100]'):
            with self.subTest(box=box):
                def shear_and_break(doc, box=box):
                    doc[0].insert_text((30, 200), 'Slanted words', fontname='helv', fontsize=12,
                                       morph=(pymupdf.Point(30, 200), pymupdf.Matrix(1, 0, -0.3, 1, 0, 0)))
                    doc.xref_set_key(doc[0].xref, 'CropBox', box)
                path = self.work / 'broken-crop.pdf'
                with pymupdf.open(self.job['original']) as doc:
                    shear_and_break(doc)
                    path.write_bytes(doc.tobytes())
                issues = inspect_content(str(path), source=True).issues
                sheared = [i for i in issues if i.kind == 'transformed-text']
                self.assertEqual(len(sheared), 1, issues)
                self.assertIsNone(sheared[0].at)

    def test_partial_extraction_cannot_drop_an_unselected_blank_page(self):
        self.mutate_pdf('original', lambda d: d.new_page(width=400, height=240))
        self.reextract(pages='1')
        self.refuses('unsupported-typography-construct')

    def test_changed_original_and_changed_stripped_geometry_refuse(self):
        self.mutate_pdf('original', lambda d: d.set_metadata({'title': 'Changed'}))
        self.refuses('stale-extraction')

    def test_incompatible_stripped_boxes_rotation_and_fields_refuse(self):
        original_bytes = self.job['stripped'].read_bytes()
        def widget(doc):
            w = pymupdf.Widget()
            w.field_name, w.field_type, w.rect = 'added', pymupdf.PDF_WIDGET_TYPE_TEXT, pymupdf.Rect(200, 180, 260, 200)
            doc[0].add_widget(w)
        for change in [lambda d: d[0].set_cropbox(pymupdf.Rect(0, 0, 390, 230)),
                       lambda d: d[0].set_rotation(90), widget, lambda d: d.new_page()]:
            self.job['stripped'].write_bytes(original_bytes)
            self.mutate_pdf('stripped', change)
            self.refuses('stale-extraction')

    def test_below_floor_exception_is_exactly_one_occurrence(self):
        def long_targets(conf):
            for target in conf['targets']:
                target['runs'][0]['text'] = 'Extremely long translated wording ' * 10
            conf['allow_scale'] = [{'occurrence_id': 's0', 'reason': 'Fixed narrow source cell'}]
        self.update_mapping(long_targets)
        refused = self.refuses('below-scale-floor')
        self.assertEqual(refused.refusals['typography'][0]['occurrence_id'], 's1')
        self.update_mapping(lambda c: c['allow_scale'].append(
            {'occurrence_id': 's1', 'reason': 'Also explicitly accepted'}))
        result = self.build()
        self.assertEqual(len(result.scaled), 2)
        self.assertTrue(all(r['ratio'] < 0.7 for r in result.scaled))
        for occurrence in result.typography['occurrences']:
            self.assertTrue(occurrence['scale_reason'])
            self.assertEqual(len({run['size'] for run in occurrence['runs']}), 1)

    def test_scale_report_can_be_disabled(self):
        result = self.build(scale_report=None)
        self.assertEqual(result.scale_report_path, '')
        self.assertFalse((self.work / 'scale_report.json').exists())
        self.assertEqual(result.typography['extraction_id'],
                         json.loads(self.job['mapping'].read_text())['extraction_id'])

    def test_cancellation_preserves_prior_output_and_report(self):
        self.job['output'].write_bytes(b'old pdf')
        report = self.work / 'scale_report.json'
        report.write_bytes(b'old report')
        result = self.build(cancel=lambda: True)
        self.assertTrue(result.cancelled)
        self.assertIsNone(result.output)
        self.assertEqual(self.job['output'].read_bytes(), b'old pdf')
        self.assertEqual(report.read_bytes(), b'old report')
        self.assertEqual(result.scale_report_path, '')

    def test_output_cannot_alias_an_input_or_a_font(self):
        for key in ('original', 'stripped', 'mapping', 'segments'):
            path = self.job[key]
            before = path.read_bytes()
            with self.subTest(key=key), self.assertRaises(MappingError):
                run_retypeset(*(str(self.job[k]) for k in ('stripped', 'segments', 'mapping')),
                              str(path), original=str(self.job['original']))
            self.assertEqual(path.read_bytes(), before)
        with self.assertRaises(MappingError):
            self.build(scale_report=str(self.job['mapping']))
        font = Path(latin_font_sets()['sans']['regular'])
        before = font.read_bytes()
        with self.assertRaises(MappingError):
            run_retypeset(*(str(self.job[k]) for k in ('stripped', 'segments', 'mapping')),
                          str(font), original=str(self.job['original']))
        self.assertEqual(font.read_bytes(), before)

    def test_named_source_constructs_refuse_even_when_every_target_is_authored(self):
        for case in ('size', 'color', 'baseline', 'rotation', 'marker', 'dots'):
            with self.subTest(case=case):
                extraction = json.loads(self.job['segments'].read_text(encoding='utf-8'))
                segment = extraction['segments'][0]
                if case == 'size':
                    segment['style_runs'][1]['size'] = 14
                elif case == 'color':
                    segment['style_runs'][1]['color'] = 0xff0000
                elif case == 'baseline':
                    segment['style_runs'][1]['origin'][1] += 1
                elif case == 'rotation':
                    segment['dir'] = [0, -1]
                else:
                    segment[case] = '1.' if case == 'marker' else '...'
                extraction['typography'] = bind_extraction(extraction)
                self.job['segments'].write_text(json.dumps(extraction), encoding='utf-8')
                self.job['mapping'].write_text(json.dumps(make_mapping(extraction, latin_font_sets())), encoding='utf-8')
                self.refuses('unsupported-typography-construct')
                self.reextract()

    def test_plain_markup_and_unicode_survive_bold_italic(self):
        self.update_mapping(lambda c: c['targets'][1]['runs'][1].update(text='<b>café</b>'))
        self.build()
        self.assertIn('<b>café</b>', ''.join(s['text'] for s in raw_spans(self.job['output'])))

    def test_italic_overhang_cannot_clip_at_left_crop_edge(self):
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=200)
            page.insert_text((0, 60), 'Pay', fontname='tiit', fontsize=12)
            doc.save(self.job['original'])
        self.reextract()
        self.update_mapping(lambda c: c['targets'][0]['runs'][0].update(text='f'))
        self.refuses('unsafe-typography-geometry')

    def test_metadata_is_separate_and_graphics_are_unchanged(self):
        def source(doc):
            doc.set_metadata({'title': 'Source title'})
            doc.set_toc([[1, 'Source bookmark', 1]])
            doc[0].draw_rect((220, 160, 350, 200), color=(1, 0, 0), fill=(0.8, 0.8, 0.8))
        self.mutate_pdf('original', source)
        self.reextract()
        self.update_mapping(lambda c: c.update(document_targets={
            'Source title': 'Translated title', 'Source bookmark': 'Translated bookmark'}))
        self.build()
        with pymupdf.open(self.job['original']) as original, pymupdf.open(self.job['output']) as final:
            self.assertEqual(final.metadata['title'], 'Translated title')
            self.assertEqual(final.get_toc()[0][1], 'Translated bookmark')
            clip = pymupdf.Rect(200, 150, 380, 220)
            self.assertEqual(original[0].get_pixmap(clip=clip).samples,
                             final[0].get_pixmap(clip=clip).samples)

    def test_failed_build_with_no_prior_output_creates_nothing(self):
        self.update_mapping(lambda c: c['targets'][0]['runs'][0].update(text='word ' * 100))
        with self.assertRaises(PdfTranslateError):
            self.build()
        self.assertFalse(self.job['output'].exists())
        self.assertFalse((self.work / 'scale_report.json').exists())

    def test_legacy_result_has_no_new_serialized_key(self):
        self.assertNotIn('typography', RetypesetResult().to_dict())

    def test_translated_neighbors_cannot_overlap_each_other(self):
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=200)
            page.insert_text((30, 60), 'Pay', fontname='helv', fontsize=12)
            page.insert_text((180, 60), 'Pay', fontname='tiit', fontsize=12)
            doc.save(self.job['original'])
        self.reextract()
        def targets(conf):
            self.assertEqual(len(conf['targets']), 2)
            conf['targets'][0]['runs'][0]['text'] = 'W' * 100
            conf['targets'][1]['runs'][0]['text'] = 'f'
            conf['allow_scale'] = [{'occurrence_id': 's0', 'reason': 'Exercise the edge at the existing floor exception'}]
        self.update_mapping(targets)
        self.refuses('unsafe-typography-geometry')

    def test_all_eight_class_role_faces_draw_at_the_source_color_and_baseline(self):
        source_faces = ['helv', 'hebo', 'heit', 'hebi', 'tiro', 'tibo', 'tiit', 'tibi']
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=300)
            for index, name in enumerate(source_faces):
                page.insert_text((30, 30 + index * 30), 'Pay', fontname=name,
                                 fontsize=12, color=(0, 0, 1))
            doc.save(self.job['original'])
        self.reextract()
        result = self.build()
        self.assertEqual(len(result.typography['fonts']), 8)
        spans = raw_spans(self.job['output'])
        self.assertEqual([s['font'] for s in spans], [
            'NotoSans-Regular', 'NotoSans-Bold', 'NotoSans-Italic', 'NotoSans-BoldItalic',
            'NotoSerif-Regular', 'NotoSerif-Bold', 'NotoSerif-Italic', 'NotoSerif-BoldItalic'])
        for index, span in enumerate(spans):
            self.assertEqual(span['text'], 'Pay')
            self.assertEqual(span['color'], 0x0000ff)
            self.assertAlmostEqual(span['origin'][1], 30 + index * 30, delta=0.05)

    def test_missing_glyph_has_typed_occurrence_context(self):
        self.update_mapping(lambda c: c['targets'][0]['runs'][0].update(text='日本語'))
        exc = self.refuses('missing-glyph')
        self.assertIsInstance(exc, GlyphError)
        item = exc.refusals['typography'][0]
        self.assertEqual((item['occurrence_id'], item['run_id'], item['page'], item['source_text']),
                         ('s0', 's0/r0', 0, 'Pay NOW'))

    def test_conflicting_codepoints_for_one_glyph_refuse_without_normalization(self):
        path = self.work / 'shared-glyph.ttf'
        with TTFont(latin_font_sets()['sans']['regular']) as font:
            for cmap in font['cmap'].tables:
                if cmap.isUnicode() and 0x20 in cmap.cmap:
                    cmap.cmap[0xa0] = cmap.cmap[0x20]
            font.save(path)
        actual = pymupdf.Font(fontfile=str(path))
        self.assertEqual(actual.has_glyph(0x20, fallback=False), actual.has_glyph(0xa0, fallback=False))
        self.update_mapping(lambda c: c['font_sets']['sans'].update(regular=str(path)))
        self.update_mapping(lambda c: c['targets'][0]['runs'][0].update(text='A B\u00a0C'))
        self.refuses('unsupported-typography-construct')

    def test_distinct_unicode_glyph_choices_are_canonicalized_per_face(self):
        self.update_mapping(lambda c: c['targets'][0]['runs'][0].update(text='A\u00a0B'))
        self.build()
        self.assertEqual([s['text'] for s in raw_spans(self.job['output'])], ['A\u00a0B', 'NOW', 'Pay ', 'NOW'])

    def test_cancellation_between_pages_never_publishes_partial_output(self):
        self.mutate_pdf('original', lambda d: d.new_page(width=400, height=240))
        self.reextract()
        calls, progress = [], []
        def cancel():
            calls.append(True)
            return len(calls) > 1
        result = self.build(cancel=cancel, progress=lambda done, total: progress.append((done, total)))
        self.assertTrue(result.cancelled)
        self.assertEqual(progress, [(1, 2)])
        self.assertIsNone(result.output)
        self.assertFalse(self.job['output'].exists())

    def test_existing_widget_identity_and_geometry_survive(self):
        def add_widget(doc):
            widget = pymupdf.Widget()
            widget.field_name, widget.field_type = 'answer', pymupdf.PDF_WIDGET_TYPE_TEXT
            widget.rect = pymupdf.Rect(200, 180, 290, 210)
            doc[0].add_widget(widget)
        self.mutate_pdf('original', add_widget)
        self.reextract()
        self.build()
        with pymupdf.open(self.job['output']) as doc:
            widgets = list(doc[0].widgets())
            self.assertEqual(len(widgets), 1)
            self.assertEqual(widgets[0].field_name, 'answer')
            self.assertEqual(list(widgets[0].rect), [200, 180, 290, 210])


if __name__ == '__main__':
    unittest.main()
