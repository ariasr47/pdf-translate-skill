#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract never overwrites a widget_text.json that holds authored text.

SKILL.md says to run `init` bare for the scaffold, author the targets, then
run `init --widget-text` again. That second run applied the targets, then
extract wrote a fresh scaffold over the file the author had just filled in:
canary run 4 lost 5 authored dropdown labels that way.
"""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pikepdf

from tests.test_pipeline import (CORPUS, build_widget_text_pdf, extract_segments,
                                 identity_widget_text, pipeline, strip_text)

from pdf_translate.extract_segments import run_extract

CHOICE_FIELDS = CORPUS / 'choice_fields.pdf'


def _spanish(scaffold):
    """Every target authored as a marked copy of its source."""
    spec = identity_widget_text(scaffold)
    for entry in spec.values():
        for key, val in entry.items():
            for slot in (val if key == 'options' else [val]):
                slot['target'] = 'ES ' + slot['source']
    for field, entry in scaffold.items():
        spec[field]['type'] = entry['type']
    return spec


def _displays(path):
    """{field: [display, ...]} of every choice field's /Opt."""
    out = {}
    with pikepdf.open(path) as pdf:
        for page in pdf.pages:
            for a in page.get('/Annots', []):
                if '/Opt' in a:
                    out[str(a.get('/T'))] = [
                        str(o[1]) if isinstance(o, pikepdf.Array) else str(o)
                        for o in a['/Opt']]
    return out


def _init(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = pipeline.main(['init', *argv])
    return rc, buf.getvalue()


class AuthoredWidgetTextIsKeptTests(unittest.TestCase):

    def test_init_with_widget_text_keeps_the_file_it_applied(self):
        with tempfile.TemporaryDirectory() as work:
            rc, log = _init(str(CHOICE_FIELDS), '--work', work)
            self.assertEqual(rc, 0, msg=log)
            path = Path(work, 'widget_text.json')
            authored = _spanish(json.loads(path.read_text(encoding='utf-8')))
            path.write_text(json.dumps(authored, ensure_ascii=False, indent=1),
                            encoding='utf-8')
            before = path.read_bytes()

            rc, log = _init(str(CHOICE_FIELDS), '--work', work,
                            '--widget-text', str(path))
            self.assertEqual(rc, 0, msg=log)
            self.assertEqual(path.read_bytes(), before, msg=log)
            self.assertIn('kept', log)
            self.assertEqual(
                _displays(os.path.join(work, 'stripped.pdf')),
                {'Fruit': ['ES Apple', 'ES Pear', 'ES Date'],
                 'Color': ['ES Red', 'ES Blue']})

    def test_a_bare_rerun_keeps_it_too(self):
        with tempfile.TemporaryDirectory() as work:
            _init(str(CHOICE_FIELDS), '--work', work)
            path = Path(work, 'widget_text.json')
            path.write_text(json.dumps(
                {'Fruit': {'options': {'Apple': 'Manzana'}}}), encoding='utf-8')
            before = path.read_bytes()
            rc, log = _init(str(CHOICE_FIELDS), '--work', work)
            self.assertEqual(rc, 0, msg=log)
            self.assertEqual(path.read_bytes(), before)

    def test_a_file_that_is_not_json_is_kept(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work, 'widget_text.json')
            path.write_text('{"Fruit": {"options": [', encoding='utf-8')
            result = run_extract(str(CHOICE_FIELDS), outdir=work)
            self.assertEqual(path.read_text(encoding='utf-8'),
                             '{"Fruit": {"options": [')
            self.assertTrue(result.widget_text_kept)

    def test_an_unauthored_scaffold_is_refreshed(self):
        # A work directory reused for another PDF: its old scaffold has no
        # authored text, so the new PDF's scaffold replaces it.
        with tempfile.TemporaryDirectory() as work:
            other = os.path.join(work, 'other.pdf')
            build_widget_text_pdf(other)
            extract_segments.extract_segments(other, outdir=work)
            self.assertIn('Applicant', json.loads(
                Path(work, 'widget_text.json').read_text(encoding='utf-8')))
            result = run_extract(str(CHOICE_FIELDS), outdir=work)
            self.assertFalse(result.widget_text_kept)
            self.assertEqual(
                json.loads(Path(work, 'widget_text.json')
                           .read_text(encoding='utf-8')),
                strip_text.widget_text_scaffold(str(CHOICE_FIELDS)))

    def test_extracting_twice_writes_the_same_scaffold(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = (os.path.join(tmp, d) for d in ('a', 'b'))
            extract_segments.extract_segments(str(CHOICE_FIELDS), outdir=first)
            shutil.copytree(first, second, dirs_exist_ok=True)
            result = extract_segments.extract_segments(str(CHOICE_FIELDS),
                                                       outdir=second)
            self.assertFalse(result['widget_text_kept'])
            self.assertEqual(Path(first, 'widget_text.json').read_bytes(),
                             Path(second, 'widget_text.json').read_bytes())

    def test_the_result_still_carries_the_fresh_scaffold(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work, 'widget_text.json')
            path.write_text(json.dumps(
                {'Color': {'options': {'Red': 'Rojo'}}}), encoding='utf-8')
            result = extract_segments.extract_segments(str(CHOICE_FIELDS),
                                                       outdir=work)
            self.assertTrue(result['widget_text_kept'])
            self.assertEqual(result['widget_text'],
                             strip_text.widget_text_scaffold(str(CHOICE_FIELDS)))


if __name__ == '__main__':
    unittest.main()
