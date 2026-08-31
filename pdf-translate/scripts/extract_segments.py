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

Segmentation rules (why they matter):
- A visual line is split at horizontal gaps > GAP pt between spans: one line
  often holds several independent cells (CITY: STATE: ZIP:) or a label and a
  dot-leader run separated by a checkbox gap. Each piece is placed on its own.
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

Usage:
  python3 extract_segments.py ORIGINAL.pdf [--gap 12] [--outdir .]
"""
import json
import os
import re
import sys

import pymupdf

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


def extract_segments(src, outdir='.', gap=12.0):
    """Extract geometry + unique cores. Writes segments.json and to_translate.json."""
    os.makedirs(outdir, exist_ok=True)
    doc = pymupdf.open(src)
    segments, warnings = [], []
    sid = 0
    for pno, page in enumerate(doc):
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0:
                continue
            for line in b['lines']:
                groups = []
                for s in line['spans']:
                    if not s['text'].strip() and not groups:
                        continue
                    if groups and s['bbox'][0] - groups[-1]['bbox'][2] < gap:
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
                       'text — this looks scanned. OCR first; do not ship an '
                       'untranslated file',
            })
    doc.close()

    warnings.extend(merge_candidate_warnings(segments))

    uniq = {}
    for s in segments:
        if not s['passthrough']:
            uniq[s['core']] = uniq.get(s['core'], 0) + 1

    seg_path = os.path.join(outdir, 'segments.json')
    to_path = os.path.join(outdir, 'to_translate.json')
    with open(seg_path, 'w', encoding='utf-8') as f:
        json.dump({'source': src, 'segments': segments, 'warnings': warnings},
                  f, ensure_ascii=False, indent=1)
    cores = [{'text': k, 'count': v} for k, v in uniq.items()]
    with open(to_path, 'w', encoding='utf-8') as f:
        json.dump({'cores': cores}, f, ensure_ascii=False, indent=1)
    return {
        'segments': segments,
        'warnings': warnings,
        'cores': cores,
        'unextractable_pages': unextractable_pages,
        'segments_path': seg_path,
        'to_translate_path': to_path,
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
    print(f'{nseg} segments, {nuniq} unique strings to translate, '
          f'{nw} warnings -> segments.json / to_translate.json')
    if result['warnings']:
        print('WARNINGS (need review):')
        for w in result['warnings']:
            kind = w.get('kind', '')
            extra = f" [{kind}]" if kind else ''
            preview = w.get('text') or (w.get('lines') or [''])[0]
            pid = w.get('id', ','.join(str(i) for i in w.get('ids', [])))
            print(f"  p{w['page']} seg {pid}{extra}: {preview}")
    if result.get('unextractable_pages'):
        pages = ', '.join(str(p) for p in result['unextractable_pages'])
        print(f'FAIL: pages with visible content but no extractable text: {pages}')
        print('  This looks scanned. OCR first; the pipeline cannot translate images.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
