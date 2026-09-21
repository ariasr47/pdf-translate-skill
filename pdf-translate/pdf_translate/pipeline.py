#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hot-path wrappers around the stage scripts.

The deterministic pipeline is a few seconds. Wall-clock is the translation
and visual loop. Use `rebuild` after the first extract instead of re-running
strip / extract / prepare_font / compare every round.

Usage:
  python3 pipeline.py init ORIGINAL.pdf --work DIR [--captions captions.json]
                                                  [--widget-text wt.json]
                                                  [--keep-encryption]
                                                  [--pages 1-10]
      strip + extract into DIR (stripped.pdf, segments.json,
      to_translate.json, widget_text.json). Run it once bare to get the
      widget_text.json scaffold, author the targets, then run it again with
      --widget-text to apply tooltips, dropdown labels and defaults.

  python3 pipeline.py from-cores --work DIR [--force]
      scaffold DIR/translations.json from DIR/to_translate.json cores.
      Values are JSON null (retypeset still FAILs until you author them).
      Refuses to overwrite unless --force. No model, no auto-merge.

  python3 pipeline.py propose-merges --work DIR [--accept] [--min-lines 2]
      turn the extractor's wrapped-paragraph candidates into ready-to-edit
      "merges" entries with html: null. Writes DIR/merges_proposed.json;
      --accept also folds them into DIR/translations.json. Nothing merges
      without this command, and a null html still FAILs retypeset until
      you author the paragraph. Paragraph mode for manuals and brochures.

  python3 pipeline.py merge-mappings OUT.json IN.json [IN.json ...]
      combine mappings authored per page range into one. Conflicting
      values for the same core are reported and nothing is written unless
      --last-wins.

  python3 pipeline.py qa --work DIR [--glossary glossary.csv] [--strict]
      linguistic QA on DIR/translations.json before you build: numbers and
      dates that moved, untranslated lines, inconsistent variants, brackets,
      punctuation parity, spacing, expansion band. Advisory; --strict makes
      warnings fail too.

  python3 pipeline.py rebuild --work DIR ORIGINAL.pdf OUT.pdf [verify flags...]
      retypeset DIR/stripped.pdf + DIR/segments.json + DIR/translations.json
      then verify ORIGINAL.pdf OUT.pdf with any extra verify flags

  python3 pipeline.py render ORIGINAL.pdf TRANSLATED.pdf renders/ [--dpi 110]

  python3 pipeline.py review --work DIR [--ingest review.json] [--notes NOTES.md]
      the second-reader step. Bare, it writes DIR/review_pairs.md (every
      core, merge, override and notice in one place) and
      DIR/review_prompt.md (the MQM prompt with this job's identity filled
      in). With --ingest it reads the reviser's verdict back, reports every
      finding, and appends the accepted terminology ones to
      DIR/glossary.csv so the next job of this class is gated on them.
      No model is called: the reviser is a person, or one you run yourself.

  python3 pipeline.py finish ORIGINAL.pdf OUT.pdf FONT.ttf FINAL.pdf HTML
                             --work DIR [--no-review]
      field_fonts + compare (delivery only). Refuses while DIR/review.json
      is absent or any finding is still open; --no-review delivers anyway
      and marks the delivery. Writes review_state.json beside FINAL.pdf on
      every run, refused or not.

  python3 pipeline.py bilingual ORIGINAL.pdf FINAL.pdf BOTH.pdf
      optional reading copy with source and target pages interleaved.
      Refuses a fillable input unless --reading-copy (duplicate field
      names fill together).
"""
import contextlib
import json
import logging
import os
import sys
import time
from dataclasses import replace

from .extract_segments import main as extract_main
from .field_fonts import field_fonts
from .compare import compare
from .render_pages import render_pages
from .retypeset import retypeset
from .strip_text import strip_text, WidgetTextError
from .bilingual import main as bilingual_main
from .qa_check import main as qa_main
from .review import run_review
from .verify import verify, main as verify_main

log = logging.getLogger(__name__)

# The new commands emit through the package logger rather than `print`, which
# is the convention E3 settles for every stage: a consumer that imports the
# library gets silence and a verdict, a consumer that runs the CLI gets the
# same lines on stdout. `main` attaches the handler; nothing else does.
#
# pipeline.py's existing 31 `print` sites are deliberately NOT converted here
# — they keep working untouched and are E3's job. The mixture is expected and
# temporary.
_console_depth = 0
_console_handler = None


@contextlib.contextmanager
def _console():
    """Attach one stdout handler to the package logger, re-entrantly.

    Re-entrant because `main` may be called from inside another `main` (the
    scripts/ wrappers, and the tests), and a second handler would double every
    line. Removed on the way out so importing the library never leaves a
    handler behind on a logger the caller owns.
    """
    global _console_depth, _console_handler
    pkg = logging.getLogger('pdf_translate')
    if _console_depth == 0:
        _console_handler = logging.StreamHandler(sys.stdout)
        _console_handler.setFormatter(logging.Formatter('%(message)s'))
        pkg.addHandler(_console_handler)
        pkg.setLevel(logging.INFO)
    _console_depth += 1
    try:
        yield
    finally:
        _console_depth -= 1
        if _console_depth == 0:
            pkg.removeHandler(_console_handler)
            _console_handler = None


def cmd_init(argv):
    src = argv[0]
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    os.makedirs(work, exist_ok=True)
    captions = None
    if '--captions' in argv:
        with open(argv[argv.index('--captions') + 1], encoding='utf-8') as f:
            captions = json.load(f)
    widget_text = None
    if '--widget-text' in argv:
        with open(argv[argv.index('--widget-text') + 1], encoding='utf-8') as f:
            widget_text = json.load(f)
    stripped = os.path.join(work, 'stripped.pdf')
    t0 = time.perf_counter()
    try:
        report = strip_text(src, stripped, captions=captions,
                            widget_text=widget_text,
                            keep_encryption='--keep-encryption' in argv)
    except WidgetTextError as exc:
        print(f'FAIL widget text: {exc}')
        return 2
    print(f'strip: xfa_removed={report.get("xfa_removed")} '
          f'dead_buttons={len(report.get("dead_buttons") or [])}')
    if report.get('perms_removed'):
        print(f'strip: deleted /Perms {report["perms_removed"]}')
    if report.get('certified'):
        print('WARNING: the source was CERTIFIED (/Perms /DocMDP); the '
              'translation is not. Say so when you deliver it.')
    if report.get('encryption', {}).get('encrypted') and not report.get('reencrypted'):
        print('NOTE: the source was encrypted; the output is not '
              '(--keep-encryption re-applies its permission bits).')
    leftover = report.get('leftover_text') or []
    if leftover:
        print(f'FAIL: page text survived strip on {len(leftover)} page(s); '
              f'{stripped} was not written:')
        for item in leftover:
            print(f"  p{item['page']}: {item['text']}")
        return 1
    extract_args = [src, '--outdir', work]
    if '--max-per-kind' in argv:
        extract_args += ['--max-per-kind', argv[argv.index('--max-per-kind') + 1]]
    if '--pages' in argv:
        extract_args += ['--pages', argv[argv.index('--pages') + 1]]
    rc = extract_main(extract_args)
    print(f'elapsed {time.perf_counter()-t0:.2f}s -> {work}')
    return rc


def scaffold_from_cores(to_translate_path, out_path, force=False):
    """Write translations.json with a null for every core. Returns 0, or 2."""
    if not os.path.isfile(to_translate_path):
        print(f'from-cores: missing {to_translate_path}')
        return 2
    if os.path.isfile(out_path) and not force:
        print(f'from-cores: {out_path} exists (pass --force to overwrite)')
        return 2
    with open(to_translate_path, encoding='utf-8') as f:
        data = json.load(f)
    cores = data.get('cores') or []
    translations = {}
    for c in cores:
        text = (c.get('text') if isinstance(c, dict) else None) or ''
        if text:
            translations[text] = None
    conf = {
        'fonts': {'regular': 'font-sub.ttf', 'bold': 'font-sub.ttf',
                  'italic': 'font-sub.ttf', 'bold_italic': 'font-sub.ttf'},
        # BCP-47 tag of the TARGET language, e.g. "es-MX". retypeset writes
        # it to /Lang and to dc:language; verify REVIEWs a mapping without
        # one, because the output otherwise tells screen readers it is
        # still in the source language.
        'lang': None,
        'translations': translations,
        'merges': [],
        'overrides': [],
        'center': [],
        'right': [],
        'skip': [],
        'allow_scale': [],
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(conf, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'from-cores: {len(translations)} cores -> {out_path} '
          f'(values are null — author them; do not ship)')
    return 0


def cmd_from_cores(argv):
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    force = '--force' in argv
    to_path = os.path.join(work, 'to_translate.json')
    out_path = os.path.join(work, 'translations.json')
    return scaffold_from_cores(to_path, out_path, force=force)


def propose_merges(work, accept=False, min_lines=2):
    """Shape the extractor's merge candidates as editable merges entries.

    A wrapped paragraph must be translated as one unit and re-flowed;
    translating each visual line on its own is how a brochure turns to
    fragments. Geometry can propose those groups but must never apply
    them — sibling list items share a column and read exactly like a
    wrapped paragraph. So: propose in bulk, accept in bulk, author each
    html. A proposal with html null still fails retypeset.
    """
    seg_path = os.path.join(work, 'segments.json')
    if not os.path.isfile(seg_path):
        print(f'propose-merges: missing {seg_path}')
        return 2
    with open(seg_path, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {s['id']: s for s in data.get('segments') or []}
    proposals = []
    for w in data.get('warnings') or []:
        ids = w.get('ids') or []
        # Candidates carry kind "merge-candidate" since row 22; a
        # segments.json from an earlier extractor has none. Both propose:
        # a stale work directory must not lose its paragraphs.
        if w.get('kind') not in (None, 'merge-candidate', 'narrow-column'):
            continue
        if len(ids) < min_lines:
            continue
        segs = [by_id[i] for i in ids if i in by_id]
        if len(segs) < min_lines:
            continue
        proposals.append({
            'page': w.get('page', segs[0]['page']),
            'lines': [s['text'].strip() for s in segs],
            'html': None,
            'align': 'left',
            # Null means "re-flow into the union of these lines". A rect
            # here is the author's decision and nothing else's: look at the
            # page first (row 26).
            'box': None,
            'why': w.get('why', ''),
        })
    out_path = os.path.join(work, 'merges_proposed.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'merges': proposals}, f, ensure_ascii=False, indent=1)
    print(f'propose-merges: {len(proposals)} candidate(s) -> {out_path} '
          f'(html is null — author each, or delete the entry; box is null '
          f'— set one only if you looked at the page)')
    if not accept:
        print('propose-merges: nothing changed. Re-run with --accept to fold '
              'these into translations.json.')
        return 0

    tr_path = os.path.join(work, 'translations.json')
    if not os.path.isfile(tr_path):
        print(f'propose-merges: missing {tr_path} (run from-cores first)')
        return 2
    with open(tr_path, encoding='utf-8') as f:
        conf = json.load(f)
    existing = {tuple(m.get('lines') or []) for m in conf.get('merges') or []}
    merges = list(conf.get('merges') or [])
    added = 0
    for p in proposals:
        key = tuple(p['lines'])
        if key in existing:
            continue
        merges.append({k: p[k] for k in ('page', 'lines', 'html', 'align')})
        existing.add(key)
        added += 1
    conf['merges'] = merges
    with open(tr_path, 'w', encoding='utf-8') as f:
        json.dump(conf, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'propose-merges: added {added} merge(s) to {tr_path}; author every '
          f'html (null still FAILs retypeset)')
    return 0


def cmd_propose_merges(argv):
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    min_lines = int(argv[argv.index('--min-lines') + 1]
                    if '--min-lines' in argv else 2)
    return propose_merges(work, accept='--accept' in argv,
                          min_lines=min_lines)


def merge_mappings(out_path, paths, last_wins=False):
    """Combine per-page-range mappings into one. Conflicts stop the write."""
    merged = None
    conflicts = []
    for path in paths:
        with open(path, encoding='utf-8') as f:
            conf = json.load(f)
        if merged is None:
            merged = json.loads(json.dumps(conf))
            continue
        for core, target in (conf.get('translations') or {}).items():
            have = merged['translations'].get(core, KeyError)
            if have is not KeyError and have != target and target is not None:
                if have is None or last_wins:
                    merged['translations'][core] = target
                else:
                    conflicts.append((core, have, target, path))
            elif have is KeyError:
                merged['translations'][core] = target
        for key in ('merges', 'overrides'):
            merged.setdefault(key, [])
            merged[key].extend(conf.get(key) or [])
        for key in ('center', 'right', 'skip', 'allow_scale',
                    'allow_translate'):
            if conf.get(key):
                merged[key] = sorted(set(merged.get(key) or [])
                                     | set(conf[key]))
    if merged is None:
        print('merge-mappings: no inputs')
        return 2
    if conflicts:
        print(f'merge-mappings: {len(conflicts)} conflicting core(s); '
              f'nothing written (pass --last-wins to take the later file):')
        for core, a, b, path in conflicts[:20]:
            print(f'  {core[:50]!r}: {a!r} vs {b!r} (from {path})')
        return 1
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
        f.write('\n')
    total = len(merged.get('translations') or {})
    print(f'merge-mappings: {total} cores -> {out_path}')
    return 0


def cmd_merge_mappings(argv):
    rest = [a for a in argv if a != '--last-wins']
    if len(rest) < 2:
        print('merge-mappings: OUT.json IN.json [IN.json ...]')
        return 2
    return merge_mappings(rest[0], rest[1:], last_wins='--last-wins' in argv)


def cmd_qa(argv):
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    rest = [a for a in argv if a not in ('--work', work)]
    tr = os.path.join(work, 'translations.json')
    segs = os.path.join(work, 'segments.json')
    if not os.path.isfile(tr):
        print(f'qa: missing {tr}')
        return 2
    args = [tr]
    if os.path.isfile(segs):
        args += ['--segments', segs]
    # --glossary resolved against the working directory while --segments was
    # joined to --work: an asymmetry that made the two-command story
    # (`review --ingest` writes work/glossary.csv, `qa --work … --glossary
    # glossary.csv` reads it back) need a path dance. A bare name that exists
    # under work now resolves there; an explicit path that resolves is left
    # exactly as the caller wrote it.
    if '--glossary' in rest:
        gi = rest.index('--glossary')
        if gi + 1 < len(rest):
            value = rest[gi + 1]
            joined = os.path.join(work, value)
            if not os.path.exists(value) and os.path.isfile(joined):
                rest = rest[:gi + 1] + [joined] + rest[gi + 2:]
    return qa_main(args + rest)


def cmd_rebuild(argv):
    if '--work' not in argv:
        print('rebuild requires --work DIR')
        return 2
    wi = argv.index('--work')
    work = argv[wi + 1]
    rest = argv[:wi] + argv[wi + 2:]
    if len(rest) < 2:
        print('rebuild: ORIGINAL.pdf OUT.pdf [verify flags...]')
        return 2
    orig, out, extra = rest[0], rest[1], rest[2:]
    orig = os.path.abspath(orig)
    out = os.path.abspath(out)
    work = os.path.abspath(work)
    stripped = os.path.join(work, 'stripped.pdf')
    segs = os.path.join(work, 'segments.json')
    tr = os.path.join(work, 'translations.json')
    t0 = time.perf_counter()
    rc = retypeset(stripped, segs, tr, out)
    if rc != 0:
        print(f'elapsed {time.perf_counter()-t0:.2f}s (retypeset failed)')
        return rc
    # Retypeset resolves font paths beside the mapping. Leave the caller's
    # directory intact so all command-line verification paths keep meaning.
    if '--report' not in extra:
        extra = extra + ['--report', os.path.join(work, 'verify_report.json')]
    rc = verify_main([orig, out] + extra)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return rc


def cmd_render(argv):
    dpi = int(argv[argv.index('--dpi') + 1]) if '--dpi' in argv else 110
    orig, trans, outdir = argv[0], argv[1], argv[2]
    t0 = time.perf_counter()
    render_pages(orig, trans, outdir, dpi=dpi)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return 0


def _finding_line(severity, kind, core, detail):
    """qa_check.main's column shape (qa_check.py:386), reused verbatim so a
    reader who knows one command can read the other."""
    return f'{severity:5} {kind:13} {core[:48]!r}: {detail}'


def cmd_review(argv):
    if '--work' not in argv:
        log.info('review requires --work DIR')
        return 2
    work = argv[argv.index('--work') + 1]
    ingest = argv[argv.index('--ingest') + 1] if '--ingest' in argv else None
    notes = argv[argv.index('--notes') + 1] if '--notes' in argv else None

    t0 = time.perf_counter()
    verdict = run_review(work, ingest=ingest, notes=notes)
    for err in verdict.errors:
        log.info(f'review: {err}')
    if verdict.errors and not verdict.findings:
        log.info(f'elapsed {time.perf_counter()-t0:.2f}s')
        return verdict.exit_code

    tr_path = os.path.join(work, 'translations.json')
    if os.path.isfile(tr_path):
        with open(tr_path, encoding='utf-8-sig') as f:
            tr = json.load(f)
        notices = len(tr.get('notices') or [])
        log.info(f'review: {len(tr.get("translations") or {})} cores, '
                 f'{len(tr.get("merges") or [])} merges, '
                 f'{len(tr.get("overrides") or [])} overrides, '
                 f'{notices} notice{"" if notices == 1 else "s"}')
    for path in verdict.wrote:
        log.info(f'review: wrote {path}')

    if not verdict.present:
        log.info('review: no review.json yet. finish will refuse.')
    else:
        who = verdict.reviewer or {}
        qualified = ('qualified in pair' if who.get('qualified_in_pair')
                     else 'not qualified in pair')
        log.info(f'review: reviewer {who.get("name", "?")} '
                 f'({who.get("kind", "?")}, {qualified})')
        counts = verdict.counts
        log.info(f'review: {len(verdict.findings)} finding(s) — '
                 f'{counts["critical"]} critical, {counts["major"]} major, '
                 f'{counts["minor"]} minor')
        log.info(f'review: {counts["accepted"]} accepted, '
                 f'{counts["rejected"]} rejected, {counts["open"]} open')
        for core, note, resolved in verdict.migrations:
            log.info(f'review: migrated resolution {note[:60]!r} → '
                     f'{resolved}; prose kept in resolution_note')
        for f in verdict.open_findings:
            log.info(_finding_line('OPEN', f.category, f.core, f.detail))
        if verdict.termbase_added:
            log.info(f'review: {len(verdict.termbase_added)} accepted '
                     f'terminology finding(s) → '
                     f'{os.path.join(work, "glossary.csv")}')
        if verdict.termbase_skipped:
            log.info(f'review: {len(verdict.termbase_skipped)} skipped — no '
                     f'term named; add "term" and "term_target"')
        for term, existing, new in verdict.conflicts:
            log.info(f'review: CONFLICT {term!r} is already {existing!r}; '
                     f'{new!r} was not written')
        if verdict.open_findings:
            log.info(f'review: {len(verdict.open_findings)} open finding(s). '
                     f'finish will refuse until each is accepted or rejected.')
    log.info(f'elapsed {time.perf_counter()-t0:.2f}s')
    return verdict.exit_code


def cmd_finish(argv):
    # --work and --no-review come out of argv before the five positionals,
    # exactly as cmd_rebuild does.
    no_review = '--no-review' in argv
    argv = [a for a in argv if a != '--no-review']
    work = None
    if '--work' in argv:
        wi = argv.index('--work')
        work = argv[wi + 1]
        argv = argv[:wi] + argv[wi + 2:]
    if len(argv) < 5:
        log.info('finish: ORIGINAL.pdf OUT.pdf FONT.ttf FINAL.pdf HTML '
                 '--work DIR [--no-review]')
        return 2
    orig, out, font, final, html = argv[0], argv[1], argv[2], argv[3], argv[4]

    if work is None:
        # Ruling 1: inferring the work directory from FINAL.pdf was rejected
        # — the FL-150 delivery went to Downloads/ while the job lived
        # elsewhere, so the gate would refuse a reviewed job and be switched
        # off. The flag is explicit or there is no gate.
        log.info('finish: --work DIR is required — it is where review.json '
                 'lives, and finish cannot check a review it cannot find.')
        return 2

    t0 = time.perf_counter()
    # Read-only: packaging never rewrites the reviser's inputs, and never
    # appends to the termbase behind `review --ingest`'s back.
    verdict = run_review(work, ingest='review.json', generate=False)
    if no_review:
        verdict = replace(verdict, no_review=True)

    if verdict.blocks_delivery and not no_review:
        if not verdict.present:
            log.info(f'finish: no {os.path.join(work, "review.json")} — no '
                     f'second reader has checked this translation.')
            log.info(f'finish: run `pipeline.py review --work {work}`, have '
                     f'it reviewed, then `review --work {work} --ingest '
                     f'review.json`.')
        else:
            log.info(f'finish: {len(verdict.open_findings)} finding(s) are '
                     f'still open; each must be accepted or rejected.')
            for f in verdict.open_findings:
                log.info(_finding_line('OPEN', f.category, f.core, f.detail))
        log.info('finish: --no-review delivers anyway and marks the delivery.')
        _write_review_state(final, verdict)
        log.info(f'elapsed {time.perf_counter()-t0:.2f}s')
        return 2

    if verdict.review_line:
        log.info(verdict.review_line)

    rc = field_fonts(out, font, final)
    if rc != 0:
        _write_review_state(final, verdict)
        return rc
    compare(orig, final, html)
    _write_review_state(final, verdict)
    log.info(f'elapsed {time.perf_counter()-t0:.2f}s')
    return 0


def _write_review_state(final, verdict):
    """The record beside the delivery, written on EVERY run, refused or not.

    R5 says a non-build stage never withholds a document, so for the product
    the load-bearing part of this loop is the record, not the refusal: a
    consumer that never reads stdout can still surface the REVIEW line.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(final)),
                        'review_state.json')
    try:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(verdict.to_dict(), f, ensure_ascii=False, indent=1)
            f.write('\n')
    except OSError as exc:
        log.info(f'finish: (could not write {path}: {exc})')


def main(argv=None):
    with _console():
        return _main(argv)


def _main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == 'review':
        return cmd_review(rest)
    if cmd == 'init':
        return cmd_init(rest)
    if cmd == 'from-cores':
        return cmd_from_cores(rest)
    if cmd == 'propose-merges':
        return cmd_propose_merges(rest)
    if cmd == 'merge-mappings':
        return cmd_merge_mappings(rest)
    if cmd == 'qa':
        return cmd_qa(rest)
    if cmd == 'rebuild':
        return cmd_rebuild(rest)
    if cmd == 'render':
        return cmd_render(rest)
    if cmd == 'finish':
        return cmd_finish(rest)
    if cmd == 'bilingual':
        return bilingual_main(rest)
    print('unknown command', cmd)
    print(__doc__)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
