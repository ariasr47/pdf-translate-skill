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


class FormAndPageGateFindingsTests(unittest.TestCase):
    def test_missing_field_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            doc = pymupdf.open()
            try:
                page = doc.new_page()
                page.insert_text((72, 72), 'Alpha source sentence here.')
                w = pymupdf.Widget()
                w.field_name = 'ApplicantName'
                w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
                w.rect = pymupdf.Rect(72, 100, 280, 118)
                page.add_widget(w)
                doc.save(src)
            finally:
                doc.close()
            _tiny_pdf(out, 'Alpha source sentence here.')
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'field-parity').status, 'FAIL')
            self.assertEqual(_findings(v, 'field-parity'), [(None, 'missing', 'ApplicantName')])

    def test_changed_opt_export_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            doc = pymupdf.open()
            try:
                page = doc.new_page()
                page.insert_text((72, 72), 'Choose one.')
                w = pymupdf.Widget()
                w.field_name = 'Choice'
                w.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
                w.rect = pymupdf.Rect(72, 100, 280, 118)
                w.choice_values = [['a', 'Apple'], ['b', 'Banana']]
                page.add_widget(w)
                doc.save(src)
            finally:
                doc.close()
            doc = pymupdf.open(src)
            try:
                for w in doc[0].widgets():
                    w.choice_values = [['x', 'Apple'], ['b', 'Banana']]
                    w.update()
                doc.save(out)
            finally:
                doc.close()
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'opt-export-parity').status, 'FAIL')
            (page, where, text), = _findings(v, 'opt-export-parity')
            self.assertEqual((page, where), (None, 'Choice'))
            self.assertIn('->', text)

    def test_ink_ratio_reports_every_page(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            (page, where, text), = _findings(v, 'ink-ratio')
            self.assertEqual((page, where), (1, 'page'))
            self.assertTrue(text.startswith('ink ratio '), text)

    def test_scan_page_is_named(self):
        from pdf_translate.verify import run_verify
        pdf = str(CORPUS / 'image_only.pdf')
        v = run_verify(pdf, pdf)
        self.assertEqual(_gate(v, 'extractable-text').status, 'FAIL')
        (page, where, text), = _findings(v, 'extractable-text')
        self.assertEqual((page, where), (1, 'page'))
        self.assertIn('images=', text)

    def test_ocr_layer_page_is_named(self):
        from pdf_translate.verify import run_verify
        pdf = str(CORPUS / 'ocr_layer.pdf')
        v = run_verify(pdf, pdf)
        self.assertEqual(_gate(v, 'visible-text').status, 'FAIL')
        page, where, text = _findings(v, 'visible-text')[0]
        self.assertEqual((page, where), (1, 'page'))
        self.assertIn('span area', text)

    def test_drifted_code_point_is_named(self):
        from pdf_translate.verify import run_verify
        latin = FONTS / 'NotoSans-Regular.ttf'
        if not latin.is_file():
            raise unittest.SkipTest('NotoSans-Regular.ttf not fetched (tools/fetch_test_fonts.py)')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            doc = pymupdf.open()
            try:
                page = doc.new_page()
                page.insert_text((72, 72), 'Hola\u00a0mundo.', fontname='F', fontfile=str(latin))
                doc.save(out)
            finally:
                doc.close()
            self.assertIn('\u00a0', pymupdf.open(out)[0].get_text(),
                          msg='the embedded face must keep U+00A0 in the text layer')
            Path(tr).write_text(json.dumps({'translations': {'Hello world.': 'Hola mundo.'}, 'skip': []}),
                                encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_gate(v, 'canonical-text').status, 'FAIL')
            self.assertEqual(_findings(v, 'canonical-text'), [(None, 'U+00A0', 'NO-BREAK SPACE x1')])


class ScriptGateFindingsTests(unittest.TestCase):
    def test_unshaped_arabic_page_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            _tiny_pdf(src, 'Peace be upon you and mercy')
            _arabic_glyph_by_glyph(bad)
            v = run_verify(src, bad, min_ink=0.05)
            self.assertEqual(_gate(v, 'arabic-letterforms').status, 'FAIL')
            (page, where, text), = _findings(v, 'arabic-letterforms')
            self.assertEqual((page, where), (1, 'page'))
            self.assertIn('isolated form', text)

    def test_broken_conjunct_face_is_named(self):
        from pdf_translate.verify import run_verify
        from tests.test_shaping_probe import DV_TARGET, build_source_pdf, draw_story_output, noto, strip_gsub
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            build_source_pdf(src)
            no_gsub = strip_gsub(noto('Devanagari'), os.path.join(tmp, 'no-gsub.ttf'))
            draw_story_output(bad, DV_TARGET, no_gsub)
            v = run_verify(src, bad, min_ink=0.1)
            self.assertEqual(_gate(v, 'conjunct-shaping').status, 'FAIL')
            (page, where, text), = _findings(v, 'conjunct-shaping')
            self.assertEqual(page, 1)
            self.assertEqual(where, 'NotoSansDevanagari-Regular')
            self.assertIn('क्षत्रिय', text)
            self.assertIn('8 -> 8', text)


class LeakGateFindingsTests(unittest.TestCase):
    SOURCE = 'Alpha bravo charlie delta echo.'

    def test_running_text_names_page_and_phrase(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, source=self.SOURCE, target=self.SOURCE)
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'leak-running').status, 'FAIL')
            page, where, text = _findings(v, 'leak-running')[0]
            self.assertEqual((page, where), (1, 'run'))
            self.assertIn('bravo', text.lower())

    def test_isolated_token_is_named_and_none_is_pass(self):
        from pdf_translate.verify import run_verify, verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, source=self.SOURCE, target='Hola mundo alpha.')
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'leak-isolated').status, 'REVIEW')
            self.assertEqual(_findings(v, 'leak-isolated'), [(1, 'token', 'alpha')])
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, source=self.SOURCE, target='Hola mundo.')
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'leak-isolated').status, 'PASS')
            self.assertEqual(_findings(v, 'leak-isolated'), [])
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify(src, out, min_ink=0.1)
            self.assertIn('PASS isolated source-script tokens: none', buf.getvalue())
            self.assertNotIn('REVIEW isolated source-script tokens', buf.getvalue())
