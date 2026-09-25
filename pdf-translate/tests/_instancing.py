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

Only a font fresh from its file is reused: no table decompiled yet, so its
table directory's checksums identify its content exactly. Anything else, and
any axis limit that is not a single value, goes straight to the instancer.
"""
import inspect
import io

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

_REAL = instancer.instantiateVariableFont
_SIGNATURE = inspect.signature(_REAL)
_results = {}
counts = {'run': 0, 'reused': 0}


def _key(varfont, axis_limits, options):
    reader = getattr(varfont, 'reader', None)
    if reader is None or varfont.tables:
        return None
    try:
        limits = tuple(sorted((tag, float(value)) for tag, value in dict(axis_limits).items()))
    except (TypeError, ValueError):
        return None
    directory = tuple(sorted((tag, entry.checkSum, entry.length)
                             for tag, entry in reader.tables.items()))
    return varfont.sfntVersion, directory, limits, tuple(sorted(options.items()))


def instantiate(*args, **kwargs):
    bound = _SIGNATURE.bind(*args, **kwargs)
    bound.apply_defaults()
    options = dict(bound.arguments)
    varfont, axis_limits = options.pop('varfont'), options.pop('axisLimits')
    inplace = options.pop('inplace')
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
    copy = TTFont(io.BytesIO(data))
    if not inplace:
        return copy
    # In place, as the caller asked: the font it holds becomes the instance.
    varfont.close()
    varfont.__dict__.clear()
    varfont.__dict__.update(copy.__dict__)
    return varfont


def install():
    instancer.instantiateVariableFont = instantiate


def uninstall():
    instancer.instantiateVariableFont = _REAL
