# -*- coding: utf-8 -*-
"""The document's /Lang, written and read exactly as the tag is spelled.

PyMuPDF keeps only part of a language tag in both directions:
`set_language('es-US')` stores `es`, `zh-Hant-TW` stores `zh`, and
`doc.language` reads a whole stored tag back as its primary subtag
(`zh-Hant-TW` as `zh`, which han-forms takes for Simplified). Screen
readers, hyphenation and the han-forms gate read the region and script,
so retypeset writes the catalog entry itself and verify reads it the same
way.
"""
import pymupdf


def write_language(doc, tag):
    """Set the catalog's /Lang to `tag` as given. Returns what was stored."""
    doc.xref_set_key(doc.pdf_catalog(), 'Lang', pymupdf.get_pdf_str(tag))
    return declared_language(doc)


def declared_language(doc):
    """The catalog's /Lang as stored, stripped; '' when there is none.

    A /Lang that is not a direct string (an indirect reference, which
    nothing here writes) falls back to PyMuPDF's own reading.
    """
    try:
        kind, value = doc.xref_get_key(doc.pdf_catalog(), 'Lang')
    except Exception:
        return ''
    if kind == 'string':
        return value.strip()
    if kind == 'null':
        return ''
    try:
        return (doc.language or '').strip()
    except Exception:
        return ''
