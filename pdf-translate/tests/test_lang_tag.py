#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""/Lang carries the mapping's whole language tag, and verify reads it whole.

PyMuPDF's `set_language` keeps only part of a tag: `es-US` became `es`,
`zh-Hant-TW` became `zh`, while retypeset's log said `/Lang -> es-US`. Its
`doc.language` getter cuts a tag that is written whole the same way. So a
typography build for `en-US` failed verify's metadata gate, and a
`zh-Hant-TW` output with no mapping was judged against Simplified forms.
"""
import importlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pymupdf

from pdf_translate import run_retypeset, run_verify
from tests.test_pipeline import (DOC_TITLE, DOC_TITLE_ES, DOC_TOC, DOC_TOC_ES,
                                 SOURCE_SENTENCE, TARGET_SENTENCE, build_metadata_pdf,
                                 extract_segments, find_test_font, strip_text, verify,
                                 write_mapping)
from tests.typography_fixtures import make_job

retypeset = importlib.import_module('pdf_translate.retypeset')

TAGS = ['es-US', 'pt-BR', 'es-419', 'en-GB', 'zh-Hans', 'zh-Hant-TW',
        'sr-Latn-RS', 'de-CH-1996', 'ja']


def _raw_lang(path_or_doc):
    """The catalog's /Lang string exactly as stored, or None."""
    if isinstance(path_or_doc, (str, Path)):
        with pymupdf.open(path_or_doc) as doc:
            return _raw_lang(doc)
    kind, value = path_or_doc.xref_get_key(path_or_doc.pdf_catalog(), 'Lang')
    return value if kind == 'string' else None


def _build(tmp, lang):
    """The metadata fixture retypeset with `lang`: (src, out, mapping, log)."""
    src = os.path.join(tmp, 'orig.pdf')
    stripped = os.path.join(tmp, 'stripped.pdf')
    out = os.path.join(tmp, 'out.pdf')
    tr = os.path.join(tmp, 'translations.json')
    build_metadata_pdf(src)
    extract_segments.extract_segments(src, outdir=tmp)
    strip_text.strip_text(src, stripped)
    mapping = {SOURCE_SENTENCE: TARGET_SENTENCE, DOC_TITLE: DOC_TITLE_ES,
               **dict(zip(DOC_TOC, DOC_TOC_ES))}
    write_mapping(tr, mapping, find_test_font(), lang=lang)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
    assert rc == 0, buf.getvalue()
    return src, out, tr, buf.getvalue()


def _with_lang(src, dst, tag):
    doc = pymupdf.open(src)
    doc.xref_set_key(doc.pdf_catalog(), 'Lang', pymupdf.get_pdf_str(tag))
    doc.save(dst)
    doc.close()


class LegacyLangTests(unittest.TestCase):

    def test_retypeset_writes_the_whole_tag_and_logs_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out, _, log = _build(tmp, 'es-US')
            self.assertEqual(_raw_lang(out), 'es-US')
            self.assertIn('/Lang -> es-US', log)

    def test_every_tag_is_written_as_the_mapping_gives_it(self):
        for tag in TAGS + ['Japanese']:
            with self.subTest(tag=tag):
                doc = pymupdf.open()
                doc.new_page()
                report = retypeset.apply_document_metadata(doc, {}, {}, tag)
                self.assertEqual(_raw_lang(doc), tag)
                self.assertEqual(report['lang'], tag)

    def test_legacy_gate_reads_the_whole_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, _ = _build(tmp, 'es-US')
            for tag, passes in (('es-US', True), ('es', True), ('fr-CA', False)):
                with self.subTest(tag=tag):
                    tagged = os.path.join(tmp, f'{tag}.pdf')
                    _with_lang(out, tagged, tag)
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        rc = verify.verify(src, tagged, translations=tr)
                    log = buf.getvalue()
                    if passes:
                        self.assertIn('PASS document metadata', log)
                    else:
                        self.assertNotEqual(rc, 0, msg=log)
                        self.assertIn('output declares "fr-CA"', log)

    def test_han_forms_gets_the_whole_output_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, _, _ = _build(tmp, 'es-MX')
            tagged = os.path.join(tmp, 'zh-Hant-TW.pdf')
            _with_lang(out, tagged, 'zh-Hant-TW')
            seen = []
            real = verify.han_forms_report

            def spy(doc, mapping_lang, output_lang, *args, **kwargs):
                seen.append(output_lang)
                return real(doc, mapping_lang, output_lang, *args, **kwargs)

            with mock.patch.object(verify, 'han_forms_report', spy):
                with redirect_stdout(io.StringIO()):
                    verify.verify(src, tagged)
            self.assertEqual(seen, ['zh-Hant-TW'])


class TypographyLangTests(unittest.TestCase):

    def _build(self, lang):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        job = make_job(Path(tmp.name))
        conf = json.loads(job['mapping'].read_text(encoding='utf-8'))
        conf['lang'] = lang
        job['mapping'].write_text(json.dumps(conf), encoding='utf-8')
        run_retypeset(*(str(job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                      original=str(job['original']))
        return job

    def _metadata(self, job):
        verdict = run_verify(str(job['original']), str(job['output']),
                             translations=str(job['mapping']), segments=str(job['segments']))
        gates = [g for g in verdict.gates if g.name == 'metadata']
        self.assertEqual(len(gates), 1)
        return gates[0]

    def test_a_region_tag_passes_the_metadata_gate(self):
        job = self._build('en-US')
        self.assertEqual(_raw_lang(job['output']), 'en-US')
        gate = self._metadata(job)
        self.assertEqual(gate.status, 'PASS', msg=[str(f) for f in gate.findings])

    def test_a_different_region_still_fails_it(self):
        job = self._build('en-US')
        _with_lang(job['output'], job['output'].with_name('gb.pdf'), 'en-GB')
        os.replace(job['output'].with_name('gb.pdf'), job['output'])
        gate = self._metadata(job)
        self.assertEqual(gate.status, 'FAIL')
        self.assertIn('output declares en-GB', ' '.join(str(f) for f in gate.findings))


if __name__ == '__main__':
    unittest.main()
