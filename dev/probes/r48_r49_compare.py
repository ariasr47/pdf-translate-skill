"""R-48/R-49: compare two r48_r49_bench.py output trees, every output byte for
byte, then the CPU time of each stage.

usage: python dev/probes/r48_r49_compare.py OUT_BASE OUT_AFTER TREE_BASE TREE_AFTER
Paths inside outputs are normalised (each tree's prefix -> TREE, each out dir
-> OUT) and a PDF's trailer /ID is masked; nothing else is.
"""
import json
import re
import sys
from pathlib import Path

base, after, tree_b, tree_a = (Path(p) for p in sys.argv[1:5])
ID = re.compile(rb'/ID\s*\[\s*<[0-9A-Fa-f]*>\s*<[0-9A-Fa-f]*>\s*\]')


def norm(path, data, tree, out):
    for old, new in ((str(tree), 'TREE'), (str(out), 'OUT')):
        data = data.replace(old.encode(), new.encode())
    if path.suffix == '.pdf':
        data = ID.sub(b'/ID[<masked>]', data)
    return data


same, differ, only = [], [], []
for f in sorted(p for p in base.rglob('*') if p.is_file()):
    rel = f.relative_to(base)
    if rel.name == 'rows.json':
        continue
    g = after / rel
    if not g.exists():
        only.append(f'base only: {rel}')
        continue
    a = norm(f, f.read_bytes(), tree_b, base)
    b = norm(g, g.read_bytes(), tree_a, after)
    (same if a == b else differ).append(str(rel))
for g in sorted(p for p in after.rglob('*') if p.is_file()):
    rel = g.relative_to(after)
    if not (base / rel).exists() and rel.name != 'oracle-1-5.json':
        only.append(f'after only: {rel}')

# The scoped oracle must equal the whole-document oracle cut to pages 1-5.
scoped = []
for g in sorted(after.rglob('oracle-1-5.json')):
    whole = json.loads((base / g.relative_to(after)).with_name('oracle-all.json').read_text())
    got = json.loads(g.read_text())
    scoped.append((g.parent.name, got == [x for x in whole if x[0] < 5], got))

print(f'files compared: {len(same) + len(differ)}; identical {len(same)}; different {len(differ)}; one side only {len(only)}')
for d in differ:
    print('  DIFFERENT', d)
for o in only:
    print('  ', o)
print(f'scoped oracle (pages 1-5) equals the whole-document verdict cut to them: '
      f'{sum(ok for _, ok, _ in scoped)}/{len(scoped)}', [n for n, ok, _ in scoped if not ok])

rb = {r['name']: r for r in json.loads((base / 'rows.json').read_text())}
ra = {r['name']: r for r in json.loads((after / 'rows.json').read_text())}
stages = ['extract_all', 'extract_1_5', 'oracle_all', 'strip', 'strip_wt', 'verify_self']
print('\nCPU seconds, before -> after (wall in brackets for the totals)')
print('| input | pages | ' + ' | '.join(stages) + ' |')
totals = {s: [0.0, 0.0] for s in stages}
for name in rb:
    cells = []
    for s in stages:
        x, y = rb[name].get(s), ra.get(name, {}).get(s)
        if isinstance(x, list) and isinstance(y, list):
            cells.append(f'{x[1]:.2f} → {y[1]:.2f}')
            totals[s][0] += x[1]
            totals[s][1] += y[1]
        elif x is None and y is None:
            cells.append('')
        else:
            cells.append(f'{x} / {y}'[:60])
    print(f'| {name} | {rb[name]["pages"]} | ' + ' | '.join(cells) + ' |')
print('| **total** | | ' + ' | '.join(f'{b:.1f} → {a:.1f}' for b, a in totals.values()) + ' |')
