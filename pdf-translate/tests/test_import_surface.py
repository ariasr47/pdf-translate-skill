#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The scripts are a library: importable stages, structured gate verdicts.

Existing tests import the modules by inserting ``scripts/`` on ``sys.path``
and drive ``main()`` / the stage functions. This file is the consumer-facing
surface: ``import pdf_translate`` must work without that path hack, must not
run a CLI as an import side effect, and verify / QA must return verdict
objects rather than only printing and exiting.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pymupdf

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / 'scripts'
CLI_SCRIPTS = (
    'bilingual.py',
    'compare.py',
    'extract_segments.py',
    'field_fonts.py',
    'pipeline.py',
    'prepare_font.py',
    'qa_check.py',
    'render_pages.py',
    'retypeset.py',
    'strip_text.py',
    'verify.py',
)
# No-args prints __doc__ and returns 2. The rest IndexError on argv[0].
USAGE_CLIS = ('pipeline.py', 'qa_check.py', 'bilingual.py')
# A Windows console on cp1252: CJK in qa_check's help is the tell.
LEGACY_ENV = {
    'PYTHONUTF8': '0',
    'PYTHONIOENCODING': 'cp1252',
}


def _tiny_pdf(path, text='Hello world.'):
    doc = pymupdf.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), text)
        doc.save(path)
    finally:
        doc.close()


class PackageImportTests(unittest.TestCase):
    def test_import_has_no_cli_side_effects(self):
        buf, err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            import pdf_translate
        self.assertEqual(buf.getvalue(), '')
        self.assertEqual(err.getvalue(), '')
        self.assertTrue(callable(pdf_translate.strip_text))
        self.assertTrue(callable(pdf_translate.extract_segments))
        self.assertTrue(callable(pdf_translate.retypeset))
        self.assertTrue(callable(pdf_translate.prepare_font))
        self.assertTrue(callable(pdf_translate.field_fonts))
        self.assertTrue(callable(pdf_translate.render_pages))
        self.assertTrue(callable(pdf_translate.compare))
        self.assertTrue(callable(pdf_translate.interleave))
        self.assertTrue(callable(pdf_translate.verify))
        self.assertTrue(callable(pdf_translate.qa_check))
        self.assertTrue(callable(pdf_translate.run_verify))
        self.assertTrue(callable(pdf_translate.run_qa))

    def test_submodules_are_importable_without_scripts_on_path(self):
        # The historical path hack must not be required for a consumer.
        cleaned = [p for p in sys.path if Path(p).resolve() != SCRIPTS.resolve()]
        self.assertNotIn(str(SCRIPTS), cleaned)
        from pdf_translate.strip_text import strip_text
        from pdf_translate.extract_segments import extract_segments
        from pdf_translate.retypeset import retypeset
        from pdf_translate.prepare_font import prepare_font
        from pdf_translate.field_fonts import field_fonts
        from pdf_translate.verify import verify, run_verify
        from pdf_translate.qa_check import qa_check, run_qa
        for fn in (strip_text, extract_segments, retypeset, prepare_font,
                   field_fonts, verify, run_verify, qa_check, run_qa):
            self.assertTrue(callable(fn))


class VerifyVerdictTests(unittest.TestCase):
    def test_run_verify_returns_a_verdict_and_does_not_print(self):
        from pdf_translate.verify import VerifyVerdict, run_verify, verify

        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            _tiny_pdf(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                verdict = run_verify(src, src)
            self.assertEqual(buf.getvalue(), '',
                             msg='run_verify must not print; the CLI wrapper does')
            self.assertIsInstance(verdict, VerifyVerdict)
            self.assertEqual(verdict.exit_code, 0)
            self.assertTrue(verdict.ok)
            self.assertTrue(verdict.gates)
            names = {g.name for g in verdict.gates}
            self.assertIn('field-parity', names)
            statuses = {g.status for g in verdict.gates}
            self.assertTrue(statuses <= {'PASS', 'FAIL', 'SKIP', 'REVIEW'})

            printed = io.StringIO()
            with redirect_stdout(printed):
                rc = verify(src, src)
            self.assertEqual(rc, 0)
            self.assertEqual(rc, verdict.exit_code)
            self.assertIn('PASS field parity', printed.getvalue())

    def test_run_verify_fail_is_exit_code_1_not_sys_exit(self):
        from pdf_translate.verify import run_verify

        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            other = os.path.join(tmp, 'other.pdf')
            doc = pymupdf.open()
            try:
                page = doc.new_page()
                page.insert_text((72, 72), 'Alpha source sentence here.')
                widget = pymupdf.Widget()
                widget.field_name = 'ApplicantName'
                widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
                widget.rect = pymupdf.Rect(72, 100, 280, 118)
                page.add_widget(widget)
                doc.save(src)
            finally:
                doc.close()
            _tiny_pdf(other, 'Alpha source sentence here.')
            verdict = run_verify(src, other)
            self.assertEqual(verdict.exit_code, 1)
            self.assertFalse(verdict.ok)
            self.assertTrue(any(g.status == 'FAIL' for g in verdict.gates))


class QAVerdictTests(unittest.TestCase):
    def test_run_qa_returns_a_verdict_and_does_not_print(self):
        from pdf_translate.qa_check import QAVerdict, qa_check, run_qa

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'translations.json')
            Path(path).write_text(json.dumps({
                'translations': {
                    'Pay $1,250.00 now': 'Pague ahora.',
                    'City': 'Ciudad',
                },
                'skip': [],
            }), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                verdict = run_qa(path)
            self.assertEqual(buf.getvalue(), '')
            self.assertIsInstance(verdict, QAVerdict)
            self.assertEqual(verdict.findings, qa_check(path))
            self.assertGreater(verdict.error_count, 0)
            self.assertEqual(verdict.exit_code, 1)
            self.assertFalse(verdict.ok)
            kinds = {f['kind'] for f in verdict.findings}
            self.assertIn('numbers', kinds)

    def test_run_qa_clean_mapping_is_ok(self):
        from pdf_translate.qa_check import run_qa

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'translations.json')
            Path(path).write_text(json.dumps({
                'translations': {'City': 'Ciudad'},
                'skip': [],
            }), encoding='utf-8')
            verdict = run_qa(path)
            self.assertEqual(verdict.findings, [])
            self.assertEqual(verdict.exit_code, 0)
            self.assertTrue(verdict.ok)


def _run_cli(name, extra_env=None):
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name)],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        env=env)


class CliPathTests(unittest.TestCase):
    def test_documented_cli_scripts_still_exist(self):
        for name in CLI_SCRIPTS:
            self.assertTrue((SCRIPTS / name).is_file(), msg=name)

    def test_pipeline_no_args_still_prints_usage_and_exits_2(self):
        r = _run_cli('pipeline.py')
        self.assertEqual(r.returncode, 2)
        self.assertIn('rebuild', r.stdout)
        self.assertIn('from-cores', r.stdout)

    def test_qa_check_no_args_still_prints_usage_and_exits_2(self):
        r = _run_cli('qa_check.py')
        self.assertEqual(r.returncode, 2)
        self.assertIn('qa_check.py', r.stdout)

    def test_usage_clis_print_help_on_a_legacy_windows_console(self):
        """Help text must not die with UnicodeEncodeError on cp1252.

        qa_check's docstring contains CJK. pipeline's is ASCII. bilingual's
        has an em dash, which cp1252 can encode. All three must still exit 2.
        """
        for name in USAGE_CLIS:
            with self.subTest(name=name):
                r = _run_cli(name, LEGACY_ENV)
                combined = r.stdout + r.stderr
                self.assertNotIn('UnicodeEncodeError', combined, msg=combined)
                self.assertEqual(r.returncode, 2, msg=combined)
                self.assertTrue(r.stdout.strip(), msg=combined)

    def test_qa_check_help_keeps_cjk_on_a_legacy_windows_console(self):
        r = _run_cli('qa_check.py', LEGACY_ENV)
        self.assertEqual(r.returncode, 2, msg=r.stdout + r.stderr)
        self.assertIn('養子支援', r.stdout)

    def test_missing_args_clis_do_not_die_on_encoding_under_cp1252(self):
        crash = [n for n in CLI_SCRIPTS if n not in USAGE_CLIS]
        for name in crash:
            with self.subTest(name=name):
                r = _run_cli(name, LEGACY_ENV)
                combined = r.stdout + r.stderr
                self.assertNotIn('UnicodeEncodeError', combined, msg=combined)
                self.assertEqual(r.returncode, 1, msg=combined)
                self.assertIn('Traceback', combined)

    def test_importing_the_package_does_not_reconfigure_stdio(self):
        code = (
            'import sys\n'
            'print(sys.stdout.encoding)\n'
            'print(sys.stderr.encoding)\n'
            'import pdf_translate\n'
            'print(sys.stdout.encoding)\n'
            'print(sys.stderr.encoding)\n'
        )
        env = dict(os.environ)
        env.update(LEGACY_ENV)
        r = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            env=env, cwd=str(SKILL))
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 4, msg=r.stdout)
        self.assertEqual(lines[0], lines[2])
        self.assertEqual(lines[1], lines[3])
        self.assertEqual(lines[0].lower().replace('-', ''), 'cp1252')


if __name__ == '__main__':
    unittest.main()
