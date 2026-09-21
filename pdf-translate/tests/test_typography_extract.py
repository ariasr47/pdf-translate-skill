"""Catch style flattening, lost source evidence and unbound extractions."""
import copy
import inspect
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from fontTools.ttLib import TTFont
import pymupdf

from pdf_translate import run_extract
from tests.typography_fixtures import make_source, raw_spans


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.source = make_source(self.work / 'original.pdf')

    def extract(self, source=None, name='job', **options):
        # The rest of each test still exercises behavior when the API exists.
        self.assertIn('typography', inspect.signature(run_extract).parameters)
        result = run_extract(str(source or self.source), str(self.work / name),
                             typography=True, **options)
        data = json.loads(Path(result.segments_path).read_text(encoding='utf-8'))
        return result, data

    def test_repeated_text_retains_different_source_styles(self):
        self.assertEqual({s['font'] for s in raw_spans(self.source)},
                         {'Helvetica', 'Helvetica-Bold', 'Times-Roman',
                          'Times-BoldItalic'})
        result, data = self.extract()
        first, second = data['segments']
        self.assertEqual((first['text'], second['text']), ('Pay NOW', 'Pay NOW'))
        self.assertEqual([s['occurrence_id'] for s in data['segments']], ['s0', 's1'])
        self.assertEqual([r['bold'] for r in first['style_runs']], [False, True])
        self.assertEqual([r['class'] for r in second['style_runs']], ['serif', 'serif'])
        self.assertEqual([r['italic'] for r in second['style_runs']], [False, True])
        self.assertEqual(first['style_runs'][1]['offsets'], [4, 7])
        self.assertEqual(first['style_runs'][1]['run_id'], 's0/r1')
        self.assertEqual(result.to_dict()['typography'], data['typography'])
        for segment in data['segments']:
            self.assertEqual(''.join(r['text'] for r in segment['style_runs']),
                             segment['text'])
            for run in segment['style_runs']:
                a, b = run['offsets']
                self.assertEqual(segment['text'][a:b], run['text'])
                self.assertIn(run['font_id'], data['typography']['fonts'])

    def test_default_extraction_retains_legacy_shapes(self):
        result = run_extract(str(self.source), str(self.work / 'legacy'))
        data = json.loads(Path(result.segments_path).read_text(encoding='utf-8'))
        self.assertEqual(set(data), {'source', 'segments', 'warnings', 'document', 'pages'})
        self.assertNotIn('typography', result.to_dict())
        self.assertNotIn('style_runs', data['segments'][0])

    def test_binding_changes_with_source_options_and_every_style_record(self):
        _, data = self.extract()
        from pdf_translate.typography import bind_extraction
        original = data['typography']['extraction_id']
        for mutation in ('order', 'style', 'geometry', 'source', 'font'):
            edited = copy.deepcopy(data)
            if mutation == 'order':
                edited['segments'].reverse()
            elif mutation == 'style':
                edited['segments'][0]['style_runs'][0]['bold'] = True
            elif mutation == 'geometry':
                edited['segments'][0]['bbox'][0] += 1
            elif mutation == 'source':
                edited['typography']['source_sha256'] = '0' * 64
            else:
                first = next(iter(edited['typography']['fonts'].values()))
                first['name'] += ' changed'
            with self.subTest(mutation=mutation):
                self.assertNotEqual(bind_extraction(edited)['extraction_id'], original)
        _, changed_gap = self.extract(name='gap', gap=11)
        self.assertNotEqual(changed_gap['typography']['extraction_id'], original)
        other = self.work / 'changed.pdf'
        with pymupdf.open(self.source) as doc:
            doc.set_metadata({'title': 'Changed source'})
            doc.save(other)
        _, changed_pdf = self.extract(other, name='source-change')
        self.assertNotEqual(changed_pdf['typography']['extraction_id'], original)

    def test_moving_input_files_does_not_change_binding(self):
        _, data = self.extract()
        copied = self.work / 'copied.pdf'
        shutil.copyfile(self.source, copied)
        _, moved = self.extract(copied, name='moved')
        self.assertEqual(data['typography']['extraction_id'],
                         moved['typography']['extraction_id'])

    def test_full_page_geometry_survives_selective_extraction(self):
        source = self.work / 'two-pages.pdf'
        with pymupdf.open(self.source) as doc:
            doc.new_page(width=410, height=250)
            doc.save(source)
        _, complete = self.extract(source, name='all')
        _, selected = self.extract(source, name='selected', pages='1')
        self.assertEqual(len(selected['typography']['page_geometry']), 2)
        self.assertEqual(selected['typography']['options']['pages'], [0])
        self.assertNotEqual(complete['typography']['extraction_id'],
                            selected['typography']['extraction_id'])

    def test_whitespace_and_mixed_size_color_are_retained(self):
        path = self.work / 'spaces.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((30, 60), '  Pay ', fontname='helv', fontsize=12)
            x = 30 + pymupdf.get_text_length('  Pay ', fontname='helv', fontsize=12)
            page.insert_text((x, 60), 'NOW  ', fontname='hebo', fontsize=13,
                             color=(1, 0, 0))
            doc.save(path)
        self.assertEqual(''.join(s['text'] for s in raw_spans(path)), '  Pay NOW  ')
        _, data = self.extract(path)
        segment = data['segments'][0]
        self.assertEqual(segment['text'], '  Pay NOW  ')
        self.assertEqual([r['size'] for r in segment['style_runs']], [12, 13])
        self.assertEqual([r['color'] for r in segment['style_runs']], [0, 0xff0000])

    def test_rotated_source_retains_direction_and_baseline(self):
        source = self.work / 'rotated.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((80, 160), 'Side label', fontname='helv', rotate=90)
            doc.save(source)
        _, data = self.extract(source)
        segment = data['segments'][0]
        self.assertEqual(segment['dir'], [0.0, -1.0])
        self.assertEqual(segment['style_runs'][0]['origin'], [80.0, 160.0])

    def test_unknown_class_is_evidence_and_warning_not_guessed_sans(self):
        source = self.work / 'courier.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((30, 60), 'Code label', fontname='cour')
            doc.save(source)
        _, data = self.extract(source)
        run = data['segments'][0]['style_runs'][0]
        self.assertEqual(run['class'], 'unknown')
        self.assertTrue(run['evidence'])
        self.assertTrue(any(w['kind'] == 'typography' for w in data['warnings']))

    def test_embedded_sans_uses_program_metadata_without_family_name_guess(self):
        source = self.work / 'embedded.pdf'
        font = Path(__file__).parent / 'fonts/NotoSans-Regular.ttf'
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((30, 60), 'Invoice', fontname='fixture', fontfile=str(font))
            doc.save(source)
        _, data = self.extract(source)
        run = data['segments'][0]['style_runs'][0]
        self.assertEqual((run['class'], run['bold'], run['italic']), ('sans', False, False))
        observation = data['typography']['fonts'][run['font_id']]
        self.assertEqual(len(observation['sha256']), 64)
        self.assertIn('panose', observation['evidence'])

    def test_same_name_resources_are_not_selected_arbitrarily(self):
        font = Path(__file__).parent / 'fonts/NotoSans-Regular.ttf'
        paths = []
        for index, weight in enumerate((400, 700)):
            target = self.work / f'face{index}.ttf'
            with TTFont(font) as face:
                for rec in face['name'].names:
                    if rec.nameID in (1, 4, 6, 16):
                        rec.string = 'SharedName'.encode(rec.getEncoding())
                face['OS/2'].usWeightClass = weight
                face.save(target)
            paths.append(target)
        source = self.work / 'ambiguous.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page()
            for index, path in enumerate(paths):
                page.insert_text((30, 60 + index * 30), 'Label',
                                 fontname=f'resource{index}', fontfile=str(path))
            doc.save(source)
        self.assertEqual({s['font'] for s in raw_spans(source)}, {'SharedName'})
        _, data = self.extract(source)
        for segment in data['segments']:
            run = segment['style_runs'][0]
            self.assertIsNone(run['font_id'])
            self.assertEqual(run['class'], 'unknown')
            self.assertEqual(len(run['candidates']), 2)
        # The deliberately inconsistent second face must not be called bold
        # merely because its weight field says 700 while head/selection do not.
        observations = list(data['typography']['fonts'].values())
        conflicted = [obs for obs in observations if obs['evidence']['weight'] == 700]
        self.assertEqual(len(conflicted), 1)
        self.assertIsNone(conflicted[0]['bold'])
        self.assertIn('unknown-or-conflicting-weight', conflicted[0]['unresolved'])

    def test_nonfinite_geometry_cannot_be_bound(self):
        _, data = self.extract()
        from pdf_translate.typography import bind_extraction
        data['segments'][0]['bbox'][0] = float('nan')
        with self.assertRaises(ValueError):
            bind_extraction(data)


if __name__ == '__main__':
    unittest.main()
