"""Reusing a workspace must not reuse a previous rebuild's success evidence."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pdf_translate import run_extract, run_strip
from pdf_translate.pipeline import main
from tests.test_import_surface import _tiny_pdf
from tests.typography_fixtures import latin_font_sets, make_job


ROOT = Path(__file__).resolve().parents[1]


class RebuildAttemptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)

    def job(self, typography=False):
        if typography:
            job = make_job(self.work, prefix_text='Payment ')
            conf = json.loads(job['mapping'].read_text(encoding='utf-8'))
            conf['lang'] = 'es'
            for target in conf['targets']:
                target['runs'][0]['text'], target['runs'][1]['text'] = 'Pague ', 'AHORA'
            job['mapping'].write_text(json.dumps(conf), encoding='utf-8')
        else:
            job = {k: self.work / name for k, name in {
                'original': 'original.pdf', 'stripped': 'stripped.pdf',
                'segments': 'segments.json', 'mapping': 'translations.json',
                'output': 'out.pdf'}.items()}
            _tiny_pdf(job['original'])
            run_strip(str(job['original']), str(job['stripped']))
            run_extract(str(job['original']), str(self.work))
            job['mapping'].write_text(json.dumps({
                'fonts': latin_font_sets()['sans'], 'lang': 'es',
                'translations': {'Hello world.': 'Hola mundo.'}}), encoding='utf-8')
        self.job_paths = job
        self.authored = job['mapping'].read_bytes()
        self.report = self.work / 'verify_report.json'
        self.args = ['rebuild', '--work', str(self.work), str(job['original']),
                     str(job['output']), '--min-ink', '0.1']
        if not typography:
            self.args += ['--translations', str(job['mapping'])]
        return job

    def cli(self, extra=()):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/pipeline.py'), *self.args, *map(str, extra)],
            cwd=self.work, env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONUTF8='1'),
            capture_output=True, encoding='utf-8', timeout=60)
        return result.returncode, result.stdout + result.stderr

    def success(self, extra=(), report=None):
        rc, output = self.cli(extra)
        self.assertEqual(rc, 0, output)
        data = json.loads((report or self.report).read_text(encoding='utf-8'))
        self.assertEqual(data['exit_code'], 0)
        self.assertEqual(data['output'], str(self.job_paths['output']))
        return data

    def test_success_refusal_success_in_both_formats(self):
        for typography in (False, True):
            with self.subTest(typography=typography):
                job = self.job(typography)
                self.success()
                old_pdf = job['output'].read_bytes()
                source = job['original'].read_bytes()
                conf = json.loads(self.authored)
                if typography:
                    conf['targets'][0]['runs'][0]['text'] = 'Payment ' * 100
                else:
                    conf['translations'] = {}
                job['mapping'].write_text(json.dumps(conf), encoding='utf-8')
                rc, output = self.cli()
                self.assertNotEqual(rc, 0, output)
                self.assertFalse(self.report.exists(), 'previous success report survived refusal')
                self.assertEqual(job['output'].read_bytes(), old_pdf)
                self.assertEqual(job['original'].read_bytes(), source)
                job['mapping'].write_bytes(self.authored)
                self.success()

    def test_mapping_load_errors_invalidate_before_rendering(self):
        job = self.job()
        for content in (b'{', b'{"format":"future"}', None):
            with self.subTest(content=content):
                job['mapping'].write_bytes(self.authored)
                self.success()
                old_pdf = job['output'].read_bytes()
                if content is None:
                    job['mapping'].unlink()
                else:
                    job['mapping'].write_bytes(content)
                rc, output = self.cli()
                self.assertNotEqual(rc, 0, output)
                self.assertFalse(self.report.exists())
                self.assertEqual(job['output'].read_bytes(), old_pdf)

    def test_custom_report_also_invalidates_default_when_switching(self):
        job = self.job()
        self.success()
        custom = self.work / 'custom.json'
        self.success(['--report', 'custom.json'], custom)
        self.assertFalse(self.report.exists())
        old_pdf = job['output'].read_bytes()
        job['mapping'].write_text('{', encoding='utf-8')
        rc, output = self.cli(['--report', 'custom.json'])
        self.assertNotEqual(rc, 0, output)
        self.assertFalse(custom.exists())
        self.assertEqual(job['output'].read_bytes(), old_pdf)

    def test_current_verification_failure_replaces_previous_success(self):
        self.job()
        self.success()
        self.args[self.args.index('--min-ink') + 1] = '10'
        rc, output = self.cli()
        self.assertEqual(rc, 1, output)
        self.assertEqual(json.loads(self.report.read_text(encoding='utf-8'))['exit_code'], 1)

    def test_interruption_or_unexpected_stage_error_cannot_leave_old_pass(self):
        job = self.job()
        for stage in ('load_mapping', 'retypeset', 'verify_main'):
            for failure in (KeyboardInterrupt, RuntimeError):
                with self.subTest(stage=stage, failure=failure):
                    self.success()
                    source = job['original'].read_bytes()
                    # Inject at the stage boundary; the preceding successful run is real.
                    with patch('pdf_translate.pipeline.' + stage, side_effect=failure), redirect_stdout(io.StringIO()):
                        with self.assertRaises(failure):
                            main(self.args)
                    self.assertFalse(self.report.exists())
                    self.assertEqual(job['original'].read_bytes(), source)

    def test_report_aliases_and_unrelated_files_are_never_removed(self):
        job = self.job()
        self.success()
        font = self.work / 'input-font.ttf'
        font.write_bytes(Path(latin_font_sets()['sans']['regular']).read_bytes())
        unrelated = self.work / 'notes.json'
        unrelated.write_text('{"notes": "keep me"}', encoding='utf-8')
        linked = self.work / 'linked-source.json'
        os.link(job['original'], linked)
        for path in [*job.values(), font, unrelated, linked]:
            with self.subTest(path=path.name):
                before = {p: p.read_bytes() for p in self.work.iterdir() if p.is_file()}
                try:
                    rc, output = self.cli(['--report', path])
                    self.assertEqual(rc, 2, output)
                    self.assertEqual({p: p.read_bytes() for p in before}, before)
                finally:
                    for p, data in before.items():
                        p.write_bytes(data)

    def test_default_report_alias_is_rejected_before_source_mutation(self):
        job = self.job()
        os.link(job['original'], self.report)
        source = job['original'].read_bytes()
        rc, output = self.cli()
        self.assertEqual(rc, 2, output)
        self.assertEqual(job['original'].read_bytes(), source)
        self.assertEqual(self.report.read_bytes(), source)
        self.assertFalse(job['output'].exists())

    def test_invalidation_failure_aborts_before_typesetting(self):
        self.job()
        self.success()
        with patch('pdf_translate.verify.os.remove', side_effect=PermissionError('locked')), \
                patch('pdf_translate.pipeline.retypeset') as render, redirect_stdout(io.StringIO()) as output:
            rc = main(self.args)
        self.assertEqual(rc, 2, output.getvalue())
        render.assert_not_called()
        self.assertIn('does not describe this run', output.getvalue())


class DefaultMappingVerificationTests(unittest.TestCase):
    """A06: a default legacy rebuild verifies against the mapping it built from.

    Before the fix, rebuild forwarded only the caller's verify flags, so a
    legacy job with an empty target, or an override that dropped the source's
    list marker, exited 0 with a PASS report and no mapping-dependent gate.
    """

    LABELS = ('Hello world', 'Another label')
    COMPLETE = {'Hello world': 'Hola mundo', 'Another label': 'Otra etiqueta'}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def job(self, translations, overrides=(), lines=LABELS, name='job'):
        import pymupdf
        work = self.root / name
        work.mkdir()
        doc = pymupdf.open()
        try:
            page = doc.new_page()
            for k, text in enumerate(lines):
                page.insert_text((72, 100 + 30 * k), text, fontsize=12)
            doc.save(str(work / 'original.pdf'))
        finally:
            doc.close()
        run_extract(str(work / 'original.pdf'), str(work))
        run_strip(str(work / 'original.pdf'), str(work / 'stripped.pdf'))
        (work / 'translations.json').write_text(json.dumps({
            'fonts': latin_font_sets()['sans'], 'lang': 'es', 'translations': translations,
            'overrides': list(overrides)}, ensure_ascii=False), encoding='utf-8')
        return work

    def rebuild(self, work, *extra):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/pipeline.py'), 'rebuild', '--work', str(work),
             str(work / 'original.pdf'), str(work / 'out.pdf'), '--min-ink', '0.1', *map(str, extra)],
            cwd=work, env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONUTF8='1'),
            capture_output=True, encoding='utf-8', timeout=120)
        report = work / 'verify_report.json'
        gates = ({g['name']: g['status'] for g in json.loads(report.read_text(encoding='utf-8'))['gates']}
                 if report.exists() else None)
        return result.returncode, gates, result.stdout + result.stderr

    def test_a_complete_mapping_passes_with_the_mapping_checks_run(self):
        rc, gates, out = self.rebuild(self.job(self.COMPLETE))
        self.assertEqual(rc, 0, out)
        self.assertEqual((gates.get('empty-targets'), gates.get('placement')), ('PASS', 'PASS'), gates)

    def test_an_empty_target_fails_the_default_rebuild(self):
        rc, gates, out = self.rebuild(self.job({'Hello world': 'Hola mundo', 'Another label': ''}))
        self.assertEqual(rc, 1, out)
        self.assertEqual(gates.get('empty-targets'), 'FAIL', gates)

    def test_a_whitespace_target_fails_the_default_rebuild(self):
        rc, gates, out = self.rebuild(self.job({'Hello world': 'Hola mundo', 'Another label': '   '}))
        self.assertEqual(rc, 1, out)
        self.assertEqual(gates.get('empty-targets'), 'FAIL', gates)

    def test_an_override_that_drops_the_marker_fails_the_default_rebuild(self):
        work = self.job({'a. Hello world': 'a. Hola mundo', 'Another label': 'Otra etiqueta'},
                        overrides=[{'page': 0, 'contains': 'a. Hello world',
                                    'parts': [{'text': 'Hola mundo'}]}],
                        lines=('a. Hello world', 'Another label'))
        rc, gates, out = self.rebuild(work)
        self.assertEqual(rc, 1, out)
        self.assertEqual(gates.get('override-markers'), 'FAIL', gates)

    def test_the_equals_spelling_does_not_switch_the_checks_off(self):
        work = self.job({'Hello world': 'Hola mundo', 'Another label': ''})
        rc, gates, out = self.rebuild(work, f'--translations={work / "translations.json"}')
        self.assertEqual(rc, 1, out)
        self.assertEqual(gates.get('empty-targets'), 'FAIL', gates)

    def test_segments_alone_still_gets_the_default_mapping(self):
        work = self.job({'Hello world': 'Hola mundo', 'Another label': ''})
        rc, gates, out = self.rebuild(work, '--segments', work / 'segments.json')
        self.assertEqual(rc, 1, out)
        self.assertEqual(gates.get('empty-targets'), 'FAIL', gates)

    def test_an_explicit_mapping_elsewhere_is_honoured(self):
        """The build's mapping is complete; the caller's own has an empty
        target. Verification follows the caller, so it fails."""
        work = self.job(self.COMPLETE)
        other = self.root / 'other'
        other.mkdir()
        conf = json.loads((work / 'translations.json').read_text(encoding='utf-8'))
        conf['translations']['Another label'] = ''
        (other / 'translations.json').write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')
        (other / 'segments.json').write_bytes((work / 'segments.json').read_bytes())
        rc, gates, out = self.rebuild(work, '--translations', other / 'translations.json')
        self.assertEqual(rc, 1, out)
        self.assertEqual(gates.get('empty-targets'), 'FAIL', gates)

    def test_a_null_target_still_refuses_the_build(self):
        rc, gates, out = self.rebuild(self.job({'Hello world': 'Hola mundo', 'Another label': None}))
        self.assertEqual(rc, 1, out)
        self.assertIsNone(gates, 'a refused build writes no verification report')


if __name__ == '__main__':
    unittest.main()
