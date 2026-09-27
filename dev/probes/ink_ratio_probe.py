"""Compare fresh rasters with verify's ink gate, including fill-roundtrip effects.

Run with the checkout under test first on PYTHONPATH (also works on v77):
    python dev/probes/ink_ratio_probe.py ORIGINAL.pdf OUT.pdf FINAL.pdf REPORT_DIR

Inputs are read-only. REPORT_DIR receives JSON and PNGs. Other verify gates
may fail on identity/control documents; only ink inconsistency fails this probe.
Use born-digital, extractable inputs (blank pages are fine); scan refusals
are outside this investigation and can omit the ink gate entirely.
This is a bounded investigation tool, not a new library acceptance gate.
"""
import argparse
import hashlib
import importlib
import json
import platform
from pathlib import Path
from unittest.mock import patch

import pikepdf
import pymupdf

verify = importlib.import_module('pdf_translate.verify')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raster(page, dpi=72, annots=True):
    pix = page.get_pixmap(dpi=dpi, annots=annots)
    samples = pix.samples
    return pix, {
        'width': pix.width, 'height': pix.height, 'channels': pix.n,
        'samples_sha256': sha(samples),
        # Independent byte-loop oracle for verify's first-channel < 100 rule.
        'dark_pixels': sum(value < 100 for value in samples[::pix.n]),
    }


def inspect(path, label, destination):
    info = {'sha256': sha(path.read_bytes()), 'pages': [], 'read_orders': {}}
    images = {}
    with pikepdf.open(path) as pdf:
        form = pdf.Root.get('/AcroForm', {})
        info['need_appearances'] = bool(form.get('/NeedAppearances', False))
    with pymupdf.open(path) as doc:
        info['widgets'] = sum(len(list(page.widgets())) for page in doc)
    for dpi, annots in ((72, True), (110, True), (120, True), (72, False)):
        key = f'{dpi}-annots-{annots}'
        with pymupdf.open(path) as doc:
            for index, page in enumerate(doc):
                pix, measured = raster(page, dpi, annots)
                images[index, key] = (pix.samples, measured)
                repeated = raster(page, dpi, annots)[1]
                measured = dict(measured, page=index + 1, mode=key,
                                repeated_identical=measured == repeated)
                info['pages'].append(measured)
                if dpi in (72, 110) and annots:
                    pix.save(str(destination / f'{label}-p{index + 1}-{dpi}.png'))
    for order in ('text', 'widgets', 'text-then-widgets', 'widgets-then-text'):
        with pymupdf.open(path) as doc:
            for operation in order.split('-then-'):
                for page in doc:
                    if operation == 'text':
                        page.get_text()
                    else:
                        list(page.widgets())
            info['read_orders'][order] = [raster(page)[1] for page in doc]
    return info, images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('final', type=Path)
    parser.add_argument('report_dir', type=Path)
    args = parser.parse_args()
    destination = args.report_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    paths = {name: getattr(args, name).resolve() for name in ('original', 'out', 'final')}
    report = {
        'runtime': {'python': platform.python_version(), 'platform': platform.platform(),
                    'pymupdf': pymupdf.VersionBind, 'mupdf': pymupdf.VersionFitz,
                    'pikepdf': pikepdf.__version__, 'verify': verify.__file__},
        'inputs': {}, 'out_vs_final': [], 'verify_runs': [], 'inconsistencies': [],
    }
    images = {}
    for label, path in paths.items():
        report['inputs'][label], images[label] = inspect(path, label, destination)
        report['inputs'][label]['path'] = str(path)
    for key in sorted(set(images['out']) | set(images['final'])):
        if key not in images['out'] or key not in images['final']:
            report['out_vs_final'].append({'page': key[0] + 1, 'mode': key[1],
                                           'same_size': False, 'missing_page': True})
            continue
        a, am = images['out'][key]
        b, bm = images['final'][key]
        same_size = all(am[k] == bm[k] for k in ('width', 'height', 'channels'))
        n = am['channels']
        changed = (sum(a[k:k+n] != b[k:k+n] for k in range(0, len(a), n))
                   if same_size else None)
        report['out_vs_final'].append({
            'page': key[0] + 1, 'mode': key[1], 'same_size': same_size,
            'samples_identical': same_size and a == b, 'changed_pixels': changed,
            'out_dark': am['dark_pixels'], 'final_dark': bm['dark_pixels'],
        })
    original_ink = verify.ink
    # Reverse the order for a second sample; return to the first sample last
    # to expose any process-wide state left behind by the other fills.
    for fill, order in (('Test value 123', ('out', 'final')),
                        ('José Muñoz García', ('final', 'out')),
                        ('WWWW WWWW WWWW WWWW 123456789', ('out', 'final')),
                        ('Test value 123', ('final', 'out'))):
        for label in order:
            calls = []

            def measured_ink(page):
                count = original_ink(page)
                calls.append({'path': str(Path(page.parent.name).resolve()),
                              'page': page.number + 1, 'dark_pixels': count})
                return count

            with patch.object(verify, 'ink', measured_ink):
                verdict = verify.run_verify(str(paths['original']), str(paths[label]),
                                            fill_text=fill)
            gate = next(g for g in verdict.gates if g.name == 'ink-ratio')
            findings = [f.to_dict() for f in gate.findings]
            expected = []
            for index, key in sorted(images[label]):
                if key != '72-annots-True' or (index, key) not in images['original']:
                    continue
                source = images['original'][index, key][1]['dark_pixels']
                target = images[label][index, key][1]['dark_pixels']
                if source < 20:
                    text = f'negligible ink: {source} px'
                else:
                    ratio = target / source
                    status = 'PASS' if 0.4 <= ratio <= 3.0 else 'FAIL'
                    text = f'{status} ink ratio {ratio:.2f}'
                expected.append({'page': index + 1, 'where': 'page', 'text': text})
            matches = findings == expected
            by_path = {str(path): name for name, path in paths.items()}
            counts_match = all(
                call['dark_pixels'] == images[by_path[call['path']]][
                    call['page'] - 1, '72-annots-True'][1]['dark_pixels']
                for call in calls)
            entry = {'target': label, 'fill_text': fill, 'exit_code': verdict.exit_code,
                     'fill_roundtrip': next(g.status for g in verdict.gates
                                            if g.name == 'fill-roundtrip'),
                     'ink_findings': findings, 'expected_from_fresh_rasters': expected,
                     'matches_fresh_rasters': matches, 'ink_calls': calls,
                     'ink_calls_match_fresh_counts': counts_match}
            report['verify_runs'].append(entry)
            if not matches:
                report['inconsistencies'].append(f'{label}: ink gate differs from fresh raster')
            if not counts_match:
                report['inconsistencies'].append(f'{label}: raw ink count differs from fresh raster')
    for label, path in paths.items():
        info = report['inputs'][label]
        info['file_unchanged'] = info['sha256'] == sha(path.read_bytes())
        fresh = [images[label][i, '72-annots-True'][1]
                 for i in range(len(info['pages']) // 4)]
        info['all_read_orders_identical'] = all(
            rows == fresh for rows in info['read_orders'].values())
        info['all_repeat_rasters_identical'] = all(
            row['repeated_identical'] for row in info['pages'])
        for field in ('file_unchanged', 'all_read_orders_identical', 'all_repeat_rasters_identical'):
            if not info[field]:
                report['inconsistencies'].append(f'{label}: {field} is false')
    output = destination / 'report.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(output), 'verify_runs': len(report['verify_runs']),
                      'inconsistencies': report['inconsistencies'],
                      'out_vs_final_72dpi': [r for r in report['out_vs_final']
                                             if r['mode'] == '72-annots-True']},
                     ensure_ascii=False))
    return bool(report['inconsistencies'])


if __name__ == '__main__':
    raise SystemExit(main())
