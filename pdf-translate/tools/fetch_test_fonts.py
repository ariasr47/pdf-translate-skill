#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch the OFL fonts the shaping tests need into tests/fonts/.

The Arabic and Devanagari tests otherwise depend on whatever the host
happens to ship (Arial on macOS/Windows, Nirmala UI on Windows) and SKIP
everywhere else — which means the shaping gates were never exercised on
Linux, where CI runs.

Nothing is committed: the fonts are downloaded on demand from pinned
commits of Google's notofonts repositories, which are SIL Open Font
License 1.1. Run it once locally, or let CI run it.

  python3 tools/fetch_test_fonts.py [--dest tests/fonts] [--check]

--check exits 1 if any font is missing, without downloading (useful in a
pre-flight step).
"""
import hashlib
import os
import sys
import urllib.request

# Candidate URLs per face, tried in order. All SIL Open Font License 1.1.
#
# These are branch-tip URLs, not commit pins: pinning needs a SHA somebody
# has actually verified, and inventing one produces a 404 that looks like a
# network problem. If you want reproducible bytes, replace "main" with a
# commit you checked and note the sha256 the fetcher prints. A fetch failure
# is fatal here on purpose — a missing font used to turn into a silent SKIP,
# which is exactly how the shaping gates went unexercised.
FONTS = {
    'NotoSans-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/latin-greek-cyrillic/'
        'main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf',
    ),
    'NotoNaskhArabic-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/arabic/'
        'main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Regular.ttf',
    ),
    'NotoSansHebrew-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansHebrew/hinted/ttf/NotoSansHebrew-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/hebrew/'
        'main/fonts/NotoSansHebrew/hinted/ttf/NotoSansHebrew-Regular.ttf',
    ),
    'NotoSansDevanagari-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansDevanagari/hinted/ttf/'
        'NotoSansDevanagari-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/devanagari/'
        'main/fonts/NotoSansDevanagari/hinted/ttf/'
        'NotoSansDevanagari-Regular.ttf',
    ),
    # Added 2026-09-15. _SHAPING_RANGES in retypeset.py already ROUTES these
    # scripts through the Story engine, but no face for any of them existed
    # here, so every one of their shaping tests SKIPPED -- the same silent
    # gap this fetcher was written to close for Arabic and Devanagari.
    # Both URLs verified 200 on 2026-09-15; the per-script notofonts repos
    # (notofonts/thai etc.) exist but carry no fonts/ tree, so the fallback
    # is the unhinted build in the same repo rather than an invented path.
    'NotoSansThai-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansThai/hinted/ttf/NotoSansThai-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansThai/unhinted/ttf/NotoSansThai-Regular.ttf',
    ),
    'NotoSansKhmer-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansKhmer/hinted/ttf/NotoSansKhmer-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansKhmer/unhinted/ttf/NotoSansKhmer-Regular.ttf',
    ),
    'NotoSansTamil-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansTamil/hinted/ttf/NotoSansTamil-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansTamil/unhinted/ttf/NotoSansTamil-Regular.ttf',
    ),
    'NotoSansBengali-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansBengali/hinted/ttf/NotoSansBengali-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansBengali/unhinted/ttf/NotoSansBengali-Regular.ttf',
    ),
    'NotoSansMyanmar-Regular.ttf': (
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansMyanmar/hinted/ttf/NotoSansMyanmar-Regular.ttf',
        'https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
        'main/fonts/NotoSansMyanmar/unhinted/ttf/NotoSansMyanmar-Regular.ttf',
    ),
    # Added 2026-09-16 for the CJK gates (kinsoku now; Han forms to follow).
    # The google/fonts builds are glyf-flavoured variable TTFs, the only CJK
    # source MuPDF renders reliably (references/fonts.md); the notofonts
    # noto-cjk "Subset" variable TTFs are the same builds under another
    # path. Both URLs per face answered 200 on 2026-09-16 (JP 9.6 MB, SC
    # 17.8 MB). Saved without the "[wght]" of the upstream name so a CSS
    # url() and a shell glob never have to quote it.
    'NotoSansJP-VF.ttf': (
        'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/'
        'NotoSansJP%5Bwght%5D.ttf',
        'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/'
        'TTF/Subset/NotoSansJP-VF.ttf',
    ),
    'NotoSansSC-VF.ttf': (
        'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/'
        'NotoSansSC%5Bwght%5D.ttf',
        'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/'
        'TTF/Subset/NotoSansSC-VF.ttf',
    ),
}
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DEST = os.path.join(os.path.dirname(HERE), 'tests', 'fonts')


def missing(dest):
    return [name for name in FONTS if not os.path.isfile(os.path.join(dest, name))]


def _download(name, urls):
    problems = []
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = r.read()
        except Exception as exc:
            problems.append(f'{url}: {exc}')
            continue
        if not (data.startswith(b'\x00\x01\x00\x00')
                or data.startswith(b'true') or data.startswith(b'OTTO')):
            problems.append(f'{url}: not a font file ({len(data)} bytes)')
            continue
        return data, url, problems
    return None, None, problems


def fetch(dest):
    os.makedirs(dest, exist_ok=True)
    failures = []
    for name, urls in FONTS.items():
        path = os.path.join(dest, name)
        if os.path.isfile(path):
            print(f'have {name}')
            continue
        print(f'fetching {name}')
        data, url, problems = _download(name, urls)
        if data is None:
            failures.append((name, problems))
            for line in problems:
                print(f'  tried {line}')
            continue
        with open(path, 'wb') as f:
            f.write(data)
        print(f'  {len(data) // 1024} KB from {url}')
        print(f'  sha256 {hashlib.sha256(data).hexdigest()}')
    if failures:
        print(f'FAIL: could not fetch {len(failures)} font(s). The shaping '
              f'tests would SKIP, which is how they went unexercised in the '
              f'first place. Fix the URLs in this file or place the faces in '
              f'{dest} by hand.')
        return 1
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dest = argv[argv.index('--dest') + 1] if '--dest' in argv else DEFAULT_DEST
    if '--check' in argv:
        gone = missing(dest)
        if gone:
            print(f'missing in {dest}: {gone}')
            return 1
        print(f'all test fonts present in {dest}')
        return 0
    return fetch(dest)


if __name__ == '__main__':
    raise SystemExit(main())
