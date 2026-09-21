"""Synthetic, explicitly font-selected sources for typography regression tests."""
from pathlib import Path

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
