#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drive shipped extract/verify against every corpus PDF and its recorded verdict."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
CORPUS = Path(__file__).resolve().parents[1] / 'corpus'
import sys
sys.path.insert(0, str(SCRIPTS))

import extract_segments  # noqa: E402
import pipeline  # noqa: E402
import retypeset  # noqa: E402
import strip_text  # noqa: E402
import verify  # noqa: E402

import pymupdf  # noqa: E402

ALLOWED = {'translate', 'refuse+OCR', 'refuse+ocr-layer', 'skip-ink'}
FONTS = Path(__file__).resolve().parent / 'fonts'
# An identity mapping is untranslated by construction, so this is the one
# FAIL a faithful identity rebuild raises.
IDENTITY_FAIL = 'FAIL untranslated running text'
# How far a rebuilt run may start from the segment it replaces.
START_TOLERANCE = 1.5


def identity_font(cores, tmp):
    """A face that draws every core, for an identity mapping: Noto Sans,
    then Noto Naskh Arabic, then PyMuPDF's bundled CJK face."""
    need = {ord(ch) for text in cores for ch in text if not ch.isspace()}
    candidates = [str(FONTS / 'NotoSans-Regular.ttf'),
                  str(FONTS / 'NotoNaskhArabic-Regular.ttf')]
    cjk = os.path.join(tmp, 'cjk.ttf')
    with open(cjk, 'wb') as fh:
        fh.write(pymupdf.Font('cjk').buffer)
    candidates.append(cjk)
    for path in candidates:
        if os.path.isfile(path):
            face = pymupdf.Font(fontfile=path)
            if all(face.has_glyph(u) for u in need):
                return path
    return None


def span_origins(pdf_path):
    """{page: [(x, y), ...]} of every drawn text span, in get_text's
    unrotated page space."""
    doc = pymupdf.open(pdf_path)
    try:
        return {page.number: [tuple(sp['origin'])
                              for b in page.get_text('dict')['blocks']
                              for line in b.get('lines', [])
                              for sp in line['spans'] if sp['text'].strip()]
                for page in doc}
    finally:
        doc.close()


def load_verdicts():
    path = CORPUS / 'verdicts.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    return {k: v for k, v in data.items()}


class CorpusVerdictTests(unittest.TestCase):
    def test_every_corpus_pdf_has_a_legal_verdict(self):
        verdicts = load_verdicts()
        pdfs = sorted(p.name for p in CORPUS.glob('*.pdf'))
        self.assertTrue(pdfs, 'corpus has no PDFs')
        self.assertEqual(set(pdfs), set(verdicts),
                         msg='verdicts.json must list every corpus PDF and only those')
        for name, v in verdicts.items():
            self.assertIn(v, ALLOWED, msg=f'{name} verdict {v!r}')
        readme = (CORPUS / 'README.md').read_text(encoding='utf-8')
        for name, v in verdicts.items():
            self.assertIn(f'`{name}`', readme)
            self.assertIn(f'`{v}`', readme)

    def test_shipped_extract_verify_match_recorded_verdicts(self):
        verdicts = load_verdicts()
        for name, expected in sorted(verdicts.items()):
            pdf = CORPUS / name
            with self.subTest(name=name, verdict=expected):
                with tempfile.TemporaryDirectory() as tmp:
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        extract_rc = extract_segments.main([str(pdf), '--outdir', tmp])
                    extract_log = buf.getvalue()
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        verify_rc = verify.verify(str(pdf), str(pdf))
                    verify_log = buf.getvalue()

                    if expected == 'refuse+OCR':
                        self.assertNotEqual(extract_rc, 0, msg=extract_log)
                        self.assertIn('OCR', extract_log)
                        self.assertNotEqual(verify_rc, 0, msg=verify_log)
                        self.assertTrue(
                            'OCR' in verify_log or 'scanned' in verify_log.lower(),
                            msg=verify_log)
                    elif expected == 'refuse+ocr-layer':
                        self.assertNotEqual(extract_rc, 0, msg=extract_log)
                        self.assertIn('invisible', extract_log.lower())
                        self.assertNotEqual(verify_rc, 0, msg=verify_log)
                        self.assertIn('invisible', verify_log.lower())
                    elif expected == 'skip-ink':
                        self.assertNotIn('FAIL page 1 ink ratio', verify_log)
                        self.assertIn('SKIP page 1 ink ratio', verify_log)
                        self.assertEqual(verify_rc, 0, msg=verify_log)
                    elif expected == 'translate':
                        self.assertEqual(extract_rc, 0, msg=extract_log)
                        segs = json.loads(
                            Path(tmp, 'segments.json').read_text(encoding='utf-8'))
                        self.assertGreater(len(segs['segments']), 0, msg=name)
                        stripped = str(Path(tmp, 'stripped.pdf'))
                        buf = io.StringIO()
                        with redirect_stdout(buf):
                            report = strip_text.strip_text(str(pdf), stripped)
                        leftover = report.get('leftover_text')
                        self.assertIsNotNone(leftover, msg='strip has no completeness gate')
                        self.assertEqual(leftover, [], msg=f'{name}: {leftover}')
                        self.assertTrue(Path(stripped).is_file(), msg=name)

    def _identity_rebuild(self, name, tmp):
        """init, an identity mapping, rebuild: (rebuild log, output, segments)."""
        pdf = CORPUS / name
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = pipeline.main(['init', str(pdf), '--work', tmp])
        self.assertEqual(rc, 0, msg=buf.getvalue())
        cores = [c['text'] for c in json.loads(
            Path(tmp, 'to_translate.json').read_text(encoding='utf-8'))['cores']]
        font = identity_font(cores, tmp)
        self.assertIsNotNone(font, msg=f'{name}: no face draws it')
        mapping = {
            'fonts': {role: font for role in
                      ('regular', 'bold', 'italic', 'bold_italic')},
            'translations': {c: c for c in cores},
            'merges': [], 'overrides': [], 'center': [], 'skip': []}
        Path(tmp, 'translations.json').write_text(
            json.dumps(mapping, ensure_ascii=False), encoding='utf-8')
        out = Path(tmp, 'out.pdf')
        buf = io.StringIO()
        with redirect_stdout(buf):
            pipeline.main(['rebuild', '--work', tmp, str(pdf), str(out)])
        segments = json.loads(Path(tmp, 'segments.json').read_text(
            encoding='utf-8'))['segments']
        return buf.getvalue(), out, segments

    @staticmethod
    def _misplaced(out, segments):
        """Segments with no rebuilt span starting within tolerance of their
        origin: [(page, core, origin)]."""
        drawn = span_origins(out)
        return [(s['page'], s['core'], s['origin']) for s in segments
                if not s['passthrough'] and not any(
                    abs(x - s['origin'][0]) <= START_TOLERANCE
                    and abs(y - s['origin'][1]) <= START_TOLERANCE
                    for x, y in drawn.get(s['page'], []))]

    def test_every_translate_fixture_rebuilds_in_place(self):
        """R-64: every `translate` fixture is built end to end with an
        identity mapping. The only FAIL that mapping may raise is untranslated
        running text. Anything else -- a blank page, a missing target, a
        changed page -- is a defect the extract-only test above cannot see.
        Each rebuilt run must also start where its segment does, which is what
        catches a run drawn on the page but in the wrong place: no verify gate
        reads positions. Right-to-left source runs are left out of that one
        check; the test below pins why."""
        verdicts = load_verdicts()
        for name, expected in sorted(verdicts.items()):
            if expected != 'translate':
                continue
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp:
                    log, out, segments = self._identity_rebuild(name, tmp)
                    self.assertTrue(out.is_file(), msg=log)
                    fails = [line.strip() for line in log.splitlines()
                             if line.strip().startswith('FAIL')]
                    self.assertEqual(
                        [f for f in fails if not f.startswith(IDENTITY_FAIL)],
                        [], msg=log)
                    ltr = [s for s in segments
                           if not retypeset.is_rtl_text(s['core'])]
                    self.assertEqual(self._misplaced(out, ltr), [], msg=name)

    @unittest.expectedFailure
    def test_right_to_left_source_runs_start_where_the_source_did(self):
        """A known defect, found by R-64's position check and proposed to the
        product, not assigned (docs/REQUESTS-from-product.md, 2026-09-24).
        MuPDF reports a right-to-left run's origin at its right end, and
        retypeset draws every run rightward from its origin, so each of
        ar_source.pdf's runs lands one source width to the right. No verify
        gate reads positions, so nothing else fails. When this passes, remove
        the decorator and the right-to-left exclusion above."""
        with tempfile.TemporaryDirectory() as tmp:
            log, out, segments = self._identity_rebuild('ar_source.pdf', tmp)
            rtl = [s for s in segments if retypeset.is_rtl_text(s['core'])]
            self.assertTrue(rtl, msg='ar_source.pdf has no right-to-left run')
            self.assertEqual(self._misplaced(out, rtl), [])

if __name__ == '__main__':
    unittest.main()
