"""A below-floor scale refusal can keep itself: pdf_translate.capture.

B1 (wrapping a translation onto a second line) is blocked because nobody has
a real failed job to measure recovery against
(docs/reviews/2026-09-19-b1-recovery-probe.md): a refusal prints a message
and exits, and nothing writes its inputs anywhere. These tests cover the
fix from both retypeset paths (typography-1 and legacy), and the four
things the task asked for at minimum: capture on writes a complete
replayable bundle; capture off writes nothing; a capture that cannot be
written still surfaces the original refusal unchanged; and an occurrence's
unknown box permission is recorded as unknown rather than guessed.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import pymupdf

from pdf_translate import run_extract, run_retypeset, run_strip
from pdf_translate import capture
from pdf_translate.results import PlacementError
from tests.typography_fixtures import latin_font_sets, make_job

LONG_TARGET = 'An extremely long translated sentence that will never fit in the original space. ' * 3


def make_legacy_job(work, font, source_text='The applicant must file this form today.'):
    """A one-segment legacy job whose translation overflows the 0.7x floor."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    src = work / 'orig.pdf'
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), source_text, fontsize=12)
    doc.save(src)
    doc.close()
    stripped = work / 'stripped.pdf'
    run_strip(str(src), str(stripped))
    run_extract(str(src), str(work))
    mapping = work / 'translations.json'
    mapping.write_text(json.dumps({
        'fonts': {'regular': font, 'bold': font, 'italic': font, 'bold_italic': font},
        'translations': {source_text: LONG_TARGET},
        'merges': [], 'overrides': [], 'center': [], 'skip': [],
    }, ensure_ascii=False), encoding='utf-8')
    return {'original': src, 'stripped': stripped, 'segments': work / 'segments.json',
            'mapping': mapping, 'output': work / 'out.pdf'}, source_text


def make_legacy_merge_job(work, font, box=None):
    """A two-line legacy merge whose paragraph overflows; optionally with an authored box."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    line1 = 'Line one of a paragraph that wraps here'
    line2 = 'and continues on the next line today.'
    src = work / 'orig.pdf'
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 80), line1, fontsize=12)
    page.insert_text((72, 96), line2, fontsize=12)
    doc.save(src)
    doc.close()
    stripped = work / 'stripped.pdf'
    run_strip(str(src), str(stripped))
    run_extract(str(src), str(work))
    mapping = work / 'translations.json'
    merge = {'page': 0, 'lines': [line1, line2], 'html': ('Wort ' * 80).strip(), 'align': 'left'}
    if box is not None:
        merge['box'] = box
    mapping.write_text(json.dumps({
        'fonts': {'regular': font, 'bold': font, 'italic': font, 'bold_italic': font},
        'translations': {line1: 'A', line2: 'B'},
        'merges': [merge], 'overrides': [], 'center': [], 'skip': [],
    }, ensure_ascii=False), encoding='utf-8')
    return {'original': src, 'stripped': stripped, 'segments': work / 'segments.json',
            'mapping': mapping, 'output': work / 'out.pdf'}, line1


class CaptureHelperTests(unittest.TestCase):
    """Direct unit coverage for the small, easy-to-get-wrong helpers."""

    def test_resolve_capture_dir_argument_wins_over_environment(self):
        old = os.environ.get(capture.ENV_VAR)
        os.environ[capture.ENV_VAR] = '/from/env'
        try:
            self.assertEqual(capture.resolve_capture_dir('/from/arg'), '/from/arg')
            self.assertEqual(capture.resolve_capture_dir(None), '/from/env')
        finally:
            if old is None:
                os.environ.pop(capture.ENV_VAR, None)
            else:
                os.environ[capture.ENV_VAR] = old

    def test_resolve_capture_dir_off_by_default(self):
        old = os.environ.pop(capture.ENV_VAR, None)
        try:
            self.assertIsNone(capture.resolve_capture_dir(None))
        finally:
            if old is not None:
                os.environ[capture.ENV_VAR] = old

    def test_is_below_floor(self):
        placement_overflow = PlacementError('x', refusals={'overflow': [{'page': 0}]})
        placement_other = PlacementError('x', refusals={'typography': [{'reason': 'unsafe-typography-geometry'}]})
        placement_floor = PlacementError('x', refusals={'typography': [{'reason': 'below-scale-floor'}]})
        self.assertTrue(capture.is_below_floor(placement_overflow))
        self.assertTrue(capture.is_below_floor(placement_floor))
        self.assertFalse(capture.is_below_floor(placement_other))


class TypographyCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / 'job'
        self.job = make_job(self.work)
        self.captures = Path(self.tmp.name) / 'captures'
        self._force_below_floor()

    def _force_below_floor(self):
        path = self.job['mapping']
        conf = json.loads(path.read_text(encoding='utf-8'))
        for target in conf['targets']:
            target['runs'][0]['text'] = 'Extremely long translated wording ' * 10
        path.write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')

    def build(self, **kwargs):
        kwargs.setdefault('original', str(self.job['original']))
        return run_retypeset(*(str(self.job[k]) for k in ('stripped', 'segments', 'mapping', 'output')),
                             **kwargs)

    def test_capture_on_writes_a_complete_replayable_bundle(self):
        with self.assertRaises(PlacementError) as caught:
            self.build(capture_dir=str(self.captures))
        exc = caught.exception
        self.assertEqual(exc.refusals['typography'][0]['reason'], 'below-scale-floor')

        cases = list(self.captures.iterdir())
        self.assertEqual(len(cases), 1, cases)
        case_dir = cases[0]
        manifest = json.loads((case_dir / 'manifest.json').read_text(encoding='utf-8'))

        self.assertEqual(manifest['mapping_format'], 'typography-1')
        self.assertEqual(manifest['refusal']['error'], 'PlacementError')
        self.assertEqual(manifest['refusal']['exit_code'], exc.exit_code)
        self.assertEqual(manifest['refusal']['refusals']['typography'][0]['reason'], 'below-scale-floor')
        self.assertEqual(manifest['occurrence']['page'], exc.page)
        self.assertEqual(manifest['occurrence']['key'], exc.key)
        self.assertEqual(manifest['occurrence']['scale'], exc.scale)
        self.assertIsNotNone(manifest['occurrence']['position'])
        self.assertIn('bbox', manifest['occurrence']['position'])

        # Box permission is recorded as unknown, not inferred: the
        # typography-1 mapping format has no per-occurrence box field.
        self.assertIsNone(manifest['occurrence']['box_permitted'])
        self.assertIn('no per-occurrence box-permission field',
                      manifest['occurrence']['box_permitted_note'])

        # Every promised file exists and is a byte-identical copy.
        self.assertEqual((case_dir / 'source.pdf').read_bytes(), self.job['original'].read_bytes())
        self.assertEqual((case_dir / 'stripped.pdf').read_bytes(), self.job['stripped'].read_bytes())
        self.assertTrue((case_dir / 'segments.json').is_file())
        self.assertTrue((case_dir / 'translations.json').is_file())
        self.assertTrue(manifest['files']['fonts'], 'no font files were recorded')
        for rel in manifest['files']['fonts'].values():
            self.assertTrue((case_dir / rel).is_file(), rel)

        # Replayable: rebuilding from the bundle ALONE reproduces the same refusal.
        replay_out = case_dir / 'replayed_out.pdf'
        with self.assertRaises(PlacementError) as replayed:
            run_retypeset(str(case_dir / 'stripped.pdf'), str(case_dir / 'segments.json'),
                          str(case_dir / 'translations.json'), str(replay_out),
                          original=str(case_dir / 'source.pdf'))
        self.assertEqual(replayed.exception.refusals['typography'][0]['reason'], 'below-scale-floor')
        self.assertEqual(replayed.exception.page, exc.page)
        self.assertEqual(replayed.exception.key, exc.key)
        self.assertFalse(replay_out.exists())

    def test_capture_off_by_default_writes_nothing(self):
        with self.assertRaises(PlacementError):
            self.build()
        self.assertFalse(self.captures.exists())

    def test_capture_failure_does_not_change_exit_or_output(self):
        self.job['output'].write_bytes(b'prior successful output')
        blocked = self.captures
        blocked.parent.mkdir(parents=True, exist_ok=True)
        blocked.write_bytes(b'not a directory')

        with self.assertRaises(PlacementError) as caught:
            self.build(capture_dir=str(blocked))
        exc = caught.exception
        self.assertEqual(exc.refusals['typography'][0]['reason'], 'below-scale-floor')
        self.assertEqual(exc.exit_code, 1)
        # The refusal is unchanged: same output preserved as a plain refusal
        # with no capture at all.
        self.assertEqual(self.job['output'].read_bytes(), b'prior successful output')
        with self.assertRaises(PlacementError) as without_capture:
            self.build()
        self.assertEqual(without_capture.exception.refusals, exc.refusals)
        self.assertEqual(without_capture.exception.console_line, exc.console_line)
        self.assertEqual(without_capture.exception.exit_code, exc.exit_code)
        # capture.py never created anything past the blocking file itself.
        self.assertEqual(blocked.read_bytes(), b'not a directory')


class LegacyCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.font = latin_font_sets()['sans']['regular']
        self.captures = Path(self.tmp.name) / 'captures'

    def test_capture_on_writes_a_replayable_bundle_with_no_source_pdf_recorded(self):
        job, source_text = make_legacy_job(Path(self.tmp.name) / 'job', self.font)
        with self.assertRaises(PlacementError) as caught:
            run_retypeset(str(job['stripped']), str(job['segments']), str(job['mapping']),
                          str(job['output']), capture_dir=str(self.captures))
        exc = caught.exception
        self.assertTrue(exc.refusals['overflow'])

        cases = list(self.captures.iterdir())
        self.assertEqual(len(cases), 1, cases)
        case_dir = cases[0]
        manifest = json.loads((case_dir / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['mapping_format'], 'legacy')
        self.assertEqual(manifest['occurrence']['key'], source_text)
        self.assertIsNotNone(manifest['occurrence']['position'])

        # `original` was never passed to run_retypeset here (legacy does not
        # require it): the bundle says so honestly instead of leaving a file
        # it cannot claim came from the job.
        self.assertIsNone(manifest['files']['source_pdf'])
        self.assertFalse((case_dir / 'source.pdf').exists())

        # No caller-authored merge or box exists for a plain segment.
        self.assertIsNone(manifest['occurrence']['box_permitted'])
        self.assertIn('no caller-authored merge or box',
                      manifest['occurrence']['box_permitted_note'])

        # Replayable without `original` at all.
        replay_out = case_dir / 'replayed_out.pdf'
        with self.assertRaises(PlacementError) as replayed:
            run_retypeset(str(case_dir / 'stripped.pdf'), str(case_dir / 'segments.json'),
                          str(case_dir / 'translations.json'), str(replay_out))
        self.assertTrue(replayed.exception.refusals['overflow'])
        self.assertEqual(replayed.exception.refusals['overflow'][0]['core'], source_text)
        self.assertFalse(replay_out.exists())

    def test_capture_off_by_default_writes_nothing(self):
        job, _ = make_legacy_job(Path(self.tmp.name) / 'job', self.font)
        with self.assertRaises(PlacementError):
            run_retypeset(str(job['stripped']), str(job['segments']), str(job['mapping']), str(job['output']))
        self.assertFalse(self.captures.exists())

    def test_authored_merge_box_is_recorded_when_it_exists(self):
        box = [72, 60, 220, 110]
        job, line1 = make_legacy_merge_job(Path(self.tmp.name) / 'job', self.font, box=box)
        with self.assertRaises(PlacementError) as caught:
            run_retypeset(str(job['stripped']), str(job['segments']), str(job['mapping']),
                          str(job['output']), capture_dir=str(self.captures))
        self.assertTrue(caught.exception.refusals['overflow'])

        case_dir = next(iter(self.captures.iterdir()))
        manifest = json.loads((case_dir / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['occurrence']['key'], line1)
        self.assertEqual(manifest['occurrence']['box_permitted'], box)
        self.assertIn('caller-authored box', manifest['occurrence']['box_permitted_note'])

    def test_env_var_is_the_opt_in_switch_when_no_argument_is_given(self):
        job, _ = make_legacy_job(Path(self.tmp.name) / 'job', self.font)
        old = os.environ.get(capture.ENV_VAR)
        os.environ[capture.ENV_VAR] = str(self.captures)
        try:
            with self.assertRaises(PlacementError):
                run_retypeset(str(job['stripped']), str(job['segments']), str(job['mapping']), str(job['output']))
        finally:
            if old is None:
                os.environ.pop(capture.ENV_VAR, None)
            else:
                os.environ[capture.ENV_VAR] = old
        self.assertEqual(len(list(self.captures.iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
