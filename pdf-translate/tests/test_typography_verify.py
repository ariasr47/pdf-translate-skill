"""Final-file inspection must defeat incorrect PDFs beside truthful old reports."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from fontTools.ttLib import TTFont
import pymupdf

from pdf_translate import run_extract, run_field_fonts, run_prepare_font, run_retypeset, run_strip, run_verify
from pdf_translate.mapping import load_mapping
from pdf_translate.results import MappingError
from tests.typography_fixtures import (draw_independently, independent_rows,
                                       latin_font_sets, make_job, make_mapping)


class TypographyVerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.job = make_job(self.work)
        self.build()

    def build(self):
        result = run_retypeset(*(str(self.job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                               original=str(self.job['original']))
        self.report = (self.work / 'scale_report.json').read_bytes()
        return result

    def reextract(self):
        run_strip(str(self.job['original']), str(self.job['stripped']))
        run_extract(str(self.job['original']), str(self.work), typography=True)
        data = json.loads(self.job['segments'].read_text(encoding='utf-8'))
        self.job['mapping'].write_text(json.dumps(make_mapping(data, latin_font_sets())), encoding='utf-8')

    def update_mapping(self, change):
        conf = json.loads(self.job['mapping'].read_text(encoding='utf-8'))
        change(conf)
        self.job['mapping'].write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')

    def verify(self, context=True, **kwargs):
        if context:
            kwargs.setdefault('translations', str(self.job['mapping']))
            kwargs.setdefault('segments', str(self.job['segments']))
        before = self.job['output'].read_bytes()
        verdict = run_verify(str(self.job['original']), str(self.job['output']), **kwargs)
        self.assertEqual(self.job['output'].read_bytes(), before, 'verification changed the delivered PDF')
        self.assertEqual((self.work / 'scale_report.json').read_bytes(), self.report)
        checks = [g for g in verdict.gates if g.name == 'typography']
        self.assertEqual(len(checks), 1, 'the requested typography check is absent')
        return verdict, checks[0]

    def tamper(self, change, pages=1):
        rows = independent_rows()
        change(rows)
        draw_independently(self.job['output'], rows, pages)
        self.assertEqual((self.work / 'scale_report.json').read_bytes(), self.report)

    def test_missing_context_is_cannot_attest_and_honors_fail_on_review(self):
        _, check = self.verify(context=False, typography=True)
        self.assertEqual(check.status, 'REVIEW')
        self.assertIn('cannot attest', check.message.lower())
        verdict, _ = self.verify(context=False, typography=True, fail_on_review=True)
        self.assertEqual(verdict.exit_code, 1)

    def test_new_mapping_selects_actual_typography_verification(self):
        _, check = self.verify()
        self.assertEqual(check.status, 'PASS', check.to_dict())

    def test_missing_extraction_is_cannot_attest_not_a_pass(self):
        _, check = self.verify(segments=str(self.work / 'missing.json'), typography=True)
        self.assertEqual(check.status, 'REVIEW')
        self.assertIn('cannot attest', check.message.lower())

    def test_stale_extraction_binding_is_an_input_error(self):
        self.update_mapping(lambda c: c.update(extraction_id='0' * 64))
        with self.assertRaises(MappingError):
            self.verify()
        self.assertTrue(self.job['output'].is_file())

    def test_independent_correct_output_passes_without_using_the_report(self):
        draw_independently(self.job['output'], independent_rows())
        _, check = self.verify()
        self.assertEqual(check.status, 'PASS', check.to_dict())

    def test_same_words_at_other_occurrence_cannot_satisfy_missing_text(self):
        self.tamper(lambda rows: rows.__setitem__(slice(0, 2), []))
        verdict, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())
        self.assertEqual(verdict.exit_code, 1)
        self.assertTrue(any('s0' in f.where for f in check.findings))
        self.assertTrue(all(f.page in (None, 1) for f in check.findings))

    def test_swapped_bold_regular_cannot_be_attested_by_the_old_report(self):
        def swap(rows):
            rows[0]['role'], rows[1]['role'] = 'bold', 'regular'
        self.tamper(swap)
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())

    def test_wrong_class_is_a_failure_even_when_the_words_and_role_match(self):
        self.tamper(lambda rows: rows[0].update(**{'class': 'serif'}))
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())

    def test_shifted_baseline_is_a_failure(self):
        self.tamper(lambda rows: rows[0].update(origin=(30, 61)))
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())

    def test_nonuniform_size_and_changed_color_are_failures(self):
        for mutation in ({'size': 10}, {'color': (1, 0, 0)}):
            self.tamper(lambda rows: rows[1].update(mutation))
            _, check = self.verify()
            self.assertEqual(check.status, 'FAIL', check.to_dict())

    def test_changed_font_outlines_fail_even_with_consistent_class_role_metadata(self):
        path = self.work / 'changed-outlines.ttf'
        with TTFont(latin_font_sets()['sans']['regular']) as font:
            name = font.getBestCmap()[ord('P')]
            glyph = font['glyf'][name]
            x, y = glyph.coordinates[0]
            glyph.coordinates[0] = (x + 70, y)
            glyph.recalcBounds(font['glyf'])
            font.save(path)
        self.tamper(lambda rows: rows[0].update(font=path))
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())

    def test_unknown_font_metadata_is_cannot_attest(self):
        path = self.work / 'unknown-class.ttf'
        with TTFont(latin_font_sets()['sans']['regular']) as font:
            font['OS/2'].sFamilyClass = 0
            font['OS/2'].panose.bFamilyType = 0
            font.save(path)
        self.tamper(lambda rows: rows[0].update(font=path))
        _, check = self.verify()
        self.assertEqual(check.status, 'REVIEW', check.to_dict())
        self.assertIn('cannot attest', check.message.lower())

    def test_subset_missing_post_does_not_hide_changed_outlines(self):
        path = self.work / 'changed-subset.ttf'
        with TTFont(latin_font_sets()['sans']['regular']) as font:
            glyph = font['glyf'][font.getBestCmap()[ord('P')]]
            x, y = glyph.coordinates[0]
            glyph.coordinates[0] = (x + 70, y)
            glyph.recalcBounds(font['glyf'])
            del font['post']
            font.save(path)
        self.tamper(lambda rows: rows[0].update(font=path))
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())

    def test_subset_missing_post_requires_consistent_surviving_metadata(self):
        path = self.work / 'unknown-subset.ttf'
        with TTFont(latin_font_sets()['sans']['regular']) as font:
            font['OS/2'].panose.bFamilyType = 0
            del font['post']
            font.save(path)
        self.tamper(lambda rows: rows[0].update(font=path))
        _, check = self.verify()
        self.assertEqual(check.status, 'REVIEW', check.to_dict())

    def test_extra_page_and_missing_blank_page_are_failures(self):
        draw_independently(self.job['output'], independent_rows(), pages=2)
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL')
        with pymupdf.open(self.job['original']) as doc:
            doc.new_page(width=400, height=240)
            data = doc.tobytes()
        self.job['original'].write_bytes(data)
        self.reextract()
        self.build()
        draw_independently(self.job['output'], independent_rows(), pages=1)
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL')

    def test_all_text_on_wrong_page_is_a_failure(self):
        with pymupdf.open(self.job['original']) as doc:
            doc.new_page(width=400, height=240)
            data = doc.tobytes()
        self.job['original'].write_bytes(data)
        self.reextract()
        self.build()
        self.tamper(lambda rows: [r.update(page=1) for r in rows], pages=2)
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL')

    def long_first_line(self, prefix):
        """Author and draw the first occurrence with `prefix` before its bold NOW."""
        self.update_mapping(lambda conf: conf['targets'][0]['runs'][0].update(text=prefix))
        regular = pymupdf.Font(fontfile=latin_font_sets()['sans']['regular'])
        x = 30 + regular.text_length(prefix, fontsize=12)

        def change(rows):
            rows[0]['text'] = prefix
            rows[1]['origin'] = (x, 60)
        self.tamper(change)
        return x

    def test_glyph_past_the_page_crop_is_a_failure(self):
        x = self.long_first_line('Pay this amount in full before the due date shown on the form ')
        self.assertLess(x, 400 - 1)
        self.assertGreater(x + 20, 400 + 1, 'fixture: NOW must cross the right edge')
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())
        self.assertIn('Run 1: glyph outline extends outside the page crop.',
                      [f['text'] for f in check.to_dict()['findings']])

    def test_glyph_over_a_source_field_is_a_failure(self):
        with pymupdf.open(self.job['original']) as doc:
            widget = pymupdf.Widget()
            widget.field_name, widget.field_type = 'answer', pymupdf.PDF_WIDGET_TYPE_TEXT
            widget.rect = pymupdf.Rect(150, 45, 250, 65)
            doc[0].add_widget(widget)
            data = doc.tobytes()
        self.job['original'].write_bytes(data)
        self.reextract()
        self.build()
        x = self.long_first_line('Pay the whole amount ')
        self.assertGreater(x, 150, 'fixture: NOW must start inside the field')
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())
        self.assertIn('Run 1: glyph outline overlaps source field answer.',
                      [f['text'] for f in check.to_dict()['findings']])

    def test_equal_style_output_may_coalesce_authored_runs(self):
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=240)
            page.insert_text((30, 60), 'Pay NOW', fontname='helv', fontsize=12)
            doc.save(self.job['original'])
        self.reextract()
        self.update_mapping(lambda c: c['targets'][0].update(runs=[
            {'text': 'Pague ', 'source_runs': ['s0/r0']}, {'text': 'ahora', 'source_runs': ['s0/r0']}]))
        self.build()
        draw_independently(self.job['output'], [{'page': 0, 'origin': (30, 60), 'size': 12,
            'class': 'sans', 'role': 'regular', 'text': 'Pague ahora'}])
        with pymupdf.open(self.job['output']) as doc:
            self.assertEqual(len(doc[0].get_texttrace()), 1)
        _, check = self.verify()
        self.assertEqual(check.status, 'PASS', check.to_dict())

    def test_clipped_italic_end_cannot_use_the_good_scale_report(self):
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=240)
            page.insert_text((30, 60), 'Pay', fontname='tiit', fontsize=12)
            doc.save(self.job['original'])
        self.reextract()
        self.update_mapping(lambda c: c['targets'][0]['runs'][0].update(text='f' * 100))
        self.build()
        draw_independently(self.job['output'], [{'page': 0, 'origin': (30, 60), 'size': 12,
            'class': 'serif', 'role': 'italic', 'text': 'f' * 100}])
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())

    def test_embedded_subset_identity_is_not_a_whole_file_hash(self):
        with pymupdf.open(self.job['output']) as doc:
            before = sum(len(doc.extract_font(f[0])[3]) for f in doc[0].get_fonts() if f[1] == 'ttf')
            doc.subset_fonts()
            data = doc.tobytes()
        self.job['output'].write_bytes(data)
        with pymupdf.open(self.job['output']) as doc:
            after = sum(len(doc.extract_font(f[0])[3]) for f in doc[0].get_fonts() if f[1] == 'ttf')
        self.assertLess(after, before)
        _, check = self.verify()
        self.assertEqual(check.status, 'PASS', check.to_dict())

    def test_final_field_font_embedding_preserves_page_typography(self):
        with pymupdf.open(self.job['original']) as doc:
            widget = pymupdf.Widget()
            widget.field_name, widget.field_type = 'answer', pymupdf.PDF_WIDGET_TYPE_TEXT
            widget.rect = pymupdf.Rect(200, 180, 290, 210)
            widget.field_value = 'User123'
            widget.text_font = 'Helv'
            widget.text_fontsize = 12
            doc[0].add_widget(widget)
            data = doc.tobytes()
        self.job['original'].write_bytes(data)
        self.reextract()
        mapping = load_mapping(self.job['mapping'])
        conf = json.loads(self.job['mapping'].read_text(encoding='utf-8'))
        for cls, role in {(r.font_class, r.font_role) for t in mapping.targets for r in t.runs}:
            subset = self.work / f'{cls}-{role}.ttf'
            run_prepare_font(mapping.font_sets[cls][role], str(self.job['mapping']), str(subset),
                             font_class=cls, font_role=role)
            conf['font_sets'][cls][role] = str(subset)
        self.job['mapping'].write_text(json.dumps(conf), encoding='utf-8')
        self.build()
        final = self.work / 'final.pdf'
        run_field_fonts(str(self.job['output']), latin_font_sets()['sans']['regular'], str(final))
        self.job['output'] = final
        with pymupdf.open(final) as doc:
            self.assertEqual(next(doc[0].widgets()).field_value, 'User123')
        _, check = self.verify()
        self.assertEqual(check.status, 'PASS', check.to_dict())

    def test_annotation_text_is_separate_but_annotation_occlusion_cannot_attest(self):
        original = self.job['output'].read_bytes()
        for rect, status in ((pymupdf.Rect(200, 180, 290, 210), 'PASS'),
                             (pymupdf.Rect(30, 48, 110, 68), 'REVIEW')):
            with pymupdf.open(stream=original, filetype='pdf') as doc:
                doc[0].add_freetext_annot(rect, 'A comment', fontsize=12)
                data = doc.tobytes()
            self.job['output'].write_bytes(data)
            _, check = self.verify()
            self.assertEqual(check.status, status, check.to_dict())

    def test_unknown_scale_report_schema_is_not_silently_accepted(self):
        module = importlib.import_module('pdf_translate.verify')
        report = self.work / 'scale_report.json'
        for schema, expected in [(1, []), (2, []), (99, None), (True, None)]:
            report.write_text(json.dumps({'schema': schema, 'runs': []}), encoding='utf-8')
            self.assertEqual(module.scale_report_for(str(self.job['output'])), expected)

    def test_clipping_or_shear_cannot_pass_with_unchanged_font_programs(self):
        original = self.job['output'].read_bytes()
        for prefix in (b'q 0 0 45 240 re W n\n', b'q 1 0 .5 1 -90 0 cm\n',
                       b'q 1 0 0 1 0 0 cm 80 Tz\n'):
            with pymupdf.open(stream=original, filetype='pdf') as doc:
                page = doc[0]
                page.clean_contents()
                xref = page.get_contents()[0]
                doc.update_stream(xref, prefix + doc.xref_stream(xref) + b'\nQ')
                data = doc.tobytes()
            self.job['output'].write_bytes(data)
            _, check = self.verify()
            self.assertIn(check.status, ('FAIL', 'REVIEW'), check.to_dict())
            self.assertTrue(check.findings)

    def test_restored_graphics_clip_does_not_taint_later_text(self):
        with pymupdf.open(self.job['output']) as doc:
            page = doc[0]
            page.clean_contents()
            xref = page.get_contents()[0]
            doc.update_stream(xref, b'q 0 0 10 10 re W n Q\n' + doc.xref_stream(xref))
            data = doc.tobytes()
        self.job['output'].write_bytes(data)
        _, check = self.verify()
        self.assertEqual(check.status, 'PASS', check.to_dict())

    def test_later_opaque_paint_over_glyphs_cannot_attest(self):
        with pymupdf.open(self.job['output']) as doc:
            doc[0].draw_rect(pymupdf.Rect(45, 48, 80, 65), fill=(1, 1, 1), color=None, overlay=True)
            data = doc.tobytes()
        self.job['output'].write_bytes(data)
        _, check = self.verify()
        self.assertIn(check.status, ('FAIL', 'REVIEW'), check.to_dict())

    def test_user_unit_cannot_change_physical_page_size_behind_equal_raw_boxes(self):
        with pymupdf.open(self.job['output']) as doc:
            page = doc[0]
            page.clean_contents()
            xref = page.get_contents()[0]
            doc.xref_set_key(page.xref, 'UserUnit', '2')
            doc.update_stream(xref, b'q .5 0 0 .5 0 120 cm\n' + doc.xref_stream(xref) + b'\nQ')
            data = doc.tobytes()
        self.job['output'].write_bytes(data)
        _, check = self.verify()
        self.assertEqual(check.status, 'FAIL', check.to_dict())


class FilledFormPageLoadTests(unittest.TestCase):
    """R-47: under field_fonts' NeedAppearances, every page load rebuilds the
    widget appearances and keeps them; one load per glyph took a 14-page form's
    verify to 4 GB. The check must load pages a fixed number of times."""

    def final_form(self, work, prefix_text):
        job = make_job(work, prefix_text=prefix_text)
        with pymupdf.open(job['original']) as doc:
            widget = pymupdf.Widget()
            widget.field_name, widget.field_type = 'answer', pymupdf.PDF_WIDGET_TYPE_TEXT
            widget.rect = pymupdf.Rect(200, 180, 290, 210)
            widget.field_value = 'User123'
            widget.text_font = 'Helv'
            widget.text_fontsize = 12
            doc[0].add_widget(widget)
            data = doc.tobytes()
        job['original'].write_bytes(data)
        run_strip(str(job['original']), str(job['stripped']))
        run_extract(str(job['original']), str(work), typography=True)
        extraction = json.loads(job['segments'].read_text(encoding='utf-8'))
        job['mapping'].write_text(json.dumps(make_mapping(extraction, latin_font_sets())), encoding='utf-8')
        run_retypeset(*(str(job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                      original=str(job['original']))
        final = work / 'final.pdf'
        run_field_fonts(str(job['output']), latin_font_sets()['sans']['regular'], str(final))
        return job, final

    def verify_counting_loads(self, job, final):
        loads = []
        load_page = pymupdf.Document.load_page

        def counted(doc, *args, **kwargs):
            if doc.name and Path(doc.name).resolve() == final.resolve():
                loads.append(args)
            return load_page(doc, *args, **kwargs)

        with mock.patch.object(pymupdf.Document, 'load_page', counted):
            verdict = run_verify(str(job['original']), str(final), translations=str(job['mapping']),
                                 segments=str(job['segments']), typography=True)
        return next(g for g in verdict.gates if g.name == 'typography'), len(loads)

    def test_page_loads_do_not_grow_with_the_glyphs_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            counts = {}
            for label, prefix in (('short', 'Pay '), ('long', 'Pay the full amount now ')):
                job, final = self.final_form(Path(tmp) / label, prefix)
                with pymupdf.open(final) as doc:
                    self.assertTrue(doc.pdf_catalog() and doc.xref_get_key(
                        doc.pdf_catalog(), 'AcroForm/NeedAppearances')[1] == 'true')
                    counts[label] = (sum(len(page.get_text('text').replace(' ', '').replace('\n', ''))
                                         for page in doc),)
                check, loads = self.verify_counting_loads(job, final)
                self.assertEqual(check.status, 'PASS', check.to_dict())
                counts[label] += (loads,)
            self.assertGreater(counts['long'][0], counts['short'][0] + 30, counts)
            self.assertEqual(counts['long'][1], counts['short'][1],
                             f'(glyphs, page loads) per form: {counts}')


if __name__ == '__main__':
    unittest.main()
