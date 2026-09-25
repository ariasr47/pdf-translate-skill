#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify reviews widget text left in the source language.

Tooltips, dropdown display labels and text-field defaults never reach a
content stream, so the leak scan cannot see them. A strip without
`--widget-text` (a bare re-run of `init`) shipped them untranslated and no
gate said so. They are REVIEW, not FAIL: a label that is data (a code, an
ID) stays in the source language on purpose, and the widget-text mapping is
where the author says so.
"""
import json
import tempfile
import unittest
from pathlib import Path

import pymupdf

from pdf_translate.verify import GATE_NAMES, run_verify
from tests.test_pipeline import (CORPUS, FRUIT_OPTS, WIDGET_DEFAULT, WIDGET_TIP,
                                 build_plain_pdf, build_widget_text_pdf, strip_text)

CHOICE_FIELDS = str(CORPUS / 'choice_fields.pdf')
SPANISH = {'Apple': 'Manzana', 'Pear': 'Pera', 'Date': 'Dátil',
           'Red': 'Rojo', 'Blue': 'Azul'}


def _gate(orig, out, **kwargs):
    verdict = run_verify(orig, out, **kwargs)
    gates = [g for g in verdict.gates if g.name == 'widget-text']
    return gates[0] if gates else None


def _reported(gate):
    return sorted((f.where, f.text) for f in gate.findings)


class WidgetTextGateTests(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def _strip(self, src, widget_text=None, name='out.pdf'):
        out = str(self.tmp / name)
        strip_text.strip_text(src, out, widget_text=widget_text)
        return out

    def test_untranslated_dropdown_labels_are_reviewed_by_field(self):
        out = self._strip(CHOICE_FIELDS)
        gate = _gate(CHOICE_FIELDS, out)
        self.assertEqual(gate.status, 'REVIEW')
        self.assertEqual(_reported(gate), [
            ('Color', 'option Blue: Blue'), ('Color', 'option Red: Red'),
            ('Fruit', 'option Apple: Apple'), ('Fruit', 'option Date: Date'),
            ('Fruit', 'option Pear: Pear')])

    def test_translated_labels_pass(self):
        spec = {'Fruit': {'options': {k: SPANISH[k] for k in ('Apple', 'Pear', 'Date')}},
                'Color': {'options': {k: SPANISH[k] for k in ('Red', 'Blue')}}}
        out = self._strip(CHOICE_FIELDS, spec)
        gate = _gate(CHOICE_FIELDS, out)
        self.assertEqual(gate.status, 'PASS', msg=_reported(gate))

    def test_a_key_deleted_on_purpose_is_not_reported(self):
        spec = {'Fruit': {'options': {k: SPANISH[k] for k in ('Apple', 'Pear', 'Date')}}}
        out = self._strip(CHOICE_FIELDS, spec)
        mapping = self.tmp / 'wt.json'
        mapping.write_text(json.dumps(spec), encoding='utf-8')
        self.assertEqual(_gate(CHOICE_FIELDS, out).status, 'REVIEW')
        gate = _gate(CHOICE_FIELDS, out, widget_text=str(mapping))
        self.assertEqual(gate.status, 'PASS', msg=_reported(gate))

    def test_a_target_equal_to_its_source_is_a_keep(self):
        spec = {'Fruit': {'options': [
                    {'export': k, 'source': k, 'target': SPANISH[k]}
                    for k in ('Apple', 'Pear', 'Date')]},
                'Color': {'options': [
                    {'export': 'Red', 'source': 'Red', 'target': 'Rojo'},
                    {'export': 'Blue', 'source': 'Blue', 'target': 'Blue'}]}}
        out = self._strip(CHOICE_FIELDS, spec)
        mapping = self.tmp / 'wt.json'
        mapping.write_text(json.dumps(spec), encoding='utf-8')
        gate = _gate(CHOICE_FIELDS, out, widget_text=str(mapping))
        self.assertEqual(gate.status, 'PASS', msg=_reported(gate))

    def test_the_mapping_beside_translations_is_read(self):
        # A bare re-run: the scaffold beside translations.json still holds
        # nulls, so nothing was kept on purpose. An authored one marks keeps.
        out = self._strip(CHOICE_FIELDS)
        tr = self.tmp / 'translations.json'
        tr.write_text(json.dumps({'translations': {}}), encoding='utf-8')
        beside = self.tmp / 'widget_text.json'
        beside.write_text(json.dumps(strip_text.widget_text_scaffold(CHOICE_FIELDS)),
                          encoding='utf-8')
        self.assertEqual(_gate(CHOICE_FIELDS, out, translations=str(tr)).status, 'REVIEW')
        beside.write_text(json.dumps({}), encoding='utf-8')
        gate = _gate(CHOICE_FIELDS, out, translations=str(tr))
        self.assertEqual(gate.status, 'PASS', msg=_reported(gate))

    def test_tooltips_and_text_defaults_are_checked(self):
        src = str(self.tmp / 'orig.pdf')
        build_widget_text_pdf(src)
        out = self._strip(src)
        reported = _reported(_gate(src, out))
        self.assertIn(('Applicant', f'tooltip: {WIDGET_TIP}'), reported)
        self.assertIn(('Applicant', f'value: {WIDGET_DEFAULT}'), reported)
        for opt in FRUIT_OPTS:
            self.assertIn(('Fruit', f'option {opt}: {opt}'), reported)

    def test_strings_without_letters_are_not_reported(self):
        src = str(self.tmp / 'numbers.pdf')
        with pymupdf.open() as doc:
            page = doc.new_page(width=300, height=200)
            for i, (name, value, tip) in enumerate((('Year', '2026', '#12'),
                                                    ('Name', '', 'Your name'))):
                widget = pymupdf.Widget()
                widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
                widget.field_name = name
                widget.field_value = value
                widget.field_label = tip
                widget.rect = pymupdf.Rect(20, 20 + 30 * i, 200, 40 + 30 * i)
                page.add_widget(widget)
            doc.save(src)
        scaffold = strip_text.widget_text_scaffold(src)
        self.assertEqual(scaffold['Year']['value']['source'], '2026')
        self.assertEqual(scaffold['Year']['tooltip']['source'], '#12')
        out = self._strip(src, {'Name': {'tooltip': 'Su nombre'}})
        gate = _gate(src, out)
        self.assertEqual(gate.status, 'PASS', msg=_reported(gate))
        self.assertEqual(gate.message, '1 string(s)')

    def test_silent_without_widget_text(self):
        src = str(self.tmp / 'plain.pdf')
        build_plain_pdf(src)
        out = self._strip(src)
        self.assertIsNone(_gate(src, out))

    def test_the_gate_is_named_after_opt_export_parity(self):
        self.assertEqual(GATE_NAMES[GATE_NAMES.index('opt-export-parity') + 1],
                         'widget-text')


if __name__ == '__main__':
    unittest.main()
