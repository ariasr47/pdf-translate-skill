#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The shipped documents state what the code does.

Each test locks one of the review's docs findings (docs/REVIEW-2026-09-24.md,
R-79, R-80, R-82 and R-83) against the code it describes, so the next change
to that code fails here instead of leaving the reference wrong.
"""
import ast
import importlib
import json
import re
import shlex
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PACKAGE = SKILL / 'pdf_translate'
SKILL_MD = SKILL / 'SKILL.md'
RETYPESET_MD = SKILL / 'references' / 'retypeset.md'


def _read(path):
    return path.read_text(encoding='utf-8')


def _section(text, heading):
    """The body under a `## heading`, up to the next `## `."""
    marker = f'\n## {heading}\n'
    if marker not in text:
        raise AssertionError(f'no "## {heading}" section')
    start = text.index(marker) + len(marker)
    end = text.find('\n## ', start)
    return text[start:] if end < 0 else text[start:end]


class _RefusalKinds(ast.NodeVisitor):
    """Every string key of a `refusals` dict literal in a module, outside the
    functions named in `skip`."""

    def __init__(self, skip):
        self.skip, self.kinds = skip, set()

    def visit_FunctionDef(self, node):
        if node.name not in self.skip:
            self.generic_visit(node)

    def _take(self, value):
        if isinstance(value, ast.Dict):
            self.kinds.update(k.value for k in value.keys if isinstance(k, ast.Constant))

    def visit_Call(self, node):
        for keyword in node.keywords:
            if keyword.arg == 'refusals':
                self._take(keyword.value)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if any(isinstance(t, ast.Name) and t.id == 'refusals' for t in node.targets):
            self._take(node.value)
        self.generic_visit(node)


class RetypesetReferenceTests(unittest.TestCase):
    """R-79: references/retypeset.md named two of the legacy build's refusals
    and showed the scale report as the bare list builds before v58 wrote."""

    def test_every_legacy_refusal_kind_is_in_the_failure_table(self):
        tree = ast.parse(_read(PACKAGE / 'retypeset.py'))
        # typography-1's own refusals all go through this one function, and
        # references/typography.md documents them.
        finder = _RefusalKinds(skip={'_typography_failure'})
        finder.visit(tree)
        self.assertGreaterEqual(len(finder.kinds), 9, finder.kinds)
        table = _section(_read(RETYPESET_MD), 'Every way a build fails')
        documented = set(re.findall(r'^\| `([a-z_]+)` \|', table, re.M))
        self.assertEqual(documented, finder.kinds)

    def test_the_scale_report_example_has_the_shape_a_build_writes(self):
        from pdf_translate.retypeset import SCALE_REPORT_SCHEMA, write_scale_report
        text = _section(_read(RETYPESET_MD), 'Every way a build fails')
        block = re.search(r'```json\n(.*?)\n```', text, re.S)
        self.assertIsNotNone(block, 'no json example of the scale report')
        example = json.loads(block.group(1))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'scale_report.json'
            self.assertTrue(write_scale_report([{'page': 0, 'key': 'k', 'ratio': 0.9}], path))
            written = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(set(example), set(written))
        self.assertEqual(example['schema'], SCALE_REPORT_SCHEMA)
        # The keys a legacy build gives each run (`consider_ratio` in retypeset).
        self.assertEqual(set(example['runs'][0]), {'page', 'key', 'ratio'})


class SkillMdTests(unittest.TestCase):
    """R-80: SKILL.md miscounted the identity facts, gave a test command that
    ran one module, and left a reference's reading note on the wrong entry."""

    NUMBERS = {'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7}

    def test_every_count_of_the_identity_facts_matches_the_list(self):
        text = _read(SKILL_MD)
        block = text[text.index('**Identity —'):]
        block = block[:block.index('\n\n', block.index('\n1. '))]
        listed = re.findall(r'^\d+\. \*\*(.+?)\*\*', block, re.M)
        self.assertEqual(len(listed), 5, listed)
        # The list's own heading ("Five facts:") and every "N identity facts".
        counts = (re.findall(r'\b(\w+)\s+facts:', block)
                  + re.findall(r'\b(\w+)\s+identity\s+facts\b', text))
        self.assertGreaterEqual(len(counts), 2, counts)
        for count in counts:
            self.assertEqual(self.NUMBERS.get(count.lower()), len(listed), count)

    def test_the_test_command_runs_every_test_module(self):
        text = _read(SKILL_MD)
        block = text[text.index('Regression tests'):]
        line = next(l for l in block.splitlines() if '-m unittest' in l)
        args = shlex.split(line)[3:]
        modules = {p.stem for p in (SKILL / 'tests').glob('test*.py')}
        if args[0] == 'discover':
            opts = dict(zip(args[1::2], args[2::2]))
            start = SKILL / opts.get('-s', '.')
            covered = {p.stem for p in start.glob(opts.get('-p', 'test*.py'))}
        else:
            covered = {a.rsplit('.', 1)[-1] for a in args if not a.startswith('-')}
        self.assertEqual(covered, modules)

    def test_the_recon_note_is_on_the_failure_modes_entry(self):
        references = _section(_read(SKILL_MD), 'References')
        entries = re.split(r'\n(?=- `)', references)
        noted = [e for e in entries if 'Read during recon' in e]
        self.assertEqual(len(noted), 1, noted)
        self.assertTrue(noted[0].startswith('- `references/failure-modes.md`'), noted[0])


class EvalsCommandTests(unittest.TestCase):
    """R-82: the evals README and three graders told the author to run
    `pipeline.py verify`, which pipeline does not have (exit 2)."""

    def test_every_pipeline_command_the_docs_name_exists(self):
        import inspect
        from pdf_translate import pipeline
        commands = set(re.findall(r"cmd == '([\w-]+)'", inspect.getsource(pipeline._main)))
        self.assertIn('rebuild', commands)
        docs = [SKILL_MD, *sorted((SKILL / 'references').glob('*.md')),
                *sorted((SKILL / 'evals').rglob('*.md'))]
        named = {}
        for doc in docs:
            for m in re.finditer(r'(?<![\w.-])pipeline\.py ([a-z][\w-]*)', _read(doc)):
                named.setdefault(m.group(1), set()).add(doc.relative_to(SKILL).as_posix())
        self.assertTrue(named)
        unknown = {c: sorted(where) for c, where in named.items() if c not in commands}
        self.assertEqual(unknown, {})


class CodeCommentTests(unittest.TestCase):
    """R-83: comments cited line numbers that had drifted, and verify's gate
    list gave the han-forms pass bar as a measurement."""

    def test_shipped_code_cites_no_line_numbers(self):
        # A line number is wrong after the next edit above it; a function name
        # is not. `:87`-style cites into the module itself count too.
        cite = re.compile(r'\b[\w./-]+\.py:\d+|\(:\d+\)')
        hits = []
        for path in sorted([*PACKAGE.rglob('*.py'), *(SKILL / 'scripts').glob('*.py')]):
            for number, line in enumerate(_read(path).splitlines(), 1):
                if cite.search(line):
                    hits.append(f'{path.relative_to(SKILL).as_posix()}:{number}: {line.strip()}')
        self.assertEqual(hits, [])

    def test_verify_states_the_han_forms_pass_bar(self):
        from pdf_translate.han_forms import OTHER_MIN, OWN_MAX
        doc = importlib.import_module('pdf_translate.verify').__doc__ or ''
        doc = ' '.join(doc.split())
        bar = f'Own reference <= {OWN_MAX:.2f} and the other >= {OTHER_MIN:.2f}'
        self.assertTrue(bar in doc, bar)


if __name__ == '__main__':
    unittest.main()
