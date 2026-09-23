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
import shutil
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


#: Long enough to shrink, short enough to clear our 0.7x floor. Measured at
#: 0.766x, so the build succeeds and only a caller holding a higher floor
#: cares - which is exactly the case this class exists for.
MODEST_TARGET = ('Pague ahora mismo sin falta y con toda urgencia posible hoy '
                 'Pague ahora mismo sin falta y con toda urgencia pos')


def make_modest_job(work, font, source_text='Please pay now.',
                    target=MODEST_TARGET):
    """A legacy job whose translation shrinks but stays above the 0.7x floor.

    This is the shape the hook was blind to: the build SUCCEEDS, so no
    refusal is ever raised, and a consumer holding a floor above ours
    reverts the core itself afterwards.
    """
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
        'translations': {source_text: target},
        'merges': [], 'overrides': [], 'center': [], 'skip': [],
    }, ensure_ascii=False), encoding='utf-8')
    return {'original': src, 'stripped': stripped, 'segments': work / 'segments.json',
            'mapping': mapping, 'output': work / 'out.pdf'}, source_text


class CaptureThresholdTests(unittest.TestCase):
    """A consumer whose floor sits above ours needs the band between them.

    Our floor is 0.7 and only a run under it refuses. A consumer applying
    0.75 app-side sees a build SUCCEED at 0.72 and reverts the core itself,
    so a hook keyed to our refusal never fires on the case that actually
    costs them. `capture_below` is that band.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.font = latin_font_sets()['sans']['regular']
        self.captures = Path(self.tmp.name) / 'captures'

    def build(self, **kwargs):
        job, source_text = make_modest_job(Path(self.tmp.name) / 'job', self.font)
        result = run_retypeset(str(job['stripped']), str(job['segments']),
                               str(job['mapping']), str(job['output']), **kwargs)
        return result, source_text

    def test_the_fixture_shrinks_without_refusing(self):
        # Without this the rest of the class could pass vacuously.
        result, _ = self.build()
        self.assertTrue(result.scaled, 'fixture did not shrink at all')
        worst = min(r['ratio'] for r in result.scaled)
        self.assertGreater(worst, 0.7, 'fixture refused; it must succeed')
        self.assertLess(worst, 1.0)

    def test_a_successful_build_above_our_floor_captures_at_the_callers_ratio(self):
        result, source_text = self.build(capture_dir=str(self.captures),
                                         capture_below=0.8)
        self.assertIsNotNone(result.output, 'the build must still succeed')
        cases = list(self.captures.iterdir())
        self.assertEqual(len(cases), 1, cases)
        manifest = json.loads((cases[0] / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['kind'], 'near-floor')
        self.assertIsNone(manifest['refusal'], 'nothing was refused')
        self.assertEqual(manifest['capture_below'], 0.8)
        keys = [o['key'] for o in manifest['occurrences']]
        self.assertIn(source_text, keys)

    def test_the_default_threshold_keeps_todays_behaviour(self):
        result, _ = self.build(capture_dir=str(self.captures))
        self.assertIsNotNone(result.output)
        self.assertFalse(self.captures.exists(),
                         'a successful build must not capture by default')

    def test_one_bundle_per_job_not_one_per_run(self):
        result, _ = self.build(capture_dir=str(self.captures), capture_below=0.8)
        self.assertEqual(len(list(self.captures.iterdir())), 1)

    def test_a_core_scaled_twice_in_one_pass_is_recorded_once(self):
        runs = [{'page': 0, 'key': 'same core', 'ratio': 0.80},
                {'page': 0, 'key': 'same core', 'ratio': 0.72},
                {'page': 1, 'key': 'other', 'ratio': 0.74}]
        kept = capture.near_floor_runs(runs, 0.75)
        self.assertEqual(len(kept), 2)
        same = [r for r in kept if r['key'] == 'same core'][0]
        # The worst attempt is the one that says whether it could ever fit.
        self.assertEqual(same['ratio'], 0.72)

    def test_runs_above_the_threshold_are_not_recorded(self):
        runs = [{'page': 0, 'key': 'fits', 'ratio': 0.90},
                {'page': 0, 'key': 'tight', 'ratio': 0.75}]
        kept = capture.near_floor_runs(runs, 0.75)
        self.assertEqual([r['key'] for r in kept], ['tight'])

    def test_the_threshold_has_its_own_environment_switch(self):
        self.assertIsNone(capture.resolve_capture_below(None, {}))
        self.assertEqual(
            capture.resolve_capture_below(None, {capture.BELOW_ENV_VAR: '0.75'}), 0.75)
        # An explicit argument wins, and unreadable text is ignored rather
        # than crashing a build over an evidence setting.
        self.assertEqual(
            capture.resolve_capture_below(0.8, {capture.BELOW_ENV_VAR: '0.75'}), 0.8)
        self.assertIsNone(
            capture.resolve_capture_below(None, {capture.BELOW_ENV_VAR: 'nonsense'}))


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


class BundleReplayTests(unittest.TestCase):
    """A bundle is only worth writing if it still reproduces the job.

    Every other test here proves a bundle is *complete* — the files are
    present, byte-identical, and the manifest is right. None of them proves
    it *replays*, which is the only reason the bundle exists. A change to
    the font-path rewriting could satisfy every completeness assertion and
    still produce a directory nobody can rebuild from.

    That gap matters more than it first looked. The consumer that prompted
    this feature publishes a promise that a customer's document is never
    stored and is deleted automatically, so it cannot switch capture on for
    real traffic at all — only staging, against synthetic or its own
    documents. For as long as that holds, a synthetic replay is not a
    supplement to real-world evidence; it is the only evidence there is.

    Each test moves the bundle somewhere else and deletes the original job
    first, so a bundle that secretly depends on a path outside itself fails
    here rather than months later.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.font = latin_font_sets()['sans']['regular']
        self.captures = Path(self.tmp.name) / 'captures'

    def _isolate(self, job_dir):
        """Move the one bundle away, then destroy the job it came from."""
        cases = list(self.captures.iterdir())
        self.assertEqual(len(cases), 1, cases)
        island = Path(self.tmp.name) / 'island'
        shutil.copytree(cases[0], island)
        shutil.rmtree(job_dir)
        self.assertFalse(job_dir.exists())
        return island

    def test_a_refusal_bundle_reproduces_the_same_refusal(self):
        job_dir = Path(self.tmp.name) / 'job'
        job, source_text = make_legacy_job(job_dir, self.font)
        with self.assertRaises(PlacementError) as first:
            run_retypeset(str(job['stripped']), str(job['segments']),
                          str(job['mapping']), str(job['output']),
                          capture_dir=str(self.captures))
        island = self._isolate(job_dir)

        with self.assertRaises(PlacementError) as again:
            run_retypeset(str(island / 'stripped.pdf'), str(island / 'segments.json'),
                          str(island / 'translations.json'), str(island / 'replayed.pdf'))
        before, after = first.exception, again.exception
        self.assertEqual(after.refusals['overflow'][0]['core'],
                         before.refusals['overflow'][0]['core'])
        self.assertEqual(after.page, before.page)
        # The ratio to the last float digit: a bundle that reproduces the
        # refusal but not the number has lost the measurement B1 needs.
        self.assertEqual(after.scale, before.scale)
        self.assertEqual(after.refusals['overflow'][0]['core'], source_text)
        self.assertFalse((island / 'replayed.pdf').exists())

    def test_a_near_floor_bundle_reproduces_the_same_ratios_and_succeeds(self):
        job_dir = Path(self.tmp.name) / 'job'
        job, _ = make_modest_job(job_dir, self.font)
        first = run_retypeset(str(job['stripped']), str(job['segments']),
                              str(job['mapping']), str(job['output']),
                              capture_dir=str(self.captures), capture_below=0.8)
        self.assertIsNotNone(first.output)
        island = self._isolate(job_dir)

        again = run_retypeset(str(island / 'stripped.pdf'), str(island / 'segments.json'),
                              str(island / 'translations.json'), str(island / 'replayed.pdf'))
        # This one must SUCCEED on replay. Nothing refused the first time,
        # and a near-floor bundle that refuses on rebuild is not the job.
        self.assertIsNotNone(again.output)
        self.assertEqual([r['ratio'] for r in again.scaled],
                         [r['ratio'] for r in first.scaled])

    def test_a_bundle_replays_with_no_font_outside_itself(self):
        """The fonts travel with it, so a caller's font path may vanish."""
        fonts_dir = Path(self.tmp.name) / 'fonts'
        fonts_dir.mkdir()
        local_font = fonts_dir / 'face.ttf'
        shutil.copy2(self.font, local_font)
        job_dir = Path(self.tmp.name) / 'job'
        job, _ = make_legacy_job(job_dir, str(local_font))
        with self.assertRaises(PlacementError):
            run_retypeset(str(job['stripped']), str(job['segments']),
                          str(job['mapping']), str(job['output']),
                          capture_dir=str(self.captures))
        island = self._isolate(job_dir)
        shutil.rmtree(fonts_dir)   # the face the mapping named is gone

        with self.assertRaises(PlacementError) as again:
            run_retypeset(str(island / 'stripped.pdf'), str(island / 'segments.json'),
                          str(island / 'translations.json'), str(island / 'replayed.pdf'))
        self.assertTrue(again.exception.refusals['overflow'])


class UnreadableSegmentsCaptureTests(unittest.TestCase):
    """Geometry is best effort; the bundle is not.

    `_write_bundle` reads segments.json to resolve each occurrence's origin
    and bbox. When that read fails the position is unknown and the note says
    so — but the manifest, the refusal and the occurrence keys are what make
    the bundle replayable, and none of them depend on that read. A build that
    truncates its own segments.json after the run has loaded it (a concurrent
    job, an interrupted write) must still leave a complete bundle behind.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.font = latin_font_sets()['sans']['regular']
        self.captures = Path(self.tmp.name) / 'captures'

    @staticmethod
    def _truncate_during_build(segments):
        """Make segments.json unparseable once the build has read it."""
        def progress(done, total):
            segments.write_text('{', encoding='utf-8')
        return progress

    def _one_manifest(self):
        cases = list(self.captures.iterdir())
        self.assertEqual(len(cases), 1, f'expected one bundle, got {cases}')
        manifest_path = cases[0] / 'manifest.json'
        self.assertTrue(manifest_path.is_file(),
                        'the bundle was abandoned instead of written')
        return json.loads(manifest_path.read_text(encoding='utf-8'))

    def test_refusal_bundle_survives_unreadable_segments(self):
        job, source_text = make_legacy_job(Path(self.tmp.name) / 'job', self.font)
        with self.assertRaises(PlacementError) as caught:
            run_retypeset(str(job['stripped']), str(job['segments']),
                          str(job['mapping']), str(job['output']),
                          capture_dir=str(self.captures),
                          progress=self._truncate_during_build(job['segments']))

        # The refusal itself is untouched by anything capture does.
        self.assertTrue(caught.exception.refusals['overflow'])
        self.assertEqual(caught.exception.refusals['overflow'][0]['core'], source_text)

        manifest = self._one_manifest()
        self.assertEqual(manifest['kind'], 'refusal')
        self.assertIsNotNone(manifest['refusal'],
                             'the original refusal was lost from the manifest')
        self.assertEqual(
            manifest['refusal']['refusals']['overflow'][0]['core'], source_text)

        occurrence = manifest['occurrence']
        self.assertEqual(occurrence['key'], source_text)
        self.assertIsNone(occurrence['position'])
        self.assertIn('could not read segments.json',
                      occurrence['position_note'])

    def test_a_parsed_null_is_not_a_failed_read(self):
        """`null` is valid JSON, so it must not answer as a read failure.

        Reading segments.json once per bundle means passing the parsed value
        around, and for a while a failed read was signalled by passing None —
        which a file containing `null` also parses to. The two then took the
        same branch, and a `null` segments.json produced a bundle whose
        `position_note` was None: no position, and no reason given either.

        The values below are b20fadd's, measured: at the baseline a
        segments.json that parses to anything other than an object writes no
        bundle at all, because `data.get` raises and capture swallows it.
        That is a pre-existing defect, pinned here only so this refactor
        cannot quietly change it; a deliberate fix updates this test.
        """
        self.assertIsNot(capture._UNREAD, None)

        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / 'null.json'
            good.write_text('null', encoding='utf-8')
            data, note = capture._read_segments(str(good))
            self.assertIsNone(data, 'a parsed null is the parsed document')
            self.assertIsNone(note)
            self.assertIsNot(data, capture._UNREAD)

            bad = Path(tmp) / 'truncated.json'
            bad.write_text('{', encoding='utf-8')
            data, note = capture._read_segments(str(bad))
            self.assertIs(data, capture._UNREAD)
            self.assertIn('could not read segments.json', note)
            # Only the unreadable one short-circuits to the note.
            self.assertEqual(capture._locate_position(data, note, 0, 'k'),
                             (None, note))

    def test_non_object_segments_behave_as_they_did_at_the_baseline(self):
        cases = {'null': 'null', 'list': '[]', 'string': '"nope"', 'number': '5'}
        for name, payload in cases.items():
            with self.subTest(payload=payload):
                captures = Path(self.tmp.name) / f'cap-{name}'
                job, _ = make_legacy_job(
                    Path(self.tmp.name) / f'job-{name}', self.font)

                def progress(done, total, segments=job['segments']):
                    segments.write_text(payload, encoding='utf-8')

                with self.assertRaises(PlacementError):
                    run_retypeset(str(job['stripped']), str(job['segments']),
                                  str(job['mapping']), str(job['output']),
                                  capture_dir=str(captures), progress=progress)
                self.assertFalse(
                    captures.exists() and list(captures.glob('*/manifest.json')),
                    f'{payload} wrote a bundle; b20fadd wrote none')

    def test_near_floor_bundle_survives_unreadable_segments(self):
        job, source_text = make_modest_job(Path(self.tmp.name) / 'job', self.font)
        result = run_retypeset(str(job['stripped']), str(job['segments']),
                               str(job['mapping']), str(job['output']),
                               capture_dir=str(self.captures), capture_below=0.8,
                               progress=self._truncate_during_build(job['segments']))
        self.assertIsNotNone(result.output, 'the build must still succeed')

        manifest = self._one_manifest()
        self.assertEqual(manifest['kind'], 'near-floor')
        self.assertIsNone(manifest['refusal'], 'nothing was refused')
        self.assertEqual(manifest['capture_below'], 0.8)

        occurrences = manifest['occurrences']
        self.assertTrue(occurrences, 'the near-floor occurrences were lost')
        self.assertIn(source_text, [o['key'] for o in occurrences])
        for occurrence in occurrences:
            self.assertIsNone(occurrence['position'])
            self.assertIn('could not read segments.json',
                          occurrence['position_note'])


if __name__ == '__main__':
    unittest.main()
