"""Regression coverage for scoring the delivered PDF, not a diagnostic."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pymupdf

import score


SCHOOL = 'Riverside Elementary School'
SOURCE = 'Please return this form today.'
TARGET = 'Devuelva este formulario hoy.'


def make_pdf(path, sentence, lang='en'):
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), SCHOOL)
        page.insert_text((72, 100), sentence)
        doc.set_language(lang)
        doc.save(path)


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.run = self.base / 'run'
        self.run.mkdir()
        self.original = self.base / 'original.pdf'
        self.final = self.run / 'final.pdf'
        make_pdf(self.original, SOURCE)
        make_pdf(self.final, TARGET, 'es')

    def manifest(self, **extra):
        data = {'output': 'final.pdf', **extra}
        (self.run / 'delivery.json').write_text(json.dumps(data), encoding='utf-8')

    def score(self, **kwargs):
        with redirect_stdout(io.StringIO()):
            return score.score_run(str(self.original), str(self.run), **kwargs)

    def test_newer_nested_diagnostic_is_not_a_delivery_candidate(self):
        (self.run / 'tmp').mkdir()
        diagnostic = self.run / 'tmp' / 'filled.pdf'
        make_pdf(diagnostic, 'Diagnostic filled form only.')
        os.utime(diagnostic, (2000000000, 2000000000))
        selected = score.candidate_output(str(self.run), str(self.original))
        self.assertIsNotNone(selected)
        self.assertEqual(Path(selected), self.final.resolve())

    def test_multiple_outputs_require_an_explicit_choice(self):
        make_pdf(self.run / 'draft.pdf', 'Draft of this form.')
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            score.candidate_output(str(self.run), str(self.original))

    def test_same_size_different_pdf_is_not_discarded(self):
        # The source and translated words have equal byte lengths.
        make_pdf(self.original, 'aaaaaa')
        make_pdf(self.final, 'bbbbbb')
        size = max(self.original.stat().st_size, self.final.stat().st_size)
        for path in (self.original, self.final):
            with path.open('ab') as f:
                f.write(b'\n' * (size - path.stat().st_size))
        selected = score.candidate_output(str(self.run), str(self.original))
        self.assertIsNotNone(selected)
        self.assertEqual(Path(selected), self.final.resolve())

    def test_translated_output_may_keep_the_original_filename(self):
        renamed = self.run / self.original.name
        self.final.rename(renamed)
        self.assertEqual(Path(score.candidate_output(self.run, self.original)), renamed.resolve())
        make_pdf(self.run / 'draft.pdf', 'Draft of this form.')
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            score.candidate_output(self.run, self.original)

    def test_manifest_selects_output_and_replays_documented_allowlist(self):
        make_pdf(self.run / 'newest.pdf', 'Diagnostic filled form only.')
        with redirect_stdout(io.StringIO()):
            score.extract_segments.extract_segments(str(self.original), outdir=str(self.run))
        (self.run / 'translations.json').write_text(json.dumps({
            'lang': 'es', 'translations': {SCHOOL: SCHOOL, SOURCE: TARGET},
        }), encoding='utf-8')
        self.manifest(translations='translations.json', segments='segments.json',
                      allow=[SCHOOL], fill_text='José Muñoz')
        result = self.score()
        self.assertEqual(result['output'], 'final.pdf')
        self.assertEqual(result['verify_rc'], 0, result)
        self.assertEqual(result['verification']['allow'], [SCHOOL])
        self.assertIn('PASS authored translations present', result['verify_log'])
        self.assertEqual(result['verification']['fill_text'], 'José Muñoz')

    def test_allowlist_does_not_hide_other_untranslated_instructions(self):
        make_pdf(self.run / 'untranslated.pdf', SOURCE)
        self.manifest(output='untranslated.pdf', allow=[SCHOOL])
        result = self.score()
        self.assertEqual(result['verify_rc'], 1)
        self.assertIn('FAIL untranslated running text', result.get('verify_log', ''))

    def test_invalid_manifest_does_not_fall_back_to_a_different_pdf(self):
        for data in ({'output': 'missing.pdf'}, {'output': '../original.pdf'},
                     {'output': 'final.pdf', 'allow': SCHOOL},
                     {'output': 'final.pdf', 'translations': 'missing.json'}):
            with self.subTest(data=data):
                self.manifest(**data)
                result = self.score()
                self.assertIsNone(result['output'])
                self.assertIn('error', result)

    def test_explicit_output_overrides_manifest_and_report_location_is_configurable(self):
        make_pdf(self.run / 'draft.pdf', 'Diagnostic filled form only.')
        self.manifest(output='draft.pdf')
        report = self.run / '..' / 'score.json'
        before = {p.name: p.read_bytes() for p in self.run.iterdir()}
        with redirect_stdout(io.StringIO()):
            rc = score.main([str(self.original), str(self.run), '--output', 'final.pdf',
                             '--allow', SCHOOL, '--report', str(report)])
        self.assertEqual(rc, 0)
        self.assertTrue(report.is_file(), 'the requested report was not written')
        result = json.loads(report.read_text(encoding='utf-8'))['runs'][0]
        self.assertEqual(result['output'], 'final.pdf')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.run.iterdir()})

    def test_failed_gates_give_a_nonzero_cli_exit(self):
        report = self.base / 'score.json'
        with redirect_stdout(io.StringIO()):
            rc = score.main([str(self.original), str(self.run), '--report', str(report)])
        self.assertEqual(rc, 1)
        self.assertNotEqual(json.loads(report.read_text())['runs'][0]['verify_rc'], 0)

    def test_report_cannot_overwrite_the_delivered_pdf(self):
        before = self.final.read_bytes()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                score.main([str(self.original), str(self.run), '--output', 'final.pdf',
                            '--allow', SCHOOL, '--report', str(self.final)])
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(self.final.read_bytes(), before)

    def test_report_cannot_change_a_run_even_when_selection_fails(self):
        make_pdf(self.run / 'draft.pdf', 'Draft of this form.')
        for invalid_manifest in (False, True):
            if invalid_manifest:
                self.manifest(translations='missing.json')
            for report_name in ('final.pdf', 'delivery.json', 'score.json'):
                with self.subTest(invalid_manifest=invalid_manifest, report=report_name):
                    before = {p.name: p.read_bytes() for p in self.run.iterdir()}
                    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            score.main([str(self.original), str(self.run),
                                        '--report', str(self.run / report_name)])
                    self.assertEqual(raised.exception.code, 2)
                    self.assertEqual(before, {p.name: p.read_bytes() for p in self.run.iterdir()})


if __name__ == '__main__':
    unittest.main()
