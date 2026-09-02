#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 5 of pdf-translate: automated gates. Run after EVERY build; exit 0 = pass.

1. field parity   set of (fully-qualified name, type) identical to original;
                  extra fields allowed only with --allow-extra-prefix
2. fill roundtrip a text value in the TARGET script + a checkbox survive
                  save/reopen (skipped if the PDF has no fields)
3. ink density    per-page dark-pixel ratio vs original within [--min-ink, hard
                  ceiling 3x] — catches invisible glyphs and blank regions
4. leak scan      split in two: THREE OR MORE consecutive source-script words
                  is untranslated running text and fails; one or two adjacent
                  tokens are reported for review only, because official form
                  names (Schedule C, Form W-2), statutes and proper nouns are
                  supposed to survive translation intact
5. text layer     a page with visible ink or an embedded image but no
                  extractable text is treated as a scan and fails (OCR first).
                  Ink ratio is skipped when the original has negligible ink,
                  instead of failing a pale/blank page with ratio 0.00.
6. placement      if --translations is given, every non-passthrough target
                  string (length ≥ 2, whitespace/NBSP normalized, U+2010/U+2011
                  folded to ASCII '-') must appear in the output text layer.
                  Omit the flag: this gate does not run. Does not judge
                  whether a target is the right term.
7. button chrome  with --translations: a visible original pushbutton caption
                  still in the output (get_text() sees /AP) must be skip'd or
                  rewritten (--captions). Otherwise FAIL and list the caption.
                  Omit the flag: this gate does not run. Field count stays
                  the field-parity gate — do not add widgets.
8. identifiers    with --translations: quoted and form-name write/find/say
                  spans from the original page (shipped write_find_say_hits)
                  must appear in the output text layer unless listed in
                  allow_translate. Missing ones FAIL and are listed.
                  Omit the flag: this gate does not run. url-or-email is not
                  a hard fail.
9. empty targets  with --translations: a non-skip, non-null translations
                  value (also merge html / override parts) whose
                  NBSP-normalized strip is empty FAILs and names the core.
                  Omit the flag: this gate does not run. Length-1 non-empty
                  placement skip is unchanged. JSON null is retypeset's job.
10. caption width with --translations: output pushbutton /MK /CA wider
                  than the widget rect (helv text_length, pad 2 pt each
                  side) FAILs listing field name and caption. Omit the
                  flag: this gate does not run. Measures output /CA only.

These gates catch structural failures. They do NOT catch visual defects —
after they pass you still render pages side-by-side and look at them.

Usage:
  python3 verify.py ORIGINAL.pdf TRANSLATED.pdf \
      [--fill-text "value in target script"] [--allow WORD,WORD,...] \
      [--min-ink 0.4] [--source-regex "[A-Za-z]{4,}"] \
      [--source-words-from segments.json] [--allow-extra-prefix tr_] \
      [--translations translations.json]
"""
import json
import os
import re
import sys
import tempfile
import time

import pymupdf

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
from extract_segments import write_find_say_hits  # noqa: E402

WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")
RUN = re.compile(r"[A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*){2,}")
# Dark-pixel floor at 72 dpi. Below this, a page is "no ink" for the ratio
# gate. At-or-above, combined with empty get_text(), it is a scan suspect.
VISIBLE_INK = 50
INK_SKIP = 20


def _arg(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def source_words_from_segments(path, allow):
    """Unique 4+ letter Latin tokens from this document's own segments."""
    words = set()
    with open(path, encoding='utf-8') as f:
        segs = json.load(f)['segments']
    for s in segs:
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", s['text']):
            words.add(w.lower())
    words -= allow
    return words


# get_text() often remaps authored ASCII '-' to U+2010/U+2011 (e.g. "W-2").
_PLACEMENT_FOLD = str.maketrans({
    '\xa0': ' ',
    '\u202f': ' ',
    '\u2007': ' ',
    '\u2010': '-',
    '\u2011': '-',
})


def normalize_ws_nbsp(text):
    """NBSP/figure spaces → ASCII space; U+2010/U+2011 → ASCII hyphen."""
    if not text:
        return ''
    return text.translate(_PLACEMENT_FOLD)


def collect_translation_targets(conf):
    """Authored strings that should land in get_text() (not skip / not passthrough).

    translations.json values are already the non-passthrough mapping. '‖' is a
    retypeset weight split, not a glyph, so each side is searched separately.
    Merges and overrides are also placed text.
    """
    skip = set(conf.get('skip') or [])
    targets = []
    for core, tgt in (conf.get('translations') or {}).items():
        if core in skip or tgt is None:
            continue
        for part in str(tgt).split('‖'):
            targets.append(part)
    for merge in conf.get('merges') or []:
        html = merge.get('html') or ''
        text = re.sub(r'<br\s*/?>', ' ', html, flags=re.I)
        text = re.sub(r'<[^>]+>', '', text)
        if text:
            targets.append(text)
    for override in conf.get('overrides') or []:
        for part in override.get('parts') or []:
            t = part.get('text')
            if t:
                targets.append(t)
    return targets


def _authored_text_is_empty(raw):
    """True when normalize + strip leaves nothing. Length-1 'Z' is not empty."""
    if raw is None:
        return False
    return len(normalize_ws_nbsp(str(raw)).strip()) == 0


def _merge_plain_text(html):
    text = html or ''
    text = re.sub(r'<br\s*/?>', ' ', text, flags=re.I)
    return re.sub(r'<[^>]+>', '', text)


def empty_translation_targets(conf):
    """Labels for authored empty/whitespace values (not skip, not null).

    Returns cores / merge first lines / override contains so FAIL can name
    them. Whitespace includes NBSP. Skip entries are omitted even if the
    mapped string is empty.
    """
    skip = set(conf.get('skip') or [])
    empty = []
    seen = set()

    def add(label):
        if label and label not in seen:
            seen.add(label)
            empty.append(label)

    for core, tgt in (conf.get('translations') or {}).items():
        if core in skip or tgt is None:
            continue
        if _authored_text_is_empty(tgt):
            add(core)
    for merge in conf.get('merges') or []:
        if _authored_text_is_empty(_merge_plain_text(merge.get('html'))):
            lines = merge.get('lines') or []
            add(lines[0] if lines else '(merge)')
    for override in conf.get('overrides') or []:
        for part in override.get('parts') or []:
            t = part.get('text')
            if t is None:
                continue
            if _authored_text_is_empty(t):
                add(override.get('contains') or '(override)')
    return empty


_ACTUALTEXT_HEX = re.compile(rb'/ActualText\s*<\s*([0-9A-Fa-f]+)\s*>')


def extract_actualtext(page):
    """Logical strings from /ActualText marked content on the page."""
    data = page.read_contents() or b''
    out = []
    for m in _ACTUALTEXT_HEX.finditer(data):
        raw = bytes.fromhex(m.group(1).decode('ascii'))
        if raw.startswith(b'\xfe\xff'):
            out.append(raw[2:].decode('utf-16-be', 'replace'))
        elif raw.startswith(b'\xff\xfe'):
            out.append(raw[2:].decode('utf-16-le', 'replace'))
        else:
            try:
                out.append(raw.decode('utf-16-be', 'replace'))
            except Exception:
                continue
    return out


def page_search_text(page):
    """get_text() plus ActualText — RTL logical order lives in the latter."""
    parts = [page.get_text() or '']
    parts.extend(extract_actualtext(page))
    return '\n'.join(parts)


def missing_translation_targets(page_text, targets):
    """Return targets of length ≥ 2 (NBSP/space-normalized) absent from page text."""
    hay = normalize_ws_nbsp(page_text)
    missing = []
    seen = set()
    for raw in targets:
        nt = normalize_ws_nbsp(raw)
        if len(nt) < 2:
            continue
        if nt in seen:
            continue
        seen.add(nt)
        if nt not in hay:
            missing.append(raw)
    return missing


PUSHBUTTON = 1 << 16


def pushbutton_captions(doc):
    """Pushbutton captions (/MK /CA) keyed by field name.

    Hidden is an annotation /F bit, not field flags — not filtered here.
    --hide-buttons is a different path; skip/captions is this gate.
    """
    caps = {}
    for page in doc:
        for w in page.widgets() or []:
            if not (w.field_flags & PUSHBUTTON):
                continue
            cap = (w.button_caption or '').strip()
            if cap:
                caps[w.field_name] = cap
    return caps


def leftover_button_captions(orig_caps, out_caps, out_text, skip=None):
    """Original pushbutton captions still drawing, and not skip / not rewritten.

    get_text() includes widget appearance streams, so a leftover /AP of
    'Print' is visible here even after strip removed page text. Rewritten
    CA plus dropped /AP removes it. skip is the explicit leave-chrome path.
    """
    skip = set(skip or [])
    hay = normalize_ws_nbsp(out_text)
    leftover = []
    for name, cap in orig_caps.items():
        nt = normalize_ws_nbsp(cap)
        if len(nt) < 2:
            continue
        if cap in skip or nt in skip:
            continue
        out_n = normalize_ws_nbsp(out_caps.get(name) or '')
        rewritten = bool(out_n) and out_n != nt
        still_in_text = nt in hay
        if rewritten and not still_in_text:
            continue
        leftover.append((name, cap))
    return leftover


def caption_overflows(caption, rect_width, fs):
    """True if Helvetica caption is wider than rect_width minus 2 pt pad each side."""
    cap = (caption or '').strip()
    if not cap:
        return False
    width = pymupdf.Font('helv').text_length(cap, fontsize=fs)
    return width > rect_width - 4


def caption_fontsize(widget):
    """widget.text_fontsize if > 0, else max(4, rect.height - 4)."""
    fs = getattr(widget, 'text_fontsize', 0) or 0
    try:
        fs = float(fs)
    except (TypeError, ValueError):
        fs = 0.0
    if fs > 0:
        return fs
    return max(4.0, float(widget.rect.height) - 4.0)


def overflowing_button_captions(doc):
    """Output pushbuttons whose /CA does not fit the widget rect."""
    hits = []
    for page in doc:
        for w in page.widgets() or []:
            if not (w.field_flags & PUSHBUTTON):
                continue
            cap = (w.button_caption or '').strip()
            if not cap:
                continue
            if caption_overflows(cap, w.rect.width, caption_fontsize(w)):
                hits.append((w.field_name, cap))
    return hits


IDENTIFIER_KINDS = ('quoted', 'form-name')


def collect_identifier_spans(orig_doc):
    """Unique quoted / form-name write/find/say spans from original pages.

    Uses shipped extract_segments.write_find_say_hits — do not copy its regexes.
    url-or-email hits are not collected (not a hard fail this sitting).
    """
    spans = []
    seen = set()
    for page in orig_doc:
        for kind, snippet in write_find_say_hits(page.get_text() or ''):
            if kind not in IDENTIFIER_KINDS:
                continue
            nt = normalize_ws_nbsp(snippet)
            if len(nt) < 2 or nt in seen:
                continue
            seen.add(nt)
            spans.append(snippet)
    return spans


def missing_identifier_spans(page_text, spans, allow_translate=None):
    """Return identifier spans absent from page_text, minus allow_translate.

    Same NBSP/hyphen normalize as placement. Omit allow_translate (or [])
    means every span is required.
    """
    allow = {normalize_ws_nbsp(s) for s in (allow_translate or []) if s}
    hay = normalize_ws_nbsp(page_text)
    missing = []
    for raw in spans:
        nt = normalize_ws_nbsp(raw)
        if nt in allow:
            continue
        if nt not in hay:
            missing.append(raw)
    return missing


def scan_leaks(text, allow, source_words=None, src_re=None):
    """Split surviving source-language tokens into running vs isolated.

    When source_words is provided (same-script pairs), both buckets use THIS
    document's own source words so the translation itself is not flagged.
    Otherwise a script regex is used (different-script default).
    """
    running, isolated = [], []
    if source_words:
        tokens = [m.group(0) for m in WORD.finditer(text)]
        i = 0
        while i < len(tokens):
            low = tokens[i].lower()
            if low in source_words and low not in allow:
                j = i
                seq = []
                while j < len(tokens):
                    lj = tokens[j].lower()
                    if lj in source_words and lj not in allow:
                        seq.append(tokens[j])
                        j += 1
                    else:
                        break
                if len(seq) >= 3:
                    running.append(' '.join(seq)[:70])
                else:
                    isolated.extend(seq)
                i = j
            else:
                i += 1
        return running, isolated

    for phrase in RUN.findall(text):
        words = re.findall(r"[A-Za-z']+", phrase)
        if sum(1 for w in words if w.lower() not in allow) >= 3:
            running.append(phrase.strip()[:70])
    masked = RUN.sub(' ', text)
    if src_re is not None:
        for word in src_re.findall(masked):
            if word.lower() not in allow:
                isolated.append(word)
    return running, isolated


def page_unextractable(page):
    """True when the page looks scanned: visible content, no text layer."""
    if page.get_text().strip():
        return False
    if page.get_images():
        return True
    return ink(page) >= VISIBLE_INK


def ink(page):
    px = page.get_pixmap(dpi=72)
    # Hoist the buffer: indexing px.samples inside the loop re-materializes
    # the whole buffer on every access (~45 s/page instead of instant).
    buf = bytes(px.samples)
    return sum(1 for k in range(0, len(buf), px.n) if buf[k] < 100)


def verify(orig, trans, fill_text='Test value 123', allow=None, min_ink=0.4,
           source_regex=None, source_words_from=None, allow_extra_prefix=None,
           translations=None):
    """Run structural gates. Returns 0 on pass, 1 on any failure."""
    allow = set(w.lower() for w in (allow or []) if w)
    source_words = None
    src_re = None
    if source_words_from:
        source_words = source_words_from_segments(source_words_from, allow)
        print(f'leak scan: {len(source_words)} source words from {source_words_from}')
    else:
        src_re = re.compile(source_regex or r'[A-Za-z]{4,}')

    o, j = pymupdf.open(orig), pymupdf.open(trans)
    fail = 0

    onames = {w.field_name: w.field_type_string for p in o for w in p.widgets()}
    jnames = {w.field_name: w.field_type_string for p in j for w in p.widgets()}
    missing = set(onames) - set(jnames)
    mismatch = [k for k in onames if k in jnames and onames[k] != jnames[k]]
    extra = {k for k in set(jnames) - set(onames)
             if not (allow_extra_prefix and k.startswith(allow_extra_prefix))}
    print(f'fields: {len(onames)} original / {len(jnames)} translated')
    for label, bad in [('missing', missing), ('type-mismatch', mismatch),
                       ('unexpected-extra', extra)]:
        if bad:
            print(f'FAIL field {label}:', sorted(bad)[:10])
            fail = 1
    if not (missing or mismatch or extra):
        print('PASS field parity')

    if onames:
        ttarget = cbtarget = None
        for p in j:
            for w in p.widgets():
                if ttarget is None and w.field_type_string == 'Text':
                    ttarget = w.field_name
                if cbtarget is None and w.field_type_string == 'CheckBox':
                    cbtarget = w.field_name
        for p in j:
            for w in p.widgets():
                if w.field_name == ttarget:
                    w.field_value = fill_text
                    w.update()
                if w.field_name == cbtarget:
                    w.field_value = True
                    w.update()
        fd, fill_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        try:
            j.save(fill_path)
            t = pymupdf.open(fill_path)
            got_t = any(w.field_value == fill_text for p in t for w in p.widgets()
                        if w.field_name == ttarget)
            got_cb = (cbtarget is None) or any(
                w.field_value for p in t for w in p.widgets()
                if w.field_name == cbtarget)
            t.close()
            ok = got_t and got_cb
            print(('PASS' if ok else 'FAIL') + ' fill round-trip')
            fail |= (0 if ok else 1)
        finally:
            try:
                os.remove(fill_path)
            except OSError:
                pass
    else:
        print('SKIP fill round-trip (no fields)')

    jc = pymupdf.open(trans)
    for i in range(min(len(o), len(jc))):
        if page_unextractable(o[i]):
            nimg = len(o[i].get_images())
            print(f'FAIL page {i+1} no extractable text with visible content '
                  f'(images={nimg}, ink={ink(o[i])}). '
                  f'This looks scanned — OCR first; do not ship.')
            fail = 1
            continue
        do, dj = ink(o[i]), ink(jc[i])
        if do < INK_SKIP:
            print(f'SKIP page {i+1} ink ratio (original negligible ink: {do} px)')
            continue
        ratio = dj / max(do, 1)
        ok = min_ink <= ratio <= 3.0
        print(f'{"PASS" if ok else "FAIL"} page {i+1} ink ratio: {ratio:.2f}')
        fail |= (0 if ok else 1)

    # Two buckets, because "a Latin word survived" and "a sentence went
    # untranslated" are completely different findings and must not score alike.
    #
    #   RUNNING TEXT  - three or more consecutive source-script words. That is
    #                   an untranslated phrase ("please press the Clear This
    #                   Form button"), a real defect. Hard fail.
    #   ISOLATED      - one or two adjacent tokens. Overwhelmingly these are
    #                   things that SHOULD stay verbatim: official document and
    #                   form names (Schedule C, Form W-2, Form 1040), statutes,
    #                   brand and product names, other proper nouns. Reported
    #                   for review, never a failure - translating an agency's
    #                   form name is itself an error, since the reader has to
    #                   locate a document that carries that exact name.
    running, isolated = [], []
    for i in range(len(jc)):
        r, iso = scan_leaks(jc[i].get_text(), allow,
                            source_words=source_words, src_re=src_re)
        running.extend((i + 1, ph) for ph in r)
        isolated.extend((i + 1, w) for w in iso)

    if running:
        print(f'FAIL untranslated running text ({len(running)}):')
        for pg, ph in running[:10]:
            print(f'   p{pg}: {ph}')
        fail = 1
    else:
        print('PASS no untranslated running text')

    if isolated:
        uniq = sorted({w for _, w in isolated})
        print(f'REVIEW isolated source-script tokens ({len(uniq)}) - expected for '
              f'form names, statutes and proper nouns; confirm each is deliberate:')
        print('   ' + ', '.join(uniq[:20]))
    else:
        print('REVIEW isolated source-script tokens: none')

    if translations:
        with open(translations, encoding='utf-8') as f:
            conf = json.load(f)
        hay = '\n'.join(page_search_text(jc[i]) for i in range(len(jc)))
        blanks = empty_translation_targets(conf)
        if blanks:
            print(f'FAIL empty translation targets ({len(blanks)}):')
            for t in blanks[:30]:
                print(f'   {t.replace(chr(10), " ")[:80]}')
            fail = 1
        else:
            print('PASS no empty translation targets')
        targets = collect_translation_targets(conf)
        missing = missing_translation_targets(hay, targets)
        if missing:
            print(f'FAIL missing translation targets ({len(missing)}):')
            for t in missing[:30]:
                print(f'   {t.replace(chr(10), " ")[:80]}')
            fail = 1
        else:
            print('PASS authored translations present')

        leftover = leftover_button_captions(
            pushbutton_captions(o),
            pushbutton_captions(jc),
            hay,
            skip=conf.get('skip') or [],
        )
        if leftover:
            print(f'FAIL untranslated button captions ({len(leftover)}):')
            for name, cap in leftover[:20]:
                print(f'   {cap} ({name})')
            fail = 1
        else:
            print('PASS button captions')

        clipped = overflowing_button_captions(jc)
        if clipped:
            print(f'FAIL caption wider than widget ({len(clipped)}):')
            for name, cap in clipped[:20]:
                print(f'   {cap} ({name})')
            fail = 1
        else:
            print('PASS caption width')

        spans = collect_identifier_spans(o)
        missing_ids = missing_identifier_spans(
            hay, spans, allow_translate=conf.get('allow_translate') or [])
        if missing_ids:
            print(f'FAIL missing write/find/say identifiers ({len(missing_ids)}):')
            for t in missing_ids[:30]:
                print(f'   {t.replace(chr(10), " ")[:80]}')
            fail = 1
        else:
            print('PASS write/find/say identifiers')

    o.close()
    j.close()
    jc.close()
    return 1 if fail else 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    orig, trans = argv[0], argv[1]
    allow = [w for w in (_arg(argv, '--allow', '') or '').split(',') if w]
    t0 = time.perf_counter()
    rc = verify(
        orig, trans,
        fill_text=_arg(argv, '--fill-text', 'Test value 123'),
        allow=allow,
        min_ink=float(_arg(argv, '--min-ink', '0.4')),
        source_regex=_arg(argv, '--source-regex', None),
        source_words_from=_arg(argv, '--source-words-from', None),
        allow_extra_prefix=_arg(argv, '--allow-extra-prefix', None),
        translations=_arg(argv, '--translations', None),
    )
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
