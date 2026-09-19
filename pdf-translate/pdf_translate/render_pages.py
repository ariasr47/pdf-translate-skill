#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write per-page PNGs of original and translation for the visual pass.

This is the inspect loop — not comparison.html. compare.py inlines 120 dpi
pages as base64 and is for delivery only.

Usage:
  python3 render_pages.py ORIGINAL.pdf TRANSLATED.pdf renders/ [--dpi 110]
"""
import logging
import os
import sys
import time

import pymupdf


from ._console import console

log = logging.getLogger(__name__)


def render_pages(orig, trans, outdir, dpi=110):
    os.makedirs(outdir, exist_ok=True)
    o, j = pymupdf.open(orig), pymupdf.open(trans)
    n = min(len(o), len(j))
    written = []
    for i in range(n):
        for doc, prefix in ((o, 'orig'), (j, 'out')):
            path = os.path.join(outdir, f'{prefix}_p{i+1}.png')
            doc[i].get_pixmap(dpi=dpi).save(path)
            written.append(path)
    o.close()
    j.close()
    log.info(f'rendered {n} page pair(s) -> {outdir} ({dpi} dpi)')
    return written


def main(argv=None):
    with console():
        return _main(argv)


def _main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    orig, trans, outdir = argv[0], argv[1], argv[2]
    dpi = int(argv[argv.index('--dpi') + 1]) if '--dpi' in argv else 110
    t0 = time.perf_counter()
    render_pages(orig, trans, outdir, dpi=dpi)
    log.info(f'elapsed {time.perf_counter()-t0:.2f}s')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
