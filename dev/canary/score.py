#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Machine-checkable half of the canary rubric.

Axes 1, 2, 4 and 5 are judgements a person makes by reading the run's
delivery. Axis 3 — did the write/find/say identifiers survive — is not a
judgement at all, and neither is "does the thing they produced actually
pass the gates". This script answers those, so the subjective half is the
only part anyone has to argue about.

  python3 dev/canary/score.py ORIGINAL.pdf RUNDIR [RUNDIR ...]

For each run directory it finds the candidate output PDF (the newest one
that is not the original), then reports:

  gates        verify.py exit code and which gates failed
  identifiers  each write/find/say span from the original, present or not
  mapping      qa_check.py findings, if a translations.json is there
  artifacts    what the run left behind
"""
import glob
import io
import json
import os
import sys
from contextlib import redirect_stdout

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(REPO, 'pdf-translate', 'scripts')
sys.path.insert(0, SCRIPTS)

import pymupdf  # noqa: E402
import extract_segments  # noqa: E402
import qa_check  # noqa: E402
import verify  # noqa: E402


def candidate_output(rundir, original):
    """The PDF this run produced: newest non-original, non-stripped file."""
    orig_size = os.path.getsize(original)
    best = None
    for path in glob.glob(os.path.join(rundir, '**', '*.pdf'), recursive=True):
        name = os.path.basename(path).lower()
        if 'stripped' in name or name == os.path.basename(original).lower():
            continue
        if os.path.getsize(path) == orig_size:
            continue
        try:
            doc = pymupdf.open(path)
            pages = len(doc)
            doc.close()
        except Exception:
            continue
        if pages < 1:
            continue
        if best is None or os.path.getmtime(path) > os.path.getmtime(best):
            best = path
    return best


def identifier_report(original, out):
    """Every write/find/say span from the original, and whether it survived."""
    o = pymupdf.open(original)
    j = pymupdf.open(out)
    try:
        spans = []
        for page in o:
            for kind, snippet in extract_segments.write_find_say_hits(
                    page.get_text() or ''):
                if snippet.strip() and snippet not in [s for _, s in spans]:
                    spans.append((kind, snippet.strip()))
        hay = verify.normalize_ws_nbsp(
            '\n'.join(verify.page_search_text(p) for p in j))
        return [(kind, snippet, verify.normalize_ws_nbsp(snippet) in hay)
                for kind, snippet in spans]
    finally:
        o.close()
        j.close()


def score_run(original, rundir):
    name = os.path.basename(rundir.rstrip('/'))
    print(f'\n===== {name} =====')
    out = candidate_output(rundir, original)
    if not out:
        print('  OUTPUT: none — the run produced no translated PDF')
        return {'run': name, 'output': None}

    print(f'  output: {os.path.relpath(out, rundir)} '
          f'({os.path.getsize(out) // 1024} KB)')
    o, j = pymupdf.open(original), pymupdf.open(out)
    print(f'  pages: {len(o)} original / {len(j)} output')
    o.close()
    j.close()

    tr = None
    for cand in glob.glob(os.path.join(rundir, '**', 'translations.json'),
                          recursive=True):
        tr = cand
        break
    segs = os.path.join(os.path.dirname(tr), 'segments.json') if tr else None

    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            rc = verify.verify(original, out, translations=tr,
                               segments=segs if segs and os.path.isfile(segs) else None)
        except Exception as exc:
            rc = -1
            print(f'verify raised: {exc}')
    log = buf.getvalue()
    failed = [ln.strip() for ln in log.splitlines() if ln.startswith('FAIL')]
    print(f'  verify: exit {rc}, {len(failed)} gate(s) failing'
          + (' (no --translations: mapping gates did not run)' if not tr else ''))
    for ln in failed[:12]:
        print(f'     {ln[:110]}')

    ids = identifier_report(original, out)
    kept = sum(1 for _, _, ok in ids)
    print(f'  identifiers: {kept}/{len(ids)} survived')
    for kind, snippet, ok in ids:
        print(f'     [{"kept" if ok else "LOST"}] {kind}: {snippet[:60]}')

    findings = []
    if tr:
        try:
            findings = qa_check.qa_check(tr, segs if segs and os.path.isfile(segs) else None)
        except Exception as exc:
            print(f'  qa_check raised: {exc}')
        errs = [f for f in findings if f['severity'] == 'error']
        print(f'  qa_check: {len(errs)} error(s), '
              f'{len(findings) - len(errs)} warning(s)')
        for f in findings[:8]:
            print(f'     {f["severity"].upper()} {f["kind"]}: '
                  f'{f["core"][:40]!r} {f["detail"][:70]}')
    else:
        print('  qa_check: no translations.json found in the run')

    artifacts = sorted(
        os.path.relpath(p, rundir)
        for p in glob.glob(os.path.join(rundir, '**', '*'), recursive=True)
        if os.path.isfile(p))
    print(f'  artifacts ({len(artifacts)}): '
          f'{", ".join(a for a in artifacts[:14])}')
    return {'run': name, 'output': os.path.relpath(out, rundir),
            'verify_rc': rc, 'gates_failed': failed,
            'identifiers': [{'kind': k, 'text': s, 'kept': ok}
                            for k, s, ok in ids],
            'qa_findings': findings, 'artifacts': artifacts}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2
    original, rundirs = argv[0], argv[1:]
    results = [score_run(original, d) for d in rundirs]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'last-score.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'original': original, 'runs': results}, f,
                  ensure_ascii=False, indent=1, default=str)
    print(f'\nwrote {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
