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
                  A run that equals the ORIGINAL's /Title is kept, not
                  counted: the compliance notice names the form it
                  translates, in the source language, and the reader has
                  to find that form. So is a run equal to a multi-word
                  --allow entry, which matches a whole run and never its
                  words. A longer run that merely contains either is
                  still a leak; kept runs are printed as a note.
5. text layer     a page with visible ink or an embedded image but no
                  extractable text is treated as a scan and fails (scans are out of
                  scope; an OCR layer is refused by gate 11).
                  Ink ratio is skipped when the original has negligible ink,
                  instead of failing a pale/blank page with ratio 0.00.
6. placement      if --translations is given, every non-passthrough target
                  string (length >= 2) must appear in the output text
                  layer, character for character apart from wrapping
                  whitespace (a re-flowed merge wraps, so the layer has a
                  newline where the paragraph has a space). retypeset
                  canonicalizes /ToUnicode, so no NBSP or hyphen folding
                  is applied here any more.
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
17. shaped marks  with --translations: every target whose script needs
                  shaping (Arabic family, Indic, Thai, Lao, Khmer, Myanmar,
                  Tibetan) must appear in an /ActualText span. retypeset
                  marks every Story-engine run that way, so a shaped target
                  that is missing was drawn glyph by glyph. This is the
                  Indic check: a broken conjunct leaves no code-point tell,
                  but who drew the run does.
12. unshaped Arabic an output page whose Arabic letters are all isolated
                  presentation forms (three or more joining letters, no
                  initial or medial form) was drawn letter by letter and
                  FAILs. Reads the glyph forms, not /ActualText. Silent
                  when the page has no Arabic presentation forms.
18. conjunct shaping every embedded face on a page that draws a conjunct-
                  forming script (Devanagari, Bengali, Tamil, Khmer, Myanmar)
                  is probed: that script's cluster string, rendered off the
                  extracted font program glyph by glyph and again through
                  the Story engine, must lose glyphs (क्षत्रिय 8 -> 4). No
                  loss means the face has no usable GSUB and every conjunct
                  drawn with it is broken: FAIL. A face that lacks the probe
                  glyphs is REVIEW (cannot attest; prepare_font adds them).
                  Thai, Lao and Hebrew niqqud have no count tell and are
                  REVIEW, never PASS; Arabic stays with gate 12. Always
                  runs; silent when no such script is on the page.
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
16. document meta with --translations: /Lang must match the mapping's
                  "lang", a translated /Title and translated outline titles
                  must actually be in the output, and the output must not
                  carry the orphaned /StructTreeRoot (its tags describe
                  stripped text). No "lang" in the mapping is a REVIEW
                  line, not a failure.
15. canonical text the output text layer must report the code points
                  somebody actually wrote. NBSP, soft hyphen, U+2010/U+2011
                  and CJK Compatibility Ideographs that are in neither the
                  original nor the authored mapping are ToUnicode drift and
                  FAIL: the page looks right while the words in it cannot
                  be searched or copied. Always runs.

These gates catch structural failures. They do NOT catch visual defects —
after they pass you still render pages side-by-side and look at them.

Usage:
  python3 verify.py ORIGINAL.pdf TRANSLATED.pdf \
      [--fill-text "value in target script"] [--allow WORD,"Multi Word Name",...] \
      [--min-ink 0.4] [--source-regex "[A-Za-z]{4,}"] \
      [--source-words-from segments.json] [--allow-extra-prefix tr_] \
      [--translations translations.json] [--segments segments.json] \
      [--report verify_report.json] [--fail-on-review]
"""
import io
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from contextlib import redirect_stdout
from dataclasses import dataclass

import pymupdf

from .extract_segments import write_find_say_hits
from .strip_text import choice_exports, invisible_text_pages
from . import shaping_probe

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
# JIS X 4051 / W3C JLREQ ("Requirements for Japanese Text Layout", Appendix A
# character classes) line-breaking prohibitions, transcribed from those
# public references and from nothing else. Chinese layout (GB/T 15834)
# forbids the same punctuation at the same positions, so the gate judges
# every CJK line, not only Japanese ones. The Story engine breaks by UAX #14
# and never violates these (measured: dev/probes/cjk_kinsoku_probe.py); a
# target split by hand across source lines can.
#
# Characters that may not BEGIN a line:
KINSOKU_LINE_START = frozenset(
    # cl-02 closing brackets 」』）］｝〉》】〕〙〗’”｠ and half-width ｣
    '\u300d\u300f\uff09\uff3d\uff5d\u3009\u300b\u3011\u3015\u3019\u3017'
    '\u2019\u201d\uff60\uff63'
    # cl-03 hyphens ‐ 〜 ゠ – and the full-width tilde ～ Windows writes for 〜
    '\u2010\u301c\u30a0\u2013\uff5e'
    # cl-04 dividing punctuation ？！‼⁇⁈⁉
    '\uff1f\uff01\u203c\u2047\u2048\u2049'
    # cl-05 middle dots ・：；
    '\u30fb\uff1a\uff1b'
    # cl-06 full stops 。． and half-width ｡
    '\u3002\uff0e\uff61'
    # cl-07 commas 、， and half-width ､
    '\u3001\uff0c\uff64'
    # cl-09 iteration marks 々〻ゝゞヽヾ
    '\u3005\u303b\u309d\u309e\u30fd\u30fe'
    # cl-10 prolonged sound mark ー and half-width ｰ
    '\u30fc\uff70'
    # cl-11 small kana ぁぃぅぇぉっゃゅょゎゕゖ, ァィゥェォッャュョヮヵヶ, half-width ｧ..ｯ
    '\u3041\u3043\u3045\u3047\u3049\u3063\u3083\u3085\u3087\u308e\u3095\u3096'
    '\u30a1\u30a3\u30a5\u30a7\u30a9\u30c3\u30e3\u30e5\u30e7\u30ee\u30f5\u30f6'
    '\uff67\uff68\uff69\uff6a\uff6b\uff6c\uff6d\uff6e\uff6f'
)
# ... and that may not END one: cl-01 opening brackets 「『（［｛〈《【〔〘〖‘“｟
# and half-width ｢
KINSOKU_LINE_END = frozenset(
    '\u300c\u300e\uff08\uff3b\uff5b\u3008\u300a\u3010\u3014\u3018\u3016'
    '\u2018\u201c\uff5f\uff62'
)
SPACELESS_RUN_CHARS = 6
# Latin keeps today's 4-letter word floor; other scripts have short real words.
MIN_WORD_LETTERS = {'Latin': 4}


@dataclass(frozen=True)
class Finding:
    """Where a gate outcome points: a 1-based page or None, the thing it
    names (field, font, script, token, …) and the run or detail, untruncated."""
    page: int | None
    where: str
    text: str

    def to_dict(self):
        return {'page': self.page, 'where': self.where, 'text': self.text}


@dataclass(frozen=True)
class GateResult:
    """One named gate: status is PASS, FAIL, SKIP, or REVIEW."""
    name: str
    status: str
    message: str = ''
    findings: tuple = ()

    def to_dict(self):
        return {'name': self.name, 'status': self.status, 'message': self.message,
                'findings': [f.to_dict() for f in self.findings]}


# Every name a GateResult can carry, in the order the gates run. A gate
# that prints nothing for a job (no fields, no Arabic, no --translations)
# records nothing either: the verdict mirrors the console, line for line.
GATE_NAMES = (
    'field-parity', 'opt-export-parity', 'fill-roundtrip',
    'extractable-text', 'ink-ratio', 'visible-text', 'canonical-text',
    'arabic-letterforms', 'conjunct-shaping',
    'leak-scan', 'leak-running', 'leak-isolated',
    'empty-targets', 'placement', 'shaped-actualtext',
    'button-captions', 'caption-width', 'override-markers',
    'metadata', 'metadata-lang', 'scaled-runs', 'identifiers',
)


@dataclass(frozen=True)
class VerifyVerdict:
    """Structured result of the structural gates. Does not print or exit."""
    exit_code: int
    gates: tuple
    original: str = ''
    output: str = ''
    fail_on_review: bool = False

    @property
    def ok(self):
        return self.exit_code == 0

    def to_dict(self):
        from . import __version__
        return {'schema': 1, 'version': __version__,
                'original': self.original, 'output': self.output,
                'exit_code': self.exit_code,
                'fail_on_review': self.fail_on_review,
                'gates': [g.to_dict() for g in self.gates]}


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


# Fold table for comparisons where the SOURCE side can drift and we cannot
# rewrite it: identifier spans read out of the original, and authored values
# that are whitespace. MuPDF builds ToUnicode by reverse-mapping the font
# cmap, so a source PDF may report NBSP for space, U+00AD or U+2010/U+2011
# for hyphen, whatever the author typed (audit finding H4). Our OWN output no
# longer needs this: retypeset rewrites /ToUnicode to the authored code
# points and the canonical-text-layer gate fails what is left, so the
# placement gate compares without folding.
_PLACEMENT_FOLD = str.maketrans({
    '\xa0': ' ',
    '\u202f': ' ',
    '\u2007': ' ',
    '\u2010': '-',
    '\u2011': '-',
    '\u00ad': '-',
})


def normalize_ws_nbsp(text):
    """NBSP/figure spaces → ASCII space; U+2010/U+2011/U+00AD → ASCII hyphen.

    For comparisons against text read out of the ORIGINAL, whose drift is
    not ours to rewrite. Placement compares with normalize_ws instead.
    """
    if not text:
        return ''
    return text.translate(_PLACEMENT_FOLD)


# Wrapping whitespace only: newline, carriage return, tab, runs of ASCII
# spaces. Deliberately NOT NBSP or the other exotic spaces — drift is the
# canonical-text-layer gate's business, and folding it here is what used to
# hide it.
_WRAP_WS = re.compile(r'[ \t\r\n]+')


def normalize_ws(text):
    """Collapse wrapping whitespace; fold nothing else.

    A merge is re-flowed by the Story engine, so a paragraph that wraps
    comes back from get_text() with a newline where the authored string
    has a space. Comparing those verbatim fails a build whose paragraph is
    placed perfectly — the gate would be the bug. Every other character
    still has to match what was authored.
    """
    return _WRAP_WS.sub(' ', text or '').strip()


# Code points that a reverse-mapped ToUnicode reports for a glyph the author
# spelled with something else: NBSP for space, soft hyphen and U+2010/U+2011
# for '-', CJK Compatibility Ideographs for common kanji (立 as U+F9F7).
DRIFT_RANGES = (
    (0x00A0, 0x00A0), (0x00AD, 0x00AD), (0x202F, 0x202F), (0x2007, 0x2007),
    (0x2010, 0x2011), (0xF900, 0xFAFF), (0x2F800, 0x2FA1F),
    # Story-engine ligatures (row 24): U+FB01 when the font carries the
    # ligature's code point, U+007F when a subset dropped it. Either one
    # means "oficina" is not in the layer and nobody can search for it.
    (0x007F, 0x007F), (0xFB00, 0xFB06),
)


def drifted_characters(out_text, authored_text):
    """[(char, count)] drift-prone code points nobody authored.

    A character that is in the original, or in an authored string, is the
    author's business and passes. What is left came from the text layer
    itself, and means retypeset's /ToUnicode rewrite did not reach that
    font: the page looks right and every string in it is a character the
    reader cannot search for or copy.
    """
    ok = set(authored_text or '')
    counts = {}
    for ch in out_text or '':
        if ch in ok:
            continue
        o = ord(ch)
        if any(a <= o <= b for a, b in DRIFT_RANGES):
            counts[ch] = counts.get(ch, 0) + 1
    return sorted(counts.items())


# retypeset writes this beside its output: every run it shipped below
# source size, so the author can name them without re-running the build
# (row 25). Absent means a build from before it existed, not a pass.
SCALE_REPORT = 'scale_report.json'


def scale_report_for(judged):
    """The scale report beside `judged`, [] if empty, None if absent."""
    path = os.path.join(os.path.dirname(os.path.abspath(judged)),
                        SCALE_REPORT)
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, list) else None


# Same narrow inline markup retypeset accepts in a single-line target.
INLINE_TAGS = re.compile(r'</?(?:b|i|em|strong)\s*/?>', re.I)


def strip_inline_markup(text):
    return INLINE_TAGS.sub('', text or '')


def collect_translation_targets(conf, exclude_cores=None):
    """Authored strings that should land in get_text() (not skip / not passthrough).

    translations.json values are already the non-passthrough mapping. '‖' is a
    retypeset weight split, not a glyph, so each side is searched separately.
    Merges and overrides are also placed text.
    """
    skip = set(conf.get('skip') or [])
    exclude = set(exclude_cores or [])
    targets = []
    for core, tgt in (conf.get('translations') or {}).items():
        if core in skip or core in exclude or tgt is None:
            continue
        for part in strip_inline_markup(str(tgt)).split('‖'):
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
    # A compliance notice is placed text like any other (P7): if the author
    # wrote it and retypeset drew it, the gate wants it in the layer.
    for notice in conf.get('notices') or []:
        for part in str(notice.get('text') or '').split('‖'):
            if part.strip():
                targets.append(part.strip())
    return targets


def document_metadata_misses(odoc, jdoc, conf):
    """[(what, detail)] document-level strings the translation left behind.

    /Lang, /Title and the outline are not page text, so nothing in the
    strip-and-retypeset path touches them. They are what the window
    caption, the bookmarks pane and every screen reader read.
    """
    T = conf.get('translations') or {}
    misses = []

    want_lang = (conf.get('lang') or '').strip()
    try:
        got_lang = (jdoc.language or '').strip()
    except Exception:
        got_lang = ''
    if want_lang:
        if not got_lang or not want_lang.lower().startswith(got_lang.lower()):
            misses.append(('lang', f'translations.json asks for '
                                   f'"{want_lang}", output declares '
                                   f'"{got_lang or "nothing"}"'))

    otitle = ((odoc.metadata or {}).get('title') or '').strip()
    jtitle = ((jdoc.metadata or {}).get('title') or '').strip()
    if otitle and T.get(otitle) and jtitle == otitle:
        misses.append(('title', f'/Title is still the source string: '
                                f'{otitle[:60]}'))

    for entry in jdoc.get_toc(simple=True) or []:
        title = str(entry[1]) if len(entry) > 1 else ''
        if title and T.get(title):
            misses.append(('outline', f'bookmark still reads: {title[:60]}'))

    try:
        cat = jdoc.pdf_catalog()
        if cat and jdoc.xref_get_key(cat, 'StructTreeRoot')[0] != 'null':
            misses.append((
                'struct-tree',
                'the output still carries /StructTreeRoot; those tags '
                'describe text that was stripped, so assistive technology '
                'reads a structure that no longer matches the page'))
    except Exception:
        pass
    return misses


def _authored_text_is_empty(raw):
    """True when normalize + strip leaves nothing. Length-1 'Z' is not empty."""
    if raw is None:
        return False
    plain = strip_inline_markup(str(raw))
    return len(normalize_ws_nbsp(plain).strip()) == 0


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


# Scripts whose letters must be shaped before they are drawn. Same table
# retypeset uses to decide what goes through the Story engine.
_SHAPING_RANGES = (
    (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFC),
    (0x0700, 0x074F), (0x07C0, 0x07FF),
    (0x0900, 0x0DFF),
    (0x0E00, 0x0EFF), (0x0F00, 0x0FFF),
    (0x1000, 0x109F), (0x1780, 0x17FF),
)


def needs_shaping(text):
    for ch in text or '':
        o = ord(ch)
        for a, b in _SHAPING_RANGES:
            if a <= o <= b:
                return True
    return False


def unmarked_shaped_targets(actual_texts, targets):
    """Shaped-script targets that no /ActualText span carries.

    Arabic has a glyph-form tell — isolated presentation forms mean the
    run was drawn letter by letter. Devanagari and Thai have none: the
    shaper writes glyph ids, so a broken conjunct and a correct one look
    the same in the text layer. What IS deterministic is who drew the run.
    retypeset places every shaping-script run through the Story engine and
    marks it with /ActualText; a run that reached the page any other way
    was drawn glyph by glyph, and that is the defect. Cheaper and more
    certain than comparing renders against a reference.
    """
    hay = '\n'.join(actual_texts)
    missing, seen = [], set()
    for raw in targets:
        text = normalize_ws(raw)
        if len(text) < 2 or text in seen or not needs_shaping(text):
            continue
        seen.add(text)
        if text not in hay:
            missing.append(raw)
    return missing


def missing_translation_targets(page_text, targets):
    """Return targets of length ≥ 2 absent from the output text layer.

    Wrapping whitespace is collapsed on both sides, because a re-flowed
    merge wraps and the layer then holds a newline where the paragraph
    holds a space. Nothing else is folded: retypeset canonicalizes
    /ToUnicode to the authored code points, so an authored NBSP must land
    as an NBSP, and folding that here would hide exactly the drift the
    canonical-text-layer gate exists for.
    """
    hay = normalize_ws(page_text)
    missing = []
    seen = set()
    for raw in targets:
        nt = normalize_ws(raw)
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


def load_segments_file(translations_path, segments_path=None):
    """Whole segments.json: --segments, else the file beside the mapping."""
    path = segments_path
    if not path and translations_path:
        candidate = os.path.join(os.path.dirname(os.path.abspath(translations_path)),
                                 'segments.json')
        if os.path.isfile(candidate):
            path = candidate
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_segments_for(translations_path, segments_path=None):
    """segments.json segments for the override gate."""
    data = load_segments_file(translations_path, segments_path)
    if data is None:
        return None
    return data.get('segments') if isinstance(data, dict) else data


def document_only_cores(segfile):
    """Cores that are document metadata and never page text.

    The document /Title and the outline titles are cores, so from-cores
    scaffolds them and the author translates them — but they are drawn by
    the window caption and the bookmarks pane, not by a content stream.
    The placement gate must not demand them in the text layer.
    """
    if not isinstance(segfile, dict):
        return set()
    doc = segfile.get('document') or {}
    candidates = {(doc.get('title') or '').strip()}
    candidates.update(str(t).strip() for t in (doc.get('outline') or []))
    candidates.discard('')
    on_page = {s.get('core') for s in (segfile.get('segments') or [])}
    return {c for c in candidates if c not in on_page}


def _run_key(text, script='Latin'):
    """A run's form for keep-list comparison: letters only, lowercased.

    Spaceless scripts compare with whitespace removed. Quotes, commas and
    case around a quoted title must not matter; a missing or extra word
    must.

    Tokens below the branch's own word floor are dropped from BOTH sides
    (row 27). The scan cannot see them in a run — `FL` and `100` in
    `FL-100 Petition—Marriage/Domestic Partnership` are two letters and a
    number, so the run it builds is `Petition Marriage Domestic
    Partnership` — and a title key that still carried them could never
    equal it. A word the scan can see is still a word: a run missing one
    of those is not the title.
    """
    text = normalize_ws_nbsp(text).lower()
    if script in SPACELESS_SCRIPTS:
        return re.sub(r'\s+', '', text)
    minlen = MIN_WORD_LETTERS.get(script, 2)
    return ' '.join(w for w in re.findall(r"[^\W\d_]+", text)
                    if len(w) >= minlen)


def _kept(run, keep, kept, script='Latin'):
    """True when run equals a keep phrase (the original /Title, or a
    multi-word --allow entry). Records it in kept for the report."""
    if not keep:
        return False
    key = _run_key(run, script)
    if not key:
        return False
    for phrase in keep:
        if _run_key(phrase, script) == key:
            if kept is not None:
                kept.append(run.strip()[:70])
            return True
    return False


def scan_leaks(text, allow, source_words=None, src_re=None, script='Latin',
               keep=None, kept=None):
    """Split surviving source-script tokens into running vs isolated.

    script is the SOURCE document's script. When source_words is provided
    (same-script pairs), both buckets use THIS document's own source words so
    the translation itself is not flagged. Otherwise runs of the source
    script are the leaks: words for space-delimited scripts, character runs
    for spaceless ones. Latin behaviour is unchanged from before goal 15.
    """
    running, isolated = [], []
    if script and script != 'Latin':
        return _scan_leaks_script(text, allow, script, source_words, src_re,
                                  keep=keep, kept=kept)
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
                if _kept(' '.join(seq), keep, kept, script):
                    pass   # the quoted title, or an allowlisted phrase
                elif len(seq) >= 3:
                    running.append(' '.join(seq)[:70])
                else:
                    isolated.extend(seq)
                i = j
            else:
                i += 1
        return running, isolated

    for phrase in RUN.findall(text):
        if _kept(phrase, keep, kept, script):
            continue
        words = re.findall(r"[A-Za-z']+", phrase)
        if sum(1 for w in words if w.lower() not in allow) >= 3:
            running.append(phrase.strip()[:70])
    masked = RUN.sub(' ', text)
    if src_re is not None:
        for word in src_re.findall(masked):
            if word.lower() not in allow:
                isolated.append(word)
    return running, isolated


def _scan_leaks_script(text, allow, script, source_words=None, src_re=None,
                       keep=None, kept=None):
    """scan_leaks for a non-Latin source script."""
    running, isolated = [], []
    cls = script_class(script)
    if script in SPACELESS_SCRIPTS:
        for m in re.finditer(cls + '+', text):
            run = m.group(0)
            if run.lower() in allow or _kept(run, keep, kept, script):
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
                if _kept(' '.join(seq), keep, kept, script):
                    pass   # the quoted title, or an allowlisted phrase
                elif len(seq) >= 3:
                    running.append(' '.join(seq)[:70])
                else:
                    isolated.extend(seq)
                i = j
            else:
                i += 1
        return running, isolated
    run_re = re.compile(word + r'(?:\s+' + word + r'){2,}')
    for phrase in run_re.findall(text):
        if _kept(phrase, keep, kept, script):
            continue
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


def conjunct_shaping_report(doc):
    """(lines, status, findings) for gate 18: probe every embedded face that draws a
    conjunct-forming script in the output.

    The text layer cannot show a broken conjunct (the shaper writes glyph
    ids), but the face can be asked directly: extract the embedded font
    program, render the script's probe cluster off it glyph by glyph and
    through the Story engine, and compare the counts (shaping_probe). Each
    (script, font) pair is probed once and reported once with the pages it
    draws. status is FAIL if any probe failed, else REVIEW if anything could
    not be attested, else PASS, else None when no such script is present.
    """
    fonts = {}       # xref -> (name, ext, program bytes or None)
    judged = {}      # (script, xref) -> [ProbeResult, pages]
    unattested = {}  # script -> pages with no face carrying the probe
    reviews = {}     # script -> pages (blind or unmeasured scripts)
    for page in doc:
        scripts = shaping_probe.scripts_in(page_search_text(page))
        for script in sorted(scripts):
            if shaping_probe.review_reason(script):
                reviews.setdefault(script, []).append(page.number + 1)
                continue
            probe = shaping_probe.PROBE_FOR.get(script)
            if probe is None:
                continue
            attested = False
            for entry in page.get_fonts(full=True):
                xref = entry[0]
                if xref not in fonts:
                    try:
                        info = doc.extract_font(xref)
                        fonts[xref] = (info[0], info[1], info[3] or None)
                    except Exception:
                        fonts[xref] = (str(entry[3]), '', None)
                name, ext, program = fonts[xref]
                if not program:
                    continue
                key = (script, xref)
                if key not in judged:
                    try:
                        results = shaping_probe.probe_font_bytes(program, ext, [script])
                        result = results[0] if results else None
                    except Exception as exc:
                        result = shaping_probe.review_result(
                            script, f'could not load the embedded font {name}: {exc}')
                    judged[key] = [result, []]
                result, pages = judged[key]
                if result is None or result.status == 'SKIP':
                    continue
                attested = True
                pages.append(page.number + 1)
            if not attested:
                unattested.setdefault(script, []).append(page.number + 1)

    def pages_of(nums):
        return 'page ' + ', '.join(str(n) for n in sorted(set(nums)))

    lines, statuses, findings = [], [], []
    for (script, xref), (result, pages) in sorted(judged.items()):
        if result is None or result.status == 'SKIP' or not pages:
            continue
        line = f'{result.line()} [{pages_of(pages)}]'
        if result.status == 'FAIL':
            line += ' — every conjunct drawn with this face is broken; do not ship'
        lines.append(line)
        statuses.append(result.status)
        face = result.expected_font or fonts[xref][0]
        findings.extend(Finding(p, face, result.line()) for p in sorted(set(pages)))
    for script, pages in sorted(unattested.items()):
        probe = shaping_probe.PROBE_FOR[script]
        lines.append(f'REVIEW conjunct shaping {script}: cannot attest [{pages_of(pages)}]: '
                     f'no embedded face carries the probe "{probe.text}"; rebuild the subset '
                     f'with prepare_font.py, which adds the probe glyphs, or check a render '
                     f'with a reader of the script')
        statuses.append('REVIEW')
        findings.extend(Finding(p, script, f'cannot attest: no embedded face carries the probe "{probe.text}"')
                        for p in sorted(set(pages)))
    for script, pages in sorted(reviews.items()):
        reason = shaping_probe.review_reason(script)
        lines.append(f'REVIEW conjunct shaping {script}: {reason} [{pages_of(pages)}]')
        statuses.append('REVIEW')
        findings.extend(Finding(p, script, reason) for p in sorted(set(pages)))
    if 'FAIL' in statuses:
        status = 'FAIL'
    elif 'REVIEW' in statuses:
        status = 'REVIEW'
    elif 'PASS' in statuses:
        status = 'PASS'
    else:
        status = None
    return lines, status, findings


def _has_cjk(text):
    return any(script_of(ch) == 'CJK' for ch in text)


def kinsoku_report(doc):
    """(lines, status, findings) for gate 19: no drawn CJK line begins with a
    character JIS X 4051 / JLREQ forbids at line start, or ends with one it
    forbids at line end.

    Judged on the lines MuPDF reads back from each page, block by block, in
    every block that carries a CJK letter on some line. A line that begins
    with closing punctuation, a small kana or the prolonged sound mark is a
    violation only when a line of the same block sits above it — the break
    before it was a choice; a line that ends with an opening bracket only
    when one sits below it. A block's lone line is a label or one segment,
    not a break. Every line of a CJK block is judged, including one made
    only of punctuation — a bracket or full stop left alone by a hand split
    is the very artefact the gate exists to catch; a block with no CJK
    letter (Latin text with a curly quote) is not Japanese typography's
    business. status is FAIL if any line violates, PASS if lines were
    judged and none did, None when no page has a CJK block.
    """
    findings, judged = [], 0
    for page in doc:
        for block in page.get_text('dict').get('blocks', []):
            texts = []
            for ln in block.get('lines', []):
                text = ''.join(sp.get('text', '') for sp in ln.get('spans', ())).strip()
                if text:
                    texts.append(text)
            if not any(_has_cjk(t) for t in texts):
                continue
            last = len(texts) - 1
            for i, text in enumerate(texts):
                judged += 1
                if i < last and text[-1] in KINSOKU_LINE_END:
                    findings.append(Finding(page.number + 1, 'line-end', text))
                if i > 0 and text[0] in KINSOKU_LINE_START:
                    findings.append(Finding(page.number + 1, 'line-start', text))
    if not judged:
        return [], None, []
    if findings:
        lines = [f'FAIL kinsoku: {len(findings)} CJK line(s) break a line-breaking rule '
                 f'(JIS X 4051 / JLREQ): closing punctuation, a small kana or the prolonged '
                 f'sound mark begins a line, or an opening bracket ends one. Declare the '
                 f'paragraph as a merge instead of splitting the target by hand:']
        for f in findings[:20]:
            lines.append(f'   p{f.page} {f.where}: {f.text[:60]}')
        return lines, 'FAIL', findings
    return [f'PASS kinsoku: {judged} CJK line(s) break within the rules'], 'PASS', []


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


def _execute_verify(orig, trans, fill_text='Test value 123', allow=None, min_ink=0.4,
                    source_regex=None, source_words_from=None, allow_extra_prefix=None,
                    translations=None, segments=None, fail_on_review=False):
    """Run structural gates. Returns (exit_code, gates). Prints as it goes."""
    # A multi-word --allow entry is a phrase: it matches a whole run and
    # nothing else (row 20). Single words behave as before. Until now a
    # phrase was accepted and silently matched nothing.
    given = [a.strip() for a in (allow or []) if a and a.strip()]
    keep = {a for a in given if re.search(r'\s', a)}
    allow = set(a.lower() for a in given if a not in keep)

    o, j = pymupdf.open(orig), pymupdf.open(trans)
    # The compliance notice names the form it translates in the source
    # language; the reader has to find that form. The original's /Title,
    # quoted as one run, is therefore kept rather than counted.
    otitle_keep = ((o.metadata or {}).get('title') or '').strip()
    if otitle_keep:
        keep.add(otitle_keep)
    kept = []
    fail = 0
    gates = []

    def record(name, status, message='', findings=()):
        gates.append(GateResult(name=name, status=status, message=message,
                                findings=tuple(findings)))

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
    parity = []
    for label, bad in [('missing', missing), ('type-mismatch', mismatch),
                       ('unexpected-extra', extra)]:
        if bad:
            print(f'FAIL field {label}:', sorted(bad)[:10])
            fail = 1
            parity.extend(Finding(None, label, name) for name in sorted(bad))
    if not (missing or mismatch or extra):
        print('PASS field parity')
        record('field-parity', 'PASS')
    else:
        record('field-parity', 'FAIL', findings=parity)

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
        record('opt-export-parity', 'FAIL',
               f'{len(drifted)} choice field(s) changed',
               findings=[Finding(None, name, f'{oopt.get(name)} -> {jopt.get(name)}')
                         for name in drifted])
    elif oopt:
        print(f'PASS /Opt export parity ({len(oopt)} choice field(s))')
        record('opt-export-parity', 'PASS',
               f'{len(oopt)} choice field(s)')

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
            broken = []
            if not got_t:
                broken.append(Finding(None, ttarget, 'text value did not survive save and reopen'))
            if not got_cb:
                broken.append(Finding(None, cbtarget, 'checkbox did not survive save and reopen'))
            record('fill-roundtrip', 'PASS' if ok else 'FAIL', findings=broken)
        finally:
            try:
                os.remove(fill_path)
            except OSError:
                pass
    else:
        print('SKIP fill round-trip (no fields)')
        record('fill-roundtrip', 'SKIP', 'no fields')

    jc = pymupdf.open(trans)
    ink_status = None
    unextractable = False
    scans = []
    inks = []
    for i in range(min(len(o), len(jc))):
        if page_unextractable(o[i]):
            nimg = len(o[i].get_images())
            page_ink = ink(o[i])
            print(f'FAIL page {i+1} no extractable text with visible content '
                  f'(images={nimg}, ink={page_ink}). '
                  f'This looks scanned — scans are out of scope with or without an OCR layer; do not ship.')
            fail = 1
            unextractable = True
            scans.append(Finding(i + 1, 'page', f'images={nimg}, ink={page_ink} px'))
            continue
        do, dj = ink(o[i]), ink(jc[i])
        if do < INK_SKIP:
            print(f'SKIP page {i+1} ink ratio (original negligible ink: {do} px)')
            if ink_status is None:
                ink_status = 'SKIP'
            inks.append(Finding(i + 1, 'page', f'negligible ink: {do} px'))
            continue
        ratio = dj / max(do, 1)
        ok = min_ink <= ratio <= 3.0
        print(f'{"PASS" if ok else "FAIL"} page {i+1} ink ratio: {ratio:.2f}')
        fail |= (0 if ok else 1)
        if not ok:
            ink_status = 'FAIL'
        elif ink_status != 'FAIL':
            ink_status = 'PASS'
        inks.append(Finding(i + 1, 'page', f'{"PASS" if ok else "FAIL"} ink ratio {ratio:.2f}'))
    if unextractable:
        record('extractable-text', 'FAIL', findings=scans)
    if ink_status:
        record('ink-ratio', ink_status, findings=inks)

    invisible = invisible_text_pages(orig)
    for pno, fraction in invisible:
        print(f'FAIL page {pno+1} invisible text layer: stripping the text changes '
              f'{fraction:.1%} of its span area. This looks like an OCR\'d scan; the '
              f'words the reader sees are pixels. Do not ship.')
        fail = 1
    if not invisible:
        print('PASS text layer is visible')
        record('visible-text', 'PASS')
    else:
        record('visible-text', 'FAIL', findings=[
            Finding(pno + 1, 'page', f'stripping the text changes {fraction:.1%} of its span area')
            for pno, fraction in invisible])

    # Canonical text layer (audit H4/H5). Authored strings count as
    # deliberate; so does anything already in the original, whose own
    # drift we cannot rewrite.
    authored = o_text
    if translations:
        with open(translations, encoding='utf-8') as f:
            _conf = json.load(f)
        authored += '\n' + '\n'.join(collect_translation_targets(_conf))
    drift = drifted_characters(
        '\n'.join(page_search_text(jc[i]) for i in range(len(jc))), authored)
    if drift:
        print(f'FAIL text layer is not canonical ({len(drift)} character(s) '
              f'nobody authored — ToUnicode drift; the page looks right but '
              f'the words cannot be searched or copied):')
        for ch, n in drift[:10]:
            print(f'   U+{ord(ch):04X} {unicodedata.name(ch, "?")} x{n}')
        fail = 1
        record('canonical-text', 'FAIL', f'{len(drift)} character(s)', findings=[
            Finding(None, f'U+{ord(ch):04X}', f'{unicodedata.name(ch, "?")} x{n}')
            for ch, n in drift])
    else:
        print('PASS canonical text layer')
        record('canonical-text', 'PASS')

    unshaped, saw_arabic = unshaped_arabic_pages(jc)
    for pno, n in unshaped:
        print(f'FAIL page {pno+1} Arabic drawn unshaped: {n} joining letters in isolated '
              f'form and none connected. The run bypassed the Story engine; do not ship.')
        fail = 1
    if unshaped:
        record('arabic-letterforms', 'FAIL', f'{len(unshaped)} page(s)', findings=[
            Finding(pno + 1, 'page', f'{n} joining letters in isolated form, none connected')
            for pno, n in unshaped])
    elif saw_arabic:
        print('PASS Arabic letterforms joined')
        record('arabic-letterforms', 'PASS')

    shaping_lines, shaping_status, shaping_findings = conjunct_shaping_report(jc)
    for line in shaping_lines:
        print(line)
    if shaping_status == 'FAIL':
        fail = 1
    if shaping_status:
        record('conjunct-shaping', shaping_status, findings=shaping_findings)

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
        record('leak-scan', 'REVIEW',
               f'source and output share the spaceless {src_script} family',
               findings=[Finding(None, 'script', src_script)])
    else:
        for i in range(len(jc)):
            r, iso = scan_leaks(jc[i].get_text(), allow, source_words=source_words,
                                src_re=src_re, script=src_script,
                                keep=keep, kept=kept)
            running.extend((i + 1, ph) for ph in r)
            isolated.extend((i + 1, w) for w in iso)

    if kept:
        uniq = sorted(set(kept))
        print(f'note: {len(kept)} source-language run(s) kept as the original '
              f'/Title or an allowlisted phrase: ' + '; '.join(uniq[:5]))
    if running:
        print(f'FAIL untranslated running text ({len(running)}):')
        for pg, ph in running[:10]:
            print(f'   p{pg}: {ph}')
        fail = 1
        record('leak-running', 'FAIL', f'{len(running)}',
               findings=[Finding(pg, 'run', ph) for pg, ph in running])
    else:
        print('PASS no untranslated running text')
        record('leak-running', 'PASS')

    if isolated:
        uniq = sorted({w for _, w in isolated})
        print(f'REVIEW isolated source-script tokens ({len(uniq)}) - expected for '
              f'form names, statutes and proper nouns; confirm each is deliberate:')
        print('   ' + ', '.join(uniq[:20]))
        record('leak-isolated', 'REVIEW', f'{len(uniq)}',
               findings=[Finding(pg, 'token', w) for pg, w in sorted(set(isolated))])
    else:
        print('PASS isolated source-script tokens: none')
        record('leak-isolated', 'PASS', 'none')

    if translations:
        with open(translations, encoding='utf-8') as f:
            conf = json.load(f)
        segfile = load_segments_file(translations, segments)
        meta_cores = document_only_cores(segfile)
        hay = '\n'.join(page_search_text(jc[i]) for i in range(len(jc)))
        blanks = empty_translation_targets(conf)
        if blanks:
            print(f'FAIL empty translation targets ({len(blanks)}):')
            for t in blanks[:30]:
                print(f'   {t.replace(chr(10), " ")[:80]}')
            fail = 1
            record('empty-targets', 'FAIL', f'{len(blanks)}',
                   findings=[Finding(None, 'target', t) for t in blanks])
        else:
            print('PASS no empty translation targets')
            record('empty-targets', 'PASS')
        # /Title and outline titles are cores but not page text; the
        # document-metadata gate is what checks those landed.
        targets = collect_translation_targets(conf, exclude_cores=meta_cores)
        missing = missing_translation_targets(hay, targets)
        if missing:
            print(f'FAIL missing translation targets ({len(missing)}):')
            for t in missing[:30]:
                print(f'   {t.replace(chr(10), " ")[:80]}')
            fail = 1
            record('placement', 'FAIL', f'{len(missing)}',
                   findings=[Finding(None, 'target', t) for t in missing])
        else:
            print('PASS authored translations present')
            record('placement', 'PASS')

        marks = [ '\n'.join(extract_actualtext(jc[i])) for i in range(len(jc))]
        unmarked = unmarked_shaped_targets(marks, targets)
        if unmarked:
            print(f'FAIL shaped-script targets not drawn by the Story engine '
                  f'({len(unmarked)}): no /ActualText span carries them, so '
                  f'they were placed glyph by glyph — joining and conjuncts '
                  f'are broken:')
            for t in unmarked[:20]:
                print(f'   {t.replace(chr(10), " ")[:80]}')
            fail = 1
            record('shaped-actualtext', 'FAIL', f'{len(unmarked)}',
                   findings=[Finding(None, 'target', t) for t in unmarked])
        elif any(needs_shaping(t) for t in targets):
            print('PASS shaped-script targets carry /ActualText')
            record('shaped-actualtext', 'PASS')

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
            record('button-captions', 'FAIL', f'{len(leftover)}',
                   findings=[Finding(None, name, cap) for name, cap in leftover])
        else:
            print('PASS button captions')
            record('button-captions', 'PASS')

        clipped = overflowing_button_captions(jc)
        if clipped:
            print(f'FAIL caption wider than widget ({len(clipped)}):')
            for name, cap in clipped[:20]:
                print(f'   {cap} ({name})')
            fail = 1
            record('caption-width', 'FAIL', f'{len(clipped)}',
                   findings=[Finding(None, name, cap) for name, cap in clipped])
        else:
            print('PASS caption width')
            record('caption-width', 'PASS')

        segs = (segfile.get('segments')
                if isinstance(segfile, dict) else segfile)
        if segs is None:
            print('SKIP override marker gate (no segments.json beside the mapping; '
                  'pass --segments)')
            record('override-markers', 'SKIP', 'no segments.json')
        else:
            misses = override_marker_misses(conf, segs)
            if misses:
                print(f'FAIL override drops source marker or tail ({len(misses)}):')
                for contains, token in misses[:20]:
                    print(f'   "{contains}" is missing "{token}"')
                fail = 1
                record('override-markers', 'FAIL', f'{len(misses)}',
                       findings=[Finding(None, contains, token) for contains, token in misses])
            elif conf.get('overrides'):
                print('PASS override parts keep markers and tails')
                record('override-markers', 'PASS')

        meta_misses = document_metadata_misses(o, jc, conf)
        if meta_misses:
            print(f'FAIL document metadata ({len(meta_misses)}):')
            for what, detail in meta_misses[:10]:
                print(f'   [{what}] {detail}')
            fail = 1
            record('metadata', 'FAIL', ', '.join(what for what, _ in meta_misses),
                   findings=[Finding(None, what, detail) for what, detail in meta_misses])
        else:
            print('PASS document metadata')
            record('metadata', 'PASS')
        if not (conf.get('lang') or '').strip():
            print('REVIEW document metadata: translations.json has no "lang"; '
                  'the output still declares the source language to screen '
                  'readers and hyphenation')
            record('metadata-lang', 'REVIEW', 'translations.json has no "lang"',
                   findings=[Finding(None, 'lang', 'translations.json has no "lang"')])

        report = scale_report_for(trans)
        if report is None:
            print(f'SKIP scaled runs: no {SCALE_REPORT} beside the output '
                  f'(a build from before it was written)')
            record('scaled-runs', 'SKIP', f'no {SCALE_REPORT}')
        elif report:
            print(f'REVIEW scaled runs ({len(report)}) — ship them or reword '
                  f'them, and name them in the delivery:')
            # Computed once, tolerantly, so a malformed sidecar entry (a
            # non-numeric ratio, a missing/non-integer page) cannot crash
            # either the console line below or the finding it mirrors.
            scaled = []
            for r in report:
                p = r.get('page')
                try:
                    ratio = f'{float(r.get("ratio", 1)):.2f}x'
                except (TypeError, ValueError):
                    ratio = f'{r.get("ratio")}x'
                scaled.append(Finding(p + 1 if isinstance(p, int) else None, ratio,
                                      str(r.get('key') or '')))
            for r, finding in zip(report[:20], scaled[:20]):
                print(f'   p{r.get("page")} {finding.where}: '
                      f'{str(r.get("key") or "")[:60]}')
            if len(report) > 20:
                print(f'   ... {len(report) - 20} more in {SCALE_REPORT}')
            record('scaled-runs', 'REVIEW', f'{len(report)}', findings=scaled)
        else:
            print('PASS scaled runs: none, everything ships at source size')
            record('scaled-runs', 'PASS')

        spans = collect_identifier_spans(o)
        missing_ids = missing_identifier_spans(
            hay, spans, allow_translate=conf.get('allow_translate') or [])
        if missing_ids:
            print(f'FAIL missing write/find/say identifiers ({len(missing_ids)}):')
            for t in missing_ids[:30]:
                print(f'   {t.replace(chr(10), " ")[:80]}')
            fail = 1
            record('identifiers', 'FAIL', f'{len(missing_ids)}',
                   findings=[Finding(None, 'identifier', t) for t in missing_ids])
        else:
            print('PASS write/find/say identifiers')
            record('identifiers', 'PASS')

    o.close()
    j.close()
    jc.close()
    rc = 1 if fail else 0
    if fail_on_review and rc == 0:
        reviews = sum(1 for g in gates if g.status == 'REVIEW')
        if reviews:
            print(f'FAIL: {reviews} REVIEW line(s) with --fail-on-review')
            rc = 1
    return rc, gates


def run_verify(orig, trans, fill_text='Test value 123', allow=None, min_ink=0.4,
               source_regex=None, source_words_from=None, allow_extra_prefix=None,
               translations=None, segments=None, fail_on_review=False):
    """Run structural gates. Returns a VerifyVerdict; does not print or exit."""
    with redirect_stdout(io.StringIO()):
        rc, gates = _execute_verify(
            orig, trans, fill_text=fill_text, allow=allow, min_ink=min_ink,
            source_regex=source_regex, source_words_from=source_words_from,
            allow_extra_prefix=allow_extra_prefix, translations=translations,
            segments=segments, fail_on_review=fail_on_review)
    return _verdict(rc, gates, orig, trans, fail_on_review)


def _verdict(rc, gates, orig, trans, fail_on_review):
    """The verdict both entry points hand out: paths absolute, whatever the
    caller passed, so a report written from the library reads like one
    written by the CLI."""
    return VerifyVerdict(exit_code=rc, gates=tuple(gates),
                         original=os.path.abspath(orig), output=os.path.abspath(trans),
                         fail_on_review=fail_on_review)


def verify(orig, trans, fill_text='Test value 123', allow=None, min_ink=0.4,
           source_regex=None, source_words_from=None, allow_extra_prefix=None,
           translations=None, segments=None, fail_on_review=False):
    """Run structural gates. Returns 0 on pass, 1 on any failure."""
    rc, _ = _execute_verify(
        orig, trans, fill_text=fill_text, allow=allow, min_ink=min_ink,
        source_regex=source_regex, source_words_from=source_words_from,
        allow_extra_prefix=allow_extra_prefix, translations=translations,
        segments=segments, fail_on_review=fail_on_review)
    return rc


def write_report(verdict, path):
    """verdict.to_dict() as JSON at path; a failure is printed, never raised."""
    text = json.dumps(verdict.to_dict(), ensure_ascii=False, indent=1)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    except OSError as exc:
        print(f'  (could not write {path}: {exc})')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    orig, trans = argv[0], argv[1]
    allow = [w for w in (_arg(argv, '--allow', '') or '').split(',') if w]
    t0 = time.perf_counter()
    rc, gates = _execute_verify(
        orig, trans,
        fill_text=_arg(argv, '--fill-text', 'Test value 123'),
        allow=allow,
        min_ink=float(_arg(argv, '--min-ink', '0.4')),
        source_regex=_arg(argv, '--source-regex', None),
        source_words_from=_arg(argv, '--source-words-from', None),
        allow_extra_prefix=_arg(argv, '--allow-extra-prefix', None),
        translations=_arg(argv, '--translations', None),
        segments=_arg(argv, '--segments', None),
        fail_on_review='--fail-on-review' in argv,
    )
    report = _arg(argv, '--report', None)
    if report:
        write_report(_verdict(rc, gates, orig, trans, '--fail-on-review' in argv), report)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
