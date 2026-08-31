#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 1 of pdf-translate: prepare a PDF for text replacement.

Deletes ALL page text (BT..ET blocks) from content streams while leaving
vector graphics, images, and form-field widgets untouched, wraps surviving
content in q/Q (prevents graphics-state leakage into text you add later),
and removes the XFA layer if present (hybrid LiveCycle forms render the XFA
layer in Acrobat, hiding page edits).

Never use redaction annotations for text removal: they delete overlapping
form-field widgets.

Usage:
  python3 strip_text.py IN.pdf OUT.pdf [--hide-buttons name1,name2,...]
                                       [--captions captions.json]

--captions rewrites pushbutton /MK /CA strings in place (field count stays
exact). --hide-buttons sets the Hidden flag instead. Prefer captions when
the widget should remain as the UI chrome.

Prints a JSON report to stdout: pages processed, XFA removed or not,
pushbuttons that have no /A action (dead if XFA was removed — decide
whether to hide them, rewrite captions, or leave them), and any Form
XObjects that contained text (also stripped).
"""
import json
import sys

import pikepdf
from pikepdf import Name, parse_content_stream, unparse_content_stream


def strip_ops(owner, pdf=None):
    ops = parse_content_stream(owner)
    out, in_text, removed = [], False, 0
    for operands, op in ops:
        o = str(op)
        if o == 'BT':
            in_text = True
            removed += 1
            continue
        if o == 'ET':
            in_text = False
            continue
        if in_text:
            continue
        out.append((operands, op))
    return unparse_content_stream(out), removed


def _field_base(name):
    name = str(name)
    return name.split('[')[0] if name else name


def strip_text(src, dst, hide_buttons=None, captions=None):
    """Strip page text, wrap content in q/Q, remove XFA. Returns a report dict.

    hide_buttons: iterable of field names (base name, without [0] suffix).
    captions: dict of field name -> new /MK /CA caption (in-place rewrite).
    """
    hide = set(hide_buttons or [])
    captions = captions or {}

    pdf = pikepdf.open(src)
    report = {'xfa_removed': False, 'pages': [], 'dead_buttons': [],
              'form_xobjects_stripped': [], 'hidden': [],
              'rewritten_captions': []}

    acro = pdf.Root.get('/AcroForm')
    if acro is not None and '/XFA' in acro:
        del acro.XFA
        report['xfa_removed'] = True

    for i, page in enumerate(pdf.pages):
        data, removed = strip_ops(page, pdf)
        page.Contents = pdf.make_stream(b'q\n' + data + b'\nQ\n')
        report['pages'].append({'page': i, 'text_blocks_removed': removed})
        res = page.get('/Resources', {})
        for name, xo in dict(res.get('/XObject', {})).items():
            if xo.get('/Subtype') == Name('/Form'):
                xdata, xremoved = strip_ops(xo, pdf)
                if xremoved:
                    xo.write(b'q\n' + xdata + b'\nQ\n')
                    report['form_xobjects_stripped'].append(
                        {'page': i, 'xobject': str(name), 'blocks': xremoved})
        for a in page.get('/Annots', []):
            if a.get('/FT') != Name('/Btn'):
                continue
            ff = int(a.get('/Ff', 0) or 0)
            if not (ff & (1 << 16)):  # pushbutton flag
                continue
            t = str(a.get('/T', ''))
            base = _field_base(t)
            if a.get('/A') is None:
                report['dead_buttons'].append({'page': i, 'name': t})
            cap_key = t if t in captions else (base if base in captions else None)
            if cap_key is not None:
                mk = a.get('/MK')
                if mk is None:
                    a.MK = pikepdf.Dictionary()
                    mk = a.MK
                mk.CA = pikepdf.String(str(captions[cap_key]))
                # Stale appearance streams keep drawing the source-language
                # caption on top of /CA; drop them so NeedAppearances rebuilds.
                if '/AP' in a:
                    del a.AP
                report['rewritten_captions'].append(t)
            if base in hide or t in hide:
                a.F = 2
                report['hidden'].append(t)

    pdf.save(dst)
    pdf.close()
    return report


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    src, dst = argv[0], argv[1]
    hide = []
    if '--hide-buttons' in argv:
        hide = [n for n in argv[argv.index('--hide-buttons') + 1].split(',') if n]
    captions = None
    if '--captions' in argv:
        with open(argv[argv.index('--captions') + 1], encoding='utf-8') as f:
            captions = json.load(f)
    report = strip_text(src, dst, hide_buttons=hide, captions=captions)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
