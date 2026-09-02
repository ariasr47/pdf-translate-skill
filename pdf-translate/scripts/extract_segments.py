#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 2 of pdf-translate: extract translatable segments from the ORIGINAL PDF.

Reads text with exact geometry and writes two files:

  segments.json     every placeable segment: page, bbox, baseline origin,
                    font size, bold/italic, raw text, parsed marker / core /
                    dot-leader info. retypeset.py consumes this.
  to_translate.json unique normalized "core" strings that need translation,
                    with occurrence counts. Author translations for ALL of
                    these (pass-through items are pre-filtered out).
  widget_text.json  the translatable strings that live in annotation
                    dictionaries and never reach a content stream: /TU
                    tooltips, choice /Opt display labels, text-field /V and
                    /DV defaults. Author the "target" of each, then pass the
                    file to strip_text.py --widget-text. Empty object when
                    the PDF has none.

segments.json also carries a "document" block: the source /Lang, /Title and
the outline (bookmark) titles. The title and the outline entries are added
to to_translate.json as cores, because the window caption, the bookmarks
pane and every screen reader read them.

Page text is read from an annotation-free display list. get_text() includes
widget appearance streams, so a text field's default value and a combo
box's current choice would otherwise arrive as page text: the author
translates them, retypeset draws the translation on the page, and the
widget keeps drawing the source value on top of it.

Segmentation rules (why they matter):
- A visual line is split at horizontal gaps > GAP pt between spans: one line
  often holds several independent cells (CITY: STATE: ZIP:) or a label and a
  dot-leader run separated by a checkbox gap. Each piece is placed on its own.
- The line's direction vector is recorded per segment ("dir"). Rotated
  lines (side labels, stamps) keep their angle at re-typeset time; a
  rotated line is never gap-split, because the x distance between its
  spans is not a horizontal gap.
- List markers (a., (1), 12.) are peeled off and kept verbatim.
- Trailing dot leaders + optional currency symbol are peeled off; retypeset
  refills dots anchored to the right so they never invade mid-line gaps.
- Segments whose core is empty or purely numbers/symbols are pass-through
  (re-inserted verbatim) and excluded from to_translate.json.
- Segments containing a run of >= 6 spaces INSIDE one span are flagged in
  "warnings": they usually hide a mid-line gap (checkboxes between phrases)
  that gap-splitting cannot see. Handle each with an "overrides" entry in
  translations.json rather than a plain translation.
- Write/find/say candidates (quoted strings, form/document names, URLs,
  emails) are flagged for confirmation — they often must stay verbatim.
- Consecutive same-column lines that look like a wrapped paragraph are
  flagged as merge *candidates*. Never auto-merged; declare each merge
  explicitly in translations.json.
- Segments that share a right edge while their left edges differ are
  flagged "right-aligned": a longer translation anchored at the left grows
  past the edge it was tucked against. The author lists those cores in
  "right"; nothing is realigned automatically.
- Three or more stacked cores sharing a skinny column (same left edge,
  bbox under 90 pt wide) are flagged "narrow-column": a pay-stub box or
  label stack, where translating each line-break on its own turns the
  box to crumbs. Warn only — never merged, and no verify gate.
- A page whose text is invisible (an OCR layer over a scanned image, or
  text hidden under an image) is refused: the words the reader sees are
  pixels, and retypeset would print the translation over them. The
  script exits non-zero and names the pages (kind: invisible-text).

Usage:
  python3 extract_segments.py ORIGINAL.pdf [--gap 12] [--outdir .]
"""
import json
import os
import re
import sys

import pymupdf

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
from strip_text import (  # noqa: E402
    invisible_text_pages, page_textdict_without_annots,
    widget_text_scaffold)

MARKER = re.compile(
    r'^\s*(\(?[a-z]\.|\([a-z0-9]{1,3}\)|\d{1,2}\.)\s+'
    r'|^\s*(\(?[a-z]\.|\([a-z0-9]{1,3}\)|\d{1,2}\.)$')
DOTS = re.compile(r'^(.*?)([.…]{3,})(\s*[$€£¥]?\s*)$')
# Pass-through ONLY when the core contains no letters at all. An earlier
# version also passed any string of <=4 chars, which silently shipped short
# words ("may", "or", "Yes") in the source language — a defect no gate
# catches. Short real words must appear in to_translate.json; if a token
# genuinely should stay verbatim (a form number like "FL-150"), map it to
# itself in translations.json so the decision is explicit and reviewable.
PASS = re.compile(r'^[^\w]*$|^[\d\s.,:;$€£¥%–—\-()/§*+=&#\'"°]*$', re.UNICODE)
INNER_GAP = re.compile(r'\S(\s{6,})\S')
# A page with this many dark pixels (72 dpi, channel < 100) counts as
# "has visible ink" even if get_text() is empty — the scanned-PDF case.
VISIBLE_INK = 50


def page_has_visible_content(page):
    """True if the page has an image or enough ink to not be blank."""
    if page.get_images():
        return True
    pix = page.get_pixmap(dpi=72)
    buf = bytes(pix.samples)
    dark = sum(1 for k in range(0, len(buf), pix.n) if buf[k] < 100)
    return dark >= VISIBLE_INK
# Write/find/say candidates: the reader may have to write, hand over, or
# search for these. Flag them; do not auto-passthrough (that decision is
# the mapping author's).
QUOTED = re.compile(r'[“"]([^”"]{3,80})[”"]')
FORM_NAME = re.compile(
    r'\b(?:Form|Schedule|Attachment|Exhibit)\s+[A-Z0-9][-A-Z0-9./]*\b')
URL_EMAIL = re.compile(
    r'https?://[^\s]+|\b[\w.+-]+@[\w.-]+\.\w{2,}\b', re.IGNORECASE)


def write_find_say_hits(text):
    """Return (kind, snippet) pairs that usually must stay verbatim."""
    hits = []
    for m in QUOTED.finditer(text):
        hits.append(('quoted', m.group(1)))
    for m in FORM_NAME.finditer(text):
        hits.append(('form-name', m.group(0)))
    for m in URL_EMAIL.finditer(text):
        hits.append(('url-or-email', m.group(0)))
    return hits


def merge_candidate_warnings(segments):
    """Suggest wrapped-paragraph merges. Never apply them automatically."""
    warnings = []
    by_page = {}
    for s in segments:
        if s['passthrough']:
            continue
        by_page.setdefault(s['page'], []).append(s)
    ender = re.compile(r'[.!?…:;]$')
    for page, segs in by_page.items():
        segs = sorted(segs, key=lambda s: (s['origin'][1], s['origin'][0]))
        run = []
        def flush():
            if len(run) >= 2:
                warnings.append({
                    'page': page,
                    'ids': [s['id'] for s in run],
                    'why': 'possible wrapped paragraph — declare a merge in '
                           'translations.json if these lines are one unit; '
                           'do not auto-merge (sibling list items share x)',
                    'lines': [s['text'].strip() for s in run],
                })
        for s in segs:
            if not run:
                run = [s]
                continue
            prev = run[-1]
            same_col = abs(s['origin'][0] - prev['origin'][0]) < 4
            dy = s['origin'][1] - prev['origin'][1]
            stacked = 0.5 < dy < max(prev['size'], s['size']) * 2.2
            prev_open = not ender.search(prev['core'].rstrip())
            if same_col and stacked and prev_open:
                run.append(s)
            else:
                flush()
                run = [s]
        flush()
    return warnings


NARROW_WIDTH = 90.0
NARROW_RUN = 3


def narrow_column_warnings(segments):
    """Warn on >=3 stacked short cores in a skinny column. Never merge them.

    Pay-stub boxes and label stacks are many one-word cores at the same x
    with a bbox about one word wide. merge_candidate_warnings only fires on
    *open sentences*, so a stack of short labels never trips it and the
    author translates each fragment independently -- the box turns to
    crumbs. Warn; the author decides whether one override with a max_width
    is right. Merging by geometry would swallow sibling list items, which
    is why this stays a warning.
    """
    warnings = []
    by_page = {}
    for s in segments:
        if s['passthrough']:
            continue
        if s['bbox'][2] - s['bbox'][0] >= NARROW_WIDTH:
            continue
        by_page.setdefault(s['page'], []).append(s)
    for page, segs in sorted(by_page.items()):
        segs = sorted(segs, key=lambda s: (s['bbox'][0], s['origin'][1]))
        run = []

        def flush():
            if len(run) >= NARROW_RUN:
                warnings.append({
                    'page': page,
                    'kind': 'narrow-column',
                    'ids': [s['id'] for s in run],
                    'width': round(max(s['bbox'][2] - s['bbox'][0]
                                       for s in run), 2),
                    'why': 'stacked cores share a column narrower than '
                           f'{NARROW_WIDTH:g} pt; translating each line on '
                           'its own breaks the box. Consider one merge, or '
                           'one override with max_width. Not auto-merged',
                    'lines': [s['core'] for s in run],
                })

        for s in segs:
            if not run:
                run = [s]
                continue
            prev = run[-1]
            same_col = abs(s['bbox'][0] - run[0]['bbox'][0]) < 4
            dy = s['origin'][1] - prev['origin'][1]
            stacked = 0.5 < dy < max(prev['size'], s['size']) * 2.2
            if same_col and stacked:
                run.append(s)
            else:
                flush()
                run = [s]
        flush()
    return warnings


def _catalog_key(doc, key):
    """(type, value) of a catalog key, or ('null', '') when absent."""
    try:
        cat = doc.pdf_catalog()
        if not cat:
            return 'null', ''
        kind, val = doc.xref_get_key(cat, key)
        return kind, val
    except Exception:
        return 'null', ''


def _is_marked(doc):
    kind, val = _catalog_key(doc, 'MarkInfo')
    return kind != 'null' and 'Marked' in str(val) and 'true' in str(val)


def _has_struct_tree(doc):
    kind, _ = _catalog_key(doc, 'StructTreeRoot')
    return kind != 'null'


def document_strings(src):
    """Document-level translatable text: /Lang, /Title and outline titles.

    None of this is page text, so strip-and-retypeset never touches it: an
    output keeps the English /Title in the window caption, the source
    /Lang for screen readers and hyphenation, and an untranslated
    bookmark tree. All three are visible to the reader and to assistive
    technology.
    """
    doc = pymupdf.open(src)
    try:
        meta = doc.metadata or {}
        try:
            lang = doc.language or ''
        except Exception:
            lang = ''
        toc = []
        for entry in doc.get_toc(simple=True) or []:
            if len(entry) >= 2 and str(entry[1]).strip():
                toc.append(str(entry[1]))
        return {
            'lang': lang,
            'title': (meta.get('title') or '').strip(),
            'subject': (meta.get('subject') or '').strip(),
            'keywords': (meta.get('keywords') or '').strip(),
            'outline': toc,
            'marked': _is_marked(doc),
            'struct_tree': _has_struct_tree(doc),
        }
    finally:
        doc.close()


RIGHT_EDGE_TOL = 1.5
RIGHT_LEFT_SPREAD = 4.0


def right_alignment_warnings(segments):
    """Propose cores that look right-aligned. Never applied automatically.

    Only `center` existed, so a right-aligned label grew rightward past its
    original right edge: "Total" at x1 540 became "Gesamt" ending at 555.3,
    over the rule it was tucked against. Segments that share a right edge
    while their left edges differ are a right-aligned column; the author
    puts those cores in "right".
    """
    warnings = []
    by_page = {}
    for s in segments:
        if s['passthrough']:
            continue
        by_page.setdefault(s['page'], []).append(s)
    for page, segs in sorted(by_page.items()):
        buckets = {}
        for s in segs:
            buckets.setdefault(round(s['bbox'][2] / RIGHT_EDGE_TOL), []).append(s)
        for _, group in sorted(buckets.items()):
            if len(group) < 2:
                continue
            lefts = [s['bbox'][0] for s in group]
            if max(lefts) - min(lefts) <= RIGHT_LEFT_SPREAD:
                continue
            warnings.append({
                'page': page,
                'kind': 'right-aligned',
                'ids': [s['id'] for s in group],
                'right_edge': round(max(s['bbox'][2] for s in group), 2),
                'why': 'these share a right edge but not a left one, so they '
                       'are right-aligned. A longer translation anchored left '
                       'grows past that edge — list these cores in "right"',
                'lines': [s['core'] for s in group],
            })
    return warnings


def extract_segments(src, outdir='.', gap=12.0):
    """Extract geometry + unique cores. Writes segments.json and to_translate.json."""
    os.makedirs(outdir, exist_ok=True)
    doc = pymupdf.open(src)
    segments, warnings = [], []
    sid = 0
    for pno, page in enumerate(doc):
        for b in page_textdict_without_annots(page)['blocks']:
            if b['type'] != 0:
                continue
            for line in b['lines']:
                # Line direction as a unit vector, (1, 0) for ordinary rows.
                # Gap-splitting is a horizontal idea: on a rotated line the
                # x distance between spans means nothing, so a rotated line
                # stays one group.
                ldir = tuple(line.get('dir') or (1.0, 0.0))[:2]
                if len(ldir) != 2:
                    ldir = (1.0, 0.0)
                rotated = abs(ldir[0] - 1.0) > 1e-6 or abs(ldir[1]) > 1e-6
                groups = []
                for s in line['spans']:
                    if not s['text'].strip() and not groups:
                        continue
                    if groups and (rotated
                                   or s['bbox'][0] - groups[-1]['bbox'][2] < gap):
                        g = groups[-1]
                        g['text'] += s['text']
                        g['bbox'] = [g['bbox'][0],
                                     min(g['bbox'][1], s['bbox'][1]),
                                     max(g['bbox'][2], s['bbox'][2]),
                                     max(g['bbox'][3], s['bbox'][3])]
                        g['bold'] = g['bold'] or ('Bold' in s['font'])
                        g['italic'] = g['italic'] or (
                            'Italic' in s['font'] or 'Oblique' in s['font'])
                    else:
                        groups.append({
                            'text': s['text'],
                            'bbox': list(s['bbox']),
                            'origin': [s['origin'][0], s['origin'][1]],
                            'size': s['size'],
                            'color': s.get('color', 0),
                            'bold': 'Bold' in s['font'],
                            'italic': ('Italic' in s['font']
                                       or 'Oblique' in s['font']),
                            'dir': [round(ldir[0], 4), round(ldir[1], 4)],
                        })
                for g in groups:
                    if not g['text'].strip():
                        continue
                    text = g['text'].strip()
                    m = MARKER.match(text)
                    marker, core = '', text
                    if m:
                        marker = m.group(0).strip()
                        core = text[m.end():].strip()
                    dm = DOTS.match(core)
                    dots, tail = None, ''
                    if dm:
                        core, dots, tail = (
                            dm.group(1).strip(), dm.group(2), dm.group(3).strip())
                    seg = {
                        'id': sid, 'page': pno,
                        'bbox': [round(v, 2) for v in g['bbox']],
                        'origin': [round(g['origin'][0], 2),
                                   round(g['origin'][1], 2)],
                        'size': round(g['size'], 2),
                        # sRGB int; retypeset re-applies it. Losing this is
                        # how white-on-dark headings turn black-on-dark —
                        # a defect the ink-density gate cannot see.
                        'color': int(g.get('color', 0)),
                        'bold': g['bold'], 'italic': g['italic'],
                        # Line direction: retypeset rotates the run about
                        # this origin. Without it a 90-degree side label is
                        # re-typeset flat across the page.
                        'dir': g.get('dir', [1.0, 0.0]),
                        'text': g['text'], 'marker': marker, 'core': core,
                        'dots': dots or '', 'tail': tail,
                        'passthrough': bool(not core or PASS.match(core)),
                    }
                    if INNER_GAP.search(g['text']):
                        warnings.append({
                            'id': sid, 'page': pno,
                            'kind': 'inner-gap',
                            'text': g['text'][:80],
                            'why': 'run of >=6 spaces inside one span; '
                                   'likely a mid-line gap — use an override',
                        })
                    for kind, snippet in write_find_say_hits(g['text']):
                        warnings.append({
                            'id': sid, 'page': pno,
                            'kind': 'write-find-say',
                            'hit': kind,
                            'text': snippet,
                            'why': 'write/find/say candidate — confirm before '
                                   'translating (reader may have to write, '
                                   'hand over, or search for this)',
                        })
                    segments.append(seg)
                    sid += 1

    unextractable_pages = []
    for pno, page in enumerate(doc):
        if any(s['page'] == pno for s in segments):
            continue
        if page_has_visible_content(page):
            unextractable_pages.append(pno)
            warnings.append({
                'page': pno,
                'kind': 'no-text-layer',
                'why': 'visible ink or an embedded image but no extractable '
                       'text — this looks scanned. Scans are out of scope with or '
                       'without an OCR layer; do not ship an untranslated file',
            })
    doc.close()

    warnings.extend(merge_candidate_warnings(segments))
    warnings.extend(narrow_column_warnings(segments))
    warnings.extend(right_alignment_warnings(segments))

    invisible = invisible_text_pages(src)
    for pno, fraction in invisible:
        warnings.append({
            'page': pno,
            'kind': 'invisible-text',
            'fraction': fraction,
            'why': 'the text layer is invisible (an OCR layer over a scanned '
                   'image, or text hidden under an image): stripping it '
                   'changes nothing the reader sees. The visible words are '
                   'pixels; do not ship',
        })

    document = document_strings(src)

    uniq = {}
    for s in segments:
        if not s['passthrough']:
            uniq[s['core']] = uniq.get(s['core'], 0) + 1
    # The document title and every outline entry are read by the window
    # caption, the bookmarks pane and every screen reader. They are cores.
    for extra in [document['title']] + document['outline']:
        if extra and not PASS.match(extra):
            uniq.setdefault(extra, 0)
            uniq[extra] += 1

    seg_path = os.path.join(outdir, 'segments.json')
    to_path = os.path.join(outdir, 'to_translate.json')
    widget_path = os.path.join(outdir, 'widget_text.json')
    widget_text = widget_text_scaffold(src)
    with open(widget_path, 'w', encoding='utf-8') as f:
        json.dump(widget_text, f, ensure_ascii=False, indent=1)
    with open(seg_path, 'w', encoding='utf-8') as f:
        json.dump({'source': src, 'segments': segments,
                   'warnings': warnings, 'document': document},
                  f, ensure_ascii=False, indent=1)
    cores = [{'text': k, 'count': v} for k, v in uniq.items()]
    with open(to_path, 'w', encoding='utf-8') as f:
        json.dump({'cores': cores}, f, ensure_ascii=False, indent=1)
    return {
        'segments': segments,
        'warnings': warnings,
        'cores': cores,
        'document': document,
        'unextractable_pages': unextractable_pages,
        'invisible_text_pages': invisible,
        'segments_path': seg_path,
        'to_translate_path': to_path,
        'widget_text': widget_text,
        'widget_text_path': widget_path,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    src = argv[0]
    gap = float(argv[argv.index('--gap') + 1]) if '--gap' in argv else 12.0
    outdir = argv[argv.index('--outdir') + 1] if '--outdir' in argv else '.'
    result = extract_segments(src, outdir=outdir, gap=gap)
    nseg = len(result['segments'])
    nuniq = len(result['cores'])
    nw = len(result['warnings'])
    nwidget = len(result['widget_text'])
    print(f'{nseg} segments, {nuniq} unique strings to translate, '
          f'{nw} warnings -> segments.json / to_translate.json')
    if nwidget:
        print(f'{nwidget} field(s) carry widget text (tooltips, dropdown '
              f'labels, defaults) -> widget_text.json; author each "target" '
              f'and pass it to strip_text.py --widget-text')
    if result['warnings']:
        print('WARNINGS (need review):')
        for w in result['warnings']:
            kind = w.get('kind', '')
            extra = f" [{kind}]" if kind else ''
            preview = w.get('text') or (w.get('lines') or [''])[0]
            pid = w.get('id', ','.join(str(i) for i in w.get('ids', [])))
            print(f"  p{w['page']} seg {pid}{extra}: {preview}")
    rc = 0
    if result.get('unextractable_pages'):
        pages = ', '.join(str(p) for p in result['unextractable_pages'])
        print(f'FAIL: pages with visible content but no extractable text: {pages}')
        print('  This looks scanned. The pipeline cannot translate images, and an '
              'OCR layer would not help (it is refused too); say so.')
        rc = 1
    if result.get('invisible_text_pages'):
        pages = ', '.join(f'{p} ({f:.1%} of text area changes)'
                          for p, f in result['invisible_text_pages'])
        print(f'FAIL: pages whose text layer is invisible: {pages}')
        print('  This looks like an OCR\'d scan (image + invisible OCR text layer). '
              'The words the reader sees are pixels; strip-and-retypeset would print '
              'the translation over them. This pipeline has no masking mode; do not ship.')
        rc = 1
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
