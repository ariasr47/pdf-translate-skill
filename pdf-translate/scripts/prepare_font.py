#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI entry for prepare_font. Implementation lives in pdf_translate.prepare_font."""
import importlib
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_root = str(_ROOT)
if _root not in sys.path:
    sys.path.insert(0, _root)

if __name__ == '__main__':
    raise SystemExit(importlib.import_module('pdf_translate.prepare_font').main())

sys.modules[__name__] = importlib.import_module('pdf_translate.prepare_font')