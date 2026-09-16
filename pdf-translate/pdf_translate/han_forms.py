# -*- coding: utf-8 -*-
"""Gate 20, han-forms: the face that drew a CJK page uses the forms its
language expects.

Han unification gives 直 骨 海 one code point each; a Japanese face and a
Simplified Chinese face draw them differently, and a reader sees the wrong
region at once. This skill never selects a face — the caller does — so the
delivered document is judged: every embedded face on a page that draws CJK
text is rendered off its own font program (the way gate 18 re-probes a
conjunct face) and compared pixel for pixel with the Noto reference of the
language's convention and with the other convention's, both instanced at
the embedded face's weight.

Measured (docs/BRIEF-han-forms-gate.md; PyMuPDF 1.28.2, the fetched Noto
Sans JP / SC variable faces): a face against its own reference at equal
weight reads 0.000 on every probe; against the other region 0.17–0.51;
weight alone (400 vs 100) reads 0.51–0.55, as large as region, which is why
references are instanced at the delivered weight. 東 is drawn the same in
both conventions: a face that differs from both references on 東 is not a
Noto face and is REVIEW, never matched to the nearer reference.

Nothing here reads the network or prints. The reference faces are files the
caller provides: tests/fonts/ in a checkout, a directory of its own in a
service (verify --reference-fonts DIR, run_verify(reference_fonts=DIR)).
"""
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pymupdf

HAN_PROBES = '\u76f4\u9aa8\u6d77'       # 直 骨 海 — drawn differently in JP and SC
HAN_CONTROL = '\u6771'                   # 東 — the same in both: the family check
HAN_CHARS = HAN_PROBES + HAN_CONTROL     # what prepare_font adds to every CJK subset

OWN_MAX = 0.02          # a face equals its own reference (measured 0.000)
OTHER_MIN = 0.10        # and differs from the other region (measured 0.17–0.51)
MIN_SEPARATING = 2      # probes, of the three, that must separate

# convention -> (display name, reference file in the reference directory; None
# when no reference has been measured for it)
CONVENTIONS = {
    'JP': ('Japanese', 'NotoSansJP-VF.ttf'),
    'SC': ('Simplified Chinese', 'NotoSansSC-VF.ttf'),
    'TC': ('Traditional Chinese', None),
    'KR': ('Korean', None),
}
OTHER = {'JP': 'SC', 'SC': 'JP'}

# verify.SCRIPT_RANGES['CJK'], repeated here because verify imports this
# module; tests.test_han_forms pins the two against each other.
CJK_RANGES = ((0x3040, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
              (0xF900, 0xFAFF), (0xFF66, 0xFF9F), (0x20000, 0x2FA1F))

RENDER_SIZE, RENDER_ZOOM, RENDER_ORIGIN, RENDER_PAGE = 48, 4, (40, 120), 200


def is_cjk(ch):
    """The test verify.script_of makes for 'CJK': a letter in the Han, kana
    or half-width kana blocks. Punctuation (。、「) is not."""
    if not unicodedata.category(ch).startswith('L'):
        return False
    o = ord(ch)
    return any(a <= o <= b for a, b in CJK_RANGES)


def has_cjk(text):
    return any(is_cjk(ch) for ch in text or '')


def convention_for_lang(lang):
    """'JP', 'SC', 'TC' or 'KR' for a BCP 47 tag (ja, zh-Hans, zh-TW, ko…);
    None for any other language or no language."""
    tags = [t for t in (lang or '').strip().lower().replace('_', '-').split('-') if t]
    if not tags:
        return None
    if tags[0] == 'ja':
        return 'JP'
    if tags[0] == 'ko':
        return 'KR'
    if tags[0] == 'zh':
        if 'hant' in tags[1:] or any(t in ('tw', 'hk', 'mo') for t in tags[1:]):
            return 'TC'
        return 'SC'
    return None


def default_reference_dir():
    """tests/fonts/ of a checkout — the fetcher's faces. An installed package
    has no such directory; a consumer passes its own."""
    return Path(__file__).resolve().parents[1] / 'tests' / 'fonts'


def _dir(reference_dir):
    return Path(reference_dir) if reference_dir is not None else default_reference_dir()


def reference_path(convention, reference_dir=None):
    """The convention's variable reference face in the directory, or None."""
    _, filename = CONVENTIONS.get(convention, (None, None))
    if not filename:
        return None
    path = _dir(reference_dir) / filename
    return path if path.is_file() else None


def reference_face(convention, weight, reference_dir=None):
    """Path of the convention's reference instanced at weight, or None when the
    convention has no reference, the file is missing, or the wght axis does
    not reach the weight.

    Instancing takes seconds (JP 4.3 s, SC 7.7 s measured), so the instance is
    cached as <stem>-wght<weight>.ttf beside the source when that directory
    can be written, else under the system temp directory. It is written to a
    temp name and moved into place: a concurrent job never reads a
    half-written file, and two writers produce the same bytes.
    """
    src = reference_path(convention, reference_dir)
    if src is None:
        return None
    weight = int(weight)
    name = f'{src.stem}-wght{weight}.ttf'
    for cache_dir in (src.parent, Path(tempfile.gettempdir()) / 'pdf-translate-han-forms'):
        cached = cache_dir / name
        if cached.is_file():
            return cached
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=name + '.', suffix='.tmp', dir=str(cache_dir))
        except OSError:
            continue
        os.close(fd)
        try:
            _instance(src, weight, tmp)
            os.replace(tmp, cached)
            return cached
        except OSError:
            _discard(tmp)
            continue
        except Exception:       # not a variable font, or the axis does not reach the weight
            _discard(tmp)
            return None
    return None


def _discard(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _instance(src, weight, out):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    font = TTFont(str(src))
    axes = {a.axisTag: a for a in font['fvar'].axes} if 'fvar' in font else {}
    wght = axes.get('wght')
    if wght is None or not wght.minValue <= weight <= wght.maxValue:
        raise ValueError(f'{src.name} has no wght axis reaching {weight}')
    instancer.instantiateVariableFont(font, {'wght': weight}, inplace=True)
    font.save(out)


def render(font, ch):
    """Grey raster (samples, width, height) of one character drawn with a
    pymupdf.Font at the geometry the table was measured at."""
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=RENDER_PAGE, height=RENDER_PAGE)
        tw = pymupdf.TextWriter(page.rect)
        tw.append(RENDER_ORIGIN, ch, font=font, fontsize=RENDER_SIZE)
        tw.write_text(page)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(RENDER_ZOOM, RENDER_ZOOM),
                              colorspace=pymupdf.csGRAY, alpha=False)
        return bytes(pix.samples), pix.width, pix.height
    finally:
        doc.close()


_INK = bytes(1 if v < 128 else 0 for v in range(256))


def diff_ratio(a, b):
    """Pixels that are ink in one raster and not the other, over the pixels
    that are ink in either: 0.0 for identical rasters, 1.0 for rasters of
    different size. The samples become one bit per pixel (ink or not) packed
    into an int, so the union and the difference are two bit counts."""
    if a[1:] != b[1:]:
        return 1.0
    ma = int.from_bytes(a[0].translate(_INK), 'big')
    mb = int.from_bytes(b[0].translate(_INK), 'big')
    union = (ma | mb).bit_count()
    return (ma ^ mb).bit_count() / union if union else 0.0


def weight_of(program):
    """OS/2 usWeightClass of a font program held in memory, or None when it
    cannot be read (a bare CFF program, a Type 3 face)."""
    try:
        from fontTools.ttLib import TTFont
        with TTFont(BytesIO(program), lazy=True) as font:
            return int(font['OS/2'].usWeightClass)
    except Exception:
        return None
