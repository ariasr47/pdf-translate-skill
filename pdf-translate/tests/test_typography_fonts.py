"""Real font programs, isolated class/role charsets and refusal behavior."""
from contextlib import contextmanager
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest

from fontTools.ttLib import TTFont
import pymupdf

from pdf_translate import run_extract, run_prepare_font
from pdf_translate.mapping import load_mapping
from pdf_translate.results import FontError
from tests.typography_fixtures import make_mapping, make_source


FONTS = Path(__file__).parent / 'fonts'
STYLES = {
    'sans': {'regular': 'helv', 'bold': 'hebo', 'italic': 'heit', 'bold_italic': 'hebi'},
    'serif': {'regular': 'tiro', 'bold': 'tibo', 'italic': 'tiit', 'bold_italic': 'tibi'},
}
SUFFIX = {'regular': 'Regular', 'bold': 'Bold', 'italic': 'Italic', 'bold_italic': 'BoldItalic'}


def face(font_class, role):
    family = 'NotoSans' if font_class == 'sans' else 'NotoSerif'
    path = FONTS / f'{family}-{SUFFIX[role]}.ttf'
    if not path.is_file():
        raise AssertionError(f'Required fixture missing: {path}; run tools/fetch_test_fonts.py')
    return path


@contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class TypographyFontTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)

    def inspect(self, path):
        module = importlib.import_module('pdf_translate.typography')
        self.assertTrue(hasattr(module, 'inspect_font'), 'font-program inspection is absent')
        return module.inspect_font(path)

    def mapping(self, font_class='sans', role='regular', text='Pague', lang='es'):
        job = self.work / f'{font_class}-{role}-{lang}'
        job.mkdir(exist_ok=True)
        original = job / 'original.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=400, height=200)
            page.insert_text((30, 60), 'Pay', fontname=STYLES[font_class][role], fontsize=12)
            pdf.save(original)
        extracted = run_extract(str(original), str(job), typography=True)
        data = json.loads(Path(extracted.segments_path).read_text(encoding='utf-8'))
        observed = data['segments'][0]['style_runs'][0]
        self.assertEqual((observed['class'], observed['bold'], observed['italic']),
                         (font_class, role in ('bold', 'bold_italic'), role in ('italic', 'bold_italic')))
        conf = make_mapping(data, {font_class: {role: 'prepared.ttf'}})
        conf['targets'][0]['runs'][0]['text'] = text
        conf['lang'] = lang
        mapping = job / 'translations.json'
        mapping.write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')
        return mapping, job / 'prepared.ttf'

    def prepare(self, source, mapping, output, font_class='sans', role='regular', **kwargs):
        return run_prepare_font(str(source), str(mapping), str(output),
                                font_class=font_class, font_role=role, **kwargs)

    def test_charset_is_only_for_selected_class_and_role(self):
        source = make_source(self.work / 'original.pdf')
        result = run_extract(str(source), str(self.work), typography=True)
        data = json.loads(Path(result.segments_path).read_text(encoding='utf-8'))
        conf = make_mapping(data)
        conf['targets'][0]['runs'][0]['text'] = 'pague'
        conf['targets'][0]['runs'][1]['text'] = 'AHORA'
        mapping = self.work / 'translations.json'
        mapping.write_text(json.dumps(conf), encoding='utf-8')
        module = importlib.import_module('pdf_translate.mapping')
        self.assertTrue(hasattr(module, 'charset_for'), 'role-specific charset is absent')
        self.assertEqual(module.charset_for(load_mapping(mapping), 'sans', 'bold'), set('AHORA'))

    def test_missing_selector_is_typed_refusal_before_output(self):
        mapping, output = self.mapping()
        with self.assertRaises(FontError) as caught:
            run_prepare_font(str(face('sans', 'regular')), str(mapping), str(output), font_class='sans')
        self.assertEqual(caught.exception.reason, 'missing-font-role')
        self.assertFalse(output.exists())

    def test_real_latin_roles_keep_class_and_style_after_subsetting(self):
        for cls in STYLES:
            for role in SUFFIX:
                with self.subTest(font_class=cls, role=role):
                    source = face(cls, role)
                    evidence = self.inspect(source)
                    expected = (cls, role in ('bold', 'bold_italic'), role in ('italic', 'bold_italic'))
                    self.assertEqual((evidence['class'], evidence['bold'], evidence['italic']), expected)
                    self.assertEqual(evidence['sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
                    mapping, output = self.mapping(cls, role)
                    result = self.prepare(source, mapping, output, cls, role)
                    self.assertEqual(result.roles, (role,))
                    actual = self.inspect(output)
                    self.assertEqual((actual['class'], actual['bold'], actual['italic']), expected)
                    font = pymupdf.Font(fontfile=str(output))
                    self.assertTrue(all(font.has_glyph(ord(ch), fallback=False) for ch in 'Pague'))

    def test_wrong_class_role_and_replaced_file_are_refused(self):
        mapping, output = self.mapping('sans', 'bold')
        selected = self.work / 'selected.ttf'
        shutil.copyfile(face('sans', 'bold'), selected)
        self.prepare(selected, mapping, output, role='bold')
        prior_hash = self.inspect(selected)['sha256']
        shutil.copyfile(face('sans', 'regular'), selected)
        self.assertNotEqual(prior_hash, self.inspect(selected)['sha256'])
        for source, reason in [(selected, 'wrong-font-role'),
                               (face('serif', 'bold'), 'wrong-font-class')]:
            with self.subTest(reason=reason), self.assertRaises(FontError) as caught:
                self.prepare(source, mapping, self.work / f'{reason}.ttf', role='bold')
            self.assertEqual(caught.exception.reason, reason)

    def test_unknown_or_conflicting_font_metadata_never_guesses(self):
        mapping, output = self.mapping()
        for case in ('class', 'weight', 'slant'):
            broken = self.work / f'{case}.ttf'
            with TTFont(face('sans', 'regular')) as font:
                if case == 'class':
                    font['OS/2'].sFamilyClass = 0
                    font['OS/2'].panose.bFamilyType = 0
                elif case == 'weight':
                    font['OS/2'].usWeightClass = 700
                else:
                    font['post'].italicAngle = -12
                font.save(broken)
            with self.subTest(case=case), self.assertRaises(FontError) as caught:
                self.prepare(broken, mapping, output)
            self.assertEqual(caught.exception.reason, 'unresolved-target-font')
            self.assertFalse(output.exists())

    def test_missing_glyph_fails_before_subset_and_never_uses_fallback(self):
        mapping, output = self.mapping(text='日本語', lang='ja')
        with self.assertRaises(FontError) as caught:
            self.prepare(face('sans', 'regular'), mapping, output)
        self.assertEqual(caught.exception.reason, 'missing-glyph')
        self.assertFalse(output.exists())

    def test_preparation_keeps_mapping_readonly_and_paths_relative_to_it(self):
        mapping, output = self.mapping()
        selected = mapping.parent / 'source.ttf'
        shutil.copyfile(face('sans', 'regular'), selected)
        before = mapping.read_bytes()
        mapping.chmod(stat.S_IREAD)
        try:
            with working_directory(self.work):
                self.prepare('source.ttf', mapping, output)
        finally:
            mapping.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.assertEqual(mapping.read_bytes(), before)
        self.assertTrue(output.is_file())

    def test_separate_faces_have_separate_charsets(self):
        first_map, first_out = self.mapping('sans', 'regular', text='pague')
        second_map, second_out = self.mapping('sans', 'bold', text='AHORA')
        self.prepare(face('sans', 'regular'), first_map, first_out)
        self.prepare(face('sans', 'bold'), second_map, second_out, role='bold')
        with TTFont(first_out) as regular, TTFont(second_out) as bold:
            self.assertEqual(set(regular.getBestCmap()), set(map(ord, 'pague')))
            self.assertEqual(set(bold.getBestCmap()), set(map(ord, 'AHORA')))

    def test_cjk_instancing_produces_actual_regular_and_bold_faces(self):
        for cls, family in [('sans', 'NotoSans'), ('serif', 'NotoSerif')]:
            for lang, suffix, target in [('ja', 'JP', '日本語'), ('zh-Hans', 'SC', '简体中文')]:
                source = FONTS / f'{family}{suffix}-VF.ttf'
                self.assertTrue(source.is_file(), f'Required fixture missing: {source}')
                outline_hashes = []
                for role, weight in [('regular', 400), ('bold', 700)]:
                    with self.subTest(font_class=cls, lang=lang, role=role):
                        mapping, output = self.mapping(cls, role, target, lang)
                        self.prepare(source, mapping, output, cls, role, instance=f'wght={weight}')
                        actual = self.inspect(output)
                        self.assertEqual((actual['class'], actual['bold'], actual['italic']),
                                         (cls, role == 'bold', False))
                        with TTFont(output) as font:
                            self.assertNotIn('fvar', font)
                            outline_hashes.append(hashlib.sha256(font.getTableData('glyf')).hexdigest())
                self.assertNotEqual(*outline_hashes, 'bold must change outlines, not only font metadata')

    def test_cjk_italic_without_a_genuine_face_refuses(self):
        source = FONTS / 'NotoSansJP-VF.ttf'
        for role, weight in [('italic', 400), ('bold_italic', 700)]:
            mapping, output = self.mapping('sans', role, '日本語', 'ja')
            with self.subTest(role=role), self.assertRaises(FontError) as caught:
                self.prepare(source, mapping, output, role=role, instance=f'wght={weight}')
            self.assertEqual(caught.exception.reason, 'wrong-font-role')
            self.assertFalse(output.exists())

    def test_variable_font_requires_a_concrete_instance(self):
        mapping, output = self.mapping(text='日本語', lang='ja')
        with self.assertRaises(FontError) as caught:
            self.prepare(FONTS / 'NotoSansJP-VF.ttf', mapping, output)
        self.assertEqual(caught.exception.reason, 'uninstantiated-font')
        self.assertFalse(output.exists())

    def test_cli_prepares_the_explicit_selection(self):
        mapping, output = self.mapping('serif', 'italic')
        module = importlib.import_module('pdf_translate.prepare_font')
        self.assertEqual(module.main([str(face('serif', 'italic')), str(mapping), str(output),
                                      '--font-class', 'serif', '--font-role', 'italic']), 0)
        self.assertEqual(self.inspect(output)['italic'], True)

    def test_unused_or_invalid_selectors_refuse(self):
        mapping, output = self.mapping()
        for cls, role in [('sans', None), (None, None), ('unknown', 'regular'),
                          ('sans', 'bold-italic'), ('serif', 'regular')]:
            with self.subTest(font_class=cls, role=role), self.assertRaises(FontError) as caught:
                self.prepare(face('sans', 'regular'), mapping, output, cls, role)
            self.assertEqual(caught.exception.reason, 'missing-font-role')
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
