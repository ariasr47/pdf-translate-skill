#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every outcome verify prints reaches a consumer as data: GateResult.findings,
VerifyVerdict.to_dict(), --report and --fail-on-review. Spec:
docs/BRIEF-unattended-delivery.md, task A and B."""
import io
import json
import os
import shutil
import stat
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


def _spaceless_job(tmp):
    """Source and output both Japanese, drawn with PyMuPDF's built-in CJK face:
    the leak scan cannot tell the sides apart and prints one REVIEW line."""
    src = os.path.join(tmp, 'orig.pdf')
    out = os.path.join(tmp, 'out.pdf')
    for path, text in ((src, '申立人の氏名を記入してください。'), (out, '申請者の名前を書いてください。')):
        doc = pymupdf.open()
        try:
            doc.new_page().insert_text((72, 72), text, fontname='japan')
            doc.save(path)
        finally:
            doc.close()
    return src, out


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
            self.assertEqual((v.original, v.output), (os.path.abspath(src), os.path.abspath(out)))
            self.assertTrue(all(isinstance(g.findings, tuple) for g in v.gates))
            self.assertEqual(v.to_dict()['gates'][0]['name'], 'field-parity')

    def test_run_verify_records_absolute_paths_like_the_cli(self):
        """A library caller passing relative paths gets the same report the CLI writes."""
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            if os.path.splitdrive(src)[0].lower() != os.path.splitdrive(os.getcwd())[0].lower():
                raise unittest.SkipTest('temp dir on another drive; no relative path exists')
            rel_src, rel_out = os.path.relpath(src), os.path.relpath(out)
            self.assertFalse(os.path.isabs(rel_src))
            v = run_verify(rel_src, rel_out, translations=tr, min_ink=0.1)
            self.assertEqual((v.original, v.output), (os.path.abspath(src), os.path.abspath(out)))


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
            self.assertRegex(text, r'^(PASS|FAIL) ink ratio \d+\.\d\d$')

    def test_ink_ratio_names_the_failing_page(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            doc = pymupdf.open()
            try:
                for text in ('Hello world.', 'Second page text.'):
                    doc.new_page().insert_text((72, 72), text)
                doc.save(src)
            finally:
                doc.close()
            doc = pymupdf.open()
            try:
                doc.new_page().insert_text((72, 72), 'Hola mundo.')
                doc.new_page()   # page 2: nothing drawn
                doc.save(out)
            finally:
                doc.close()
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'ink-ratio').status, 'FAIL')
            findings = _findings(v, 'ink-ratio')
            self.assertEqual([f[0] for f in findings], [1, 2])
            self.assertRegex(findings[0][2], r'^PASS ink ratio ')
            self.assertEqual(findings[1][2], 'FAIL ink ratio 0.00')

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

    def test_shared_spaceless_family_names_the_script(self):
        """zh -> ja: the scan cannot tell the sides apart; the REVIEW names the family."""
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out = _spaceless_job(tmp)
            v = run_verify(src, out, min_ink=0.1)
            self.assertEqual(_gate(v, 'leak-scan').status, 'REVIEW')
            self.assertEqual(_findings(v, 'leak-scan'), [(None, 'script', 'CJK')])


class MappingReadOrderTests(unittest.TestCase):
    """A malformed mapping fails as a mapping, before the output is read.

    The translated document's text is read once and shared by three gates.
    That read has to stay behind the mapping, or a job with both a bad
    mapping and an unreadable output surfaces a content-stream error instead
    of the mapping error that actually needs fixing.
    """

    def test_a_malformed_mapping_is_reported_before_the_output_is_read(self):
        import importlib
        from pdf_translate.verify import run_verify

        # `pdf_translate.verify` the NAME is the exported function; the module
        # has to be asked for by import_module.
        verify_module = importlib.import_module('pdf_translate.verify')

        reads = []
        real = verify_module.extract_actualtext

        def unreadable(page):
            reads.append(page.number)
            raise RuntimeError('mupdf: broken content stream')

        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            conf = json.loads(Path(tr).read_text(encoding='utf-8'))
            # Hand-authored and wrong: a merge's `html` must be a string.
            conf['merges'] = [{'page': 0, 'lines': ['Hello world.'],
                               'html': ['not', 'a', 'string']}]
            Path(tr).write_text(json.dumps(conf), encoding='utf-8')

            verify_module.extract_actualtext = unreadable
            try:
                with self.assertRaises(TypeError):
                    run_verify(src, out, translations=tr, min_ink=0.1)
            finally:
                verify_module.extract_actualtext = real

        self.assertEqual(reads, [], 'the output was read before the mapping')


class TranslationGateFindingsTests(unittest.TestCase):
    def test_empty_target_and_missing_placement_name_the_target(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            _tiny_pdf(out, 'Adios.')
            Path(tr).write_text(json.dumps({'translations': {'Hello world.': 'Hola mundo.', 'Other': '   '},
                                            'skip': []}), encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'empty-targets'), [(None, 'target', 'Other')])
            self.assertEqual(_findings(v, 'placement'), [(None, 'target', 'Hola mundo.')])

    def test_findings_are_not_truncated_like_the_console(self):
        from pdf_translate.verify import run_verify, verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            _tiny_pdf(out, 'Adios.')
            targets = {f'Source line {i:02d}': f'Target line {i:02d}' for i in range(35)}
            Path(tr).write_text(json.dumps({'translations': targets, 'skip': []}), encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(len(_findings(v, 'placement')), 35)
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify(src, out, translations=tr, min_ink=0.1)
            printed = [ln for ln in buf.getvalue().splitlines() if ln.startswith('   Target line ')]
            self.assertEqual(len(printed), 30)   # the console's [:30] limit, unchanged

    def test_glyph_by_glyph_target_is_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Peace be upon you and mercy')
            Path(tr).write_text(json.dumps({'translations': {'Peace be upon you and mercy': AR_PHRASE},
                                            'skip': []}, ensure_ascii=False), encoding='utf-8')
            _arabic_glyph_by_glyph(bad)
            v = run_verify(src, bad, translations=tr, min_ink=0.05)
            self.assertEqual(_findings(v, 'shaped-actualtext'), [(None, 'target', AR_PHRASE)])

    def test_vanished_identifier_is_named(self):
        from pdf_translate.verify import run_verify
        from tests.test_pipeline import QUOTE_LINE, SCHED_LINE, VANISH_IDENT_TR, build_identifier_pdf
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_identifier_pdf(src)
            doc = pymupdf.open()
            try:
                page = doc.new_page(width=612, height=792)
                page.insert_text((72, 80), VANISH_IDENT_TR[QUOTE_LINE], fontsize=12)
                page.insert_text((72, 110), VANISH_IDENT_TR[SCHED_LINE], fontsize=12)
                doc.save(out)
            finally:
                doc.close()
            Path(tr).write_text(json.dumps({'translations': VANISH_IDENT_TR, 'skip': []},
                                           ensure_ascii=False), encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_gate(v, 'identifiers').status, 'FAIL')
            names = [text for _, where, text in _findings(v, 'identifiers') if where == 'identifier']
            self.assertIn('Attachment A', names)

    def test_metadata_scaled_runs_and_override_markers_are_named(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, lang='es',
                                scale_report=[{'page': 0, 'ratio': 0.85, 'key': 'Hello world.'}])
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            (page, where, text), = _findings(v, 'metadata')
            self.assertEqual((page, where), (None, 'lang'))
            self.assertIn('"es"', text)
            self.assertEqual(_findings(v, 'scaled-runs'), [(1, '0.85x', 'Hello world.')])
        segments = [{'page': 0, 'text': 'd. Hello world.        .... $', 'marker': 'd.',
                     'core': 'Hello world.', 'dots': '....', 'tail': '$'}]
        drop = [{'page': 0, 'contains': 'Hello world.',
                 'parts': [{'text': 'Hola mundo.', 'x': 72.0}]}]
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, overrides=drop, segments=segments)
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'override-markers'),
                             [(None, 'Hello world.', 'd.'), (None, 'Hello world.', '$')])

    def test_button_caption_gates_name_field_and_caption(self):
        from pdf_translate.verify import run_verify
        from tests.test_pipeline import (LONG_CAPTION, NARROW_BTN, SHORT_CAPTION, SOURCE_SENTENCE,
                                         TARGET_SENTENCE, build_narrow_button_pdf)
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_narrow_button_pdf(src)
            shutil.copy(src, out)   # caption still SHORT_CAPTION in the output
            Path(tr).write_text(json.dumps({'translations': {SOURCE_SENTENCE: TARGET_SENTENCE,
                                                             SHORT_CAPTION: 'Aceptar'}, 'skip': []}),
                                encoding='utf-8')
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'button-captions'), [(None, NARROW_BTN, SHORT_CAPTION)])
            self.assertEqual(_gate(v, 'caption-width').status, 'PASS')
            doc = pymupdf.open(src)
            try:
                for w in doc[0].widgets():
                    if w.field_name == NARROW_BTN:
                        w.button_caption = LONG_CAPTION
                        w.update()
                doc.save(out)
            finally:
                doc.close()
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_findings(v, 'caption-width'), [(None, NARROW_BTN, LONG_CAPTION)])

    def test_scaled_runs_tolerates_a_malformed_sidecar_entry(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, scale_report=[
                {'page': None, 'ratio': 'n/a', 'key': 'Hello world.'},
                {'ratio': 0.9},
            ])
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_gate(v, 'scaled-runs').status, 'REVIEW')
            self.assertEqual(_findings(v, 'scaled-runs'),
                             [(None, 'n/ax', 'Hello world.'), (None, '0.90x', '')])

    def test_missing_lang_review_names_lang(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)   # no lang in the mapping
            v = run_verify(src, out, translations=tr, min_ink=0.1)
            self.assertEqual(_gate(v, 'metadata-lang').status, 'REVIEW')
            self.assertEqual(_findings(v, 'metadata-lang'),
                             [(None, 'lang', 'translations.json has no "lang"')])


class FindingsInvariantTests(unittest.TestCase):
    """Every gate that is FAIL or REVIEW carries at least one finding.

    The report exists so that a consumer can explain a non-PASS status from
    data alone. A location-less FAIL or REVIEW defeats that, whichever gate
    grows it next; this test runs the invariant over every kind of job the
    suite builds."""

    def _jobs(self, tmp):
        source = 'Alpha bravo charlie delta echo.'
        segments = [{'page': 0, 'text': 'd. Hello world.        .... $', 'marker': 'd.',
                     'core': 'Hello world.', 'dots': '....', 'tail': '$'}]
        drop = [{'page': 0, 'contains': 'Hello world.',
                 'parts': [{'text': 'Hola mundo.', 'x': 72.0}]}]
        jobs = []
        for name, kw in (('trivial', {}), ('meta-fail', {'lang': 'es'}),
                         ('scaled', {'scale_report': [{'page': 0, 'ratio': 0.85, 'key': 'Hello world.'}]}),
                         ('override', {'overrides': drop, 'segments': segments}),
                         ('leak', {'source': source, 'target': source})):
            d = os.path.join(tmp, name)
            os.makedirs(d)
            src, out, tr = _job(d, **kw)
            jobs.append((name, src, out, tr))
        d = os.path.join(tmp, 'spaceless')
        os.makedirs(d)
        src, out = _spaceless_job(d)
        jobs.append(('spaceless', src, out, None))
        for pdf in ('image_only.pdf', 'ocr_layer.pdf'):
            jobs.append((pdf, str(CORPUS / pdf), str(CORPUS / pdf), None))
        try:
            d = os.path.join(tmp, 'arabic')
            os.makedirs(d)
            src = os.path.join(d, 'orig.pdf')
            bad = os.path.join(d, 'bad.pdf')
            tr = os.path.join(d, 'translations.json')
            _tiny_pdf(src, 'Peace be upon you and mercy')
            Path(tr).write_text(json.dumps({'translations': {'Peace be upon you and mercy': AR_PHRASE},
                                            'skip': []}, ensure_ascii=False), encoding='utf-8')
            _arabic_glyph_by_glyph(bad)
            jobs.append(('arabic', src, bad, tr))
        except unittest.SkipTest:
            pass
        return jobs

    def test_every_fail_or_review_gate_has_a_finding(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            seen = set()
            for name, src, out, tr in self._jobs(tmp):
                v = run_verify(src, out, translations=tr, min_ink=0.05)
                for g in v.gates:
                    if g.status in ('FAIL', 'REVIEW'):
                        seen.add(g.name)
                        self.assertTrue(g.findings, msg=f'{name}: {g.name} is {g.status} with no finding')
            # The jobs above must exercise a broad set, or the invariant proves little.
            for expected in ('metadata', 'metadata-lang', 'scaled-runs', 'override-markers',
                             'leak-running', 'leak-scan', 'extractable-text', 'visible-text'):
                self.assertIn(expected, seen)


class ReportAndPolicyTests(unittest.TestCase):
    def _console(self, argv):
        from pdf_translate.verify import main
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(argv)
        lines = [ln for ln in buf.getvalue().splitlines() if not ln.startswith('elapsed ')]
        return rc, lines

    def test_report_flag_writes_the_verdict_and_leaves_the_console_alone(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp, lang='es')
            report = os.path.join(tmp, 'verify_report.json')
            base = [src, out, '--translations', tr, '--min-ink', '0.1']
            rc_plain, plain = self._console(base)
            rc_rep, with_report = self._console(base + ['--report', report])
            self.assertEqual((rc_plain, rc_rep), (1, 1))
            self.assertEqual(plain, with_report)
            data = json.loads(Path(report).read_text(encoding='utf-8'))
            expected = run_verify(os.path.abspath(src), os.path.abspath(out),
                                  translations=tr, min_ink=0.1).to_dict()
            self.assertEqual(data['original'], os.path.abspath(src))
            self.assertEqual(data['output'], os.path.abspath(out))
            self.assertEqual(data['gates'], expected['gates'])
            self.assertEqual(data['schema'], 1)
            self.assertIs(data['fail_on_review'], False)
            names = [g['name'] for g in data['gates']]
            self.assertIn('metadata', names)
            meta = next(g for g in data['gates'] if g['name'] == 'metadata')
            self.assertEqual(meta['findings'][0]['where'], 'lang')

    def test_unwritable_report_path_keeps_the_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)
            rc, lines = self._console([src, out, '--translations', tr, '--min-ink', '0.1',
                                       '--report', os.path.join(tmp, 'no-such-dir', 'r.json')])
            self.assertEqual(rc, 0)
            self.assertTrue(any('could not write' in ln for ln in lines), lines)

    def test_a_refused_report_write_leaves_no_stale_report(self):
        # PR #5 review, defect 1: pipeline.py rebuild writes to a FIXED path, so
        # a reused work dir is the normal case. A report from an earlier run must
        # not survive a refused write, or a consumer reads PASS for a job that
        # failed, attributed to a document it did not ask about. After the second
        # run either no report exists or it describes the second run.
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = os.path.join(tmp, 'good'), os.path.join(tmp, 'bad')
            os.mkdir(good)
            os.mkdir(bad)
            report = os.path.join(tmp, 'r.json')
            try:
                src, out, tr = _job(good)
                rc, _ = self._console([src, out, '--translations', tr, '--min-ink', '0.1',
                                       '--report', report])
                self.assertEqual(rc, 0)
                with open(report, encoding='utf-8') as f:
                    self.assertEqual(json.load(f)['exit_code'], 0)
                os.chmod(report, stat.S_IREAD)   # the file is unwritable; its directory is not
                src2, out2, tr2 = _job(bad, lang='es')   # output declares no lang: metadata FAIL
                rc, lines = self._console([src2, out2, '--translations', tr2, '--min-ink', '0.1',
                                           '--report', report])
                self.assertEqual(rc, 1, lines)
                if os.path.exists(report):
                    with open(report, encoding='utf-8') as f:
                        data = json.load(f)
                    self.assertEqual(data['exit_code'], 1, data)
                    self.assertEqual(data['output'], os.path.abspath(out2), data)
            finally:
                if os.path.exists(report):
                    os.chmod(report, stat.S_IREAD | stat.S_IWRITE)

    def test_fail_on_review_turns_review_into_exit_1(self):
        from pdf_translate.verify import run_verify
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = _job(tmp)   # no lang -> metadata-lang REVIEW, no FAIL
            base = [src, out, '--translations', tr, '--min-ink', '0.1']
            self.assertEqual(self._console(base)[0], 0)
            rc, lines = self._console(base + ['--fail-on-review'])
            self.assertEqual(rc, 1)
            self.assertTrue(any(ln.startswith('FAIL: ') and 'REVIEW' in ln for ln in lines), lines)
            self.assertEqual(run_verify(src, out, translations=tr, min_ink=0.1).exit_code, 0)
            self.assertEqual(run_verify(src, out, translations=tr, min_ink=0.1,
                                        fail_on_review=True).exit_code, 1)
            report = os.path.join(tmp, 'r.json')
            self._console(base + ['--fail-on-review', '--report', report])
            data = json.loads(Path(report).read_text(encoding='utf-8'))
            self.assertIs(data['fail_on_review'], True)
            self.assertEqual(data['exit_code'], 1)
            self.assertEqual([g['name'] for g in data['gates'] if g['status'] == 'FAIL'], [])

    def test_pipeline_rebuild_writes_the_report_into_the_work_dir(self):
        from pdf_translate.extract_segments import extract_segments
        from pdf_translate.pipeline import main as pipeline_main
        from pdf_translate.strip_text import strip_text
        latin = FONTS / 'NotoSans-Regular.ttf'
        if not latin.is_file():
            raise unittest.SkipTest('NotoSans-Regular.ttf not fetched (tools/fetch_test_fonts.py)')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            _tiny_pdf(src, 'Hello world.')
            font = str(latin)
            Path(tr).write_text(json.dumps({
                'fonts': {'regular': font, 'bold': font, 'italic': font, 'bold_italic': font},
                'translations': {'Hello world.': 'Hola mundo.'}, 'lang': 'es',
                'merges': [], 'overrides': [], 'center': [], 'skip': []}), encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                strip_text(src, os.path.join(tmp, 'stripped.pdf'))
                extract_segments(src, outdir=tmp)
                rc = pipeline_main(['rebuild', '--work', tmp, src, out, '--min-ink', '0.1',
                                    '--translations', tr])
            self.assertEqual(rc, 0)
            data = json.loads(Path(tmp, 'verify_report.json').read_text(encoding='utf-8'))
            self.assertEqual(data['schema'], 1)
            self.assertEqual(data['exit_code'], 0)


class VersionLockstepTests(unittest.TestCase):
    def test_four_version_sources_agree(self):
        import re
        import pdf_translate
        root = SKILL.parent
        skill = re.search(r'^\s+version:\s*"(\d+)"', (SKILL / 'SKILL.md').read_text(encoding='utf-8'),
                          re.M).group(1)
        plugin = json.loads((root / '.claude-plugin' / 'plugin.json').read_text(encoding='utf-8'))['version']
        pyproject = re.search(r'^version\s*=\s*"([\d.]+)"', (SKILL / 'pyproject.toml').read_text(encoding='utf-8'),
                              re.M).group(1)
        self.assertEqual(plugin, f'{skill}.0.0')
        self.assertEqual(pyproject, plugin)
        self.assertEqual(pdf_translate.__version__, skill)
        self.assertEqual(skill, '76')


class PackagingMetadataTests(unittest.TestCase):
    """R-110: the licence is a PEP 639 SPDX expression with its file named.
    The TOML table form (`{text = "MIT"}`) is deprecated, and setuptools
    stops accepting it on 2027-02-18; the string form needs setuptools>=77."""

    def test_the_licence_is_an_spdx_expression_with_its_file(self):
        import tomllib
        conf = tomllib.loads((SKILL / 'pyproject.toml').read_text(encoding='utf-8'))
        project = conf['project']
        self.assertEqual(project['license'], 'MIT')
        self.assertEqual(project['license-files'], ['LICENSE'])
        self.assertTrue((SKILL / 'LICENSE').is_file())
        self.assertIn('setuptools>=77', conf['build-system']['requires'])
        # A licence classifier beside an expression is an error under PEP 639.
        self.assertFalse(any(c.startswith('License ::') for c in project.get('classifiers', [])))
