#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 1 of pdf-translate: prepare a PDF for text replacement.

Deletes ALL page text (BT..ET blocks) from content streams while leaving
vector graphics, images, and form-field widgets untouched, wraps surviving
content in q/Q (prevents graphics-state leakage into text you add later),
and removes the XFA layer if present (hybrid LiveCycle forms render the XFA
layer in Acrobat, hiding page edits).

Form XObjects are stripped recursively (an XObject inside an XObject, any
depth) and page /Resources are resolved through /Parent inheritance, because
letterheads and imposed pages hide text there.

Strip is also a gate. After saving, the stripped file is re-read with
annotation appearances excluded; if any page still has text the run FAILS,
lists page and text, and the stripped file is deleted. A stripped file that
still carries source text must never reach retypeset. Widget captions and
field values are appearance streams, not page text; they do not count.

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
whether to hide them, rewrite captions, or leave them), Form XObjects that
contained text (also stripped, with nesting depth), and leftover_text
(empty on success). Exit 1 when leftover_text is not empty.
"""
import json
import os
import sys
import tempfile

import pikepdf
import pymupdf
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


def _objgen(obj):
    try:
        return obj.objgen
    except Exception:
        return None


def resources_of(page_obj):
    """/Resources of a page, following /Parent inheritance.

    Some producers put /Resources on the /Pages node. pikepdf (QPDF) pushes
    inherited attributes onto the page when it opens a file, so the walk
    below is a safety net for readers that do not; the leftover-text gate
    after save is what actually proves nothing was missed.
    """
    node = page_obj
    seen = set()
    while node is not None:
        res = node.get('/Resources')
        if res is not None:
            return res
        key = _objgen(node)
        if key is not None:
            if key in seen:
                break
            seen.add(key)
        node = node.get('/Parent')
    return None


def strip_xobjects(res, pdf, page_index, report, seen, depth=1):
    """Strip BT..ET from every Form XObject reachable from res, recursively."""
    if res is None:
        return
    xobjs = res.get('/XObject')
    if xobjs is None:
        return
    for name, xo in dict(xobjs).items():
        key = _objgen(xo)
        if key is not None and key != (0, 0):
            if key in seen:
                continue
            seen.add(key)
        if xo.get('/Subtype') != Name('/Form'):
            continue
        xdata, xremoved = strip_ops(xo, pdf)
        if xremoved:
            xo.write(b'q\n' + xdata + b'\nQ\n')
            report['form_xobjects_stripped'].append(
                {'page': page_index, 'xobject': str(name), 'blocks': xremoved,
                 'depth': depth})
        strip_xobjects(xo.get('/Resources'), pdf, page_index, report, seen,
                       depth + 1)


def page_text_without_annots(page):
    """Text of the page CONTENT only: annotation appearance streams excluded.

    get_text() includes widget appearances (captions, field values); those
    are not page text and must not count as leftovers.
    """
    dl = page.get_displaylist(annots=False)
    tp = dl.get_textpage()
    if not isinstance(tp, pymupdf.TextPage):
        tp = pymupdf.TextPage(tp)
    return tp.extractText()


def leftover_page_text(path):
    """[(page_index, snippet)] for every page whose content still has text."""
    doc = pymupdf.open(path)
    out = []
    try:
        for page in doc:
            text = ' '.join(page_text_without_annots(page).split())
            if text:
                out.append((page.number, text[:80]))
    finally:
        doc.close()
    return out


# Invisible-text oracle (goal 14). Real text changes the render when it is
# stripped: glyph ink covers at least ~10% of a span's bbox for any legible
# face. An OCR layer (render mode 3) or text hidden under an image changes
# nothing. 3% leaves headroom; both renders share every non-text pixel, so
# there is no anti-aliasing noise to absorb.
INVISIBLE_TEXT_MAX_CHANGED = 0.03
CHANGED_CHANNEL_DELTA = 16   # per-channel difference that counts as a change
INK_SKIP = 20                # same floor as verify: below this the page is blank


def text_span_area(page):
    """Sum of text-span bbox areas (pt²) from page content, annotations excluded."""
    dl = page.get_displaylist(annots=False)
    tp = dl.get_textpage()
    if not isinstance(tp, pymupdf.TextPage):
        tp = pymupdf.TextPage(tp)
    area = 0.0
    for block in tp.extractDICT().get('blocks', []):
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                if not span.get('text', '').strip():
                    continue
                x0, y0, x1, y1 = span['bbox']
                area += max(0.0, x1 - x0) * max(0.0, y1 - y0)
    return area


def _changed_pixels(a, b, n, delta=CHANGED_CHANNEL_DELTA):
    """Approximate number of pixels whose colour differs between two renders."""
    changed = sum(1 for x, y in zip(a, b) if abs(x - y) > delta)
    return changed / max(n, 1)


def invisible_text_pages(src):
    """[(page_index, changed_fraction)] for pages whose text is not what the reader sees.

    Strips a temporary copy and compares 72-dpi renders. If removing the
    text changes fewer than INVISIBLE_TEXT_MAX_CHANGED of the page's
    text-span area (in pixels), the text was invisible: an OCR layer over a
    scanned image, or text hidden under an image. Pages with negligible ink
    are skipped (a pale blank page is not a scan). If strip itself refuses
    the file, nothing is judged; that refusal already blocks the pipeline.
    """
    with tempfile.TemporaryDirectory() as tmp:
        stripped = os.path.join(tmp, 'stripped.pdf')
        report = strip_text(src, stripped)
        if report['leftover_text'] or not os.path.isfile(stripped):
            return []
        o, s = pymupdf.open(src), pymupdf.open(stripped)
        out = []
        try:
            for i in range(min(len(o), len(s))):
                area = text_span_area(o[i])
                if area <= 0:
                    continue
                po, ps = o[i].get_pixmap(dpi=72), s[i].get_pixmap(dpi=72)
                if (po.width, po.height, po.n) != (ps.width, ps.height, ps.n):
                    continue
                bo, bs = bytes(po.samples), bytes(ps.samples)
                dark = sum(1 for k in range(0, len(bo), po.n) if bo[k] < 100)
                if dark < INK_SKIP:
                    continue
                fraction = _changed_pixels(bo, bs, po.n) / area
                if fraction < INVISIBLE_TEXT_MAX_CHANGED:
                    out.append((i, round(fraction, 4)))
        finally:
            o.close()
            s.close()
        return out


def strip_text(src, dst, hide_buttons=None, captions=None):
    """Strip page text, wrap content in q/Q, remove XFA. Returns a report dict.

    hide_buttons: iterable of field names (base name, without [0] suffix).
    captions: dict of field name -> new /MK /CA caption (in-place rewrite).

    report['leftover_text'] lists pages whose content still had text after
    stripping (annotation appearances excluded). When it is not empty the
    output file is deleted: never hand retypeset a stripped file that still
    carries source text.
    """
    hide = set(hide_buttons or [])
    captions = captions or {}

    pdf = pikepdf.open(src)
    report = {'xfa_removed': False, 'pages': [], 'dead_buttons': [],
              'form_xobjects_stripped': [], 'hidden': [],
              'rewritten_captions': [], 'leftover_text': []}

    acro = pdf.Root.get('/AcroForm')
    if acro is not None and '/XFA' in acro:
        del acro.XFA
        report['xfa_removed'] = True

    seen_xobjects = set()
    for i, page in enumerate(pdf.pages):
        data, removed = strip_ops(page, pdf)
        page.Contents = pdf.make_stream(b'q\n' + data + b'\nQ\n')
        report['pages'].append({'page': i, 'text_blocks_removed': removed})
        strip_xobjects(resources_of(page.obj), pdf, i, report, seen_xobjects)
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

    leftover = leftover_page_text(dst)
    report['leftover_text'] = [{'page': p, 'text': t} for p, t in leftover]
    if leftover:
        try:
            os.remove(dst)
        except OSError:
            pass
    return report


def _say(line):
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode('ascii', 'backslashreplace').decode('ascii'))


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
    _say(json.dumps(report, indent=2, ensure_ascii=False))
    if report['leftover_text']:
        _say(f"FAIL: page text survived strip on {len(report['leftover_text'])} "
             f"page(s); {dst} was not written. Text hiding somewhere the "
             f"walker did not reach:")
        for item in report['leftover_text']:
            _say(f"  p{item['page']}: {item['text']}")
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
