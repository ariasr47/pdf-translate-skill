#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every outcome verify prints reaches a consumer as data: GateResult.findings,
VerifyVerdict.to_dict(), --report and --fail-on-review. Spec:
docs/BRIEF-unattended-delivery.md, task A and B."""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf

from tests.test_import_surface import _gates, _job, _tiny_pdf

SKILL = Path(__file__).resolve().parents[1]
FONTS = SKILL / 'tests' / 'fonts'
CORPUS = SKILL / 'corpus'
RTL_FONT = FONTS / 'NotoNaskhArabic-Regular.ttf'
AR_PHRASE = 'السلام عليكم ورحمة الله'


def _gate(verdict, name):
    hits = [g for g in verdict.gates if g.name == name]
    assert len(hits) == 1, f'{name}: {[g.name for g in verdict.gates]}'
    return hits[0]


def _findings(verdict, name):
    return [(f.page, f.where, f.text) for f in _gate(verdict, name).findings]


def _arabic_glyph_by_glyph(path):
    """An output page whose Arabic was drawn by TextWriter: no shaping, no /ActualText.
    Raises SkipTest when the Naskh face is not fetched."""
    if not RTL_FONT.is_file():
        raise unittest.SkipTest(f'{RTL_FONT.name} not fetched (tools/fetch_test_fonts.py)')
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=612, height=792)
        tw = pymupdf.TextWriter(page.rect)
        tw.append((72, 80), AR_PHRASE, font=pymupdf.Font(fontfile=str(RTL_FONT)),
                  fontsize=12, right_to_left=True)
        tw.write_text(page)
        doc.save(path)
    finally:
        doc.close()


class FindingShapeTests(unittest.TestCase):
    def test_finding_gate_result_and_verdict_serialise(self):
        import pdf_translate
        from pdf_translate.verify import Finding, GateResult, VerifyVerdict
        f = Finding(page=2, where='ApplicantName', text='missing')
        self.assertEqual(f.to_dict(), {'page': 2, 'where': 'ApplicantName', 'text': 'missing'})
        g = GateResult(name='field-parity', status='FAIL', message='1', findings=(f,))
        self.assertEqual(g.to_dict(), {
            'name': 'field-parity', 'status': 'FAIL', 'message': '1',
            'findings': [{'page': 2, 'where': 'ApplicantName', 'text': 'missing'}]})
        self.assertEqual(GateResult(name='x', status='PASS').findings, ())
        v = VerifyVerdict(exit_code=1, gates=(g,), original='a.pdf', output='b.pdf')
        d = v.to_dict()
        self.assertEqual(d['schema'], 1)
        self.assertEqual(d['version'], pdf_translate.__version__)
        self.assertEqual((d['original'], d['output'], d['exit_code']), ('a.pdf', 'b.pdf', 1))
        self.assertEqual(d['gates'], [g.to_dict()])
        json.dumps(d)   # must be JSON-serialisable as is

    def test_run_verify_fills_original_and_output(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual((v.original, v.output), (src, out))
            self.assertTrue(all(isinstance(g.findings, tuple) for g in v.gates))
            self.assertEqual(v.to_dict()['gates'][0]['name'], 'field-parity')
