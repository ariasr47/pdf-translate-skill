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
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
CORPUS = Path(__file__).resolve().parents[1] / 'corpus'
CHOICE_SENTENCE = 'Choose fruit from the list and a color below.'
CHOICE_TARGET = 'Elija fruta de la lista y un color abajo.'
sys.path.insert(0, str(SCRIPTS))

import compare  # noqa: E402
import extract_segments  # noqa: E402
import pipeline  # noqa: E402
import render_pages  # noqa: E402
import field_fonts  # noqa: E402
import prepare_font  # noqa: E402
import retypeset  # noqa: E402
import strip_text  # noqa: E402
import verify  # noqa: E402

SOURCE_SENTENCE = 'The applicant must file this form today.'
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


def find_rtl_font():
    font = find_test_font()
    f = pymupdf.Font(fontfile=str(font))
    if f.has_glyph(ord(AR_TARGET[0])) and f.has_glyph(ord(HE_TARGET[0])):
        return font
    arial = Path(r'C:\Windows\Fonts\arial.ttf')
    if arial.is_file():
        f = pymupdf.Font(fontfile=str(arial))
        if f.has_glyph(ord(AR_TARGET[0])) and f.has_glyph(ord(HE_TARGET[0])):
            return arial
    raise unittest.SkipTest('no TTF with Arabic and Hebrew glyphs')


def find_test_font():
    candidates = [
        Path(__file__).resolve().parents[2] / 'work' / 'NotoSansJP-Regular-full.ttf',
        Path(r'C:\Windows\Fonts\arial.ttf'),
        Path(r'C:\Windows\Fonts\Arial.ttf'),
        Path(r'C:\Windows\Fonts\calibri.ttf'),
        Path(r'C:\Windows\Fonts\segoeui.ttf'),
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise unittest.SkipTest('no glyf TTF available for tests')


def write_mapping(path, translations, font, skip=None, allow_scale=None,
                  mirror=False, allow_translate=None):
    data = {
        'fonts': {'regular': str(font), 'bold': str(font)},
        'translations': translations,
        'merges': [],
        'overrides': [],
        'center': [],
        # Widget chrome ("Print") is drawn from /MK /CA, not page text.
        'skip': list(skip) if skip is not None else ['Print'],
    }
    if allow_scale is not None:
        data['allow_scale'] = list(allow_scale)
    if mirror:
        data['mirror'] = True
    if allow_translate is not None:
        data['allow_translate'] = list(allow_translate)
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


class HotLoopTests(unittest.TestCase):
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

    def test_nbsp_normalized_targets_length_gate(self):
        # Same glyphs, NBSP vs space, must count as present.
        page = 'Adjunte\xa0el recibo hoy.'
        self.assertEqual(
            verify.missing_translation_targets(
                page, ['Adjunte el recibo hoy.', 'x', '']),
            [])
        # Absent target of length ≥ 2 is reported; length-1 is not required.
        missing = verify.missing_translation_targets(
            'nope', ['Adjunte el recibo hoy.', 'Z'])
        self.assertEqual(missing, ['Adjunte el recibo hoy.'])
        self.assertNotIn('Z', missing)

    def test_hyphen_variants_match_authored_ascii_hyphen(self):
        authored = 'Vease Form W-2 y Schedule C.'
        self.assertIn('-', authored)
        # What the text layer actually contains after retypeset (NBSP + U+2011).
        landed = authored.replace(' ', '\xa0').replace('-', '\u2011')
        self.assertNotEqual(landed, authored)
        self.assertEqual(
            verify.missing_translation_targets(landed, [authored]), [])
        landed_2010 = authored.replace('-', '\u2010')
        self.assertEqual(
            verify.missing_translation_targets(landed_2010, [authored]), [])
        self.assertEqual(
            verify.missing_translation_targets('nope', [authored]),
            [authored])

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

    def test_fillable_hyphenated_target_passes_after_retypeset(self):
        """ASCII 'W-2' in the mapping must PASS even when get_text() emits U+2011.

        Do not swap this for a hyphen-free fixture: the authored target contains
        '-' and the placed layer must still satisfy --translations.
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
            # The layer is not a byte-identical copy of the authored ASCII string.
            self.assertNotIn(hyphen_tgt, layer)
            self.assertTrue(
                ('\u2011' in layer) or ('\u2010' in layer),
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
        font = find_rtl_font()
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


if __name__ == '__main__':
    unittest.main()
