"""R-50 evidence (docs/reviews/2026-09-25-r50-subset-before-instancing.md). Are two fonts' GPOS tables the same positioning, however they are encoded?

usage: dev/probes/r50_gpos_equal.py A.ttf B.ttf
For every feature: SinglePos values per glyph and PairPos values per glyph
pair (first-applying subtable wins, as a shaper applies them), and ChainContext
rules as sets of glyph sets with their nested lookups' effects. Extension
lookups are unwrapped. Zero adjustments count as absent.
"""
import sys
from fontTools.ttLib import TTFont

VR_FIELDS = ('XPlacement', 'YPlacement', 'XAdvance', 'YAdvance')


def vr(value):
    if value is None:
        return ()
    return tuple((f, getattr(value, f, 0) or 0) for f in VR_FIELDS if getattr(value, f, 0))


def subtables(lookup):
    for st in lookup.SubTable:
        if lookup.LookupType == 9:
            yield st.ExtensionLookupType, st.ExtSubTable
        else:
            yield lookup.LookupType, st


def single_effect(lookup):
    out = {}
    for kind, st in subtables(lookup):
        if kind != 1:
            continue
        glyphs = st.Coverage.glyphs
        for i, g in enumerate(glyphs):
            if g in out:
                continue
            value = st.Value if st.Format == 1 else st.Value[i]
            out[g] = vr(value)
    return frozenset((g, v) for g, v in out.items() if v)


def pair_effect(lookup, glyph_set):
    out = {}
    for kind, st in subtables(lookup):
        if kind != 2:
            continue
        first = st.Coverage.glyphs
        if st.Format == 1:
            for i, g1 in enumerate(first):
                for rec in st.PairSet[i].PairValueRecord:
                    out.setdefault((g1, rec.SecondGlyph), (vr(rec.Value1), vr(rec.Value2)))
        else:
            cd1, cd2 = st.ClassDef1.classDefs, st.ClassDef2.classDefs
            for g1 in first:
                c1 = cd1.get(g1, 0)
                for g2 in glyph_set:
                    rec = st.Class1Record[c1].Class2Record[cd2.get(g2, 0)]
                    out.setdefault((g1, g2), (vr(rec.Value1), vr(rec.Value2)))
    return frozenset((k, v) for k, v in out.items() if v != ((), ()))


def chain_effect(lookup, lookups, glyph_set):
    rules = set()
    for kind, st in subtables(lookup):
        if kind != 8:
            continue
        def nested(records):
            return tuple((r.SequenceIndex, effect(lookups[r.LookupListIndex], lookups, glyph_set))
                         for r in records)
        if st.Format == 3:
            rules.add((tuple(frozenset(c.glyphs) for c in st.BacktrackCoverage),
                       tuple(frozenset(c.glyphs) for c in st.InputCoverage),
                       tuple(frozenset(c.glyphs) for c in st.LookAheadCoverage),
                       nested(st.PosLookupRecord)))
        elif st.Format == 2:
            def members(cd, c):
                return frozenset(g for g in glyph_set if cd.classDefs.get(g, 0) == c)
            cov = set(st.Coverage.glyphs)
            for c0, crs in enumerate(st.ChainPosClassSet or []):
                if crs is None:
                    continue
                first = frozenset(members(st.InputClassDef, c0) & cov)
                for r in crs.ChainPosClassRule:
                    rules.add((tuple(members(st.BacktrackClassDef, c) for c in r.Backtrack),
                               (first,) + tuple(members(st.InputClassDef, c) for c in r.Input),
                               tuple(members(st.LookAheadClassDef, c) for c in r.LookAhead),
                               nested(r.PosLookupRecord)))
        else:
            for i, g0 in enumerate(st.Coverage.glyphs):
                for r in st.ChainPosRuleSet[i].ChainPosRule:
                    rules.add((tuple(frozenset([g]) for g in r.Backtrack),
                               (frozenset([g0]),) + tuple(frozenset([g]) for g in r.Input),
                               tuple(frozenset([g]) for g in r.LookAhead),
                               nested(r.PosLookupRecord)))
    return frozenset(rules)


def effect(lookup, lookups, glyph_set):
    kinds = {k for k, _ in subtables(lookup)}
    return (single_effect(lookup) if 1 in kinds else frozenset(),
            pair_effect(lookup, glyph_set) if 2 in kinds else frozenset(),
            chain_effect(lookup, lookups, glyph_set) if 8 in kinds else frozenset(),
            frozenset(kinds - {1, 2, 8}))


def features(font):
    g = font['GPOS'].table
    lookups = g.LookupList.Lookup
    glyph_set = font.getGlyphOrder()
    per_feature = {}
    for rec in g.FeatureList.FeatureRecord:
        per_feature.setdefault(rec.FeatureTag, set()).update(rec.Feature.LookupListIndex)
    return {tag: [effect(lookups[i], lookups, glyph_set) for i in sorted(idx)]
            for tag, idx in per_feature.items()}


a, b = TTFont(sys.argv[1]), TTFont(sys.argv[2])
fa, fb = features(a), features(b)
same = True
for tag in sorted(set(fa) | set(fb)):
    ea = set().union(*[e[0] | e[1] for e in fa.get(tag, [])]) if fa.get(tag) else set()
    eb = set().union(*[e[0] | e[1] for e in fb.get(tag, [])]) if fb.get(tag) else set()
    ca = set().union(*[e[2] for e in fa.get(tag, [])]) if fa.get(tag) else set()
    cb = set().union(*[e[2] for e in fb.get(tag, [])]) if fb.get(tag) else set()
    other_a = set().union(*[e[3] for e in fa.get(tag, [])]) if fa.get(tag) else set()
    ok = ea == eb and ca == cb and not other_a
    same &= ok
    print(f'{tag}: {"same" if ok else "DIFFERENT"}  single/pair entries {len(ea)} vs {len(eb)}, '
          f'context rules {len(ca)} vs {len(cb)}' + (f', unhandled lookup types {other_a}' if other_a else ''))
print('GPOS positioning identical:', same)
sys.exit(0 if same else 1)
