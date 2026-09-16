# -*- coding: utf-8 -*-
"""Importable stages for pdf-translate.

The skill's documented CLI paths remain ``scripts/*.py``. Those files are
thin wrappers around this package so ``python scripts/pipeline.py`` is
unchanged. A consumer imports from here:

    from pdf_translate import strip_text, extract_segments, retypeset
    from pdf_translate import prepare_font, field_fonts
    from pdf_translate import run_verify, run_qa
"""

__version__ = '51'

from .strip_text import WidgetTextError, strip_text
from .extract_segments import extract_segments
from .retypeset import retypeset
from .prepare_font import prepare_font
from .field_fonts import field_fonts
from .render_pages import render_pages
from .compare import compare
from .bilingual import interleave
from .verify import GATE_NAMES, Finding, GateResult, VerifyVerdict, run_verify, verify
from .qa_check import QAVerdict, qa_check, run_qa
from .shaping_probe import ProbeResult, probe_font

__all__ = (
    'GATE_NAMES',
    'GateResult',
    'Finding',
    'ProbeResult',
    'QAVerdict',
    'VerifyVerdict',
    'WidgetTextError',
    'compare',
    'extract_segments',
    'field_fonts',
    'interleave',
    'prepare_font',
    'probe_font',
    'qa_check',
    'render_pages',
    'retypeset',
    'run_qa',
    'run_verify',
    'strip_text',
    'verify',
)
