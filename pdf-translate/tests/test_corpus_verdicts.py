#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drive shipped extract/verify against every corpus PDF and its recorded verdict."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
CORPUS = Path(__file__).resolve().parents[1] / 'corpus'
import sys
sys.path.insert(0, str(SCRIPTS))

import extract_segments  # noqa: E402
import strip_text  # noqa: E402
import verify  # noqa: E402

ALLOWED = {'translate', 'refuse+OCR', 'skip-ink'}


def load_verdicts():
    path = CORPUS / 'verdicts.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    return {k: v for k, v in data.items()}


class CorpusVerdictTests(unittest.TestCase):
    def test_every_corpus_pdf_has_a_legal_verdict(self):
        verdicts = load_verdicts()
        pdfs = sorted(p.name for p in CORPUS.glob('*.pdf'))
        self.assertTrue(pdfs, 'corpus has no PDFs')
        self.assertEqual(set(pdfs), set(verdicts),
                         msg='verdicts.json must list every corpus PDF and only those')
        for name, v in verdicts.items():
            self.assertIn(v, ALLOWED, msg=f'{name} verdict {v!r}')
        readme = (CORPUS / 'README.md').read_text(encoding='utf-8')
        for name, v in verdicts.items():
            self.assertIn(f'`{name}`', readme)
            self.assertIn(f'`{v}`', readme)

    def test_shipped_extract_verify_match_recorded_verdicts(self):
        verdicts = load_verdicts()
        for name, expected in sorted(verdicts.items()):
            pdf = CORPUS / name
            with self.subTest(name=name, verdict=expected):
                with tempfile.TemporaryDirectory() as tmp:
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        extract_rc = extract_segments.main([str(pdf), '--outdir', tmp])
                    extract_log = buf.getvalue()
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        verify_rc = verify.verify(str(pdf), str(pdf))
                    verify_log = buf.getvalue()

                    if expected == 'refuse+OCR':
                        self.assertNotEqual(extract_rc, 0, msg=extract_log)
                        self.assertIn('OCR', extract_log)
                        self.assertNotEqual(verify_rc, 0, msg=verify_log)
                        self.assertTrue(
                            'OCR' in verify_log or 'scanned' in verify_log.lower(),
                            msg=verify_log)
                    elif expected == 'skip-ink':
                        self.assertNotIn('FAIL page 1 ink ratio', verify_log)
                        self.assertIn('SKIP page 1 ink ratio', verify_log)
                        self.assertEqual(verify_rc, 0, msg=verify_log)
                    elif expected == 'translate':
                        self.assertEqual(extract_rc, 0, msg=extract_log)
                        segs = json.loads(
                            Path(tmp, 'segments.json').read_text(encoding='utf-8'))
                        self.assertGreater(len(segs['segments']), 0, msg=name)
                        stripped = str(Path(tmp, 'stripped.pdf'))
                        buf = io.StringIO()
                        with redirect_stdout(buf):
                            report = strip_text.strip_text(str(pdf), stripped)
                        leftover = report.get('leftover_text')
                        self.assertIsNotNone(leftover, msg='strip has no completeness gate')
                        self.assertEqual(leftover, [], msg=f'{name}: {leftover}')
                        self.assertTrue(Path(stripped).is_file(), msg=name)


if __name__ == '__main__':
    unittest.main()
