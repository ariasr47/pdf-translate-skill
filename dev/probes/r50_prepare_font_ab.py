"""R-50 evidence (docs/reviews/2026-09-25-r50-subset-before-instancing.md). R-50 A/B: run prepare_font over the same cases with one tree; record everything.

usage: dev/probes/r50_prepare_font_ab.py build TREE CASEDIR        (once, with the base tree)
       dev/probes/r50_prepare_font_ab.py run TREE CASEDIR OUTFILE  (once per tree, fresh process)
"""
import hashlib
import importlib
import io
import json
import os
import shutil
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

mode, tree, casedir = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
sys.path.insert(0, str(tree))
os.chdir(tree)
import pdf_translate  # noqa: E402
assert Path(pdf_translate.__file__).resolve().is_relative_to(tree)
FONTS = tree / 'tests' / 'fonts'

JA, ZH = '申請者は直骨海東京で書類を提出する', '申请人在直骨海东京提交表格'
LEGACY = []
for family, target, lang in (('NotoSansJP-VF', JA, 'ja'), ('NotoSansSC-VF', ZH, 'zh-Hans'),
                             ('NotoSerifJP-VF', JA, 'ja'), ('NotoSerifSC-VF', ZH, 'zh-Hans')):
    for wght in (400, 700):
        for judged in (False, True):
            LEGACY.append({'name': f'legacy-{family}-{wght}-{"judged" if judged else "quiet"}',
                           'face': f'{family}.ttf', 'target': target,
                           'lang': lang if judged else None, 'instance': f'wght={wght}'})
# Wrong-region face, judged: must refuse the same way.
LEGACY.append({'name': 'legacy-SC-face-for-ja', 'face': 'NotoSansSC-VF.ttf', 'target': JA,
               'lang': 'ja', 'instance': 'wght=400'})
# Controls with no instancing: the path this change does not touch.
LEGACY += [{'name': 'legacy-latin', 'face': 'NotoSans-Regular.ttf', 'target': 'Nombre del solicitante',
            'lang': 'es', 'instance': None},
           {'name': 'legacy-arabic', 'face': 'NotoNaskhArabic-Regular.ttf', 'target': 'اسم مقدم الطلب',
            'lang': 'ar', 'instance': None},
           {'name': 'legacy-devanagari', 'face': 'NotoSansDevanagari-Regular.ttf', 'target': 'आवेदक का नाम क्षत्रिय',
            'lang': 'hi', 'instance': None},
           {'name': 'legacy-jp-static', 'face': 'NotoSansJP-VF-wght400.ttf', 'target': JA,
            'lang': 'ja', 'instance': None}]
TYPO = []
for cls, fam in (('sans', 'NotoSans'), ('serif', 'NotoSerif')):
    for lang, suffix, target in (('ja', 'JP', '日本語の申請書'), ('zh-Hans', 'SC', '简体中文申请表')):
        for role, wght in (('regular', 400), ('bold', 700), ('italic', 400), ('bold_italic', 700)):
            TYPO.append({'name': f'typo-{cls}-{suffix}-{role}', 'face': f'{fam}{suffix}-VF.ttf',
                         'cls': cls, 'role': role, 'lang': lang, 'target': target, 'instance': f'wght={wght}'})


def build():
    from tests.test_pipeline import SOURCE_SENTENCE, write_mapping
    from tests.test_typography_fonts import STYLES, make_mapping
    run_extract = importlib.import_module('pdf_translate.extract_segments').run_extract
    import pymupdf
    if casedir.exists():
        shutil.rmtree(casedir)
    casedir.mkdir(parents=True)
    for case in LEGACY:
        d = casedir / case['name']
        d.mkdir()
        write_mapping(str(d / 'translations.json'), {SOURCE_SENTENCE: case['target']},
                      FONTS / case['face'], lang=case['lang'])
    for case in TYPO:
        d = casedir / case['name']
        d.mkdir()
        original = d / 'original.pdf'
        style = STYLES[case['cls']]['bold' if 'bold' in case['role'] else 'regular']
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=400, height=200)
            page.insert_text((30, 60), 'Pay', fontname=style, fontsize=12)
            pdf.save(original)
        extracted = run_extract(str(original), str(d), typography=True)
        data = json.loads(Path(extracted.segments_path).read_text(encoding='utf-8'))
        conf = make_mapping(data, {case['cls']: {case['role']: 'prepared.ttf'}})
        conf['targets'][0]['runs'][0]['text'] = case['target']
        conf['lang'] = case['lang']
        (d / 'translations.json').write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')
    (casedir / 'cases.json').write_text(json.dumps({'legacy': LEGACY, 'typo': TYPO}, ensure_ascii=False))
    print('built', len(LEGACY) + len(TYPO))


def normalized(path):
    from fontTools.ttLib import TTFont
    with TTFont(path) as font:
        font.recalcTimestamp = False
        font['head'].modified = 0
        buf = io.BytesIO()
        font.save(buf)
    return hashlib.sha256(buf.getvalue()).hexdigest()


def run(outfile):
    prepare_font = importlib.import_module('pdf_translate.prepare_font')
    han_forms = importlib.import_module('pdf_translate.han_forms')
    for conv in ('JP', 'SC'):
        for w in (400, 700):
            han_forms.reference_face(conv, w, FONTS)   # warm the reference cache
    cases = json.loads((casedir / 'cases.json').read_text())
    work = Path(outfile).with_suffix('.work')
    if work.exists():
        shutil.rmtree(work)
    rows = []
    for case in cases['legacy'] + cases['typo']:
        out_dir = work / case['name']
        out_dir.mkdir(parents=True)
        for item in (casedir / case['name']).iterdir():
            if item.is_file():
                shutil.copy(item, out_dir / item.name)
        out = out_dir / ('prepared.ttf' if 'cls' in case else 'subset.ttf')
        kwargs = {'instance': case['instance'], 'reference_fonts': str(FONTS)}
        if 'cls' in case:
            kwargs.update(font_class=case['cls'], font_role=case['role'])
        buf = io.StringIO()
        c0, w0 = time.process_time(), time.perf_counter()
        error = None
        try:
            with redirect_stdout(buf):
                result = prepare_font.run_prepare_font(str(FONTS / case['face']), str(out_dir / 'translations.json'),
                                                       str(out), **kwargs)
            outcome = {k: v for k, v in result.to_dict().items() if k not in ('version', 'output', 'face')}
        except Exception as exc:
            error = {'type': type(exc).__name__, 'reason': getattr(exc, 'reason', None),
                     'text': str(exc).replace(str(out_dir), 'OUT').replace(str(FONTS), 'FONTS')}
            outcome = None
        cpu, wall = round(time.process_time() - c0, 3), round(time.perf_counter() - w0, 3)
        inputs = {p.name for p in (casedir / case['name']).iterdir() if p.is_file()}
        files = sorted(p.name for p in out_dir.iterdir() if p.name not in inputs)
        rows.append({'name': case['name'], 'cpu': cpu, 'wall': wall, 'error': error, 'result': outcome,
                     'log': buf.getvalue().replace(str(out_dir), 'OUT').replace(str(FONTS), 'FONTS'),
                     'files': files, 'bytes': os.path.getsize(out) if out.exists() else None,
                     'sha256_no_timestamp': normalized(out) if out.exists() else None})
        print(case['name'], cpu, error['reason'] if error else 'ok', flush=True)
    Path(outfile).write_text(json.dumps(rows, ensure_ascii=False, indent=1))


build() if mode == 'build' else run(sys.argv[4])
