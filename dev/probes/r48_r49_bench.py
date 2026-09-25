"""R-48/R-49: time each stage and save every output, for one tree.

usage: python dev/probes/r48_r49_bench.py TREE OUTDIR [--only NAME,...]

TREE is a pdf-translate package root (the directory holding pdf_translate/),
for example a `git archive` of the commit before and of the commit after.
Run once per tree, each in a fresh process, then compare the two OUTDIRs with
r48_r49_compare.py. Inputs are dev/wild/files/*.pdf (fetched, not committed:
dev/wild/SOURCES.md), TREE/corpus/*.pdf and a constructed 40-page job; add
more with R48_EXTRA=path.pdf[:path.pdf]. For FL-150, R48_JOB_WIDGET_TEXT
names its job's widget_text.json (dev/jobs/fl150-ja-2026-09-17).
Evidence: docs/reviews/2026-09-25-r48-r49-pixel-loops.md.
"""
import inspect
import io
import json
import os
import shutil
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
ONLY = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
sys.path.insert(0, str(TREE))

import pymupdf  # noqa: E402
import pdf_translate  # noqa: E402
import importlib  # noqa: E402
extract_segments = importlib.import_module('pdf_translate.extract_segments')
strip_text = importlib.import_module('pdf_translate.strip_text')
prepare_font = importlib.import_module('pdf_translate.prepare_font')
from pdf_translate.verify import run_verify  # noqa: E402

assert Path(pdf_translate.__file__).resolve().is_relative_to(TREE), pdf_translate.__file__
REPO = Path(__file__).resolve().parents[2]
WILD = REPO / 'dev' / 'wild' / 'files'
CORPUS = TREE / 'corpus'
SYNTH = OUT.parent / 'synth40.pdf'


def synth40(path):
    if path.exists():
        return path
    doc = pymupdf.open()
    for p in range(40):
        page = doc.new_page()
        for line in range(40):
            page.insert_text((50, 60 + 17 * line),
                             f'Page {p + 1} line {line + 1}: the applicant must file this form today.',
                             fontsize=10)
    doc.save(path)
    return path


def timed(fn, *a, **k):
    w0, c0 = time.perf_counter(), time.process_time()
    with redirect_stdout(io.StringIO()):
        value = fn(*a, **k)
    return value, round(time.perf_counter() - w0, 3), round(time.process_time() - c0, 3)


def fill_targets(node):
    """Every null target in a widget_text scaffold becomes a marked string."""
    if isinstance(node, dict):
        if 'target' in node and node['target'] is None:
            node['target'] = 'JA ' + str(node.get('source', ''))[:40]
        for v in node.values():
            fill_targets(v)
    elif isinstance(node, list):
        for v in node:
            fill_targets(v)
    return node


def verdict_dict(v):
    d = v.to_dict()
    for key in ('version', 'original', 'output'):
        d.pop(key, None)
    return d


def main():
    inputs = sorted(WILD.glob('*.pdf')) + sorted(CORPUS.glob('*.pdf')) + [synth40(SYNTH)]
    inputs += [Path(x) for x in os.environ.get('R48_EXTRA', '').split(os.pathsep) if x]
    has_pages = 'pages' in inspect.signature(strip_text.invisible_text_pages).parameters
    rows = []
    for src in inputs:
        name = src.stem
        if ONLY and name not in ONLY:
            continue
        work = OUT / name
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        with pymupdf.open(src) as d:
            npages = d.page_count
            widgets = sum(1 for p in d for _ in p.widgets())
        row = {'name': name, 'pages': npages}
        # extract, whole document
        try:
            _, w, c = timed(extract_segments.extract_segments, str(src), outdir=str(work / 'extract-all'))
            row['extract_all'] = [w, c]
        except Exception as exc:
            row['extract_all'] = f'{type(exc).__name__}: {exc}'[:200]
        if npages >= 10:
            try:
                _, w, c = timed(extract_segments.extract_segments, str(src),
                                outdir=str(work / 'extract-1-5'), pages='1-5')
                row['extract_1_5'] = [w, c]
            except Exception as exc:
                row['extract_1_5'] = f'{type(exc).__name__}: {exc}'[:200]
        # the oracle alone
        found, w, c = timed(strip_text.invisible_text_pages, str(src))
        row['oracle_all'] = [w, c]
        (work / 'oracle-all.json').write_text(json.dumps(found))
        if has_pages and npages >= 10:
            found5, w, c = timed(strip_text.invisible_text_pages, str(src), pages=set(range(5)))
            row['oracle_1_5'] = [w, c]
            (work / 'oracle-1-5.json').write_text(json.dumps(found5))
        # strip, plain and with a filled widget_text mapping
        try:
            report, w, c = timed(strip_text.strip_text, str(src), str(work / 'stripped.pdf'))
            row['strip'] = [w, c]
            (work / 'strip-report.json').write_text(json.dumps(report, sort_keys=True, default=str))
        except Exception as exc:
            row['strip'] = f'{type(exc).__name__}: {exc}'[:200]
        if widgets:
            try:
                mapping = fill_targets(strip_text.widget_text_scaffold(str(src)))
                (work / 'widget_text.json').write_text(json.dumps(mapping, ensure_ascii=False, sort_keys=True))
                report, w, c = timed(strip_text.strip_text, str(src), str(work / 'stripped-wt.pdf'),
                                     widget_text=mapping)
                row['strip_wt'] = [w, c]
                (work / 'strip-wt-report.json').write_text(json.dumps(report, sort_keys=True, default=str))
            except Exception as exc:
                row['strip_wt'] = f'{type(exc).__name__}: {exc}'[:200]
        job_wt = os.environ.get('R48_JOB_WIDGET_TEXT')
        if job_wt and name == 'fl150':
            try:
                mapping = json.loads(Path(job_wt).read_text(encoding='utf-8'))
                report, w, c = timed(strip_text.strip_text, str(src), str(work / 'stripped-job.pdf'),
                                     widget_text=mapping,
                                     hide_buttons=['Print_bt', 'Save_bt', 'Reset_bt', 'T23'])
                row['strip_job'] = [w, c]
                (work / 'strip-job-report.json').write_text(json.dumps(report, sort_keys=True, default=str))
            except Exception as exc:
                row['strip_job'] = f'{type(exc).__name__}: {exc}'[:200]
                (work / 'strip-job-error.txt').write_text(row['strip_job'])
        # verify, the original against itself: every per-page loop runs
        try:
            v, w, c = timed(run_verify, str(src), str(src))
            row['verify_self'] = [w, c]
            (work / 'verify-self.json').write_text(json.dumps(verdict_dict(v), sort_keys=True, default=str))
        except Exception as exc:
            row['verify_self'] = f'{type(exc).__name__}: {exc}'[:200]
        rows.append(row)
        print(json.dumps(row), flush=True)
    # prepare_font's render check, on one Latin face
    tmp = OUT / '_prepare'
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    tr = tmp / 'translations.json'
    tr.write_text(json.dumps({'fonts': {'regular': str(TREE / 'tests/fonts/NotoSans-Regular.ttf')},
                              'translations': {'Name': 'Nombre del solicitante'}}))
    buf = io.StringIO()
    w0 = time.perf_counter()
    with redirect_stdout(buf):
        rc = prepare_font.prepare_font(str(TREE / 'tests/fonts/NotoSans-Regular.ttf'), str(tr), str(tmp / 'subset.ttf'))
    (OUT / 'prepare-font.log').write_text(f'rc={rc}\n' + buf.getvalue())
    (OUT / 'rows.json').write_text(json.dumps(rows, indent=1))
    print(json.dumps({'prepare_font': rc, 'seconds': round(time.perf_counter() - w0, 3)}))


main()
