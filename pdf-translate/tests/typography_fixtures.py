"""Synthetic, explicitly font-selected sources for typography regression tests."""
from pathlib import Path
from copy import deepcopy

import pymupdf


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
