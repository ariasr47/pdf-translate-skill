"""Synthetic, explicitly font-selected sources for typography regression tests."""
from pathlib import Path
from copy import deepcopy
import json

import pymupdf

from pdf_translate import run_extract, run_strip


def make_source(path):
    path = Path(path)
    with pymupdf.open() as doc:
        page = doc.new_page(width=400, height=240)
        for y, prefix, tail in [(60, 'helv', 'hebo'), (120, 'tiro', 'tibi')]:
            page.insert_text((30, y), 'Pay ', fontname=prefix, fontsize=12)
            x = 30 + pymupdf.get_text_length('Pay ', fontname=prefix, fontsize=12)
            page.insert_text((x, y), 'NOW', fontname=tail, fontsize=12)
        doc.save(path)
    return path


def raw_spans(path):
    with pymupdf.open(path) as doc:
        return [s for page in doc for block in page.get_text('dict')['blocks']
                if block['type'] == 0 for line in block['lines']
                for s in line['spans']]


def make_mapping(extraction, font_sets=None):
    document = extraction.get('document') or {}
    metadata = [document.get('title', '')] + list(document.get('outline') or [])
    if font_sets is None:
        font_sets = {cls: {role: f'fonts/{cls}-{role}.ttf'
                          for role in ('regular', 'bold', 'italic', 'bold_italic')}
                     for cls in ('serif', 'sans')}
    return {
        'format': 'typography-1',
        'extraction_id': extraction['typography']['extraction_id'],
        'lang': 'en', 'font_sets': deepcopy(font_sets),
        'source_font_resolutions': [], 'allow_scale': [],
        'document_targets': {text: text for text in metadata if text},
        'targets': [
            {'occurrence_id': seg['occurrence_id'],
             'runs': [{'text': run['text'], 'source_runs': [run['run_id']]}
                      for run in seg['style_runs']]}
            for seg in extraction['segments']
        ],
    }


def latin_font_sets():
    suffixes = {'regular': 'Regular', 'bold': 'Bold', 'italic': 'Italic', 'bold_italic': 'BoldItalic'}
    fonts = {cls: {role: str(Path(__file__).parent / 'fonts' / f'{family}-{suffix}.ttf')
                   for role, suffix in suffixes.items()}
             for cls, family in [('sans', 'NotoSans'), ('serif', 'NotoSerif')]}
    for roles in fonts.values():
        for path in roles.values():
            if not Path(path).is_file():
                raise AssertionError(f'Required typography fixture missing: {path}')
    return fonts


def make_job(work, font_sets=None):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    source = make_source(work / 'original.pdf')
    stripped = work / 'stripped.pdf'
    run_strip(str(source), str(stripped))
    extracted = run_extract(str(source), str(work), typography=True)
    segments = Path(extracted.segments_path)
    data = json.loads(segments.read_text(encoding='utf-8'))
    mapping = work / 'translations.json'
    mapping.write_text(json.dumps(make_mapping(data, font_sets or latin_font_sets()), ensure_ascii=False),
                       encoding='utf-8')
    return {'original': source, 'stripped': stripped, 'segments': segments,
            'mapping': mapping, 'output': work / 'out.pdf'}
