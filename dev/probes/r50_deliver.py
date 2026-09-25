"""R-50 evidence (docs/reviews/2026-09-25-r50-subset-before-instancing.md). Build the same CJK deliveries with one tree (its prepare_font, same inputs).

usage: dev/probes/r50_deliver.py TREE OUTDIR
Each job: a 3-line English paragraph plus two single lines; the paragraph is
a merge (the Story engine, which applies GPOS kern), the lines are plain
runs. Targets mix CJK, kana, CJK punctuation, Latin and digits.
"""
import importlib
import io
import json
import os
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

tree, outdir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(tree))
os.chdir(tree)
import pdf_translate  # noqa: E402
assert Path(pdf_translate.__file__).resolve().is_relative_to(tree)
import pymupdf  # noqa: E402
extract = importlib.import_module('pdf_translate.extract_segments')
strip = importlib.import_module('pdf_translate.strip_text')
prepare = importlib.import_module('pdf_translate.prepare_font')
retypeset = importlib.import_module('pdf_translate.retypeset')
FONTS = tree / 'tests' / 'fonts'

PARA = ['The applicant must file this form with the clerk',
        'before the hearing date, together with Attachment A',
        'and a copy of Form RS-14, by 5:00 p.m. on May 8, 2026.']
LINES = ['Name of the applicant', 'Telephone number (daytime)']
JOBS = {
    'ja-sans': ('NotoSansJP-VF.ttf', 'ja',
                '申請者は、審理日の前に、この書類を「Attachment A」およびForm RS-14の写しとともに、'
                '2026年5月8日午後5:00までに書記官へ提出してください。（注：AV、WA、To、Ty）',
                ['申請者の氏名', '電話番号（日中）']),
    'ja-serif': ('NotoSerifJP-VF.ttf', 'ja',
                 '申請者は審理日の前に、Attachment AとForm RS-14を添えて提出すること。「AVATAR」、1,234円。',
                 ['申請者氏名', '電話番号']),
    'zh-sans': ('NotoSansSC-VF.ttf', 'zh-Hans',
                '申请人必须在听证日期之前，将本表格连同Attachment A和Form RS-14副本，于2026年5月8日下午5:00前提交。（AV、To）',
                ['申请人姓名', '电话号码（白天）']),
}


def build_original(path):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    for i, line in enumerate(PARA):
        page.insert_text((72, 100 + 14 * i), line, fontsize=11)
    for i, line in enumerate(LINES):
        page.insert_text((72, 220 + 30 * i), line, fontsize=11)
    doc.save(path)


def main():
    if outdir.exists():
        shutil.rmtree(outdir)
    for name, (face, lang, para, lines) in JOBS.items():
        for wght in (400, 700):
            job = outdir / f'{name}-{wght}'
            job.mkdir(parents=True)
            src, stripped, out = job / 'orig.pdf', job / 'stripped.pdf', job / 'out.pdf'
            build_original(str(src))
            with redirect_stdout(io.StringIO()):
                extract.extract_segments(str(src), outdir=str(job))
                strip.strip_text(str(src), str(stripped))
            segs = json.loads((job / 'segments.json').read_text(encoding='utf-8'))['segments']
            texts = [s['text'].strip() for s in segs]
            conf = {'fonts': {'regular': 'subset.ttf'}, 'lang': lang,
                    'translations': {t: None for t in texts},
                    'merges': [{'page': 0, 'lines': PARA, 'html': para}]}
            for src_line, tgt in zip(LINES, lines):
                conf['translations'][src_line] = tgt
            for t in PARA:
                conf['translations'].pop(t, None)
            conf['skip'] = [t for t in texts if t not in conf['translations'] and t not in PARA]
            (job / 'translations.json').write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prepare.prepare_font(str(FONTS / face), str(job / 'translations.json'),
                                          str(job / 'subset.ttf'), instance=f'wght={wght}')
                rc2 = retypeset.retypeset(str(stripped), str(job / 'segments.json'),
                                          str(job / 'translations.json'), str(out))
            (job / 'console.txt').write_text(buf.getvalue().replace(str(job), 'JOB').replace(str(FONTS), 'FONTS'))
            print(name, wght, 'prepare', rc, 'retypeset', rc2, flush=True)


main()
