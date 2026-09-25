# -*- coding: utf-8 -*-
"""fontTools' instancer, run once per distinct input for a whole test run.

Instancing a CJK variable face takes 3 to 9 s, and the suite asked for the
same instance over and over: 33 calls for 14 distinct inputs, 134 s of a cold
run (R-51, docs/reviews/2026-09-25-r51-test-font-instances.md). A module opts
in with `setUpModule = _instancing.install` and
`tearDownModule = _instancing.uninstall`. What its tests exercise does not
change: prepare_font, han_forms and field_fonts still call the instancer, which
runs in full the first time an input is seen; a repeat gets a copy of that
first result.

Only a font that is still its file is reused: read into memory, as
`TTFont(path)` reads it, and every table it has read compiles back to the
file's bytes, so the table directory's checksums identify its content
exactly. Anything else, and any axis limit that is not a single value, goes
straight to the instancer. A reuse replaces only what the font is (its reader,
tables and glyph order); the caller's own settings on the TTFont, such as
recalcTimestamp, stay as a real call leaves them. The first call's result
has been saved once to keep a copy, so its bounding boxes and timestamp are
already recalculated in memory, as the caller's own save would do.
"""
import copy as _copy
import inspect
import io

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

_REAL = instancer.instantiateVariableFont
_SIGNATURE = inspect.signature(_REAL)
_results = {}
counts = {'run': 0, 'reused': 0}
# What a font is. Everything else on a TTFont is its caller's setting.
_CONTENT = ('reader', 'tables', 'glyphOrder', '_reverseGlyphOrderDict')


def _key(varfont, axis_limits, options):
    reader = getattr(varfont, 'reader', None)
    # A reader on an open file belongs to whoever opened it. A glyph order set
    # in memory, or a table read and changed, would make the file's checksums
    # describe another font. A table only read, as han_forms reads fvar,
    # compiles back to the file's own bytes.
    if (reader is None or not isinstance(getattr(reader, 'file', None), io.BytesIO)
            or 'glyphOrder' in vars(varfont)):
        return None
    try:
        for tag in list(varfont.tables):
            if tag not in reader or varfont.tables[tag].compile(varfont) != reader[tag]:
                return None
    except Exception:
        return None
    try:
        limits = tuple(sorted((tag, float(value)) for tag, value in dict(axis_limits).items()))
    except (TypeError, ValueError):
        return None
    directory = tuple(sorted((tag, entry.checkSum, entry.length)
                             for tag, entry in reader.tables.items()))
    return varfont.sfntVersion, directory, limits, tuple(sorted(options.items()))


def instantiate(*args, **kwargs):
    try:
        bound = _SIGNATURE.bind(*args, **kwargs)
        bound.apply_defaults()
        options = dict(bound.arguments)
        varfont, axis_limits = options.pop('varfont'), options.pop('axisLimits')
        inplace = options.pop('inplace')
    except (TypeError, KeyError):
        # Arguments this cannot read, or an instancer already wrapped by
        # something else: not reused.
        return _REAL(*args, **kwargs)
    key = _key(varfont, axis_limits, options)
    if key is None:
        return _REAL(*args, **kwargs)
    data = _results.get(key)
    if data is None:
        result = _REAL(*args, **kwargs)
        buffer = io.BytesIO()
        result.save(buffer)
        _results[key] = buffer.getvalue()
        counts['run'] += 1
        return result
    counts['reused'] += 1
    instance = TTFont(io.BytesIO(data))
    if inplace:
        # The font the caller holds becomes the instance; its settings stay.
        # Its old reader is left open, as a real call leaves it: over a
        # buffer, it may be the caller's own.
        _take_content(varfont, instance)
        return varfont
    # A real call returns a deep copy of the caller's font, settings included.
    settings = {name: value for name, value in vars(varfont).items() if name not in _CONTENT}
    vars(instance).update(_copy.deepcopy(settings))
    return instance


def _take_content(target, source):
    for name in _CONTENT:
        vars(target).pop(name, None)
        if name in vars(source):
            vars(target)[name] = vars(source)[name]


def install():
    instancer.instantiateVariableFont = instantiate


def uninstall():
    instancer.instantiateVariableFont = _REAL
