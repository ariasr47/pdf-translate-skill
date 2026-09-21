"""Reproducible synthetic typography jobs; no model or product source is used.

From pdf-translate/, naming the checkout under test the way the parity runners do:

    PYTHONPATH=<checkout>/pdf-translate python ../dev/probes/typography_acceptance.py \
        --work DIR --fonts tests/fonts

`sys.path[0]` is this probe's own directory, not the caller's, so without that the
import resolves to whichever pdf_translate the interpreter already installs — an
editable venv target is a different checkout and fails or measures the wrong code.
The recorded package path below is the one actually measured.

The output directory must be empty. Every case keeps its source, final PDF,
authored mapping, evidence JSON and actual 150-dpi rasters for independent review.
"""
import argparse
import json
from pathlib import Path
import platform
import subprocess

import fontTools
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
import pikepdf
import pymupdf

import pdf_translate
from pdf_translate import (run_extract, run_field_fonts, run_prepare_font,
                           run_qa, run_retypeset, run_review, run_strip, run_verify)
from pdf_translate.mapping import load_mapping, role_name
from pdf_translate.typography import observe_fonts, page_geometry, source_digest, _unsubset


STYLES = {'sans': {'regular': 'helv', 'bold': 'hebo', 'italic': 'heit', 'bold_italic': 'hebi'},
          'serif': {'regular': 'tiro', 'bold': 'tibo', 'italic': 'tiit', 'bold_italic': 'tibi'}}
SUFFIX = {'regular': 'Regular', 'bold': 'Bold', 'italic': 'Italic', 'bold_italic': 'BoldItalic'}
CASES = ('repeated-reordered', 'latin-roles', 'italic-overhang', 'ja', 'zh-Hans', 'blank-page')


def write_json(path, value, root, fixtures):
    def clean(item):
        if isinstance(item, dict):
            return {k: clean(v) for k, v in item.items()}
        if isinstance(item, (tuple, list)):
            return [clean(v) for v in item]
        if isinstance(item, str):
            for prefix, label in ((str(root.resolve()), '.'), (str(fixtures.resolve()), 'fixture-fonts')):
                if item.startswith(prefix):
                    return label + item[len(prefix):].replace('\\', '/')
        return item
    path.write_text(json.dumps(clean(value), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def source_rows(case):
    if case in ('repeated-reordered', 'blank-page'):
        return [[('Please pay ', 'sans', 'regular'), ('NOW', 'sans', 'bold')],
                [('Please pay ', 'serif', 'regular'), ('NOW', 'serif', 'bold_italic')]]
    if case == 'italic-overhang':
        # A glyph-overhang stress case, not a language example. Comparable
        # source ink keeps the existing ink-ratio check meaningful.
        return [[('f' * 90, 'serif', 'italic')]]
    roles = ('regular', 'bold') if case in ('ja', 'zh-Hans') else tuple(SUFFIX)
    return [[('Payment details', cls, role)] for cls in STYLES for role in roles]


def build_case(work, fixtures, case):
    work.mkdir()
    selected = work / 'selected'
    selected.mkdir()
    source, stripped, final = (work / n for n in ('original.pdf', 'stripped.pdf', 'final.pdf'))
    rows = source_rows(case)
    with pymupdf.open() as doc:
        page = doc.new_page(width=400, height=400)
        page.draw_rect(pymupdf.Rect(20, 20, 380, 330), color=(0.6, 0.6, 0.6), width=0.5)
        for index, row in enumerate(rows):
            x, y = 30., 60. + 32 * index
            for text, cls, role in row:
                name = STYLES[cls][role]
                page.insert_text((x, y), text, fontname=name, fontsize=12, color=(0, 0, 0.7))
                x += pymupdf.get_text_length(text, fontname=name, fontsize=12)
        if case in ('repeated-reordered', 'blank-page', 'ja', 'zh-Hans'):
            widget = pymupdf.Widget()
            widget.field_name, widget.field_type = 'answer', pymupdf.PDF_WIDGET_TYPE_TEXT
            widget.rect = pymupdf.Rect(30, 345, 240, 370)
            page.add_widget(widget)
        if case == 'blank-page':
            doc.new_page(width=400, height=400)
        doc.set_metadata({'title': 'Payment form'})
        doc.save(source)
    run_strip(str(source), str(stripped))
    run_extract(str(source), str(work), typography=True)
    segments = work / 'segments.json'
    extraction = json.loads(segments.read_text(encoding='utf-8'))
    # Source paths are not part of extraction identity; keep this fixture portable.
    extraction['source'] = 'original.pdf'
    segments.write_text(json.dumps(extraction, ensure_ascii=False, indent=2), encoding='utf-8')
    lang = case if case in ('ja', 'zh-Hans') else 'es'
    title = {'ja': '記入例', 'zh-Hans': '填写示例'}.get(lang, 'Formulario de pago')
    target_text = {'ja': '日本語の記入例', 'zh-Hans': '简体中文示例'}.get(lang, 'Datos del pago')
    conf = {'format': 'typography-1', 'extraction_id': extraction['typography']['extraction_id'],
            'lang': lang, 'font_sets': {}, 'source_font_resolutions': [], 'allow_scale': [],
            'document_targets': {'Payment form': title}, 'targets': []}
    for segment in extraction['segments']:
        runs = segment['style_runs']
        if case in ('repeated-reordered', 'blank-page'):
            targets = [{'text': 'AHORA ', 'source_runs': [runs[1]['run_id']]},
                       {'text': 'pague', 'source_runs': [runs[0]['run_id']]}]
        else:
            targets = [{'text': 'f' * 110 if case == 'italic-overhang' else target_text,
                        'source_runs': [runs[0]['run_id']]}]
        conf['targets'].append({'occurrence_id': segment['occurrence_id'], 'runs': targets})
        for run in runs:
            cls, role = run['class'], role_name(run['bold'], run['italic'])
            conf['font_sets'].setdefault(cls, {})[role] = f'selected/{cls}-{role}.ttf'
    mapping = work / 'translations.json'
    mapping.write_text(json.dumps(conf, ensure_ascii=False, indent=2), encoding='utf-8')
    prepared = []
    for cls, roles in conf['font_sets'].items():
        family = 'NotoSans' if cls == 'sans' else 'NotoSerif'
        for role, relative in roles.items():
            if lang in ('ja', 'zh-Hans'):
                source_font = fixtures / f'{family}{"JP" if lang == "ja" else "SC"}-VF.ttf'
                options = {'instance': f'wght={700 if role == "bold" else 400}'}
            else:
                source_font = fixtures / f'{family}-{SUFFIX[role]}.ttf'
                options = {}
            if not source_font.is_file():
                raise FileNotFoundError(f'Required genuine fixture font: {source_font}')
            result = run_prepare_font(str(source_font), str(mapping), str(work / relative),
                                      font_class=cls, font_role=role, reference_fonts=str(fixtures), **options)
            prepared.append(result.to_dict())
    authored = load_mapping(mapping)
    built = run_retypeset(str(stripped), str(segments), str(mapping), str(work / 'out.pdf'), original=str(source))
    # Fields need a full face, not the page-text subset: future user input is
    # not confined to the words this fixture translated.
    field_font = fixtures / 'NotoSans-Regular.ttf'
    if lang in ('ja', 'zh-Hans'):
        field_font = work / 'field-font.ttf'
        variable = fixtures / f'NotoSans{"JP" if lang == "ja" else "SC"}-VF.ttf'
        with TTFont(variable) as font:
            count = len(font.getBestCmap())
            instantiateVariableFont(font, {'wght': 400}, inplace=True, updateFontNames=True)
            if 'fvar' in font or len(font.getBestCmap()) != count:
                raise AssertionError('Full field face lost coverage or remains variable')
            font.save(field_font)
    field_result = run_field_fonts(built.output, str(field_font), str(final))
    fill = {'ja': target_text, 'zh-Hans': target_text}.get(lang, 'pague' if case in ('repeated-reordered', 'blank-page') else target_text)
    verdict = run_verify(str(source), str(final), translations=str(mapping), segments=str(segments),
                         typography=True, fill_text=fill, source_words_from=str(segments), reference_fonts=str(fixtures))
    check = next(g for g in verdict.gates if g.name == 'typography')
    qa = run_qa(str(mapping), str(segments))
    review = run_review(str(work))
    if review.errors:
        raise RuntimeError(review.errors)
    with pymupdf.open(source) as original, pymupdf.open(final) as output:
        observations = observe_fonts(output)
        actual = []
        for page in output:
            for span in page.get_texttrace():
                matched = [f for f in observations['fonts'].values()
                           if _unsubset(span['font']) in {_unsubset(n) for n in f['aliases']}]
                actual.append({'page': page.number, 'font': span['font'], 'size': span['size'],
                               'text': ''.join(chr(c[0]) for c in span['chars']),
                               'baselines': sorted({round(c[2][1], 5) for c in span['chars']}),
                               'programs': [{'class': f['class'], 'bold': f['bold'], 'italic': f['italic'],
                                             'sha256': f['sha256']} for f in matched]})
        same_pages = page_geometry(original) == page_geometry(output)
        counts = [original.page_count, output.page_count]
        for label, document in (('source', original), ('final', output)):
            for page in document:
                page.get_pixmap(dpi=150).save(work / f'{label}-{page.number + 1}.png')
    summary = {'case': case, 'source_language': 'en', 'target_language': lang,
               'page_counts': counts, 'same_page_geometry': same_pages, 'typography': check.to_dict(),
               'expected_roles': [{'occurrence_id': t.occurrence_id,
                                   'roles': [f'{r.font_class}/{r.font_role}' for r in t.runs]} for t in authored.targets],
               'actual_drawn': actual, 'selected_font_hashes': {f'{c}/{r}': source_digest(p)
                  for c, roles in authored.font_sets.items() for r, p in roles.items()},
               'codes': {'build': 0, 'field_fonts': 0, 'verify': verdict.exit_code, 'qa': qa.exit_code},
               'fill_text': fill, 'language_semantics': 'Not attested; synthetic authored examples need a qualified reader.'}
    with TTFont(field_font) as font:
        summary['field_font'] = {'sha256': source_digest(field_font), 'cmap_entries': len(font.getBestCmap()),
                                 'coverage': 'Full supplied regular face; not a translation subset.'}
    for name, value in [('summary.json', summary), ('build.json', built.to_dict()), ('fonts.json', prepared),
                        ('field-fonts.json', field_result.to_dict()), ('verify.json', verdict.to_dict()),
                        ('qa.json', {'findings': qa.findings}), ('review-state.json', review.to_dict())]:
        write_json(work / name, value, work, fixtures)
    scale_path = work / 'scale_report.json'
    write_json(scale_path, json.loads(scale_path.read_text(encoding='utf-8')), work, fixtures)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--fonts', required=True, type=Path)
    args = parser.parse_args(argv)
    work, fixtures = args.work.resolve(), args.fonts.resolve()
    if work.exists() and (not work.is_dir() or any(work.iterdir())):
        parser.error('--work must be an empty output directory')
    work.mkdir(parents=True, exist_ok=True)
    summaries = []
    for case in CASES:
        result = build_case(work / case, fixtures, case)
        summaries.append(result)
        print(f'{case}: typography={result["typography"]["status"]}; pages={result["page_counts"]}; '
              f'verify={result["codes"]["verify"]}', flush=True)
    candidate = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[2],
                               capture_output=True, text=True, check=True).stdout.strip()
    summary = {'candidate_base': candidate, 'working_tree_runtime': True,
               'runtime': {'python': platform.python_version(), 'pymupdf': pymupdf.VersionBind,
                           'mupdf': pymupdf.VersionFitz, 'fonttools': fontTools.__version__, 'pikepdf': pikepdf.__version__,
                           'pdf_translate': pdf_translate.__file__, 'version': pdf_translate.__version__},
               'cases': summaries, 'unmeasured': ['Genuine CJK italic and bold-italic positive cells',
                                                'Qualified language/emphasis semantics', 'Other OS/Python/host environments']}
    write_json(work / 'summary.json', summary, work, fixtures)
    return int(any(s['typography']['status'] != 'PASS' or not s['same_page_geometry'] or
                   s['codes']['verify'] != 0 for s in summaries))


if __name__ == '__main__':
    raise SystemExit(main())
