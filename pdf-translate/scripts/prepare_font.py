#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 3 of pdf-translate: produce render-safe, small, embeddable fonts.

Subsets a font to the exact characters your translations use, and — the part
that saves you from a silent disaster — ASSERTS the result actually
rasterizes in MuPDF by rendering a sample and counting dark pixels.
`Font.has_glyph()` passing proves nothing: MuPDF silently draws NOTHING for
CJK glyphs from subsetted CFF/OTF fonts. Only TrueType-flavored (glyf) fonts
are safe. For CJK, start from a variable TTF (e.g. Google Fonts Noto Sans JP)
and pass --instance to extract a weight. See references/fonts.md for
per-script font sources.

Usage:
  python3 prepare_font.py FONT.ttf translations.json OUT.ttf \
      [--instance wght=700] [--sample "text in target script"]

Skip subsetting entirely (use the font as-is) when the font is already small,
or when it will also serve form-field input (users type characters outside
your translations — see field_fonts.py).
"""
import json
import os
import shutil
import string
import subprocess
import sys
from pathlib import Path

import pymupdf


def find_pyftsubset():
    """Locate pyftsubset: PATH, then next to the interpreter, then fontTools."""
    found = shutil.which('pyftsubset')
    if found:
        return [found]
    exe_dir = Path(sys.executable).parent
    for name in ('pyftsubset.exe', 'pyftsubset'):
        for candidate in (exe_dir / name, exe_dir / 'Scripts' / name):
            if candidate.is_file():
                return [str(candidate)]
    return [sys.executable, '-m', 'fontTools.subset']


def prepare_font(font_in, trf, font_out, instance=None, sample=None):
    """Subset (and optionally instance) a font; rasterization-assert the result.

    Returns 0 on success, 1 if the font does not rasterize the sample.
    """
    with open(trf, encoding='utf-8') as f:
        conf = json.load(f)
    chars = set(string.printable)
    for v in conf['translations'].values():
        chars.update(v)
    for m in conf.get('merges', []):
        chars.update(m['html'])
    for o in conf.get('overrides', []):
        for p in o['parts']:
            chars.update(p['text'])
    chars.discard('‖')
    chars.update('.…·—–「」（）『』、。・　％＄€£¥')

    src = font_in
    if instance:
        tag, val = instance.split('=')
        from fontTools import ttLib
        from fontTools.varLib.instancer import instantiateVariableFont
        font = ttLib.TTFont(font_in)
        instantiateVariableFont(font, {tag: float(val)}, inplace=True)
        # A variable font's default instance may be a different weight than the
        # one you asked for (Noto Sans JP defaults to Thin), and instancing does
        # not rewrite the name table — leaving /BaseFont advertising "Thin" for
        # Regular outlines. Cosmetic, but it misleads anyone inspecting the PDF.
        try:
            fam = (font['name'].getDebugName(16)
                   or font['name'].getDebugName(1) or 'Subset')
            style = {100: 'Thin', 200: 'ExtraLight', 300: 'Light',
                     400: 'Regular', 500: 'Medium', 600: 'SemiBold',
                     700: 'Bold', 800: 'ExtraBold',
                     900: 'Black'}.get(int(float(val)), str(int(float(val))))
            fam = fam.split(' Thin')[0].strip()
            for rec in font['name'].names:
                if rec.nameID == 1:
                    rec.string = fam
                elif rec.nameID == 2:
                    rec.string = style
                elif rec.nameID in (4, 6):
                    full = f'{fam} {style}'
                    rec.string = (full if rec.nameID == 4
                                  else full.replace(' ', ''))
        except Exception as e:
            print(f'  (name-table touch-up skipped: {e})')
        src = font_out + '.instanced.ttf'
        font.save(src)

    charfile = font_out + '.chars.txt'
    with open(charfile, 'w', encoding='utf-8') as f:
        f.write(''.join(sorted(chars)))
    cmd = find_pyftsubset() + [src, f'--text-file={charfile}',
                               f'--output-file={font_out}']
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print('FAIL: pyftsubset not found. Install fonttools '
              '(used as: python -m fontTools.subset) and retry.')
        return 1

    if not sample:
        non_ascii = [c for c in chars if ord(c) > 0x2000]
        sample = ''.join(sorted(non_ascii)[:12]) or 'Sample text 123'
    font = pymupdf.Font(fontfile=font_out)
    doc = pymupdf.open()
    p = doc.new_page()
    tw = pymupdf.TextWriter(p.rect)
    tw.append((72, 100), sample, font=font, fontsize=14)
    tw.write_text(p)
    pix = p.get_pixmap(dpi=100, clip=pymupdf.Rect(60, 80, 560, 120))
    dark = sum(1 for i in range(0, len(pix.samples), pix.n) if pix.samples[i] < 128)
    per_char = dark / max(len(sample.strip()), 1)
    doc.close()
    if per_char < 15:
        print(f'FAIL: font does not rasterize sample "{sample[:30]}" '
              f'({dark} dark px). Use a glyf-flavored TTF source.')
        return 1
    print(f'OK: {font_out} ({os.path.getsize(font_out)//1024} KB, '
          f'{len(chars)} chars, render check {dark} px)')
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    font_in, trf, font_out = argv[0], argv[1], argv[2]
    instance = (argv[argv.index('--instance') + 1]
                if '--instance' in argv else None)
    sample = (argv[argv.index('--sample') + 1]
              if '--sample' in argv else None)
    return prepare_font(font_in, trf, font_out, instance=instance, sample=sample)


if __name__ == '__main__':
    raise SystemExit(main())
