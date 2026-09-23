#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf-translate final stage: make text TYPED INTO form fields render.

A translated form whose fields still declare a Latin default appearance will
store what a user types and display nothing (or tofu) in most viewers. Values
survive; the rendering is what breaks — easy to miss if you only test with
ASCII, so test with real target-script input.

What this does:
  1. embeds a FULL-coverage target-script font (NOT the translation subset —
     users type arbitrary names containing characters the document never used)
  2. registers it in /AcroForm /DR /Font, creating /DR and /Font if absent
     (many forms ship a /DA referencing /Helv with no /DR at all)
  3. rewrites every text AND choice field's /DA to that font, preserving the
     original size (a combo box renders its selection from /DA the same way a
     text field renders a typed value)
  4. adds /Helv and /ZaDb alongside it: NeedAppearances makes viewers rebuild
     appearance streams, and a rebuilt checkbox draws its tick from ZapfDingbats
  5. sets an AcroForm-level /DA fallback and /NeedAppearances

Checkbox /DA entries are deliberately left alone — their appearance streams are
self-contained and carry their own ZapfDingbats resource.

Usage: python3 field_fonts.py IN.pdf FULL_FONT.ttf OUT.pdf [--name TransFF]
"""
import logging
import os
import re
import sys

import pikepdf
import pymupdf

from ._console import console, _arg
from .results import FieldFontsResult, PdfTranslateError

log = logging.getLogger(__name__)


def field_fonts(inp, font, out, name='TransFF'):
    """Embed a full-coverage field font and rewrite text-field /DA. Returns 0.

    The loud shape, unchanged: same signature, same printed bytes, same return
    code. `run_field_fonts` is the one a service calls — it returns a
    `FieldFontsResult` and raises instead of printing.
    """
    with console():
        try:
            run_field_fonts(inp, font, out, name=name)
        except PdfTranslateError as exc:
            log.info(exc.console_line)
            return exc.exit_code
    return 0


def run_field_fonts(inp, font, out, name='TransFF'):
    """Embed a full-coverage field font and rewrite text-field /DA.

    Silent. Returns a FieldFontsResult. Raises on refusal.
    """
    tmp = out + '.tmp_withfont.pdf'
    doc = pymupdf.open(inp)
    try:
        doc[0].insert_font(fontname='TransFieldFont', fontfile=font)
        doc.save(tmp)
    finally:
        doc.close()

    pdf = pikepdf.open(tmp)
    try:
        fobj = pdf.pages[0].Resources.Font.TransFieldFont

        if '/AcroForm' not in pdf.Root:
            log.info('no /AcroForm — nothing to do (non-form PDF); copying through')
            pdf.save(out)
            return FieldFontsResult(output=out, fields=0, face=name,
                                    acroform=False)
        af = pdf.Root.AcroForm

        if '/DR' not in af:
            af.DR = pdf.make_indirect(pikepdf.Dictionary())
        if '/Font' not in af.DR:
            af.DR.Font = pdf.make_indirect(pikepdf.Dictionary())

        # register under EXACTLY the name the /DA strings will reference — a
        # mismatch here leaves every /DA pointing at a resource that does not
        # exist, which renders as nothing while every structural check still
        # passes
        af.DR.Font[pikepdf.Name('/' + name)] = fobj

        for nm, base in (('/Helv', '/Helvetica'), ('/ZaDb', '/ZapfDingbats')):
            if pikepdf.Name(nm) not in af.DR.Font:
                extra = ({'Encoding': pikepdf.Name('/WinAnsiEncoding')}
                         if nm == '/Helv' else {})
                af.DR.Font[pikepdf.Name(nm)] = pdf.make_indirect(pikepdf.Dictionary(
                    Type=pikepdf.Name('/Font'), Subtype=pikepdf.Name('/Type1'),
                    BaseFont=pikepdf.Name(base), **extra))

        count, seen = 0, set()

        def fix_da(obj):
            nonlocal count
            da = obj.get('/DA')
            size = '0'
            if da is not None:
                m = re.match(r'/\S+\s+([\d.]+)\s+Tf', str(da))
                if m:
                    size = m.group(1)
            obj.DA = pikepdf.String(f'/{name} {size} Tf 0 g')
            count += 1

        for page in pdf.pages:
            for a in page.get('/Annots', []):
                parent = a.get('/Parent')
                ft = a.get('/FT') or (parent and parent.get('/FT'))
                # Choice fields (/Ch) render typed or selected text from
                # their own /DA exactly as text fields do. Leaving them on a
                # Latin default is the same tofu, one widget over.
                if ft in (pikepdf.Name('/Tx'), pikepdf.Name('/Ch')):
                    fix_da(a)
                    if parent is not None:
                        key = parent.objgen
                        if key not in seen:
                            fix_da(parent)
                            seen.add(key)

        af.DA = pikepdf.String(f'/{name} 0 Tf 0 g')
        af.NeedAppearances = True
        pdf.save(out)
    finally:
        pdf.close()

    try:
        os.remove(tmp)
    except OSError as e:
        # Windows: the temp file can stay locked (WinError 32) after a
        # successful save. The output PDF is already written; do not fail.
        if getattr(e, 'winerror', None) == 32 or e.errno in (13, 16):
            log.info(f'(temp cleanup skipped: {e})')
        else:
            raise
    log.info(f'registered /{name} in /DR, rewrote /DA on {count} text and '
             f'choice field objects -> {out}')
    if count == 0:
        log.info('  (no text or choice fields found — checkboxes and buttons '
                 'are unaffected by design)')
    return FieldFontsResult(output=out, fields=count, face=name,
                            acroform=True)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    inp, font, out = argv[0], argv[1], argv[2]
    name = _arg(argv, '--name', 'TransFF')
    return field_fonts(inp, font, out, name=name)


if __name__ == '__main__':
    raise SystemExit(main())
