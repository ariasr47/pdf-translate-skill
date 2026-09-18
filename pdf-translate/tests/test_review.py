#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Row 32, the terminology loop: the review stage as a schema-versioned result.

The fixture of record is dev/jobs/fl150-ja-2026-09-17/ — the first FL-150 to
Japanese job, the one that shipped 世帯主 for "head of household" past every
gate and past qa_check. Its counts are measured from the files themselves, not
quoted from any brief: 247 cores, 13 merges, 5 overrides, 1 notice; 31 findings
(1 critical, 6 major, 24 minor); 25 accepted and 6 rejected by the file's own
resolutions; 12 terminology findings, 11 of them accepted.

A mismatch here is a defect in review.py, never a reason to edit the numbers.
"""
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path

# `from pdf_translate import qa_check` binds the CONVENIENCE FUNCTION the
# package exports, not the module. The glossary helpers live on the module.
qa_check = importlib.import_module('pdf_translate.qa_check')

from pdf_translate import review
from pdf_translate.review import (
    ReviewFinding, ReviewVerdict, append_termbase, load_review,
    review_pairs_md, review_prompt_md, run_review, termbase_rows, validate,
)

ROOT = Path(__file__).resolve().parents[2]
JOB = ROOT / 'dev' / 'jobs' / 'fl150-ja-2026-09-17'
REFERENCES = ROOT / 'pdf-translate' / 'references'

# The four legacy prose resolutions the real file actually stores. Three of
# them carry a qualifier BEFORE the colon ("rejected on measurement: …"), which
# is why the leading token is the first WORD of the trimmed head, not the whole
# head. A rule that stopped at the colon would put "rejected on measurement"
# outside the enum and refuse a finding the file resolved perfectly clearly.
LEGACY = (
    ('accepted, applied in v2 (2026-09-17)', 'accepted'),
    ('rejected: both renderings are attested; the legal reference works '
     'and the August bake-off differ', 'rejected'),
    ('rejected on measurement: the label ends at 259.5 pt, the checkbox '
     'starts at 261.0', 'rejected'),
    ('accepted with a different fix: 月給／週給／時給, the pattern Japanese '
     'forms use', 'accepted'),
)


def a_finding(**over):
    """A minimal valid finding dict; override one field per test."""
    base = {
        'core': 'head of household',
        'target': '世帯主',
        'category': 'terminology',
        'subtype': 'mistranslation',
        'severity': 'critical',
        'detail': 'US filing status is for the unmarried',
        'suggestion': '特定世帯主',
        'resolution': 'accepted',
    }
    base.update(over)
    return base


def a_review(findings=None, **over):
    doc = {
        'document': {'class': 'court form', 'issuer': 'Judicial Council',
                     'parallel_text': None, 'pair': 'en->ja',
                     'register': 'です・ます'},
        'reviewer': {'kind': 'model', 'name': 'Claude Opus',
                     'qualified_in_pair': False},
        'findings': findings if findings is not None else [a_finding()],
        'summary': {'critical': 1, 'major': 0, 'minor': 0,
                    'verdict': 'revise', 'remaining_risks': ''},
    }
    doc.update(over)
    return doc


class SchemaTests(unittest.TestCase):

    def test_the_enum_resolutions_are_accepted_as_is(self):
        for value in review.RESOLUTIONS:
            findings, errors = validate(a_review([a_finding(resolution=value)]))
            self.assertEqual(errors, [], value)
            self.assertEqual(findings[0].resolution, value)
            self.assertFalse(findings[0].migrated, value)
            self.assertEqual(findings[0].resolution_note, '')

    def test_a_legacy_prose_resolution_is_parsed_by_its_leading_token(self):
        for prose, expected in LEGACY:
            findings, errors = validate(a_review([a_finding(resolution=prose)]))
            self.assertEqual(errors, [], prose)
            self.assertEqual(findings[0].resolution, expected, prose)
            self.assertTrue(findings[0].migrated, prose)
            # The rationale is the most valuable text in the file; it is kept
            # whole, not truncated to the token that was parsed out of it.
            self.assertEqual(findings[0].resolution_note, prose)

    def test_a_leading_token_outside_the_enum_is_an_error_not_a_guess(self):
        findings, errors = validate(
            a_review([a_finding(resolution='deferred to the client')]))
        self.assertEqual(findings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn('deferred', errors[0])

    def test_an_unknown_category_is_an_error(self):
        findings, errors = validate(a_review([a_finding(category='vibes')]))
        self.assertEqual(findings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn('vibes', errors[0])

    def test_an_unknown_severity_is_an_error(self):
        findings, errors = validate(a_review([a_finding(severity='huge')]))
        self.assertEqual(findings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn('huge', errors[0])

    def test_a_malformed_review_json_is_an_error_not_an_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, 'review.json')
            with open(bad, 'w', encoding='utf-8') as fh:
                fh.write('{"findings": [')
            doc, errors = load_review(bad)
            self.assertEqual(doc, {})
            self.assertEqual(len(errors), 1)

    def test_a_missing_review_json_is_an_error_not_an_exception(self):
        doc, errors = load_review(os.path.join(tempfile.gettempdir(), 'nope.json'))
        self.assertEqual(doc, {})
        self.assertEqual(len(errors), 1)

    def test_a_missing_reviewer_block_is_an_error(self):
        doc = a_review()
        del doc['reviewer']
        findings, errors = validate(doc)
        self.assertTrue(any('reviewer' in e for e in errors))

    def test_a_finding_missing_core_is_an_error(self):
        bad = a_finding()
        del bad['core']
        findings, errors = validate(a_review([bad]))
        self.assertEqual(findings, [])
        self.assertTrue(any('core' in e for e in errors))

    def test_to_dict_carries_schema_and_version(self):
        from pdf_translate import __version__
        verdict = ReviewVerdict(work='w')
        got = verdict.to_dict()
        self.assertEqual(got['schema'], review.SCHEMA)
        self.assertEqual(got['version'], __version__)

    def test_the_verdict_and_finding_are_frozen(self):
        verdict = ReviewVerdict(work='w')
        with self.assertRaises(Exception):
            verdict.work = 'other'
        finding = validate(a_review())[0][0]
        with self.assertRaises(Exception):
            finding.core = 'other'


class GeneratorTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(JOB / 'translations.json', encoding='utf-8') as fh:
            cls.translations = json.load(fh)
        cls.notes = (JOB / 'NOTES.md').read_text(encoding='utf-8')

    def test_review_pairs_lists_every_core_merge_override_and_notice(self):
        md = review_pairs_md(self.translations, None, self.notes)
        self.assertIn('247 cores, 13 merges, 5 overrides, 1 notice', md)
        # Every core is actually present, not merely counted.
        for core in self.translations['translations']:
            self.assertIn(core, md)

    def test_review_pairs_reproduces_the_mapping_key_verbatim(self):
        # Findings key on this string. A case-folded or stripped column would
        # silently break --ingest for every finding on that core.
        md = review_pairs_md(self.translations, None, self.notes)
        self.assertIn('head of household', md)
        self.assertNotIn('Head Of Household', md)

    def test_review_pairs_states_page_numbers_are_one_based(self):
        md = review_pairs_md(self.translations, None, self.notes)
        self.assertIn('1-based', md)
        # merges[0] is on page 0 in the mapping; it must read as page 1.
        self.assertNotIn('page 0', md)

    def test_review_pairs_renders_an_override_as_positioned_parts(self):
        md = review_pairs_md(self.translations, None, self.notes)
        # overrides[0] parts, in x order, on one line.
        self.assertIn('公的扶助（例：TANF、SSI、GA/GR）', md)

    def test_review_pairs_renders_every_break_marker_as_a_line_break(self):
        # The marker is a layout instruction. It appears in core targets as
        # well as in the notice, and a reviser who reads it as a character
        # reports it as an error — so none may survive raw, and the file must
        # say what the rendering means.
        md = review_pairs_md(self.translations, None, self.notes)
        self.assertNotIn('‖', md)
        self.assertIn('<br>', md)
        self.assertIn('not a character in the translation', md)
        self.assertIn('【参考訳】裁判所には提出できません。', md)

    def test_review_prompt_fills_every_identity_slot(self):
        # The reference template carries SIX braces before {schema}, not the
        # four its prose claims. None of them may survive into the prompt a
        # reviser is handed. The JSON schema block that replaces {schema} has
        # braces of its own, so this checks the placeholders by name rather
        # than banning the character.
        document = {'class': 'court form', 'issuer': 'Judicial Council',
                    'parallel_text': None, 'pair': 'en->ja',
                    'register': 'です・ます'}
        out = review_prompt_md(document, 'review_pairs.md')
        for slot in ('{document class}', '{issuer}', '{source language}',
                     '{target language}', '{register}', '{schema}',
                     '{source}', '{target}', '{exists at URL'):
            self.assertNotIn(slot, out)
        self.assertIn('court form', out)
        self.assertIn('Judicial Council', out)
        self.assertIn('です・ます', out)

    def test_review_prompt_asks_for_term_and_term_target(self):
        out = review_prompt_md({'class': 'c', 'issuer': 'i',
                                'parallel_text': None, 'pair': 'en->ja',
                                'register': 'r'}, 'review_pairs.md')
        self.assertIn('term_target', out)
        self.assertIn('term', out)

    def test_review_prompt_keeps_the_reference_templates_mqm_categories(self):
        # The prompt is the reference template with its slots filled; the MQM
        # category sentence is what makes a finding classifiable, so it is the
        # line that must not drift.
        out = review_prompt_md({'class': 'c', 'issuer': 'i',
                                'parallel_text': None, 'pair': 'en->ja',
                                'register': 'r'}, 'review_pairs.md')
        for category in review.CATEGORIES:
            self.assertIn(category.replace('-', ' '), out.replace('-', ' '))
        self.assertIn('Do not rewrite anything you cannot justify', out)


class TermbaseTests(unittest.TestCase):

    def test_only_accepted_terminology_findings_reach_the_termbase(self):
        findings, _ = validate(a_review([
            a_finding(term='head of household', term_target='特定世帯主'),
            a_finding(category='accuracy', term='x', term_target='y'),
            a_finding(resolution='rejected', term='a', term_target='b'),
        ]))
        rows, skipped = termbase_rows(findings)
        self.assertEqual(rows, [('head of household', '特定世帯主')])
        self.assertEqual(skipped, [])

    def test_a_terminology_finding_without_a_named_term_is_skipped(self):
        findings, _ = validate(a_review([a_finding()]))
        rows, skipped = termbase_rows(findings)
        self.assertEqual(rows, [])
        self.assertEqual(skipped, ['head of household'])

    def test_a_terminology_finding_with_only_one_side_is_skipped(self):
        for half in ({'term': 'x'}, {'term_target': 'y'}):
            findings, _ = validate(a_review([a_finding(**half)]))
            rows, skipped = termbase_rows(findings)
            self.assertEqual(rows, [], half)
            self.assertEqual(len(skipped), 1, half)

    def test_appending_the_same_pair_twice_writes_one_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'glossary.csv')
            added, conflicts = append_termbase(path, [('a', 'b')])
            self.assertEqual(added, [('a', 'b')])
            added, conflicts = append_termbase(path, [('a', 'b')])
            self.assertEqual(added, [])
            self.assertEqual(conflicts, [])
            self.assertEqual(qa_check.load_glossary(path), [('a', 'b')])

    def test_a_source_term_remapped_to_a_different_target_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'glossary.csv')
            append_termbase(path, [('a', 'b')])
            added, conflicts = append_termbase(path, [('a', 'c')])
            self.assertEqual(added, [])
            self.assertEqual(conflicts, [('a', 'b', 'c')])
            # The existing mapping is untouched: a conflict is reported, not
            # resolved by whoever ran --ingest last.
            self.assertEqual(qa_check.load_glossary(path), [('a', 'b')])

    def test_a_term_containing_a_comma_round_trips_through_load_glossary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'glossary.csv')
            append_termbase(path, [('married, filing separately', '夫婦個別申告')])
            self.assertEqual(qa_check.load_glossary(path),
                             [('married, filing separately', '夫婦個別申告')])

    def test_the_written_file_is_readable_by_qa_check_glossary_findings(self):
        # The real enforcement path, end to end: the loop's output is the
        # gate's input, and 世帯主 is the term this whole row exists for.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'glossary.csv')
            append_termbase(path, [('head of household', '特定世帯主')])
            terms = qa_check.load_glossary(path)
            hits = qa_check.glossary_findings(
                {'head of household': '世帯主'}, terms)
            self.assertTrue(hits, 'the termbase must catch the reverted term')

    def test_the_file_is_written_without_a_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'glossary.csv')
            append_termbase(path, [('a', 'b')])
            self.assertFalse(Path(path).read_bytes().startswith(b'\xef\xbb\xbf'))


class Fl150FixtureTests(unittest.TestCase):
    """The brief's §4 Proof, first half — against the real files."""

    @classmethod
    def setUpClass(cls):
        cls.doc, cls.load_errors = load_review(str(JOB / 'review.json'))
        cls.findings, cls.errors = validate(cls.doc)

    def test_the_real_review_json_validates_with_migration(self):
        self.assertEqual(self.load_errors, [])
        self.assertEqual(self.errors, [])
        self.assertEqual(len(self.findings), 31)
        by_sev = {}
        for f in self.findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        self.assertEqual(by_sev, {'critical': 1, 'major': 6, 'minor': 24})
        by_res = {}
        for f in self.findings:
            by_res[f.resolution] = by_res.get(f.resolution, 0) + 1
        self.assertEqual(by_res, {'accepted': 25, 'rejected': 6})

    def test_the_real_file_has_twelve_terminology_findings_eleven_accepted(self):
        term = [f for f in self.findings if f.category == 'terminology']
        self.assertEqual(len(term), 12)
        self.assertEqual(len([f for f in term if f.resolution == 'accepted']), 11)

    def test_every_migrated_resolution_keeps_its_prose(self):
        migrated = [f for f in self.findings if f.migrated]
        self.assertTrue(migrated)
        for f in migrated:
            self.assertTrue(f.resolution_note)
            self.assertTrue(f.resolution_note.casefold()
                            .startswith(f.resolution))

    def test_the_real_job_names_no_terms_so_every_pair_is_skipped(self):
        # MEASURED, and it is the point of ruling 3. This review pass predates
        # the term/term_target fields, so not one of its eleven accepted
        # terminology findings names a term. Six of them are keyed to a whole
        # sentence ("Utilities (gas, electric, water, trash)" — the term is
        # Utilities), so the core cannot stand in for the term either. The
        # loop reports all eleven and writes none: a termbase that gates the
        # next job is never filled by inference.
        rows, skipped = termbase_rows(self.findings)
        self.assertEqual(rows, [])
        self.assertEqual(len(skipped), 11)

    def test_the_critical_finding_is_the_one_this_row_exists_for(self):
        critical = [f for f in self.findings if f.severity == 'critical']
        self.assertEqual(len(critical), 1)
        self.assertEqual(critical[0].core, 'head of household')
        self.assertEqual(critical[0].target, '世帯主')
        self.assertEqual(critical[0].category, 'terminology')


class RunReviewTests(unittest.TestCase):

    def _job(self, tmp, with_review=True):
        work = Path(tmp)
        for name in ('translations.json', 'NOTES.md'):
            (work / name).write_bytes((JOB / name).read_bytes())
        if with_review:
            (work / 'review.json').write_bytes((JOB / 'review.json').read_bytes())
        return str(work)

    def test_run_review_writes_the_two_files_and_prints_nothing(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmp:
            work = self._job(tmp, with_review=False)
            buf = io.StringIO()
            with redirect_stdout(buf):
                verdict = run_review(work)
            self.assertEqual(buf.getvalue(), '')
            self.assertTrue(os.path.isfile(os.path.join(work, 'review_pairs.md')))
            self.assertTrue(os.path.isfile(os.path.join(work, 'review_prompt.md')))
            self.assertFalse(verdict.present)
            self.assertTrue(verdict.blocks_delivery)

    def test_run_review_with_ingest_fills_the_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = self._job(tmp)
            verdict = run_review(work, ingest='review.json')
            self.assertTrue(verdict.present)
            self.assertEqual(len(verdict.findings), 31)
            self.assertEqual(verdict.counts['accepted'], 25)
            self.assertEqual(verdict.counts['rejected'], 6)
            self.assertEqual(verdict.counts['open'], 0)
            self.assertEqual(len(verdict.termbase_skipped), 11)
            self.assertFalse(verdict.blocks_delivery)
            self.assertEqual(verdict.exit_code, 0)

    def test_an_open_finding_blocks_delivery_and_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = self._job(tmp)
            path = os.path.join(work, 'review.json')
            with open(path, encoding='utf-8') as fh:
                doc = json.load(fh)
            doc['findings'][0]['resolution'] = 'open'
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump(doc, fh, ensure_ascii=False)
            verdict = run_review(work, ingest='review.json')
            self.assertEqual(len(verdict.open_findings), 1)
            self.assertTrue(verdict.blocks_delivery)
            self.assertEqual(verdict.exit_code, 1)

    def test_a_missing_work_directory_is_an_error_not_an_exception(self):
        verdict = run_review(os.path.join(tempfile.gettempdir(), 'no-such-work'))
        self.assertTrue(verdict.errors)
        self.assertEqual(verdict.exit_code, 2)

    def test_run_review_never_creates_the_work_directory(self):
        target = os.path.join(tempfile.gettempdir(), 'review-should-not-exist')
        run_review(target)
        self.assertFalse(os.path.isdir(target))

    def test_the_verdict_round_trips_through_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = self._job(tmp)
            verdict = run_review(work, ingest='review.json')
            text = json.dumps(verdict.to_dict(), ensure_ascii=False)
            back = json.loads(text)
            self.assertEqual(back['schema'], review.SCHEMA)
            self.assertEqual(len(back['findings']), 31)


if __name__ == '__main__':
    unittest.main()
