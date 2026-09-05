#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drive the shipped strip / extract / retypeset / verify / field-font stages.

Fixtures are tiny born-digital PDFs constructed here. Tests import the
scripts (not a copy) and start from an original file — never from a
pre-stripped stand-in when checking strip.
"""
import io
import json
import os
import re
import shutil
import string
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stdout
from pathlib import Path

import pikepdf
import pymupdf

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
CORPUS = Path(__file__).resolve().parents[1] / 'corpus'
CHOICE_SENTENCE = 'Choose fruit from the list and a color below.'
CHOICE_TARGET = 'Elija fruta de la lista y un color abajo.'
sys.path.insert(0, str(SCRIPTS))

import bilingual  # noqa: E402
import compare  # noqa: E402
import extract_segments  # noqa: E402
import pipeline  # noqa: E402
import render_pages  # noqa: E402
import field_fonts  # noqa: E402
import prepare_font  # noqa: E402
import qa_check  # noqa: E402
import retypeset  # noqa: E402
import strip_text  # noqa: E402
import verify  # noqa: E402

SOURCE_SENTENCE = 'The applicant must file this form today.'
# Spaces and an ASCII hyphen: exactly the characters a reverse-mapped
# ToUnicode turns into NBSP and a soft hyphen.
DRIFT_TARGET = 'Vease Form W-2 y no-custodio hoy.'
TARGET_SENTENCE = 'El solicitante debe presentar este formulario hoy.'
EMPTY_CORE = 'are living with me'
EMPTY_HAPPY = 'viven conmigo ahora'
URI = 'https://example.gov/forms'
BOOKMARK = 'Section One'
WHITE = 16777215


AR_TARGET = 'طلب المساعدة'
HE_TARGET = 'בקשת סיוע'
AR_SOURCE = 'Need help today.'
HE_SOURCE = 'Please send aid now.'


# Fonts fetched by tools/fetch_test_fonts.py. Preferred over whatever the
# host happens to ship, so the shaping tests behave the same everywhere
# instead of SKIPping on Linux.
VENDORED_FONTS = Path(__file__).resolve().parent / 'fonts'


def vendored(*names):
    for name in names:
        path = VENDORED_FONTS / name
        if path.is_file():
            return path
    return None


def _covers(path, *chars):
    f = pymupdf.Font(fontfile=str(path))
    return all(f.has_glyph(ord(c)) for c in chars)


SYSTEM_FONTS = [
    Path(r'C:\Windows\Fonts\arial.ttf'),
    Path(r'C:\Windows\Fonts\Arial.ttf'),
    Path(r'C:\Windows\Fonts\calibri.ttf'),
    Path(r'C:\Windows\Fonts\segoeui.ttf'),
    Path(r'C:\Windows\Fonts\Nirmala.ttf'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
    # Local convenience only: never let a gitignored font decide whether
    # the suite is green (Arial's cmap reports soft hyphens and NBSPs,
    # which is exactly what the gates must cope with).
    Path(__file__).resolve().parents[2] / 'work' / 'NotoSansJP-Regular-full.ttf',
]


def font_candidates():
    """Fetched faces first, then whatever the host happens to ship."""
    out = []
    if VENDORED_FONTS.is_dir():
        out.extend(sorted(VENDORED_FONTS.glob('*.ttf')))
    out.extend(p for p in SYSTEM_FONTS if p.is_file())
    return out


def find_font_for(*texts, what=None):
    """A TTF covering every character of texts.

    Asking for one font that covers two unrelated scripts is how these
    tests used to SKIP on Linux: Arial happens to carry Arabic AND Hebrew,
    no Noto face does, and each test only ever needs one of them.
    """
    want = sorted({c for t in texts for c in t if not c.isspace()})
    for path in font_candidates():
        if _covers(path, *want):
            return path
    raise unittest.SkipTest(
        f'no TTF covering {what or "".join(want)[:40]}')


def find_rtl_font():
    """Arabic. Hebrew-only tests ask for HE_TARGET explicitly."""
    return find_font_for(AR_TARGET, AR_PHRASE, what='Arabic')


# The Latin repertoire the constructed fixtures actually use. "First
# candidate wins" is not good enough: with the fetched faces present,
# sorted() puts Noto Naskh Arabic first, and a face with no Latin fails
# the glyph-coverage gate on every ordinary test.
LATIN_SAMPLE = ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                '0123456789.,:;!?()[]{}$%&*+=/\\@#\'"-_ '
                'áéíóúñüàèìòùâêîôûäëïöüçÁÉÍÓÚÑ')


def find_test_font():
    return find_font_for(LATIN_SAMPLE, what='Latin')


def write_mapping(path, translations, font, skip=None, allow_scale=None,
                  mirror=False, allow_translate=None, lang=None, right=None,
                  italic=None, center=None):
    data = {
        'fonts': {'regular': str(font), 'bold': str(font),
                  'italic': str(italic or font),
                  'bold_italic': str(italic or font)},
        'translations': translations,
        'merges': [],
        'overrides': [],
        'center': list(center) if center is not None else [],
        # Widget chrome ("Print") is drawn from /MK /CA, not page text.
        'skip': list(skip) if skip is not None else ['Print'],
    }
    if allow_scale is not None:
        data['allow_scale'] = list(allow_scale)
    if mirror:
        data['mirror'] = True
    if allow_translate is not None:
        data['allow_translate'] = list(allow_translate)
    if lang is not None:
        data['lang'] = lang
    if right is not None:
        data['right'] = list(right)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def form_translations():
    return {
        SOURCE_SENTENCE: TARGET_SENTENCE,
        'CONFIDENTIAL': 'CONFIDENCIAL',
        'before        after': 'antes        despues',
        'Public assistance': 'Ayuda',
        'See Form W-2 and Schedule C.': 'Vease Form W-2 y Schedule C.',
        'Write "Question 1" at the top.': 'Escriba "Question 1" arriba.',
        'Name:': 'Nombre:',
        URI: URI,
    }


def build_form_pdf(path, with_dots=True):
    """Fillable one-page form: running text, white-on-dark, numbers, inner
    gap, dot leaders + mid-line checkbox, text field, link, bookmark, rule."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), SOURCE_SENTENCE, fontsize=12)
    page.draw_rect(pymupdf.Rect(72, 100, 540, 128), fill=(0.1, 0.2, 0.5))
    page.insert_text((80, 120), 'CONFIDENTIAL', fontsize=14, color=(1, 1, 1))
    page.insert_text((72, 160), '12345', fontsize=11)
    page.insert_text((72, 200), 'before' + (' ' * 8) + 'after', fontsize=11)
    page.insert_text((72, 230), 'See Form W-2 and Schedule C.', fontsize=11)
    page.insert_text((72, 250), 'Write "Question 1" at the top.', fontsize=11)
    page.insert_text((72, 270), 'Name:', fontsize=11)
    page.insert_text((200, 270), 'Name:', fontsize=11)
    if with_dots:
        page.insert_text((72, 300), 'Public assistance ' + ('.' * 60) + ' $',
                         fontsize=11)
        cb = pymupdf.Widget()
        cb.field_name = 'Agree'
        cb.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
        # Between a short translation ("Ayuda") and the original right-anchored
        # dots — naive refill from the short label to $ would cover this rect.
        cb.rect = pymupdf.Rect(120, 288, 134, 302)
        page.add_widget(cb)
    page.draw_line(pymupdf.Point(72, 350), pymupdf.Point(400, 350),
                   color=(0, 0, 0), width=1.5)
    tf = pymupdf.Widget()
    tf.field_name = 'ApplicantName'
    tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    tf.rect = pymupdf.Rect(72, 400, 280, 418)
    page.add_widget(tf)
    btn = pymupdf.Widget()
    btn.field_name = 'PrintForm'
    btn.field_type = pymupdf.PDF_WIDGET_TYPE_BUTTON
    btn.field_flags = 1 << 16
    btn.rect = pymupdf.Rect(400, 400, 520, 424)
    btn.button_caption = 'Print'
    page.add_widget(btn)
    page.insert_link({
        'kind': pymupdf.LINK_URI,
        'from': pymupdf.Rect(72, 500, 280, 516),
        'uri': URI,
    })
    page.insert_text((72, 512), URI, fontsize=9)
    doc.set_toc([[1, BOOKMARK, 1]])
    doc.save(path)
    doc.close()


SQUEEZE_CORE = 'Hi'
SQUEEZE_LONG = (
    'This is a very long translation that will not fit in the gap '
    'before the widget and must shrink a lot to squeeze in.'
)


def build_squeeze_pdf(path):
    """Short core, then a text field that leaves little room to the right."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), SQUEEZE_CORE, fontsize=12)
    tf = pymupdf.Widget()
    tf.field_name = 'X'
    tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    tf.rect = pymupdf.Rect(200, 68, 280, 88)
    page.add_widget(tf)
    doc.save(path)
    doc.close()


def build_plain_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), SOURCE_SENTENCE, fontsize=12)
    page.draw_rect(pymupdf.Rect(72, 120, 200, 140), color=(0, 0, 0), width=1)
    doc.save(path)
    doc.close()


LONG_CAPTION = 'X' * 40
SHORT_CAPTION = 'OK'
NARROW_BTN = 'TinyBtn'


def build_narrow_button_pdf(path):
    """One 60-pt-wide pushbutton plus a translatable sentence and a text field."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), SOURCE_SENTENCE, fontsize=12)
    tf = pymupdf.Widget()
    tf.field_name = 'ApplicantName'
    tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    tf.rect = pymupdf.Rect(72, 200, 280, 218)
    page.add_widget(tf)
    btn = pymupdf.Widget()
    btn.field_name = NARROW_BTN
    btn.field_type = pymupdf.PDF_WIDGET_TYPE_BUTTON
    btn.field_flags = 1 << 16
    btn.rect = pymupdf.Rect(72, 400, 132, 424)  # width 60, height 24
    btn.button_caption = SHORT_CAPTION
    page.add_widget(btn)
    doc.save(path)
    doc.close()


def build_empty_target_pdf(path):
    """Two cores: one real translation, one that tests empty mapping values."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), SOURCE_SENTENCE, fontsize=12)
    page.insert_text((72, 110), EMPTY_CORE, fontsize=12)
    page.draw_rect(pymupdf.Rect(72, 140, 200, 160), color=(0, 0, 0), width=1)
    doc.save(path)
    doc.close()


QUOTE_LINE = 'Write "Attachment A" at the top.'
SCHED_LINE = 'Please attach Schedule Q.'
KEEP_IDENT_TR = {
    QUOTE_LINE: 'Escriba "Attachment A" arriba.',
    SCHED_LINE: 'Adjunte Schedule Q.',
}
VANISH_IDENT_TR = {
    QUOTE_LINE: 'Escriba "Anexo A" arriba.',
    SCHED_LINE: 'Adjunte Anexo Q.',
}


def build_identifier_pdf(path):
    """LTR page whose extractor must see quoted Attachment A and Schedule Q."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), QUOTE_LINE, fontsize=12)
    page.insert_text((72, 110), SCHED_LINE, fontsize=12)
    doc.save(path)
    doc.close()


NARROW_WORDS = ['Gross', 'Taxes', 'Net', 'Hours', 'Rate']
WIDE_LINES = [
    'The court will review every declaration filed before the hearing date',
    'and the clerk will mail one conformed copy back to each party listed',
    'so that everybody knows which documents the judge actually received.',
]


def build_narrow_column_pdf(path):
    """A 5-row pay-stub column beside a wide paragraph and wide list items."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    for i, word in enumerate(NARROW_WORDS):
        page.insert_text((72, 80 + 14 * i), word, fontsize=10)
    for i, line in enumerate(WIDE_LINES):
        page.insert_text((220, 80 + 14 * i), line, fontsize=8)
    # Sibling list items: same left edge, stacked, but each is wider than
    # the 90 pt threshold. The warning must not reach for these.
    for i, item in enumerate(['a. First remedy requested by the applicant',
                              'b. Second remedy requested by the applicant',
                              'c. Third remedy requested by the applicant']):
        page.insert_text((72, 300 + 16 * i), item, fontsize=9)
    doc.save(path)
    doc.close()


WIDGET_LABEL = 'Real page label here.'
WIDGET_DEFAULT = 'LEAKED DEFAULT VALUE'
WIDGET_TIP = 'Enter your full legal name'
FRUIT_TIP = 'Pick one fruit'
FRUIT_OPTS = ['Apple', 'Pear', 'Plum']


def build_widget_text_pdf(path):
    """A page label plus widgets carrying /TU, /Opt and a /V default."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((50, 50), WIDGET_LABEL, fontsize=11)
    tf = pymupdf.Widget()
    tf.field_name = 'Applicant'
    tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    tf.rect = pymupdf.Rect(50, 80, 250, 100)
    tf.field_value = WIDGET_DEFAULT
    tf.field_label = WIDGET_TIP
    page.add_widget(tf)
    cb = pymupdf.Widget()
    cb.field_name = 'Fruit'
    cb.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
    cb.rect = pymupdf.Rect(50, 120, 250, 140)
    cb.choice_values = list(FRUIT_OPTS)
    cb.field_value = FRUIT_OPTS[0]
    cb.field_label = FRUIT_TIP
    page.add_widget(cb)
    doc.save(path)
    doc.close()


def retranslate_opt_exports(src, dst, mapping):
    """Copy src to dst with /Opt entries replaced by translated exports.

    This is the defect the parity gate exists for: a well-meaning rewrite
    that translates the whole option instead of its display half.
    """
    pdf = pikepdf.open(src)
    try:
        for page in pdf.pages:
            for a in page.get('/Annots', []):
                if a.get('/Opt') is None:
                    continue
                a.Opt = pikepdf.Array(
                    [pikepdf.String(mapping.get(str(e), str(e)))
                     for e in a.Opt])
        pdf.save(dst)
    finally:
        pdf.close()


ROT_ROWS = [
    # (x, y, text, rotate, expected line dir)
    (60, 60, 'Application for benefits', 0, (1.0, 0.0)),
    (360, 340, 'FOR OFFICE USE ONLY', 90, (0.0, -1.0)),
    (40, 300, 'Filed copy', 270, (0.0, 1.0)),
    (330, 30, 'Void if altered', 180, (-1.0, 0.0)),
]
ROT_TR = {
    'Application for benefits': 'Solicitud de prestaciones',
    'FOR OFFICE USE ONLY': 'USO OFICIAL',
    'Filed copy': 'Copia',
    'Void if altered': 'Nulo si se altera',
}


def build_rotated_text_pdf(path):
    """One flat row plus a 90, a 270 and a 180 degree line on one page."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=400)
    for x, y, text, rot, _ in ROT_ROWS:
        page.insert_text((x, y), text, fontsize=10, rotate=rot)
    doc.save(path)
    doc.close()


def line_dirs(pdf_path):
    """{text: (dx, dy)} of every line in a PDF, rounded."""
    doc = pymupdf.open(pdf_path)
    try:
        out = {}
        for page in doc:
            for b in page.get_text('dict')['blocks']:
                if b['type'] != 0:
                    continue
                for line in b['lines']:
                    text = verify.normalize_ws_nbsp(
                        ''.join(sp['text'] for sp in line['spans']))
                    if text:
                        out[text] = (round(line['dir'][0], 3),
                                     round(line['dir'][1], 3))
        return out
    finally:
        doc.close()


def widget_map(pdf_path):
    doc = pymupdf.open(pdf_path)
    out = {w.field_name: (w.field_type_string, pymupdf.Rect(w.rect))
           for p in doc for w in p.widgets()}
    doc.close()
    return out


def dot_chars_overlap_widget(pdf_path, field_name):
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    widget = next(w for w in page.widgets() if w.field_name == field_name)
    wr = widget.rect
    hit = False
    raw = page.get_text('rawdict')
    for block in raw['blocks']:
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                for ch in span.get('chars', []):
                    if ch.get('c') != '.':
                        continue
                    bb = ch.get('bbox') or span['bbox']
                    r = pymupdf.Rect(bb)
                    if r.intersects(wr):
                        hit = True
                        break
    doc.close()
    return hit


NESTED_PAGE = 'Page body text stays on the page.'
NESTED_MID = 'Middle band text lives in a Form XObject.'
NESTED_INNER = 'Inner letterhead text is two XObjects deep.'


def build_nested_xobject_pdf(path, inherit_resources=False):
    """Page text plus a Form XObject that contains text AND a second Form
    XObject with text (two levels deep). A vector rule and a text field sit
    on the page so tests can assert graphics and widgets survive. With
    inherit_resources the page's /Resources move to the /Pages node, which
    some producers do and which a per-page walker never sees."""
    inner = pymupdf.open()
    ip = inner.new_page(width=200, height=100)
    ip.insert_text((10, 50), NESTED_INNER, fontsize=9)
    mid = pymupdf.open()
    mp = mid.new_page(width=300, height=200)
    mp.show_pdf_page(pymupdf.Rect(20, 20, 280, 120), inner, 0)
    mp.insert_text((10, 190), NESTED_MID, fontsize=9)
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), NESTED_PAGE, fontsize=12)
    page.show_pdf_page(pymupdf.Rect(72, 100, 372, 300), mid, 0)
    page.draw_line(pymupdf.Point(72, 320), pymupdf.Point(400, 320),
                   color=(0, 0, 0), width=1.5)
    tf = pymupdf.Widget()
    tf.field_name = 'ApplicantName'
    tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    tf.rect = pymupdf.Rect(72, 340, 280, 358)
    page.add_widget(tf)
    doc.save(path)
    doc.close()
    mid.close()
    inner.close()
    if inherit_resources:
        # pikepdf/QPDF push inherited attributes back onto the page when
        # saving, so the move has to be PyMuPDF xref surgery to survive on
        # disk. MuPDF resolves the inheritance when rendering/extracting.
        doc = pymupdf.open(path)
        page = doc[0]
        kind, val = doc.xref_get_key(page.xref, 'Resources')
        assert kind != 'null', 'page has no /Resources to move'
        parent_xref = int(doc.xref_get_key(page.xref, 'Parent')[1].split()[0])
        doc.xref_set_key(parent_xref, 'Resources', val)
        doc.xref_set_key(page.xref, 'Resources', 'null')
        moved = path + '.inherited.pdf'
        doc.save(moved)
        doc.close()
        os.replace(moved, path)


OCR_HEADING = 'NOTICE OF HEARING'
OCR_BODY = 'You must appear in court on the date shown below.'


def _render_text_png(path, heading, body, dpi=150):
    tmp = pymupdf.open()
    page = tmp.new_page(width=612, height=792)
    page.insert_text((72, 80), heading, fontsize=20)
    page.insert_text((72, 120), body, fontsize=12)
    page.get_pixmap(dpi=dpi).save(path)
    tmp.close()


def build_ocr_layer_pdf(path):
    """A scan that was OCR'd: a full-page image of the text plus an invisible
    (render mode 3) text layer at the same positions. The words the reader
    sees are pixels; the text layer only makes them searchable."""
    png = path + '.scan.png'
    _render_text_png(png, OCR_HEADING, OCR_BODY)
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(page.rect, filename=png)
    page.insert_text((72, 80), OCR_HEADING, fontsize=20, render_mode=3)
    page.insert_text((72, 120), OCR_BODY, fontsize=12, render_mode=3)
    doc.save(path)
    doc.close()
    os.remove(png)


def build_text_over_image_pdf(path):
    """Real, visible text over a full-page light background image, as in a
    brochure. Must NOT be mistaken for an OCR layer."""
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 260), False)
    pix.clear_with(236)
    png = path + '.bg.png'
    pix.save(png)
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(page.rect, filename=png)
    page.insert_text((72, 80), OCR_HEADING, fontsize=20)
    page.insert_text((72, 120), OCR_BODY, fontsize=12)
    doc.save(path)
    doc.close()
    os.remove(png)


JA_LINES = ['申立人は以下の情報を正確に記入してください。', '氏名：', '住所：', '署名']
JA_TARGETS = {
    '申立人は以下の情報を正確に記入してください。':
        'The petitioner must complete the information below accurately.',
    '氏名：': 'Name:',
    '住所：': 'Address:',
    '署名': 'Signature',
}
AR_LINES = ['طلب المساعدة القانونية', 'الاسم:', 'العنوان:']
AR_TARGETS_EN = ['Legal aid request', 'Name:', 'Address:']


def cjk_font_file(tmp):
    """Write the bundled CJK font (Droid Sans Fallback) to a file for retypeset."""
    path = os.path.join(tmp, 'cjk.ttf')
    with open(path, 'wb') as fh:
        fh.write(pymupdf.Font('cjk').buffer)
    return path


def build_ja_source_pdf(path):
    """A Japanese-language source document, set with the bundled CJK font."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    font = pymupdf.Font('cjk')
    tw = pymupdf.TextWriter(page.rect)
    for i, text in enumerate(JA_LINES):
        tw.append((60, 80 + 30 * i), text, font=font, fontsize=11)
    tw.write_text(page)
    doc.save(path)
    doc.close()


def build_ar_source_pdf(path, fontfile):
    """An Arabic-language source document set through the HarfBuzz path so the
    letters are joined like a real Arabic PDF."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    base = os.path.basename(str(fontfile))
    css = "@font-face {font-family: t; src: url(%s);} body {font-family: t;}" % base
    arch = pymupdf.Archive(os.path.dirname(str(fontfile)))
    for i, text in enumerate(AR_LINES):
        y = 80 + 40 * i
        page.insert_htmlbox(
            pymupdf.Rect(60, y, 500, y + 24),
            '<div style="font-size:12px;direction:rtl;text-align:right">%s</div>' % text,
            css=css, archive=arch)
    doc.save(path)
    doc.close()


AR_PHRASE = 'السلام عليكم ورحمة الله'
DV_PHRASE = 'नमस्ते क्षत्रिय'
SHAPE_SOURCE = 'Peace be upon you and mercy'
# Arabic Presentation Forms-B: four-form groups start at these code points
# (isolated, final, initial, medial). Initial/medial forms only appear when
# the letters were joined by a shaper.
_AR_GROUPS = (0xFE89, 0xFE8F, 0xFE95, 0xFE99, 0xFE9D, 0xFEA1, 0xFEA5, 0xFEB1,
              0xFEB5, 0xFEB9, 0xFEBD, 0xFEC1, 0xFEC5, 0xFEC9, 0xFECD, 0xFED1,
              0xFED5, 0xFED9, 0xFEDD, 0xFEE1, 0xFEE5, 0xFEE9, 0xFEF1)
AR_CONNECTED_FORMS = {b + 2 for b in _AR_GROUPS} | {b + 3 for b in _AR_GROUPS}


def find_devanagari_font():
    fetched = vendored('NotoSansDevanagari-Regular.ttf')
    if fetched:
        return fetched
    for name in ('Nirmala.ttc', 'Nirmala.ttf', 'mangal.ttf', 'Mangal.ttf'):
        path = Path(r'C:\Windows\Fonts') / name
        if path.is_file():
            return path
    for path in (Path('/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf'),
                 Path('/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf')):
        if path.is_file():
            return path
    raise unittest.SkipTest('no Devanagari-capable TTF')


def raw_codepoints(page, clip=None):
    out = []
    flags = pymupdf.TEXTFLAGS_RAWDICT | pymupdf.TEXT_IGNORE_ACTUALTEXT
    for block in page.get_text('rawdict', clip=clip, flags=flags)['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                out.extend(ord(c['c']) for c in span['chars'])
    return out


def first_line_geometry(page):
    """(bbox, origin) of the first text line on the page."""
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            span = line['spans'][0]
            return pymupdf.Rect(line['bbox']), span['origin']
    return None, None


def build_one_line_pdf(path, text=SHAPE_SOURCE, x=72, y=80, size=12):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((x, y), text, fontsize=size)
    # A rule just under the baseline: a shaped run must not paint over it.
    page.draw_line(pymupdf.Point(60, y + 4), pymupdf.Point(300, y + 4), color=(0, 0, 0), width=1)
    doc.save(path)
    doc.close()


def render_region(page, rect, dpi=100):
    return bytes(page.get_pixmap(dpi=dpi, clip=rect).samples)


def ink_left_edge(page, rect, dpi=144):
    """Left edge of the drawn ink inside rect, in points, or None.

    A span's reported bbox is font metadata, not ink: Noto Naskh Arabic's
    connecting tails reach left of the glyph origin, so MuPDF reports a
    box 8 pt right of where the letters actually are, while Arial reports
    one that matches. Placement tests must measure what the reader sees.
    """
    pix = page.get_pixmap(dpi=dpi, clip=rect)
    w, h, n = pix.width, pix.height, pix.n
    buf = bytes(pix.samples)
    scale = dpi / 72.0
    for x in range(w):
        for y in range(h):
            if buf[(y * w + x) * n] < 128:
                return rect.x0 + x / scale
    return None


def pixel_diff(a, b):
    return sum(1 for x, y in zip(a, b) if abs(x - y) > 40)


OVERRIDE_CORE = 'Public aid'
OVERRIDE_LINE = 'd. ' + OVERRIDE_CORE + (' ' * 8) + '.... $'
OVERRIDE_OTHER = 'Other text line.'


def build_override_pdf(path):
    """One inner-gap row `d. Public aid      [cb] .... $` plus a plain line."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), OVERRIDE_LINE, fontsize=11)
    cb = pymupdf.Widget()
    cb.field_name = 'Aid'
    cb.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
    cb.rect = pymupdf.Rect(150, 88, 164, 102)
    page.add_widget(cb)
    page.insert_text((72, 140), OVERRIDE_OTHER, fontsize=11)
    doc.save(path)
    doc.close()


def override_mapping(path, font, parts):
    """Mapping for build_override_pdf with one override on the inner-gap row."""
    data = {
        'fonts': {'regular': str(font), 'bold': str(font)},
        'translations': {OVERRIDE_CORE: 'Ayuda', OVERRIDE_OTHER: 'Otra linea.'},
        'merges': [],
        'overrides': [{'page': 0, 'contains': OVERRIDE_CORE, 'parts': parts}],
        'center': [],
        'skip': [],
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


PARTS_KEEP = [{'text': 'd. Ayuda', 'x': 72.0}, {'text': '.... $', 'x': 180.0}]
PARTS_DROP = [{'text': 'Ayuda', 'x': 72.0}]


class ImportSafeTests(unittest.TestCase):
    def test_field_fonts_and_compare_import_without_argv(self):
        # These two historically read sys.argv at import time, which crashes
        # any harness whose argv is not "in.pdf font.ttf out.pdf".
        self.assertTrue(callable(field_fonts.field_fonts))
        self.assertTrue(callable(field_fonts.main))
        self.assertTrue(callable(compare.compare))
        self.assertTrue(callable(compare.main))
        self.assertTrue(callable(strip_text.strip_text))
        self.assertTrue(callable(extract_segments.extract_segments))
        self.assertTrue(callable(retypeset.retypeset))
        self.assertTrue(callable(verify.verify))
        self.assertTrue(callable(prepare_font.prepare_font))


class StripTests(unittest.TestCase):
    def test_source_text_gone_widget_and_vector_remain(self):
        font = find_test_font()  # noqa: F841 — environment check
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_form_pdf(src)
            before = pymupdf.open(src)
            self.assertIn(SOURCE_SENTENCE, before[0].get_text())
            n_draw = len(before[0].get_drawings())
            before.close()
            report = strip_text.strip_text(src, dst)
            self.assertGreater(report['pages'][0]['text_blocks_removed'], 0)
            after = pymupdf.open(dst)
            text = after[0].get_text()
            self.assertNotIn(SOURCE_SENTENCE, text)
            self.assertNotIn('CONFIDENTIAL', text)
            names = {w.field_name for w in after[0].widgets()}
            self.assertIn('ApplicantName', names)
            self.assertIn('Agree', names)
            self.assertGreaterEqual(len(after[0].get_drawings()), n_draw)
            after.close()

    def test_button_captions_rewritten_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            with_ap = os.path.join(tmp, 'with_ap.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_form_pdf(src)
            orig_names = set(widget_map(src))
            import pikepdf
            pdf = pikepdf.open(src)
            try:
                for a in pdf.pages[0].get('/Annots', []):
                    if str(a.get('/T', '')) == 'PrintForm':
                        a.AP = pikepdf.Dictionary(
                            N=pdf.make_stream(b'BT /Helv 10 Tf (Print) Tj ET'))
                pdf.save(with_ap)
            finally:
                pdf.close()
            report = strip_text.strip_text(
                with_ap, dst, captions={'PrintForm': 'Imprimir'})
            self.assertIn('PrintForm', report['rewritten_captions'])
            self.assertEqual(set(widget_map(dst)), orig_names)
            pdf = pikepdf.open(dst)
            found = False
            for a in pdf.pages[0].get('/Annots', []):
                if str(a.get('/T', '')) == 'PrintForm':
                    self.assertEqual(str(a.MK.CA), 'Imprimir')
                    self.assertTrue('/AP' not in a)
                    found = True
            pdf.close()
            self.assertTrue(found)


class StripCompletenessTests(unittest.TestCase):
    """Goal 13: strip must leave no page text, however deep it hides, and
    must refuse (and write nothing) when it cannot prove that."""

    def _assert_clean(self, dst, report):
        self.assertEqual(report['leftover_text'], [], msg=report)
        self.assertEqual(strip_text.leftover_page_text(dst), [])
        after = pymupdf.open(dst)
        text = after[0].get_text()
        for s in (NESTED_PAGE, NESTED_MID, NESTED_INNER):
            self.assertNotIn(s, text)
        self.assertIn('ApplicantName', {w.field_name for w in after[0].widgets()})
        self.assertGreaterEqual(len(after[0].get_drawings()), 1)
        after.close()

    def test_nested_xobject_text_is_stripped(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_nested_xobject_pdf(src)
            before = pymupdf.open(src)
            for s in (NESTED_PAGE, NESTED_MID, NESTED_INNER):
                self.assertIn(s, before[0].get_text())
            before.close()
            report = strip_text.strip_text(src, dst)
            self._assert_clean(dst, report)
            depths = {x.get('depth') for x in report['form_xobjects_stripped']}
            self.assertIn(2, depths, msg=report['form_xobjects_stripped'])

    def test_inherited_resources_xobject_text_is_stripped(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_nested_xobject_pdf(src, inherit_resources=True)
            doc = pymupdf.open(src)
            self.assertEqual(doc.xref_get_key(doc[0].xref, 'Resources')[0], 'null')
            parent_xref = int(doc.xref_get_key(doc[0].xref, 'Parent')[1].split()[0])
            self.assertNotEqual(doc.xref_get_key(parent_xref, 'Resources')[0], 'null')
            for t in (NESTED_PAGE, NESTED_MID, NESTED_INNER):
                self.assertIn(t, doc[0].get_text())
            doc.close()
            report = strip_text.strip_text(src, dst)
            self._assert_clean(dst, report)

    def test_nested_xobject_text_round_trips_through_retypeset(self):
        font = find_test_font()
        targets = {
            NESTED_PAGE: 'El cuerpo del texto se queda en la pagina.',
            NESTED_MID: 'La banda central vive en un Form XObject.',
            NESTED_INNER: 'El membrete interior esta dos XObjects abajo.',
        }
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_nested_xobject_pdf(src, inherit_resources=True)
            strip_text.strip_text(src, dst)
            res = extract_segments.extract_segments(src, outdir=tmp)
            origins = {seg['core']: seg['origin'] for seg in res['segments']}
            self.assertEqual(set(origins), set(targets), msg=list(origins))
            write_mapping(tr, targets, font, skip=[])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(dst, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            placed = {}
            doc = pymupdf.open(out)
            for b in doc[0].get_text('dict')['blocks']:
                for line in b.get('lines', []):
                    for span in line['spans']:
                        placed[verify.normalize_ws_nbsp(span['text']).strip()] = span['origin']
            doc.close()
            for core, target in targets.items():
                self.assertIn(target, placed, msg=list(placed))
                ox, oy = origins[core]
                px, py = placed[target]
                self.assertAlmostEqual(ox, px, delta=1.0, msg=target)
                self.assertAlmostEqual(oy, py, delta=1.0, msg=target)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, source_words_from=os.path.join(tmp, 'segments.json'),
                                   translations=tr)
            self.assertEqual(rc, 0, msg=buf.getvalue())

    def test_leftover_page_text_ignores_widget_appearance_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_form_pdf(src)
            before = strip_text.leftover_page_text(src)
            self.assertTrue(before)
            self.assertIn(SOURCE_SENTENCE[:20], before[0][1])
            strip_text.strip_text(src, dst)
            self.assertEqual(strip_text.leftover_page_text(dst), [])
            after = pymupdf.open(dst)
            # Widget chrome still draws (get_text sees /AP); it is not page text.
            self.assertIn('Print', after[0].get_text())
            after.close()

    @staticmethod
    def _keep_everything(owner, pdf=None):
        import pikepdf
        ops = pikepdf.parse_content_stream(owner)
        return pikepdf.unparse_content_stream(ops), 0

    def test_leftover_text_fails_and_does_not_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_plain_pdf(src)
            with mock.patch.object(strip_text, 'strip_ops', self._keep_everything):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = strip_text.main([src, dst])
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL', log)
            self.assertIn(SOURCE_SENTENCE[:20], log)
            self.assertFalse(os.path.exists(dst))

    def test_pipeline_init_fails_on_leftover_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_plain_pdf(src)
            with mock.patch.object(strip_text, 'strip_ops', self._keep_everything):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = pipeline.main(['init', src, '--work', tmp])
            self.assertNotEqual(rc, 0, msg=buf.getvalue())
            self.assertFalse(os.path.exists(os.path.join(tmp, 'stripped.pdf')))


class InvisibleTextTests(unittest.TestCase):
    """Goal 14: an OCR'd scan (image + invisible text layer) is refused;
    visible text over a background image is not."""

    def test_invisible_text_pages_unit(self):
        with tempfile.TemporaryDirectory() as tmp:
            ocr = os.path.join(tmp, 'ocr.pdf')
            plain = os.path.join(tmp, 'plain.pdf')
            over = os.path.join(tmp, 'over.pdf')
            build_ocr_layer_pdf(ocr)
            build_plain_pdf(plain)
            build_text_over_image_pdf(over)
            flagged = strip_text.invisible_text_pages(ocr)
            self.assertEqual([pg for pg, _ in flagged], [0], msg=flagged)
            self.assertLess(flagged[0][1], strip_text.INVISIBLE_TEXT_MAX_CHANGED)
            self.assertEqual(strip_text.invisible_text_pages(plain), [])
            self.assertEqual(strip_text.invisible_text_pages(over), [])

    def test_ocr_layer_fails_extract_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            ocr = os.path.join(tmp, 'ocr.pdf')
            build_ocr_layer_pdf(ocr)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = extract_segments.main([ocr, '--outdir', tmp])
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('invisible', log.lower())
            self.assertIn('OCR', log)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(ocr, ocr)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('invisible', log.lower())

    def test_visible_text_over_image_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            over = os.path.join(tmp, 'over.pdf')
            build_text_over_image_pdf(over)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = extract_segments.main([over, '--outdir', tmp])
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('invisible', log.lower())
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify.verify(over, over)
            self.assertNotIn('invisible', buf.getvalue().lower())


class ExtractTests(unittest.TestCase):
    def test_cores_passthrough_and_inner_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_form_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            cores = {c['text']: c['count'] for c in result['cores']}
            self.assertIn(SOURCE_SENTENCE, cores)
            self.assertIn('CONFIDENTIAL', cores)
            self.assertIn('Public assistance', cores)
            self.assertNotIn('12345', cores)
            self.assertEqual(cores['Name:'], 2)
            segs = {s['core']: s for s in result['segments']}
            self.assertTrue(segs['12345']['passthrough'])
            inner = [w for w in result['warnings'] if w.get('kind') == 'inner-gap']
            self.assertTrue(inner, msg=result['warnings'])
            wfs = [w for w in result['warnings']
                   if w.get('kind') == 'write-find-say']
            hits = {w['text'] for w in wfs}
            self.assertTrue(any('Form W-2' in h or 'W-2' in h for h in hits)
                            or any(w.get('hit') == 'form-name' for w in wfs),
                            msg=hits)
            self.assertTrue(any('Question 1' in h for h in hits), msg=hits)


class NarrowColumnTests(unittest.TestCase):
    """Gate 12: the extractor yells at skinny stacked columns. Warn only."""

    def narrow_warnings(self, result):
        return [w for w in result['warnings']
                if w.get('kind') == 'narrow-column']

    def test_skinny_stack_warns_wide_paragraph_and_list_do_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_narrow_column_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            by_id = {s['id']: s for s in result['segments']}
            narrow = self.narrow_warnings(result)
            self.assertTrue(narrow, msg=result['warnings'])

            covered = set()
            for w in narrow:
                covered.update(w['ids'])
                self.assertEqual(w['page'], 0)
                self.assertGreaterEqual(len(w['ids']), 3)
                self.assertLess(w['width'], extract_segments.NARROW_WIDTH)
                self.assertEqual(w['lines'],
                                 [by_id[i]['core'] for i in w['ids']])

            words = {by_id[i]['core'] for i in covered}
            self.assertTrue(set(NARROW_WORDS) <= words, msg=sorted(words))
            # Neither the wide paragraph nor the wide list items may appear.
            for wide in WIDE_LINES:
                self.assertNotIn(wide, words)
            self.assertFalse([w for w in words if w.startswith('First remedy')],
                             msg=sorted(words))

    def test_narrow_column_never_merges_segments_or_cores(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_narrow_column_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            cores = {c['text'] for c in result['cores']}
            for word in NARROW_WORDS:
                self.assertIn(word, cores)
            # Warning only: no verify gate, no combined core.
            self.assertNotIn(' '.join(NARROW_WORDS), cores)

    def test_unit_needs_three_stacked_same_column_narrow_segments(self):
        def seg(i, x, y, w, size=10.0):
            return {'id': i, 'page': 0, 'bbox': [x, y - size, x + w, y + 2],
                    'origin': [x, y], 'size': size, 'core': f'c{i}',
                    'passthrough': False}

        stack = [seg(0, 72, 80, 40), seg(1, 72, 94, 40), seg(2, 72, 108, 40)]
        self.assertEqual(
            len(extract_segments.narrow_column_warnings(stack)), 1)
        # Two is not a stack.
        self.assertFalse(extract_segments.narrow_column_warnings(stack[:2]))
        # A different left edge breaks the run.
        moved = [seg(0, 72, 80, 40), seg(1, 200, 94, 40), seg(2, 72, 108, 40)]
        self.assertFalse(extract_segments.narrow_column_warnings(moved))
        # Wide segments are not a skinny column.
        wide = [seg(i, 72, 80 + 14 * i, 120) for i in range(3)]
        self.assertFalse(extract_segments.narrow_column_warnings(wide))
        # A big vertical gap is a different block.
        apart = [seg(0, 72, 80, 40), seg(1, 72, 94, 40), seg(2, 72, 400, 40)]
        self.assertFalse(extract_segments.narrow_column_warnings(apart))
        # Passthrough rows (bare numbers) never count toward the run.
        nums = [seg(i, 72, 80 + 14 * i, 40) for i in range(3)]
        nums[1]['passthrough'] = True
        self.assertFalse(extract_segments.narrow_column_warnings(nums))


class WidgetTextTests(unittest.TestCase):
    """Goal 17: widget text is not page text, and export values are data."""

    def test_field_value_and_choice_do_not_leak_into_cores(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_widget_text_pdf(src)
            doc = pymupdf.open(src)
            # The defect this closes: get_text() DOES show the widget text.
            self.assertIn(WIDGET_DEFAULT, doc[0].get_text())
            self.assertIn(FRUIT_OPTS[0], doc[0].get_text())
            doc.close()

            result = extract_segments.extract_segments(src, outdir=tmp)
            cores = {c['text'] for c in result['cores']}
            self.assertIn(WIDGET_LABEL, cores)
            self.assertNotIn(WIDGET_DEFAULT, cores)
            self.assertNotIn(FRUIT_OPTS[0], cores)
            texts = ' '.join(seg['text'] for seg in result['segments'])
            self.assertNotIn(WIDGET_DEFAULT, texts)

    def test_scaffold_lists_tooltips_options_and_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_widget_text_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            scaffold = result['widget_text']
            self.assertEqual(
                json.loads(Path(tmp, 'widget_text.json')
                           .read_text(encoding='utf-8')), scaffold)
            self.assertEqual(scaffold['Applicant']['tooltip'],
                             {'source': WIDGET_TIP, 'target': None})
            self.assertEqual(scaffold['Applicant']['value'],
                             {'source': WIDGET_DEFAULT, 'target': None})
            self.assertEqual(
                [o['export'] for o in scaffold['Fruit']['options']],
                FRUIT_OPTS)
            self.assertTrue(
                all(o['target'] is None for o in scaffold['Fruit']['options']))
            self.assertEqual(scaffold['Fruit']['tooltip']['source'], FRUIT_TIP)

    def test_apply_translates_display_and_keeps_export_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            build_widget_text_pdf(src)
            spec = {
                'Applicant': {
                    'tooltip': {'source': WIDGET_TIP,
                                'target': 'Nombre legal completo'},
                    'value': {'source': WIDGET_DEFAULT,
                              'target': 'VALOR PREDETERMINADO'},
                },
                'Fruit': {
                    'tooltip': 'Elija una fruta',
                    'options': {'Apple': 'Manzana', 'Pear': 'Pera',
                                'Plum': 'Ciruela'},
                },
            }
            report = strip_text.strip_text(src, stripped, widget_text=spec)
            self.assertEqual(report['leftover_text'], [])
            changed = {r['name']: set(r['changed'])
                       for r in report['rewritten_widget_text']}
            self.assertEqual(changed['Applicant'], {'tooltip', 'value'})
            self.assertEqual(changed['Fruit'], {'tooltip', 'options'})

            # Export values are untouched; only the display half moved.
            self.assertEqual(strip_text.choice_exports(stripped),
                             strip_text.choice_exports(src))
            doc = pymupdf.open(stripped)
            widgets = {w.field_name: w for p in doc for w in p.widgets()}
            self.assertEqual(widgets['Applicant'].field_label,
                             'Nombre legal completo')
            self.assertEqual(widgets['Applicant'].field_value,
                             'VALOR PREDETERMINADO')
            self.assertEqual(widgets['Fruit'].field_label, 'Elija una fruta')
            self.assertEqual(list(widgets['Fruit'].choice_values),
                             [('Apple', 'Manzana'), ('Pear', 'Pera'),
                              ('Plum', 'Ciruela')])
            # /V still holds the export value a viewer submits.
            self.assertEqual(widgets['Fruit'].field_value, 'Apple')
            doc.close()

    def test_unauthored_or_export_breaking_specs_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_widget_text_pdf(src)
            cases = [
                ({'Applicant': {'value': {'source': 'x', 'target': None}}},
                 'null'),
                ({'Applicant': {'value': {'source': 'x', 'target': '  '}}},
                 'empty'),
                ({'Fruit': {'value': 'Manzana'}}, 'export value'),
                ({'Fruit': {'default': 'Manzana'}}, 'export value'),
                ({'Nope': {'tooltip': 'x'}}, 'does not have'),
                ({'Fruit': {'options': {'Banana': 'Platano'}}},
                 'not export values'),
                ({'Applicant': {'options': {'Apple': 'Manzana'}}},
                 'non-choice'),
                ({'Applicant': {'tip': 'x'}}, 'unknown widget-text keys'),
                ({'Applicant': 'just a string'}, 'must be an object'),
            ]
            for spec, needle in cases:
                with self.assertRaises(strip_text.WidgetTextError) as ctx:
                    strip_text.strip_text(src, dst, widget_text=spec)
                self.assertIn(needle, str(ctx.exception))

    def test_cli_exits_2_on_a_bad_widget_text_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            wt = os.path.join(tmp, 'widget_text.json')
            build_widget_text_pdf(src)
            Path(wt).write_text(json.dumps(
                {'Applicant': {'value': {'source': 'x', 'target': None}}}),
                encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = strip_text.main([src, dst, '--widget-text', wt])
            self.assertEqual(rc, 2, msg=buf.getvalue())
            self.assertIn('FAIL widget text', buf.getvalue())

            Path(wt).write_text(json.dumps(
                {'Applicant': {'value': {'source': 'x', 'target': 'Valor'}}}),
                encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = strip_text.main([src, dst, '--widget-text', wt])
            self.assertEqual(rc, 0, msg=buf.getvalue())

    def test_opt_parity_gate_fails_a_translated_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            good = os.path.join(tmp, 'good.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            build_widget_text_pdf(src)
            strip_text.strip_text(src, good, widget_text={
                'Fruit': {'options': {'Apple': 'Manzana', 'Pear': 'Pera',
                                      'Plum': 'Ciruela'}}})
            retranslate_opt_exports(src, bad, {'Apple': 'Manzana',
                                               'Pear': 'Pera',
                                               'Plum': 'Ciruela'})
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, bad)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL /Opt export values changed', log)
            self.assertIn('Fruit', log)

            buf = io.StringIO()
            with redirect_stdout(buf):
                verify.verify(src, good)
            log = buf.getvalue()
            self.assertIn('PASS /Opt export parity', log)
            self.assertNotIn('FAIL /Opt export values changed', log)

    def test_opt_parity_is_silent_without_choice_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            build_plain_pdf(src)
            shutil.copy(src, out)
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify.verify(src, out)
            self.assertNotIn('/Opt export', buf.getvalue())


class RetypesetTests(unittest.TestCase):
    def test_complete_mapping_places_target_at_baseline(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_form_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            with open(os.path.join(tmp, 'segments.json'), encoding='utf-8') as f:
                segs = json.load(f)
            orig_y = next(s['origin'][1] for s in segs['segments']
                          if s['core'] == SOURCE_SENTENCE)
            orig_color_y = next(s['origin'][1] for s in segs['segments']
                                if s['core'] == 'CONFIDENTIAL')
            orig_color = next(s['color'] for s in segs['segments']
                              if s['core'] == 'CONFIDENTIAL')
            self.assertEqual(orig_color, WHITE)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, form_translations(), font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            doc = pymupdf.open(out)
            try:
                text = doc[0].get_text().replace('\xa0', ' ')
                self.assertIn(TARGET_SENTENCE, text)
                self.assertNotIn(SOURCE_SENTENCE, text)
                sentence_ys, colors, color_ys = [], [], []
                for b in doc[0].get_text('dict')['blocks']:
                    if b['type'] != 0:
                        continue
                    for line in b['lines']:
                        for s in line['spans']:
                            st = s['text'].replace('\xa0', ' ')
                            if 'solicitante' in st:
                                sentence_ys.append(s['origin'][1])
                            if 'CONFIDENCIAL' in st:
                                colors.append(s.get('color', 0))
                                color_ys.append(s['origin'][1])
                self.assertTrue(sentence_ys)
                self.assertTrue(any(abs(y - orig_y) < 1.5 for y in sentence_ys))
                self.assertTrue(colors, msg='CONFIDENCIAL span missing')
                # White is 0xFFFFFF; anything near-black would be the color-drop bug.
                self.assertGreater(max(colors), 0xCCCCCC)
                self.assertTrue(any(abs(y - orig_color_y) < 2.0 for y in color_ys))
            finally:
                doc.close()

    def test_incomplete_mapping_fails_and_lists_core(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_form_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            t = form_translations()
            del t['CONFIDENTIAL']
            write_mapping(tr, t, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 1)
            log = buf.getvalue()
            self.assertIn('FAIL', log)
            self.assertIn('CONFIDENTIAL', log)

    def test_dot_leaders_do_not_cover_midline_widget(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_form_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, form_translations(), font)
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0)
            self.assertFalse(
                dot_chars_overlap_widget(out, 'Agree'),
                'refilled dots overlapped the mid-line checkbox')


class RotatedTextTests(unittest.TestCase):
    """Audit H1: a rotated line must not be re-typeset flat."""

    def test_extract_records_the_line_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_rotated_text_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            by_core = {s['core']: s for s in result['segments']}
            for _, _, text, _, expected in ROT_ROWS:
                seg = by_core[text]
                self.assertEqual(tuple(seg['dir']), expected, msg=text)

    def test_unit_direction_helpers(self):
        self.assertEqual(retypeset.seg_dir({'dir': [0, -2]}), (0.0, -1.0))
        self.assertEqual(retypeset.seg_dir({}), (1.0, 0.0))
        self.assertEqual(retypeset.seg_dir({'dir': [0, 0]}), (1.0, 0.0))
        self.assertEqual(retypeset.seg_dir({'dir': 'nonsense'}), (1.0, 0.0))
        self.assertFalse(retypeset.is_rotated(1.0, 0.0))
        self.assertTrue(retypeset.is_rotated(0.0, -1.0))
        page = mock.Mock()
        page.rect = pymupdf.Rect(0, 0, 400, 400)
        seg = {'origin': [360, 340]}
        # Straight up from y=340: 340 - 16 of room, not the page width.
        self.assertAlmostEqual(
            retypeset.direction_limit(page, seg, 0.0, -1.0), 324.0)
        self.assertAlmostEqual(
            retypeset.direction_limit(page, seg, 1.0, 0.0), 24.0)

    def test_rotated_lines_keep_their_angle_through_retypeset(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_rotated_text_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, dict(ROT_TR), font, skip=[])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())

            dirs = line_dirs(out)
            src_dirs = line_dirs(src)
            for _, _, text, _, expected in ROT_ROWS:
                target = verify.normalize_ws_nbsp(ROT_TR[text])
                self.assertIn(target, dirs, msg=sorted(dirs))
                self.assertEqual(dirs[target], expected, msg=target)
                self.assertEqual(dirs[target],
                                 src_dirs[verify.normalize_ws_nbsp(text)],
                                 msg=target)

    def test_rotated_run_starts_at_the_original_origin(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_rotated_text_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, dict(ROT_TR), font, skip=[])
            buf = io.StringIO()
            with redirect_stdout(buf):
                retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            origins = {}
            doc = pymupdf.open(out)
            for page in doc:
                for b in page.get_text('dict')['blocks']:
                    for line in b.get('lines', []):
                        for sp in line['spans']:
                            key = verify.normalize_ws_nbsp(sp['text'])
                            if key:
                                origins.setdefault(key, sp['origin'])
            doc.close()
            src_seg = {s['core']: s for s in result['segments']}
            for _, _, text, _, _ in ROT_ROWS:
                got = origins[verify.normalize_ws_nbsp(ROT_TR[text])]
                want = src_seg[text]['origin']
                self.assertAlmostEqual(got[0], want[0], places=1, msg=text)
                self.assertAlmostEqual(got[1], want[1], places=1, msg=text)

    def test_rotated_line_is_not_gap_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            doc = pymupdf.open()
            page = doc.new_page(width=400, height=400)
            page.insert_text((360, 340), 'CITY        STATE', fontsize=10,
                             rotate=90)
            doc.save(src)
            doc.close()
            result = extract_segments.extract_segments(src, outdir=tmp)
            rotated = [s for s in result['segments']
                       if tuple(s['dir']) != (1.0, 0.0)]
            self.assertEqual(len(rotated), 1, msg=result['segments'])
            self.assertIn('STATE', rotated[0]['text'])

    def test_rotated_shaped_target_is_refused_not_drawn_flat(self):
        font = find_rtl_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            doc = pymupdf.open()
            page = doc.new_page(width=400, height=400)
            page.insert_text((360, 340), 'FOR OFFICE USE ONLY', fontsize=10,
                             rotate=90)
            doc.save(src)
            doc.close()
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {'FOR OFFICE USE ONLY': AR_TARGET}, font,
                          skip=[])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('rotated segments whose target needs shaping', log)
            self.assertFalse(os.path.exists(out), msg=log)


class CanonicalTextLayerTests(unittest.TestCase):
    """Audit H4/H5: the text layer must report the authored code points."""

    def _build(self, tmp, canonicalize=True):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_plain_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        write_mapping(tr, {SOURCE_SENTENCE: DRIFT_TARGET}, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            if canonicalize:
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            else:
                with mock.patch.object(retypeset, 'canonicalize_text_layer',
                                       return_value=0):
                    rc = retypeset.retypeset(
                        stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out, tr, os.path.join(tmp, 'segments.json')

    def layer(self, path):
        doc = pymupdf.open(path)
        try:
            return '\n'.join(p.get_text() for p in doc)
        finally:
            doc.close()

    def test_authored_gid_map_prefers_the_lower_code_point(self):
        font = find_test_font()
        gidmap, name = retypeset.authored_gid_map(str(font), ['a b-c'])
        self.assertTrue(name)
        f = pymupdf.Font(fontfile=str(font))
        space, hyphen = f.has_glyph(0x20), f.has_glyph(0x2D)
        # Values are the authored text, not a code point: a ligature glyph
        # maps to more than one character (row 24).
        self.assertEqual(gidmap.get(space), ' ')
        self.assertEqual(gidmap.get(hyphen), '-')
        # Authoring the drifted character too must not raise the mapping.
        gidmap, _ = retypeset.authored_gid_map(str(font), ['\xa0 x\u00ad-'])
        self.assertEqual(gidmap.get(space), ' ')
        self.assertEqual(gidmap.get(hyphen), '-')
        self.assertEqual(retypeset.authored_gid_map('no-such.ttf', ['x']),
                         (None, ''))

    def test_font_key_ignores_subset_prefix_and_spacing(self):
        self.assertEqual(retypeset._font_key('/ABCDEF+Arial Regular'),
                         retypeset._font_key('ArialRegular'))
        self.assertEqual(retypeset._font_key(None), '')

    def test_layer_is_canonical_after_retypeset(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp)
            layer = self.layer(out)
            self.assertIn(DRIFT_TARGET, layer, msg=repr(layer))
            for ch in ('\xa0', '\u00ad', '\u2010', '\u2011'):
                self.assertNotIn(ch, layer, msg=repr(layer))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS canonical text layer', log)

    def test_gate_fails_a_drifted_text_layer(self):
        """Drift the layer deliberately, so the gate is tested and not the font.

        Whether a face's cmap reverse-maps space to NBSP is the font's
        business: Arial's does, Noto Sans's does not. Pointing /ToUnicode
        at the drift characters — the exact inverse of retypeset's rewrite
        — reproduces the defect on any font, so this runs everywhere.
        """
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp)
            self.assertNotIn('\xa0', self.layer(out))

            drifted = os.path.join(tmp, 'drifted.pdf')
            f = pymupdf.Font(fontfile=str(font))
            gidmap = {f.has_glyph(0x20): '\xa0', f.has_glyph(0x2D): '\xad'}
            gidmap.pop(0, None)
            self.assertTrue(gidmap, msg='test font has no space or hyphen')
            block = retypeset._override_block(gidmap)
            pdf = pikepdf.open(out)
            try:
                patched = 0
                for obj in pdf.objects:
                    try:
                        tu = obj.get('/ToUnicode')
                    except Exception:
                        continue
                    if tu is None:
                        continue
                    data = bytes(tu.read_bytes())
                    i = data.rfind(b'endcmap')
                    if i < 0:
                        continue
                    obj.ToUnicode = pdf.make_stream(data[:i] + block + data[i:])
                    patched += 1
                self.assertTrue(patched, msg='no /ToUnicode to drift')
                pdf.save(drifted)
            finally:
                pdf.close()

            self.assertIn('\xa0', self.layer(drifted),
                          msg='the fixture did not actually drift')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, drifted, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL text layer is not canonical', log)
            self.assertIn('U+00A0', log)

    def test_original_drift_is_not_the_outputs_fault(self):
        # A character already in the original is the source's business.
        self.assertEqual(
            verify.drifted_characters('a\xa0b', 'the original had \xa0'), [])
        self.assertTrue(verify.drifted_characters('a\xa0b', 'plain'))


class GlyphCoverageTests(unittest.TestCase):
    """Audit M5: a character the font cannot draw must fail, not fall back."""

    def test_missing_glyphs_unit(self):
        helv = pymupdf.Font('helv')
        self.assertEqual(retypeset.missing_glyphs(helv, 'Plain ASCII'), [])
        self.assertEqual(retypeset.missing_glyphs(helv, '\u6c17\u6301'),
                         ['\u6c17', '\u6301'])
        # Reported once per character, in order.
        self.assertEqual(retypeset.missing_glyphs(helv, '\u6c17\u6c17'),
                         ['\u6c17'])
        # Control and format characters are never drawn.
        self.assertEqual(retypeset.missing_glyphs(helv, 'a\u00adb\u200dc'), [])
        self.assertEqual(retypeset.missing_glyphs(helv, ''), [])

    def test_cjk_target_in_a_latin_font_fails_and_saves_nothing(self):
        font = find_test_font()
        latin = pymupdf.Font(fontfile=str(font))
        target = '\u3053\u306e\u66f8\u985e'
        if not retypeset.missing_glyphs(latin, target):
            raise unittest.SkipTest('the test font covers CJK; nothing to miss')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: target}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('the chosen font cannot draw', log)
            self.assertIn('U+3053', log)
            self.assertFalse(os.path.exists(out), msg=log)

    def test_a_covered_target_still_passes(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('cannot draw', log)


def build_certified_pdf(path):
    """A page plus /Perms /UR3 and /Perms /DocMDP signature stand-ins."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=200)
    page.insert_text((50, 60), SOURCE_SENTENCE, fontsize=11)
    doc.save(path)
    doc.close()
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    sig = pikepdf.Dictionary(Type=pikepdf.Name('/Sig'),
                             Filter=pikepdf.Name('/Adobe.PPKLite'))
    pdf.Root.Perms = pikepdf.Dictionary(
        UR3=pdf.make_indirect(sig), DocMDP=pdf.make_indirect(sig))
    pdf.save(path)
    pdf.close()


class EncryptionAndPermsTests(unittest.TestCase):
    """Audit M3: say what happened to encryption, usage rights and DocMDP."""

    def test_perms_are_deleted_and_certification_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_certified_pdf(src)
            report = strip_text.strip_text(src, dst)
            self.assertEqual(report['perms_removed'], ['/DocMDP', '/UR3'])
            self.assertTrue(report['certified'])
            pdf = pikepdf.open(dst)
            try:
                self.assertNotIn('/Perms', pdf.Root)
            finally:
                pdf.close()

    def test_cli_warns_about_certification_and_encryption(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_certified_pdf(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = strip_text.main([src, dst])
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('deleted /Perms', log)
            self.assertIn('CERTIFIED', log)

    def test_plain_pdf_reports_no_encryption_and_no_perms(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_plain_pdf(src)
            report = strip_text.strip_text(src, dst)
            self.assertEqual(report['encryption'], {'encrypted': False})
            self.assertEqual(report['perms_removed'], [])
            self.assertFalse(report['certified'])
            self.assertFalse(report['reencrypted'])

    def test_encrypted_source_is_reported_and_can_keep_permissions(self):
        pdf_path = CORPUS / 'encrypted.pdf'
        with tempfile.TemporaryDirectory() as tmp:
            plain = os.path.join(tmp, 'plain.pdf')
            kept = os.path.join(tmp, 'kept.pdf')
            report = strip_text.strip_text(str(pdf_path), plain)
            enc = report['encryption']
            self.assertTrue(enc['encrypted'])
            self.assertIn('permissions', enc)
            self.assertFalse(report['reencrypted'])
            opened = pikepdf.open(plain)
            try:
                self.assertFalse(opened.is_encrypted)
            finally:
                opened.close()

            report = strip_text.strip_text(str(pdf_path), kept,
                                           keep_encryption=True)
            self.assertTrue(report['reencrypted'])
            self.assertIn('encryption_applied', report)
            opened = pikepdf.open(kept)
            try:
                self.assertTrue(opened.is_encrypted)
                # print_highres was denied in the source and stays denied.
                self.assertEqual(
                    report['encryption_applied']['print_highres'],
                    enc['permissions']['print_highres'])
            finally:
                opened.close()

    def test_signature_fields_are_not_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            dst = os.path.join(tmp, 'stripped.pdf')
            build_form_pdf(src)
            before = widget_map(src)
            strip_text.strip_text(src, dst)
            self.assertEqual(set(widget_map(dst)), set(before))


DOC_TITLE = 'Application for Benefits'
DOC_TITLE_ES = 'Solicitud de prestaciones'
DOC_TOC = ['Section One', 'Part A']
DOC_TOC_ES = ['Seccion Uno', 'Parte A']


def build_metadata_pdf(path):
    """A tagged, titled, bookmarked, en-US document."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((50, 60), SOURCE_SENTENCE, fontsize=11)
    doc.set_metadata({'title': DOC_TITLE, 'subject': 'Court form'})
    doc.set_toc([[1, DOC_TOC[0], 1], [2, DOC_TOC[1], 1]])
    doc.set_language('en-US')
    doc.save(path)
    doc.close()
    # A structure tree, the way a tagged form carries one.
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    pdf.Root.StructTreeRoot = pdf.make_indirect(
        pikepdf.Dictionary(Type=pikepdf.Name('/StructTreeRoot')))
    pdf.Root.MarkInfo = pikepdf.Dictionary(Marked=True)
    pdf.save(path)
    pdf.close()


class DocumentMetadataTests(unittest.TestCase):
    """Audit M4: /Lang, /Title, bookmarks and orphaned tags."""

    def _run(self, tmp, lang='es-MX', translate_meta=True):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_metadata_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        mapping = {SOURCE_SENTENCE: TARGET_SENTENCE}
        if translate_meta:
            mapping[DOC_TITLE] = DOC_TITLE_ES
            for a, b in zip(DOC_TOC, DOC_TOC_ES):
                mapping[a] = b
        else:
            mapping[DOC_TITLE] = DOC_TITLE
            for a in DOC_TOC:
                mapping[a] = a
        write_mapping(tr, mapping, font, lang=lang)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out, tr, buf.getvalue()

    def test_extract_lists_title_and_outline_as_cores(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_metadata_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            cores = {c['text'] for c in result['cores']}
            self.assertIn(DOC_TITLE, cores)
            for title in DOC_TOC:
                self.assertIn(title, cores)
            doc = result['document']
            self.assertEqual(doc['title'], DOC_TITLE)
            self.assertEqual(doc['outline'], DOC_TOC)
            self.assertTrue(doc['lang'].lower().startswith('en'))
            self.assertTrue(doc['struct_tree'])
            self.assertTrue(doc['marked'])
            on_disk = json.loads(
                Path(tmp, 'segments.json').read_text(encoding='utf-8'))
            self.assertEqual(on_disk['document'], doc)

    def test_retypeset_retargets_lang_title_outline_and_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, log = self._run(tmp)
            doc = pymupdf.open(out)
            try:
                self.assertEqual((doc.metadata or {}).get('title'),
                                 DOC_TITLE_ES)
                self.assertEqual([e[1] for e in doc.get_toc(simple=True)],
                                 DOC_TOC_ES)
                self.assertTrue(doc.language.lower().startswith('es'))
                cat = doc.pdf_catalog()
                self.assertEqual(
                    doc.xref_get_key(cat, 'StructTreeRoot')[0], 'null')
                self.assertIn('false',
                              str(doc.xref_get_key(cat, 'MarkInfo')[1]))
            finally:
                doc.close()
            self.assertIn('/Lang -> es-MX', log)
            self.assertIn('orphaned /StructTreeRoot', log)

    def test_gate_passes_a_retargeted_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, _ = self._run(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS document metadata', log)
            self.assertNotIn('REVIEW document metadata', log)

    def test_gate_fails_a_stale_title_lang_and_struct_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, _ = self._run(tmp)
            # Put the source metadata back, the way an output that never
            # retargeted anything looks.
            stale = os.path.join(tmp, 'stale.pdf')
            doc = pymupdf.open(out)
            doc.set_metadata({'title': DOC_TITLE})
            doc.set_toc([[1, DOC_TOC[0], 1], [2, DOC_TOC[1], 1]])
            doc.set_language('en-US')
            doc.save(stale)
            doc.close()
            pdf = pikepdf.open(stale, allow_overwriting_input=True)
            pdf.Root.StructTreeRoot = pdf.make_indirect(
                pikepdf.Dictionary(Type=pikepdf.Name('/StructTreeRoot')))
            pdf.save(stale)
            pdf.close()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, stale, translations=tr)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL document metadata', log)
            for what in ('[lang]', '[title]', '[outline]', '[struct-tree]'):
                self.assertIn(what, log)

    def test_missing_lang_is_a_review_line_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, _ = self._run(tmp, lang=None)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('REVIEW document metadata', log)

    def test_xmp_language_is_retargeted_when_present(self):
        xml = ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF><rdf:Description>'
               '<dc:language><rdf:Bag><rdf:li>en-US</rdf:li></rdf:Bag>'
               '</dc:language></rdf:Description></rdf:RDF></x:xmpmeta>')
            
        out, changed = retypeset.retarget_xmp(xml, 'es-MX')
        self.assertTrue(changed)
        self.assertIn('<rdf:li>es-MX</rdf:li>', out)
        self.assertNotIn('en-US', out)
        plain = '<dc:language>en-US</dc:language>'
        out, changed = retypeset.retarget_xmp(plain, 'es-MX')
        self.assertTrue(changed)
        self.assertEqual(out, '<dc:language>es-MX</dc:language>')
        self.assertEqual(retypeset.retarget_xmp('<x/>', 'es'), ('<x/>', False))
        self.assertEqual(retypeset.retarget_xmp('', 'es'), ('', False))
        self.assertEqual(retypeset.retarget_xmp(plain, ''), (plain, False))


RIGHT_LABELS = ['Total', 'Subtotal amount', 'Tax']
RIGHT_EDGE = 300.0
ITALIC_CORE = 'Read the notice carefully.'


def build_right_aligned_pdf(path):
    """Three labels sharing a right edge, tucked against a vertical rule,
    plus one left-aligned column."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    helv = pymupdf.Font('helv')
    # The rule the labels sit against (audit M1: "Gesamt ... over the rule
    # it was tucked against"). Row 21: a shared right edge alone is also
    # the shape of justified text; the rule is what makes this a column.
    page.draw_line((RIGHT_EDGE + 2, 45), (RIGHT_EDGE + 2, 110))
    for i, label in enumerate(RIGHT_LABELS):
        w = helv.text_length(label, 11)
        page.insert_text((RIGHT_EDGE - w, 60 + 20 * i), label, fontsize=11)
    for i, label in enumerate(['Name', 'Address', 'City']):
        page.insert_text((40, 160 + 20 * i), label, fontsize=11)
    doc.save(path)
    doc.close()


def span_edges(pdf_path):
    """text -> (x0, x1) of every span, whitespace-normalized."""
    doc = pymupdf.open(pdf_path)
    try:
        out = {}
        for page in doc:
            for b in page.get_text('dict')['blocks']:
                for line in b.get('lines', []):
                    for sp in line['spans']:
                        key = verify.normalize_ws_nbsp(sp['text'])
                        if key:
                            out[key] = (round(sp['bbox'][0], 1),
                                        round(sp['bbox'][2], 1))
        return out
    finally:
        doc.close()


def right_edges(pdf_path):
    return {k: x1 for k, (_, x1) in span_edges(pdf_path).items()}


# Row 18: signature captions are flush left with the rule they label.
CAPTION = 'Signature of parent or guardian'
CAPTION_ES = 'Firma del padre, madre o tutor legal'
DATE_CAPTION = 'Date'
DATE_ES = 'Fecha'
RULE_X0 = 72.0
DATE_X0 = 300.0


def build_caption_pdf(path):
    """Two signature rules, each with its caption starting where it starts."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.draw_line((RULE_X0, 100), (RULE_X0 + 180, 100))
    page.draw_line((DATE_X0, 100), (DATE_X0 + 80, 100))
    page.insert_text((RULE_X0, 112), CAPTION, fontsize=9)
    page.insert_text((DATE_X0, 112), DATE_CAPTION, fontsize=9)
    doc.save(path)
    doc.close()


class AlignmentAndFontRoleTests(unittest.TestCase):
    """Audit M1/M2: right anchoring, four font roles, inline b/i."""

    def test_extractor_proposes_right_aligned_cores(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_right_aligned_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            hits = [w for w in result['warnings']
                    if w.get('kind') == 'right-aligned']
            self.assertTrue(hits, msg=result['warnings'])
            proposed = set()
            for w in hits:
                proposed.update(w['lines'])
            self.assertTrue(set(RIGHT_LABELS) <= proposed, msg=proposed)
            # The left-aligned column shares a LEFT edge, not a right one.
            self.assertNotIn('Address', proposed)

    def test_right_alignment_unit_needs_differing_left_edges(self):
        def seg(i, x0, x1, y):
            return {'id': i, 'page': 0, 'bbox': [x0, y - 10, x1, y + 2],
                    'origin': [x0, y], 'size': 10.0, 'core': f'c{i}',
                    'passthrough': False}

        # A vertical rule one point past the shared edge, spanning the rows:
        # what the labels are tucked against.
        rule = {0: [(301.0, 40.0, 100.0)]}
        aligned = [seg(0, 100, 300, 60), seg(1, 200, 300, 80)]
        self.assertEqual(
            len(extract_segments.right_alignment_warnings(aligned, rule)), 1)
        # Same left edge too: an ordinary block, not a right-aligned column.
        block = [seg(0, 100, 300, 60), seg(1, 100, 300, 80)]
        self.assertFalse(extract_segments.right_alignment_warnings(block, rule))
        # Different right edges.
        ragged = [seg(0, 100, 300, 60), seg(1, 200, 280, 80)]
        self.assertFalse(extract_segments.right_alignment_warnings(ragged, rule))
        # Passthrough rows never propose anything.
        nums = [seg(0, 100, 300, 60), seg(1, 200, 300, 80)]
        nums[0]['passthrough'] = True
        self.assertFalse(extract_segments.right_alignment_warnings(nums, rule))

    def test_right_alignment_unit_needs_something_to_be_tucked_against(self):
        """Row 21: a shared right edge with spread left edges is also the
        shape of a justified paragraph with an indented first line. What
        makes a label column is what it sits against: a rule, a field or
        the next segment starting within one em of the edge."""
        def seg(i, x0, x1, y):
            return {'id': i, 'page': 0, 'bbox': [x0, y - 10, x1, y + 2],
                    'origin': [x0, y], 'size': 10.0, 'core': f'c{i}',
                    'passthrough': False}

        aligned = [seg(0, 100, 300, 60), seg(1, 200, 300, 80)]
        # Nothing to the right: no column, nothing proposed.
        self.assertFalse(extract_segments.right_alignment_warnings(aligned))
        self.assertFalse(extract_segments.right_alignment_warnings(aligned, {0: []}))
        # A rule within one em (size 10): proposed.
        near = {0: [(309.0, 40.0, 100.0)]}
        self.assertEqual(len(extract_segments.right_alignment_warnings(aligned, near)), 1)
        # A rule two ems away is a column gutter, not a tuck.
        far = {0: [(321.0, 40.0, 100.0)]}
        self.assertFalse(extract_segments.right_alignment_warnings(aligned, far))
        # A rule that does not reach the rows counts for neither of them.
        elsewhere = {0: [(305.0, 150.0, 200.0)]}
        self.assertFalse(extract_segments.right_alignment_warnings(aligned, elsewhere))
        # The next segment on the row is an obstacle too: a value column.
        with_values = aligned + [seg(2, 306, 380, 60), seg(3, 306, 380, 80)]
        self.assertEqual(len(extract_segments.right_alignment_warnings(with_values)), 1)

    def test_justified_text_and_hanging_indents_are_not_right_aligned(self):
        """Row 21: on the wild corpus 11,507 segments were proposed for
        `right`, most of them justified body text. Neither fixture below
        has anything to its right; both share a right edge with spread
        left edges, so both warned before the fix."""
        just = pymupdf.TEXT_ALIGN_JUSTIFY
        para = ('These words are set as a justified paragraph so that every '
                'line but the last one ends at the same right edge of the '
                'column, which is what the extractor used to read as a '
                'right-aligned column of labels whenever a first line was '
                'indented by a few points.')
        item = ('A bullet item whose continuation lines are indented under '
                'the text and not under the bullet, the hanging indent of '
                'every numbered list in every manual, which also shares a '
                'right edge while its left edges differ.')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            doc = pymupdf.open()
            page = doc.new_page(width=400, height=400)
            # Justified paragraph: an indented first pair of lines, then the
            # rest flush left; every full line ends at x = 300.
            page.insert_textbox(pymupdf.Rect(84, 40, 300, 70), para[:90],
                                fontsize=10, align=just)
            page.insert_textbox(pymupdf.Rect(72, 66, 300, 160), para[90:],
                                fontsize=10, align=just)
            # Hanging-indent list item: bullet line flush, continuation
            # lines indented by 12 pt, all ending at x = 300.
            page.insert_textbox(pymupdf.Rect(72, 200, 300, 226), '• ' + item[:80],
                                fontsize=10, align=just)
            page.insert_textbox(pymupdf.Rect(84, 222, 300, 320), item[80:],
                                fontsize=10, align=just)
            doc.save(src)
            doc.close()
            result = extract_segments.extract_segments(src, outdir=tmp)
            edges = sorted({s['bbox'][2] for s in result['segments']})
            # The fixture means something only if lines really share x = 300
            # while their left edges differ.
            at_edge = [s for s in result['segments'] if abs(s['bbox'][2] - 300) < 1.5]
            self.assertGreaterEqual(len(at_edge), 4, msg=edges)
            self.assertGreater(max(s['bbox'][0] for s in at_edge)
                               - min(s['bbox'][0] for s in at_edge), 4)
            hits = [w for w in result['warnings'] if w.get('kind') == 'right-aligned']
            self.assertEqual(hits, [])

    def test_right_list_anchors_the_right_edge(self):
        font = find_test_font()
        longer = {'Total': 'Gesamtbetrag', 'Subtotal amount': 'Zwischensumme',
                  'Tax': 'Steuer', 'Name': 'Name', 'Address': 'Adresse',
                  'City': 'Stadt'}
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            left_out = os.path.join(tmp, 'left.pdf')
            right_out = os.path.join(tmp, 'right.pdf')
            tr_l = os.path.join(tmp, 'left.json')
            tr_r = os.path.join(tmp, 'right.json')
            build_right_aligned_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            segs = os.path.join(tmp, 'segments.json')
            write_mapping(tr_l, longer, font)
            write_mapping(tr_r, longer, font, right=RIGHT_LABELS)
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(
                    retypeset.retypeset(stripped, segs, tr_l, left_out), 0)
                self.assertEqual(
                    retypeset.retypeset(stripped, segs, tr_r, right_out), 0)
            src_edges = right_edges(src)
            left_edges = right_edges(left_out)
            right_out_edges = right_edges(right_out)
            # Anchored left, the longer German word runs past the edge.
            self.assertGreater(left_edges['Gesamtbetrag'],
                               src_edges['Total'] + 1)
            # In "right", it ends where the source ended.
            self.assertAlmostEqual(right_out_edges['Gesamtbetrag'],
                                   src_edges['Total'], delta=1.0)
            # The left column is untouched by either mapping.
            self.assertAlmostEqual(right_out_edges['Adresse'],
                                   left_edges['Adresse'], delta=0.1)

    def test_center_moves_a_left_flush_caption_off_its_rule(self):
        """Row 18: the one place the old `center` example was wrong.

        A signature caption starts where its rule starts. Centring a wider
        translation on the source midpoint pushes it out both sides, so it
        hangs off the left end of the rule it labels; anchored left it
        starts exactly where the source did. Every gate passes either way,
        which is why the documentation must not invite it.
        """
        font = find_test_font()
        tr = {CAPTION: CAPTION_ES, DATE_CAPTION: DATE_ES}
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            plain_out = os.path.join(tmp, 'plain.pdf')
            centred_out = os.path.join(tmp, 'centred.pdf')
            tr_plain = os.path.join(tmp, 'plain.json')
            tr_centred = os.path.join(tmp, 'centred.json')
            build_caption_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            segs = os.path.join(tmp, 'segments.json')
            write_mapping(tr_plain, tr, font)
            write_mapping(tr_centred, tr, font,
                          center=[CAPTION, DATE_CAPTION])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc_plain = retypeset.retypeset(stripped, segs, tr_plain,
                                               plain_out)
                rc_centred = retypeset.retypeset(stripped, segs, tr_centred,
                                                 centred_out)
            self.assertEqual((rc_plain, rc_centred), (0, 0),
                             msg=buf.getvalue())
            source = span_edges(src)
            plain = span_edges(plain_out)
            centred = span_edges(centred_out)
            # The fixture only means something if the translation is wider.
            self.assertGreater(
                plain[CAPTION_ES][1] - plain[CAPTION_ES][0],
                source[CAPTION][1] - source[CAPTION][0] + 10)
            # Anchored left, each caption starts where its rule starts.
            self.assertAlmostEqual(plain[CAPTION_ES][0], RULE_X0, delta=0.1)
            self.assertAlmostEqual(plain[DATE_ES][0], DATE_X0, delta=0.1)
            # Centred, each now starts left of its own rule.
            self.assertLess(centred[CAPTION_ES][0], RULE_X0 - 1.0)
            self.assertLess(centred[DATE_ES][0], DATE_X0 - 1.0)
            # And no gate sees it: a silent PASS, not a refusal.
            for out, mapping in ((plain_out, tr_plain),
                                 (centred_out, tr_centred)):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = verify.verify(src, out, translations=mapping,
                                       source_words_from=segs)
                self.assertEqual(rc, 0, msg=buf.getvalue())

    def test_font_roles_fall_back_to_the_nearest_named_face(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            conf = {
                'fonts': {'regular': str(font)},   # nothing else named
                'translations': {SOURCE_SENTENCE: TARGET_SENTENCE},
                'merges': [], 'overrides': [], 'center': [], 'skip': [],
            }
            Path(tr).write_text(json.dumps(conf), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            doc = pymupdf.open(out)
            try:
                self.assertIn(TARGET_SENTENCE, doc[0].get_text())
            finally:
                doc.close()

    def test_inline_markup_lands_as_plain_text_and_passes_the_gates(self):
        font = find_test_font()
        marked = 'El <b>solicitante</b> debe <i>presentar</i> esto hoy.'
        plain = 'El solicitante debe presentar esto hoy.'
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: marked}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, segs, tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            doc = pymupdf.open(out)
            try:
                layer = doc[0].get_text()
            finally:
                doc.close()
            self.assertIn(plain, verify.normalize_ws_nbsp(layer))
            self.assertNotIn('<b>', layer)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS authored translations present', log)

    def test_inline_markup_helpers_are_narrow(self):
        self.assertTrue(retypeset.has_inline_markup('a <b>x</b>'))
        self.assertTrue(retypeset.has_inline_markup('<em>x</em>'))
        self.assertFalse(retypeset.has_inline_markup('a < b and c > d'))
        self.assertFalse(retypeset.has_inline_markup('<span>x</span>'))
        self.assertEqual(retypeset.strip_inline_markup('a <b>x</b> y'),
                         'a x y')
        self.assertEqual(verify.strip_inline_markup('<i>x</i>'), 'x')
        self.assertEqual(retypeset.strip_inline_markup('a < b'), 'a < b')


QA_MAPPING = {
    'Pay $1,250.00 by 12/31/2024.': 'Pague $1.250,00 antes del 31/12/2024.',
    'Pay $1,250.00 by 12/31/2025.': 'Pague $1.500,00 antes del 31/12/2025.',
    'Total': 'Total',
    'See Form W-2.': 'Vease Form W-2.',
    'Name:': 'Nombre',
    'Address (mailing)': 'Direccion (postal',
    'City': 'La ciudad  donde usted reside habitualmente y trabaja',
    'state': 'estado',
    'State': 'provincia',
}


def write_qa_mapping(path, translations=None, **extra):
    conf = {'fonts': {'regular': 'f.ttf'},
            'translations': dict(QA_MAPPING if translations is None
                                 else translations),
            'skip': []}
    conf.update(extra)
    Path(path).write_text(json.dumps(conf, ensure_ascii=False),
                          encoding='utf-8')
    return path


def qa_kinds(findings):
    return {(f['kind'], f['severity']) for f in findings}


# Row 19: a list body starts where the source put it. The first line has
# two spaces after its marker, the second one; both must land on the source
# body x, and the one-space line must not move at all.
LIST_TWO_CORE = 'Two spaces after the marker'
LIST_ONE_CORE = 'One space after the marker'
LIST_TWO = '1.  ' + LIST_TWO_CORE
LIST_ONE = '2. ' + LIST_ONE_CORE
LIST_TARGETS = {LIST_TWO_CORE: 'Dos espacios tras la marca',
                LIST_ONE_CORE: 'Un espacio tras la marca'}


def build_list_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((72, 100), LIST_TWO, fontsize=11)
    page.insert_text((72, 140), LIST_ONE, fontsize=11)
    doc.save(path)
    doc.close()


def body_x0(pdf_path, body):
    """x of the first glyph of `body` on page 1, from the raw character boxes.

    A span's bbox is not enough: in the original the marker and the body
    share one span, so the body's own start is only visible per character.
    """
    doc = pymupdf.open(pdf_path)
    try:
        for b in doc[0].get_text('rawdict')['blocks']:
            for line in b.get('lines', []):
                chars = [c for sp in line['spans'] for c in sp['chars']]
                s = ''.join(c['c'] for c in chars)
                i = s.find(body)
                if i >= 0:
                    return round(chars[i]['origin'][0], 2)
    finally:
        doc.close()
    raise AssertionError(f'{body!r} not found in {pdf_path}')


class ListMarkerGapTests(unittest.TestCase):
    """Row 19: retypeset used to re-emit marker + one space whatever the
    source printed, shifting every two-space list body 3.06 pt left on the
    canary fixture. The segment now records the gap and retypeset re-emits
    it; a segments.json without the key falls back to one space."""

    def _build(self, tmp, drop_gap=False):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        segs = os.path.join(tmp, 'segments.json')
        build_list_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        if drop_gap:
            # A segments.json from before row 19 has neither the gap nor the
            # measured body offset (row 23); drop both to stand in for one.
            data = json.loads(Path(segs).read_text(encoding='utf-8'))
            for s in data['segments']:
                s.pop('gap', None)
                s.pop('body_dx', None)
            Path(segs).write_text(json.dumps(data), encoding='utf-8')
        strip_text.strip_text(src, stripped)
        write_mapping(tr, LIST_TARGETS, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, segs, tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out

    def test_extractor_records_the_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_list_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            by_core = {s['core']: s for s in result['segments']}
            self.assertEqual(by_core[LIST_TWO_CORE]['marker'], '1.')
            self.assertEqual(by_core[LIST_TWO_CORE]['gap'], '  ')
            self.assertEqual(by_core[LIST_ONE_CORE]['marker'], '2.')
            self.assertEqual(by_core[LIST_ONE_CORE]['gap'], ' ')

    def test_multi_span_line_after_a_marker_still_extracts(self):
        """Real lines have several spans (a bold lead-in, a regular rest).

        The fixtures above are single-span lines, so a bug that only bites
        when the extractor compares span gaps *after* a list item passed the
        whole suite and failed on all seventeen wild-corpus files at once.
        """
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            doc = pymupdf.open()
            page = doc.new_page(width=400, height=300)
            page.insert_text((72, 100), LIST_TWO, fontsize=11)
            page.insert_text((72, 140), 'Bold lead-in', fontsize=11,
                             fontname='hebo')
            lead = pymupdf.Font('hebo').text_length('Bold lead-in', 11)
            page.insert_text((72 + lead + 3, 140), 'then the rest', fontsize=11)
            doc.save(src)
            doc.close()
            result = extract_segments.extract_segments(src, outdir=tmp)
            texts = [s['text'].strip() for s in result['segments']]
            self.assertIn(LIST_TWO, texts)
            # Two spans within the split threshold are one segment.
            self.assertTrue(any('Bold lead-in' in t and 'then the rest' in t
                                for t in texts), msg=texts)

    def test_body_lands_where_the_source_put_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = self._build(tmp)
            for core, target in LIST_TARGETS.items():
                self.assertAlmostEqual(body_x0(out, target), body_x0(src, core),
                                       delta=0.5, msg=core)

    def test_old_segments_without_gap_fall_back_to_one_space(self):
        helv = pymupdf.Font('helv')
        with tempfile.TemporaryDirectory() as tmp:
            src, out = self._build(tmp, drop_gap=True)
            # One-space list: unchanged.
            self.assertAlmostEqual(body_x0(out, LIST_TARGETS[LIST_ONE_CORE]),
                                   body_x0(src, LIST_ONE_CORE), delta=0.5)
            # Two-space list: the pre-row-19 placement, exactly one Helvetica
            # space short of the source. A stale work directory still builds.
            self.assertAlmostEqual(body_x0(out, LIST_TARGETS[LIST_TWO_CORE]),
                                   body_x0(src, LIST_TWO_CORE) - helv.text_length(' ', 11),
                                   delta=0.5)


# Row 23: the marker is drawn in Helvetica, so the body used to start at
# Helvetica's width of marker + gap, whatever the source font. Times and
# Courier markers are 1.6 and 9.6 pt off at 14 pt; the corpus measured
# 1.3 pt (Medicare) and 4.9 pt (FL-300) on one-space lists.
METRIC_TIMES_CORE = 'Body set in Times'
METRIC_COURIER_CORE = 'Body set in Courier'
METRIC_TARGETS = {METRIC_TIMES_CORE: 'Cuerpo en Times',
                  METRIC_COURIER_CORE: 'Cuerpo en Courier'}


def build_metric_list_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((72, 100), '1. ' + METRIC_TIMES_CORE, fontsize=14,
                     fontname='tiro')
    page.insert_text((72, 140), '2. ' + METRIC_COURIER_CORE, fontsize=14,
                     fontname='cour')
    doc.save(path)
    doc.close()


class MarkerFontMetricTests(unittest.TestCase):
    """Row 23: a list body starts at the measured source x, whatever the
    marker font. The segment records body_dx from per-character geometry;
    retypeset starts the body there; an old segments.json falls back to
    the Helvetica advance (row 19 behaviour)."""

    def _build(self, tmp, drop_key=False):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        segs = os.path.join(tmp, 'segments.json')
        build_metric_list_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        if drop_key:
            data = json.loads(Path(segs).read_text(encoding='utf-8'))
            for s in data['segments']:
                s.pop('body_dx', None)
            Path(segs).write_text(json.dumps(data), encoding='utf-8')
        strip_text.strip_text(src, stripped)
        write_mapping(tr, METRIC_TARGETS, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, segs, tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out

    def test_extractor_measures_the_body_offset(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_metric_list_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            by_core = {s['core']: s for s in result['segments']}
            for core, fontname in ((METRIC_TIMES_CORE, 'tiro'),
                                   (METRIC_COURIER_CORE, 'cour')):
                seg = by_core[core]
                self.assertEqual(seg['gap'], ' ')
                # Measured, not computed from a font: it equals the
                # source font's own advance for "N. ".
                want = pymupdf.Font(fontname).text_length(seg['marker'] + ' ', 14)
                self.assertAlmostEqual(seg['body_dx'], want, delta=0.3, msg=core)
            # A segment with no marker carries no offset.
            self.assertTrue(all('body_dx' not in s for s in result['segments']
                                if not s['marker']))

    def test_body_lands_on_the_source_x_whatever_the_marker_font(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = self._build(tmp)
            for core, target in METRIC_TARGETS.items():
                self.assertAlmostEqual(body_x0(out, target), body_x0(src, core),
                                       delta=0.5, msg=core)

    def test_old_segments_without_the_key_use_the_helvetica_advance(self):
        helv = pymupdf.Font('helv')
        with tempfile.TemporaryDirectory() as tmp:
            src, out = self._build(tmp, drop_key=True)
            # Row 19 behaviour, exactly: origin + Helvetica width of "2. ".
            self.assertAlmostEqual(body_x0(out, METRIC_TARGETS[METRIC_COURIER_CORE]),
                                   72 + helv.text_length('2. ', 14), delta=0.5)
            # Which is not where Courier put it.
            self.assertGreater(body_x0(src, METRIC_COURIER_CORE)
                               - body_x0(out, METRIC_TARGETS[METRIC_COURIER_CORE]), 5)


class MergePlacementGateTests(unittest.TestCase):
    """A re-flowed merge wraps; the gate must not read that as missing.

    Found by the canary: retypeset placed a two-line Spanish paragraph at
    full size, exit 0, and verify --translations failed it, because
    get_text() returns a newline at the wrap point while the authored html
    is one long string. Gates that fail correct output are the bug.
    """

    PARA_HTML = ('El secretario revisara todas las declaraciones presentadas '
                 'antes de la fecha de la audiencia y enviara por correo una '
                 'copia conformada a cada parte nombrada en el encabezado.')

    def test_wrapping_whitespace_is_collapsed_not_folded(self):
        self.assertEqual(verify.normalize_ws('a\nb'), 'a b')
        self.assertEqual(verify.normalize_ws('a  \t b'), 'a b')
        self.assertEqual(verify.normalize_ws('  a b  '), 'a b')
        # NBSP and the hyphen variants are NOT wrapping whitespace: the
        # canonical-text-layer gate owns those, and folding here hid them.
        self.assertEqual(verify.normalize_ws('a\xa0b'), 'a\xa0b')
        self.assertEqual(verify.normalize_ws('W\u2011 2'), 'W\u2011 2')
        self.assertEqual(
            verify.missing_translation_targets('one two\nthree',
                                               ['one two three']), [])
        self.assertEqual(
            verify.missing_translation_targets('one two\xa0three',
                                               ['one two three']),
            ['one two three'])

    def test_a_wrapped_merge_passes_the_placement_gate(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_paragraph_pdf(src, pages=1)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            conf = {
                'fonts': {'regular': str(font), 'bold': str(font)},
                'translations': {'Page 1 note here.': 'Nota de la pagina 1.'},
                'merges': [{'page': 0, 'lines': PARA_LINES,
                            'html': self.PARA_HTML, 'align': 'left'}],
                'overrides': [], 'center': [], 'skip': [],
            }
            Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                                encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())

            # The paragraph really did wrap — otherwise this proves nothing.
            doc = pymupdf.open(out)
            layer = doc[0].get_text()
            doc.close()
            self.assertNotIn(self.PARA_HTML, layer,
                             msg='fixture did not wrap; widen the paragraph')
            self.assertIn('\n', layer)

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS authored translations present', log)

    def test_a_merge_that_really_is_missing_still_fails(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_paragraph_pdf(src, pages=1)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            conf = {
                'fonts': {'regular': str(font), 'bold': str(font)},
                'translations': {'Page 1 note here.': 'Nota de la pagina 1.'},
                'merges': [{'page': 0, 'lines': PARA_LINES,
                            'html': self.PARA_HTML, 'align': 'left'}],
                'overrides': [], 'center': [], 'skip': [],
            }
            Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                                encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            # Now claim a paragraph nobody placed.
            conf['merges'][0]['html'] = 'Un parrafo que nadie coloco jamas.'
            Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                                encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL missing translation targets', log)


class QaCheckTests(unittest.TestCase):
    """The linguistic layer: what a reviser looks for first."""

    def test_expansion_band_is_length_dependent(self):
        self.assertEqual(qa_check.expansion_limit(4), 3.0)
        self.assertEqual(qa_check.expansion_limit(10), 3.0)
        self.assertEqual(qa_check.expansion_limit(11), 2.0)
        self.assertEqual(qa_check.expansion_limit(60), 1.4)
        self.assertEqual(qa_check.expansion_limit(500), 1.3)

    def test_number_and_date_units(self):
        self.assertEqual(qa_check.number_tokens('Pay $1,250.00 now'),
                         ['125000'])
        self.assertEqual(qa_check.number_tokens('1.250,00'), ['125000'])
        self.assertEqual(qa_check.number_tokens('no digits'), [])
        self.assertEqual([r for _, r in qa_check.date_parts('due 12/31/2024')],
                         ['12/31/2024'])
        self.assertEqual(qa_check.date_parts('12/31/2024')[0][0],
                         ('12', '2024', '31'))
        self.assertEqual(qa_check.strip_dates('due 12/31/2024 ok').split(),
                         ['due', 'ok'])
        self.assertEqual(qa_check.unbalanced_pairs('a (b'), [('(', ')')])
        self.assertEqual(qa_check.unbalanced_pairs('a (b)'), [])
        self.assertEqual(qa_check.unbalanced_pairs('say "hi'), [('"', '"')])
        self.assertEqual(qa_check.normalize_key('State:'),
                         qa_check.normalize_key('state'))

    def test_findings_over_a_bad_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_qa_mapping(os.path.join(tmp, 'translations.json'))
            findings = qa_check.qa_check(path)
            kinds = qa_kinds(findings)
            self.assertIn(('numbers', 'error'), kinds)
            self.assertIn(('brackets', 'error'), kinds)
            self.assertIn(('dates', 'warn'), kinds)
            self.assertIn(('inconsistent', 'warn'), kinds)
            self.assertIn(('length', 'warn'), kinds)
            self.assertIn(('punctuation', 'warn'), kinds)
            self.assertIn(('spacing', 'warn'), kinds)
            self.assertIn(('untranslated', 'warn'), kinds)
            # A reordered date is a warning, not a lost figure.
            date_findings = [f for f in findings if f['kind'] == 'dates']
            self.assertTrue(all(f['severity'] == 'warn' for f in date_findings),
                            msg=date_findings)
            # An identifier line kept verbatim is not "untranslated".
            untranslated = {f['core'] for f in findings
                            if f['kind'] == 'untranslated'}
            self.assertIn('Total', untranslated)
            self.assertNotIn('See Form W-2.', untranslated)

    def test_a_clean_mapping_reports_nothing(self):
        clean = {
            'The applicant must file this form today.':
                'El solicitante debe presentar este formulario hoy.',
            'Amount due: $1,250.00': 'Importe a pagar: $1,250.00',
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_qa_mapping(os.path.join(tmp, 'translations.json'),
                                    clean)
            self.assertEqual(qa_check.qa_check(path), [])

    def test_null_and_skip_entries_are_not_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_qa_mapping(
                os.path.join(tmp, 'translations.json'),
                {'Total': None, 'Amount (net)': None})
            self.assertEqual(qa_check.qa_check(path), [])
            path = write_qa_mapping(
                os.path.join(tmp, 'skipped.json'),
                {'Print': 'Print'}, skip=['Print'])
            self.assertEqual(qa_check.qa_check(path), [])

    def test_cjk_target_is_not_flagged_for_shrinking(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_qa_mapping(
                os.path.join(tmp, 'translations.json'),
                {'The applicant must file this form today.': '本日提出',
                 'Please describe the reason below.': '理由を記入'})
            findings = [f for f in qa_check.qa_check(path)
                        if f['kind'] == 'length']
            self.assertEqual(findings, [], msg=findings)

    def test_job_glossary_is_checked_and_never_shipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            gloss = os.path.join(tmp, 'glossary.csv')
            Path(gloss).write_text(
                'source,target\nForm W-2,Formulario W-2\n', encoding='utf-8')
            self.assertEqual(qa_check.load_glossary(gloss),
                             [('Form W-2', 'Formulario W-2')])
            path = write_qa_mapping(os.path.join(tmp, 'translations.json'),
                                    {'See Form W-2.': 'Vease Form W-2.'})
            self.assertEqual(qa_check.qa_check(path), [])
            findings = qa_check.qa_check(path, glossary_path=gloss)
            self.assertEqual(qa_kinds(findings), {('glossary', 'error')})
            ok = write_qa_mapping(os.path.join(tmp, 'ok.json'),
                                  {'See Form W-2.': 'Vease Formulario W-2.'})
            self.assertEqual(qa_check.qa_check(ok, glossary_path=gloss), [])
            # No glossary ships with the skill.
            self.assertEqual(
                sorted(p.name for p in Path(SCRIPTS).parent.rglob('*.csv')),
                [])

    def test_cli_exit_codes_and_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = write_qa_mapping(os.path.join(tmp, 'bad.json'))
            report = os.path.join(tmp, 'findings.json')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = qa_check.main([bad, '--json', report])
            self.assertEqual(rc, 1, msg=buf.getvalue())
            data = json.loads(Path(report).read_text(encoding='utf-8'))
            self.assertTrue(data['findings'])

            warn_only = write_qa_mapping(os.path.join(tmp, 'warn.json'),
                                         {'Total': 'Total'})
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(qa_check.main([warn_only]), 0)
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(qa_check.main([warn_only, '--strict']), 1)

            clean = write_qa_mapping(
                os.path.join(tmp, 'clean.json'),
                {'The applicant must file this form today.':
                 'El solicitante debe presentar este formulario hoy.'})
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(qa_check.main([clean]), 0)
            self.assertIn('no script can judge that', buf.getvalue())

    def test_pipeline_qa_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_qa_mapping(os.path.join(tmp, 'translations.json'))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['qa', '--work', tmp])
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn('qa_check:', buf.getvalue())
            with tempfile.TemporaryDirectory() as empty:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.assertEqual(pipeline.main(['qa', '--work', empty]), 2)


PARA_LINES = [
    'The clerk will review every declaration that is filed before',
    'the hearing date and will mail one conformed copy back to',
    'each party named in the caption of this proceeding.',
]


def build_paragraph_pdf(path, pages=2):
    """A wrapped paragraph per page, plus a page-specific line."""
    doc = pymupdf.open()
    for n in range(pages):
        page = doc.new_page(width=420, height=300)
        for i, line in enumerate(PARA_LINES):
            page.insert_text((40, 60 + 14 * i), line, fontsize=9)
        page.insert_text((40, 160), f'Page {n + 1} note here.', fontsize=9)
    doc.save(path)
    doc.close()


class MergeCandidateKindTests(unittest.TestCase):
    """Row 22: every warning names its kind; the paragraph proposals did not,
    so anything keyed on `kind` mislabelled them (the wild-corpus probe
    miscounted 2,484 of them). The kind exists now, and a segments.json
    from before it still proposes."""

    def test_merge_candidates_carry_their_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_paragraph_pdf(src, pages=1)
            result = extract_segments.extract_segments(src, outdir=tmp)
            cands = [w for w in result['warnings']
                     if w.get('kind') == 'merge-candidate']
            self.assertTrue(cands, msg=result['warnings'])
            self.assertGreaterEqual(len(cands[0]['lines']), 2)
            nameless = [w for w in result['warnings'] if not w.get('kind')]
            self.assertEqual(nameless, [])

    def test_main_prints_the_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_paragraph_pdf(src, pages=1)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = extract_segments.main([src, '--outdir', tmp])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            self.assertIn('[merge-candidate]', buf.getvalue())

    def test_propose_merges_accepts_old_and_new_candidates_only(self):
        segs = [{'id': 0, 'page': 0, 'text': 'first line of a paragraph',
                 'core': 'first line of a paragraph', 'passthrough': False},
                {'id': 1, 'page': 0, 'text': 'second line of it.',
                 'core': 'second line of it.', 'passthrough': False}]
        lines = [s['text'] for s in segs]
        # (kind on the warning, proposals expected)
        for kind, expected in ((None, 1), ('merge-candidate', 1),
                               ('right-aligned', 0)):
            with tempfile.TemporaryDirectory() as tmp:
                w = {'page': 0, 'ids': [0, 1], 'why': 'possible wrapped paragraph',
                     'lines': lines}
                if kind:
                    w['kind'] = kind
                Path(tmp, 'segments.json').write_text(
                    json.dumps({'segments': segs, 'warnings': [w]}),
                    encoding='utf-8')
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = pipeline.main(['propose-merges', '--work', tmp])
                self.assertEqual(rc, 0, msg=buf.getvalue())
                data = json.loads(Path(tmp, 'merges_proposed.json')
                                  .read_text(encoding='utf-8'))
                self.assertEqual(len(data['merges']), expected, msg=(kind, data))
                if expected:
                    self.assertEqual(data['merges'][0]['lines'], lines)


def build_many_warnings_pdf(path, n=14):
    """n lines that each carry one quoted write/find/say payload.

    "Question N" matches the quoted-string rule only; an "Attachment N"
    payload would match the form-name rule as well and be reported twice.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=60 + 20 * n)
    for i in range(n):
        page.insert_text((72, 60 + 20 * i), f'Write "Question {i + 1}" at the top.',
                         fontsize=11)
    doc.save(path)
    doc.close()


class WarningDigestTests(unittest.TestCase):
    """Lane B row P6: the extractor prints a per-kind digest — counts and what
    each kind asks of the author — then at most --max-per-kind lines per
    kind. On the wild corpus the one-line-per-warning printout ran to 2,394
    lines for one booklet. Nothing leaves the JSON."""

    def _run(self, tmp, extra=()):
        src = os.path.join(tmp, 'orig.pdf')
        build_many_warnings_pdf(src)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = extract_segments.main([src, '--outdir', tmp, *extra])
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return buf.getvalue()

    def test_digest_counts_then_capped_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._run(tmp)
            self.assertIn('WARNINGS: 14', out)
            self.assertRegex(out, r'write-find-say\s+14\s')
            self.assertIn('segments.json', out)
            lines = [l for l in out.splitlines() if '[write-find-say]' in l]
            self.assertEqual(len(lines), 10, msg=out)
            self.assertIn('4 more write-find-say', out)
            # The digest comes before the first per-line entry.
            self.assertLess(out.index('WARNINGS: 14'), out.index('[write-find-say]'))
            data = json.loads(Path(tmp, 'segments.json').read_text(encoding='utf-8'))
            self.assertEqual(
                sum(1 for w in data['warnings'] if w.get('kind') == 'write-find-say'), 14)

    def test_max_per_kind_is_configurable(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._run(tmp, ['--max-per-kind', '2'])
            lines = [l for l in out.splitlines() if '[write-find-say]' in l]
            self.assertEqual(len(lines), 2, msg=out)
            self.assertIn('12 more write-find-say', out)


class ParagraphAndSplitTests(unittest.TestCase):
    """Paragraph mode, page partitioning and the bilingual reading copy."""

    def test_propose_merges_writes_candidates_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_paragraph_pdf(src, pages=1)
            extract_segments.extract_segments(src, outdir=tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['propose-merges', '--work', tmp])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            data = json.loads(Path(tmp, 'merges_proposed.json')
                              .read_text(encoding='utf-8'))
            self.assertTrue(data['merges'])
            first = data['merges'][0]
            self.assertIsNone(first['html'])
            self.assertGreaterEqual(len(first['lines']), 2)
            self.assertFalse(Path(tmp, 'translations.json').exists())
            self.assertIn('nothing changed', buf.getvalue())

    def test_accept_folds_merges_in_with_null_html_that_still_fails(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            build_paragraph_pdf(src, pages=1)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            cores = json.loads(Path(tmp, 'to_translate.json')
                               .read_text(encoding='utf-8'))['cores']
            mapping = {c['text']: c['text'] + ' (es)' for c in cores}
            write_mapping(os.path.join(tmp, 'translations.json'), mapping,
                          font, skip=[])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['propose-merges', '--work', tmp,
                                    '--accept'])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            conf = json.loads(Path(tmp, 'translations.json')
                              .read_text(encoding='utf-8'))
            self.assertTrue(conf['merges'])
            self.assertTrue(all(m['html'] is None for m in conf['merges']))
            # Accepting a proposal does not translate it.
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'),
                    os.path.join(tmp, 'translations.json'), out)
            self.assertNotEqual(rc, 0, msg=buf.getvalue())

            # Authoring the html makes the same build pass.
            conf['merges'][0]['html'] = 'Un parrafo re-flujado en una unidad.'
            Path(tmp, 'translations.json').write_text(
                json.dumps(conf, ensure_ascii=False), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'),
                    os.path.join(tmp, 'translations.json'), out)
            self.assertEqual(rc, 0, msg=buf.getvalue())

    def test_pages_slice_extracts_only_that_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_paragraph_pdf(src, pages=3)
            first = extract_segments.extract_segments(src, outdir=tmp,
                                                      pages='1')
            self.assertEqual(first['pages'], [0])
            self.assertEqual({s['page'] for s in first['segments']}, {0})
            cores = {c['text'] for c in first['cores']}
            self.assertIn('Page 1 note here.', cores)
            self.assertNotIn('Page 2 note here.', cores)

            rest = extract_segments.extract_segments(src, outdir=tmp,
                                                     pages='2-3')
            self.assertEqual(rest['pages'], [1, 2])
            cores = {c['text'] for c in rest['cores']}
            self.assertNotIn('Page 1 note here.', cores)
            self.assertIn('Page 3 note here.', cores)

    def test_merge_mappings_combines_and_refuses_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, 'a.json')
            b = os.path.join(tmp, 'b.json')
            out = os.path.join(tmp, 'all.json')
            write_qa_mapping(a, {'One': 'Uno', 'Shared': 'Compartido'},
                             center=['One'])
            write_qa_mapping(b, {'Two': 'Dos', 'Shared': 'Compartido'},
                             center=['Two'])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['merge-mappings', out, a, b])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            conf = json.loads(Path(out).read_text(encoding='utf-8'))
            self.assertEqual(conf['translations'],
                             {'One': 'Uno', 'Shared': 'Compartido',
                              'Two': 'Dos'})
            self.assertEqual(sorted(conf['center']), ['One', 'Two'])

            clash = os.path.join(tmp, 'clash.json')
            write_qa_mapping(clash, {'Shared': 'Otra cosa'})
            conflicted = os.path.join(tmp, 'conflicted.json')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['merge-mappings', conflicted, a, clash])
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn('conflicting core', buf.getvalue())
            self.assertFalse(Path(conflicted).exists())

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['merge-mappings', conflicted, a, clash,
                                    '--last-wins'])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            conf = json.loads(Path(conflicted).read_text(encoding='utf-8'))
            self.assertEqual(conf['translations']['Shared'], 'Otra cosa')

    def test_null_from_cores_values_are_filled_not_conflicted(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, 'a.json')
            b = os.path.join(tmp, 'b.json')
            out = os.path.join(tmp, 'all.json')
            write_qa_mapping(a, {'One': None})
            write_qa_mapping(b, {'One': 'Uno'})
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['merge-mappings', out, a, b])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            conf = json.loads(Path(out).read_text(encoding='utf-8'))
            self.assertEqual(conf['translations']['One'], 'Uno')

    def test_bilingual_interleaves_and_refuses_fillable_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            tgt = os.path.join(tmp, 'out.pdf')
            both = os.path.join(tmp, 'both.pdf')
            build_paragraph_pdf(src, pages=2)
            shutil.copy(src, tgt)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['bilingual', src, tgt, both])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            doc = pymupdf.open(both)
            try:
                self.assertEqual(len(doc), 4)
            finally:
                doc.close()

            form = os.path.join(tmp, 'form.pdf')
            build_form_pdf(form)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = bilingual.main([form, form, both])
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn('form fields', buf.getvalue())
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = bilingual.main([form, form, both, '--reading-copy'])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            self.assertIn('reading copy only', buf.getvalue())

    def test_bilingual_target_first_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, 'a.pdf')
            b = os.path.join(tmp, 'b.pdf')
            out = os.path.join(tmp, 'both.pdf')
            for path, word in ((a, 'SOURCE'), (b, 'TARGET')):
                doc = pymupdf.open()
                page = doc.new_page(width=200, height=200)
                page.insert_text((20, 40), word, fontsize=12)
                doc.save(path)
                doc.close()
            bilingual.interleave(a, b, out)
            doc = pymupdf.open(out)
            try:
                self.assertIn('SOURCE', doc[0].get_text())
                self.assertIn('TARGET', doc[1].get_text())
            finally:
                doc.close()
            bilingual.interleave(a, b, out, target_first=True)
            doc = pymupdf.open(out)
            try:
                self.assertIn('TARGET', doc[0].get_text())
                self.assertIn('SOURCE', doc[1].get_text())
            finally:
                doc.close()


def patch_fstype(src, dst, value):
    """Copy a TTF with only OS/2.fsType changed, byte for byte otherwise.

    Re-saving through fontTools produces a font this machine's MuPDF will
    not rasterize, which would make the licence fixture fail for an
    unrelated reason.
    """
    import struct
    data = bytearray(Path(src).read_bytes())
    num_tables = struct.unpack('>H', data[4:6])[0]
    for i in range(num_tables):
        rec = 12 + i * 16
        if bytes(data[rec:rec + 4]) == b'OS/2':
            offset = struct.unpack('>I', data[rec + 8:rec + 12])[0]
            struct.pack_into('>H', data, offset + 8, value)
            Path(dst).write_bytes(bytes(data))
            return dst
    raise unittest.SkipTest('test font has no OS/2 table')


class SmallGuardTests(unittest.TestCase):
    """Three guards the audit called out: images, choice /DA, font licence."""

    def test_image_regions_are_listed_as_review_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            png = os.path.join(tmp, 'banner.png')
            _render_text_png(png, 'OFFICIAL BANNER', 'do not translate me')
            doc = pymupdf.open()
            page = doc.new_page(width=400, height=300)
            page.insert_text((40, 240), SOURCE_SENTENCE, fontsize=10)
            page.insert_image(pymupdf.Rect(40, 40, 360, 140), filename=png)
            doc.save(src)
            doc.close()
            result = extract_segments.extract_segments(src, outdir=tmp)
            hits = [w for w in result['warnings']
                    if w.get('kind') == 'image-region']
            self.assertEqual(len(hits), 1, msg=result['warnings'])
            self.assertEqual(hits[0]['page'], 0)
            self.assertEqual(len(hits[0]['bbox']), 4)
            self.assertIn('pixels', hits[0]['why'])

    def test_a_page_without_images_reports_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_plain_pdf(src)
            result = extract_segments.extract_segments(src, outdir=tmp)
            self.assertFalse([w for w in result['warnings']
                              if w.get('kind') == 'image-region'])

    def test_choice_field_default_appearance_is_rewritten(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = str(CORPUS / 'choice_fields.pdf')
            out = os.path.join(tmp, 'final.pdf')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = field_fonts.field_fonts(src, str(font), out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            pdf = pikepdf.open(out)
            try:
                das = {}
                for page in pdf.pages:
                    for a in page.get('/Annots', []):
                        parent = a.get('/Parent')
                        ft = a.get('/FT') or (parent and parent.get('/FT'))
                        if ft == pikepdf.Name('/Ch'):
                            das[str(a.get('/T', ''))] = str(a.get('/DA', ''))
                self.assertTrue(das, msg='no choice fields in the fixture')
                for name, da in das.items():
                    self.assertIn('/TransFF', da, msg=f'{name}: {da}')
            finally:
                pdf.close()

    def test_choice_values_survive_the_field_font_pass(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = str(CORPUS / 'choice_fields.pdf')
            out = os.path.join(tmp, 'final.pdf')
            buf = io.StringIO()
            with redirect_stdout(buf):
                field_fonts.field_fonts(src, str(font), out)
            self.assertEqual(strip_text.choice_exports(out),
                             strip_text.choice_exports(src))
            self.assertEqual(set(widget_map(out)), set(widget_map(src)))

    def test_fstype_refuses_a_restricted_font(self):
        font = find_test_font()
        fs, reason = prepare_font.embedding_permission(str(font))
        self.assertIsNone(reason, msg=f'test font is not embeddable: {reason}')
        with tempfile.TemporaryDirectory() as tmp:
            restricted = patch_fstype(str(font),
                                      os.path.join(tmp, 'restricted.ttf'),
                                      prepare_font.FSTYPE_RESTRICTED)
            fs, reason = prepare_font.embedding_permission(restricted)
            self.assertEqual(fs, prepare_font.FSTYPE_RESTRICTED)
            self.assertIn('forbids embedding', reason)

            tr = write_qa_mapping(os.path.join(tmp, 'translations.json'),
                                  {'Hello': 'Hola'})
            out = os.path.join(tmp, 'sub.ttf')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.prepare_font(restricted, tr, out,
                                               sample='Hola')
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn('OS/2.fsType', buf.getvalue())
            self.assertFalse(os.path.exists(out))

            # --allow-restricted downgrades the licence refusal to a
            # warning. It does not conjure a usable font: FreeType declines
            # to load a restricted-licence face at all, so the
            # rasterization assert refuses it a second time.
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.prepare_font(restricted, tr, out,
                                               sample='Hola',
                                               allow_restricted=True)
            log = buf.getvalue()
            self.assertIn('WARNING', log)
            self.assertIn('OS/2.fsType', log)
            self.assertNotIn('FAIL: the font', log)
            if rc:
                self.assertIn('cannot draw the sample', log)

            # A no-subsetting font is one the renderer WILL load, so the
            # override actually produces a font there.
            nosub = patch_fstype(str(font), os.path.join(tmp, 'nosub.ttf'),
                                 prepare_font.FSTYPE_NO_SUBSET)
            out2 = os.path.join(tmp, 'sub2.ttf')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.prepare_font(nosub, tr, out2, sample='Hola')
            self.assertEqual(rc, 1, msg=buf.getvalue())
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.prepare_font(nosub, tr, out2, sample='Hola',
                                               allow_restricted=True)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            self.assertTrue(os.path.exists(out2))

    def test_no_subset_and_bitmap_only_are_refused_too(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            for bit, needle in ((prepare_font.FSTYPE_NO_SUBSET,
                                 'forbids subsetting'),
                                (prepare_font.FSTYPE_BITMAP_ONLY,
                                 'bitmap embedding only')):
                path = patch_fstype(str(font),
                                    os.path.join(tmp, f'f{bit}.ttf'), bit)
                _, reason = prepare_font.embedding_permission(path)
                self.assertIn(needle, reason)
            # Editable and preview-print licences are fine.
            for bit in (0x0004, 0x0008):
                path = patch_fstype(str(font),
                                    os.path.join(tmp, f'ok{bit}.ttf'), bit)
                _, reason = prepare_font.embedding_permission(path)
                self.assertIsNone(reason, msg=reason)

    def test_unreadable_font_is_a_note_not_a_refusal(self):
        fs, reason = prepare_font.embedding_permission('/no/such/font.ttf')
        self.assertIsNone(fs)
        self.assertIn('could not read', reason)


class OverflowTests(unittest.TestCase):
    def test_squeeze_below_0_7_fails_and_does_not_save(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_squeeze_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SQUEEZE_CORE: SQUEEZE_LONG}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL', log)
            self.assertIn('0.7', log)
            self.assertIn(SQUEEZE_CORE, log)
            self.assertFalse(os.path.isfile(out), msg='must not save undersized PDF')

    def test_allow_scale_opts_in_and_saves(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_squeeze_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SQUEEZE_CORE: SQUEEZE_LONG}, font,
                          allow_scale=[SQUEEZE_CORE])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('allow_scale', log)
            self.assertTrue(os.path.isfile(out))
            doc = pymupdf.open(out)
            try:
                sizes = [s['size']
                         for b in doc[0].get_text('dict')['blocks'] if b['type'] == 0
                         for line in b['lines'] for s in line['spans']]
            finally:
                doc.close()
            self.assertTrue(sizes)
            self.assertLess(min(sizes) / 12.0, 0.7)

    def test_dot_leader_label_overflow_fails(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_form_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            t = form_translations()
            t['Public assistance'] = SQUEEZE_LONG * 2
            write_mapping(tr, t, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('Public assistance', log)
            self.assertIn('scaled below', log)
            self.assertFalse(os.path.isfile(out))

    def test_merge_htmlbox_overflow_fails(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            line1 = 'Line one of a paragraph that wraps here'
            line2 = 'and continues on the next line today.'
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 80), line1, fontsize=12)
            page.insert_text((72, 96), line2, fontsize=12)
            doc.save(src)
            doc.close()
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            rel = 'font.ttf'
            import shutil
            shutil.copy(font, os.path.join(tmp, rel))
            here = os.getcwd()
            try:
                os.chdir(tmp)
                write_mapping(tr, {line1: 'A', line2: 'B'}, rel)
                with open(tr, encoding='utf-8') as f:
                    conf = json.load(f)
                conf['fonts'] = {'regular': rel, 'bold': rel}
                conf['merges'] = [{
                    'page': 0,
                    'lines': [line1, line2],
                    'html': ('Wort ' * 80).strip(),
                    'align': 'left',
                }]
                with open(tr, 'w', encoding='utf-8') as f:
                    json.dump(conf, f, ensure_ascii=False)
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = retypeset.retypeset(stripped, 'segments.json', tr, out)
            finally:
                os.chdir(here)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('scaled below', log)
            self.assertIn(line1, log)
            self.assertFalse(os.path.isfile(out))

    def test_existing_fillable_mapping_does_not_overflow(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_form_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, form_translations(), font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            self.assertTrue(os.path.isfile(out))


class FieldsLinksTests(unittest.TestCase):
    def test_field_identity_fill_roundtrip_links_bookmarks(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            final = os.path.join(tmp, 'final.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_form_pdf(src)
            orig_w = widget_map(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, form_translations(), font)
            self.assertEqual(
                retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out),
                0)
            after_w = widget_map(out)
            self.assertEqual(set(orig_w), set(after_w))
            for name, (typ, rect) in orig_w.items():
                self.assertEqual(after_w[name][0], typ)
                self.assertTrue(rect.irect == after_w[name][1].irect
                                or abs(rect.x0 - after_w[name][1].x0) < 0.6)
            doc = pymupdf.open(out)
            uris = [lk.get('uri') for lk in doc[0].get_links()]
            self.assertIn(URI, uris)
            titles = [t[1] for t in doc.get_toc()]
            self.assertIn(BOOKMARK, titles)
            doc.close()

            self.assertEqual(field_fonts.field_fonts(out, str(font), final), 0)
            fill = 'Niño Pérez'
            doc = pymupdf.open(final)
            for p in doc:
                for w in p.widgets():
                    if w.field_name == 'ApplicantName':
                        w.field_value = fill
                        w.update()
            filled = os.path.join(tmp, 'filled.pdf')
            doc.save(filled)
            doc.close()
            doc = pymupdf.open(filled)
            values = [w.field_value for p in doc for w in p.widgets()
                      if w.field_name == 'ApplicantName']
            doc.close()
            self.assertIn(fill, values)

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, final,
                    fill_text=fill,
                    allow=['form', 'schedule', 'question', 'vease'],
                    source_words_from=os.path.join(tmp, 'segments.json'),
                )
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS field parity', log)
            self.assertIn('PASS fill round-trip', log)
            self.assertIn('PASS page 1 ink ratio', log)
            self.assertIn('PASS no untranslated running text', log)


class CheckboxOnlyFormTests(unittest.TestCase):
    def test_checkbox_only_form_passes_fill_round_trip(self):
        # Consent sheets and questionnaires often have tick boxes and no text
        # field. The fill gate must not fail them for lacking a text field.
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'boxes.pdf')
            doc = pymupdf.open()
            page = doc.new_page(width=612, height=792)
            page.insert_text((72, 80), 'Tick all that apply.', fontsize=12)
            for i, name in enumerate(('Agree', 'Consent')):
                cb = pymupdf.Widget()
                cb.field_name = name
                cb.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
                cb.rect = pymupdf.Rect(72, 100 + 20 * i, 86, 114 + 20 * i)
                page.add_widget(cb)
            doc.save(src)
            doc.close()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, src, min_ink=0.2)
            log = buf.getvalue()
            self.assertIn('PASS fill round-trip', log)
            self.assertNotIn('FAIL fill round-trip', log)


class NonFormTests(unittest.TestCase):
    def test_non_form_pipeline_skips_fill_does_not_fail(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            self.assertEqual(
                retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out),
                0)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, out,
                    source_words_from=os.path.join(tmp, 'segments.json'),
                )
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS field parity', log)
            self.assertIn('SKIP fill round-trip (no fields)', log)
            self.assertNotIn('FAIL', log)
            doc = pymupdf.open(out)
            try:
                got = doc[0].get_text().replace('\xa0', ' ')
                self.assertIn(TARGET_SENTENCE, got)
            finally:
                doc.close()


class LeakScanTests(unittest.TestCase):
    def test_three_source_words_fail_allowlisted_token_does_not(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            leak = os.path.join(tmp, 'leak.pdf')
            okp = os.path.join(tmp, 'ok.pdf')
            tr_leak = os.path.join(tmp, 'tr_leak.json')
            tr_ok = os.path.join(tmp, 'tr_ok.json')
            build_form_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            leaked = dict(form_translations())
            leaked[SOURCE_SENTENCE] = SOURCE_SENTENCE  # untranslated running text
            write_mapping(tr_leak, leaked, font)
            self.assertEqual(retypeset.retypeset(stripped, segs, tr_leak, leak), 0)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, leak, allow=['form', 'schedule', 'question'],
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL untranslated running text', log)

            write_mapping(tr_ok, form_translations(), font)
            self.assertEqual(retypeset.retypeset(stripped, segs, tr_ok, okp), 0)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, okp,
                    allow=['form', 'schedule', 'question', 'vease'],
                    source_words_from=segs,
                )
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS no untranslated running text', log)

    def test_scan_leaks_unit_on_shipped_function(self):
        src_words = {'please', 'press', 'the', 'submit', 'button', 'schedule'}
        running, isolated = verify.scan_leaks(
            'Please press the submit button now. Schedule remains.',
            allow={'schedule'},
            source_words=src_words,
        )
        self.assertTrue(running)
        self.assertNotIn('Schedule', ' '.join(isolated))
        running, isolated = verify.scan_leaks(
            'El formulario esta listo. Schedule',
            allow={'schedule'},
            source_words=src_words,
        )
        self.assertFalse(running)


# Row 20: a compliance notice names the form it translates, in the source
# language. The leak scan must not read that title as untranslated text —
# and must still fail a sentence that is.
NOTICE_TITLE = 'Field Trip Permission Slip'
NOTICE_SENTENCE = 'Please return this form to the office.'
NOTICE_ISSUER = 'Riverside Elementary School'
NOTICE_TARGETS = {
    NOTICE_TITLE: 'Autorizacion de excursion escolar',
    NOTICE_SENTENCE: 'Devuelva este formulario a la oficina.',
    NOTICE_ISSUER: NOTICE_ISSUER,   # the author kept the issuer's name
}
# compliance.md's wording, target language, quoting the source title as a unit.
NOTICE_LINE = ('Traduccion solo informativa. Esta es una traduccion no oficial de '
               + NOTICE_TITLE + ', que se ofrece para ayudarle a entender el formulario.')


def build_titled_pdf(path, title=NOTICE_TITLE):
    """Heading, one sentence and an issuer line; /Title set to the heading."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((72, 80), title, fontsize=14)
    page.insert_text((72, 120), NOTICE_SENTENCE, fontsize=11)
    page.insert_text((72, 150), NOTICE_ISSUER, fontsize=11)
    doc.set_metadata({'title': title})
    doc.save(path)
    doc.close()


def add_notice(pdf_in, pdf_out, line=NOTICE_LINE):
    """Draw a notice line at the foot of page 1 (the author's own step; the
    skill has no notice channel of its own)."""
    doc = pymupdf.open(pdf_in)
    doc[0].insert_text((72, 270), line, fontsize=7, fontname='helv')
    doc.save(pdf_out)
    doc.close()


class NoticeTitleTests(unittest.TestCase):
    """Row 20: compliance.md tells the author to name the source form in the
    notice; the leak scan then failed that title as untranslated running
    text (two of three canary models had to allowlist it word by word).
    The original's /Title, quoted as a unit, is not a leak; a longer run
    that merely contains it still is."""

    def _translated(self, tmp, targets):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_titled_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        write_mapping(tr, targets, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out, os.path.join(tmp, 'segments.json')

    def _verify(self, src, out, **kw):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = verify.verify(src, out, **kw)
        return rc, buf.getvalue()

    def test_notice_quoting_the_title_is_not_a_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, segs = self._translated(tmp, NOTICE_TARGETS)
            noticed = os.path.join(tmp, 'noticed.pdf')
            add_notice(out, noticed)
            # The issuer's name is the author's decision: allowlisted as a
            # phrase, which matches that run and nothing else.
            rc, log = self._verify(src, noticed, source_words_from=segs,
                                   allow=[NOTICE_ISSUER])
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS no untranslated running text', log)
            self.assertNotIn('FAIL untranslated running text', log)
            # Kept runs are said out loud, not silently dropped.
            note = [l for l in log.splitlines() if l.startswith('note:')]
            self.assertEqual(len(note), 1, msg=log)
            self.assertIn(NOTICE_TITLE, note[0])
            self.assertIn(NOTICE_ISSUER, note[0])

    def test_an_untranslated_sentence_still_fails_beside_the_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            leaked = dict(NOTICE_TARGETS)
            leaked[NOTICE_SENTENCE] = NOTICE_SENTENCE   # forgotten, not decided
            src, out, segs = self._translated(tmp, leaked)
            noticed = os.path.join(tmp, 'noticed.pdf')
            add_notice(out, noticed)
            rc, log = self._verify(src, noticed, source_words_from=segs,
                                   allow=[NOTICE_ISSUER])
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL untranslated running text', log)
            fail_block = log.split('FAIL untranslated running text')[1].split('\n\n')[0]
            self.assertIn('return this form', fail_block)
            self.assertNotIn('Field Trip Permission', fail_block)

    def test_issuer_name_needs_a_phrase_allow_not_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, segs = self._translated(tmp, NOTICE_TARGETS)
            # Kept verbatim and not allowlisted: three source words in a row.
            rc, log = self._verify(src, out, source_words_from=segs)
            self.assertEqual(rc, 1, msg=log)
            self.assertIn(NOTICE_ISSUER, log)
            # The phrase allow clears exactly that run.
            rc, log = self._verify(src, out, source_words_from=segs,
                                   allow=[NOTICE_ISSUER])
            self.assertEqual(rc, 0, msg=log)
            # And does not clear a different three-word run built from the
            # same words: the phrase is a unit, not a word list.
            other = os.path.join(tmp, 'other.pdf')
            add_notice(out, other, line='School Riverside Elementary again')
            rc, log = self._verify(src, other, source_words_from=segs,
                                   allow=[NOTICE_ISSUER])
            self.assertEqual(rc, 1, msg=log)

    def test_scan_leaks_keeps_a_run_equal_to_the_title_only(self):
        words = {'field', 'trip', 'permission', 'slip', 'form', 'please', 'return', 'this'}
        keep = {NOTICE_TITLE}
        running, isolated = verify.scan_leaks(
            'Traduccion de Field Trip Permission Slip, para usted.',
            allow=set(), source_words=words, keep=keep)
        self.assertEqual(running, [])
        self.assertEqual(isolated, [])
        # Title plus one more source word: a longer run, still a leak.
        running, _ = verify.scan_leaks(
            'Traduccion de Field Trip Permission Slip Form ahora.',
            allow=set(), source_words=words, keep=keep)
        self.assertEqual(len(running), 1, msg=running)
        # Case does not matter; punctuation around the title does not either.
        running, _ = verify.scan_leaks(
            'Vea "FIELD TRIP PERMISSION SLIP".', allow=set(), source_words=words, keep=keep)
        self.assertEqual(running, [])


class ScriptAwareLeakTests(unittest.TestCase):
    """Goal 15: the leak scan follows the source document's script."""

    def _translate(self, src, tmp, mapping_fn, font):
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'tr.json')
        strip_text.strip_text(src, stripped)
        res = extract_segments.extract_segments(src, outdir=tmp)
        cores = [c['text'] for c in res['cores']]
        write_mapping(tr, mapping_fn(cores), font)   # default skip drops the form's 'Print' chrome
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return out, cores

    def _verify(self, src, out, **kw):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = verify.verify(src, out, **kw)
        return rc, buf.getvalue()

    def test_dominant_script_unit(self):
        self.assertEqual(verify.dominant_script('申立人は以下の情報'), 'CJK')
        self.assertEqual(verify.dominant_script('Name of applicant 123'), 'Latin')
        self.assertEqual(verify.dominant_script('طلب المساعدة'), 'Arabic')
        self.assertEqual(verify.dominant_script('Заявитель'), 'Cyrillic')
        self.assertIsNone(verify.dominant_script('123 -- 4.5'))

    def test_ja_source_correct_english_output_passes(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'ja.pdf')
            build_ja_source_pdf(src)
            out, cores = self._translate(src, tmp, lambda cs: {c: JA_TARGETS[c] for c in cs}, font)
            self.assertEqual(set(cores), set(JA_LINES), msg=cores)
            rc, log = self._verify(src, out)
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS no untranslated running text', log)
            self.assertIn('source script CJK', log)

    def test_ja_source_leftover_line_fails(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'ja.pdf')
            build_ja_source_pdf(src)

            def leak(cs):
                m = {c: JA_TARGETS[c] for c in cs}
                m[JA_LINES[0]] = JA_LINES[0]   # a whole line left untranslated
                return m
            out, _ = self._translate(src, tmp, leak, cjk_font_file(tmp))
            rc, log = self._verify(src, out)
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL untranslated running text', log)
            self.assertIn('申立人', log)

    def test_ja_source_two_char_leftover_is_review_only(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'ja.pdf')
            build_ja_source_pdf(src)

            def leak(cs):
                m = {c: JA_TARGETS[c] for c in cs}
                m['署名'] = '署名'
                return m
            out, _ = self._translate(src, tmp, leak, cjk_font_file(tmp))
            rc, log = self._verify(src, out)
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('REVIEW isolated source-script tokens', log)
            self.assertIn('署名', log)

    def test_ar_source_english_output_passes_and_leftover_fails(self):
        arfont = find_rtl_font()
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'ar.pdf')
            build_ar_source_pdf(src, arfont)
            out, cores = self._translate(
                src, tmp, lambda cs: dict(zip(cs, AR_TARGETS_EN)), font)
            self.assertEqual(len(cores), 3, msg=cores)
            rc, log = self._verify(src, out)
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('source script Arabic', log)
            # The leak case needs an English page carrying one Arabic run.
            # Building it through retypeset would need a single font that
            # draws both scripts: Arial does, no Noto face does, and
            # demanding one is how these tests used to skip on Linux. Draw
            # the leftover onto the good output with the Arabic face
            # instead, the same Story path the source fixture uses.
            out2 = os.path.join(tmp, 'leak.pdf')
            leaked = pymupdf.open(out)
            # A right-to-left TextWriter run, not the Story engine: the
            # engine leaves presentation forms that extract as separate
            # tokens, and the leak scan is about three CONSECUTIVE source
            # words on one line. Base letterforms also keep the unshaped
            # Arabic gate quiet, so this test fails on its own subject.
            tw = pymupdf.TextWriter(leaked[0].rect)
            tw.append((60, 300), AR_LINES[0],
                      font=pymupdf.Font(fontfile=str(arfont)), fontsize=12,
                      right_to_left=True)
            tw.write_text(leaked[0])
            leaked.save(out2)
            leaked.close()
            rc, log = self._verify(src, out2)
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL untranslated running text', log)

    def test_same_script_pair_uses_document_words_without_flag(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_form_pdf(src)
            out, _ = self._translate(src, tmp, lambda cs: form_translations(), font)
            rc, log = self._verify(src, out, allow=['form', 'schedule', 'question', 'vease'])
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('document words', log)


class HotLoopTests(unittest.TestCase):
    def test_rebuild_resolves_verify_arguments_from_the_callers_directory(self):
        font = os.path.abspath(find_test_font())
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            work = os.path.join(tmp, 'job')
            os.mkdir(work)
            src = os.path.join(tmp, 'original.pdf')
            out = os.path.join(work, 'out.pdf')
            build_plain_pdf(src)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pipeline.main(['init', src, '--work', work]), 0)
            tr = os.path.join(work, 'translations.json')
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font, lang='es')
            here = os.getcwd()
            buf = io.StringIO()
            try:
                # Windows CI keeps the checkout and TEMP on different drives.
                # Make the isolated temp directory the caller so relative paths
                # exist, while the mapping remains in its separate job folder.
                os.chdir(tmp)
                with redirect_stdout(buf):
                    rc = pipeline.main([
                        'rebuild', '--work', os.path.relpath(work),
                        os.path.relpath(src), os.path.relpath(out),
                        '--source-words-from', os.path.relpath(os.path.join(work, 'segments.json')),
                        '--translations', os.path.relpath(tr),
                        '--segments', os.path.relpath(os.path.join(work, 'segments.json')),
                    ])
                self.assertEqual(os.getcwd(), tmp)
            except FileNotFoundError as exc:
                self.fail(f'caller-relative verification path was lost: {exc}')
            finally:
                os.chdir(here)
            self.assertEqual(rc, 0, buf.getvalue())
            self.assertIn('PASS authored translations present', buf.getvalue())

    def test_direct_retypeset_resolves_fonts_beside_the_mapping(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'original.pdf')
            out = os.path.join(tmp, 'out.pdf')
            build_plain_pdf(src)
            shutil.copyfile(font, os.path.join(tmp, 'local-font.ttf'))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pipeline.main(['init', src, '--work', tmp]), 0)
            tr = os.path.join(tmp, 'translations.json')
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, 'local-font.ttf')
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    rc = retypeset.retypeset(os.path.join(tmp, 'stripped.pdf'),
                                            os.path.join(tmp, 'segments.json'), tr, out)
            except Exception as exc:
                self.fail(f'mapping-relative font was not resolved: {exc}')
            self.assertEqual(rc, 0, buf.getvalue())
            with pymupdf.open(out) as doc:
                self.assertIn(TARGET_SENTENCE, doc[0].get_text())

    def test_story_uses_the_configured_font_in_a_directory_with_spaces(self):
        from fontTools.ttLib import TTFont

        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "job with spaces (ñ)'s"
            work.mkdir()
            src, out = work / 'original.pdf', work / 'out.pdf'
            build_plain_pdf(str(src))
            shutil.copyfile(font, work / 'local-font.ttf')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pipeline.main(['init', str(src), '--work', str(work)]), 0)
            tr = work / 'translations.json'
            write_mapping(str(tr), {SOURCE_SENTENCE: f'<b>{TARGET_SENTENCE}</b>'},
                          'local-font.ttf')
            with redirect_stdout(io.StringIO()):
                rc = retypeset.retypeset(str(work / 'stripped.pdf'),
                                        str(work / 'segments.json'), str(tr), str(out))
            self.assertEqual(rc, 0)
            normalize = lambda name: name.replace(' ', '').replace('-', '').lower()
            with TTFont(font) as face:
                expected = normalize(face['name'].getDebugName(6))
            with pymupdf.open(out) as doc:
                spans = [span for block in doc[0].get_text('dict')['blocks']
                         for line in block.get('lines', []) for span in line['spans']]
                self.assertIn(TARGET_SENTENCE, doc[0].get_text())
                self.assertTrue(any(normalize(span['font']) == expected for span in spans),
                                f'configured font {expected} was replaced: {spans}')

    def test_rebuild_and_render_without_reextract(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            renders = os.path.join(tmp, 'renders')
            build_plain_pdf(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['init', src, '--work', tmp])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            write_mapping(os.path.join(tmp, 'translations.json'),
                          {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main([
                    'rebuild', '--work', tmp, src, out,
                    '--source-words-from', os.path.join(tmp, 'segments.json'),
                ])
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS field parity', log)
            self.assertIn('elapsed', log)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['render', src, out, renders, '--dpi', '72'])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            self.assertTrue(os.path.isfile(os.path.join(renders, 'orig_p1.png')))
            self.assertTrue(os.path.isfile(os.path.join(renders, 'out_p1.png')))


class FromCoresTests(unittest.TestCase):
    def test_scaffold_nulls_refuse_overwrite_force_and_retypeset_fails(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_plain_pdf(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['init', src, '--work', tmp])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            self.assertFalse(
                os.path.isfile(os.path.join(tmp, 'translations.json')),
                'init must not write translations.json')
            cores = json.loads(
                Path(tmp, 'to_translate.json').read_text(encoding='utf-8'))['cores']
            self.assertTrue(any(c['text'] == SOURCE_SENTENCE for c in cores))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['from-cores', '--work', tmp])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            tr = os.path.join(tmp, 'translations.json')
            conf = json.loads(Path(tr).read_text(encoding='utf-8'))
            self.assertIn(SOURCE_SENTENCE, conf['translations'])
            self.assertIsNone(conf['translations'][SOURCE_SENTENCE])
            self.assertEqual(set(conf['translations']), {c['text'] for c in cores})
            self.assertEqual(conf['merges'], [])
            self.assertEqual(conf['skip'], [])
            self.assertNotIn('mirror', conf)
            self.assertIn('regular', conf['fonts'])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['from-cores', '--work', tmp])
            self.assertEqual(rc, 2, msg=buf.getvalue())
            self.assertIn('--force', buf.getvalue())
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['from-cores', '--work', tmp, '--force'])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn(SOURCE_SENTENCE, buf.getvalue())
            self.assertFalse(os.path.isfile(out))
            # Identity would have saved; null must not.
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            self.assertEqual(
                retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out),
                0)

    def test_from_cores_missing_to_translate(self):
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['from-cores', '--work', tmp])
            self.assertEqual(rc, 2, msg=buf.getvalue())


class PrepareFontAndCompareTests(unittest.TestCase):
    def test_prepare_font_subsets_and_rasterizes(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            tr = os.path.join(tmp, 'translations.json')
            out_font = os.path.join(tmp, 'sub.ttf')
            write_mapping(tr, form_translations(), font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.prepare_font(
                    str(font), tr, out_font, sample=TARGET_SENTENCE)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            self.assertTrue(os.path.isfile(out_font))
            self.assertGreater(os.path.getsize(out_font), 1000)

    def test_compare_html_is_language_neutral(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            html = os.path.join(tmp, 'comparison.html')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            self.assertEqual(
                retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out),
                0)
            self.assertEqual(
                compare.compare(src, out, html, labels='English|Español',
                                lang='es'),
                0)
            body = Path(html).read_text(encoding='utf-8')
            self.assertIn('lang="es"', body)
            self.assertNotIn('lang="ja"', body)
            self.assertNotIn('Hiragino', body)
            self.assertNotIn('Noto Sans JP', body)


class RefusalGateTests(unittest.TestCase):
    def test_scanned_image_page_fails_extract_and_verify(self):
        """A page that only contains a raster image must not get a passing verdict."""
        with tempfile.TemporaryDirectory() as tmp:
            drawn = os.path.join(tmp, 'drawn.pdf')
            src = os.path.join(tmp, 'scan.pdf')
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 72), 'NOTICE OF HEARING', fontsize=18)
            page.insert_text((72, 120), SOURCE_SENTENCE, fontsize=12)
            pix = page.get_pixmap(dpi=110)
            doc.save(drawn)
            doc.close()
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_image(page.rect, pixmap=pix)
            doc.save(src)
            doc.close()

            result = extract_segments.extract_segments(src, outdir=tmp)
            self.assertEqual(result['segments'], [])
            self.assertEqual(result['unextractable_pages'], [0])
            kinds = {w.get('kind') for w in result['warnings']}
            self.assertIn('no-text-layer', kinds)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = extract_segments.main([src, '--outdir', tmp])
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn('OCR', buf.getvalue())

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, src)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('scanned', log.lower())

    def test_pale_blank_page_skips_ink_ratio_instead_of_failing(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'pale.pdf')
            doc = pymupdf.open()
            page = doc.new_page()
            page.draw_rect(page.rect, fill=(0.96, 0.96, 0.97))
            doc.save(src)
            doc.close()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, src)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('SKIP page 1 ink ratio', log)
            self.assertNotIn('FAIL page 1 ink ratio', log)


class PlacementTests(unittest.TestCase):
    """Authored targets must appear in the output text layer when asked."""

    def test_source_side_fold_survives_for_identifier_comparison(self):
        # Arial maps U+00AD to the hyphen glyph, so a SOURCE PDF can report
        # 'W\u00ad2' for a printed 'W-2'. That drift is not ours to rewrite,
        # so identifier spans read out of the original still fold.
        self.assertEqual(verify.normalize_ws_nbsp('Form W\u00ad2'), 'Form W-2')
        self.assertEqual(verify.normalize_ws_nbsp('Form\xa0W-2'), 'Form W-2')
        self.assertEqual(
            verify.missing_identifier_spans('Vease Form W\u00ad2',
                                            ['Form W-2']), [])

    def test_placement_targets_are_compared_verbatim(self):
        # Retypeset canonicalizes /ToUnicode, so an authored space must land
        # as a space. Folding here would hide the drift the canonical gate
        # exists to catch.
        self.assertEqual(
            verify.missing_translation_targets(
                'Adjunte el recibo hoy.', ['Adjunte el recibo hoy.', 'x', '']),
            [])
        self.assertEqual(
            verify.missing_translation_targets(
                'Adjunte\xa0el recibo hoy.', ['Adjunte el recibo hoy.']),
            ['Adjunte el recibo hoy.'])
        # Absent target of length ≥ 2 is reported; length-1 is not required.
        missing = verify.missing_translation_targets(
            'nope', ['Adjunte el recibo hoy.', 'Z'])
        self.assertEqual(missing, ['Adjunte el recibo hoy.'])
        self.assertNotIn('Z', missing)

    def test_drifted_characters_unit(self):
        authored = 'Vease Form W-2 y Schedule C.'
        landed = authored.replace(' ', '\xa0').replace('-', '\u2011')
        drift = dict(verify.drifted_characters(landed, authored))
        self.assertIn('\xa0', drift)
        self.assertIn('\u2011', drift)
        self.assertEqual(verify.drifted_characters(authored, authored), [])
        # A character the author really wrote is not drift.
        self.assertEqual(
            verify.drifted_characters('caf\u00e9\xa0here', 'x\xa0y'), [])
        # CJK compatibility ideograph for 立.
        self.assertEqual(
            [c for c, _ in verify.drifted_characters('\uf9f7', '\u7acb')],
            ['\uf9f7'])

    def test_pipe_split_is_what_lands_not_the_separator(self):
        conf = {
            'translations': {'Lead (rest)': 'LeadIn‖ remainder'},
            'skip': [],
        }
        targets = verify.collect_translation_targets(conf)
        self.assertIn('LeadIn', targets)
        self.assertIn(' remainder', targets)
        self.assertTrue(all('‖' not in t for t in targets))
        # Retypeset writes two runs; concatenated get_text() has both sides.
        self.assertEqual(
            verify.missing_translation_targets('LeadIn remainder', targets),
            [])

    def test_fillable_hyphenated_target_lands_canonical(self):
        """ASCII 'W-2' in the mapping must come back as ASCII 'W-2'.

        MuPDF's reverse-mapped ToUnicode reports U+2010/U+2011 (Noto) or
        U+00AD (Arial) for the hyphen glyph and NBSP for space. Retypeset
        rewrites /ToUnicode to the authored code points, so the layer is
        byte-identical to what was authored. Do not swap this for a
        hyphen-free fixture: the authored target contains '-'.
        """
        font = find_test_font()
        hyphen_src = 'See Form W-2 and Schedule C.'
        hyphen_tgt = form_translations()[hyphen_src]
        self.assertIn('-', hyphen_tgt)
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_form_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, form_translations(), font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, segs, tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            placed = pymupdf.open(out)
            try:
                layer = placed[0].get_text()
            finally:
                placed.close()
            # The layer IS a byte-identical copy of the authored ASCII string.
            self.assertIn(hyphen_tgt, layer, msg=repr(layer))
            self.assertFalse(
                [h for h in ('\u2011', '\u2010', '\u00ad', '\xa0')
                 if h in layer],
                msg=repr(layer))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, out,
                    allow=['form', 'schedule', 'question', 'vease'],
                    source_words_from=segs,
                    translations=tr,
                )
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS authored translations present', log)
            self.assertIn('PASS canonical text layer', log)
            self.assertNotIn('FAIL missing translation targets', log)
            self.assertNotIn(hyphen_tgt, log)

    def test_retypeset_mapping_passes_stripped_names_missing_target(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, segs, tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, out,
                    source_words_from=segs,
                    translations=tr,
                )
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS authored translations present', log)
            self.assertNotIn('FAIL missing translation targets', log)
            placed = pymupdf.open(out)
            try:
                layer = placed[0].get_text().replace('\xa0', ' ')
            finally:
                placed.close()
            self.assertIn(TARGET_SENTENCE, layer)

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, stripped,
                    source_words_from=segs,
                    translations=tr,
                )
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL missing translation targets', log)
            self.assertIn(TARGET_SENTENCE, log)
            gone = pymupdf.open(stripped)
            try:
                layer = gone[0].get_text().replace('\xa0', ' ')
            finally:
                gone.close()
            self.assertNotIn(TARGET_SENTENCE, layer)
            self.assertNotIn(SOURCE_SENTENCE, layer)

    def test_omit_translations_does_not_run_placement_gate(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            self.assertEqual(retypeset.retypeset(stripped, segs, tr, out), 0)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('authored translations present', log)
            self.assertNotIn('missing translation targets', log)
            self.assertIn('PASS field parity', log)

    def test_verify_cli_twice_pass_and_twice_fail(self):
        font = find_test_font()
        script = str(SCRIPTS / 'verify.py')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: TARGET_SENTENCE}, font)
            self.assertEqual(retypeset.retypeset(stripped, segs, tr, out), 0)
            pass_args = [
                sys.executable, script, src, out,
                '--source-words-from', segs, '--translations', tr,
            ]
            fail_args = [
                sys.executable, script, src, stripped,
                '--source-words-from', segs, '--translations', tr,
            ]
            pass_logs = []
            for _ in range(2):
                r = subprocess.run(
                    pass_args, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertIn('PASS authored translations present', r.stdout)
                pass_logs.append(r.stdout)
            fail_logs = []
            for _ in range(2):
                r = subprocess.run(
                    fail_args, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertIn('FAIL missing translation targets', r.stdout)
                self.assertIn(TARGET_SENTENCE, r.stdout)
                fail_logs.append(r.stdout)
            self.assertEqual(pass_logs[0].split('elapsed')[0],
                             pass_logs[1].split('elapsed')[0])
            self.assertEqual(fail_logs[0].split('elapsed')[0],
                             fail_logs[1].split('elapsed')[0])

    def test_rebuild_fillable_without_translations_flag(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            build_form_pdf(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['init', src, '--work', tmp])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            write_mapping(os.path.join(tmp, 'translations.json'),
                          form_translations(), font)
            fill = 'Niño Pérez'
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main([
                    'rebuild', '--work', tmp, src, out,
                    '--fill-text', fill,
                    '--source-words-from', os.path.join(tmp, 'segments.json'),
                    '--allow', 'form,schedule,question,vease',
                ])
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS field parity', log)
            self.assertIn('PASS fill round-trip', log)
            self.assertIn('PASS page 1 ink ratio', log)
            self.assertIn('PASS no untranslated running text', log)
            self.assertNotIn('authored translations present', log)
            self.assertNotIn('missing translation targets', log)


def choice_snapshot(pdf_path):
    doc = pymupdf.open(pdf_path)
    try:
        widgets = []
        for p in doc:
            for w in p.widgets():
                widgets.append({
                    'name': w.field_name,
                    'type': w.field_type_string,
                    'choices': list(w.choice_values or []),
                })
        return widgets
    finally:
        doc.close()


class ChoiceFieldsTests(unittest.TestCase):
    def test_corpus_choice_fields_survive_strip_retypeset(self):
        pdf = CORPUS / 'choice_fields.pdf'
        self.assertTrue(pdf.is_file(), 'corpus/choice_fields.pdf missing')
        font = find_test_font()
        orig = choice_snapshot(pdf)
        names = {w['name'] for w in orig}
        self.assertIn('Fruit', names)
        self.assertIn('Color', names)
        types = {w['name']: w['type'] for w in orig}
        self.assertEqual(types['Fruit'], 'ComboBox')
        self.assertEqual(types['Color'], 'ListBox')
        fruit = next(w['choices'] for w in orig if w['name'] == 'Fruit')
        color = next(w['choices'] for w in orig if w['name'] == 'Color')
        self.assertGreaterEqual(len(fruit), 3)
        self.assertGreaterEqual(len(color), 2)
        with tempfile.TemporaryDirectory() as tmp:
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            extract_segments.extract_segments(str(pdf), outdir=tmp)
            strip_text.strip_text(str(pdf), stripped)
            write_mapping(
                tr, {CHOICE_SENTENCE: CHOICE_TARGET}, font,
                skip=['Print', 'Red', 'Blue'])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            after = choice_snapshot(out)
            self.assertEqual(len(after), len(orig))
            self.assertEqual(
                {(w['name'], w['type'], tuple(w['choices'])) for w in after},
                {(w['name'], w['type'], tuple(w['choices'])) for w in orig})
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    str(pdf), out,
                    source_words_from=os.path.join(tmp, 'segments.json'),
                    allow=['fruta', 'lista', 'color'],
                )
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS field parity', log)


class ChromeTests(unittest.TestCase):
    """Original pushbutton captions still drawing are a FAIL unless skip/captions."""

    _ALLOW = ['form', 'schedule', 'question', 'vease']

    def _build(self, tmp, captions=None, skip=None, extra_tr=None):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_form_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        segs = os.path.join(tmp, 'segments.json')
        strip_text.strip_text(src, stripped, captions=captions)
        mapping = dict(form_translations())
        if extra_tr:
            mapping.update(extra_tr)
        write_mapping(tr, mapping, font, skip=skip)
        self.assertEqual(
            retypeset.retypeset(stripped, segs, tr, out), 0)
        return src, stripped, out, tr, segs

    def test_leftover_unit_skip_rewrite_stale_ap(self):
        orig = {'PrintForm': 'Print'}
        self.assertEqual(
            verify.leftover_button_captions(
                orig, orig, 'Print\n', skip=[]),
            [('PrintForm', 'Print')])
        self.assertEqual(
            verify.leftover_button_captions(
                orig, orig, 'Print\n', skip=['Print']),
            [])
        self.assertEqual(
            verify.leftover_button_captions(
                orig, {'PrintForm': 'Imprimir'}, 'Imprimir\n', skip=[]),
            [])
        # CA rewritten but stale /AP still draws the source caption.
        self.assertEqual(
            verify.leftover_button_captions(
                orig, {'PrintForm': 'Imprimir'}, 'Print\n', skip=[]),
            [('PrintForm', 'Print')])

    def test_skip_print_leaves_chrome_and_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, _, out, tr, segs = self._build(tmp, skip=['Print'])
            names = widget_map(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, out, allow=self._ALLOW,
                    source_words_from=segs, translations=tr)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS button captions', log)
            self.assertNotIn('FAIL untranslated button captions', log)
            self.assertEqual(set(widget_map(out)), set(names))
            layer = pymupdf.open(out)
            try:
                self.assertIn('Print', layer[0].get_text())
            finally:
                layer.close()

    def test_empty_skip_fails_naming_print(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Extract sees widget "Print" as a core. Map it so retypeset
            # succeeds; do not skip or --captions — chrome must still FAIL.
            src, _, out, tr, segs = self._build(
                tmp, skip=[], extra_tr={'Print': 'Print'})
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, out, allow=self._ALLOW,
                    source_words_from=segs, translations=tr)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL untranslated button captions', log)
            self.assertIn('Print', log)
            self.assertEqual(set(widget_map(out)), set(widget_map(src)))

    def test_captions_rewrite_passes_field_count_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, _, out, tr, segs = self._build(
                tmp, captions={'PrintForm': 'Imprimir'}, skip=[],
                extra_tr={'Print': 'Imprimir'})
            orig_names = widget_map(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(
                    src, out, allow=self._ALLOW,
                    source_words_from=segs, translations=tr)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS button captions', log)
            self.assertNotIn('FAIL untranslated button captions', log)
            self.assertEqual(set(widget_map(out)), set(orig_names))
            self.assertEqual(len(widget_map(out)), len(orig_names))
            layer = pymupdf.open(out)
            try:
                text = layer[0].get_text()
            finally:
                layer.close()
            self.assertNotIn('Print', text)
            self.assertIn('Imprimir', text)

    def test_omit_translations_does_not_run_chrome_gate(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            out = os.path.join(tmp, 'out.pdf')
            build_form_pdf(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main(['init', src, '--work', tmp])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            write_mapping(os.path.join(tmp, 'translations.json'),
                          form_translations(), font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.main([
                    'rebuild', '--work', tmp, src, out,
                    '--fill-text', 'Niño Pérez',
                    '--source-words-from', os.path.join(tmp, 'segments.json'),
                    '--allow', 'form,schedule,question,vease',
                ])
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS field parity', log)
            self.assertIn('PASS fill round-trip', log)
            self.assertNotIn('button captions', log)


class CaptionWidthTests(unittest.TestCase):
    """Output pushbutton /CA wider than the widget rect is a FAIL."""

    def _build(self, tmp, caption):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_narrow_button_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        segs = os.path.join(tmp, 'segments.json')
        strip_text.strip_text(src, stripped, captions={NARROW_BTN: caption})
        mapping = {SOURCE_SENTENCE: TARGET_SENTENCE}
        cores = json.loads(
            Path(tmp, 'to_translate.json').read_text(encoding='utf-8'))['cores']
        for c in cores:
            if c['text'] == SHORT_CAPTION:
                continue
            mapping.setdefault(c['text'], c['text'])
        mapping[SOURCE_SENTENCE] = TARGET_SENTENCE
        write_mapping(tr, mapping, font, skip=[SHORT_CAPTION])
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, segs, tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out, tr, segs

    def test_caption_overflows_unit(self):
        fs = max(4, 24 - 4)
        self.assertTrue(verify.caption_overflows(LONG_CAPTION, 60, fs))
        self.assertFalse(verify.caption_overflows(SHORT_CAPTION, 60, fs))
        self.assertFalse(verify.caption_overflows('Fit', 60, fs))
        self.assertFalse(verify.caption_overflows('', 60, fs))
        self.assertFalse(verify.caption_overflows(None, 60, fs))
        self.assertTrue(verify.caption_overflows(LONG_CAPTION, 60, 12))
        self.assertFalse(verify.caption_overflows(SHORT_CAPTION, 120, 20))

    def test_long_caption_fails_short_passes_field_count_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp, LONG_CAPTION)
            orig_names = widget_map(src)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL caption wider than widget', log)
            self.assertIn(NARROW_BTN, log)
            self.assertIn(LONG_CAPTION, log)
            self.assertEqual(set(widget_map(out)), set(orig_names))
            self.assertEqual(len(widget_map(out)), len(orig_names))

            src, out, tr, segs = self._build(tmp, SHORT_CAPTION)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('FAIL caption wider than widget', log)
            self.assertEqual(set(widget_map(out)), set(widget_map(src)))

    def test_omit_translations_does_not_run_caption_width_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp, LONG_CAPTION)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('caption wider than widget', log)
            self.assertNotIn(LONG_CAPTION, log)

    def test_verify_cli_twice_overflow_and_twice_short(self):
        script = str(SCRIPTS / 'verify.py')
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp, LONG_CAPTION)
            args = [
                sys.executable, script, src, out,
                '--source-words-from', segs, '--translations', tr,
            ]
            logs = []
            for _ in range(2):
                r = subprocess.run(
                    args, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertIn('FAIL caption wider than widget', r.stdout)
                self.assertIn(NARROW_BTN, r.stdout)
                logs.append(r.stdout)
            self.assertEqual(logs[0].split('elapsed')[0],
                             logs[1].split('elapsed')[0])

            src, out, tr, segs = self._build(tmp, SHORT_CAPTION)
            args = [
                sys.executable, script, src, out,
                '--source-words-from', segs, '--translations', tr,
            ]
            logs = []
            for _ in range(2):
                r = subprocess.run(
                    args, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertNotIn('FAIL caption wider than widget', r.stdout)
                logs.append(r.stdout)
            self.assertEqual(logs[0].split('elapsed')[0],
                             logs[1].split('elapsed')[0])


class IdentifierTests(unittest.TestCase):
    """Quoted / form-name write/find/say spans must survive unless opted out."""

    def _build(self, tmp, translations, allow_translate=None):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_identifier_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        segs = os.path.join(tmp, 'segments.json')
        strip_text.strip_text(src, stripped)
        write_mapping(tr, translations, font, allow_translate=allow_translate)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, segs, tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, stripped, out, tr, segs

    def test_shipped_hits_see_attachment_a_and_schedule_q(self):
        hits = extract_segments.write_find_say_hits(
            QUOTE_LINE + ' ' + SCHED_LINE)
        snippets = {s for _, s in hits}
        kinds = {k for k, _ in hits}
        self.assertIn('quoted', kinds)
        self.assertIn('form-name', kinds)
        self.assertIn('Attachment A', snippets)
        self.assertIn('Schedule Q', snippets)

    def test_missing_identifier_spans_unit(self):
        keep = 'Escriba "Attachment A" arriba. Adjunte Schedule Q.'
        gone = 'Escriba "Anexo A" arriba. Adjunte Anexo Q.'
        spans = ['Attachment A', 'Schedule Q']
        self.assertEqual(verify.missing_identifier_spans(keep, spans), [])
        self.assertEqual(
            set(verify.missing_identifier_spans(gone, spans)),
            set(spans))
        self.assertEqual(
            verify.missing_identifier_spans(
                gone, spans, allow_translate=spans),
            [])
        self.assertEqual(
            verify.missing_identifier_spans(gone, spans, allow_translate=None),
            verify.missing_identifier_spans(gone, spans, allow_translate=[]))

    def test_keep_tokens_pass_vanish_fails_allow_translate_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, _, out, tr, segs = self._build(tmp, KEEP_IDENT_TR)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS write/find/say identifiers', log)
            self.assertNotIn('FAIL missing write/find/say identifiers', log)

            src, _, out, tr, segs = self._build(tmp, VANISH_IDENT_TR)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('FAIL missing write/find/say identifiers', log)
            self.assertIn('Attachment A', log)
            self.assertIn('Schedule Q', log)

            src, _, out, tr, segs = self._build(
                tmp, VANISH_IDENT_TR,
                allow_translate=['Attachment A', 'Schedule Q'])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS write/find/say identifiers', log)
            self.assertNotIn('FAIL missing write/find/say identifiers', log)

    def test_omit_translations_does_not_run_identifier_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, _, out, tr, segs = self._build(tmp, VANISH_IDENT_TR)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('write/find/say identifiers', log)
            self.assertNotIn('Attachment A', log)
            self.assertNotIn('Schedule Q', log)

    def test_verify_cli_twice_keep_and_twice_vanish(self):
        script = str(SCRIPTS / 'verify.py')
        with tempfile.TemporaryDirectory() as tmp:
            src, _, out, tr, segs = self._build(tmp, KEEP_IDENT_TR)
            args = [
                sys.executable, script, src, out,
                '--source-words-from', segs, '--translations', tr,
            ]
            logs = []
            for _ in range(2):
                r = subprocess.run(
                    args, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertIn('PASS write/find/say identifiers', r.stdout)
                logs.append(r.stdout)
            self.assertEqual(logs[0].split('elapsed')[0],
                             logs[1].split('elapsed')[0])

            src, _, out, tr, segs = self._build(tmp, VANISH_IDENT_TR)
            args = [
                sys.executable, script, src, out,
                '--source-words-from', segs, '--translations', tr,
            ]
            logs = []
            for _ in range(2):
                r = subprocess.run(
                    args, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertIn('FAIL missing write/find/say identifiers', r.stdout)
                self.assertIn('Attachment A', r.stdout)
                self.assertIn('Schedule Q', r.stdout)
                logs.append(r.stdout)
            self.assertEqual(logs[0].split('elapsed')[0],
                             logs[1].split('elapsed')[0])


class EmptyTargetTests(unittest.TestCase):
    """Authored empty/whitespace values are not translations."""

    def _build(self, tmp, empty_value):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_empty_target_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        segs = os.path.join(tmp, 'segments.json')
        strip_text.strip_text(src, stripped)
        write_mapping(tr, {
            SOURCE_SENTENCE: TARGET_SENTENCE,
            EMPTY_CORE: empty_value,
        }, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, segs, tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out, tr, segs

    def test_empty_translation_targets_unit(self):
        conf = {
            'skip': ['Print'],
            'translations': {
                EMPTY_CORE: '',
                'space': ' ',
                'nbsp': '\u00a0',
                'Name:': 'Name:',
                'Z': 'Z',
                'Print': '',
                'nullcore': None,
                'ok': 'hola',
            },
            'merges': [{'lines': ['merge first'], 'html': '  '}],
            'overrides': [{'contains': 'All other', 'parts': [{'text': ''}]}],
        }
        got = verify.empty_translation_targets(conf)
        self.assertIn(EMPTY_CORE, got)
        self.assertIn('space', got)
        self.assertIn('nbsp', got)
        self.assertIn('merge first', got)
        self.assertIn('All other', got)
        self.assertNotIn('Name:', got)
        self.assertNotIn('Z', got)
        self.assertNotIn('Print', got)
        self.assertNotIn('nullcore', got)
        self.assertNotIn('ok', got)

    def test_empty_space_nbsp_fail_happy_and_identity_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp, EMPTY_HAPPY)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('FAIL empty translation target', log)
            self.assertIn('PASS authored translations present', log)

            for blank in ('', ' ', '\u00a0'):
                src, out, tr, segs = self._build(tmp, blank)
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = verify.verify(src, out, translations=tr,
                                       source_words_from=segs)
                log = buf.getvalue()
                self.assertNotEqual(rc, 0, msg=log)
                self.assertIn('FAIL empty translation target', log)
                self.assertIn(EMPTY_CORE, log)

    def test_omit_translations_does_not_run_empty_target_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp, '')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('empty translation target', log)
            self.assertNotIn(EMPTY_CORE, log)

    def test_verify_cli_twice_empty_and_twice_happy(self):
        script = str(SCRIPTS / 'verify.py')
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._build(tmp, '')
            args = [
                sys.executable, script, src, out,
                '--source-words-from', segs, '--translations', tr,
            ]
            logs = []
            for _ in range(2):
                r = subprocess.run(
                    args, capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertIn('FAIL empty translation target', r.stdout)
                self.assertIn(EMPTY_CORE, r.stdout)
                logs.append(r.stdout)
            self.assertEqual(logs[0].split('elapsed')[0],
                             logs[1].split('elapsed')[0])

            src, out, tr, segs = self._build(tmp, EMPTY_HAPPY)
            args = [
                sys.executable, script, src, out,
                '--source-words-from', segs, '--translations', tr,
            ]
            logs = []
            for _ in range(2):
                r = subprocess.run(
                    args, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
                self.assertNotIn('FAIL empty translation target', r.stdout)
                logs.append(r.stdout)
            self.assertEqual(logs[0].split('elapsed')[0],
                             logs[1].split('elapsed')[0])


class RtlTextLayerTests(unittest.TestCase):
    def _retypeset_pair(self, tmp, source, target):
        # Arabic and Hebrew live in different Noto faces; ask for the one
        # this target actually needs.
        font = find_font_for(target)
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        doc = pymupdf.open()
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 80), source, fontsize=12)
        page.draw_rect(pymupdf.Rect(72, 120, 200, 140), color=(0, 0, 0), width=1)
        doc.save(src)
        doc.close()
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        write_mapping(tr, {source: target}, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, stripped, out, tr

    def test_arabic_actualtext_is_logical_layout_not_mirrored(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, stripped, out, tr = self._retypeset_pair(tmp, AR_SOURCE, AR_TARGET)
            doc = pymupdf.open(out)
            try:
                layer = doc[0].get_text().replace('\xa0', ' ')
                actuals = verify.extract_actualtext(doc[0])
                search = verify.page_search_text(doc[0])
                xs = []
                for b in doc[0].get_text('dict')['blocks']:
                    if b['type'] != 0:
                        continue
                    for line in b['lines']:
                        for s in line['spans']:
                            xs.append(s['bbox'][0])
            finally:
                doc.close()
            self.assertTrue(any(AR_TARGET in a for a in actuals), msg=actuals)
            self.assertIn(AR_TARGET, search.replace('\xa0', ' '))
            self.assertTrue(xs)
            self.assertLess(min(xs), 120, msg='layout was mirrored off the left origin')
            self.assertGreater(min(xs), 40)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr, min_ink=0.2)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS authored translations present', log)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, stripped, translations=tr, min_ink=0.2)
            self.assertNotEqual(rc, 0, msg=buf.getvalue())
            self.assertIn(AR_TARGET, buf.getvalue())

    def test_hebrew_logical_round_trip_not_mirrored(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, stripped, out, tr = self._retypeset_pair(tmp, HE_SOURCE, HE_TARGET)
            doc = pymupdf.open(out)
            try:
                search = verify.page_search_text(doc[0]).replace('\xa0', ' ')
                actuals = verify.extract_actualtext(doc[0])
                xs = [s['bbox'][0]
                      for b in doc[0].get_text('dict')['blocks'] if b['type'] == 0
                      for line in b['lines'] for s in line['spans']]
            finally:
                doc.close()
            self.assertIn(HE_TARGET, search)
            self.assertTrue(any(HE_TARGET in a for a in actuals), msg=actuals)
            self.assertTrue(xs)
            self.assertLess(min(xs), 120)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr, min_ink=0.2)
            self.assertEqual(rc, 0, msg=buf.getvalue())


class RtlLayoutTests(unittest.TestCase):
    def test_mirror_opt_in_flips_text_and_field_not_default(self):
        font = find_rtl_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out_ltr = os.path.join(tmp, 'out_ltr.pdf')
            out_rtl = os.path.join(tmp, 'out_rtl.pdf')
            tr_ltr = os.path.join(tmp, 'tr_ltr.json')
            tr_rtl = os.path.join(tmp, 'tr_rtl.json')
            doc = pymupdf.open()
            page = doc.new_page(width=612, height=792)
            page.insert_text((72, 80), AR_SOURCE, fontsize=12)
            tf = pymupdf.Widget()
            tf.field_name = 'Name'
            tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
            tf.rect = pymupdf.Rect(400, 70, 540, 90)
            page.add_widget(tf)
            doc.save(src)
            doc.close()
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            orig_w = widget_map(src)
            write_mapping(tr_ltr, {AR_SOURCE: AR_TARGET}, font)
            write_mapping(tr_rtl, {AR_SOURCE: AR_TARGET}, font, mirror=True)
            self.assertEqual(retypeset.retypeset(stripped, segs, tr_ltr, out_ltr), 0)
            self.assertEqual(retypeset.retypeset(stripped, segs, tr_rtl, out_rtl), 0)

            def min_x(path):
                d = pymupdf.open(path)
                try:
                    xs = [s['bbox'][0]
                          for b in d[0].get_text('dict')['blocks'] if b['type'] == 0
                          for line in b['lines'] for s in line['spans']]
                    return min(xs)
                finally:
                    d.close()

            self.assertLess(min_x(out_ltr), 120)
            self.assertGreater(min_x(out_rtl), 300)
            ltr_fields = widget_map(out_ltr)
            rtl_fields = widget_map(out_rtl)
            self.assertEqual(set(ltr_fields), set(orig_w))
            self.assertEqual(set(rtl_fields), set(orig_w))
            self.assertEqual(ltr_fields['Name'][0], orig_w['Name'][0])
            self.assertEqual(rtl_fields['Name'][0], orig_w['Name'][0])
            # Default keeps the field on the right; mirror flips it left.
            self.assertGreater(ltr_fields['Name'][1].x0, 300)
            self.assertLess(rtl_fields['Name'][1].x0, 220)
            d = pymupdf.open(out_rtl)
            try:
                actuals = verify.extract_actualtext(d[0])
            finally:
                d.close()
            self.assertTrue(any(AR_TARGET in a for a in actuals), msg=actuals)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out_rtl, translations=tr_rtl, min_ink=0.2)
            self.assertEqual(rc, 0, msg=buf.getvalue())


DOTS_SOURCE = 'Monthly income'
DOTS_LINE = 'Monthly income ................. $'


def build_dot_leader_pdf(path, text=DOTS_LINE, x=72, y=80, size=11):
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=200)
    page.insert_text((x, y), text, fontsize=size)
    doc.save(path)
    doc.close()


class ShapedLeaderTests(unittest.TestCase):
    """Goal 16 leftover: dot leaders on a Story-engine or RTL label."""

    def _run(self, tmp, target, font):
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'tr.json')
        build_dot_leader_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        result = json.loads(
            Path(tmp, 'segments.json').read_text(encoding='utf-8'))
        cores = {sg['core'] for sg in result['segments']}
        self.assertIn(DOTS_SOURCE, cores, msg=sorted(cores))
        write_mapping(tr, {DOTS_SOURCE: target}, font, skip=[])
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out, tr

    def leader_run(self, path):
        doc = pymupdf.open(path)
        try:
            text = doc[0].get_text()
        finally:
            doc.close()
        runs = re.findall(r'\.{3,}', text)
        return max(runs, key=len) if runs else ''

    def test_latin_label_still_gets_leaders_and_tail(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = self._run(tmp, 'Ingresos mensuales', font)
            self.assertTrue(len(self.leader_run(out)) >= 3,
                            msg=repr(self.leader_run(out)))
            doc = pymupdf.open(out)
            try:
                self.assertIn('$', doc[0].get_text())
            finally:
                doc.close()

    def test_shaped_label_keeps_its_leaders(self):
        font = find_rtl_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = self._run(tmp, AR_TARGET, font)
            leaders = self.leader_run(out)
            self.assertTrue(len(leaders) >= 3,
                            msg=f'shaped label lost its leaders: {leaders!r}')
            doc = pymupdf.open(out)
            try:
                page = doc[0]
                self.assertIn('$', page.get_text())
                self.assertTrue(
                    any(AR_TARGET in a
                        for a in verify.extract_actualtext(page)))
                # Leaders must not run through the label.
                dots = [w for w in page.get_text('words')
                        if set(w[4]) <= {'.'} and len(w[4]) >= 3]
                self.assertTrue(dots, msg=page.get_text('words'))
                self.assertGreater(min(d[0] for d in dots), 72.0)
            finally:
                doc.close()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr, min_ink=0.2)
            self.assertEqual(rc, 0, msg=buf.getvalue())

    def test_hebrew_label_keeps_its_leaders(self):
        font = find_font_for(HE_TARGET, what='Hebrew')
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr = self._run(tmp, HE_TARGET, font)
            self.assertTrue(len(self.leader_run(out)) >= 3,
                            msg=repr(self.leader_run(out)))

    def test_unmarked_shaped_target_fails_the_gate(self):
        self.assertTrue(verify.needs_shaping(AR_TARGET))
        self.assertTrue(verify.needs_shaping('\u0928\u092e\u0938\u094d\u0924\u0947'))
        self.assertFalse(verify.needs_shaping('Hola'))
        self.assertFalse(verify.needs_shaping(HE_TARGET))
        # Present in an /ActualText span: fine.
        self.assertEqual(
            verify.unmarked_shaped_targets([AR_TARGET], [AR_TARGET, 'Hola']),
            [])
        # Absent: the run was drawn glyph by glyph.
        self.assertEqual(
            verify.unmarked_shaped_targets(['something else'],
                                           [AR_TARGET, 'Hola']),
            [AR_TARGET])

    def test_arabic_target_drawn_glyph_by_glyph_fails_the_marks_gate(self):
        font = find_rtl_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            tr = os.path.join(tmp, 'tr.json')
            build_one_line_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            write_mapping(tr, {SHAPE_SOURCE: AR_TARGET}, font, skip=[])
            doc = pymupdf.open()
            page = doc.new_page(width=612, height=792)
            tw = pymupdf.TextWriter(page.rect)
            tw.append((72, 80), AR_TARGET,
                      font=pymupdf.Font(fontfile=str(font)), fontsize=12,
                      right_to_left=True)
            tw.write_text(page)
            doc.save(bad)
            doc.close()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, bad, translations=tr, min_ink=0.05)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('not drawn by the Story engine', log)

    def test_indic_target_drawn_glyph_by_glyph_fails_verify(self):
        font = find_devanagari_font()
        target = '\u0928\u092e\u0938\u094d\u0924\u0947 \u0926\u0941\u0928\u093f\u092f\u093e'
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'bad.pdf')
            tr = os.path.join(tmp, 'tr.json')
            build_one_line_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            write_mapping(tr, {SHAPE_SOURCE: target}, font, skip=[])
            # A TextWriter run: the logical string is in the text layer, but
            # nothing marks it, because nothing shaped it.
            doc = pymupdf.open()
            page = doc.new_page(width=612, height=792)
            tw = pymupdf.TextWriter(page.rect)
            tw.append((72, 80), target, font=pymupdf.Font(fontfile=str(font)),
                      fontsize=12)
            tw.write_text(page)
            doc.save(bad)
            doc.close()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, bad, translations=tr, min_ink=0.05)
            log = buf.getvalue()
            self.assertNotEqual(rc, 0, msg=log)
            self.assertIn('not drawn by the Story engine', log)


class ShapedScriptTests(unittest.TestCase):
    """Goal 16: runs whose target script needs shaping take the Story
    (HarfBuzz) path; unshaped Arabic in an output is a verify FAIL."""

    def _translate_one_line(self, tmp, target, font):
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'tr.json')
        build_one_line_pdf(src)
        strip_text.strip_text(src, stripped)
        extract_segments.extract_segments(src, outdir=tmp)
        write_mapping(tr, {SHAPE_SOURCE: target}, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
        return src, out, tr, rc, buf.getvalue()

    def test_needs_shaping_unit(self):
        self.assertTrue(retypeset.needs_shaping(AR_PHRASE))
        self.assertTrue(retypeset.needs_shaping(DV_PHRASE))
        self.assertTrue(retypeset.needs_shaping('สวัสดี'))
        self.assertFalse(retypeset.needs_shaping(HE_TARGET))
        self.assertFalse(retypeset.needs_shaping('Hello world'))
        self.assertFalse(retypeset.needs_shaping('申立人'))

    def test_arabic_target_is_shaped_and_on_baseline(self):
        font = find_rtl_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, rc, log = self._translate_one_line(tmp, AR_PHRASE, font)
            self.assertEqual(rc, 0, msg=log)
            doc = pymupdf.open(out)
            cps = raw_codepoints(doc[0])
            actual = verify.extract_actualtext(doc[0])
            bbox, origin = first_line_geometry(doc[0])
            rule = render_region(doc[0], pymupdf.Rect(150, 82, 300, 86))
            # Where the letters actually are, not where the font metadata
            # says the box is. Clipped above the rule at y=84, which starts
            # at x=60 and would otherwise be the leftmost ink.
            left = ink_left_edge(doc[0], pymupdf.Rect(60, 60, 300, 82))
            doc.close()
            self.assertTrue(AR_CONNECTED_FORMS & set(cps),
                            msg=f'no initial/medial Arabic forms in {[hex(c) for c in cps][:20]}')
            self.assertTrue(any(AR_PHRASE in a for a in actual), msg=actual)
            self.assertGreater(sum(1 for b in rule if b < 100), 50, msg='rule under the run was painted over')
            self.assertIsNotNone(left, msg='the shaped run drew no ink')
            # 2 pt, not 1.5: at 144 dpi one device pixel is 0.5 pt, and the
            # first column of anti-aliased stem ink lands a pixel or two in.
            self.assertAlmostEqual(left, 72.0, delta=2.0,
                                   msg=f'ink starts at {left}, bbox {bbox}')
            self.assertAlmostEqual(origin[1], 80.0, delta=1.5, msg=origin)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr, min_ink=0.2)
            self.assertEqual(rc, 0, msg=buf.getvalue())

    def test_unshaped_arabic_output_fails_verify(self):
        font = find_rtl_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            bad = os.path.join(tmp, 'unshaped.pdf')
            good = os.path.join(tmp, 'shaped.pdf')
            build_one_line_pdf(src)
            doc = pymupdf.open()
            page = doc.new_page(width=612, height=792)
            tw = pymupdf.TextWriter(page.rect)
            tw.append((72, 80), AR_PHRASE, font=pymupdf.Font(fontfile=str(font)),
                      fontsize=12, right_to_left=True)
            tw.write_text(page)
            doc.save(bad)
            doc.close()
            doc = pymupdf.open()
            page = doc.new_page(width=612, height=792)
            css = "@font-face {font-family: t; src: url(%s);} body {font-family: t; margin: 0; padding: 0;}" % os.path.basename(str(font))
            page.insert_htmlbox(pymupdf.Rect(72, 70, 540, 86),
                                '<div style="font-size:12px; line-height:1">%s</div>' % AR_PHRASE,
                                css=css, archive=pymupdf.Archive(os.path.dirname(str(font))))
            doc.save(good)
            doc.close()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, bad, min_ink=0.2)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('unshaped', log.lower())
            buf = io.StringIO()
            with redirect_stdout(buf):
                verify.verify(src, good, min_ink=0.2)
            self.assertNotIn('unshaped', buf.getvalue().lower())

    def test_devanagari_target_uses_story_path(self):
        font = find_devanagari_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, rc, log = self._translate_one_line(tmp, DV_PHRASE, font)
            self.assertEqual(rc, 0, msg=log)
            region = pymupdf.Rect(60, 60, 400, 83)   # above the rule at y=84
            out_doc = pymupdf.open(out)
            got = render_region(out_doc[0], region)
            actual = verify.extract_actualtext(out_doc[0])
            out_doc.close()
            ref = pymupdf.open()
            page = ref.new_page(width=612, height=792)
            css = "@font-face {font-family: t; src: url(%s);} body {font-family: t; margin: 0; padding: 0;}" % os.path.basename(str(font))
            page.insert_htmlbox(pymupdf.Rect(72, 80 - 0.8 * 12, 540, 80 - 0.8 * 12 + 15),
                                '<div style="font-size:12px; line-height:1">%s</div>' % DV_PHRASE,
                                css=css, archive=pymupdf.Archive(os.path.dirname(str(font))))
            story_ref = render_region(page, region)
            tw_doc = pymupdf.open()
            tw_page = tw_doc.new_page(width=612, height=792)
            tw = pymupdf.TextWriter(tw_page.rect)
            tw.append((72, 80), DV_PHRASE, font=pymupdf.Font(fontfile=str(font)), fontsize=12)
            tw.write_text(tw_page)
            tw_ref = render_region(tw_page, region)
            d_story = pixel_diff(got, story_ref)
            d_tw = pixel_diff(got, tw_ref)
            self.assertLess(d_story, d_tw, msg=f'story diff {d_story} vs textwriter diff {d_tw}')
            self.assertLess(d_story, 0.02 * len(got))
            self.assertTrue(any(DV_PHRASE in a for a in actual), msg=actual)

    def test_shaped_run_in_narrow_gap_fails_overflow(self):
        font = find_rtl_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'tr.json')
            build_squeeze_pdf(src)
            strip_text.strip_text(src, stripped)
            extract_segments.extract_segments(src, outdir=tmp)
            write_mapping(tr, {SQUEEZE_CORE: ' '.join([AR_PHRASE] * 4)}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn('scaled below', buf.getvalue())
            self.assertFalse(os.path.exists(out))


class OverrideMarkerTests(unittest.TestCase):
    """Goal 11: an override replaces the whole span, so its parts must keep
    the source marker (d.) and tail ($); verify --translations fails if not."""

    def _run(self, tmp, parts, font):
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_override_pdf(src)
        strip_text.strip_text(src, stripped)
        res = extract_segments.extract_segments(src, outdir=tmp)
        self.assertTrue(any(w.get('kind') == 'inner-gap' for w in res['warnings']), msg=res['warnings'])
        override_mapping(tr, font, parts)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return src, out, tr, os.path.join(tmp, 'segments.json')

    def test_override_marker_misses_unit(self):
        segs = [{'page': 0, 'text': OVERRIDE_LINE, 'marker': 'd.', 'core': OVERRIDE_CORE,
                 'dots': '....', 'tail': '$'},
                {'page': 0, 'text': OVERRIDE_OTHER, 'marker': '', 'core': OVERRIDE_OTHER,
                 'dots': '', 'tail': ''}]
        conf = {'overrides': [{'page': 0, 'contains': OVERRIDE_CORE, 'parts': PARTS_DROP}]}
        self.assertEqual(verify.override_marker_misses(conf, segs),
                         [(OVERRIDE_CORE, 'd.'), (OVERRIDE_CORE, '$')])
        conf['overrides'][0]['parts'] = PARTS_KEEP
        self.assertEqual(verify.override_marker_misses(conf, segs), [])
        conf['overrides'][0]['contains'] = 'Other text'
        self.assertEqual(verify.override_marker_misses(conf, segs), [])

    def test_override_keeps_marker_and_tail_passes(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._run(tmp, PARTS_KEEP, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr, min_ink=0.2)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS override parts keep', log)

    def test_override_drops_marker_and_tail_fails(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._run(tmp, PARTS_DROP, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr, min_ink=0.2)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL override', log)
            self.assertIn('d.', log)
            self.assertIn('$', log)
            self.assertIn(OVERRIDE_CORE, log)

    def test_omit_translations_does_not_run_override_gate(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._run(tmp, PARTS_DROP, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, min_ink=0.2)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('override', log.lower())

    def test_segments_flag_and_sibling_default_cli(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs = self._run(tmp, PARTS_DROP, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.main([src, out, '--translations', tr, '--segments', segs, '--min-ink', '0.2'])
            self.assertEqual(rc, 1, msg=buf.getvalue())
            self.assertIn('FAIL override', buf.getvalue())
            # A mapping with no segments.json beside it and no flag: the gate is skipped, not failed.
            alone = os.path.join(tmp, 'alone')
            os.makedirs(alone)
            tr2 = os.path.join(alone, 'translations.json')
            shutil.copy(tr, tr2)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.main([src, out, '--translations', tr2, '--min-ink', '0.2'])
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('SKIP override', log)


class ProviderAgnosticTests(unittest.TestCase):
    def test_rtl_docs_match_measured_behaviour(self):
        fonts = (Path(__file__).resolve().parents[1] / 'references' / 'fonts.md')
        text = fonts.read_text(encoding='utf-8')
        self.assertIn('ActualText', text)
        self.assertIn('not mirrored', text)
        self.assertIn('mirror', text)
        self.assertNotIn('pymupdf TextWriter does not shape or bidi-reorder text', text)
        self.assertNotIn('Neither ships in the default pipeline yet', text)

    def test_scripts_have_no_vendor_client(self):
        banned = (
            'openai', 'anthropic', 'claude', 'httpx', 'requests.get',
            'api_key', 'API_KEY', 'generativeai', 'google.genai',
        )
        for py in SCRIPTS.glob('*.py'):
            text = py.read_text(encoding='utf-8')
            for token in banned:
                self.assertNotIn(token, text, msg=f'{py.name} mentions {token}')


LIG_HTML = ('La oficina del secretario revisara toda declaracion presentada '
            'antes de la fecha de la audiencia y enviara una copia con la '
            'firma oficial a cada parte nombrada en el encabezado.')


class StoryLigatureTests(unittest.TestCase):
    """Row 24: the Story engine shapes Latin too.

    HarfBuzz applies `liga`/`clig` by default and MuPDF 1.28 honours
    neither `font-variant-ligatures: none` nor `font-feature-settings`
    (both measured on the constructed paragraph below), so a merged
    Spanish paragraph was drawn with the fi glyph and its text layer said
    U+FB01 — or U+007F once the font was subsetted, where nothing caught
    it at all. Two models hit this independently on canary run 2.
    """

    def _job(self, tmp, font, html=LIG_HTML):
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_paragraph_pdf(src, pages=1)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        conf = {
            'fonts': {'regular': str(font), 'bold': str(font)},
            'translations': {'Page 1 note here.': 'Nota de la pagina 1.'},
            'merges': [{'page': 0, 'lines': PARA_LINES, 'html': html,
                        'align': 'left'}],
            'overrides': [], 'center': [], 'skip': [],
        }
        Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                            encoding='utf-8')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        doc = pymupdf.open(out)
        try:
            layer = doc[0].get_text()
        finally:
            doc.close()
        return src, out, tr, os.path.join(tmp, 'segments.json'), layer

    def test_a_merged_paragraph_says_what_the_author_wrote(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs, layer = self._job(tmp, font)
            self.assertIn('oficina', layer)
            self.assertIn('firma', layer)
            self.assertEqual(
                [c for c in layer if 0xFB00 <= ord(c) <= 0xFB06], [])
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS authored translations present', log)
            self.assertIn('PASS canonical text layer', log)

    def test_a_subset_font_says_it_too(self):
        """The silent half: pyftsubset keeps the ligature and drops U+FB01
        from the cmap, so the layer carried U+007F and only a run with
        --translations would ever have noticed."""
        with tempfile.TemporaryDirectory() as tmp:
            subset = os.path.join(tmp, 'subset.ttf')
            pre = os.path.join(tmp, 'pre.json')
            Path(pre).write_text(json.dumps({
                'fonts': {}, 'translations': {'x': LIG_HTML},
                'merges': [], 'overrides': [], 'center': [], 'skip': [],
            }, ensure_ascii=False), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.main([str(find_test_font()), pre, subset])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            # The premise: cmap cannot find this glyph, GSUB can.
            self.assertFalse(pymupdf.Font(fontfile=subset).has_glyph(0xFB01))
            self.assertIn('fi', retypeset.ligature_gid_map(
                subset, set(LIG_HTML)).values())

            src, out, tr, segs, layer = self._job(tmp, subset)
            self.assertIn('oficina', layer)
            self.assertNotIn('\x7f', layer)

    def test_an_inline_markup_line_says_it_too(self):
        """place_story_line is the Story engine as well."""
        font = find_test_font()
        marked = 'La <b>oficina</b> debe recibir la firma hoy.'
        plain = 'La oficina debe recibir la firma hoy.'
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_plain_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {SOURCE_SENTENCE: marked}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, segs, tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            doc = pymupdf.open(out)
            try:
                layer = doc[0].get_text()
            finally:
                doc.close()
            self.assertIn(plain, verify.normalize_ws_nbsp(layer))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, out, translations=tr,
                                   source_words_from=segs)
            self.assertEqual(rc, 0, msg=buf.getvalue())

    def test_the_gate_fails_a_ligature_that_is_still_in_the_layer(self):
        """Build the defect back in and the gate must name it, with or
        without --translations: the subset case had no other witness."""
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs, layer = self._job(tmp, font)
            f = pymupdf.Font(fontfile=str(font))
            gidmap = {f.has_glyph(ord('f')): '\ufb01'}
            gidmap.pop(0, None)
            self.assertTrue(gidmap, msg='test font has no f')
            block = retypeset._override_block(gidmap)
            drifted = os.path.join(tmp, 'drifted.pdf')
            pdf = pikepdf.open(out)
            try:
                patched = 0
                for obj in pdf.objects:
                    try:
                        tu = obj.get('/ToUnicode')
                    except Exception:
                        continue
                    if tu is None:
                        continue
                    data = bytes(tu.read_bytes())
                    i = data.rfind(b'endcmap')
                    if i < 0:
                        continue
                    obj.ToUnicode = pdf.make_stream(
                        data[:i] + block + data[i:])
                    patched += 1
                self.assertTrue(patched, msg='no /ToUnicode to drift')
                pdf.save(drifted)
            finally:
                pdf.close()
            doc = pymupdf.open(drifted)
            try:
                self.assertIn('\ufb01', doc[0].get_text(),
                              msg='the fixture did not actually drift')
            finally:
                doc.close()
            for kwargs in ({'translations': tr, 'source_words_from': segs},
                           {}):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = verify.verify(src, drifted, **kwargs)
                log = buf.getvalue()
                self.assertNotEqual(rc, 0, msg=log)
                self.assertIn('FAIL text layer is not canonical', log)
                self.assertIn('U+FB01', log)

    def test_only_authored_ligatures_are_mapped(self):
        font = str(find_test_font())
        self.assertEqual(retypeset.ligature_gid_map(font, set('xyz')), {})
        self.assertIn('fi', retypeset.ligature_gid_map(font, set('fi')).values())
        self.assertEqual(retypeset.ligature_gid_map('no-such.ttf', set('fi')), {})



BAND_SOURCE = 'Applicant name and mailing address'
BAND_TARGET = 'Nombre y direccion postal del solicitante'   # lands at 0.88x
BAND_FITS = 'Nombre del solicitante'


def build_band_pdf(path):
    """A label with a field close on its right: a longer target must shrink,
    but the ink ratio stays comparable so the other gates keep their say."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 80), BAND_SOURCE, fontsize=12)
    tf = pymupdf.Widget()
    tf.field_name = 'X'
    tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    tf.rect = pymupdf.Rect(275, 68, 395, 88)
    page.add_widget(tf)
    doc.save(path)
    doc.close()


class ShrinkBandTests(unittest.TestCase):
    """Row 25: a run between 0.7x and 1.0x was placed and mentioned nowhere.

    On canary run 2 the same merged paragraph shipped at 0.81x and 0.91x
    under two deliveries that both said nothing had shrunk — one of them
    ticking "no over-shrunk text - allow_scale is EMPTY". The floor is
    unchanged; what changes is that the author is told.
    """

    def _build(self, tmp, target):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_band_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        write_mapping(tr, {BAND_SOURCE: target}, font)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        log = buf.getvalue()
        self.assertEqual(rc, 0, msg=log)
        return src, out, tr, os.path.join(tmp, 'segments.json'), log

    def _report(self, out):
        path = os.path.join(os.path.dirname(out), retypeset.SCALE_REPORT)
        self.assertTrue(os.path.isfile(path), msg='no scale report written')
        with open(path, encoding='utf-8') as f:
            return json.load(f)

    def _verify_log(self, src, out, tr, segs):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = verify.verify(src, out, translations=tr,
                               source_words_from=segs)
        return rc, buf.getvalue()

    def test_a_run_in_the_band_is_printed_written_and_reviewed(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs, log = self._build(tmp, BAND_TARGET)
            self.assertIn('scaled runs (1)', log)
            self.assertIn(BAND_SOURCE, log.split('scaled runs')[1])

            report = self._report(out)
            self.assertEqual(len(report), 1)
            self.assertEqual(report[0]['page'], 0)
            self.assertEqual(report[0]['key'], BAND_SOURCE)
            self.assertGreater(report[0]['ratio'], retypeset.SCALE_MIN)
            self.assertLess(report[0]['ratio'], 1.0)

            rc, vlog = self._verify_log(src, out, tr, segs)
            self.assertEqual(rc, 0, msg=vlog)      # a REVIEW, never a FAIL
            self.assertIn('REVIEW scaled runs (1)', vlog)
            self.assertIn(f'{report[0]["ratio"]:.2f}x', vlog)

    def test_a_full_size_build_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs, log = self._build(tmp, BAND_FITS)
            self.assertNotIn('scaled runs', log)
            self.assertEqual(self._report(out), [])
            rc, vlog = self._verify_log(src, out, tr, segs)
            self.assertEqual(rc, 0, msg=vlog)
            self.assertIn('PASS scaled runs: none', vlog)

    def test_an_older_build_still_verifies(self):
        """No report beside the output is a SKIP with a note, not a pass and
        not a failure: builds from before row 25 must still verify."""
        with tempfile.TemporaryDirectory() as tmp:
            src, out, tr, segs, log = self._build(tmp, BAND_TARGET)
            os.remove(os.path.join(tmp, retypeset.SCALE_REPORT))
            rc, vlog = self._verify_log(src, out, tr, segs)
            self.assertEqual(rc, 0, msg=vlog)
            self.assertIn('SKIP scaled runs', vlog)
            self.assertNotIn('PASS scaled runs', vlog)
            self.assertIsNone(verify.scale_report_for(out))

    def test_a_merge_in_the_band_is_reported_too(self):
        """The canary's actual defect: the paragraph, not the label."""
        font = find_test_font()
        long_html = (LIG_HTML + ' Toda parte debe conservar una copia de '
                     'este aviso para sus registros y presentarla cuando '
                     'la secretaria lo solicite en la audiencia.')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_paragraph_pdf(src, pages=1)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            Path(tr).write_text(json.dumps({
                'fonts': {'regular': str(font), 'bold': str(font)},
                'translations': {'Page 1 note here.': 'Nota de la pagina 1.'},
                'merges': [{'page': 0, 'lines': PARA_LINES,
                            'html': long_html, 'align': 'left'}],
                'overrides': [], 'center': [], 'skip': [],
            }, ensure_ascii=False), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            report = self._report(out)
            keys = {r['key'] for r in report}
            self.assertTrue(
                any(PARA_LINES[0] in k for k in keys),
                msg=f'the merge is not in the report: {report}')
            self.assertIn('scaled runs', log)

    def test_the_floor_is_where_it_was(self):
        self.assertEqual(retypeset.SCALE_MIN, 0.7)



# The real Judicial Council title, with its em dash flattened to a hyphen:
# helv redraws U+2014 as something else, and the dash is not what this row
# is about. `FL` (two letters) and `100` (not a word) are.
FL_TITLE = 'FL-100 Petition-Marriage/Domestic Partnership'
FL_TITLE_EM = 'FL-100 Petition\u2014Marriage/Domestic Partnership'
# Short, and the title early: the fixture page is 400 pt wide and a 7 pt
# notice line runs off it, so a long preamble would clip the quote itself.
FL_LINE = 'Traduccion no oficial de ' + FL_TITLE + '. Solo informativa.'


class KeptTitleTokenTests(unittest.TestCase):
    """Row 27: row 20's keep compares a run against the original /Title, but
    the scan cannot see every part of a real title. On FL-100 `FL` is under
    the four-letter Latin floor and `100` is not a word, so the run the scan
    builds is `Petition Marriage Domestic Partnership` and the title's key
    never equalled it. Fable allowlisted two spellings by guesswork."""

    def test_the_title_key_uses_the_branch_word_floor(self):
        run = 'Petition Marriage Domestic Partnership'
        self.assertEqual(verify._run_key(FL_TITLE), verify._run_key(run))
        self.assertTrue(verify._kept(run, [FL_TITLE], []))
        # The dash the issuer actually uses makes no difference either.
        self.assertTrue(verify._kept(run, [FL_TITLE_EM], []))

    def test_a_part_of_the_title_is_still_running_text(self):
        for short in ('Petition Marriage Domestic',
                      'Marriage Domestic Partnership'):
            self.assertFalse(verify._kept(short, [FL_TITLE], []),
                             msg=f'{short} is not the whole title')

    def test_a_run_that_contains_the_title_is_still_a_leak(self):
        self.assertFalse(verify._kept(
            'the FL-100 Petition Marriage Domestic Partnership form',
            [FL_TITLE], []))

    def test_the_spaceless_branch_is_unchanged(self):
        # CJK compares with whitespace removed and nothing dropped.
        self.assertEqual(verify._run_key('\u5e73\u62102 \u5e74', script='CJK'),
                         '\u5e73\u62102\u5e74')
        self.assertTrue(verify._kept('\u7533\u8acb\u66f8', ['\u7533\u8acb\u66f8'],
                                     [], script='CJK'))

    def test_a_notice_quoting_a_numbered_title_is_kept_end_to_end(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            noticed = os.path.join(tmp, 'noticed.pdf')
            build_titled_pdf(src, title=FL_TITLE)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {
                FL_TITLE: 'FL-100 Peticion-Matrimonio/Pareja de hecho',
                NOTICE_SENTENCE: 'Devuelva este formulario a la oficina.',
                NOTICE_ISSUER: NOTICE_ISSUER,
            }, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, segs, tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            add_notice(out, noticed, line=FL_LINE)

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, noticed, source_words_from=segs,
                                   allow=[NOTICE_ISSUER])
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('PASS no untranslated running text', log)
            note = [l for l in log.splitlines() if l.startswith('note:')]
            self.assertEqual(len(note), 1, msg=log)
            self.assertIn('Petition', note[0])

    def test_a_longer_run_around_the_title_still_leaks(self):
        """The keep is the title, not a prefix of it: one more source word
        beside the quote and the run is running text again. (Dropping a
        word cannot be tested here — the hyphen makes `Petition-Marriage`
        one token, so a shortened quote falls under the three-word
        threshold and is isolated rather than running text.)"""
        font = find_test_font()
        broken = FL_LINE.replace(FL_TITLE, FL_TITLE + ' Form')
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            noticed = os.path.join(tmp, 'noticed.pdf')
            build_titled_pdf(src, title=FL_TITLE)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {
                FL_TITLE: 'FL-100 Peticion-Matrimonio/Pareja de hecho',
                NOTICE_SENTENCE: 'Devuelva este formulario a la oficina.',
                NOTICE_ISSUER: NOTICE_ISSUER,
            }, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, segs, tr, out)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            add_notice(out, noticed, line=broken)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = verify.verify(src, noticed, source_words_from=segs,
                                   allow=[NOTICE_ISSUER])
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('FAIL untranslated running text', log)



ANCHOR_LABEL = 'BRANCH:'
ANCHOR_TARGET = 'SUCURSAL Y CIUDAD:'
ANCHOR_EDGE = 200.0


def build_right_anchor_pdf(path, neighbour_x=None):
    """A right-anchored label with a field immediately on its right, and
    optionally a neighbour close on its left."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=300)
    helv = pymupdf.Font('helv')
    w = helv.text_length(ANCHOR_LABEL, 11)
    page.insert_text((ANCHOR_EDGE - w, 80), ANCHOR_LABEL, fontsize=11)
    tf = pymupdf.Widget()
    tf.field_name = 'X'
    tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    tf.rect = pymupdf.Rect(ANCHOR_EDGE + 4, 68, 400, 88)
    page.add_widget(tf)
    if neighbour_x is not None:
        page.insert_text((neighbour_x, 80), 'ID', fontsize=11)
    doc.save(path)
    doc.close()


class RightAnchorRoomTests(unittest.TestCase):
    """Row 28: a `right` core keeps the source's right edge and grows
    leftward, but its width budget was the room to the RIGHT of the
    original origin — which on a form is the field the label names. On
    FL-100 that shrank labels with free room on their left (`SUCURSAL:`,
    `Pág. N de 3`) for no reason: measured here at 0.47x, a hard FAIL,
    where the label in fact fits at full size."""

    def _run(self, tmp, neighbour_x=None, extra=None):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_right_anchor_pdf(src, neighbour_x)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        targets = {ANCHOR_LABEL: ANCHOR_TARGET}
        targets.update(extra or {})
        write_mapping(tr, targets, font, right=[ANCHOR_LABEL])
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        self.assertEqual(rc, 0, msg=buf.getvalue())
        return out, span_edges(out), buf.getvalue()

    def _size_of(self, path, text):
        doc = pymupdf.open(path)
        try:
            for b in doc[0].get_text('dict')['blocks']:
                for line in b.get('lines', []):
                    for sp in line['spans']:
                        if verify.normalize_ws_nbsp(sp['text']) == text:
                            return sp['size']
        finally:
            doc.close()
        raise AssertionError(f'{text!r} not in {path}')

    def test_room_on_the_left_means_no_shrink(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, edges, log = self._run(tmp)
            x0, x1 = edges[ANCHOR_TARGET]
            self.assertAlmostEqual(x1, ANCHOR_EDGE, delta=1.0)
            self.assertAlmostEqual(self._size_of(out, ANCHOR_TARGET), 11.0,
                                   delta=0.01)
            # A translation this much longer than the source would have been
            # measured against the field on its right and shrunk to 0.47x.
            self.assertNotIn('scaled runs', log)
            self.assertGreater(x0, 32.0)

    def test_a_neighbour_on_the_left_still_bounds_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, edges, log = self._run(tmp, neighbour_x=100.0,
                                        extra={'ID': 'ID'})
            x0, x1 = edges[ANCHOR_TARGET]
            self.assertAlmostEqual(x1, ANCHOR_EDGE, delta=1.0)
            size = self._size_of(out, ANCHOR_TARGET)
            self.assertLess(size, 11.0)
            self.assertGreater(size / 11.0, retypeset.SCALE_MIN)
            # It stops clear of the neighbour's right edge, not over it.
            self.assertGreaterEqual(x0, edges['ID'][1])
            self.assertIn('scaled runs', log)

    def test_a_plain_label_is_measured_on_its_right_as_before(self):
        """Not in `right`: the budget is still the room to the right, so the
        same target against the same field shrinks exactly as it used to."""
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_right_anchor_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            write_mapping(tr, {ANCHOR_LABEL: ANCHOR_TARGET}, font)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('scaled below', log)



BOX_LINES = ['The clerk will review every declaration filed before the hearing',
             'and will mail one conformed copy back to each named party.']
BOX_HTML = ('El secretario revisara toda declaracion presentada antes de la '
            'fecha de la audiencia y enviara por correo una copia conformada '
            'a cada parte nombrada en el encabezado de este procedimiento.')
# One line taller than the union of the two source lines (~y 52-77).
BOX_RECT = [40.0, 52.0, 380.0, 96.0]


def build_two_line_paragraph_pdf(path, widget=None):
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=300)
    for i, line in enumerate(BOX_LINES):
        page.insert_text((40, 60 + 14 * i), line, fontsize=9)
    page.insert_text((40, 160), 'Page 1 note here.', fontsize=9)
    if widget:
        tf = pymupdf.Widget()
        tf.field_name = 'X'
        tf.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        tf.rect = pymupdf.Rect(*widget)
        page.add_widget(tf)
    doc.save(path)
    doc.close()


class MergeBoxTests(unittest.TestCase):
    """Row 26: a merge is re-flowed into the union of its member lines, so a
    two-line paragraph whose target needs three had two outcomes on canary
    run 2 — the engine shrinks it (0.81x, 0.91x), or the author declines the
    merge and hard-codes the source's wrap points into the target. Nothing
    let the author say "this paragraph may be one line taller"."""

    def _run(self, tmp, box=None, widget=None):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_two_line_paragraph_pdf(src, widget)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        merge = {'page': 0, 'lines': BOX_LINES, 'html': BOX_HTML,
                 'align': 'left'}
        if box is not None:
            merge['box'] = box
        Path(tr).write_text(json.dumps({
            'fonts': {'regular': str(font), 'bold': str(font)},
            'translations': {'Page 1 note here.': 'Nota de la pagina 1.'},
            'merges': [merge], 'overrides': [], 'center': [], 'skip': [],
        }, ensure_ascii=False), encoding='utf-8')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        return rc, out, tmp, buf.getvalue()

    def _lines(self, out):
        """(size, y0, y1) of every placed span, top to bottom."""
        doc = pymupdf.open(out)
        try:
            got = [(round(sp['size'], 2), round(sp['bbox'][1], 1),
                    round(sp['bbox'][3], 1))
                   for b in doc[0].get_text('dict')['blocks']
                   for line in b.get('lines', []) for sp in line['spans']]
        finally:
            doc.close()
        return sorted(got, key=lambda t: t[1])

    def test_without_a_box_the_paragraph_cannot_fit(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out, _, log = self._run(tmp)
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('scaled below', log)
            self.assertFalse(os.path.isfile(out))

    def test_a_box_one_line_taller_places_at_full_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out, work, log = self._run(tmp, box=BOX_RECT)
            self.assertEqual(rc, 0, msg=log)
            with open(os.path.join(work, retypeset.SCALE_REPORT),
                      encoding='utf-8') as f:
                self.assertEqual(json.load(f), [], msg='it should not shrink')
            lines = [l for l in self._lines(out) if l[1] < 140]
            self.assertEqual(len(lines), 3, msg=f'{lines}')
            # The third line lands below the source's last line and inside
            # the box the author drew.
            self.assertGreater(lines[2][1], 77.0)
            self.assertLess(lines[2][2], BOX_RECT[3])

    def test_a_box_over_a_widget_still_places(self):
        """The author chose the rect; the visual pass is the check, not a
        gate. Geometry must not veto it."""
        with tempfile.TemporaryDirectory() as tmp:
            rc, out, _, log = self._run(tmp, box=BOX_RECT,
                                        widget=(300, 78, 400, 96))
            self.assertEqual(rc, 0, msg=log)
            self.assertEqual(len([l for l in self._lines(out) if l[1] < 140]), 3)

    def test_a_malformed_box_is_refused_not_guessed(self):
        for bad in ([40, 52, 380], [40, 96, 380, 52], 'wide'):
            with tempfile.TemporaryDirectory() as tmp:
                rc, out, _, log = self._run(tmp, box=bad)
                self.assertEqual(rc, 1, msg=f'{bad}: {log}')
                self.assertIn('merge box', log)
                self.assertFalse(os.path.isfile(out))

    def test_proposals_carry_a_null_box(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            build_paragraph_pdf(src, pages=1)
            extract_segments.extract_segments(src, outdir=tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pipeline.propose_merges(tmp)
            self.assertEqual(rc, 0, msg=buf.getvalue())
            with open(os.path.join(tmp, 'merges_proposed.json'),
                      encoding='utf-8') as f:
                proposals = json.load(f)['merges']
            self.assertTrue(proposals)
            for m in proposals:
                self.assertIsNone(m['box'])
            self.assertIn('box is null', buf.getvalue())



def build_two_page_override_pdf(path):
    """The same inner-gap row on both pages; only page 0 gets an override."""
    doc = pymupdf.open()
    for n in range(2):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 100), OVERRIDE_LINE, fontsize=11)
        page.insert_text((72, 140), f'Other text line {n + 1}.', fontsize=11)
    doc.save(path)
    doc.close()


class OverridePlainValueTests(unittest.TestCase):
    """Row 29: an override replaces its whole span with explicit parts, but
    the coverage check still demanded a non-null translation for the core
    and verify's placement gate then wanted that never-drawn value in the
    layer. On FL-100 the author wrote phantom values to satisfy two checks
    and qa_check flagged them (13 warnings) for length and added numbers."""

    def _job(self, tmp, core_value, parts=PARTS_KEEP):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_override_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        Path(tr).write_text(json.dumps({
            'fonts': {'regular': str(font), 'bold': str(font)},
            'translations': {OVERRIDE_CORE: core_value,
                             OVERRIDE_OTHER: 'Otra linea.'},
            'merges': [],
            'overrides': [{'page': 0, 'contains': OVERRIDE_CORE,
                           'parts': parts}],
            'center': [], 'skip': [],
        }, ensure_ascii=False), encoding='utf-8')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        return rc, src, out, tr, os.path.join(tmp, 'segments.json'), buf.getvalue()

    def test_a_covered_core_needs_no_plain_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, src, out, tr, segs, log = self._job(tmp, None)
            self.assertEqual(rc, 0, msg=log)
            doc = pymupdf.open(out)
            try:
                layer = doc[0].get_text()
            finally:
                doc.close()
            self.assertIn('d. Ayuda', verify.normalize_ws_nbsp(layer))
            buf = io.StringIO()
            with redirect_stdout(buf):
                vrc = verify.verify(src, out, translations=tr,
                                    source_words_from=segs)
            vlog = buf.getvalue()
            self.assertEqual(vrc, 0, msg=vlog)
            self.assertIn('PASS authored translations present', vlog)
            self.assertIn('PASS override parts keep markers and tails', vlog)

    def test_the_gate_wants_the_parts_and_not_the_plain_value(self):
        conf = {'translations': {OVERRIDE_CORE: None,
                                 OVERRIDE_OTHER: 'Otra linea.'},
                'overrides': [{'page': 0, 'contains': OVERRIDE_CORE,
                               'parts': PARTS_KEEP}]}
        targets = verify.collect_translation_targets(conf)
        self.assertIn('d. Ayuda', targets)
        self.assertIn('Otra linea.', targets)
        self.assertNotIn('Ayuda', [t for t in targets if t == 'Ayuda'])

    def test_an_uncovered_occurrence_still_fails_and_names_its_page(self):
        font = find_test_font()
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_two_page_override_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            Path(tr).write_text(json.dumps({
                'fonts': {'regular': str(font), 'bold': str(font)},
                'translations': {OVERRIDE_CORE: None,
                                 'Other text line 1.': 'Otra linea 1.',
                                 'Other text line 2.': 'Otra linea 2.'},
                'merges': [],
                'overrides': [{'page': 0, 'contains': OVERRIDE_CORE,
                               'parts': PARTS_KEEP}],
                'center': [], 'skip': [],
            }, ensure_ascii=False), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('untranslated segments', log)
            self.assertIn('p1', log)
            self.assertNotIn('p0', log)
            self.assertFalse(os.path.isfile(out))

    def test_qa_check_does_not_flag_a_null_covered_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = os.path.join(tmp, 'translations.json')
            Path(tr).write_text(json.dumps({
                'fonts': {}, 'merges': [], 'center': [], 'skip': [],
                'translations': {OVERRIDE_CORE: None,
                                 OVERRIDE_OTHER: 'Otra linea.'},
                'overrides': [{'page': 0, 'contains': OVERRIDE_CORE,
                               'parts': PARTS_KEEP}],
            }, ensure_ascii=False), encoding='utf-8')
            findings = qa_check.qa_check(tr)
            self.assertEqual([f for f in findings if f['core'] == OVERRIDE_CORE],
                             [])

    def test_a_plain_null_with_no_override_still_fails(self):
        """The null is legal only where an override covers it."""
        with tempfile.TemporaryDirectory() as tmp:
            rc, src, out, tr, segs, log = self._job(tmp, 'Ayuda')
            self.assertEqual(rc, 0, msg=log)
        with tempfile.TemporaryDirectory() as tmp:
            font = find_test_font()
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            build_override_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            strip_text.strip_text(src, stripped)
            Path(tr).write_text(json.dumps({
                'fonts': {'regular': str(font), 'bold': str(font)},
                'translations': {OVERRIDE_CORE: 'Ayuda',
                                 OVERRIDE_OTHER: None},
                'merges': [], 'overrides': [], 'center': [], 'skip': [],
            }, ensure_ascii=False), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(
                    stripped, os.path.join(tmp, 'segments.json'), tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 1, msg=log)
            self.assertIn(OVERRIDE_OTHER, log)



# compliance.md §1's wording, in the target language, quoting the source
# title as one unit. The bold lead-in is the half before the weight split.
NOTICE_LEAD = 'Traduccion solo informativa.'
NOTICE_BODY = ('Esta es una traduccion no oficial de ' + NOTICE_TITLE +
               '. Debe presentar la version oficial en ingles.')
NOTICE_BOX = [40.0, 240.0, 360.0, 285.0]


class NoticeChannelTests(unittest.TestCase):
    """P7: the notice compliance.md requires is the one thing an author must
    add that is not the translation of an existing string, and the pipeline
    had no way to add it. Four of five canary runs on a form that needs one
    wrote their own script, each re-deriving fonts, placement and the
    canonical-layer rewrite by hand."""

    def _build(self, tmp, notices, targets=None):
        font = find_test_font()
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_titled_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        segs = os.path.join(tmp, 'segments.json')
        strip_text.strip_text(src, stripped)
        conf = {
            'fonts': {'regular': str(font), 'bold': str(font)},
            'translations': targets or dict(NOTICE_TARGETS),
            'merges': [], 'overrides': [], 'center': [], 'skip': [],
            'notices': notices,
        }
        Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                            encoding='utf-8')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(stripped, segs, tr, out)
        return rc, src, out, tr, segs, buf.getvalue()

    def _notice(self, **kw):
        n = {'page': 0, 'text': NOTICE_LEAD + '‖' + NOTICE_BODY,
             'box': list(NOTICE_BOX), 'size': 7, 'bold_lead': True}
        n.update(kw)
        return n

    def test_the_notice_lands_and_passes_every_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, src, out, tr, segs, log = self._build(tmp, [self._notice()])
            self.assertEqual(rc, 0, msg=log)
            self.assertIn('notices: placed 1', log)

            doc = pymupdf.open(out)
            try:
                self.assertEqual(doc.page_count, 1, msg='no page was added')
                layer = doc[0].get_text()
                sizes = {round(sp['size'], 1)
                         for b in doc[0].get_text('dict')['blocks']
                         for line in b.get('lines', []) for sp in line['spans']}
            finally:
                doc.close()
            # Verbatim, with the gate's own whitespace rule: the notice
            # wraps inside its box exactly as a merged paragraph does.
            self.assertIn(verify.normalize_ws(NOTICE_LEAD),
                          verify.normalize_ws(layer))
            self.assertIn(verify.normalize_ws(NOTICE_BODY),
                          verify.normalize_ws(layer))
            self.assertIn(7.0, sizes, msg=f'notice size not placed: {sizes}')

            buf = io.StringIO()
            with redirect_stdout(buf):
                vrc = verify.verify(src, out, translations=tr,
                                    source_words_from=segs,
                                    allow=[NOTICE_ISSUER])
            vlog = buf.getvalue()
            self.assertEqual(vrc, 0, msg=vlog)
            self.assertIn('PASS authored translations present', vlog)
            self.assertIn('PASS canonical text layer', vlog)
            # Row 20's keep, unchanged: the quoted title is a note.
            note = [l for l in vlog.splitlines() if l.startswith('note:')]
            self.assertEqual(len(note), 1, msg=vlog)
            self.assertIn(NOTICE_TITLE, note[0])

    def test_the_gate_wants_the_notice_in_the_layer(self):
        conf = {'translations': {}, 'notices': [self._notice()]}
        targets = verify.collect_translation_targets(conf)
        self.assertIn(NOTICE_LEAD, targets)
        self.assertIn(NOTICE_BODY, targets)

    def test_a_source_language_sentence_beside_it_still_fails(self):
        """The notice is not an amnesty: a forgotten English sentence on the
        same page is running text exactly as before."""
        leaked = dict(NOTICE_TARGETS)
        leaked[NOTICE_SENTENCE] = NOTICE_SENTENCE
        with tempfile.TemporaryDirectory() as tmp:
            rc, src, out, tr, segs, log = self._build(
                tmp, [self._notice()], targets=leaked)
            self.assertEqual(rc, 0, msg=log)
            buf = io.StringIO()
            with redirect_stdout(buf):
                vrc = verify.verify(src, out, translations=tr,
                                    source_words_from=segs,
                                    allow=[NOTICE_ISSUER])
            vlog = buf.getvalue()
            self.assertEqual(vrc, 1, msg=vlog)
            self.assertIn('FAIL untranslated running text', vlog)
            block = vlog.split('FAIL untranslated running text')[1]
            self.assertIn('return this form', block)
            self.assertNotIn(NOTICE_TITLE, block.split('\n\n')[0])

    def test_a_glyph_the_font_cannot_draw_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, src, out, tr, segs, log = self._build(
                tmp, [self._notice(text='Traduccion \u4e0d\u516c\u5f0f.')])
            self.assertEqual(rc, 1, msg=log)
            self.assertIn('cannot draw', log)
            self.assertFalse(os.path.isfile(out))

    def test_the_bold_lead_really_goes_through_the_bold_role(self):
        """Only one Latin face ships with the tests, so the roles cannot be
        told apart by font name. They can be told apart by the glyph check:
        point `bold` at a face with no Latin and the lead fails on it —
        and the same job with bold_lead off builds, because then only the
        regular font is asked to draw anything."""
        reg = str(find_test_font())
        no_latin = str(Path(reg).parent / 'NotoSansDevanagari-Regular.ttf')
        if not os.path.isfile(no_latin):
            self.skipTest('fetch_test_fonts.py has not run')
        for bold_lead, want_rc in ((True, 1), (False, 0)):
            with tempfile.TemporaryDirectory() as tmp:
                src = os.path.join(tmp, 'orig.pdf')
                stripped = os.path.join(tmp, 'stripped.pdf')
                out = os.path.join(tmp, 'out.pdf')
                tr = os.path.join(tmp, 'translations.json')
                build_titled_pdf(src)
                extract_segments.extract_segments(src, outdir=tmp)
                strip_text.strip_text(src, stripped)
                Path(tr).write_text(json.dumps({
                    'fonts': {'regular': reg, 'bold': no_latin},
                    'translations': dict(NOTICE_TARGETS),
                    'merges': [], 'overrides': [], 'center': [], 'skip': [],
                    'notices': [self._notice(bold_lead=bold_lead)],
                }, ensure_ascii=False), encoding='utf-8')
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = retypeset.retypeset(
                        stripped, os.path.join(tmp, 'segments.json'), tr, out)
                log = buf.getvalue()
                self.assertEqual(rc, want_rc, msg=f'bold_lead={bold_lead}: {log}')
                if want_rc:
                    self.assertIn('cannot draw', log)

    def test_a_notice_this_file_cannot_place_is_refused(self):
        cases = [
            (self._notice(text=None), 'text is null'),
            (self._notice(text='   '), 'text is null'),
            (self._notice(page=4), 'not a page of this document'),
            (self._notice(box=[40, 240, 360]), 'not four numbers'),
            (self._notice(box=[360, 285, 40, 240]), 'empty or inverted'),
        ]
        for notice, expected in cases:
            with tempfile.TemporaryDirectory() as tmp:
                rc, src, out, tr, segs, log = self._build(tmp, [notice])
                self.assertEqual(rc, 1, msg=f'{notice}: {log}')
                self.assertIn('cannot place', log)
                self.assertIn(expected, log)
                self.assertFalse(os.path.isfile(out))

    def test_no_notices_key_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, src, out, tr, segs, log = self._build(tmp, [])
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('notices:', log)
            doc = pymupdf.open(out)
            try:
                self.assertEqual(doc.page_count, 1)
                self.assertNotIn(NOTICE_LEAD, doc[0].get_text())
            finally:
                doc.close()



def build_sibling_xobject_pdf(path):
    """One page, four Form XObject names, two of them the same object.

    /Xd is a second name for /Xa's object, so whichever the walk reaches
    first is the one the strip report names — the half that sorting the
    finished report would not fix.
    """
    pdf = pikepdf.new()
    font = pdf.make_indirect(pikepdf.Dictionary(
        Type=pikepdf.Name('/Font'), Subtype=pikepdf.Name('/Type1'),
        BaseFont=pikepdf.Name('/Helvetica')))

    def form(label, y):
        st = pdf.make_stream(
            f'BT /F1 12 Tf 10 {y} Td ({label}) Tj ET'.encode('ascii'))
        st.Type = pikepdf.Name('/XObject')
        st.Subtype = pikepdf.Name('/Form')
        st.BBox = pikepdf.Array([0, 0, 200, 100])
        st.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
        return st

    a, b, c = form('alpha', 10), form('bravo', 30), form('charlie', 50)
    page = pdf.add_blank_page(page_size=(300, 200))
    page.obj.Resources = pikepdf.Dictionary(
        XObject=pikepdf.Dictionary(Xa=a, Xb=b, Xc=c, Xd=a))
    page.obj.Contents = pdf.make_stream(
        b'q 1 0 0 1 20 20 cm /Xa Do Q\n'
        b'q 1 0 0 1 20 60 cm /Xb Do Q\n'
        b'q 1 0 0 1 20 100 cm /Xc Do Q\n'
        b'q 1 0 0 1 20 140 cm /Xd Do Q\n')
    pdf.save(path)
    pdf.close()


STRIP_REPORT_PROBE = """
import io, json, os, sys, tempfile
from contextlib import redirect_stdout
sys.path.insert(0, sys.argv[1])
import strip_text
with tempfile.TemporaryDirectory() as tmp:
    with redirect_stdout(io.StringIO()):
        rep = strip_text.strip_text(sys.argv[2], os.path.join(tmp, 'out.pdf'))
print(json.dumps([(e['page'], e['xobject'], e['blocks'], e['depth'])
                  for e in rep['form_xobjects_stripped']]))
"""


class StripReportOrderTests(unittest.TestCase):
    """strip walked a page's XObjects in pikepdf dictionary order, which runs
    through a hash-randomized structure: the same file reported its stripped
    Form XObjects in a different order in every process, and where two names
    pointed at one object, `seen` skipped whichever came second so the
    recorded NAME floated too. Nothing about what gets stripped depended on
    it — this is a diagnostic that could not be compared between runs, which
    is how it surfaced: a wild-corpus re-run showed two page-17 entries of
    the IRS 1040 instructions swapped with every count identical.

    Sorting the finished report would fix only the order, so the traversal
    is what is pinned.
    """

    SEEDS = ('0', '1', '7', '999')

    def _report_under(self, pdf_path, seed):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run(
            [sys.executable, '-c', STRIP_REPORT_PROBE, str(SCRIPTS), pdf_path],
            capture_output=True, text=True, env=env, check=True)
        return json.loads(out.stdout)

    def test_the_report_is_the_same_in_every_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'xobjects.pdf')
            build_sibling_xobject_pdf(src)
            reports = [self._report_under(src, s) for s in self.SEEDS]
            first = reports[0]
            for seed, got in zip(self.SEEDS, reports):
                self.assertEqual(
                    got, first,
                    msg=f'PYTHONHASHSEED={seed} reported a different walk')
            # Sorted by name, and the alias never wins: /Xd is /Xa's object
            # under a later name, so /Xa is always the one recorded.
            self.assertEqual([e[1] for e in first], ['/Xa', '/Xb', '/Xc'])
            self.assertEqual([e[2] for e in first], [1, 1, 1])
            self.assertEqual({e[3] for e in first}, {1})

    def test_the_fixture_really_has_an_aliased_object(self):
        """Otherwise the name half of this test proves nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'xobjects.pdf')
            build_sibling_xobject_pdf(src)
            pdf = pikepdf.open(src)
            try:
                xo = dict(pdf.pages[0].obj['/Resources']['/XObject'])
                self.assertEqual(len(xo), 4)
                self.assertEqual(xo['/Xa'].objgen, xo['/Xd'].objgen)
            finally:
                pdf.close()



NOTICE_ACCENTS = 'Traducci\u00f3n \u201cno oficial\u201d.'


class JobCharsetTests(unittest.TestCase):
    """Row 30: the subset is built from the mapping, and two blocks that
    shipped on 3 September were not in that walk. A `null` core — legal
    wherever an override covers every occurrence (row 29) — raised
    TypeError, and `notices` (P7) was never read, so a character used only
    in the notice was missing from the subset and retypeset's glyph check
    then FAILed a correct build. Opus 5 and Fable 5.1 hit them
    independently on canary run 3."""

    def test_a_null_core_is_skipped_not_iterated(self):
        conf = {'translations': {'Public aid': None, 'Other': 'Otra'},
                'overrides': [{'page': 0, 'contains': 'Public aid',
                               'parts': [{'text': 'Ayuda', 'x': 72.0}]}]}
        chars = prepare_font.job_charset(conf)
        self.assertLessEqual(set('Otra'), chars)
        self.assertLessEqual(set('Ayuda'), chars)

    def test_notice_text_is_harvested_and_the_split_is_not(self):
        conf = {'translations': {'Hi': 'Hola'},
                'notices': [{'page': 0, 'text': 'Lead\u2016' + NOTICE_ACCENTS,
                             'box': [40, 700, 560, 745]}]}
        chars = prepare_font.job_charset(conf)
        self.assertLessEqual(set(NOTICE_ACCENTS), chars)
        self.assertNotIn('\u2016', chars)

    def test_an_empty_mapping_still_gives_the_printable_floor(self):
        chars = prepare_font.job_charset({})
        self.assertLessEqual(set(string.printable) - {'\u2016'}, chars)

    def test_a_null_core_no_longer_crashes_prepare_font(self):
        with tempfile.TemporaryDirectory() as tmp:
            tr = os.path.join(tmp, 'translations.json')
            out = os.path.join(tmp, 'subset.ttf')
            Path(tr).write_text(json.dumps({
                'fonts': {}, 'translations': {'Public aid': None,
                                              'Other': 'Otra linea.'},
                'merges': [], 'center': [], 'skip': [],
                'overrides': [{'page': 0, 'contains': 'Public aid',
                               'parts': [{'text': 'Ayuda', 'x': 72.0}]}],
            }, ensure_ascii=False), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.main([str(find_test_font()), tr, out])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            font = pymupdf.Font(fontfile=out)
            for ch in 'AyudaOtralinea':
                self.assertTrue(font.has_glyph(ord(ch)), msg=ch)

    def test_a_notice_only_character_survives_into_a_build(self):
        """The end of the story: subset the font for a job whose accents and
        curly quotes appear ONLY in the notice, then build with it and let
        the glyph check have its say."""
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            tr = os.path.join(tmp, 'translations.json')
            subset = os.path.join(tmp, 'subset.ttf')
            build_titled_pdf(src)
            extract_segments.extract_segments(src, outdir=tmp)
            segs = os.path.join(tmp, 'segments.json')
            strip_text.strip_text(src, stripped)
            notice = {'page': 0, 'text': NOTICE_ACCENTS,
                      'box': list(NOTICE_BOX), 'size': 7}
            # Plain ASCII everywhere but the notice.
            targets = {NOTICE_TITLE: 'Permiso de excursion',
                       NOTICE_SENTENCE: 'Devuelva este formulario.',
                       NOTICE_ISSUER: NOTICE_ISSUER}
            conf = {'fonts': {}, 'translations': targets, 'merges': [],
                    'overrides': [], 'center': [], 'skip': [],
                    'notices': [notice]}
            Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                                encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare_font.main([str(find_test_font()), tr, subset])
            self.assertEqual(rc, 0, msg=buf.getvalue())
            font = pymupdf.Font(fontfile=subset)
            for ch in NOTICE_ACCENTS:
                self.assertTrue(font.has_glyph(ord(ch)),
                                msg=f'{ch!r} missing from the subset')

            conf['fonts'] = {'regular': subset, 'bold': subset}
            Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                                encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, segs, tr, out)
            log = buf.getvalue()
            self.assertEqual(rc, 0, msg=log)
            self.assertNotIn('cannot draw', log)
            doc = pymupdf.open(out)
            try:
                self.assertIn(NOTICE_ACCENTS,
                              verify.normalize_ws(doc[0].get_text()))
            finally:
                doc.close()



class FontRoleFallbackTests(unittest.TestCase):
    """Row 31: `fonts` falls back to the nearest role the mapping named,
    which is right and was silent. On canary run 3 Sonnet 5 set
    `bold_lead: true` with `fonts.bold` pointing at the same file as
    `fonts.regular`; the notice's lead drew regular, nothing said so, and
    the delivery called the page pixel-faithful. Fable 5.1 hit the same
    thing and caught it only by eye."""

    def _build(self, tmp, fonts, targets=None, notices=None):
        src = os.path.join(tmp, 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        out = os.path.join(tmp, 'out.pdf')
        tr = os.path.join(tmp, 'translations.json')
        build_titled_pdf(src)
        extract_segments.extract_segments(src, outdir=tmp)
        strip_text.strip_text(src, stripped)
        conf = {'fonts': fonts, 'translations': targets or dict(NOTICE_TARGETS),
                'merges': [], 'overrides': [], 'center': [], 'skip': []}
        if notices is not None:
            conf['notices'] = notices
        Path(tr).write_text(json.dumps(conf, ensure_ascii=False),
                            encoding='utf-8')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = retypeset.retypeset(
                stripped, os.path.join(tmp, 'segments.json'), tr, out)
        log = buf.getvalue()
        self.assertEqual(rc, 0, msg=log)
        return [l for l in log.splitlines() if l.startswith('font roles')]

    def _notice(self):
        return [{'page': 0, 'text': NOTICE_LEAD + '‖' + NOTICE_BODY,
                 'box': list(NOTICE_BOX), 'size': 7, 'bold_lead': True}]

    def test_a_bold_lead_on_the_regular_face_is_named(self):
        reg = str(find_test_font())
        with tempfile.TemporaryDirectory() as tmp:
            lines = self._build(tmp, {'regular': reg, 'bold': reg},
                                notices=self._notice())
            self.assertEqual(len(lines), 1, msg=lines)
            self.assertIn('"bold" resolved to the regular face', lines[0])
            self.assertIn('notices[0]', lines[0])

    def test_a_real_bold_face_says_nothing(self):
        reg = str(find_test_font())
        with tempfile.TemporaryDirectory() as tmp:
            bold = os.path.join(tmp, 'bold.ttf')
            shutil.copy(reg, bold)
            lines = self._build(tmp, {'regular': reg, 'bold': bold},
                                notices=self._notice())
            self.assertEqual(lines, [])

    def test_a_symlink_to_the_regular_face_is_still_the_regular_face(self):
        """Resolved paths, nothing cleverer — but resolved."""
        reg = str(find_test_font())
        with tempfile.TemporaryDirectory() as tmp:
            link = os.path.join(tmp, 'link.ttf')
            os.symlink(reg, link)
            lines = self._build(tmp, {'regular': reg, 'bold': link},
                                notices=self._notice())
            self.assertEqual(len(lines), 1, msg=lines)
            self.assertIn('"bold"', lines[0])

    def test_an_inline_bold_run_is_named_too(self):
        """The Story engine picks its face from <b>, not from role()."""
        reg = str(find_test_font())
        targets = dict(NOTICE_TARGETS)
        targets[NOTICE_SENTENCE] = 'Devuelva <b>este formulario</b> hoy.'
        with tempfile.TemporaryDirectory() as tmp:
            lines = self._build(tmp, {'regular': reg}, targets=targets)
            self.assertEqual(len(lines), 1, msg=lines)
            self.assertIn('"bold" resolved to the regular face', lines[0])
            self.assertIn('Please return this form', lines[0])

    def test_a_job_that_never_asks_for_bold_says_nothing(self):
        reg = str(find_test_font())
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._build(tmp, {'regular': reg}), [])

    def test_it_is_a_line_not_a_failure(self):
        """A one-face job is legitimate and must still build."""
        reg = str(find_test_font())
        with tempfile.TemporaryDirectory() as tmp:
            lines = self._build(tmp, {'regular': reg, 'bold': reg},
                                notices=self._notice())
            self.assertTrue(lines)
            self.assertNotIn('FAIL', lines[0])


if __name__ == '__main__':
    unittest.main()
