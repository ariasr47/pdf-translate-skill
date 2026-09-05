#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Machine-checkable half of the canary rubric.

Axes 1, 2, 4 and 5 are judgements a person makes by reading the run's
delivery. Axis 3 — did the write/find/say identifiers survive — is not a
judgement at all, and neither is "does the thing they produced actually
pass the gates". This script answers those, so the subjective half is the
only part anyone has to argue about.

  python3 dev/canary/score.py ORIGINAL.pdf RUNDIR [RUNDIR ...]
  python3 dev/canary/score.py ORIGINAL.pdf RUNDIR --output final.pdf

Select the output with --output (one run only), or delivery.json in each
run. Without either, only a single non-original PDF at the run root is
accepted; multiple candidates are an error, and subdirectories are never
searched for diagnostic PDFs. Then report:

  gates        verify.py exit code and which gates failed
  identifiers  each write/find/say span from the original, present or not
  mapping      qa_check.py findings, if a translations.json is there
  artifacts    what the run left behind
"""
import argparse
import glob
import hashlib
import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(REPO, 'pdf-translate', 'scripts')
sys.path.insert(0, SCRIPTS)

import pymupdf  # noqa: E402
import extract_segments  # noqa: E402
import qa_check  # noqa: E402
import verify  # noqa: E402


def run_file(rundir, value, label):
    """Resolve a declared file within its run, never against the caller cwd."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be a non-empty path string')
    root = Path(rundir).resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'{label} must be inside the run directory: {value}')
    if not path.is_file():
        raise ValueError(f'{label} does not exist: {value}')
    return str(path)


def load_delivery(rundir):
    """Read only supported, auditable verification decisions."""
    manifest = Path(rundir) / 'delivery.json'
    if not manifest.is_file():
        return {}
    conf = json.loads(manifest.read_text(encoding='utf-8-sig'))
    keys = {'output', 'translations', 'segments', 'allow', 'fill_text'}
    if not isinstance(conf, dict) or set(conf) - keys:
        raise ValueError('delivery.json must be an object with only '
                         'output, translations, segments, allow and fill_text')
    if not isinstance(conf.get('output'), str) or not conf['output'].strip():
        raise ValueError('delivery.json output must be a non-empty path string')
    for key in ('translations', 'segments'):
        if key in conf:
            run_file(rundir, conf.get(key), f'delivery.json {key}')
    allow = conf.get('allow', [])
    if not isinstance(allow, list) or any(
            not isinstance(a, str) or not a.strip() for a in allow):
        raise ValueError('delivery.json allow must be a list of non-empty phrases')
    if 'fill_text' in conf and (not isinstance(conf['fill_text'], str)
                                or not conf['fill_text'].strip()):
        raise ValueError('delivery.json fill_text must be a non-empty string')
    return conf


def candidate_output(rundir, original, output=None):
    """Use an explicit file, or require exactly one root-level candidate."""
    rundir = str(Path(rundir).resolve())
    if output is not None:
        path = run_file(rundir, output, 'output')
        try:
            with pymupdf.open(path) as doc:
                if not doc.is_pdf or len(doc) < 1:
                    raise ValueError('expected a non-empty PDF')
        except Exception as exc:
            raise ValueError(f'invalid output PDF {output}: {exc}') from exc
        return path
    original_hash = hashlib.sha256(Path(original).read_bytes()).digest()
    candidates = []
    for item in sorted(Path(rundir).iterdir()):
        if not item.is_file() or item.suffix.lower() != '.pdf':
            continue
        path = str(item)
        name = item.name.lower()
        if 'stripped' in name:
            continue
        if hashlib.sha256(item.read_bytes()).digest() == original_hash:
            continue
        try:
            with pymupdf.open(path) as doc:
                pages = len(doc) if doc.is_pdf else 0
        except Exception:
            continue
        if pages < 1:
            continue
        candidates.append(run_file(rundir, str(item.resolve()), 'output'))
    if len(candidates) > 1:
        names = ', '.join(os.path.relpath(p, rundir) for p in candidates)
        raise ValueError(f'ambiguous output PDFs: {names}; '
                         'use --output or delivery.json')
    return candidates[0] if candidates else None


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


def score_run(original, rundir, output=None, allow=None, fill_text=None):
    # Match run_file's canonical paths, including Windows 8.3 aliases, before
    # calculating relative artifact names for the report.
    rundir = str(Path(rundir).resolve())
    name = Path(rundir).name
    print(f'\n===== {name} =====')
    try:
        conf = load_delivery(rundir)
        out = candidate_output(rundir, original, output or conf.get('output'))
        tr = None
        if 'translations' in conf:
            tr = run_file(rundir, conf['translations'], 'translations')
        else:
            # Deterministic defaults; do not pick an arbitrary nested mapping.
            for directory in (Path(out).parent if out else Path(rundir), Path(rundir)):
                cand = directory / 'translations.json'
                if cand.is_file():
                    tr = run_file(rundir, str(cand.resolve()), 'translations')
                    break
        segs = None
        if 'segments' in conf:
            segs = run_file(rundir, conf['segments'], 'segments')
        elif tr and Path(tr).with_name('segments.json').is_file():
            segs = run_file(rundir, str(Path(tr).with_name('segments.json')), 'segments')
    except (OSError, ValueError) as exc:
        print(f'  OUTPUT ERROR: {exc}')
        return {'run': name, 'output': None, 'error': str(exc)}
    if not out:
        print('  OUTPUT: none — no root-level translated PDF; '
              'use --output or delivery.json for a nested deliverable')
        return {'run': name, 'output': None}

    print(f'  output: {os.path.relpath(out, rundir)} '
          f'({os.path.getsize(out) // 1024} KB)')
    o, j = pymupdf.open(original), pymupdf.open(out)
    print(f'  pages: {len(o)} original / {len(j)} output')
    o.close()
    j.close()

    settings = {
        'translations': tr, 'segments': segs, 'source_words_from': segs,
        'allow': list(dict.fromkeys(conf.get('allow', []) + list(allow or []))),
        'fill_text': fill_text or conf.get('fill_text', 'Test value 123'),
    }
    print('  verification settings: ' + json.dumps(settings, ensure_ascii=False))
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            rc = verify.verify(original, out, **settings)
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
            findings = qa_check.qa_check(tr, segs)
        except Exception as exc:
            print(f'  qa_check raised: {exc}')
            findings = [{'severity': 'error', 'kind': 'qa-exception',
                         'core': '', 'detail': str(exc)}]
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
            'verification': settings, 'verify_log': log,
            'identifiers': [{'kind': k, 'text': s, 'kept': ok}
                            for k, s, ok in ids],
            'qa_findings': findings, 'artifacts': artifacts}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('original')
    parser.add_argument('rundirs', nargs='+')
    parser.add_argument('--output', help='PDF relative to the run directory; one run only')
    parser.add_argument('--allow', action='append', default=[],
                        help='deliberate source phrase to preserve; repeat for each phrase')
    parser.add_argument('--fill-text', help='target-language value for the fill round-trip')
    parser.add_argument('--report', default=str(Path(__file__).with_name('last-score.json')),
                        help='JSON report path, relative to the caller (default: %(default)s)')
    args = parser.parse_args(argv)
    if args.output and len(args.rundirs) != 1:
        parser.error('--output requires exactly one run directory; use per-run delivery.json files')
    if not Path(args.original).is_file():
        parser.error(f'original does not exist: {args.original}')
    # Check before selection: even malformed manifests and ambiguous outputs
    # must leave every delivery artifact intact. Reports belong outside runs.
    report = Path(args.report).resolve()
    if report == Path(args.original).resolve() or any(
            report.is_relative_to(Path(directory).resolve())
            or Path(os.path.abspath(args.report)).is_relative_to(Path(os.path.abspath(directory)))
            for directory in args.rundirs):
        parser.error('--report must be outside every run directory and must not overwrite the original')
    results = [score_run(args.original, d, args.output, args.allow, args.fill_text)
               for d in args.rundirs]
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump({'original': args.original, 'runs': results}, f,
                  ensure_ascii=False, indent=1, default=str)
    print(f'\nwrote {args.report}')
    if any('error' in r for r in results):
        return 2
    return int(any(not r.get('output') or r['verify_rc'] != 0
                   or any(not item['kept'] for item in r['identifiers'])
                   or any(f['severity'] == 'error' for f in r['qa_findings'])
                   for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
