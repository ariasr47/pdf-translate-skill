#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 4 of pdf-translate: re-typeset translated text onto the stripped PDF.

Consumes segments.json (from extract_segments.py) + translations.json
(authored by you — format documented in references/translations-format.md)
and writes the translated PDF. All layout mechanics live here so every
document gets the same behavior:

- single-line segments -> TextWriter at the ORIGINAL baseline origin
- a list marker is re-emitted in Helvetica followed by the whitespace the
  source printed after it (segment "gap"; one space when a segments.json
  predates the key), and the body starts at the measured offset the
  source's own characters had (segment "body_dx"), because Helvetica's
  advance for the marker is only right for a Helvetica-metric source;
  without that key the body starts at Helvetica's width of marker + gap
- shrink-to-fit bounded by the nearest same-row obstacle (next segment or
  widget rect) so text never overlaps fields or neighboring cells
- dot leaders refilled anchored to the RIGHT at most the original run width
  (keeps leaders out of mid-line checkbox gaps), including on labels drawn
  by the Story engine (shaped scripts) or right-to-left
- '‖' in a translation splits a bold lead-in from a regular remainder
- declared merges rendered as re-flowed paragraphs via insert_htmlbox
  with auto-shrink (scale_low=0); a merge whose html is null is an
  accepted proposal nobody wrote yet, and FAILs like a null translation
- centered strings re-centered on the original bbox midpoint; strings in
  "right" re-anchored on the original bbox RIGHT edge, so a longer
  translation grows leftward instead of past the rule it sat against
- four font roles (regular, bold, italic, bold-italic) chosen from the
  source span's flags; a single-line target may carry inline <b>/<i>
  (or <strong>/<em>) and is then placed through the Story engine
- the compliance notice, if the job needs one, placed from "notices" into
  the box the author chose — the only text here that is not the
  translation of an existing string, and it goes through the same glyph
  check, canonical layer, scale report and placement gate as every run
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
import os
import re
import sys
import time
import unicodedata
from pathlib import PurePath

import pymupdf

SCALE_MIN = 0.7
# A notice the author did not size. Small enough for a footer line, big
# enough to read; `notices[].size` overrides it.
NOTICE_SIZE = 8.0
NOTICE_LH = 1.25
# Written beside the output on every successful build, so verify and a
# delivery can read what shrank without re-running retypeset. Pages are
# 0-based, the same as translations.json's merges[].page.
SCALE_REPORT = 'scale_report.json'
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


def _family(bold, italic):
    return ('trbi' if bold else 'tri') if italic else ('trb' if bold else 'tr')


def place_story_line(page, x, baseline, inner_html, bold, italic, fs,
                     color_int, avail, css, arch, logical=None):
    """Draw one line through the Story engine at the ORIGINAL baseline.

    Used for two jobs a TextWriter cannot do: scripts that need shaping
    (joining, conjuncts) and single-line targets that carry inline <b>/<i>.
    inner_html is already-built markup, so callers escape their own text.
    """
    top = baseline - SHAPED_BASELINE * fs
    rect = pymupdf.Rect(x, top, x + max(avail, 1.0) + 1.0, top + SHAPED_LINE * fs)
    body = (f'<div style="font-family:{_family(bold, italic)}; '
            f'font-size:{fs:.2f}px; line-height:1; '
            f'color:#{color_int:06x}; margin:0; padding:0">{inner_html}</div>')
    _, scale = page.insert_htmlbox(rect, body, css=css, archive=arch, scale_low=0)
    if logical:
        wrap_last_stream_actualtext(page, logical)
    return scale


def place_shaped(page, x, baseline, text, bold, fs, color_int, avail, css,
                 arch, italic=False):
    """Draw one shaped run with the Story engine; returns the scale applied."""
    return place_story_line(page, x, baseline, htmlmod.escape(text), bold,
                            italic, fs, color_int, avail, css, arch,
                            logical=text)


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


# Inline weight/style markup allowed in a SINGLE-LINE target, the way
# merges already allow it. Deliberately narrow: only these tags count as
# markup, so a translation that genuinely contains "<" is left alone.
INLINE_TAGS = re.compile(r'</?(?:b|i|em|strong)\s*/?>', re.I)


def has_inline_markup(text):
    return bool(INLINE_TAGS.search(text or ''))


def strip_inline_markup(text):
    return INLINE_TAGS.sub('', text or '')


def _role_name(bold, italic):
    if bold and italic:
        return 'bold-italic'
    return 'bold' if bold else ('italic' if italic else 'regular')


def _font_label(font, labels):
    return labels.get(id(font), 'font')


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


def ligature_gid_map(fontfile, chars):
    """{glyph id: text} for the ligatures and the single-substitution
    alternates this text could have produced.

    Alternates: Noto Sans JP swaps its digits for `locl` forms when
    HarfBuzz shapes a Latin run under the Japanese language tag (FL-150
    after "FL-", 11 in "11-inch"; digits inside a CJK run are untouched),
    and the alternate glyph has no cmap entry, so the layer said Ɍɐɋ for
    150 (measured on the FL-150 -> ja job, 2026-09-17). Each such glyph is
    mapped to its base glyph's character.

    The Story engine shapes Latin too: HarfBuzz applies `liga`/`clig` by
    default, and MuPDF 1.28 honours neither `font-variant-ligatures: none`
    nor `font-feature-settings` (measured, row 24), so "oficina" is drawn
    with the fi glyph and the layer says U+FB01 — or U+007F once the font
    is subsetted. The glyph is read from GSUB, not from cmap: pyftsubset
    keeps the substitution and the outline but drops U+FB01 from the cmap
    when the authored text never contained it, so cmap cannot find it.

    Only ligatures whose components are all authored are mapped, which
    keeps the override block to the handful a job can actually reach.
    """
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(fontfile, lazy=True, fontNumber=0)
    except Exception:
        return {}
    try:
        return _ligatures(font, chars)
    except Exception:
        return {}
    finally:
        try:
            font.close()
        except Exception:
            pass


def _ligatures(font, chars):
    if 'GSUB' not in font:
        return {}
    lookups = font['GSUB'].table.LookupList.Lookup or []
    cmap = font.getBestCmap()
    lowest = {}
    for cp, name in cmap.items():
        if name not in lowest or cp < lowest[name]:
            lowest[name] = cp
    want = set(chars)
    out = {}
    for lookup in lookups:
        for sub in (getattr(lookup, 'SubTable', None) or []):
            # An extension lookup (type 7) wraps the real one.
            sub = getattr(sub, 'ExtSubTable', sub)
            # A single substitution (locl digits, vert forms, stylistic
            # sets) parks an authored character on an alternate glyph that
            # no code point names: map it back to the base's character. An
            # alternate that cmap already names is somebody's character
            # and is left alone.
            for base, alt in (getattr(sub, 'mapping', None) or {}).items():
                cp = lowest.get(base)
                if cp is None or chr(cp) not in want or alt in lowest:
                    continue
                try:
                    gid = font.getGlyphID(alt)
                except Exception:
                    continue
                prev = out.get(gid)
                if prev is None or (len(prev) == 1 and cp < ord(prev)):
                    out[gid] = chr(cp)
            for first, ligs in (getattr(sub, 'ligatures', None) or {}).items():
                for lig in ligs:
                    cps = [lowest.get(n)
                           for n in [first] + list(lig.Component)]
                    if any(c is None for c in cps):
                        continue
                    text = ''.join(chr(c) for c in cps)
                    if not set(text) <= want:
                        continue
                    try:
                        out[font.getGlyphID(lig.LigGlyph)] = text
                    except Exception:
                        continue
    return out


def authored_gid_map(fontfile, texts):
    """{glyph id: authored text} for every character placed with this font.

    Two authored characters can share one glyph (space and NBSP, hyphen
    and soft hyphen, 立 and its compatibility ideograph). The lower code
    point wins: in every drift pair the canonical character is the lower
    one, and picking it is what makes the layer canonical.

    A ligature glyph is nobody's character, so it is not reached by the
    loop below and keeps whatever the font said; those come from GSUB and
    map to more than one code point, which is why the values are strings.
    """
    try:
        font = pymupdf.Font(fontfile=fontfile)
    except Exception:
        return None, ''
    out = {}
    chars = set()
    for text in texts:
        for ch in text or '':
            chars.add(ch)
            cp = ord(ch)
            gid = font.has_glyph(cp)
            if not gid:
                continue
            if gid not in out or cp < ord(out[gid]):
                out[gid] = ch
    for gid, text in ligature_gid_map(fontfile, chars).items():
        out.setdefault(gid, text)
    return out, font.name


def _override_block(gidmap):
    lines = []
    items = sorted(gidmap.items())
    for i in range(0, len(items), 100):
        chunk = items[i:i + 100]
        lines.append(f'{len(chunk)} beginbfchar')
        for gid, text in chunk:
            # A bfchar destination may be several UTF-16BE code units, so
            # one entry can say "this glyph is f then i"; a bfrange cannot.
            lines.append(f'<{gid:04x}> <{_utf16be_hex(text)}>')
        lines.append('endbfchar')
    return ('\n' + '\n'.join(lines) + '\n').encode('ascii')


def _utf16be_hex(text):
    return text.encode('utf-16-be').hex()


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
            # pdf.objects yields every indirect object, including arrays,
            # numbers and strings. Asking one of those for a key raises,
            # and WHICH exception depends on the pikepdf version
            # (ValueError on 9.x, TypeError elsewhere) — so catch the
            # attempt, not a guessed type.
            try:
                if obj.get('/Type') != pikepdf.Name('/Font'):
                    continue
            except Exception:
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
    right = set(conf.get('right') or [])
    skip = set(conf.get('skip', []))
    allow_scale = set(conf.get('allow_scale') or [])
    overrides = conf.get('overrides', [])
    notices = conf.get('notices') or []
    # Mapping-relative paths work for both the direct command and rebuild.
    # Keep old caller-relative mappings usable, but make the fallback visible.
    font_dir = os.path.dirname(os.path.abspath(trf))
    fonts = {}
    for role_name, path in conf['fonts'].items():
        if path and not os.path.isabs(path):
            local = os.path.join(font_dir, path)
            if not os.path.isfile(local) and os.path.isfile(path):
                print(f'NOTE font {role_name}: legacy caller-relative path {path}; '
                      'prefer a path relative to translations.json')
                local = os.path.abspath(path)
            path = local
        fonts[role_name] = path
    overflow = []
    scaled = []
    mirror = bool(conf.get('mirror'))

    def mirror_left(left, width, pw):
        if not mirror:
            return left
        return pw - left - width

    def consider_ratio(pno, key, ratio, opted=False):
        # Anything the fit or the engine shrank is reported, not only what
        # it shrank past the floor: the author cannot name a scaled run in
        # the delivery if nothing ever tells them (row 25).
        if ratio < 1.0:
            scaled.append({'page': pno, 'key': key or '', 'ratio': round(ratio, 4)})
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
    unauthored_merges = []
    for m in merges:
        if m.get('html') is None:
            # A merge proposal accepted in bulk but not yet written. Same
            # rule as a null translation: it must not ship silently.
            unauthored_merges.append(
                (m.get('page'), (m.get('lines') or [''])[0]))
            continue
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
        # An author may hand the merge a rect of their own (row 26): a
        # paragraph whose target needs one more line than the source could
        # otherwise only shrink, or be declined and hard-wrapped at the
        # source's breaks. Geometry must not choose this box — a box that
        # grows into a rule or a field is worse than a shrink — but the
        # author can see the page and choose.
        boxed = m.get('box') is not None
        if boxed:
            try:
                bx0, by0, bx1, by1 = (float(v) for v in m['box'])
            except (TypeError, ValueError):
                print(f"!! merge box p{m['page']} is not four numbers "
                      f"[x0, y0, x1, y1]: {m['box']!r}")
                return 1
            if bx1 <= bx0 or by1 <= by0:
                print(f"!! merge box p{m['page']} is empty or inverted: "
                      f"{m['box']!r}")
                return 1
            r = pymupdf.Rect(bx0, by0, bx1, by1)
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
                           size, lh, color, merge_key, merge_opt, boxed))
        for i in sorted(idxs, reverse=True):
            del page_segs[i]

    over_by_page = {}
    for o in overrides:
        over_by_page.setdefault(o['page'], []).append(o)

    def override_for(pno, text):
        """The override that replaces this whole segment, if any."""
        return next((o for o in over_by_page.get(pno, [])
                     if o['contains'] in text), None)

    missing = []
    for pno, segs in by_page.items():
        for seg in segs:
            text = seg['text'].strip()
            if text in skip:
                continue
            if T.get(seg['core']) is None and not seg['passthrough']:
                # An override replaces the segment's whole span with its
                # own parts, so the plain value is never drawn. Demanding
                # one anyway made the author write a phantom string that
                # exists only to satisfy this check and verify's (row 29).
                if override_for(pno, text):
                    continue
                missing.append((pno, seg['core']))
    if unauthored_merges:
        print(f'FAIL: {len(unauthored_merges)} merges with html null '
              f'(accepted as proposals; author the paragraph or delete the '
              f'entry):')
        for p, first in unauthored_merges[:30]:
            print(f'  p{p}: {first[:70]}')
    if missing:
        print(f'FAIL: {len(missing)} untranslated segments:')
        for p, c in missing[:30]:
            print(f'  p{p}: {c}')
    if missing or unauthored_merges:
        return 1

    # Four roles, each falling back to the nearest one the mapping named.
    # A document set in Times Italic used to come back upright Arial: the
    # extractor recorded italic and retypeset had nowhere to put it.
    f_regular = fonts['regular']
    f_bold = fonts.get('bold') or f_regular
    f_italic = fonts.get('italic') or f_regular
    f_bold_italic = fonts.get('bold_italic') or fonts.get('bold') or f_italic
    font_r = pymupdf.Font(fontfile=f_regular)
    font_b = pymupdf.Font(fontfile=f_bold)
    font_i = pymupdf.Font(fontfile=f_italic)
    font_bi = pymupdf.Font(fontfile=f_bold_italic)
    helv = pymupdf.Font('helv')
    hebo = pymupdf.Font('hebo')
    heit = pymupdf.Font('heit')
    hebi = pymupdf.Font('hebi')

    # Which non-regular roles are the regular face wearing another name.
    # The fallback itself is right — a job with one face must still build —
    # but it is silent, so an author can ask for bold, get regular, and
    # report a faithful page (row 31, measured on canary run 3).
    def _same_file(a, b):
        try:
            return os.path.samefile(a, b)
        except OSError:
            return os.path.abspath(a) == os.path.abspath(b)

    alias_roles = {name for name, path in (('bold', f_bold),
                                           ('italic', f_italic),
                                           ('bold-italic', f_bold_italic))
                   if _same_file(path, f_regular)}
    role_asks = {}

    def note_role(name, key):
        if name in alias_roles:
            role_asks.setdefault(name, []).append(str(key or '?')[:40])

    def note_markup(html, key):
        """The Story engine picks its face from <b>/<i>, not from role()."""
        if re.search(r'<(b|strong)\b', html or '', re.I):
            note_role('bold', key)
        if re.search(r'<(i|em)\b', html or '', re.I):
            note_role('italic', key)

    def role(bold, italic, key=None):
        note_role(_role_name(bold, italic), key)
        if bold and italic:
            return font_bi
        if bold:
            return font_b
        if italic:
            return font_i
        return font_r

    def helv_role(bold, italic):
        if bold and italic:
            return hebi
        if bold:
            return hebo
        if italic:
            return heit
        return helv

    doc = pymupdf.open(stripped)

    bad_notices = []
    for i, n in enumerate(notices):
        text = n.get('text')
        if text is None or not str(text).strip():
            bad_notices.append((i, 'text is null or empty — a notice nobody '
                                   'can read is not a notice'))
            continue
        pno = n.get('page')
        if not isinstance(pno, int) or not 0 <= pno < doc.page_count:
            bad_notices.append((i, f'page {pno!r} is not a page of this '
                                   f'document (0-{doc.page_count - 1})'))
            continue
        try:
            bx0, by0, bx1, by1 = (float(v) for v in n.get('box'))
        except (TypeError, ValueError):
            bad_notices.append((i, f'box is not four numbers '
                                   f'[x0, y0, x1, y1]: {n.get("box")!r}'))
            continue
        if bx1 <= bx0 or by1 <= by0:
            bad_notices.append((i, f'box is empty or inverted: '
                                   f'{n.get("box")!r}'))
    if bad_notices:
        print(f'FAIL: {len(bad_notices)} notice(s) this file cannot place:')
        for i, why in bad_notices[:30]:
            print(f'  notices[{i}]: {why}')
        doc.close()
        return 1

    widg = {p.number: [w.rect for w in p.widgets()] for p in doc}
    arch = pymupdf.Archive('.')
    # CSS URLs need quoted, escaped paths: spaces otherwise cause silent
    # font substitution, and Windows separators are interpreted as escapes.
    def css_url(path):
        escaped = re.sub(r'[\x00-\x1f\x7f"\\]',
                         lambda m: f'\\{ord(m[0]):x} ', PurePath(path).as_posix())
        return f'"{escaped}"'

    css_regular = css_url(f_regular)
    css_bold = css_url(f_bold)
    css_italic = css_url(f_italic)
    css_bold_italic = css_url(f_bold_italic)
    css = (f"@font-face {{font-family: tr; src: url({css_regular});}}"
           f"@font-face {{font-family: trb; src: url({css_bold});}}"
           f"@font-face {{font-family: tri; src: url({css_italic});}}"
           f"@font-face {{font-family: trbi; src: url({css_bold_italic});}}"
           "body {font-family: tr; margin: 0; padding: 0;}"
           "b, strong {font-family: trb; font-weight: normal;}"
           "i, em {font-family: tri; font-style: normal;}"
           "b i, b em, i b, em b, strong i, strong em "
           "{font-family: trbi; font-weight: normal; font-style: normal;}")

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

    def left_limit(pno, seg, segs):
        """How far back a RIGHT-anchored run may grow (row 28).

        A `right` core keeps the source's right edge and grows leftward, so
        its width budget is the room on its left — the nearest same-row
        obstacle's right edge, or the page margin — not the room on its
        right, which is where the field it labels usually sits.
        """
        y0, y1 = seg['bbox'][1], seg['bbox'][3]
        lim = 32.0
        for o in segs:
            if o is seg:
                continue
            if o['bbox'][2] < seg['bbox'][0] + 1 and not (
                    o['bbox'][3] < y0 + 1 or o['bbox'][1] > y1 - 1):
                lim = max(lim, o['bbox'][2])
        for wr in widg.get(pno, []):
            if wr.x1 < seg['bbox'][2] - 1 and not (
                    wr.y1 < y0 + 1 or wr.y0 > y1 - 1):
                if wr.x1 < seg['bbox'][0] + 2:
                    lim = max(lim, wr.x1)
        return lim + 1.5

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
        inline_jobs = []

        def place_rotated(px, py, parts_fs, cint, dx, dy, rtl=False,
                          logical=''):
            rtw = pymupdf.TextWriter(page.rect)
            xx = px
            for item in parts_fs:
                t, f, fsz = item[:3]
                # A fourth element is an explicit advance (a list marker
                # whose body starts at the measured source offset).
                adv = item[3] if len(item) > 3 else f.text_length(t, fsz)
                rtw.append((xx, py), t, font=f, fontsize=fsz,
                           right_to_left=rtl)
                xx += adv
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
            ov = override_for(pno, text)
            if ov:
                for part in ov['parts']:
                    f = role(part.get('bold'), part.get('italic'),
                             ov.get('contains') or t)
                    x = part.get('x', ox)
                    t = part['text']
                    check_glyphs(pno, f, t, ov.get('contains') or t,
                                 _role_name(part.get('bold'),
                                            part.get('italic')))
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
                                            avail, ov.get('contains') or t,
                                            bool(part.get('italic'))))
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
            # The whitespace the source printed after the marker (row 19).
            # A segments.json from before the key gets one space, which is
            # what every build wrote until then: a stale work directory
            # must rebuild, not crash.
            gap = seg.get('gap')
            if gap is None:
                gap = ' '
            mk = marker + gap
            # Row 23: where the body's first glyph was in the source, measured
            # from its characters. The marker is drawn in Helvetica whatever
            # the source font, so Helvetica's advance is right only for a
            # Helvetica-metric source. An old segments.json has no key and
            # keeps the row-19 placement. Scales with the run when it shrinks.
            body_dx = seg.get('body_dx')

            def marker_adv(mfont, fsz):
                if body_dx is not None:
                    return body_dx * (fsz / fs if fs else 1.0)
                return mfont.text_length(mk, fsz)

            def part_adv(i, t, f, fsz):
                if i == 0 and marker:
                    return marker_adv(f, fsz)
                return f.text_length(t, fsz)
            jp = T.get(core)
            if jp is None:
                if not seg['passthrough']:
                    missing.append((pno, core))
                f = helv_role(seg['bold'], seg.get('italic'))
                raw = seg['text'].rstrip()
                check_glyphs(pno, f, raw, raw, 'Helvetica (pass-through)')
                if rot:
                    place_rotated(ox, oy, [(raw, f, fs)],
                                  int(seg.get('color', 0)), dx, dy)
                    continue
                tw.append((mirror_left(ox, f.text_length(raw, fs), page.rect.width),
                           oy), raw, font=f, fontsize=fs)
                continue
            if has_inline_markup(jp) and not rot:
                # Mixed weights inside one line: the Story engine resolves
                # <b>/<i> against the four font roles, the way merges do.
                plain = strip_inline_markup(jp).replace('‖', '')
                check_glyphs(pno, font_r, plain, core, 'regular')
                if re.search(r'<(b|strong)\b', jp, re.I):
                    check_glyphs(pno, font_b, plain, core, 'bold')
                if re.search(r'<(i|em)\b', jp, re.I):
                    check_glyphs(pno, font_i, plain, core, 'italic')
                bx = ox
                if marker:
                    mfont = helv_role(seg['bold'], seg.get('italic'))
                    tw.append((bx, oy), mk, font=mfont, fontsize=fs)
                    bx += marker_adv(mfont, fs)
                avail = right_limit(pno, seg, segs) - bx
                inline_jobs.append((bx, oy, jp.replace('‖', ''),
                                    bool(seg['bold']), bool(seg.get('italic')),
                                    fs, int(seg.get('color', 0)), avail, core,
                                    plain))
                continue
            parts = []
            if marker:
                mk_font = helv_role(seg['bold'], seg.get('italic'))
                check_glyphs(pno, mk_font, mk, core,
                             'Helvetica (list marker)')
                parts.append((mk, mk_font))
            if '‖' in jp:
                bp, rp = jp.split('‖', 1)
                parts.append((bp, role(True, seg.get('italic'), core)))
                parts.append((rp, role(False, seg.get('italic'), core)))
            else:
                parts.append((jp, role(seg['bold'], seg.get('italic'), core)))
            for t, f in parts:
                check_glyphs(pno, f, t, core, _font_label(f, {
                    id(font_r): 'regular', id(font_b): 'bold',
                    id(font_i): 'italic', id(font_bi): 'bold-italic'}))
            wsum = sum(part_adv(i, t, f, fs) for i, (t, f) in enumerate(parts))
            rtl_body = is_rtl_text(jp)
            shaped = needs_shaping(jp)
            def leader_geometry():
                end = seg['bbox'][2] - (
                    helv.text_length(tail, fs) + 2 if tail else 0)
                return end, end - ox - 8

            def fill_leaders(label_end, cur_end):
                """Refill dots from the label's end to the original right edge.

                Anchored right and never longer than the source run, so
                leaders cannot invade a mid-line checkbox gap.
                """
                dw = helv.text_length('.', fs)
                dstart = max(label_end + 1, cur_end - len(dots) * dw)
                n = max(0, int((cur_end - dstart) / dw))
                if n:
                    tw.append((dstart, oy), '.' * n, font=helv, fontsize=fs)
                if tail:
                    check_glyphs(pno, helv, tail, core, 'Helvetica (tail)')
                    tw.append((cur_end + 2, oy), tail, font=helv, fontsize=fs)

            if dots and (shaped or rtl_body) and not mirror and not rot:
                # The label goes through the Story engine (shaped) or a
                # right-to-left TextWriter; the leaders are still ordinary
                # Helvetica dots, so they are refilled here instead of
                # being dropped with the whole dot path.
                cur_end, label_max = leader_geometry()
                body = jp.replace('‖', '')
                cint = int(seg.get('color', 0))
                body_font = role(seg['bold'], seg.get('italic'), core)
                bx = ox
                if marker:
                    mfont = helv_role(seg['bold'], seg.get('italic'))
                    tw.append((bx, oy), mk, font=mfont, fontsize=fs)
                    bx += marker_adv(mfont, fs)
                room = max(label_max - (bx - ox), 1.0)
                if shaped:
                    # Shaping usually narrows a run (ligatures, conjuncts),
                    # so the unshaped measurement is a safe upper bound for
                    # the box; anything wider is scaled by the engine and
                    # caught by the 0.7x gate.
                    width = min(room, body_font.text_length(body, fs))
                    shaped_jobs.append((bx, oy, body, bool(seg['bold']), fs,
                                        cint, width, core,
                                        bool(seg.get('italic'))))
                else:
                    w = body_font.text_length(body, fs)
                    fs2 = fs if w <= room else max(4.0, fs * room / w)
                    if fs and fs2 < fs:
                        consider_ratio(pno, core, fs2 / fs)
                    check_glyphs(pno, body_font, body, core,
                                 _role_name(seg['bold'], seg.get('italic')))
                    rtl_jobs.append((bx, oy, body, body_font, fs2, cint, body))
                    width = body_font.text_length(body, fs2)
                fill_leaders(bx + width, cur_end)
                continue

            if dots and not rtl_body and not shaped and not mirror and not rot:
                cur_end, label_max = leader_geometry()
                fs2 = fs if wsum <= label_max else max(4.0, fs * label_max / wsum)
                if fs and fs2 < fs:
                    consider_ratio(pno, core, fs2 / fs)
                x = ox
                for i, (t, f) in enumerate(parts):
                    tw.append((x, oy), t, font=f, fontsize=fs2)
                    x += part_adv(i, t, f, fs2)
                fill_leaders(x, cur_end)
                continue
            if rot:
                maxw = direction_limit(page, seg, dx, dy)
            elif core in right:
                # Measured against the room it will occupy, not the room to
                # the right of an origin it is not going to keep (row 28).
                maxw = seg['bbox'][2] - left_limit(pno, seg, segs)
            else:
                maxw = right_limit(pno, seg, segs) - ox
            fs2 = fs if wsum <= maxw or wsum == 0 else max(4.0, fs * maxw / wsum)
            if fs and fs2 < fs and not shaped:
                consider_ratio(pno, core, fs2 / fs)
            x = ox
            run_w = sum(part_adv(i, t, f, fs2) for i, (t, f) in enumerate(parts))
            if core in center and not rot:
                cx = (seg['bbox'][0] + seg['bbox'][2]) / 2
                x = max(ox - 200, cx - run_w / 2)
            elif core in right and not rot:
                # Anchor the run's RIGHT edge where the source's was. A
                # longer translation grows leftward instead of over the
                # rule the column was tucked against.
                x = max(0.0, seg['bbox'][2] - run_w)
            if not rot:
                x = mirror_left(x, run_w, page.rect.width)
            if rot:
                if shaped:
                    # Drawing a shaped script flat on a rotated label is the
                    # exact silent defect this program refuses to ship.
                    rotated_shaped.append((pno, core))
                    continue
                place_rotated(x, oy, [(t, f, fs2, part_adv(i, t, f, fs2))
                                      for i, (t, f) in enumerate(parts)],
                              int(seg.get('color', 0)), dx, dy,
                              rtl=rtl_body, logical=jp.replace('‖', ''))
                continue
            if shaped:
                # Marker stays a TextWriter run in Helvetica; the body is
                # shaped at the ORIGINAL size and the engine's own scale
                # feeds the overflow gate.
                bx = x
                if marker:
                    mfont = helv_role(seg['bold'], seg.get('italic'))
                    tw.append((bx, oy), mk, font=mfont, fontsize=fs)
                    bx += marker_adv(mfont, fs)
                shaped_jobs.append((bx, oy, jp.replace('‖', ''), bool(seg['bold']), fs,
                                    int(seg.get('color', 0)), maxw - (bx - x), core,
                                    bool(seg.get('italic'))))
                continue
            if rtl_body:
                logical = jp.replace('‖', '')
                rtl_jobs.append((x, oy, logical,
                                 role(seg['bold'], seg.get('italic'), core), fs2,
                                 int(seg.get('color', 0)), logical))
            else:
                for i, (t, f) in enumerate(parts):
                    tw.append((x, oy), t, font=f, fontsize=fs2)
                    x += part_adv(i, t, f, fs2)
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
        for (ix, iy, body, ibold, iital, ifs, icint, iavail, ikey,
             iplain) in inline_jobs:
            note_markup(body, ikey)
            scale = place_story_line(page, ix, iy, body, ibold, iital, ifs,
                                     icint, iavail, css, arch)
            consider_ratio(pno, ikey, scale)
        for (sx, sy, text, bold, fsz, cint, avail, key, ital) in shaped_jobs:
            scale = place_shaped(page, sx, sy, text, bold, fsz, cint, avail,
                                 css, arch, italic=ital)
            consider_ratio(pno, key, scale)

    for (pno, r, html, align, size, lh, color, merge_key, merge_opt,
         boxed) in merge_jobs:
        plain_html = re.sub(r'<[^>]+>', '', html or '')
        note_markup(html, merge_key)
        check_glyphs(pno, font_r, plain_html, merge_key, 'regular')
        if re.search(r'<(b|strong)\b', html or '', re.I):
            check_glyphs(pno, font_b, plain_html, merge_key, 'bold')
        pw = doc[pno].rect.width
        if mirror:
            r = pymupdf.Rect(pw - r.x1, r.y0, pw - r.x0, r.y1)
            align = {'left': 'right', 'right': 'left'}.get(align, align)
        # A union bbox is a measurement of ink and runs tight, so it gets a
        # little slop; an authored box is an instruction and is used as
        # given.
        rect = (r if boxed
                else pymupdf.Rect(r.x0, r.y0 - 0.5, r.x1 + 1.5, r.y1 + 1.5))
        hexcol = f'#{color:06x}'
        h = (f'<div style="font-size:{size*0.98:.1f}px; line-height:{lh}; '
             f'color:{hexcol}; text-align:{align};">{html}</div>')
        _, scale = doc[pno].insert_htmlbox(rect, h, css=css, archive=arch, scale_low=0)
        consider_ratio(pno, merge_key, scale, opted=merge_opt)
        plain = re.sub(r'<[^>]+>', '', html)
        if is_rtl_text(plain) or needs_shaping(plain):
            wrap_last_stream_actualtext(doc[pno], plain)

    # The notice compliance.md requires is the one thing the author has to
    # add that is not the translation of an existing string. Four of five
    # canary runs wrote their own script for it, each re-deriving fonts,
    # placement and the canonical-layer rewrite by hand (lane B, P7). It
    # goes through everything a merge goes through; only the rect is the
    # author's rather than the source's, because only the author can see
    # what the page has room for.
    for i, n in enumerate(notices):
        pno = n['page']
        parts = [p for p in str(n['text']).split('‖')]
        size = float(n.get('size') or NOTICE_SIZE)
        key = f'notices[{i}]'
        plain = ' '.join(p.strip() for p in parts if p.strip())
        check_glyphs(pno, font_r, plain, key, 'regular')
        if n.get('bold_lead'):
            note_role('bold', key)
            check_glyphs(pno, font_b, parts[0], key, 'bold')
            body = (f'<b>{htmlmod.escape(parts[0].strip())}</b> '
                    + ' '.join(htmlmod.escape(p.strip())
                               for p in parts[1:] if p.strip()))
        else:
            body = ' '.join(htmlmod.escape(p.strip())
                            for p in parts if p.strip())
        r = pymupdf.Rect(*(float(v) for v in n['box']))
        if mirror:
            pw = doc[pno].rect.width
            r = pymupdf.Rect(pw - r.x1, r.y0, pw - r.x0, r.y1)
        h = (f'<div style="font-size:{size:.1f}px; line-height:{NOTICE_LH}; '
             f'color:#000000; text-align:left;">{body}</div>')
        _, scale = doc[pno].insert_htmlbox(r, h, css=css, archive=arch,
                                           scale_low=0)
        consider_ratio(pno, key, scale)
        if is_rtl_text(plain) or needs_shaping(plain):
            wrap_last_stream_actualtext(doc[pno], plain)
    if notices:
        print(f'notices: placed {len(notices)} on '
              f'{len({n["page"] for n in notices})} page(s); look at the '
              f'render — no gate judges where a notice sits')

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

    for name in ('bold', 'italic', 'bold-italic'):
        asks = role_asks.get(name)
        if not asks:
            continue
        shown = ', '.join(dict.fromkeys(asks))
        print(f'font roles: "{name}" resolved to the regular face; '
              f'{len(asks)} run(s) asked for it ({shown[:100]}'
              f'{"…" if len(shown) > 100 else ""}). Name it in the delivery '
              f'or give the role its own file.')

    if scaled:
        print(f'scaled runs ({len(scaled)}) — reword them or name them in '
              f'the delivery:')
        for r in sorted(scaled, key=lambda r: (r['page'], r['ratio']))[:30]:
            print(f'  p{r["page"]} {r["ratio"]:.2f}x: {r["key"][:60]}')
        if len(scaled) > 30:
            print(f'  … {len(scaled) - 30} more in {SCALE_REPORT}')
    report = os.path.join(os.path.dirname(os.path.abspath(out)), SCALE_REPORT)
    try:
        with open(report, 'w', encoding='utf-8') as f:
            json.dump(sorted(scaled, key=lambda r: (r['page'], r['key'])), f,
                      ensure_ascii=False, indent=1)
    except OSError as exc:
        print(f'  (could not write {SCALE_REPORT}: {exc})')

    doc.ez_save(out)
    doc.close()

    # The glyphs are right either way; this is the text layer.
    placed = [t for t in T.values() if isinstance(t, str)]
    placed.extend(re.sub(r'<[^>]+>', '', m.get('html') or '') for m in merges)
    for o in overrides:
        placed.extend(part.get('text') or '' for part in o.get('parts') or [])
    placed.extend(str(n.get('text') or '').replace('‖', ' ') for n in notices)
    for seg in segments:
        placed.extend(((seg.get('marker') or '')
                       + (' ' if seg.get('gap') is None else seg['gap']),
                       seg.get('tail') or ''))
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
