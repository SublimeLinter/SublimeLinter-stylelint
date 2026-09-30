import importlib
import json
import unittest

import sublime
from SublimeLinter.lint.linter import VirtualView


Linter = importlib.import_module('SublimeLinter-stylelint.linter').Stylelint


class TestColumns(unittest.TestCase):
    def test_issue_24_converts_both_json_endpoints(self):
        source = 'a {\n  content: "é😀"; color: red; margin: 0 !important\n}\n'
        positions = [(2, 26, 2, 29, 'color-named'), (2, 41, 2, 51, 'declaration-no-important')]
        self.assertDiagnostics(source, positions, [(1, 24, 'red'), (1, 39, '!important')])

    def test_multiline_range_uses_each_endpoints_source(self):
        self.assertDiagnostics('😀 red\né😀 blue', [(1, 4, 2, 9, 'rule')], [(0, 2, 'red\né😀 blue')])

    def test_ascii_range_is_unchanged(self):
        self.assertDiagnostics('a red;', [(1, 3, 1, 6, 'rule')], [(0, 2, 'red')])

    def assertDiagnostics(self, source, positions, expected):
        output = json.dumps([{'warnings': [
            {'line': line, 'column': col, 'endLine': end_line, 'endColumn': end_col,
             'rule': rule, 'severity': 'warning', 'text': 'problem (' + rule + ')'}
            for line, col, end_line, end_col, rule in positions
        ]}])
        linter = Linter(sublime.View(0), {})
        vv = VirtualView(source)
        matches = list(linter.find_errors(output))
        self.assertEqual(len(matches), len(expected))
        for match, (line, col, text) in zip(matches, expected):
            error = linter.process_match(match, vv)
            self.assertIsNotNone(error)
            begin = vv.full_line(line)[0] + col
            self.assertEqual({k: error[k] for k in ('line', 'start', 'region', 'offending_text')}, {
                'line': line, 'start': col, 'region': sublime.Region(begin, begin + len(text)),
                'offending_text': text,
            })
