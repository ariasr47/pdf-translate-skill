"""Occurrence-aware language checks and review freshness, without a renderer."""
import json
from pathlib import Path
import tempfile
import unittest
import pymupdf

from pdf_translate import run_extract, run_qa, run_review
from pdf_translate.mapping import load_mapping
from pdf_translate.results import MappingError
from tests.typography_fixtures import latin_font_sets, make_job, make_mapping


class TypographyReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.job = make_job(self.work)

    def change(self, edit):
        conf = json.loads(self.job['mapping'].read_text(encoding='utf-8'))
        edit(conf)
        self.job['mapping'].write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')

    def review_doc(self):
        mapping = load_mapping(self.job['mapping'])
        target = mapping.targets[0]
        return {'reviewer': {'name': 'Fixture reviewer'},
                'typography': {'extraction_id': mapping.extraction_id,
                               'mapping_sha256': mapping.mapping_sha256},
                'findings': [{'core': target.source_text,
                              'target': ''.join(r.text for r in target.runs),
                              'occurrence_id': target.occurrence_id,
                              'source_runs': [s for r in target.runs for s in r.source_runs],
                              'category': 'terminology', 'subtype': 'mistranslation',
                              'severity': 'minor', 'detail': 'Use the agreed term.',
                              'term': 'Pay', 'term_target': 'Pague', 'resolution': 'accepted'}]}

    def ingest(self, doc, generate=False):
        (self.work / 'review.json').write_text(json.dumps(doc), encoding='utf-8')
        return run_review(str(self.work), ingest='review.json', generate=generate)

    def test_numbers_and_glossary_keep_both_occurrences(self):
        self.change(lambda c: [t['runs'][0].update(text=f'Pague {i + 2} ')
                               for i, t in enumerate(c['targets'])])
        glossary = self.work / 'glossary.csv'
        glossary.write_text('Pay,Abone\n', encoding='utf-8')
        result = run_qa(str(self.job['mapping']), str(self.job['segments']), str(glossary))
        for kind in ('numbers', 'glossary', 'inconsistent'):
            findings = [f for f in result.findings if f['kind'] == kind]
            self.assertEqual({f['occurrence_id'] for f in findings}, {'s0', 's1'})
            self.assertTrue(all(f['page'] == 0 and f['source_runs'] and f['core'] == 'Pay NOW'
                                for f in findings))

    def test_style_alone_is_not_wording_inconsistency(self):
        result = run_qa(str(self.job['mapping']))
        self.assertFalse(any(f['kind'] == 'inconsistent' for f in result.findings))
        echoes = [f for f in result.findings if f['kind'] == 'untranslated']
        self.assertEqual({f['occurrence_id'] for f in echoes}, {'s0', 's1'})

    def test_qa_uses_plain_literal_text(self):
        self.change(lambda c: c['targets'][0]['runs'][0].update(text='<12> '))
        glossary = self.work / 'glossary.csv'
        glossary.write_text('Pay,<12>\n', encoding='utf-8')
        findings = run_qa(str(self.job['mapping']), glossary_path=str(glossary)).findings
        self.assertTrue(any(f['kind'] == 'numbers' and f['occurrence_id'] == 's0' for f in findings))
        self.assertFalse(any(f['kind'] == 'glossary' and f['occurrence_id'] == 's0' for f in findings))

    def test_generated_rows_show_associations_escape_text_and_bind_prompt(self):
        self.change(lambda c: c['targets'][0]['runs'].reverse())
        self.change(lambda c: c['targets'][0]['runs'][0].update(text='<b>|NOW</b>'))
        before = self.job['mapping'].read_bytes()
        result = run_review(str(self.work))
        self.assertFalse(result.errors, result.errors)
        pairs = (self.work / 'review_pairs.md').read_text(encoding='utf-8')
        prompt = (self.work / 'review_prompt.md').read_text(encoding='utf-8')
        mapping = load_mapping(self.job['mapping'])
        for marker in ('s0', 's1', 'sans/bold', 'serif/bold_italic', 's0/r1', 's0/r0', '30.0', '60.0'):
            self.assertIn(marker, pairs)
        self.assertIn('&lt;b&gt;\\|NOW&lt;/b&gt;', pairs)
        self.assertNotIn('<b>', pairs)
        self.assertLess(pairs.index('s0/r1'), pairs.index('s0/r0'))
        self.assertIn(mapping.extraction_id, prompt)
        self.assertIn(mapping.mapping_sha256, prompt)
        self.assertIn('occurrence_id', prompt)
        self.assertEqual(self.job['mapping'].read_bytes(), before)

    def test_stale_or_missing_binding_cannot_append_terms(self):
        for mutation in ('missing', 'extraction_id', 'mapping_sha256'):
            doc = self.review_doc()
            if mutation == 'missing':
                del doc['typography']
            else:
                doc['typography'][mutation] = '0' * 64
            result = self.ingest(doc, generate=True)
            self.assertTrue(result.errors, mutation)
            self.assertFalse(result.findings)
            self.assertFalse(result.termbase_added)
            self.assertFalse((self.work / 'glossary.csv').exists())

    def test_repeated_core_requires_occurrence_and_source_run_ids(self):
        for key in ('occurrence_id', 'source_runs'):
            doc = self.review_doc()
            del doc['findings'][0][key]
            result = self.ingest(doc)
            self.assertTrue(result.errors, key)
            self.assertFalse(result.findings)

    def test_foreign_duplicate_or_incorrect_associations_are_rejected(self):
        for mutation in ({'occurrence_id': 'foreign'}, {'source_runs': ['s1/r0']},
                         {'source_runs': ['s0/r0', 's0/r0']}, {'source_runs': 's0/r0'},
                         {'occurrence_id': 1}, {'target': 'wrong'}, {'core': 'wrong'}):
            doc = self.review_doc()
            doc['findings'][0].update(mutation)
            result = self.ingest(doc)
            self.assertTrue(result.errors, mutation)
            self.assertFalse(result.findings, mutation)

    def test_valid_ids_survive_serialization_and_read_only_ingestion(self):
        run_review(str(self.work))
        doc = self.review_doc()
        (self.work / 'review.json').write_text(json.dumps(doc), encoding='utf-8')
        before = {p.name: p.read_bytes() for p in self.work.iterdir() if p.is_file()}
        result = run_review(str(self.work), ingest='review.json', generate=False)
        self.assertFalse(result.errors, result.errors)
        finding = result.to_dict()['findings'][0]
        self.assertEqual(finding['occurrence_id'], 's0')
        self.assertEqual(finding['source_runs'], ['s0/r0', 's0/r1'])
        self.assertFalse(result.wrote)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.work.iterdir() if p.is_file()})

    def test_bound_accepted_terms_append_only_explicit_pairs(self):
        doc = self.review_doc()
        result = self.ingest(doc, generate=True)
        self.assertFalse(result.errors, result.errors)
        self.assertEqual(result.termbase_added, (('Pay', 'Pague'),))
        self.assertEqual(self.ingest(doc, generate=True).termbase_added, ())

    def test_reordered_mapping_invalidates_prior_review(self):
        doc = self.review_doc()
        self.change(lambda c: c['targets'][0]['runs'].reverse())
        result = self.ingest(doc)
        self.assertTrue(any('mapping' in error.lower() for error in result.errors))

    def test_unknown_format_does_not_succeed_with_zero_checks(self):
        self.change(lambda c: c.update(format='typography-future'))
        with self.assertRaises(MappingError):
            run_qa(str(self.job['mapping']))
        result = run_review(str(self.work))
        self.assertTrue(result.errors)
        self.assertFalse(result.wrote)

    def test_invalid_mapping_prevents_review_writes(self):
        doc = self.review_doc()
        self.change(lambda c: c.update(extraction_id='0' * 64))
        result = self.ingest(doc, generate=True)
        self.assertTrue(result.errors)
        self.assertFalse(result.wrote)
        self.assertFalse(result.findings)

    def test_document_metadata_keeps_language_qa_and_review(self):
        with pymupdf.open(self.job['original']) as doc:
            doc.set_metadata({'title': 'Payment 12'})
            data = doc.tobytes()
        self.job['original'].write_bytes(data)
        run_extract(str(self.job['original']), str(self.work), typography=True)
        extraction = json.loads(self.job['segments'].read_text(encoding='utf-8'))
        self.job['mapping'].write_text(json.dumps(make_mapping(extraction, latin_font_sets())), encoding='utf-8')
        self.change(lambda c: c.update(document_targets={'Payment 12': 'Pago 13'}))
        findings = run_qa(str(self.job['mapping'])).findings
        self.assertTrue(any(f['kind'] == 'numbers' and f['core'] == 'Payment 12' and
                            f['where'] == 'document-metadata' for f in findings))
        doc = self.review_doc()
        finding = doc['findings'][0]
        finding.update(core='Payment 12', target='Pago 13')
        del finding['occurrence_id'], finding['source_runs']
        result = self.ingest(doc)
        self.assertFalse(result.errors, result.errors)
        self.assertNotIn('occurrence_id', result.findings[0].to_dict())


if __name__ == '__main__':
    unittest.main()
