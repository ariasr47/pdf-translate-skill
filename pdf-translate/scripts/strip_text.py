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
                                       [--widget-text widget_text.json]

--captions rewrites pushbutton /MK /CA strings in place (field count stays
exact). --hide-buttons sets the Hidden flag instead. Prefer captions when
the widget should remain as the UI chrome.

--widget-text rewrites the text that lives in the annotation dictionaries
and never reaches a content stream: /TU tooltips, choice /Opt display
strings and text-field /V /DV defaults. Export values are preserved (an
/Opt entry becomes [export, display]); a spec that would translate a
choice /V is refused, not ignored. extract_segments.py writes the
scaffold. Exit 2 on a mapping that is unauthored or wrong.

Prints a JSON report to stdout: pages processed, XFA removed or not,
pushbuttons that have no /A action (dead if XFA was removed — decide
whether to hide them, rewrite captions, or leave them), Form XObjects that
contained text (also stripped, with nesting depth), rewritten widget text,
and leftover_text (empty on success). Exit 1 when leftover_text is not
empty.
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


def page_textdict_without_annots(page):
    """get_text('dict') of the page CONTENT only: annotation appearances out.

    Same shape as page.get_text('dict'), minus the widget appearance
    streams. A text field's default value and a combo box's current choice
    are drawn by the widget, not by the page; letting them into extraction
    puts them in to_translate.json, where the author translates them and
    retypeset draws the translation *under* a widget that still shows the
    source value.
    """
    dl = page.get_displaylist(annots=False)
    tp = dl.get_textpage()
    if not isinstance(tp, pymupdf.TextPage):
        tp = pymupdf.TextPage(tp)
    return tp.extractDICT()


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


# ---------------------------------------------------------------- widget text
# Widget text is not page text. /TU tooltips, /Opt choice labels and text
# /V /DV defaults live in the annotation dictionaries, never reach the
# content stream, and so are invisible to strip-and-retypeset. Without this
# channel a "fully translated" form still shows English on every hover and
# in every dropdown. Export values must survive: a choice /Opt entry becomes
# [export, display] so scripts, /V and submitted data keep working.


class WidgetTextError(Exception):
    """A widget-text mapping that cannot be applied honestly."""


def _target_of(spec, what, field):
    """Author's target string from a scaffold entry or a bare string."""
    if spec is None:
        return None
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        if 'target' not in spec:
            raise WidgetTextError(
                f'{field}: {what} entry has no "target" key')
        target = spec['target']
        if target is None:
            raise WidgetTextError(
                f'{field}: {what} target is null — author it, or delete the '
                f'key to leave the source text in place')
        if not str(target).strip():
            raise WidgetTextError(f'{field}: {what} target is empty')
        return str(target)
    raise WidgetTextError(f'{field}: {what} must be a string or an object')


def _option_pairs(spec, field):
    """[(export, target)] from either scaffold list or {export: display} dict."""
    pairs = []
    if isinstance(spec, dict):
        for export, target in spec.items():
            if target is None:
                raise WidgetTextError(
                    f'{field}: option "{export}" target is null — author it, '
                    f'or delete the key')
            pairs.append((str(export), str(target)))
        return pairs
    if isinstance(spec, list):
        for item in spec:
            if not isinstance(item, dict) or 'export' not in item:
                raise WidgetTextError(
                    f'{field}: each option needs an "export" key')
            pairs.append((str(item['export']),
                          _target_of(item, f'option {item["export"]}', field)))
        return pairs
    raise WidgetTextError(f'{field}: options must be an object or a list')


def _opt_export(entry):
    """Export value of one /Opt entry (string, or [export, display])."""
    if isinstance(entry, pikepdf.Array) or isinstance(entry, list):
        return str(entry[0]) if len(entry) else ''
    return str(entry)


def opt_exports(annot):
    """Ordered export values of a choice widget's /Opt, or None."""
    opt = annot.get('/Opt')
    if opt is None:
        return None
    return [_opt_export(e) for e in opt]


WIDGET_TEXT_KEYS = {'type', 'tooltip', 'options', 'value', 'default'}


def _pdf_str(obj):
    return str(obj) if obj is not None else None


def widget_text_scaffold(src):
    """{field: {...}} of every translatable annotation string in a PDF.

    Values are {"source": ..., "target": null} so the author can see what
    the string is and strip_text can tell "not authored yet" from "left in
    the source language on purpose" (delete the key for that). Pushbutton
    captions are the --captions channel and are not repeated here.
    """
    out = {}
    pdf = pikepdf.open(src)
    try:
        for page in pdf.pages:
            for a in page.get('/Annots', []):
                ft = a.get('/FT')
                if ft is None:
                    continue
                name = str(a.get('/T', ''))
                if not name or name in out:
                    continue
                is_push = (ft == Name('/Btn')
                           and int(a.get('/Ff', 0) or 0) & (1 << 16))
                if is_push:
                    continue
                entry = {'type': str(ft)}
                tu = _pdf_str(a.get('/TU'))
                if tu and tu.strip():
                    entry['tooltip'] = {'source': tu, 'target': None}
                if ft == Name('/Ch'):
                    exports = opt_exports(a) or []
                    options = []
                    for export, raw in zip(exports, a.get('/Opt', [])):
                        display = (str(raw[1]) if (isinstance(raw, pikepdf.Array)
                                                   and len(raw) > 1)
                                   else export)
                        options.append({'export': export, 'source': display,
                                        'target': None})
                    if options:
                        entry['options'] = options
                elif ft == Name('/Tx'):
                    for key, pdfkey in (('value', '/V'), ('default', '/DV')):
                        val = _pdf_str(a.get(pdfkey))
                        if val and val.strip():
                            entry[key] = {'source': val, 'target': None}
                if len(entry) > 1:
                    out[name] = entry
    finally:
        pdf.close()
    return out


def choice_exports(path):
    """{field name: [export values]} for every choice widget in a PDF.

    The export value is what a viewer submits and what /V holds; translating
    a dropdown must change only the display half of each /Opt entry. This is
    what verify's /Opt parity gate compares.
    """
    out = {}
    pdf = pikepdf.open(path)
    try:
        for page in pdf.pages:
            for a in page.get('/Annots', []):
                if a.get('/FT') != Name('/Ch'):
                    continue
                name = str(a.get('/T', ''))
                exports = opt_exports(a)
                if name and exports is not None:
                    out[name] = exports
    finally:
        pdf.close()
    return out


def apply_widget_text(annot, spec, field, report):
    """Rewrite /TU, /Opt display halves and text /V /DV from one spec.

    Choice /V and /DV are export values once /Opt carries [export, display]
    pairs; translating them would break the submitted data, so a spec that
    asks for it is refused rather than quietly ignored.
    """
    if not isinstance(spec, dict):
        raise WidgetTextError(f'{field}: widget-text entry must be an object')
    unknown = sorted(set(spec) - WIDGET_TEXT_KEYS)
    if unknown:
        raise WidgetTextError(
            f'{field}: unknown widget-text keys {unknown} (expected '
            f'{sorted(WIDGET_TEXT_KEYS)})')
    changed = []
    is_choice = annot.get('/FT') == Name('/Ch')

    tooltip = _target_of(spec.get('tooltip'), 'tooltip', field)
    if tooltip is not None:
        annot.TU = pikepdf.String(tooltip)
        changed.append('tooltip')

    if 'options' in spec:
        if not is_choice:
            raise WidgetTextError(f'{field}: options on a non-choice field')
        exports = opt_exports(annot)
        if exports is None:
            raise WidgetTextError(f'{field}: field has no /Opt to translate')
        pairs = dict(_option_pairs(spec['options'], field))
        unknown = [e for e in pairs if e not in exports]
        if unknown:
            raise WidgetTextError(
                f'{field}: options {unknown} are not export values of this '
                f'field ({exports})')
        rebuilt = []
        for entry, export in zip(annot.Opt, exports):
            display = pairs.get(export)
            if display is None:
                rebuilt.append(entry)
                continue
            rebuilt.append(pikepdf.Array([pikepdf.String(export),
                                          pikepdf.String(display)]))
        annot.Opt = pikepdf.Array(rebuilt)
        changed.append('options')

    for key, pdfkey in (('value', '/V'), ('default', '/DV')):
        if key not in spec:
            continue
        if is_choice:
            raise WidgetTextError(
                f'{field}: {key} on a choice field is an export value; '
                f'translate "options" instead and leave {pdfkey} alone')
        target = _target_of(spec[key], key, field)
        if target is None:
            continue
        annot[Name(pdfkey)] = pikepdf.String(target)
        changed.append(key)

    if changed and '/AP' in annot:
        # Same reason as captions: a stale appearance keeps drawing the
        # source string on top of the value we just rewrote.
        del annot.AP
    if changed:
        report['rewritten_widget_text'].append(
            {'name': field, 'changed': changed})
    return bool(changed)


def strip_text(src, dst, hide_buttons=None, captions=None, widget_text=None):
    """Strip page text, wrap content in q/Q, remove XFA. Returns a report dict.

    hide_buttons: iterable of field names (base name, without [0] suffix).
    captions: dict of field name -> new /MK /CA caption (in-place rewrite).
    widget_text: dict of field name -> {tooltip, options, value, default}
        (see apply_widget_text). Rewrites annotation text that never
        reaches the content stream. Raises WidgetTextError on a mapping
        that is unauthored (null target) or would break export values.

    report['leftover_text'] lists pages whose content still had text after
    stripping (annotation appearances excluded). When it is not empty the
    output file is deleted: never hand retypeset a stripped file that still
    carries source text.
    """
    hide = set(hide_buttons or [])
    captions = captions or {}
    widget_text = widget_text or {}

    pdf = pikepdf.open(src)
    report = {'xfa_removed': False, 'pages': [], 'dead_buttons': [],
              'form_xobjects_stripped': [], 'hidden': [],
              'rewritten_captions': [], 'rewritten_widget_text': [],
              'leftover_text': []}

    acro = pdf.Root.get('/AcroForm')
    if acro is not None and '/XFA' in acro:
        del acro.XFA
        report['xfa_removed'] = True

    seen_xobjects = set()
    seen_widget_text = set()
    for i, page in enumerate(pdf.pages):
        data, removed = strip_ops(page, pdf)
        page.Contents = pdf.make_stream(b'q\n' + data + b'\nQ\n')
        report['pages'].append({'page': i, 'text_blocks_removed': removed})
        strip_xobjects(resources_of(page.obj), pdf, i, report, seen_xobjects)
        for a in page.get('/Annots', []):
            t = str(a.get('/T', ''))
            base = _field_base(t)
            spec_key = (t if t in widget_text
                        else (base if base in widget_text else None))
            if spec_key is not None:
                if apply_widget_text(a, widget_text[spec_key], t, report):
                    seen_widget_text.add(spec_key)
            if a.get('/FT') != Name('/Btn'):
                continue
            ff = int(a.get('/Ff', 0) or 0)
            if not (ff & (1 << 16)):  # pushbutton flag
                continue
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

    unknown = sorted(set(widget_text) - seen_widget_text)
    if unknown:
        pdf.close()
        raise WidgetTextError(
            f'widget-text mapping names fields this PDF does not have: '
            f'{unknown}')
    if report['rewritten_widget_text']:
        # The appearances we dropped have to be rebuilt by the viewer.
        if acro is None:
            pdf.Root.AcroForm = pdf.make_indirect(pikepdf.Dictionary())
            acro = pdf.Root.AcroForm
        acro.NeedAppearances = True

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
    widget_text = None
    if '--widget-text' in argv:
        with open(argv[argv.index('--widget-text') + 1], encoding='utf-8') as f:
            widget_text = json.load(f)
    try:
        report = strip_text(src, dst, hide_buttons=hide, captions=captions,
                            widget_text=widget_text)
    except WidgetTextError as exc:
        _say(f'FAIL widget text: {exc}')
        return 2
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
