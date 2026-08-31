#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 4 of pdf-translate: re-typeset translated text onto the stripped PDF.

Consumes segments.json (from extract_segments.py) + translations.json
(authored by you — format documented in references/translations-format.md)
and writes the translated PDF. All layout mechanics live here so every
document gets the same behavior:

- single-line segments -> TextWriter at the ORIGINAL baseline origin
- shrink-to-fit bounded by the nearest same-row obstacle (next segment or
  widget rect) so text never overlaps fields or neighboring cells
- dot leaders refilled anchored to the RIGHT at most the original run width
  (keeps leaders out of mid-line checkbox gaps)
- '‖' in a translation splits a bold lead-in from a regular remainder
- declared merges rendered as re-flowed paragraphs via insert_htmlbox
  with auto-shrink (scale_low=0)
- centered strings re-centered on the original bbox midpoint
- pass-through segments re-inserted verbatim in Helvetica
- every non-passthrough segment lacking a translation is reported; the run
  FAILS (exit 1) if any exist — missing text must never ship silently
- any run scaled below 0.7× FAILS unless its core (or merge first line) is
  in allow_scale — tiny type must not ship as a note
- RTL targets (Hebrew/Arabic) are written with right_to_left and wrapped in
  /ActualText so the logical string is in the text layer; layout stays LTR
  unless translations.json sets mirror: true (opt-in x-flip of text +
  field/link rects; graphics stay)

Usage:
  python3 retypeset.py STRIPPED.pdf segments.json translations.json OUT.pdf
"""
import json
import re
import sys
import time

import pymupdf

SCALE_MIN = 0.7
# Hebrew, Arabic, Syriac, Thaana, Arabic supplement/presentation forms.
_RTL_RANGES = (
    (0x0590, 0x08FF),
    (0xFB1D, 0xFDFF),
    (0xFE70, 0xFEFC),
)


def is_rtl_text(text):
    """True if text contains Hebrew/Arabic-block letters."""
    for ch in text or '':
        o = ord(ch)
        for a, b in _RTL_RANGES:
            if a <= o <= b:
                return True
    return False


def _actualtext_bdc(text):
    raw = b'\xfe\xff' + (text or '').encode('utf-16-be')
    return b'/Span << /ActualText <' + raw.hex().encode('ascii') + b'> >> BDC\n'


def wrap_last_bt_actualtext(page, logical):
    """Mark the most recent content stream's BT..ET with /ActualText."""
    if not logical:
        return
    xrefs = page.get_contents()
    if not xrefs:
        return
    xref = xrefs[-1]
    data = page.parent.xref_stream(xref) or b''
    i = data.find(b'BT')
    if i < 0:
        return
    j = data.find(b'ET', i)
    if j < 0:
        return
    if b'/ActualText' in data[i:j]:
        return
    k = i + 2
    if k < len(data) and data[k:k + 1] in (b'\n', b'\r', b' '):
        k += 1
        if data[k - 1:k + 1] == b'\r\n':
            k += 1
    new = data[:k] + _actualtext_bdc(logical) + data[k:j] + b'EMC\n' + data[j:]
    page.parent.update_stream(xref, new)


def _load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def retypeset(stripped, segf, trf, out):
    """Place translations onto a stripped PDF. Returns 0, or 1 if cores/overflow."""
    segd = _load_json(segf)
    conf = _load_json(trf)
    T = conf['translations']
    merges = conf.get('merges', [])
    center = set(conf.get('center', []))
    skip = set(conf.get('skip', []))
    allow_scale = set(conf.get('allow_scale') or [])
    overrides = conf.get('overrides', [])
    fonts = conf['fonts']
    overflow = []
    mirror = bool(conf.get('mirror'))

    def mirror_left(left, width, pw):
        if not mirror:
            return left
        return pw - left - width

    def consider_ratio(pno, key, ratio, opted=False):
        if ratio >= SCALE_MIN:
            return
        shown = (key or '')[:50]
        if opted or key in allow_scale:
            print(f'  note: p{pno} scaled to {ratio:.2f}x (allow_scale): {shown}')
            return
        overflow.append((pno, ratio, key))

    segments = segd['segments']
    by_page = {}
    for s in segments:
        by_page.setdefault(s['page'], []).append(s)

    merge_jobs = []
    for m in merges:
        page_segs = by_page.get(m['page'], [])
        idxs, li = [], 0
        for i, s in enumerate(page_segs):
            if li < len(m['lines']) and s['text'].strip() == m['lines'][li].strip():
                idxs.append(i)
                li += 1
        if li != len(m['lines']):
            print(f"!! merge not matched p{m['page']}: {m['lines'][0][:60]} "
                  f"({li}/{len(m['lines'])})")
            return 1
        r = pymupdf.Rect(min(page_segs[i]['bbox'][0] for i in idxs),
                         min(page_segs[i]['bbox'][1] for i in idxs),
                         max(page_segs[i]['bbox'][2] for i in idxs),
                         max(page_segs[i]['bbox'][3] for i in idxs))
        size = max(page_segs[i]['size'] for i in idxs)
        # Derive leading from the ORIGINAL baselines rather than assuming a
        # ratio: a flyer set 11pt on 16pt leading re-flows visibly compressed
        # if you hardcode 1.18, and the block no longer lines up with the rules
        # and headings around it.
        ys = sorted(page_segs[i]['origin'][1] for i in idxs)
        gaps = [b - a for a, b in zip(ys, ys[1:]) if b - a > 0.5]
        lh = round((sum(gaps) / len(gaps)) / size, 3) if gaps else 1.18
        color = m.get('color', page_segs[idxs[0]].get('color', 0))
        merge_key = (m.get('lines') or [m.get('html') or ''])[0]
        merge_opt = bool(m.get('allow_scale'))
        merge_jobs.append((m['page'], r, m['html'], m.get('align', 'left'),
                           size, lh, color, merge_key, merge_opt))
        for i in sorted(idxs, reverse=True):
            del page_segs[i]

    missing = []
    for pno, segs in by_page.items():
        for seg in segs:
            if seg['text'].strip() in skip:
                continue
            if T.get(seg['core']) is None and not seg['passthrough']:
                missing.append((pno, seg['core']))
    if missing:
        print(f'FAIL: {len(missing)} untranslated segments:')
        for p, c in missing[:30]:
            print(f'  p{p}: {c}')
        return 1

    font_r = pymupdf.Font(fontfile=fonts['regular'])
    font_b = pymupdf.Font(fontfile=fonts.get('bold', fonts['regular']))
    helv = pymupdf.Font('helv')
    hebo = pymupdf.Font('hebo')

    doc = pymupdf.open(stripped)
    widg = {p.number: [w.rect for w in p.widgets()] for p in doc}

    def right_limit(pno, seg, segs):
        x0 = seg['origin'][0]
        y0, y1 = seg['bbox'][1], seg['bbox'][3]
        lim = doc[pno].rect.width - 32
        for o in segs:
            if o is seg:
                continue
            if o['bbox'][0] > seg['bbox'][2] - 1 and not (
                    o['bbox'][3] < y0 + 1 or o['bbox'][1] > y1 - 1):
                lim = min(lim, o['bbox'][0])
        for wr in widg.get(pno, []):
            if wr.x0 > x0 + 1 and not (wr.y1 < y0 + 1 or wr.y0 > y1 - 1):
                if wr.x0 > seg['bbox'][2] - 2:
                    lim = min(lim, wr.x0)
        return lim - 1.5

    missing = []
    over_by_page = {}
    for o in overrides:
        over_by_page.setdefault(o['page'], []).append(o)

    for pno, page in enumerate(doc):
        segs = by_page.get(pno, [])
        # One TextWriter per distinct source color. A single black writer is
        # how white-on-dark headings silently become black-on-dark: the ink
        # gate barely moves because the band was already dark.
        writers = {}
        rtl_jobs = []

        def W(cint):
            if cint not in writers:
                writers[cint] = pymupdf.TextWriter(page.rect)
            return writers[cint]

        def rgb_of(cint):
            return (((cint >> 16) & 255) / 255.0,
                    ((cint >> 8) & 255) / 255.0,
                    (cint & 255) / 255.0)

        for seg in segs:
            tw = W(int(seg.get('color', 0)))
            text = seg['text'].strip()
            if text in skip:
                continue
            fs = seg['size']
            ox, oy = seg['origin']
            ov = next((o for o in over_by_page.get(pno, [])
                       if o['contains'] in text), None)
            if ov:
                for part in ov['parts']:
                    f = font_b if part.get('bold') else font_r
                    x = part.get('x', ox)
                    t = part['text']
                    w = f.text_length(t, fs)
                    maxw = part.get('max_width', 10_000)
                    fs2 = fs if w <= maxw else max(4.0, fs * maxw / w)
                    if fs and fs2 < fs:
                        consider_ratio(pno, ov.get('contains') or t, fs2 / fs)
                    if is_rtl_text(t):
                        rtl_jobs.append((x, oy, t, f, fs2, int(seg.get('color', 0)), t))
                    else:
                        tw.append((mirror_left(x, f.text_length(t, fs2),
                                               page.rect.width), oy),
                                  t, font=f, fontsize=fs2)
                continue
            core, marker, dots, tail = (
                seg['core'], seg['marker'], seg['dots'], seg['tail'])
            jp = T.get(core)
            if jp is None:
                if not seg['passthrough']:
                    missing.append((pno, core))
                f = hebo if seg['bold'] else helv
                raw = seg['text'].rstrip()
                tw.append((mirror_left(ox, f.text_length(raw, fs), page.rect.width),
                           oy), raw, font=f, fontsize=fs)
                continue
            parts = []
            if marker:
                parts.append((marker + ' ', hebo if seg['bold'] else helv))
            if '‖' in jp:
                bp, rp = jp.split('‖', 1)
                parts.append((bp, font_b))
                parts.append((rp, font_r))
            else:
                parts.append((jp, font_b if seg['bold'] else font_r))
            wsum = sum(f.text_length(t, fs) for t, f in parts)
            rtl_body = is_rtl_text(jp)
            if dots and not rtl_body and not mirror:
                cur_end = seg['bbox'][2] - (
                    helv.text_length(tail, fs) + 2 if tail else 0)
                label_max = cur_end - ox - 8
                fs2 = fs if wsum <= label_max else max(4.0, fs * label_max / wsum)
                if fs and fs2 < fs:
                    consider_ratio(pno, core, fs2 / fs)
                x = ox
                for t, f in parts:
                    tw.append((x, oy), t, font=f, fontsize=fs2)
                    x += f.text_length(t, fs2)
                dw = helv.text_length('.', fs)
                dstart = max(x + 1, cur_end - len(dots) * dw)
                n = max(0, int((cur_end - dstart) / dw))
                if n:
                    tw.append((dstart, oy), '.' * n, font=helv, fontsize=fs)
                if tail:
                    tw.append((cur_end + 2, oy), tail, font=helv, fontsize=fs)
                continue
            maxw = right_limit(pno, seg, segs) - ox
            fs2 = fs if wsum <= maxw or wsum == 0 else max(4.0, fs * maxw / wsum)
            if fs and fs2 < fs:
                consider_ratio(pno, core, fs2 / fs)
            x = ox
            if core in center:
                w2 = sum(f.text_length(t, fs2) for t, f in parts)
                cx = (seg['bbox'][0] + seg['bbox'][2]) / 2
                x = max(ox - 200, cx - w2 / 2)
            run_w = sum(f.text_length(t, fs2) for t, f in parts)
            x = mirror_left(x, run_w, page.rect.width)
            if rtl_body:
                logical = jp.replace('‖', '')
                rtl_jobs.append((x, oy, logical,
                                 font_b if seg['bold'] else font_r, fs2,
                                 int(seg.get('color', 0)), logical))
            else:
                for t, f in parts:
                    tw.append((x, oy), t, font=f, fontsize=fs2)
                    x += f.text_length(t, fs2)
        for cint, w in writers.items():
            w.write_text(page, color=rgb_of(cint))
        for (rx, ry, t, fnt, fsz, cint, logical) in rtl_jobs:
            rtw = pymupdf.TextWriter(page.rect)
            rtw.append((rx, ry), t, font=fnt, fontsize=fsz, right_to_left=True)
            rtw.write_text(page, color=rgb_of(cint))
            wrap_last_bt_actualtext(page, logical)

    arch = pymupdf.Archive('.')
    css = (f"@font-face {{font-family: tr; src: url({fonts['regular']});}}"
           f"@font-face {{font-family: trb; src: url({fonts.get('bold', fonts['regular'])});}}"
           "body {font-family: tr; margin: 0; padding: 0;}"
           "b {font-family: trb; font-weight: normal;}")
    for (pno, r, html, align, size, lh, color, merge_key, merge_opt) in merge_jobs:
        pw = doc[pno].rect.width
        if mirror:
            r = pymupdf.Rect(pw - r.x1, r.y0, pw - r.x0, r.y1)
            align = {'left': 'right', 'right': 'left'}.get(align, align)
        rect = pymupdf.Rect(r.x0, r.y0 - 0.5, r.x1 + 1.5, r.y1 + 1.5)
        hexcol = f'#{color:06x}'
        h = (f'<div style="font-size:{size*0.98:.1f}px; line-height:{lh}; '
             f'color:{hexcol}; text-align:{align};">{html}</div>')
        _, scale = doc[pno].insert_htmlbox(rect, h, css=css, archive=arch, scale_low=0)
        consider_ratio(pno, merge_key, scale, opted=merge_opt)
        plain = re.sub(r'<[^>]+>', '', html)
        if is_rtl_text(plain):
            wrap_last_bt_actualtext(doc[pno], plain)

    if missing:
        print(f'FAIL: {len(missing)} untranslated segments:')
        for p, c in missing[:30]:
            print(f'  p{p}: {c}')
    if overflow:
        print(f'FAIL: {len(overflow)} segments scaled below {SCALE_MIN}x '
              f'(shorten the translation or add allow_scale):')
        for p, ratio, c in overflow[:30]:
            print(f'  p{p} {ratio:.2f}x: {c}')
    if missing or overflow:
        doc.close()
        return 1

    if mirror:
        for page in doc:
            pw = page.rect.width
            for w in list(page.widgets() or []):
                r = w.rect
                w.rect = pymupdf.Rect(pw - r.x1, r.y0, pw - r.x0, r.y1)
                w.update()
            for lnk in list(page.get_links() or []):
                r = pymupdf.Rect(lnk['from'])
                flipped = dict(lnk)
                flipped['from'] = pymupdf.Rect(pw - r.x1, r.y0, pw - r.x0, r.y1)
                page.delete_link(lnk)
                page.insert_link(flipped)

    doc.ez_save(out)
    doc.close()
    print('saved', out)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    stripped, segf, trf, out = argv[0], argv[1], argv[2], argv[3]
    t0 = time.perf_counter()
    rc = retypeset(stripped, segf, trf, out)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
