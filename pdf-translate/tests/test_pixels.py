#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R-48 and R-49: the pixel and character counts are exact replacements, the
dark-pixel loop lives in one place, and the invisible-text oracle judges only
the pages asked for.

The reference loops below are the shipped code these replaced, kept here as
the definition the replacements must equal.
"""
import ast
import importlib
import os
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pymupdf

from pdf_translate import _pixels
from tests.test_pipeline import build_ocr_layer_pdf, build_plain_pdf

strip_text = importlib.import_module('pdf_translate.strip_text')
extract_segments = importlib.import_module('pdf_translate.extract_segments')
shaping_probe = importlib.import_module('pdf_translate.shaping_probe')
PACKAGE = Path(__file__).resolve().parents[1] / 'pdf_translate'


def reference_dark(buf, n, below):
    return sum(1 for k in range(0, len(buf), n) if buf[k] < below)


def reference_changed(a, b, delta):
    return sum(1 for x, y in zip(a, b) if abs(x - y) > delta)


def reference_scripts(text):
    found = set()
    for ch in text or '':
        o = ord(ch)
        for name, ranges in shaping_probe.SCRIPT_RANGES.items():
            if any(a <= o <= b for a, b in ranges):
                found.add(name)
                break
    return found


class ExactCountTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(48)

    def test_dark_pixels_is_the_loop_it_replaced(self):
        for n in (1, 2, 3, 4):
            for below in (100, 128, 0, 1, 255, 256):
                for size in (0, 1, n - 1, n, 7 * n + 1, 5000):
                    buf = bytes(self.rng.choice((0, 99, 100, 101, 127, 128, 200, 255))
                                if self.rng.random() < 0.5 else self.rng.randrange(256)
                                for _ in range(max(size, 0)))
                    with self.subTest(n=n, below=below, size=size):
                        self.assertEqual(_pixels.dark_pixels(buf, n, below), reference_dark(buf, n, below))

    def test_dark_pixels_on_real_renders(self):
        page = pymupdf.open().new_page()
        page.insert_text((72, 100), 'Name of the applicant', fontsize=14)
        for colorspace, alpha in ((pymupdf.csRGB, False), (pymupdf.csGRAY, False), (pymupdf.csRGB, True)):
            pix = page.get_pixmap(dpi=72, colorspace=colorspace, alpha=alpha)
            with self.subTest(n=pix.n):
                self.assertEqual(_pixels.dark_pixels(pix.samples, pix.n),
                                 reference_dark(bytes(pix.samples), pix.n, 100))
                self.assertGreater(_pixels.dark_pixels(pix.samples, pix.n), 0)

    def test_changed_channels_is_the_loop_it_replaced(self):
        for size in (0, 1, 1023, 1024, 1025, 5000):
            for extra in (0, 3):
                a = bytes(self.rng.randrange(256) for _ in range(size + extra))
                b = bytearray(a[:size])
                for _ in range(size // 3):
                    k = self.rng.randrange(size)
                    b[k] = (b[k] + self.rng.choice((1, 15, 16, 17, 100, 240))) % 256
                for delta in (0, 15, 16, 17):
                    with self.subTest(size=size, extra=extra, delta=delta):
                        self.assertEqual(_pixels.changed_channels(a, bytes(b), delta),
                                         reference_changed(a, bytes(b), delta))

    def test_stopping_early_gives_the_same_decision(self):
        a = bytes(self.rng.randrange(256) for _ in range(20000))
        b = bytearray(a)
        for k in range(0, 20000, 7):
            b[k] ^= 0xFF
        full = reference_changed(a, bytes(b), 16)
        for threshold in (1, 50, full - 1, full, full + 1):
            with self.subTest(threshold=threshold):
                partial = _pixels.changed_channels(a, bytes(b), 16, stop=lambda c: c >= threshold)
                self.assertEqual(partial >= threshold, full >= threshold)
                self.assertLessEqual(partial, full)

    def test_scripts_in_is_the_loop_it_replaced(self):
        edges = [chr(c) for ranges in shaping_probe.SCRIPT_RANGES.values()
                 for a, b in ranges for c in (a - 1, a, b, b + 1)]
        pool = edges + list('Hello 123 שלום مكتبة 日本語 ')
        for _ in range(300):
            text = ''.join(self.rng.choice(pool) for _ in range(self.rng.randrange(0, 40)))
            self.assertEqual(shaping_probe.scripts_in(text), reference_scripts(text), text)
        self.assertEqual(shaping_probe.scripts_in(None), set())


class OneCopyTests(unittest.TestCase):
    """The dark-pixel loop and its thresholds were copied into four places."""

    def test_the_dark_pixel_loop_and_its_floors_live_in_one_module(self):
        loops, floors = [], []
        for path in sorted(PACKAGE.glob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                # sum(1 for k in range(0, len(buf), n) if buf[k] < ...)
                if (isinstance(node, ast.GeneratorExp) and isinstance(node.elt, ast.Constant)
                        and node.elt.value == 1 and any(
                            isinstance(g.iter, ast.Call) and getattr(g.iter.func, 'id', '') == 'range'
                            and len(g.iter.args) == 3 for g in node.generators)):
                    loops.append(f'{path.name}:{node.lineno}')
                if isinstance(node, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id in ('VISIBLE_INK', 'INK_SKIP') for t in node.targets):
                    floors.append(path.name)
        self.assertEqual(loops, [])
        self.assertEqual(sorted(floors), ['_pixels.py', '_pixels.py'])


class OracleScopeTests(unittest.TestCase):
    """R-49: the oracle judges the pages it is asked about, and gives each
    the verdict it gets when the whole document is judged."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        ocr, plain = os.path.join(tmp.name, 'ocr.pdf'), os.path.join(tmp.name, 'plain.pdf')
        build_ocr_layer_pdf(ocr)
        build_plain_pdf(plain)
        self.src = os.path.join(tmp.name, 'mixed.pdf')
        with pymupdf.open() as doc, pymupdf.open(ocr) as a, pymupdf.open(plain) as b:
            doc.insert_pdf(a)      # page 1: an OCR layer
            doc.insert_pdf(b)      # pages 2 and 3: real text
            doc.insert_pdf(b)
            doc.save(self.src)

    def judged(self, call):
        with mock.patch.object(strip_text, 'text_span_area', wraps=strip_text.text_span_area) as area:
            result = call()
        return result, area.call_count

    def test_only_the_pages_asked_about_are_judged(self):
        everything, judged = self.judged(lambda: strip_text.invisible_text_pages(self.src))
        self.assertEqual([p for p, _ in everything], [0])
        self.assertEqual(judged, 3)
        for pages in ({0}, {1, 2}, {0, 2}, set()):
            with self.subTest(pages=pages):
                some, judged = self.judged(lambda: strip_text.invisible_text_pages(self.src, pages=pages))
                self.assertEqual(some, [(p, f) for p, f in everything if p in pages])
                self.assertEqual(judged, len(pages))

    def test_extract_judges_only_its_pages(self):
        _, judged = self.judged(lambda: extract_segments.run_extract(
            self.src, os.path.join(self.tmp, 'out'), pages='2-3'))
        self.assertEqual(judged, 2)


if __name__ == '__main__':
    unittest.main()
