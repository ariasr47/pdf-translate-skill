"""The CLI must not drop supplied inputs or hide its result under python -m."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf

from tests.test_consumer_contract import build_source, write_mapping, TARGETS
from tests.test_import_surface import _job, _tiny_pdf

SKILL = Path(__file__).resolve().parents[1]


def _cli(name, *args, module=False, env=None):
    entry = ['-m', f'pdf_translate.{name}'] if module else [
        str(SKILL / 'scripts' / f'{name}.py')]
    return subprocess.run(
        [sys.executable, *entry, *map(str, args)], cwd=SKILL,
        env={**os.environ, 'PYTHONUTF8': '1', **(env or {})}, capture_output=True,
        text=True, encoding='utf-8', timeout=30)


class VerifyOptionSyntaxTests(unittest.TestCase):
    def test_equals_options_refuse_before_verifying_or_touching_files(self):
        # Ignoring any of these options silently changes the requested run.
        options = (
            '--allow', '--report', '--fill-text', '--min-ink',
            '--source-regex', '--source-words-from', '--allow-extra-prefix',
            '--translations', '--segments', '--reference-fonts', '--widget-text',
        )
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            source = work / 'original.pdf'
            _tiny_pdf(source)
            report = work / 'report.json'
            report.write_text('prior report', encoding='utf-8')
            before = {p.name: p.read_bytes() for p in work.iterdir()}
            for option in options:
                with self.subTest(option=option):
                    result = _cli('verify', source, source,
                                  f'{option}=ignored', '--report', report)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn('usage:', result.stdout)
                    self.assertIn(option, result.stdout)
                    self.assertIn(f'{option} VALUE', result.stdout)
                    self.assertNotIn('PASS ', result.stdout)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(
                        {p.name: p.read_bytes() for p in work.iterdir()}, before)

    def test_empty_equals_input_is_also_a_usage_error(self):
        result = _cli('verify', 'absent.pdf', 'also-absent.pdf', '--translations=')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('--translations VALUE', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_equals_mapping_cannot_silently_skip_a_missing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output, mapping = _job(tmp)
            Path(mapping).write_text(json.dumps({
                'translations': {'Hello world.': 'Missing authored target'},
            }), encoding='utf-8')
            separated = _cli('verify', source, output, '--translations', mapping)
            self.assertEqual(separated.returncode, 1, separated.stdout + separated.stderr)
            self.assertIn('FAIL missing translation targets (1)', separated.stdout)
            self.assertIn('Missing authored target', separated.stdout)
            result = _cli('verify', source, output, f'--translations={mapping}')
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('--translations VALUE', result.stdout)

    def test_separate_value_can_contain_an_equals_sign(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output, mapping = _job(tmp)
            named = Path(tmp) / 'mapping=authored.json'
            Path(mapping).rename(named)
            named.write_text(json.dumps({
                'translations': {'Hello world.': 'Missing authored target'},
            }), encoding='utf-8')
            result = _cli('verify', source, output, '--translations', named)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('FAIL missing translation targets (1)', result.stdout)
            self.assertIn('Missing authored target', result.stdout)
            self.assertNotIn('usage:', result.stdout)


class ModuleConsoleTests(unittest.TestCase):
    def assert_same_console(self, script, module):
        self.assertEqual(module.returncode, script.returncode, module.stderr)
        scrub = lambda text: re.sub(r'elapsed \d+\.\d+s', 'elapsed <T>s', text)
        self.assertEqual(scrub(module.stdout), scrub(script.stdout))
        self.assertNotIn('Traceback', module.stderr)

    def test_verify_module_prints_success_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'original.pdf'
            _tiny_pdf(source)
            script = _cli('verify', source, source)
            self.assertEqual(script.returncode, 0, script.stdout + script.stderr)
            self.assertIn('PASS ', script.stdout)
            module = _cli('verify', source, source, module=True)
            self.assert_same_console(script, module)
            self.assertEqual(module.stdout.count('elapsed '), 1)

    def test_verify_module_prints_failed_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output, mapping = _job(tmp, target='')
            args = [source, output, '--translations', mapping]
            script = _cli('verify', *args)
            self.assertEqual(script.returncode, 1, script.stdout + script.stderr)
            self.assertIn('FAIL', script.stdout)
            self.assert_same_console(script, _cli('verify', *args, module=True))

    def test_verify_module_prints_usage_error(self):
        args = ['absent.pdf', 'also-absent.pdf', '--translations']
        script = _cli('verify', *args)
        self.assertEqual(script.returncode, 2, script.stdout + script.stderr)
        self.assert_same_console(script, _cli('verify', *args, module=True))

    def test_verify_module_prints_equals_option_refusal(self):
        args = ['absent.pdf', 'also-absent.pdf', '--translations=ignored.json']
        result = _cli('verify', *args, module=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('--translations VALUE', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_verify_module_keeps_unicode_findings_on_a_legacy_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output, mapping = _job(tmp)
            Path(mapping).write_text(json.dumps({
                'translations': {'Hello world.': '日本語'},
            }), encoding='utf-8')
            args = [source, output, '--translations', mapping]
            env = {'PYTHONUTF8': '0', 'PYTHONIOENCODING': 'cp1252'}
            script = _cli('verify', *args, env=env)
            self.assertEqual(script.returncode, 1, script.stdout + script.stderr)
            self.assertIn('日本語', script.stdout)
            module = _cli('verify', *args, module=True, env=env)
            self.assert_same_console(script, module)
            self.assertNotIn('UnicodeEncodeError', module.stderr)

    def retypeset_job(self, work):
        from pdf_translate import run_extract, run_strip
        source = build_source(work / 'original.pdf')
        run_extract(source, outdir=str(work))
        stripped = work / 'stripped.pdf'
        run_strip(source, str(stripped))
        mapping = write_mapping(str(work))
        return [stripped, work / 'segments.json', mapping, work / 'out.pdf']

    def test_retypeset_module_prints_success_and_builds_translation(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.retypeset_job(Path(tmp))
            script = _cli('retypeset', *args)
            self.assertEqual(script.returncode, 0, script.stdout + script.stderr)
            self.assertIn('saved ', script.stdout)
            module = _cli('retypeset', *args, module=True)
            self.assert_same_console(script, module)
            self.assertEqual(module.stdout.count('elapsed '), 1)
            with pymupdf.open(args[-1]) as doc:
                text = ''.join(page.get_text() for page in doc)
            for target in TARGETS.values():
                self.assertIn(target, text)

    def test_retypeset_module_prints_refusal_and_writes_no_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.retypeset_job(Path(tmp))
            write_mapping(tmp, translations={})
            script = _cli('retypeset', *args)
            self.assertEqual(script.returncode, 1, script.stdout + script.stderr)
            self.assertIn('untranslated', script.stdout.lower())
            self.assert_same_console(script, _cli('retypeset', *args, module=True))
            self.assertFalse(args[-1].exists())

    def test_retypeset_module_keeps_unicode_paths_on_a_legacy_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.retypeset_job(Path(tmp))
            args[-1] = Path(tmp) / '日本語.pdf'
            env = {'PYTHONUTF8': '0', 'PYTHONIOENCODING': 'cp1252'}
            script = _cli('retypeset', *args, env=env)
            self.assertEqual(script.returncode, 0, script.stdout + script.stderr)
            self.assertIn('日本語.pdf', script.stdout)
            module = _cli('retypeset', *args, module=True, env=env)
            self.assert_same_console(script, module)
            self.assertNotIn('UnicodeEncodeError', module.stderr)


if __name__ == '__main__':
    unittest.main()
