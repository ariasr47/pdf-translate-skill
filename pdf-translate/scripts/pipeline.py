#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hot-path wrappers around the seven stage scripts.

The deterministic pipeline is a few seconds. Wall-clock is the translation
and visual loop. Use `rebuild` after the first extract instead of re-running
strip / extract / prepare_font / compare every round.

Usage:
  python3 pipeline.py init ORIGINAL.pdf --work DIR [--captions captions.json]
                                                  [--widget-text wt.json]
                                                  [--keep-encryption]
      strip + extract into DIR (stripped.pdf, segments.json,
      to_translate.json, widget_text.json). Run it once bare to get the
      widget_text.json scaffold, author the targets, then run it again with
      --widget-text to apply tooltips, dropdown labels and defaults.

  python3 pipeline.py from-cores --work DIR [--force]
      scaffold DIR/translations.json from DIR/to_translate.json cores.
      Values are JSON null (retypeset still FAILs until you author them).
      Refuses to overwrite unless --force. No model, no auto-merge.

  python3 pipeline.py rebuild --work DIR ORIGINAL.pdf OUT.pdf [verify flags...]
      retypeset DIR/stripped.pdf + DIR/segments.json + DIR/translations.json
      then verify ORIGINAL.pdf OUT.pdf with any extra verify flags

  python3 pipeline.py render ORIGINAL.pdf TRANSLATED.pdf renders/ [--dpi 110]

  python3 pipeline.py finish ORIGINAL.pdf OUT.pdf FONT.ttf FINAL.pdf HTML
      field_fonts + compare (delivery only)
"""
import json
import os
import sys
import time

# Same directory as the stage scripts.
from extract_segments import main as extract_main
from field_fonts import field_fonts
from compare import compare
from render_pages import render_pages
from retypeset import retypeset
from strip_text import strip_text, WidgetTextError
from verify import verify, main as verify_main


def cmd_init(argv):
    src = argv[0]
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    os.makedirs(work, exist_ok=True)
    captions = None
    if '--captions' in argv:
        with open(argv[argv.index('--captions') + 1], encoding='utf-8') as f:
            captions = json.load(f)
    widget_text = None
    if '--widget-text' in argv:
        with open(argv[argv.index('--widget-text') + 1], encoding='utf-8') as f:
            widget_text = json.load(f)
    stripped = os.path.join(work, 'stripped.pdf')
    t0 = time.perf_counter()
    try:
        report = strip_text(src, stripped, captions=captions,
                            widget_text=widget_text,
                            keep_encryption='--keep-encryption' in argv)
    except WidgetTextError as exc:
        print(f'FAIL widget text: {exc}')
        return 2
    print(f'strip: xfa_removed={report.get("xfa_removed")} '
          f'dead_buttons={len(report.get("dead_buttons") or [])}')
    if report.get('perms_removed'):
        print(f'strip: deleted /Perms {report["perms_removed"]}')
    if report.get('certified'):
        print('WARNING: the source was CERTIFIED (/Perms /DocMDP); the '
              'translation is not. Say so when you deliver it.')
    if report.get('encryption', {}).get('encrypted') and not report.get('reencrypted'):
        print('NOTE: the source was encrypted; the output is not '
              '(--keep-encryption re-applies its permission bits).')
    leftover = report.get('leftover_text') or []
    if leftover:
        print(f'FAIL: page text survived strip on {len(leftover)} page(s); '
              f'{stripped} was not written:')
        for item in leftover:
            print(f"  p{item['page']}: {item['text']}")
        return 1
    rc = extract_main([src, '--outdir', work])
    print(f'elapsed {time.perf_counter()-t0:.2f}s -> {work}')
    return rc


def scaffold_from_cores(to_translate_path, out_path, force=False):
    """Write translations.json with a null for every core. Returns 0, or 2."""
    if not os.path.isfile(to_translate_path):
        print(f'from-cores: missing {to_translate_path}')
        return 2
    if os.path.isfile(out_path) and not force:
        print(f'from-cores: {out_path} exists (pass --force to overwrite)')
        return 2
    with open(to_translate_path, encoding='utf-8') as f:
        data = json.load(f)
    cores = data.get('cores') or []
    translations = {}
    for c in cores:
        text = (c.get('text') if isinstance(c, dict) else None) or ''
        if text:
            translations[text] = None
    conf = {
        'fonts': {'regular': 'font-sub.ttf', 'bold': 'font-sub.ttf'},
        'translations': translations,
        'merges': [],
        'overrides': [],
        'center': [],
        'skip': [],
        'allow_scale': [],
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(conf, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'from-cores: {len(translations)} cores -> {out_path} '
          f'(values are null — author them; do not ship)')
    return 0


def cmd_from_cores(argv):
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    force = '--force' in argv
    to_path = os.path.join(work, 'to_translate.json')
    out_path = os.path.join(work, 'translations.json')
    return scaffold_from_cores(to_path, out_path, force=force)


def cmd_rebuild(argv):
    if '--work' not in argv:
        print('rebuild requires --work DIR')
        return 2
    wi = argv.index('--work')
    work = argv[wi + 1]
    rest = argv[:wi] + argv[wi + 2:]
    if len(rest) < 2:
        print('rebuild: ORIGINAL.pdf OUT.pdf [verify flags...]')
        return 2
    orig, out, extra = rest[0], rest[1], rest[2:]
    orig = os.path.abspath(orig)
    out = os.path.abspath(out)
    work = os.path.abspath(work)
    stripped = os.path.join(work, 'stripped.pdf')
    segs = os.path.join(work, 'segments.json')
    tr = os.path.join(work, 'translations.json')
    here = os.getcwd()
    t0 = time.perf_counter()
    try:
        os.chdir(work)
        rc = retypeset(stripped, segs, tr, out)
        if rc != 0:
            print(f'elapsed {time.perf_counter()-t0:.2f}s (retypeset failed)')
            return rc
        rc = verify_main([orig, out] + extra)
        print(f'elapsed {time.perf_counter()-t0:.2f}s')
        return rc
    finally:
        os.chdir(here)


def cmd_render(argv):
    dpi = int(argv[argv.index('--dpi') + 1]) if '--dpi' in argv else 110
    orig, trans, outdir = argv[0], argv[1], argv[2]
    t0 = time.perf_counter()
    render_pages(orig, trans, outdir, dpi=dpi)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return 0


def cmd_finish(argv):
    orig, out, font, final, html = argv[0], argv[1], argv[2], argv[3], argv[4]
    t0 = time.perf_counter()
    rc = field_fonts(out, font, final)
    if rc != 0:
        return rc
    compare(orig, final, html)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == 'init':
        return cmd_init(rest)
    if cmd == 'from-cores':
        return cmd_from_cores(rest)
    if cmd == 'rebuild':
        return cmd_rebuild(rest)
    if cmd == 'render':
        return cmd_render(rest)
    if cmd == 'finish':
        return cmd_finish(rest)
    print('unknown command', cmd)
    print(__doc__)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
