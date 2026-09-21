"""Conservative drawing-state checks omitted by MuPDF's text trace.

Text traces identify glyphs and origins but cannot prove that a clipping path,
affine shear or later paint left the glyph visible in its original shape.
"""
from dataclasses import dataclass
import math

import pikepdf
import pymupdf


IDENTITY = (1., 0., 0., 1., 0., 0.)


@dataclass(frozen=True)
class ContentIssue:
    page: int
    kind: str
    detail: str


@dataclass(frozen=True)
class ContentInspection:
    issues: tuple
    drawn_fonts: dict


def _compose(left, right):
    a, b, c, d, e, f = left
    g, h, i, j, k, l = right
    return (a*g + c*h, b*g + d*h, a*i + c*j, b*i + d*j,
            a*k + c*l + e, b*k + d*l + f)


def page_drawing(document, index):
    """Return page-only glyphs and all paint, including annotation appearances.

    MuPDF text traces include widget values and comments, unlike extraction.
    Suppress annotations only in memory, reload its cached page, and restore
    them before returning. No input file is saved. Validate the drawing-order
    prefix before using page glyph sequence numbers against the complete log.
    """
    page = document[index]
    paints = page.get_bboxlog()
    kind, value = document.xref_get_key(page.xref, 'Annots')
    if kind == 'null':
        return page.get_texttrace(), paints, len(paints)
    xref = page.xref
    try:
        document.xref_set_key(xref, 'Annots', 'null')
        page = document.reload_page(page)
        page_paints = page.get_bboxlog()
        traces = page.get_texttrace()
    finally:
        document.xref_set_key(xref, 'Annots', value)
        document.reload_page(page)
    if paints[:len(page_paints)] != page_paints:
        raise ValueError('Cannot resolve page and annotation drawing order.')
    return traces, paints, len(page_paints)


def later_paint_intersects(paints, sequence, box, annotation_start=None):
    if not isinstance(sequence, int) or not 0 <= sequence < len(paints):
        return True  # Unknown drawing order cannot establish visibility.
    return any((kind in ('fill-path', 'stroke-path', 'fill-image', 'fill-shade') or
                (annotation_start is not None and index >= annotation_start and
                 kind in ('fill-text', 'stroke-text'))) and
               pymupdf.Rect(bounds).intersects(box)
               for index, (kind, bounds, *_) in enumerate(paints[sequence + 1:], sequence + 1))


def inspect_content(path, *, source=False):
    """Name unsupported text drawing state; graphics-only state is irrelevant.

    Arbitrary clipping (including Form bounds) stays cannot-attest. We do not
    pretend a bounding rectangle proves containment in an arbitrary clip path.
    """
    issues, drawn_fonts = [], {}
    def record(page, kind, detail):
        issue = ContentIssue(page, kind, detail)
        if issue not in issues:
            issues.append(issue)

    def walk(stream, resources, initial, page, ancestors=()):
        state, saved = dict(initial), []
        for instruction in pikepdf.parse_content_stream(stream):
            if not isinstance(instruction, pikepdf.ContentStreamInstruction):
                continue  # Inline image; its paint order is inspected separately.
            values, op = instruction.operands, str(instruction.operator)
            if op == 'q':
                saved.append(dict(state))
            elif op == 'Q':
                if not saved:
                    raise ValueError('unbalanced graphics state')
                state = saved.pop()
            elif op == 'cm':
                state['ctm'] = _compose(state['ctm'], tuple(map(float, values)))
            elif op == 'BT':
                state['text'] = IDENTITY
            elif op == 'Tm':
                state['text'] = tuple(map(float, values))
            elif op == 'Tf':
                font = resources.get('/Font', {}).get(values[0])
                if font is None or not font.objgen[0]:
                    raise ValueError('unresolved text font resource')
                state['font'] = font.objgen[0]
            elif op == 'Tz':
                state['horizontal'] = float(values[0]) / 100
            elif op == 'Tr':
                state['mode'] = int(values[0])
            elif op in ('W', 'W*'):
                state['clip'] = True
            elif op == 'gs':
                gs = resources.get('/ExtGState', {}).get(values[0])
                if gs is None:
                    raise ValueError('unresolved graphics state resource')
                for pdf_key, key in (('/ca', 'fill_alpha'), ('/CA', 'stroke_alpha')):
                    if pdf_key in gs:
                        state[key] = float(gs[pdf_key])
                if '/BM' in gs:
                    state['blend'] = str(gs['/BM'])
                if '/SMask' in gs:
                    state['mask'] = str(gs['/SMask']) != '/None'
            elif op == 'Do':
                obj = resources.get('/XObject', {}).get(values[0])
                if obj is None:
                    raise ValueError('unresolved XObject')
                if str(obj.get('/Subtype')) == '/Form':
                    if obj.objgen in ancestors or len(ancestors) >= 20:
                        raise ValueError('recursive Form XObject')
                    child = dict(state)
                    child['ctm'] = _compose(state['ctm'], tuple(map(float, obj.get('/Matrix', IDENTITY))))
                    child['clip'] = True  # A Form's BBox imposes an implicit clip.
                    walk(obj, obj.get('/Resources', resources), child, page, ancestors + (obj.objgen,))
            elif op in ('Tj', 'TJ', "'", '"'):
                if state['font'] is None:
                    raise ValueError('text has no selected font resource')
                drawn_fonts.setdefault(page, set()).add(state['font'])
                transform = _compose(state['ctm'], state['text'])
                a, b, c, d, _, _ = transform
                a, b = a * state['horizontal'], b * state['horizontal']
                if (not all(math.isfinite(x) for x in transform) or a <= 0 or d <= 0 or
                        abs(b) > 1e-7 or abs(c) > 1e-7 or abs(a - d) > 1e-7):
                    record(page, 'transformed-text', 'Text uses shear, rotation or nonuniform scaling.')
                if state['clip'] or state['mode'] >= 4:
                    record(page, 'clipped-text', 'Text is subject to a clipping path or Form bounds.')
                if (state['mode'] != 0 or state['fill_alpha'] != 1 or state['stroke_alpha'] != 1 or
                        state['blend'] not in ('/Normal', '/Compatible') or state['mask']):
                    record(page, 'unsupported-text-paint', 'Text uses stroke, transparency, soft mask or nonstandard blending.')

    with pikepdf.open(path) as doc:
        for index, page in enumerate(doc.pages):
            if source and page.get('/UserUnit', 1) != 1:
                record(index, 'unsupported-page-units', 'Nondefault page UserUnit is outside the first typography scope.')
            initial = {'ctm': IDENTITY, 'text': IDENTITY, 'horizontal': 1., 'mode': 0,
                       'clip': False, 'fill_alpha': 1., 'stroke_alpha': 1., 'blend': '/Normal', 'mask': False, 'font': None}
            try:
                walk(page, page.get('/Resources', {}), initial, index)
            except (pikepdf.PdfError, ValueError, TypeError, KeyError, RuntimeError) as exc:
                record(index, 'unreadable-content', f'Cannot resolve text drawing state: {type(exc).__name__}.')
    if source:
        with pymupdf.open(path) as doc:
            for index in range(doc.page_count):
                try:
                    traces, paints, annotation_start = page_drawing(doc, index)
                except (ValueError, RuntimeError):
                    record(index, 'unreadable-content', 'Cannot resolve page and annotation drawing order.')
                    continue
                for span in traces:
                    if any(later_paint_intersects(paints, span.get('seqno'), pymupdf.Rect(char[3]), annotation_start)
                           for char in span['chars'] if char[0] > 32):
                        record(index, 'occluded-text', 'Later page or annotation paint may cover source glyphs.')
    return ContentInspection(tuple(issues), drawn_fonts)
