"""PDF advances and crop bounds must use the units of the actual drawing."""
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
import pikepdf
import pymupdf

from pdf_translate import run_extract, run_retypeset, run_strip
from pdf_translate.mapping import load_mapping
from pdf_translate.results import MappingError
from pdf_translate.retypeset import _glyph_inks, _measure_typography
from pdf_translate.typography_verify import inspect_output
from tests.typography_fixtures import latin_font_sets, make_job, make_mapping


class TypographyWidthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.font_tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.font_tmp.cleanup)
        cls.fonts = latin_font_sets()
        # Portable OFL fixtures: no dependency on installed Arial or Times.
        for family, roles in cls.fonts.items():
            for role, source in roles.items():
                path = Path(cls.font_tmp.name) / f'{family}-{role}-2048.ttf'
                with TTFont(source) as font:
                    scale_upem(font, 2048)
                    font.save(path)
                roles[role] = str(path)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)
        self.job = make_job(self.work, font_sets=self.fonts,
                            prefix_text='Pay this amount in full before ')
        self.build()

    def build(self):
        return run_retypeset(*(str(self.job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                             original=str(self.job['original']))

    def change_mapping(self, change):
        data = json.loads(self.job['mapping'].read_text(encoding='utf-8'))
        change(data)
        self.job['mapping'].write_text(json.dumps(data), encoding='utf-8')

    def check(self, status):
        before = self.job['output'].read_bytes()
        gate = inspect_output(str(self.job['original']), str(self.job['output']),
                              load_mapping(self.job['mapping'], self.job['segments']))
        self.assertEqual(gate.status, status, gate.to_dict())
        self.assertEqual(before, self.job['output'].read_bytes())
        return gate

    def mutate_pdf(self, change):
        with pikepdf.open(self.job['output']) as doc:
            change(doc)
            out = io.BytesIO()
            doc.save(out)
        self.job['output'].write_bytes(out.getvalue())

    def test_long_2048_unit_faces_pass_with_real_embedded_programs(self):
        with pymupdf.open(self.job['output']) as doc:
            spans = doc[0].get_texttrace()
            self.assertEqual([s['font'] for s in spans],
                             ['NotoSans-Regular', 'NotoSans-Bold',
                              'NotoSerif-Regular', 'NotoSerif-BoldItalic'])
            for xref, ext, *_ in doc[0].get_fonts():
                if ext == 'ttf':
                    with TTFont(io.BytesIO(doc.extract_font(xref)[3])) as font:
                        self.assertEqual(font['head'].unitsPerEm, 2048)
        self.check('PASS')

    def test_2048_unit_widths_follow_uniform_shrink_and_style_boundaries(self):
        self.change_mapping(lambda data: [t['runs'][0].update(
            text='Pay this amount in full before ' * 2) for t in data['targets']])
        result = self.build()
        self.assertTrue(all(0.7 < o['scale'] < 1 for o in result.typography['occurrences']))
        self.check('PASS')

    def test_same_face_authored_runs_can_share_one_pdf_span(self):
        def split(data):
            runs = data['targets'][0]['runs']
            second = deepcopy(runs[0])
            second['text'] = 'the due date '
            runs.insert(1, second)
        self.change_mapping(split)
        self.build()
        with pymupdf.open(self.job['output']) as doc:
            self.assertEqual(len(doc[0].get_texttrace()), 4)
        self.check('PASS')

    def test_subsetting_preserves_width_attestation(self):
        with pymupdf.open(self.job['output']) as doc:
            doc.subset_fonts()
            data = doc.tobytes()
        self.job['output'].write_bytes(data)
        self.check('PASS')

    def exact_widths(self):
        def exact_widths(doc):
            for resource in doc.pages[0].Resources.Font.values():
                if resource.get('/Subtype') != pikepdf.Name.Type0:
                    continue
                descendant = resource.DescendantFonts[0]
                with TTFont(io.BytesIO(descendant.FontDescriptor.FontFile2.read_bytes())) as font:
                    widths = [font['hmtx'].metrics[g][0] * 1000 / font['head'].unitsPerEm
                              for g in font.getGlyphOrder()]
                descendant.W = pikepdf.Array([0, pikepdf.Array(widths)])
        self.mutate_pdf(exact_widths)

    def test_pdf_with_exact_fractional_widths_also_passes(self):
        self.exact_widths()
        self.check('PASS')

    def test_changed_pdf_widths_cannot_redefine_correct_spacing(self):
        self.exact_widths()
        def wrong_width(doc):
            descendant = doc.pages[0].Resources.Font.F0.DescendantFonts[0]
            with TTFont(io.BytesIO(descendant.FontDescriptor.FontFile2.read_bytes())) as font:
                gid = font.getGlyphID(font.getBestCmap()[ord('P')])
            # 0.024pt at 12pt stays within position tolerance. Width evidence
            # must independently fail even when all glyph positions look close.
            descendant.W[1][gid] = float(descendant.W[1][gid]) + 2
        self.mutate_pdf(wrong_width)
        gate = self.check('FAIL')
        self.assertTrue(any('PDF glyph width differs' in f.text for f in gate.findings))

    def test_default_pdf_width_is_used_for_omitted_glyph(self):
        self.exact_widths()
        def default_width(doc):
            descendant = doc.pages[0].Resources.Font.F0.DescendantFonts[0]
            widths = list(descendant.W[1])
            with TTFont(io.BytesIO(descendant.FontDescriptor.FontFile2.read_bytes())) as font:
                gid = font.getGlyphID(font.getBestCmap()[ord('P')])
            descendant.DW = int(widths[gid])
            descendant.W = pikepdf.Array([0, pikepdf.Array(widths[:gid]),
                                          gid + 1, pikepdf.Array(widths[gid + 1:])])
        self.mutate_pdf(default_width)
        self.check('PASS')

    def test_range_form_pdf_widths_are_equivalent(self):
        self.exact_widths()
        def ranges(doc):
            for resource in doc.pages[0].Resources.Font.values():
                if resource.get('/Subtype') != pikepdf.Name.Type0:
                    continue
                descendant = resource.DescendantFonts[0]
                widths = [item for gid, width in enumerate(descendant.W[1])
                          for item in (gid, gid, width)]
                descendant.W = pikepdf.Array(widths)
        self.mutate_pdf(ranges)
        self.check('PASS')

    def test_identical_font_programs_require_equivalent_pdf_widths(self):
        self.exact_widths()
        original = self.job['output'].read_bytes()
        for delta, status in ((0, 'PASS'), (2, 'REVIEW')):
            with self.subTest(delta=delta):
                self.job['output'].write_bytes(original)
                def duplicate(doc):
                    page = doc.pages[0]
                    copy = pikepdf.Dictionary(page.Resources.Font.F0)
                    descendant = pikepdf.Dictionary(copy.DescendantFonts[0])
                    widths = list(descendant.W[1])
                    with TTFont(io.BytesIO(descendant.FontDescriptor.FontFile2.read_bytes())) as font:
                        gid = font.getGlyphID(font.getBestCmap()[ord('P')])
                        space = font.getGlyphID(font.getBestCmap()[ord(' ')])
                    widths[gid] = float(widths[gid]) + delta
                    descendant.W = pikepdf.Array([0, pikepdf.Array(widths)])
                    copy.DescendantFonts = pikepdf.Array([doc.make_indirect(descendant)])
                    page.Resources.Font.F5 = doc.make_indirect(copy)
                    # Register a real drawing through the second resource;
                    # unassigned whitespace is permitted by the existing gate.
                    stream = f'q BT /F5 12 Tf 1 0 0 1 350 80 Tm [<{space:04x}>]TJ ET Q'.encode('ascii')
                    page.Contents = pikepdf.Array(list(page.Contents) + [doc.make_stream(stream)])
                self.mutate_pdf(duplicate)
                gate = self.check(status)
                if status == 'REVIEW':
                    self.assertTrue(any('font resource is ambiguous' in f.text for f in gate.findings))

    def test_unresolved_cid_mapping_cannot_claim_width_attestation(self):
        self.exact_widths()
        def mapping_stream(doc):
            descendant = doc.pages[0].Resources.Font.F0.DescendantFonts[0]
            count = len(descendant.W[1])
            # Valid explicit identity stream; this conservative verifier only
            # proves the absent/name Identity mapping, not arbitrary streams.
            descendant.CIDToGIDMap = doc.make_stream(b''.join(g.to_bytes(2, 'big') for g in range(count)))
        self.mutate_pdf(mapping_stream)
        gate = self.check('REVIEW')
        self.assertTrue(any('unsupported PDF glyph widths' in f.text for f in gate.findings))

    def test_extra_character_spacing_is_still_a_failure(self):
        def shifted(doc):
            page = doc.pages[0]
            content = b'\n'.join(s.read_bytes() for s in page.Contents)
            page.Contents = doc.make_stream(content.replace(b'BT\n', b'BT\n0.1 Tc\n'))
        self.mutate_pdf(shifted)
        self.check('FAIL')

    def test_shifted_style_boundary_is_still_a_failure(self):
        with pymupdf.open(self.job['output']) as doc:
            before = doc[0].get_texttrace()[1]['chars'][0][2][0]
        def shifted(doc):
            page = doc.pages[0]
            instructions = list(pikepdf.parse_content_stream(page))
            after_bold = False
            for index, instruction in enumerate(instructions):
                if str(instruction.operator) == 'Tf':
                    after_bold = str(instruction.operands[0]) == '/F1'
                if after_bold and str(instruction.operator) == 'Tm':
                    operands = list(instruction.operands)
                    operands[4] = float(operands[4]) + 0.2
                    instructions[index] = pikepdf.ContentStreamInstruction(operands, instruction.operator)
            page.Contents = doc.make_stream(pikepdf.unparse_content_stream(instructions))
        self.mutate_pdf(shifted)
        with pymupdf.open(self.job['output']) as doc:
            self.assertAlmostEqual(doc[0].get_texttrace()[1]['chars'][0][2][0] - before, 0.2, delta=0.0001)
        self.check('FAIL')


class TypographyUnrotatedFrameTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)

    def job(self, width, height, origin):
        job = {key: self.work / name for key, name in (
            ('original', 'source.pdf'), ('stripped', 'stripped.pdf'),
            ('segments', 'segments.json'), ('mapping', 'translations.json'), ('output', 'out.pdf'))}
        with pymupdf.open() as doc:
            page = doc.new_page(width=width + 40, height=height + 60)
            page.set_cropbox(pymupdf.Rect(20, 30, width + 20, height + 30))
            page.insert_text(origin, 'Pay NOW', fontname='helv', fontsize=12)
            doc.save(job['original'])
        self.extract(job)
        return job

    def extract(self, job):
        run_strip(str(job['original']), str(job['stripped']))
        run_extract(str(job['original']), str(self.work), typography=True)
        data = json.loads(job['segments'].read_text(encoding='utf-8'))
        job['mapping'].write_text(json.dumps(make_mapping(data, latin_font_sets())), encoding='utf-8')
        return load_mapping(job['mapping'], job['segments'])

    def rotate(self, path, rotation):
        with pymupdf.open(path) as doc:
            doc[0].set_rotation(rotation)
            data = doc.tobytes()
        path.write_bytes(data)

    def test_measurements_do_not_change_with_page_rotation_or_crop_offset(self):
        for width, height, origin in [(400, 240, (280, 60)), (240, 400, (30, 380))]:
            job = self.job(width, height, origin)
            document = load_mapping(job['mapping'], job['segments'])
            target, segment = document.targets[0], document.extraction['segments'][0]
            key = ('sans', 'regular')
            path = document.font_sets[key[0]][key[1]]
            font = pymupdf.Font(fontfile=path)
            inks = _glyph_inks(path, font, set(target.runs[0].text))
            with pymupdf.open(job['original']) as doc:
                def measure():
                    return _measure_typography(doc[0], segment, target, {key: font}, {key: inks},
                                               [segment], [], [], {})
                expected = measure()
                for rotation in (90, 180, 270):
                    with self.subTest(width=width, height=height, rotation=rotation):
                        doc[0].set_rotation(rotation)
                        self.assertEqual(measure(), expected)

    def test_independent_verification_uses_unrotated_crop_at_every_rotation(self):
        for width, height, origin in [(400, 240, (280, 60)), (240, 400, (30, 380))]:
            job = self.job(width, height, origin)
            run_retypeset(*(str(job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                          original=str(job['original']))
            for rotation in (0, 90, 180, 270):
                with self.subTest(width=width, height=height, rotation=rotation):
                    for key in ('original', 'output'):
                        self.rotate(job[key], rotation)
                    document = self.extract(job)
                    gate = inspect_output(str(job['original']), str(job['output']), document)
                    self.assertEqual(gate.status, 'PASS', gate.to_dict())

    def test_rotation_does_not_hide_real_crop_overflow(self):
        job = self.job(240, 400, (185, 60))
        document = load_mapping(job['mapping'], job['segments'])
        path = document.font_sets['sans']['regular']
        # A longer authored target overflows the real 240pt crop, while a
        # /Rotate 90 viewer rectangle misleadingly allows 400pt of width.
        conf = json.loads(job['mapping'].read_text(encoding='utf-8'))
        conf['targets'][0]['runs'][0]['text'] = 'Pay NOW please'
        with pymupdf.open(job['stripped']) as doc:
            writer = pymupdf.TextWriter(doc[0].rect)
            writer.append((185, 60), 'Pay NOW please', font=pymupdf.Font(fontfile=path), fontsize=12)
            writer.write_text(doc[0])
            doc.save(job['output'])
        for key in ('original', 'output'):
            self.rotate(job[key], 90)
        rebound = self.extract(job)
        conf['extraction_id'] = rebound.extraction_id
        job['mapping'].write_text(json.dumps(conf), encoding='utf-8')
        gate = inspect_output(str(job['original']), str(job['output']),
                              load_mapping(job['mapping'], job['segments']))
        self.assertEqual(gate.status, 'FAIL', gate.to_dict())
        self.assertTrue(any('outside the page crop' in f.text for f in gate.findings), gate.to_dict())

    def test_public_build_still_refuses_rotated_source(self):
        job = self.job(400, 240, (280, 60))
        self.rotate(job['original'], 90)
        self.extract(job)
        job['output'].write_bytes(b'previous output')
        with self.assertRaises(MappingError) as caught:
            run_retypeset(*(str(job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                          original=str(job['original']))
        self.assertEqual(caught.exception.refusals['typography'][0]['reason'],
                         'unsupported-typography-construct')
        self.assertEqual(job['output'].read_bytes(), b'previous output')


if __name__ == '__main__':
    unittest.main()
