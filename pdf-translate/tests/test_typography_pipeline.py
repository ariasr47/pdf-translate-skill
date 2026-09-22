"""Real commands must carry exact context and refuse lossy helper paths."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import pymupdf

from pdf_translate import run_retypeset
from pdf_translate.mapping import load_mapping
from pdf_translate.results import MappingError
from tests.typography_fixtures import latin_font_sets, make_job, make_mapping


ROOT = Path(__file__).resolve().parents[1]


class TypographyPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.job = make_job(self.work, prefix_text='Payment ')

    def cli(self, script, *args):
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONUTF8='1')
        return subprocess.run([sys.executable, str(ROOT / 'scripts' / (script + '.py')),
                               *(str(a) for a in args)], cwd=self.work, env=env,
                              encoding='utf-8', capture_output=True, timeout=90)

    def pipeline(self, *args):
        return self.cli('pipeline', *args)

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.work.iterdir() if p.is_file()}

    def successful_rebuild(self):
        conf = json.loads(self.job['mapping'].read_text(encoding='utf-8'))
        conf['lang'] = 'es'
        for target in conf['targets']:
            target['runs'][0]['text'], target['runs'][1]['text'] = 'Pague ', 'AHORA'
        self.job['mapping'].write_text(json.dumps(conf), encoding='utf-8')
        self.assert_ok(self.pipeline('rebuild', self.job['original'], self.job['output'], '--work', self.work))
        report = json.loads((self.work / 'verify_report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['exit_code'], 0)

    def test_init_scaffold_author_rebuild_review_and_final_verify(self):
        self.assert_ok(self.pipeline('init', self.job['original'], '--work', self.work, '--typography'))
        self.assert_ok(self.pipeline('from-cores', '--work', self.work, '--force'))
        template = json.loads(self.job['mapping'].read_text(encoding='utf-8'))
        self.assertEqual(template['format'], 'typography-1')
        self.assertEqual(template['lang'], '')
        self.assertEqual(template['font_sets'], {})
        self.assertEqual([t['occurrence_id'] for t in template['targets']], ['s0', 's1'])
        self.assertTrue(all(t['runs'] == [] for t in template['targets']))
        self.assertNotIn('translations', template)
        rejected = self.pipeline('rebuild', self.job['original'], self.job['output'], '--work', self.work)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(self.job['output'].exists())
        extraction = json.loads(self.job['segments'].read_text(encoding='utf-8'))
        authored = make_mapping(extraction, latin_font_sets())
        authored['lang'] = 'es'
        for target in authored['targets']:
            target['runs'][0]['text'], target['runs'][1]['text'] = 'Pague ', 'AHORA'
        self.job['mapping'].write_text(json.dumps(authored), encoding='utf-8')
        self.assert_ok(self.pipeline('rebuild', self.job['original'], self.job['output'], '--work', self.work,
                                    '--fill-text', 'Valor 123', '--source-words-from', self.job['segments']))
        report = json.loads((self.work / 'verify_report.json').read_text(encoding='utf-8'))
        self.assertTrue(any(g['name'] == 'typography' and g['status'] == 'PASS' for g in report['gates']))
        review = self.pipeline('review', '--work', self.work)
        self.assert_ok(review)
        self.assertIn('2 occurrences', review.stdout)
        final = self.work / 'final.pdf'
        self.assert_ok(self.cli('field_fonts', self.job['output'], latin_font_sets()['sans']['regular'], final))
        self.assert_ok(self.cli('verify', self.job['original'], final, '--translations', self.job['mapping'],
                                '--segments', self.job['segments'], '--fill-text', 'Valor 123',
                                '--source-words-from', self.job['segments']))

    def test_from_cores_no_overwrite_and_stale_reference(self):
        before = self.snapshot()
        self.assertEqual(self.pipeline('from-cores', '--work', self.work).returncode, 2)
        self.assertEqual(self.snapshot(), before)
        path = self.work / 'to_translate.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(data['extraction_id'], load_mapping(self.job['mapping']).extraction_id)
        data['extraction_id'] = '0' * 64
        path.write_text(json.dumps(data), encoding='utf-8')
        before = self.snapshot()
        self.assertNotEqual(self.pipeline('from-cores', '--work', self.work, '--force').returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_removed_reference_cannot_flatten_typography_extraction(self):
        path = self.work / 'to_translate.json'
        path.write_text('{"cores": [{"text":"Pay NOW"}]}', encoding='utf-8')
        before = self.snapshot()
        self.assertNotEqual(self.pipeline('from-cores', '--work', self.work, '--force').returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_merge_helpers_refuse_new_and_mixed_formats_without_writes(self):
        legacy = self.work / 'legacy.json'
        legacy.write_text('{"translations": {"Hello":"Hola"}}', encoding='utf-8')
        combined = self.work / 'combined.json'
        combined.write_text('prior output', encoding='utf-8')
        before = self.snapshot()
        for args in [('propose-merges', '--work', self.work),
                     ('propose-merges', '--work', self.work, '--accept'),
                     ('merge-mappings', combined, self.job['mapping'], legacy),
                     ('merge-mappings', combined, legacy, self.job['mapping'], '--last-wins')]:
            self.assertNotEqual(self.pipeline(*args).returncode, 0, args)
            self.assertEqual(self.snapshot(), before)

    def test_unknown_and_duplicate_formats_have_named_cli_refusals(self):
        original = self.job['mapping'].read_text(encoding='utf-8')
        for text in (original.replace('typography-1', 'typography-future'),
                     '{"format":"typography-1",' + original[1:]):
            self.job['mapping'].write_text(text, encoding='utf-8')
            with self.assertRaises(MappingError) as caught:
                run_retypeset(*(str(self.job[k]) for k in ('stripped','segments','mapping','output')),
                               original=str(self.job['original']))
            for script, args in [('retypeset', [self.job[k] for k in ('stripped','segments','mapping','output')] +
                                               ['--original', self.job['original']]),
                                 ('qa_check', [self.job['mapping']]),
                                 ('verify', [self.job['original'], self.job['stripped'], '--translations', self.job['mapping']]),
                                 ('prepare_font', [latin_font_sets()['sans']['regular'], self.job['mapping'], self.work / 'sub.ttf'])]:
                result = self.cli(script, *args)
                self.assertEqual(result.returncode, caught.exception.exit_code, result.stdout + result.stderr)
                self.assertIn('format', result.stdout)
                self.assertNotIn('Traceback', result.stderr)
            self.assertFalse(self.job['output'].exists())
            self.assertFalse((self.work / 'sub.ttf').exists())

    def test_missing_original_refuses_with_same_library_reason(self):
        args = [str(self.job[k]) for k in ('stripped','segments','mapping','output')]
        with self.assertRaises(MappingError) as caught:
            run_retypeset(*args)
        result = self.cli('retypeset', *args)
        self.assertEqual(result.returncode, caught.exception.exit_code)
        self.assertIn('original', result.stdout.lower())
        self.assertFalse(self.job['output'].exists())

    def test_missing_values_are_usage_errors_before_work(self):
        cases = [('pipeline', ['init', self.job['original'], '--work']),
                 ('pipeline', ['rebuild', self.job['original'], self.job['output'], '--work', self.work, '--fill-text']),
                 ('extract_segments', [self.job['original'], '--typography', '--outdir']),
                 ('retypeset', [self.job[k] for k in ('stripped','segments','mapping','output')] + ['--original']),
                 ('verify', [self.job['original'], self.job['stripped'], '--translations']),
                 ('prepare_font', [latin_font_sets()['sans']['regular'], self.job['mapping'], self.work / 'sub.ttf', '--font-class']),
                 ('prepare_font', [latin_font_sets()['sans']['regular'], self.job['mapping'], self.work / 'sub.ttf', '--font-role'])]
        for script, args in cases:
            before = self.snapshot()
            result = self.cli(script, *args)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn(args[-1], result.stdout)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(self.snapshot(), before)

    def test_conflicting_bound_context_or_report_alias_preserves_previous_files(self):
        for flag, value in [('--translations', self.work / 'other.json'), ('--segments', self.job['segments']),
                            ('--report', self.job['original']), ('--report', self.job['output'])]:
            self.successful_rebuild()
            before = self.snapshot()
            result = self.pipeline('rebuild', self.job['original'], self.job['output'], '--work', self.work, flag, value)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            if flag != '--report':
                self.assertIn('conflicting forwarded flags', result.stdout)
                before.pop('verify_report.json')
            else:
                self.assertIn('must not overwrite', result.stdout)
            self.assertEqual(self.snapshot(), before)

    def test_unknown_format_merge_proposal_cannot_write_first(self):
        self.job['mapping'].write_text('{"format":"future"}', encoding='utf-8')
        before = self.snapshot()
        result = self.pipeline('propose-merges', '--work', self.work, '--accept')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_required_metadata_is_unauthored_and_stale_rebuild_preserves_files(self):
        self.successful_rebuild()
        with pymupdf.open(self.job['original']) as doc:
            doc.set_metadata({'title': 'Payment'})
            data = doc.tobytes()
        self.job['original'].write_bytes(data)
        self.assert_ok(self.pipeline('init', self.job['original'], '--work', self.work, '--typography'))
        self.assert_ok(self.pipeline('from-cores', '--work', self.work, '--force'))
        conf = json.loads(self.job['mapping'].read_text(encoding='utf-8'))
        self.assertEqual(conf['document_targets'], {'Payment': None})
        extraction = json.loads(self.job['segments'].read_text(encoding='utf-8'))
        conf = make_mapping(extraction, latin_font_sets())
        conf['extraction_id'] = '0' * 64
        self.job['mapping'].write_text(json.dumps(conf), encoding='utf-8')
        before = self.snapshot()
        result = self.pipeline('rebuild', self.job['original'], self.job['output'], '--work', self.work)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('extraction', result.stdout)
        before.pop('verify_report.json')
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
