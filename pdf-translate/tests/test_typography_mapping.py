"""New mappings cannot silently lose occurrences, style or input binding."""
import copy
import importlib
import json
from pathlib import Path
import tempfile
import unittest

import pymupdf

from pdf_translate import run_extract
from pdf_translate.results import MappingError
from pdf_translate.typography import bind_extraction
from tests.typography_fixtures import make_source, make_mapping


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Resolved, because the reader resolves too and the comparison is
        # between the two. On Windows the temp directory comes back in 8.3
        # short form when the user name is long enough to need one
        # (RUNNER~1 for runneradmin on CI), so an unresolved expectation
        # names the same file by a different string and the test fails for
        # a reason that has nothing to do with the mapping.
        self.work = Path(self.temp.name).resolve()
        source = make_source(self.work / 'original.pdf')
        result = run_extract(str(source), str(self.work), typography=True)
        self.extraction = json.loads(Path(result.segments_path).read_text(encoding='utf-8'))
        self.conf = make_mapping(self.extraction)

    def reader(self):
        try:
            return importlib.import_module('pdf_translate.mapping')
        except ModuleNotFoundError:
            self.fail('The shared typography mapping reader is not implemented')

    def parse(self, conf=None, extraction=None):
        return self.reader().parse_mapping(
            json.dumps(self.conf if conf is None else conf, ensure_ascii=False),
            extraction=self.extraction if extraction is None else extraction,
            mapping_dir=self.work)

    def refused(self, conf, reason, extraction=None):
        with self.assertRaises(MappingError) as caught:
            self.parse(conf, extraction)
        self.assertEqual(caught.exception.refusals['typography'][0]['reason'], reason)
        self.assertTrue({'occurrence_id', 'run_id', 'page', 'source_text'} <=
                        caught.exception.refusals['typography'][0].keys())

    def test_reordered_targets_keep_exact_style_associations(self):
        self.conf['targets'][0]['runs'] = [
            {'text': 'AHORA ', 'source_runs': ['s0/r1']},
            {'text': 'pague', 'source_runs': ['s0/r0']}]
        doc = self.parse()
        self.assertEqual([t.occurrence_id for t in doc.targets], ['s0', 's1'])
        self.assertEqual([r.font_role for r in doc.targets[0].runs], ['bold', 'regular'])
        self.assertEqual([r.font_class for r in doc.targets[1].runs], ['serif', 'serif'])
        self.assertEqual(doc.targets[1].runs[1].font_role, 'bold_italic')
        self.conf['font_sets']['serif']['regular'] = 'modified.ttf'
        self.extraction['segments'][0]['text'] = 'modified source'
        self.assertNotIn('modified', str(doc.font_sets))
        self.assertEqual(doc.targets[0].source_text, 'Pay NOW')

    def test_shape_and_coverage_mutations_refuse_with_typed_context(self):
        mutations = [
            ('unknown-format', lambda c: c.update(format='typography-2'), 'invalid-style-reference'),
            ('mixed-root', lambda c: c.update(translations={}), 'invalid-style-reference'),
            ('missing', lambda c: c['targets'].pop(), 'unknown-occurrence'),
            ('duplicate', lambda c: c['targets'].append(copy.deepcopy(c['targets'][0])), 'duplicate-occurrence'),
            ('foreign', lambda c: c['targets'][0].update(occurrence_id='s999'), 'unknown-occurrence'),
            ('cross-reference', lambda c: c['targets'][0]['runs'][0].update(source_runs=['s1/r0']), 'invalid-style-reference'),
            ('duplicate-run', lambda c: c['targets'][0]['runs'][0].update(source_runs=['s0/r0','s0/r0']), 'invalid-style-reference'),
            ('omitted-emphasis', lambda c: c['targets'][0]['runs'].pop(), 'unsupported-style-alignment'),
            ('wrong-binding', lambda c: c.update(extraction_id='0'*64), 'stale-extraction'),
            ('empty-target', lambda c: c['targets'][0]['runs'][0].update(text=''), 'unsupported-style-alignment'),
            ('mixed-styles', lambda c: c['targets'][0].update(runs=[{'text':'Pague ahora','source_runs':['s0/r0','s0/r1']}]), 'unsupported-style-alignment'),
            ('missing-role', lambda c: c['font_sets']['sans'].pop('bold'), 'missing-font-role'),
            ('wrong-role-key', lambda c: c['font_sets']['sans'].update({'bold-italic':'face.ttf'}), 'invalid-style-reference'),
            ('bad-scale', lambda c: c.update(allow_scale=[{'occurrence_id':'s99','reason':'approved'}]), 'unknown-occurrence'),
            ('empty-scale-reason', lambda c: c.update(allow_scale=[{'occurrence_id':'s0','reason':''}]), 'invalid-style-reference'),
            ('duplicate-scale', lambda c: c.update(allow_scale=[{'occurrence_id':'s0','reason':'approved'}]*2), 'duplicate-occurrence'),
            ('unknown-resolution', lambda c: c.update(source_font_resolutions=[{'font_id':'f999','class':'sans','bold':False,'italic':False,'reason':'inspected'}]), 'invalid-style-reference'),
        ]
        for name, mutate, reason in mutations:
            with self.subTest(case=name):
                conf = copy.deepcopy(self.conf)
                mutate(conf)
                self.refused(conf, reason)

    def test_nested_duplicate_keys_are_rejected_only_for_new_format(self):
        reader = self.reader()
        for text in ['{"format":"legacy","format":"typography-1"}',
                     json.dumps(self.conf).replace('"text": "Pay "',
                                                   '"text": "bad", "text": "Pay "', 1)]:
            with self.assertRaises(MappingError):
                reader.parse_mapping(text, extraction=self.extraction)
        legacy = reader.parse_mapping('{"translations":{"Pay":"Uno","Pay":"Dos"}}')
        self.assertEqual(legacy.legacy['translations']['Pay'], 'Dos')
        self.assertEqual(legacy.format, 'legacy')

    def test_plain_markup_like_text_is_literal_and_scaling_is_occurrence_specific(self):
        self.conf['targets'][0]['runs'][0]['text'] = '<b>literal</b> '
        self.conf['allow_scale'] = [{'occurrence_id':'s0', 'reason':'author reviewed'}]
        doc = self.parse()
        self.assertEqual(doc.targets[0].runs[0].text, '<b>literal</b> ')
        self.assertEqual(doc.allow_scale, {'s0':'author reviewed'})
        self.assertEqual(doc.targets[1].runs[0].text, 'Pay ')

    def test_control_marks_and_unsupported_scripts_do_not_reach_placement(self):
        for text in ['one\ntwo', 'one‖two', 'x\u202ey', 'e\u0301', '骨\ufe00',
                     'مرحبا', 'हिन्दी', 'Привет', '😀']:
            with self.subTest(text=text):
                conf = copy.deepcopy(self.conf)
                conf['targets'][0]['runs'][0]['text'] = text
                self.refused(conf, 'unsupported-typography-construct')

    def test_decomposed_cluster_split_is_refused(self):
        self.conf['targets'][0]['runs'][0]['text'] = 'e'
        self.conf['targets'][0]['runs'][1]['text'] = '\u0301'
        self.refused(self.conf, 'unsupported-typography-construct')

    def test_common_document_symbols_remain_plain_text(self):
        self.conf['targets'][0]['runs'][0]['text'] = '© Invoice ™ → '
        parsed = self.parse()
        self.assertEqual(parsed.targets[0].runs[0].text, '© Invoice ™ → ')

    def test_same_style_can_expand_across_multiple_target_runs(self):
        self.conf['targets'][0]['runs'][:1] = [
            {'text':'Por ', 'source_runs':['s0/r0']},
            {'text':'favor ', 'source_runs':['s0/r0']}]
        doc = self.parse()
        self.assertEqual([r.font_role for r in doc.targets[0].runs],
                         ['regular','regular','bold'])

    def test_extraction_edit_and_missing_extraction_are_stale(self):
        edited = copy.deepcopy(self.extraction)
        edited['segments'][0]['style_runs'][0]['bold'] = True
        self.refused(self.conf, 'stale-extraction', edited)
        with self.assertRaises(MappingError) as caught:
            self.reader().parse_mapping(json.dumps(self.conf))
        self.assertEqual(caught.exception.refusals['typography'][0]['reason'],
                         'stale-extraction')

    def test_duplicate_extraction_occurrences_cannot_be_rebound_into_valid_input(self):
        edited = copy.deepcopy(self.extraction)
        edited['segments'].append(copy.deepcopy(edited['segments'][0]))
        edited['typography'] = bind_extraction(edited)
        conf = copy.deepcopy(self.conf)
        conf['extraction_id'] = edited['typography']['extraction_id']
        self.refused(conf, 'duplicate-occurrence', edited)

    def test_unknown_font_resolution_is_explicit_and_cannot_conflict(self):
        source = self.work / 'unknown.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((30,60),'Label',fontname='cour')
            doc.save(source)
        result=run_extract(str(source), str(self.work/'unknown'),typography=True)
        extraction=json.loads(Path(result.segments_path).read_text(encoding='utf-8'))
        conf=make_mapping(extraction)
        self.refused(conf,'unresolved-source-style',extraction)
        font_id=extraction['segments'][0]['style_runs'][0]['font_id']
        resolution={'font_id':font_id,'class':'serif','bold':False,'italic':False,
                    'reason':'author inspected source'}
        conf['source_font_resolutions']=[resolution]
        parsed=self.parse(conf,extraction)
        self.assertEqual(parsed.targets[0].runs[0].font_class,'serif')
        self.assertEqual(parsed.source_font_resolutions[0]['reason'],resolution['reason'])
        conf['source_font_resolutions']=[resolution,resolution]
        self.refused(conf,'invalid-style-reference',extraction)
        known=copy.deepcopy(self.conf)
        known_id=self.extraction['segments'][0]['style_runs'][0]['font_id']
        known['source_font_resolutions']=[dict(resolution,font_id=known_id)]
        self.refused(known,'invalid-style-reference')
        conf['source_font_resolutions']=[dict(resolution,bold=1)]
        self.refused(conf,'invalid-style-reference',extraction)

    def test_document_targets_do_not_satisfy_page_coverage(self):
        conf=copy.deepcopy(self.conf)
        conf['document_targets']={'Pay NOW':'Pague ahora'}
        conf['targets']=[]
        self.refused(conf,'unknown-occurrence')

    def test_font_paths_and_mapping_digest_are_not_working_directory_dependent(self):
        path=self.work/'translations.json'
        path.write_text(json.dumps(self.conf),encoding='utf-8')
        doc=self.reader().load_mapping(path)
        self.assertEqual(doc.font_sets['sans']['bold'], str(self.work/'fonts/sans-bold.ttf'))
        reordered=dict(reversed(list(self.conf.items())))
        self.assertEqual(doc.mapping_sha256,self.parse(reordered).mapping_sha256)

    def test_a_noncanonical_mapping_dir_resolves_to_the_same_font_path(self):
        """Two spellings of one directory must give one resolved font path.

        The reader resolves `mapping_dir`, so how the caller spelled it must
        not reach `font_sets`. Windows CI found this with an 8.3 short name
        (RUNNER~1 for runneradmin); `fonts/..` reproduces the same class
        anywhere. It has to be `..` and not `.`, because pathlib drops a
        single dot on construction and the test would pass even if the
        reader stopped resolving.
        """
        detour=self.work/'fonts'/'..'
        self.assertNotEqual(str(detour),str(self.work),
                            'the detour collapsed, so this proves nothing')
        path=self.work/'translations.json'
        path.write_text(json.dumps(self.conf),encoding='utf-8')
        straight=self.reader().load_mapping(path)
        noncanonical=self.reader().parse_mapping(
            json.dumps(self.conf,ensure_ascii=False),extraction=self.extraction,
            mapping_dir=detour)
        self.assertEqual(noncanonical.font_sets,straight.font_sets)
        self.assertEqual(noncanonical.font_sets['sans']['bold'],
                         str(self.work/'fonts/sans-bold.ttf'))

    def test_nonfinite_and_unexpected_nested_fields_are_invalid(self):
        conf=copy.deepcopy(self.conf)
        conf['targets'][0]['runs'][0]['unexpected']=float('nan')
        self.refused(conf,'invalid-style-reference')

    def test_locale_tags_and_document_metadata_follow_scope(self):
        for lang in ('ja', 'zh-Hans', 'es-MX'):
            with self.subTest(lang=lang):
                conf=copy.deepcopy(self.conf)
                conf['lang']=lang
                self.assertEqual(self.parse(conf).lang,lang)
        for lang in ('zh-Hant','ko','Japanese'):
            conf=copy.deepcopy(self.conf)
            conf['lang']=lang
            self.refused(conf,'unsupported-typography-construct')
        extraction=copy.deepcopy(self.extraction)
        extraction['document']['title']='Invoice title'
        extraction['typography']=bind_extraction(extraction)
        conf=copy.deepcopy(self.conf)
        conf['extraction_id']=extraction['typography']['extraction_id']
        self.refused(conf,'invalid-style-reference',extraction)
        conf['document_targets']['Invoice title']='Titulo de factura'
        self.assertEqual(self.parse(conf,extraction).document_targets,
                         {'Invoice title':'Titulo de factura'})

    def test_multiple_source_runs_with_the_same_style_can_combine(self):
        source=self.work/'same-style.pdf'
        font=Path(__file__).parent/'fonts/NotoSans-Regular.ttf'
        with pymupdf.open() as doc:
            page=doc.new_page()
            page.insert_text((30,60),'Pay ',fontname='helv',fontsize=12)
            x=30+pymupdf.get_text_length('Pay ',fontname='helv',fontsize=12)
            page.insert_text((x,60),'NOW',fontname='fixture',fontfile=str(font),fontsize=12)
            doc.save(source)
        result=run_extract(str(source),str(self.work/'same-style'),typography=True)
        extraction=json.loads(Path(result.segments_path).read_text(encoding='utf-8'))
        self.assertEqual(len(extraction['segments'][0]['style_runs']),2)
        conf=make_mapping(extraction)
        conf['targets'][0]['runs']=[{'text':'Pague ahora','source_runs':['s0/r0','s0/r1']}]
        parsed=self.parse(conf,extraction)
        self.assertEqual(parsed.targets[0].runs[0].font_role,'regular')
        self.assertEqual(parsed.targets[0].runs[0].source_runs,('s0/r0','s0/r1'))

    def test_malformed_bound_extraction_is_an_input_error_not_a_traceback(self):
        mutations = [
            ('font-id', lambda e: e['segments'][0]['style_runs'][0].update(font_id=[])),
            ('document', lambda e: e.update(document=None)),
            ('options', lambda e: e['typography'].update(options=None)),
            ('boolean-schema', lambda e: e['typography'].update(schema=True)),
            ('run-id', lambda e: e['segments'][0]['style_runs'][0].update(run_id='s0/rbad')),
            ('color', lambda e: e['segments'][0].update(color=True)),
            ('run-size', lambda e: e['segments'][0]['style_runs'][0].update(size=[])),
            ('field-list', lambda e: e['typography'].update(fields=None)),
        ]
        for name, mutate in mutations:
            with self.subTest(case=name):
                extraction=copy.deepcopy(self.extraction)
                mutate(extraction)
                extraction['typography']=bind_extraction(extraction)
                conf=copy.deepcopy(self.conf)
                conf['extraction_id']=extraction['typography']['extraction_id']
                self.refused(conf,'invalid-style-reference',extraction)


if __name__ == '__main__':
    unittest.main()
