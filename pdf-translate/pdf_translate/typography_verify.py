"""Read actual final glyphs and font programs; a build report is never evidence."""
from contextlib import ExitStack
import io
import math
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
import pymupdf

from .mapping import refuse, role_name
from .typography import (_program_observation, _unsubset, field_identities,
                         observe_fonts, page_geometry, source_digest)
from .verify import Finding, GateResult
from .typography_content import inspect_content, later_paint_intersects, page_drawing


TOLERANCE = 0.05


class _Face:
    """A program actually loaded in this check, with normalized used-glyph data."""
    def __init__(self, data, stack):
        self.font = stack.enter_context(TTFont(io.BytesIO(data)))
        self.drawer = pymupdf.Font(fontbuffer=data)
        self.observed = _program_observation(data)
        self.glyphs = self.font.getGlyphSet()
        self.order = self.font.getGlyphOrder()
        self.units = self.font['head'].unitsPerEm
        self.cache = {}

    def glyph(self, gid):
        if gid not in self.cache:
            name = self.order[gid]
            pen = DecomposingRecordingPen(self.glyphs)
            self.glyphs[name].draw(pen)
            bounds = BoundsPen(self.glyphs)
            self.glyphs[name].draw(bounds)
            def normalize(value):
                if isinstance(value, (tuple, list)):
                    return tuple(normalize(item) for item in value)
                if isinstance(value, (int, float)):
                    return round(value / self.units, 7)
                return value
            advance = self.font['hmtx'].metrics[name][0] / self.units
            ink = None
            if bounds.bounds is not None:
                x0, y0, x1, y1 = bounds.bounds
                ink = (x0 / self.units, -y1 / self.units, x1 / self.units, -y0 / self.units)
            self.cache[gid] = ((normalize(pen.value), round(advance, 7)), ink)
        return self.cache[gid]


def _rgb(span):
    color = span['color']
    if len(color) == 1:
        return color * 3
    if len(color) == 3:
        return color
    if len(color) == 4:
        c, m, y, k = color
        return tuple(1 - min(1, v + k) for v in (c, m, y))
    return None


def _characters(traces):
    result = []
    for index, span in enumerate(traces):
        if span['type'] == 3 or span.get('opacity', 1) <= 0:
            continue
        for offset, (cp, gid, origin, bbox) in enumerate(span['chars']):
            result.append({'id': (index, offset), 'text': chr(cp) if cp >= 0 else '\ufffd',
                           'gid': gid, 'origin': origin, 'span': span, 'bbox': bbox})
    return result


def _subset_metadata_matches(actual, selected):
    """MuPDF drops post when subsetting; all surviving style evidence must agree.

    This exception applies only alongside exact used-glyph outline/advance checks.
    Missing or contradictory metadata in a complete font is still unresolved.
    """
    a, b = actual.font, selected.font
    if 'post' in a or 'fvar' in a or not all(t in a and t in b for t in ('OS/2', 'head')):
        return False
    return (a['head'].macStyle == b['head'].macStyle and
            all(getattr(a['OS/2'], name) == getattr(b['OS/2'], name)
                for name in ('sFamilyClass', 'usWeightClass', 'fsSelection')) and
            vars(a['OS/2'].panose) == vars(b['OS/2'].panose))


def inspect_output(original, final, document):
    """Attest only resolvable actual glyphs at each exact source occurrence."""
    if document is None or document.extraction is None:
        return GateResult('typography', 'REVIEW', 'cannot attest: mapping and extraction context are required')
    expected = document.extraction['typography']
    if source_digest(original) != expected['source_sha256']:
        refuse('stale-extraction', 'original PDF does not match the bound typography extraction')
    failures, reviews, owned, actual_boxes = [], [], {}, {}
    for issue in inspect_content(original, source=True).issues:
        reviews.append(Finding(issue.page + 1, 'source-paint', 'cannot attest source: ' + issue.detail))
    content = inspect_content(final)
    for issue in content.issues:
        collection = failures if issue.kind == 'transformed-text' else reviews
        collection.append(Finding(issue.page + 1, 'final-paint',
                                  ('' if collection is failures else 'cannot attest: ') + issue.detail))
    def finding(target, detail, uncertain=False):
        collection = reviews if uncertain else failures
        collection.append(Finding(target.page + 1, target.occurrence_id, detail))
    with ExitStack() as stack:
        source = stack.enter_context(pymupdf.open(original))
        output = stack.enter_context(pymupdf.open(final))
        if page_geometry(source) != expected['page_geometry']:
            refuse('stale-extraction', 'source page geometry differs from the bound extraction')
        if document.extraction['pages'] != list(range(source.page_count)):
            return GateResult('typography', 'REVIEW', 'cannot attest: extraction does not cover every source page')
        if page_geometry(output) != expected['page_geometry']:
            return GateResult('typography', 'FAIL', 'final page count, boxes or rotations differ from the source',
                              (Finding(None, 'pages', 'Every original page, including blank pages, must remain.'),))
        if field_identities(output) != expected['fields']:
            failures.append(Finding(None, 'fields', 'Final field identities or geometry differ from the source.'))
        observations = observe_fonts(output)
        try:
            drawings = {index: page_drawing(output, index) for index in range(output.page_count)}
        except (ValueError, RuntimeError):
            return GateResult('typography', 'REVIEW', 'cannot attest: unresolved page and annotation drawing order')
        traces = {index: _characters(drawing[0]) for index, drawing in drawings.items()}
        source_segments = {s['occurrence_id']: s for s in document.extraction['segments']}
        selected, embedded = {}, {}
        for target in document.targets:
            segment = source_segments[target.occurrence_id]
            first = segment['style_runs'][0]
            ox, baseline = first['origin']
            expected_text = ''.join(run.text for run in target.runs)
            row = sorted((c for c in traces[target.page] if abs(c['origin'][1] - baseline) <= TOLERANCE),
                         key=lambda c: (c['origin'][0], c['id']))
            candidates = []
            for index, char in enumerate(row):
                if abs(char['origin'][0] - ox) <= TOLERANCE:
                    match = row[index:index + len(expected_text)]
                    if ''.join(c['text'] for c in match) == expected_text:
                        candidates.append(match)
            if not candidates:
                finding(target, f'Missing, shifted or reordered target at the original baseline: {expected_text}')
                continue
            if len(candidates) != 1:
                finding(target, 'cannot attest: more than one drawn sequence matches this occurrence', True)
                continue
            chars = candidates[0]
            taken = owned.setdefault(target.page, set())
            if any(c['id'] in taken for c in chars):
                finding(target, 'cannot attest: drawn glyphs already belong to another occurrence', True)
                continue
            taken.update(c['id'] for c in chars)
            size = chars[0]['span']['size']
            scale = size / first['size']
            if not math.isfinite(scale) or scale <= 0 or scale > 1 + TOLERANCE / first['size']:
                finding(target, 'Final size is invalid or larger than the source.')
            elif scale < 0.7 - 0.00001:
                reason = document.allow_scale.get(target.occurrence_id)
                if reason:
                    finding(target, f'Approved below-floor scale {scale:.4f}: {reason}', True)
                else:
                    finding(target, f'Below-floor scale {scale:.4f} has no occurrence-specific permission.')
            wanted_color = tuple(((first['color'] >> shift) & 255) / 255 for shift in (16, 8, 0))
            cursor, char_index, drawn = ox, 0, []
            for run_index, run in enumerate(target.runs):
                key = (run.font_class, run.font_role)
                if key not in selected:
                    try:
                        selected[key] = _Face(Path(document.font_sets[run.font_class][run.font_role]).read_bytes(), stack)
                    except Exception:
                        selected[key] = None
                wanted = selected[key]
                if wanted is None:
                    finding(target, f'cannot attest run {run_index}: selected font program is unavailable', True)
                elif (wanted.observed['unresolved'] or wanted.observed['evidence'].get('variable')):
                    finding(target, f'cannot attest run {run_index}: selected font metadata is unresolved', True)
                elif (wanted.observed['class'], role_name(wanted.observed['bold'], wanted.observed['italic'])) != key:
                    finding(target, f'Selected font no longer matches {run.font_class}/{run.font_role}.')
                for text in run.text:
                    char = chars[char_index]
                    char_index += 1
                    span = char['span']
                    if (tuple(span['dir']) != (1, 0) or span.get('wmode', 0) != 0 or
                            abs(span['size'] - size) > TOLERANCE or
                            abs(char['origin'][0] - cursor) > TOLERANCE):
                        finding(target, f'Run {run_index} is not at its ordered, uniformly scaled position.')
                    color = _rgb(span)
                    if color is None:
                        finding(target, f'cannot attest run {run_index}: unsupported output color space', True)
                    elif any(abs(a - b) > 1 / 255 for a, b in zip(color, wanted_color)):
                        finding(target, f'Run {run_index} changed the source color.')
                    if span['type'] != 0 or span.get('opacity', 1) != 1:
                        finding(target, f'Run {run_index} uses unsupported stroke or opacity.')
                    font_ids = [font_id for font_id in observations['pages'][target.page]
                                if observations['fonts'][font_id]['xref'] in content.drawn_fonts.get(target.page, set()) and
                                _unsubset(span['font']) in
                                {_unsubset(name) for name in observations['fonts'][font_id]['aliases']}]
                    # Field-font embedding may add another resource for identical
                    # bytes. The actual glyph ID has the same meaning in each.
                    font_ids = list({observations['fonts'][f]['sha256'] or f: f for f in font_ids}.values())
                    actual = None
                    if len(font_ids) != 1:
                        finding(target, f'cannot attest run {run_index}: output font resource is ambiguous', True)
                    else:
                        font_id = font_ids[0]
                        obs = observations['fonts'][font_id]
                        if font_id not in embedded:
                            try:
                                program = output.extract_font(obs['xref'])[3]
                                embedded[font_id] = _Face(program, stack) if program else None
                            except Exception:
                                embedded[font_id] = None
                        actual = embedded[font_id]
                        if actual is None:
                            finding(target, f'cannot attest run {run_index}: no readable embedded font program', True)
                        if obs['unresolved'] or obs['class'] == 'unknown' or obs['bold'] is None or obs['italic'] is None:
                            if actual is None or wanted is None or not _subset_metadata_matches(actual, wanted):
                                finding(target, f'cannot attest run {run_index}: output font metadata is unresolved', True)
                        elif (obs['class'], role_name(obs['bold'], obs['italic'])) != key:
                            finding(target, f'Run {run_index} drew {obs["class"]}/{role_name(obs["bold"], obs["italic"])}; '
                                            f'expected {run.font_class}/{run.font_role}.')
                    if actual is not None:
                        try:
                            actual_shape, ink = actual.glyph(char['gid'])
                            if wanted is not None:
                                wanted_gid = wanted.drawer.has_glyph(ord(text), fallback=False)
                                if not wanted_gid or actual_shape != wanted.glyph(wanted_gid)[0]:
                                    finding(target, f'Run {run_index}: selected glyph outlines/advance differ for U+{ord(text):04X}.')
                            if ink is not None:
                                x, y = char['origin']
                                box = pymupdf.Rect(x + ink[0] * span['size'], y + ink[1] * span['size'],
                                                   x + ink[2] * span['size'], y + ink[3] * span['size'])
                                drawn.append(box)
                                if later_paint_intersects(drawings[target.page][1], span.get('seqno'), box,
                                                          drawings[target.page][2]):
                                    finding(target, f'cannot attest run {run_index}: later page paint may cover glyph outlines', True)
                                page_rect = output[target.page].rect + (-TOLERANCE, -TOLERANCE, TOLERANCE, TOLERANCE)
                                if not page_rect.contains(box):
                                    finding(target, f'Run {run_index}: glyph outline extends outside the page crop.')
                                for field in expected['fields']:
                                    if field['page'] == target.page and box.intersects(pymupdf.Rect(field['rect'])):
                                        finding(target, f'Run {run_index}: glyph outline overlaps source field {field["name"]}.')
                        except Exception:
                            finding(target, f'cannot attest run {run_index}: unsupported embedded glyph outlines', True)
                    if wanted is not None:
                        cursor += wanted.drawer.glyph_advance(ord(text)) * size
            if drawn:
                bounds = pymupdf.Rect(min(b.x0 for b in drawn), min(b.y0 for b in drawn),
                                      max(b.x1 for b in drawn), max(b.y1 for b in drawn))
                for other_id, other_bounds, other_boxes in actual_boxes.get(target.page, []):
                    if bounds.intersects(other_bounds) and any(a.intersects(b) for a in drawn for b in other_boxes):
                        finding(target, f'Actual glyph bounds overlap occurrence {other_id}.')
                actual_boxes.setdefault(target.page, []).append((target.occurrence_id, bounds, drawn))
        for page, chars in traces.items():
            extra = [c for c in chars if c['id'] not in owned.get(page, set()) and not c['text'].isspace()]
            if extra:
                failures.append(Finding(page + 1, 'unassigned-text',
                                        'Visible text is not assigned to exactly one occurrence: ' + ''.join(c['text'] for c in extra)))
        for resolution in document.source_font_resolutions:
            reviews.append(Finding(None, resolution['font_id'], 'Caller-authored source style resolution: ' + resolution['reason']))
    # Many letters may expose the same discrepancy; retain distinct findings once.
    failures = list(dict.fromkeys(failures))
    reviews = list(dict.fromkeys(reviews))
    status = 'FAIL' if failures else ('REVIEW' if reviews else 'PASS')
    message = ('Final occurrence typography differs from the authored source association.' if failures else
               'cannot attest fully; review the named evidence or authored exceptions.' if reviews else
               f'{len(document.targets)} occurrences checked from actual final glyphs and font programs.')
    return GateResult('typography', status, message, tuple(failures + reviews))
