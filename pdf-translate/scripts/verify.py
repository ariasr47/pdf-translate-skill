#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 5 of pdf-translate: automated gates. Run after EVERY build; exit 0 = pass.

1. field parity   set of (fully-qualified name, type) identical to original;
                  extra fields allowed only with --allow-extra-prefix
2. fill roundtrip a text value in the TARGET script + a checkbox survive
                  save/reopen (skipped if the PDF has no fields)
3. ink density    per-page dark-pixel ratio vs original within [--min-ink, hard
                  ceiling 3x] — catches invisible glyphs and blank regions
4. leak scan      keyed to the SOURCE document's script (detected from its
                  text layer; Han + kana count as one family, CJK). When the
                  output is in another script: three or more consecutive
                  source-script words (>= 4 letters for Latin, >= 2 otherwise),
                  or a run of six or more characters of a spaceless script,
                  is untranslated running text and fails; shorter leftovers
                  are reported for review only, because official form names
                  (Schedule C, Form W-2), statutes and proper nouns are
                  supposed to survive translation intact. When source and
                  output share a space-delimited script the scan uses the
                  document's own words (--source-words-from, or harvested
                  from the original automatically). A shared spaceless
                  family (zh->ja) gets one REVIEW line, not a gate.
5. text layer     a page with visible ink or an embedded image but no
                  extractable text is treated as a scan and fails (scans are out of
                  scope; an OCR layer is refused by gate 11).
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
11. invisible text a page of the ORIGINAL whose text is not what the reader
                  sees (stripping it changes under 3% of the text-span
                  area in pixels: an OCR layer over a scan, or text under
                  an image) FAILs. Always runs. Refusal, not a fix.
12. unshaped Arabic an output page whose Arabic letters are all isolated
                  presentation forms (three or more joining letters, no
                  initial or medial form) was drawn letter by letter and
                  FAILs. Reads the glyph forms, not /ActualText. Silent
                  when the page has no Arabic presentation forms.
13. override markers with --translations: an override replaces its whole
                  span, so its parts must keep the source segment's list
                  marker (d.) and tail ($). Needs segments.json: --segments
                  PATH, else the file beside translations.json; without
                  one the gate is SKIPped, not failed.
14. /Opt parity   a choice field's export values (the /Opt entry, or its
                  first element once entries are [export, display]) must be
                  byte-identical to the original's, in the same order.
                  Translating a dropdown changes the display half only;
                  changing an export breaks /V and everything submitted.
                  Always runs, like field parity. Silent with no choice
                  fields.

These gates catch structural failures. They do NOT catch visual defects —
after they pass you still render pages side-by-side and look at them.

Usage:
  python3 verify.py ORIGINAL.pdf TRANSLATED.pdf \
      [--fill-text "value in target script"] [--allow WORD,WORD,...] \
      [--min-ink 0.4] [--source-regex "[A-Za-z]{4,}"] \
      [--source-words-from segments.json] [--allow-extra-prefix tr_] \
      [--translations translations.json] [--segments segments.json]
"""
import json
import os
import re
import sys
import tempfile
import time
import unicodedata

import pymupdf

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
from extract_segments import write_find_say_hits  # noqa: E402
from strip_text import choice_exports, invisible_text_pages  # noqa: E402

# Unicode letter ranges per script (goal 15). A range table, not an ICU
# dependency: the scan only needs to tell the source script from the target
# one. Han, hiragana and katakana are one family because Japanese mixes them.
SCRIPT_RANGES = {
    'Latin': ((0x41, 0x5A), (0x61, 0x7A), (0xAA, 0xAA), (0xBA, 0xBA), (0xC0, 0x24F),
              (0x1E00, 0x1EFF), (0x2C60, 0x2C7F), (0xA720, 0xA7FF),
              (0xFF21, 0xFF3A), (0xFF41, 0xFF5A)),
    'Greek': ((0x370, 0x3FF), (0x1F00, 0x1FFF)),
    'Cyrillic': ((0x400, 0x52F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F)),
    'Armenian': ((0x530, 0x58F),),
    'Hebrew': ((0x590, 0x5FF), (0xFB1D, 0xFB4F)),
    'Arabic': ((0x600, 0x6FF), (0x750, 0x77F), (0x8A0, 0x8FF), (0xFB50, 0xFDFF),
               (0xFE70, 0xFEFF)),
    'Devanagari': ((0x900, 0x97F), (0xA8E0, 0xA8FF)),
    'Bengali': ((0x980, 0x9FF),),
    'Gurmukhi': ((0xA00, 0xA7F),),
    'Gujarati': ((0xA80, 0xAFF),),
    'Tamil': ((0xB80, 0xBFF),),
    'Telugu': ((0xC00, 0xC7F),),
    'Kannada': ((0xC80, 0xCFF),),
    'Malayalam': ((0xD00, 0xD7F),),
    'Sinhala': ((0xD80, 0xDFF),),
    'Thai': ((0xE00, 0xE7F),),
    'Lao': ((0xE80, 0xEFF),),
    'Tibetan': ((0xF00, 0xFFF),),
    'Myanmar': ((0x1000, 0x109F),),
    'Georgian': ((0x10A0, 0x10FF),),
    'Khmer': ((0x1780, 0x17FF),),
    'Hangul': ((0x1100, 0x11FF), (0x3130, 0x318F), (0xA960, 0xA97F), (0xAC00, 0xD7FF)),
    'CJK': ((0x3040, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
            (0xF900, 0xFAFF), (0xFF66, 0xFF9F), (0x20000, 0x2FA1F)),
}
# No word spaces: "three words" is approximated by six consecutive characters.
SPACELESS_SCRIPTS = {'CJK', 'Thai', 'Lao', 'Khmer', 'Myanmar', 'Tibetan'}
SPACELESS_RUN_CHARS = 6
# Latin keeps today's 4-letter word floor; other scripts have short real words.
MIN_WORD_LETTERS = {'Latin': 4}


def script_of(ch):
    """Script name for a letter; None for digits, punctuation, unknown scripts."""
    if not unicodedata.category(ch).startswith('L'):
        return None
    o = ord(ch)
    for name, ranges in SCRIPT_RANGES.items():
        for a, b in ranges:
            if a <= o <= b:
                return name
    return None


def dominant_script(text):
    """The script most of the letters in text belong to, or None if no letters."""
    counts = {}
    for ch in text or '':
        name = script_of(ch)
        if name:
            counts[name] = counts.get(name, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def _letter_bag(line):
    return tuple(sorted(ch for ch in line if unicodedata.category(ch).startswith('L')))


def target_script(out_text, source_text):
    """Dominant script of the output, ignoring lines that also occur in the source.

    Leaks are source text, so a large leftover would make the output's
    dominant script look like the source's and hide itself. Lines that occur
    in the source, verbatim or as the same bag of letters (the text layer of
    a re-typeset RTL line can come back in another order), are set aside
    before judging what the target is.
    """
    src_norm = ' '.join(normalize_ws_nbsp(source_text or '').split())
    src_bags = set()
    for line in (source_text or '').splitlines():
        bag = _letter_bag(line)
        if len(bag) >= 2:
            src_bags.add(bag)
    keep = []
    for line in (out_text or '').splitlines():
        norm = ' '.join(normalize_ws_nbsp(line).split())
        if not norm or norm in src_norm:
            continue
        bag = _letter_bag(line)
        if len(bag) >= 2 and bag in src_bags:
            continue
        keep.append(line)
    return dominant_script(chr(10).join(keep))


def script_class(script):
    """Regex character class matching one letter of the script."""
    parts = []
    for a, b in SCRIPT_RANGES[script]:
        parts.append(chr(a) if a == b else f'{chr(a)}-{chr(b)}')
    return '[' + ''.join(parts) + ']'


def source_words_from_text(text, allow, script='Latin'):
    """Unique source words of the given script from text (lowercased)."""
    if script == 'Latin':
        words = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", text or '')}
    else:
        minlen = MIN_WORD_LETTERS.get(script, 2)
        words = {w.lower() for w in re.findall(script_class(script) + '{%d,}' % minlen, text or '')}
    return words - set(allow)


WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")
RUN = re.compile(r"[A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*){2,}")
# Dark-pixel floor at 72 dpi. Below this, a page is "no ink" for the ratio
# gate. At-or-above, combined with empty get_text(), it is a scan suspect.
VISIBLE_INK = 50
INK_SKIP = 20


def _arg(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def source_words_from_segments(path, allow, script='Latin'):
    """Unique source words of the document's script from its segments."""
    with open(path, encoding='utf-8') as f:
        segs = json.load(f)['segments']
    return source_words_from_text('\n'.join(s['text'] for s in segs), allow, script)


# get_text() often remaps authored ASCII '-' to U+2010/U+2011 (e.g. "W-2"),
# and fonts whose cmap maps U+00AD to the hyphen glyph (Arial) report a soft
# hyphen. Spaces come back as NBSP the same way. One root cause: MuPDF builds
# ToUnicode by reverse-mapping the font cmap (audit finding H4).
_PLACEMENT_FOLD = str.maketrans({
    '\xa0': ' ',
    '\u202f': ' ',
    '\u2007': ' ',
    '\u2010': '-',
    '\u2011': '-',
    '\u00ad': '-',
})


def normalize_ws_nbsp(text):
    """NBSP/figure spaces → ASCII space; U+2010/U+2011/U+00AD → ASCII hyphen."""
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


def override_marker_misses(conf, segments):
    """[(contains, token)] for override parts that drop a source marker or tail.

    An override replaces the whole span, so the list marker ('d.') and the
    tail after the dot leaders ('$') only survive if some part carries them.
    Overrides whose `contains` matches no segment are not this gate's job.
    """
    by_page = {}
    for seg in segments or []:
        by_page.setdefault(seg.get('page'), []).append(seg)
    misses = []
    for ov in conf.get('overrides') or []:
        contains = ov.get('contains') or ''
        if not contains:
            continue
        parts_text = normalize_ws_nbsp(' '.join(
            str(part.get('text') or '') for part in (ov.get('parts') or [])))
        for seg in by_page.get(ov.get('page'), []):
            if contains not in seg.get('text', ''):
                continue
            for token in ((seg.get('marker') or '').strip(), (seg.get('tail') or '').strip()):
                if token and token not in parts_text and (contains, token) not in misses:
                    misses.append((contains, token))
    return misses


def load_segments_for(translations_path, segments_path=None):
    """segments.json for the override gate: --segments, else beside the mapping."""
    path = segments_path
    if not path and translations_path:
        candidate = os.path.join(os.path.dirname(os.path.abspath(translations_path)),
                                 'segments.json')
        if os.path.isfile(candidate):
            path = candidate
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('segments') if isinstance(data, dict) else data


def scan_leaks(text, allow, source_words=None, src_re=None, script='Latin'):
    """Split surviving source-script tokens into running vs isolated.

    script is the SOURCE document's script. When source_words is provided
    (same-script pairs), both buckets use THIS document's own source words so
    the translation itself is not flagged. Otherwise runs of the source
    script are the leaks: words for space-delimited scripts, character runs
    for spaceless ones. Latin behaviour is unchanged from before goal 15.
    """
    running, isolated = [], []
    if script and script != 'Latin':
        return _scan_leaks_script(text, allow, script, source_words, src_re)
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


def _scan_leaks_script(text, allow, script, source_words=None, src_re=None):
    """scan_leaks for a non-Latin source script."""
    running, isolated = [], []
    cls = script_class(script)
    if script in SPACELESS_SCRIPTS:
        for m in re.finditer(cls + '+', text):
            run = m.group(0)
            if run.lower() in allow:
                continue
            if len(run) >= SPACELESS_RUN_CHARS:
                running.append(run[:70])
            else:
                isolated.append(run)
        return running, isolated
    minlen = MIN_WORD_LETTERS.get(script, 2)
    word = cls + '{%d,}' % minlen
    if source_words:
        tokens = re.findall(cls + '+', text)
        i = 0
        while i < len(tokens):
            if tokens[i].lower() in source_words and tokens[i].lower() not in allow:
                j = i
                seq = []
                while j < len(tokens) and tokens[j].lower() in source_words \
                        and tokens[j].lower() not in allow:
                    seq.append(tokens[j])
                    j += 1
                if len(seq) >= 3:
                    running.append(' '.join(seq)[:70])
                else:
                    isolated.extend(seq)
                i = j
            else:
                i += 1
        return running, isolated
    run_re = re.compile(word + r'(?:\s+' + word + r'){2,}')
    for phrase in run_re.findall(text):
        words = re.findall(cls + '+', phrase)
        if sum(1 for w in words if w.lower() not in allow) >= 3:
            running.append(phrase.strip()[:70])
    masked = run_re.sub(' ', text)
    iso_re = src_re if src_re is not None else re.compile(word)
    for w in iso_re.findall(masked):
        if w.lower() not in allow:
            isolated.append(w)
    return running, isolated


# Arabic Presentation Forms-B: four-form groups (isolated, final, initial,
# medial) start at these code points. Initial and medial forms only exist
# when a shaper joined the letters; a run drawn letter by letter shows the
# isolated forms only.
_AR_GROUPS = (0xFE89, 0xFE8F, 0xFE95, 0xFE99, 0xFE9D, 0xFEA1, 0xFEA5, 0xFEB1,
              0xFEB5, 0xFEB9, 0xFEBD, 0xFEC1, 0xFEC5, 0xFEC9, 0xFECD, 0xFED1,
              0xFED5, 0xFED9, 0xFEDD, 0xFEE1, 0xFEE5, 0xFEE9, 0xFEF1)
ARABIC_ISOLATED_JOINING = set(_AR_GROUPS)
ARABIC_CONNECTED_FORMS = {b + 2 for b in _AR_GROUPS} | {b + 3 for b in _AR_GROUPS}


def unshaped_arabic_pages(doc):
    """([(page_index, isolated_count)], saw_forms) from the drawn glyph forms."""
    flags = pymupdf.TEXTFLAGS_RAWDICT | pymupdf.TEXT_IGNORE_ACTUALTEXT
    flagged, saw = [], False
    for page in doc:
        iso = conn = 0
        for block in page.get_text('rawdict', flags=flags)['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    for c in span['chars']:
                        o = ord(c['c'])
                        if o in ARABIC_CONNECTED_FORMS:
                            conn += 1
                        elif o in ARABIC_ISOLATED_JOINING:
                            iso += 1
        if iso or conn:
            saw = True
        if conn == 0 and iso >= 3:
            flagged.append((page.number, iso))
    return flagged, saw


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
           translations=None, segments=None):
    """Run structural gates. Returns 0 on pass, 1 on any failure."""
    allow = set(w.lower() for w in (allow or []) if w)

    o, j = pymupdf.open(orig), pymupdf.open(trans)
    fail = 0

    # Gate 4 is keyed to the source document's script, not to Latin.
    o_text = '\n'.join(p.get_text() or '' for p in o)
    j_text = '\n'.join(p.get_text() or '' for p in j)
    src_script = dominant_script(o_text) or 'Latin'
    out_script = target_script(j_text, o_text)
    print(f'leak scan: source script {src_script}; output script {out_script or "none"}')
    same_spaceless = src_script in SPACELESS_SCRIPTS and out_script == src_script
    source_words = None
    src_re = None
    if source_words_from:
        source_words = source_words_from_segments(source_words_from, allow, src_script)
        print(f'leak scan: {len(source_words)} source words from {source_words_from}')
    elif out_script == src_script and not same_spaceless:
        source_words = source_words_from_text(o_text, allow, src_script)
        print(f'leak scan: same script on both sides; using {len(source_words)} '
              f'document words from the original')
    if not source_words:
        source_words = None
        src_re = re.compile(source_regex or r'[A-Za-z]{4,}') if src_script == 'Latin' \
            else (re.compile(source_regex) if source_regex else None)

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

    # Widget text is translated by rewriting the DISPLAY half of each /Opt
    # entry. The export half is what /V holds and what a viewer submits;
    # a translated export silently breaks the form's data.
    oopt, jopt = choice_exports(orig), choice_exports(trans)
    drifted = sorted(name for name in set(oopt) | set(jopt)
                     if oopt.get(name) != jopt.get(name))
    if drifted:
        print(f'FAIL /Opt export values changed ({len(drifted)}):')
        for name in drifted[:10]:
            print(f'   {name}: {oopt.get(name)} -> {jopt.get(name)}')
        fail = 1
    elif oopt:
        print(f'PASS /Opt export parity ({len(oopt)} choice field(s))')

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
            got_t = (ttarget is None) or any(w.field_value == fill_text for p in t for w in p.widgets()
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
                  f'This looks scanned — scans are out of scope with or without an OCR layer; do not ship.')
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

    invisible = invisible_text_pages(orig)
    for pno, fraction in invisible:
        print(f'FAIL page {pno+1} invisible text layer: stripping the text changes '
              f'{fraction:.1%} of its span area. This looks like an OCR\'d scan; the '
              f'words the reader sees are pixels. Do not ship.')
        fail = 1
    if not invisible:
        print('PASS text layer is visible')

    unshaped, saw_arabic = unshaped_arabic_pages(jc)
    for pno, n in unshaped:
        print(f'FAIL page {pno+1} Arabic drawn unshaped: {n} joining letters in isolated '
              f'form and none connected. The run bypassed the Story engine; do not ship.')
        fail = 1
    if saw_arabic and not unshaped:
        print('PASS Arabic letterforms joined')

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
    if same_spaceless:
        print(f'REVIEW leak scan: source and output share the spaceless {src_script} '
              f'family; the scan cannot tell them apart. Rely on --translations and '
              f'the visual pass.')
    else:
        for i in range(len(jc)):
            r, iso = scan_leaks(jc[i].get_text(), allow, source_words=source_words,
                                src_re=src_re, script=src_script)
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

        segs = load_segments_for(translations, segments)
        if segs is None:
            print('SKIP override marker gate (no segments.json beside the mapping; '
                  'pass --segments)')
        else:
            misses = override_marker_misses(conf, segs)
            if misses:
                print(f'FAIL override drops source marker or tail ({len(misses)}):')
                for contains, token in misses[:20]:
                    print(f'   "{contains}" is missing "{token}"')
                fail = 1
            elif conf.get('overrides'):
                print('PASS override parts keep markers and tails')

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
        segments=_arg(argv, '--segments', None),
    )
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
