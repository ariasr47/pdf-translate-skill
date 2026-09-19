#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The product's named acceptance for E3, reproduced literally.

From `docs/REQUESTS-from-product.md`, row E3: "one document through every
stage as function calls with stdout captured empty; two concurrent jobs; a
cancel between pages leaving no file; the eleven CLIs byte-identical (parity
runner)."

**sha256 determinism and the fixed-timestamp option are NOT here.** Ruling 3
of 2026-09-18 moved C7 to E8, because E8's acceptance already read "the C7
determinism test gates" and the size was unknown until a probe ran. The probe
has since run (`docs/BRIEF-determinism.md`): only `/ID`'s second element
varies, and only with the clock, so C7 is a `doc_id=` parameter and a test —
not an epic, and not this epic. Do not add them back here.

The eleven CLIs are covered by `dev/probes/cli_parity_runner.py`, which is run
between two checkouts rather than inside a unit test: byte-identity is a claim
about two versions, and one version cannot make it about itself.
"""
import concurrent.futures
import importlib
import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf

import pdf_translate
from pdf_translate import (
    ExtractResult, FieldFontsResult, FontResult, PdfTranslateError,
    RetypesetResult, StripResult,
)

SKILL = Path(__file__).resolve().parents[1]
FONT = SKILL / 'tests' / 'fonts' / 'NotoSans-Regular.ttf'

SOURCE_LINES = [
    'Income and Expense Declaration',
    'Employment status and monthly figures',
    'Attach copies of your pay stubs',
]
TARGETS = {
    'Income and Expense Declaration': 'Declaracion de ingresos y gastos',
    'Employment status and monthly figures': 'Situacion laboral y cifras',
    'Attach copies of your pay stubs': 'Adjunte copias de sus recibos',
}


def build_source(path, pages=1):
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page()
        for i, line in enumerate(SOURCE_LINES):
            page.insert_text((72, 72 + i * 24), line)
    doc.save(path)
    doc.close()
    return str(path)


def write_mapping(work, **extra):
    font = str(FONT)
    conf = {
        'fonts': {'regular': font, 'bold': font,
                  'italic': font, 'bold_italic': font},
        'lang': 'es',
        'translations': dict(TARGETS),
        'merges': [], 'overrides': [], 'center': [], 'skip': [],
    }
    conf.update(extra)
    path = os.path.join(work, 'translations.json')
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(conf, fh, ensure_ascii=False)
    return path


class OneDocumentThroughEveryStageTests(unittest.TestCase):
    """C1: every stage callable as a function, and stdout stays empty."""

    def test_a_document_goes_through_every_stage_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = build_source(Path(tmp) / 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            out = os.path.join(tmp, 'out.pdf')
            final = os.path.join(tmp, 'final.pdf')
            font_out = os.path.join(tmp, 'font-sub.ttf')

            buf = io.StringIO()
            with redirect_stdout(buf):
                strip = pdf_translate.run_strip(src, stripped)
                extract = pdf_translate.run_extract(src, outdir=tmp)
                trf = write_mapping(tmp)
                font = pdf_translate.run_prepare_font(str(FONT), trf, font_out)
                built = pdf_translate.run_retypeset(
                    stripped, extract.segments_path, trf, out)
                verdict = pdf_translate.run_verify(src, out, min_ink=0.0)
                fields = pdf_translate.run_field_fonts(out, str(FONT), final)

            # THE assertion of this epic.
            self.assertEqual(buf.getvalue(), '',
                             'a stage printed to the caller\'s stdout')

            for result, cls in ((strip, StripResult), (extract, ExtractResult),
                                (font, FontResult), (built, RetypesetResult),
                                (fields, FieldFontsResult)):
                self.assertIsInstance(result, cls)
                got = result.to_dict()
                self.assertIn('schema', got)
                self.assertIn('version', got)
                json.dumps(got, ensure_ascii=False)

            self.assertTrue(strip.ok)
            self.assertEqual(len(extract.cores), len(SOURCE_LINES))
            self.assertEqual(built.output, out)
            self.assertFalse(built.cancelled)
            self.assertTrue(os.path.isfile(out))
            self.assertTrue(os.path.isfile(final))
            self.assertEqual(verdict.exit_code, 0,
                             [g.name for g in verdict.gates
                              if g.status == 'FAIL'])

    def test_a_refusal_is_raised_as_typed_data_not_printed(self):
        # C3 and the product's B3: a printed format is an undeclared API. A
        # consumer branches on the exception and reads the refused cores in
        # full — not by parsing the console, and not truncated.
        with tempfile.TemporaryDirectory() as tmp:
            src = build_source(Path(tmp) / 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            pdf_translate.run_strip(src, stripped)
            extract = pdf_translate.run_extract(src, outdir=tmp)
            long_core = SOURCE_LINES[1]
            trf = write_mapping(tmp, translations={
                **TARGETS, long_core: None})

            buf = io.StringIO()
            with redirect_stdout(buf):
                with self.assertRaises(PdfTranslateError) as raised:
                    pdf_translate.run_retypeset(
                        stripped, extract.segments_path, trf,
                        os.path.join(tmp, 'out.pdf'))
            self.assertEqual(buf.getvalue(), '')

            exc = raised.exception
            self.assertTrue(exc.console_line)
            self.assertEqual(exc.exit_code, 1)
            cores = [item['core']
                     for item in exc.refusals.get('untranslated', ())]
            self.assertIn(long_core, cores)
            # In FULL. The console abbreviates; the data does not.
            for core in cores:
                self.assertFalse(core.endswith('…'))
            json.dumps(exc.to_dict(), ensure_ascii=False)

    def test_the_loud_twin_still_prints_and_returns_the_same_code(self):
        retypeset = importlib.import_module('pdf_translate.retypeset')
        with tempfile.TemporaryDirectory() as tmp:
            src = build_source(Path(tmp) / 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            pdf_translate.run_strip(src, stripped)
            extract = pdf_translate.run_extract(src, outdir=tmp)
            trf = write_mapping(tmp, translations={
                **TARGETS, SOURCE_LINES[1]: None})
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = retypeset.retypeset(stripped, extract.segments_path, trf,
                                         os.path.join(tmp, 'out.pdf'))
        self.assertEqual(rc, 1)
        self.assertIn('FAIL:', buf.getvalue())
        self.assertIn('untranslated segments', buf.getvalue())


class ProgressAndCancellationTests(unittest.TestCase):
    """C4."""

    def _job(self, tmp, pages=2, merges=None):
        src = build_source(Path(tmp) / 'orig.pdf', pages=pages)
        stripped = os.path.join(tmp, 'stripped.pdf')
        pdf_translate.run_strip(src, stripped)
        extract = pdf_translate.run_extract(src, outdir=tmp)
        trf = write_mapping(tmp, merges=merges or [])
        return stripped, extract.segments_path, trf

    def test_progress_total_is_pages_plus_merges(self):
        # retypeset runs TWO loops: a per-page pass, then a per-merge-job
        # pass. A counter of pages alone reaches 100% and keeps working.
        with tempfile.TemporaryDirectory() as tmp:
            stripped, segf, trf = self._job(tmp, pages=3)
            seen = []
            pdf_translate.run_retypeset(
                stripped, segf, trf, os.path.join(tmp, 'out.pdf'),
                progress=lambda done, total: seen.append((done, total)))
        self.assertTrue(seen)
        totals = {total for _, total in seen}
        self.assertEqual(len(totals), 1, f'total moved: {totals}')
        self.assertEqual(totals.pop(), 3)

    def test_progress_done_is_monotonic_and_never_exceeds_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            stripped, segf, trf = self._job(tmp, pages=3)
            seen = []
            pdf_translate.run_retypeset(
                stripped, segf, trf, os.path.join(tmp, 'out.pdf'),
                progress=lambda done, total: seen.append((done, total)))
        dones = [d for d, _ in seen]
        self.assertEqual(dones, sorted(dones), f'progress went backwards: {dones}')
        for done, total in seen:
            self.assertLessEqual(done, total)
        self.assertEqual(dones[-1], seen[-1][1])

    def test_a_cancel_between_units_writes_no_file_at_the_output_path(self):
        # The product's exact acceptance.
        with tempfile.TemporaryDirectory() as tmp:
            stripped, segf, trf = self._job(tmp, pages=3)
            out = os.path.join(tmp, 'out.pdf')
            calls = []

            def cancel():
                calls.append(1)
                return len(calls) > 1

            result = pdf_translate.run_retypeset(
                stripped, segf, trf, out, cancel=cancel)
        self.assertTrue(result.cancelled)
        self.assertIsNone(result.output)
        self.assertFalse(os.path.exists(out), 'a cancelled run left a file')

    def test_a_cancel_before_the_first_unit_also_leaves_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            stripped, segf, trf = self._job(tmp, pages=2)
            out = os.path.join(tmp, 'out.pdf')
            result = pdf_translate.run_retypeset(
                stripped, segf, trf, out, cancel=lambda: True)
        self.assertTrue(result.cancelled)
        self.assertFalse(os.path.exists(out))

    def test_a_cancel_that_never_fires_builds_normally(self):
        with tempfile.TemporaryDirectory() as tmp:
            stripped, segf, trf = self._job(tmp, pages=2)
            out = os.path.join(tmp, 'out.pdf')
            result = pdf_translate.run_retypeset(
                stripped, segf, trf, out, cancel=lambda: False)
        self.assertFalse(result.cancelled)
        self.assertEqual(result.output, out)


class ConcurrencyTests(unittest.TestCase):
    """C5: two jobs at once, neither treading on the other."""

    def _job(self, tmp):
        src = build_source(Path(tmp) / 'orig.pdf')
        stripped = os.path.join(tmp, 'stripped.pdf')
        pdf_translate.run_strip(src, stripped)
        extract = pdf_translate.run_extract(src, outdir=tmp)
        trf = write_mapping(tmp)
        return src, stripped, extract.segments_path, trf

    def test_two_concurrent_jobs_both_verify_pass(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            jobs = [self._job(a), self._job(b)]

            def run(job):
                src, stripped, segf, trf = job
                out = os.path.join(os.path.dirname(stripped), 'out.pdf')
                pdf_translate.run_retypeset(stripped, segf, trf, out)
                return pdf_translate.run_verify(src, out, min_ink=0.0)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                verdicts = list(pool.map(run, jobs))
        for verdict in verdicts:
            self.assertEqual(verdict.exit_code, 0,
                             [g.name for g in verdict.gates
                              if g.status == 'FAIL'])

    def test_two_concurrent_jobs_do_not_share_a_scale_report(self):
        # Red before Task 4: the report path was a fixed name beside `out`,
        # so two jobs writing to one directory raced for one file.
        with tempfile.TemporaryDirectory() as tmp:
            src = build_source(Path(tmp) / 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            pdf_translate.run_strip(src, stripped)
            extract = pdf_translate.run_extract(src, outdir=tmp)
            trf = write_mapping(tmp)
            reports = [os.path.join(tmp, 'a.json'), os.path.join(tmp, 'b.json')]

            def run(i):
                return pdf_translate.run_retypeset(
                    stripped, extract.segments_path, trf,
                    os.path.join(tmp, f'out{i}.pdf'),
                    scale_report=reports[i])

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(run, (0, 1)))
            for result, path in zip(results, reports):
                self.assertEqual(result.scale_report_path, path)
                self.assertTrue(os.path.isfile(path))

    def test_scale_report_none_writes_nothing_and_still_returns_the_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = build_source(Path(tmp) / 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            pdf_translate.run_strip(src, stripped)
            extract = pdf_translate.run_extract(src, outdir=tmp)
            trf = write_mapping(tmp)
            out = os.path.join(tmp, 'out.pdf')
            result = pdf_translate.run_retypeset(
                stripped, extract.segments_path, trf, out, scale_report=None)
            self.assertEqual(result.scale_report_path, '')
            self.assertFalse(os.path.exists(os.path.join(tmp, 'scale_report.json')))
            self.assertIsInstance(result.scaled, tuple)


class WorkingDirectoryTests(unittest.TestCase):
    """C1's last clause: no dependence on the process's working directory."""

    def test_authored_html_resources_resolve_against_the_mapping_not_the_cwd(self):
        # Red before Task 4: pymupdf.Archive('.') resolved a merge's CSS font
        # URLs against whatever directory the PROCESS happened to be in, so a
        # service that chdir'd, or simply ran from elsewhere, silently got a
        # substituted face.
        with tempfile.TemporaryDirectory() as tmp:
            src = build_source(Path(tmp) / 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            pdf_translate.run_strip(src, stripped)
            extract = pdf_translate.run_extract(src, outdir=tmp)
            merges = [{'page': 0, 'lines': SOURCE_LINES[:2],
                       'html': 'Declaracion y situacion laboral',
                       'align': 'left', 'box': None}]
            trf = write_mapping(tmp, merges=merges)
            out = os.path.join(tmp, 'out.pdf')

            here = os.getcwd()
            with tempfile.TemporaryDirectory() as other:
                try:
                    os.chdir(other)
                    result = pdf_translate.run_retypeset(
                        stripped, extract.segments_path, trf, out)
                finally:
                    os.chdir(here)
            # Inside the temp directory's lifetime: asserting on a file after
            # its directory has been cleaned up tests nothing.
            self.assertEqual(result.output, out)
            self.assertTrue(os.path.isfile(out))

    def test_resource_root_can_be_named_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = build_source(Path(tmp) / 'orig.pdf')
            stripped = os.path.join(tmp, 'stripped.pdf')
            pdf_translate.run_strip(src, stripped)
            extract = pdf_translate.run_extract(src, outdir=tmp)
            trf = write_mapping(tmp)
            out = os.path.join(tmp, 'out.pdf')
            result = pdf_translate.run_retypeset(
                stripped, extract.segments_path, trf, out,
                resource_root=tmp)
            self.assertEqual(result.output, out)
            self.assertTrue(os.path.isfile(out))


if __name__ == '__main__':
    unittest.main()
