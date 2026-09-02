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
- document metadata is retargeted: /Lang (and dc:language in XMP) from
  translations.json's "lang", /Title and every outline title from the
  mapping (both are cores), and the orphaned /StructTreeRoot is removed
  with /MarkInfo /Marked false, because the tags describe text that no
  longer exists
- every character of every placed run is checked against the exact font
  object that will draw it; a character the font lacks FAILS, because
  MuPDF substitutes a fallback face mid-string (or draws a box) and
  reports nothing
- RTL targets (Hebrew/Arabic) are written with right_to_left and wrapped in
  /ActualText so the logical string is in the text layer; layout stays LTR
  unless translations.json sets mirror: true (opt-in x-flip of text +
  field/link rects; graphics stay)
- runs whose target script needs shaping (Arabic-family, Indic, Thai, Lao,
  Khmer, Myanmar, Tibetan) are placed with the Story engine
  (insert_htmlbox, HarfBuzz) on the original baseline, at the original
  size and colour, then wrapped in /ActualText; TextWriter would draw
  them letter by letter (isolated Arabic forms, broken conjuncts)
- rotated lines (side labels, stamps) keep their angle: the run is written
  horizontally and morphed about its own origin by the segment's recorded
  direction, so origin, bbox and line direction match the source run. The
  width budget runs along that direction. Dot leaders, centering and the
  RTL mirror stay horizontal-only ideas and are skipped on a rotated run;
  a rotated run whose target also needs SHAPING is refused rather than
  drawn flat

Usage:
  python3 retypeset.py STRIPPED.pdf segments.json translations.json OUT.pdf
"""
import html as htmlmod
import json
import math
import re
import sys
import time
import unicodedata
from pathlib import PurePath

import pymupdf

SCALE_MIN = 0.7
# Hebrew, Arabic, Syriac, Thaana, Arabic supplement/presentation forms.
_RTL_RANGES = (
    (0x0590, 0x08FF),
    (0xFB1D, 0xFDFF),
    (0xFE70, 0xFEFC),
)


def seg_dir(seg):
    """Unit line direction of a segment; (1, 0) when absent or unusable."""
    d = seg.get('dir') or (1.0, 0.0)
    try:
        dx, dy = float(d[0]), float(d[1])
    except (TypeError, ValueError, IndexError, KeyError):
        return 1.0, 0.0
    n = math.hypot(dx, dy)
    if n < 1e-9:
        return 1.0, 0.0
    return dx / n, dy / n


def is_rotated(dx, dy):
    return abs(dx - 1.0) > 1e-6 or abs(dy) > 1e-6


def rotation_morph(x, y, dx, dy):
    """(pivot, matrix) that turns a horizontal run into direction (dx, dy).

    Verified against extraction: text written horizontally at (x, y) and
    morphed this way comes back with the same origin, the same bbox and
    the same line dir as the source run it replaces.
    """
    return (pymupdf.Point(x, y), pymupdf.Matrix(dx, -dy, dy, dx, 0, 0))


def direction_limit(page, seg, dx, dy, margin=16.0):
    """Room from the segment origin to the page edge ALONG its direction.

    right_limit's obstacle scan is a horizontal idea (same-row neighbours,
    widget rects to the right). Projecting every neighbour onto an
    arbitrary axis is a different problem, and a rotated run is nearly
    always a margin label or a stamp with nothing beyond it. The page edge
    is the budget; the 0.7x gate still refuses a translation that cannot
    fit in it.
    """
    x, y = seg['origin']
    r = page.rect
    limits = []
    if dx > 1e-9:
        limits.append((r.x1 - margin - x) / dx)
    elif dx < -1e-9:
        limits.append((x - r.x0 - margin) / -dx)
    if dy > 1e-9:
        limits.append((r.y1 - margin - y) / dy)
    elif dy < -1e-9:
        limits.append((y - r.y0 - margin) / -dy)
    return max(1.0, min(limits)) if limits else 1.0


def is_rtl_text(text):
    """True if text contains Hebrew/Arabic-block letters."""
    for ch in text or '':
        o = ord(ch)
        for a, b in _RTL_RANGES:
            if a <= o <= b:
                return True
    return False


# Scripts whose letters must be shaped before they are drawn: joining
# (Arabic family), conjuncts and mark placement (Indic, Thai, Lao, Khmer,
# Myanmar, Tibetan). Hebrew only needs direction and stays on TextWriter.
_SHAPING_RANGES = (
    (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),   # Arabic
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFC),                      # Arabic presentation forms
    (0x0700, 0x074F),                                        # Syriac
    (0x07C0, 0x07FF),                                        # N'Ko
    (0x0900, 0x0DFF),                                        # Devanagari .. Sinhala
    (0x0E00, 0x0EFF),                                        # Thai, Lao
    (0x0F00, 0x0FFF),                                        # Tibetan
    (0x1000, 0x109F),                                        # Myanmar
    (0x1780, 0x17FF),                                        # Khmer
)
# Measured on insert_htmlbox with line-height 1: a single line's baseline sits
# 0.8 x size below the rect top for every font tried, and the run starts at
# the rect's left edge. A rect 1.25 x size tall holds one line; a second line
# only fits once the engine has scaled below the 0.7x gate, which refuses.
SHAPED_BASELINE = 0.8
SHAPED_LINE = 1.25


def needs_shaping(text):
    """True if text contains letters of a script that must be shaped."""
    for ch in text or '':
        o = ord(ch)
        for a, b in _SHAPING_RANGES:
            if a <= o <= b:
                return True
    return False


def place_shaped(page, x, baseline, text, bold, fs, color_int, avail, css, arch):
    """Draw one shaped run with the Story engine; returns the scale applied."""
    top = baseline - SHAPED_BASELINE * fs
    rect = pymupdf.Rect(x, top, x + max(avail, 1.0) + 1.0, top + SHAPED_LINE * fs)
    fam = 'trb' if bold else 'tr'
    body = (f'<div style="font-family:{fam}; font-size:{fs:.2f}px; line-height:1; '
            f'color:#{color_int:06x}; margin:0; padding:0">{htmlmod.escape(text)}</div>')
    _, scale = page.insert_htmlbox(rect, body, css=css, archive=arch, scale_low=0)
    wrap_last_stream_actualtext(page, text)
    return scale


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


def wrap_last_stream_actualtext(page, logical):
    """Mark the page's newest content stream with /ActualText.

    The Story engine (insert_htmlbox) draws into a Form XObject and appends
    a stream that only invokes it (q /fzFrmN Do Q); the glyphs it leaves in
    the text layer are presentation forms or glyph ids. Wrapping that
    invocation in a marked-content span makes extraction report the logical
    string instead, which is what the placement gate reads.
    """
    if not logical:
        return
    xrefs = page.get_contents()
    if not xrefs:
        return
    xref = xrefs[-1]
    data = page.parent.xref_stream(xref) or b''
    if b'/ActualText' in data:
        return
    tail = (chr(10) + 'EMC' + chr(10)).encode('ascii')
    page.parent.update_stream(xref, _actualtext_bdc(logical) + data + tail)


def missing_glyphs(font, text):
    """Characters of text this font cannot draw.

    MuPDF does not report a missing glyph: it silently substitutes its own
    fallback face mid-string, and draws a box when the fallback has nothing
    either. Both look like a rendering choice, not a defect, so nothing
    downstream catches them — the ink gate barely moves and the text layer
    reads correctly. Control and format characters (soft hyphen, ZWJ,
    newlines) are not drawn and are not counted.
    """
    out = []
    seen = set()
    for ch in text or '':
        if ch in seen or ch in '\n\r\t':
            continue
        if unicodedata.category(ch) in ('Cc', 'Cf'):
            continue
        seen.add(ch)
        if not font.has_glyph(ord(ch)):
            out.append(ch)
    return out


# --------------------------------------------------------- document metadata
_DC_LANG = re.compile(r'(<dc:language>)(.*?)(</dc:language>)', re.S)
_RDF_LI = re.compile(r'(<rdf:li[^>]*>)(.*?)(</rdf:li>)', re.S)


def retarget_xmp(xml, lang):
    """Point every dc:language entry at the target tag. Returns (xml, changed).

    The Info dictionary and /Lang are rewritten from the mapping; XMP that
    still claims the source language contradicts both, and readers and
    catalogues believe XMP first. Everything else in the packet is left
    alone: it is the producer's, not ours.
    """
    if not xml or not lang:
        return xml, False
    changed = False

    def one(block):
        inner = block.group(2)
        if _RDF_LI.search(inner):
            new_inner = _RDF_LI.sub(lambda m: m.group(1) + lang + m.group(3),
                                    inner)
        else:
            new_inner = lang
        return block.group(1) + new_inner + block.group(3)

    out, n = _DC_LANG.subn(one, xml)
    changed = bool(n)
    return out, changed


def apply_document_metadata(doc, document, translations, lang):
    """Retarget /Lang, /Title and the outline; drop orphaned structure tags.

    None of this is page text, so nothing else in the pipeline touches it:
    an output otherwise keeps the source /Title in the window caption, the
    source /Lang for screen readers and hyphenation, and untranslated
    bookmarks. Structure tags describe text that no longer exists, so the
    tree is removed and /MarkInfo /Marked set false rather than left
    pointing at deleted content.
    """
    report = {'lang': None, 'title': None, 'outline': 0, 'xmp': False,
              'struct_tree_removed': False}
    document = document or {}

    if lang:
        try:
            doc.set_language(lang)
            report['lang'] = lang
        except Exception:
            pass
        xml = doc.get_xml_metadata() or ''
        new_xml, changed = retarget_xmp(xml, lang)
        if changed:
            doc.set_xml_metadata(new_xml)
            report['xmp'] = True

    src_title = (document.get('title') or '').strip()
    new_title = translations.get(src_title) if src_title else None
    if new_title:
        meta = dict(doc.metadata or {})
        meta['title'] = new_title
        meta.pop('format', None)
        meta.pop('encryption', None)
        doc.set_metadata(meta)
        report['title'] = new_title

    toc = doc.get_toc(simple=True) or []
    if toc:
        changed = 0
        for entry in toc:
            title = str(entry[1])
            target = translations.get(title)
            if target:
                entry[1] = target
                changed += 1
        if changed:
            doc.set_toc(toc)
            report['outline'] = changed

    cat = doc.pdf_catalog()
    if cat:
        try:
            kind, _ = doc.xref_get_key(cat, 'StructTreeRoot')
            if kind != 'null':
                doc.xref_set_key(cat, 'StructTreeRoot', 'null')
                report['struct_tree_removed'] = True
            doc.xref_set_key(cat, 'MarkInfo', '<< /Marked false >>')
        except Exception:
            pass
    return report


# ---------------------------------------------------- canonical text layer
# MuPDF builds an embedded font's /ToUnicode by reverse-mapping the font's
# cmap. When several code points share one glyph it can report the wrong
# one: Arial's space glyph comes back as NBSP (U+00A0), its hyphen as a
# soft hyphen (U+00AD), and common kanji as CJK Compatibility Ideographs
# (立 as U+F9F7). The glyphs on the page are right; the text layer is not,
# so copy-paste, search and every string gate see characters nobody
# authored. After saving we rewrite /ToUnicode for the glyphs we actually
# placed, to the code points the author actually wrote.
_SUBSET_PREFIX = re.compile(r'^[A-Z]{6}\+')


def _font_key(name):
    return _SUBSET_PREFIX.sub('', str(name or '').lstrip('/')).replace(
        ' ', '').lower()


def authored_gid_map(fontfile, texts):
    """{glyph id: code point} for every character placed with this font.

    Two authored characters can share one glyph (space and NBSP, hyphen
    and soft hyphen, 立 and its compatibility ideograph). The lower code
    point wins: in every drift pair the canonical character is the lower
    one, and picking it is what makes the layer canonical.
    """
    try:
        font = pymupdf.Font(fontfile=fontfile)
    except Exception:
        return None, ''
    out = {}
    for text in texts:
        for ch in text or '':
            cp = ord(ch)
            gid = font.has_glyph(cp)
            if not gid:
                continue
            if gid not in out or cp < out[gid]:
                out[gid] = cp
    return out, font.name


def _override_block(gidmap):
    lines = []
    items = sorted(gidmap.items())
    for i in range(0, len(items), 100):
        chunk = items[i:i + 100]
        lines.append(f'{len(chunk)} beginbfchar')
        for gid, cp in chunk:
            lines.append(f'<{gid:04x}> <{cp:04x}>' if cp <= 0xFFFF
                         else f'<{gid:04x}> <{_utf16be_hex(cp)}>')
        lines.append('endbfchar')
    return ('\n' + '\n'.join(lines) + '\n').encode('ascii')


def _utf16be_hex(cp):
    return chr(cp).encode('utf-16-be').hex()


def canonicalize_text_layer(path, fontfiles, texts):
    """Rewrite /ToUnicode so the text layer reports the authored code points.

    A CMap is executed in order, so a bfchar block appended before endcmap
    overrides whatever an earlier bfrange said for the same code. Returns
    the number of font objects patched.
    """
    import pikepdf

    maps = {}
    for fontfile in fontfiles:
        gidmap, name = authored_gid_map(fontfile, texts)
        if not gidmap or not name:
            continue
        maps.setdefault(_font_key(name), {}).update(gidmap)
    if not maps:
        return 0
    patched = 0
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    try:
        for obj in pdf.objects:
            try:
                if obj.get('/Type') != pikepdf.Name('/Font'):
                    continue
            except (AttributeError, TypeError):
                continue
            gidmap = maps.get(_font_key(obj.get('/BaseFont')))
            tu = obj.get('/ToUnicode')
            if not gidmap or tu is None:
                continue
            data = bytes(tu.read_bytes())
            i = data.rfind(b'endcmap')
            if i < 0:
                continue
            obj.ToUnicode = pdf.make_stream(
                data[:i] + _override_block(gidmap) + data[i:])
            patched += 1
        if patched:
            pdf.save(path)
    finally:
        pdf.close()
    return patched


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
    arch = pymupdf.Archive('.')
    # MuPDF's CSS parser eats backslashes, so a Windows path in url() loses
    # its separators and the engine silently falls back to a font without
    # the target script. Always hand it POSIX separators.
    css_regular = PurePath(fonts['regular']).as_posix()
    css_bold = PurePath(fonts.get('bold', fonts['regular'])).as_posix()
    css = (f"@font-face {{font-family: tr; src: url({css_regular});}}"
           f"@font-face {{font-family: trb; src: url({css_bold});}}"
           "body {font-family: tr; margin: 0; padding: 0;}"
           "b {font-family: trb; font-weight: normal;}")

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
    rotated_shaped = []
    glyph_misses = []
    seen_glyph_miss = set()

    def check_glyphs(pno, font, text, key, label):
        for ch in missing_glyphs(font, text):
            sig = (pno, label, ch)
            if sig in seen_glyph_miss:
                continue
            seen_glyph_miss.add(sig)
            glyph_misses.append((pno, label, ch, key))

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
        shaped_jobs = []
        # One writer per rotated run: a morph rotates a whole TextWriter
        # about a single pivot, and each run must turn about its own origin.
        rot_jobs = []

        def place_rotated(px, py, parts_fs, cint, dx, dy, rtl=False,
                          logical=''):
            rtw = pymupdf.TextWriter(page.rect)
            xx = px
            for t, f, fsz in parts_fs:
                rtw.append((xx, py), t, font=f, fontsize=fsz,
                           right_to_left=rtl)
                xx += f.text_length(t, fsz)
            rot_jobs.append((rtw, cint, rotation_morph(px, py, dx, dy),
                             logical if rtl else ''))

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
            dx, dy = seg_dir(seg)
            rot = is_rotated(dx, dy)
            ov = next((o for o in over_by_page.get(pno, [])
                       if o['contains'] in text), None)
            if ov:
                for part in ov['parts']:
                    f = font_b if part.get('bold') else font_r
                    x = part.get('x', ox)
                    t = part['text']
                    check_glyphs(pno, f, t, ov.get('contains') or t,
                                 'bold' if part.get('bold') else 'regular')
                    w = f.text_length(t, fs)
                    maxw = part.get('max_width', 10_000)
                    fs2 = fs if w <= maxw else max(4.0, fs * maxw / w)
                    if fs and fs2 < fs:
                        consider_ratio(pno, ov.get('contains') or t, fs2 / fs)
                    if needs_shaping(t):
                        if rot:
                            rotated_shaped.append((pno, t))
                            continue
                        avail = maxw if maxw < 5000 else page.rect.width - 32 - x
                        shaped_jobs.append((mirror_left(x, w, page.rect.width), oy, t,
                                            bool(part.get('bold')), fs, int(seg.get('color', 0)),
                                            avail, ov.get('contains') or t))
                    elif rot:
                        place_rotated(x, oy, [(t, f, fs2)],
                                      int(seg.get('color', 0)), dx, dy,
                                      rtl=is_rtl_text(t), logical=t)
                    elif is_rtl_text(t):
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
                check_glyphs(pno, f, raw, raw, 'Helvetica (pass-through)')
                if rot:
                    place_rotated(ox, oy, [(raw, f, fs)],
                                  int(seg.get('color', 0)), dx, dy)
                    continue
                tw.append((mirror_left(ox, f.text_length(raw, fs), page.rect.width),
                           oy), raw, font=f, fontsize=fs)
                continue
            parts = []
            if marker:
                mk_font = hebo if seg['bold'] else helv
                check_glyphs(pno, mk_font, marker, core,
                             'Helvetica (list marker)')
                parts.append((marker + ' ', mk_font))
            if '‖' in jp:
                bp, rp = jp.split('‖', 1)
                parts.append((bp, font_b))
                parts.append((rp, font_r))
            else:
                parts.append((jp, font_b if seg['bold'] else font_r))
            for t, f in parts:
                check_glyphs(pno, f, t, core,
                             'bold' if f is font_b else
                             ('regular' if f is font_r else 'Helvetica'))
            wsum = sum(f.text_length(t, fs) for t, f in parts)
            rtl_body = is_rtl_text(jp)
            shaped = needs_shaping(jp)
            if dots and not rtl_body and not shaped and not mirror and not rot:
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
                    check_glyphs(pno, helv, tail, core, 'Helvetica (tail)')
                    tw.append((cur_end + 2, oy), tail, font=helv, fontsize=fs)
                continue
            maxw = (direction_limit(page, seg, dx, dy) if rot
                    else right_limit(pno, seg, segs) - ox)
            fs2 = fs if wsum <= maxw or wsum == 0 else max(4.0, fs * maxw / wsum)
            if fs and fs2 < fs and not shaped:
                consider_ratio(pno, core, fs2 / fs)
            x = ox
            if core in center and not rot:
                w2 = sum(f.text_length(t, fs2) for t, f in parts)
                cx = (seg['bbox'][0] + seg['bbox'][2]) / 2
                x = max(ox - 200, cx - w2 / 2)
            run_w = sum(f.text_length(t, fs2) for t, f in parts)
            if not rot:
                x = mirror_left(x, run_w, page.rect.width)
            if rot:
                if shaped:
                    # Drawing a shaped script flat on a rotated label is the
                    # exact silent defect this program refuses to ship.
                    rotated_shaped.append((pno, core))
                    continue
                place_rotated(x, oy, [(t, f, fs2) for t, f in parts],
                              int(seg.get('color', 0)), dx, dy,
                              rtl=rtl_body, logical=jp.replace('‖', ''))
                continue
            if shaped:
                # Marker stays a TextWriter run in Helvetica; the body is
                # shaped at the ORIGINAL size and the engine's own scale
                # feeds the overflow gate.
                bx = x
                if marker:
                    mfont = hebo if seg['bold'] else helv
                    tw.append((bx, oy), marker + ' ', font=mfont, fontsize=fs)
                    bx += mfont.text_length(marker + ' ', fs)
                shaped_jobs.append((bx, oy, jp.replace('‖', ''), bool(seg['bold']), fs,
                                    int(seg.get('color', 0)), maxw - (bx - x), core))
                continue
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
        for (rtw, cint, morph, logical) in rot_jobs:
            rtw.write_text(page, color=rgb_of(cint), morph=morph)
            if logical:
                wrap_last_bt_actualtext(page, logical)
        for (rx, ry, t, fnt, fsz, cint, logical) in rtl_jobs:
            rtw = pymupdf.TextWriter(page.rect)
            rtw.append((rx, ry), t, font=fnt, fontsize=fsz, right_to_left=True)
            rtw.write_text(page, color=rgb_of(cint))
            wrap_last_bt_actualtext(page, logical)
        for (sx, sy, text, bold, fsz, cint, avail, key) in shaped_jobs:
            scale = place_shaped(page, sx, sy, text, bold, fsz, cint, avail, css, arch)
            consider_ratio(pno, key, scale)

    for (pno, r, html, align, size, lh, color, merge_key, merge_opt) in merge_jobs:
        plain_html = re.sub(r'<[^>]+>', '', html or '')
        check_glyphs(pno, font_r, plain_html, merge_key, 'regular')
        if re.search(r'<(b|strong)\b', html or '', re.I):
            check_glyphs(pno, font_b, plain_html, merge_key, 'bold')
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
        if is_rtl_text(plain) or needs_shaping(plain):
            wrap_last_stream_actualtext(doc[pno], plain)

    if missing:
        print(f'FAIL: {len(missing)} untranslated segments:')
        for p, c in missing[:30]:
            print(f'  p{p}: {c}')
    if overflow:
        print(f'FAIL: {len(overflow)} segments scaled below {SCALE_MIN}x '
              f'(shorten the translation or add allow_scale):')
        for p, ratio, c in overflow[:30]:
            print(f'  p{p} {ratio:.2f}x: {c}')
    if glyph_misses:
        print(f'FAIL: {len(glyph_misses)} character(s) the chosen font cannot '
              f'draw. MuPDF substitutes a fallback face mid-string or draws a '
              f'box and reports nothing; pick a font that covers the target '
              f'script (references/fonts.md):')
        for pno, label, ch, key in glyph_misses[:30]:
            name = unicodedata.name(ch, '?')
            print(f'  p{pno} [{label}] U+{ord(ch):04X} {name} ({ch}) in: '
                  f'{(key or "")[:40]}')
    if rotated_shaped:
        print(f'FAIL: {len(rotated_shaped)} rotated segments whose target needs '
              f'shaping. The Story engine places shaped runs upright; drawing '
              f'them flat on a rotated label would ship confidently wrong text:')
        for p, c in rotated_shaped[:30]:
            print(f'  p{p}: {c}')
    if missing or overflow or rotated_shaped or glyph_misses:
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

    meta_report = apply_document_metadata(
        doc, segd.get('document'), T, conf.get('lang'))
    if meta_report['title']:
        print(f'metadata: /Title -> {meta_report["title"][:60]}')
    if meta_report['outline']:
        print(f'metadata: {meta_report["outline"]} outline title(s) translated')
    if meta_report['lang']:
        print(f'metadata: /Lang -> {meta_report["lang"]}'
              + (' (and dc:language)' if meta_report['xmp'] else ''))
    if meta_report['struct_tree_removed']:
        print('metadata: removed the orphaned /StructTreeRoot and set '
              '/MarkInfo /Marked false — the tags described text that no '
              'longer exists. Tell the user the file is no longer tagged.')

    doc.ez_save(out)
    doc.close()

    # The glyphs are right either way; this is the text layer.
    placed = [t for t in T.values() if isinstance(t, str)]
    placed.extend(re.sub(r'<[^>]+>', '', m.get('html') or '') for m in merges)
    for o in overrides:
        placed.extend(part.get('text') or '' for part in o.get('parts') or [])
    for seg in segments:
        placed.extend((seg.get('marker') or '', seg.get('tail') or ''))
        if seg.get('passthrough'):
            placed.append(seg.get('text') or '')
    fontfiles = [fonts['regular'], fonts.get('bold', fonts['regular'])]
    n = canonicalize_text_layer(out, fontfiles, placed)
    if n:
        print(f'canonical text layer: rewrote /ToUnicode on {n} font object(s)')

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
