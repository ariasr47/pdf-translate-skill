"""R-50 evidence (docs/reviews/2026-09-25-r50-subset-before-instancing.md). Compare two deliver.py output trees: page content, text, renders, glyph positions.
usage: dev/probes/r50_deliver_compare.py OUT_A OUT_B"""
import hashlib
import sys
from pathlib import Path

import pymupdf

a_root, b_root = Path(sys.argv[1]), Path(sys.argv[2])
all_same = True
for job in sorted(p.name for p in a_root.iterdir() if p.is_dir()):
    a, b = a_root / job / 'out.pdf', b_root / job / 'out.pdf'
    if not a.exists() or not b.exists():
        print(job, 'missing output', a.exists(), b.exists())
        all_same = False
        continue
    da, db = pymupdf.open(a), pymupdf.open(b)
    checks = {}
    checks['console'] = (a_root / job / 'console.txt').read_text() == (b_root / job / 'console.txt').read_text()
    checks['pages'] = da.page_count == db.page_count
    checks['content'] = all(pa.read_contents() == pb.read_contents() for pa, pb in zip(da, db))
    checks['text'] = all(pa.get_text('rawdict') == pb.get_text('rawdict') for pa, pb in zip(da, db))
    checks['render'] = all(
        hashlib.sha256(pa.get_pixmap(dpi=200).samples).digest() == hashlib.sha256(pb.get_pixmap(dpi=200).samples).digest()
        for pa, pb in zip(da, db))
    texttrace_a = [[(s['font'], tuple(c[0] for c in s['chars']), tuple(tuple(round(v, 4) for v in c[2]) for c in s['chars'])) for s in p.get_texttrace()] for p in da]
    texttrace_b = [[(s['font'], tuple(c[0] for c in s['chars']), tuple(tuple(round(v, 4) for v in c[2]) for c in s['chars'])) for s in p.get_texttrace()] for p in db]
    checks['glyph positions'] = texttrace_a == texttrace_b
    ok = all(checks.values())
    all_same &= ok
    print(f'{job}: {"identical" if ok else "DIFFERENT"}', {k: v for k, v in checks.items() if not v} or '')
print('all deliveries identical:', all_same)
sys.exit(0 if all_same else 1)
