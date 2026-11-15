"""Invented source references, retained lexemes and shared adapter behavior."""

from copy import deepcopy
import csv
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ravel.engine import csv_text, generate, preview_rows, run_metadata
from ravel.recipe import MAX_BYTES, ValidationError, dumps, loads
from ravel.sample import assumption_origin, parse_csv, profile
from ravel.workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'examples/sample-assisted'


def reference(mode='new', count=1000, confirmed=True):
    return profile((FIXTURES / 'ten-rows.csv').read_bytes(), mode=mode, count=count,
                   confirm_identifiers=confirmed)


class SampleTests(unittest.TestCase):
    def test_profile_matches_independent_arithmetic(self):
        recipe = reference()
        identity, length, material = recipe['table']['fields']
        self.assertEqual((identity['kind'], identity['start']), ('id', 11))
        self.assertEqual(recipe['sample']['identifiers'], ['sample_0'])
        self.assertEqual((length['minimum'], length['maximum'], length['places'], length['missing_probability']),
                         ('9.8', '12.2', 1, '0.2'))
        self.assertEqual(material['values'], ['A', 'B'])
        self.assertEqual(list(map(Decimal, material['probabilities'])), [Decimal('.6'), Decimal('.4')])
        self.assertEqual(assumption_origin(recipe, 'sample_1', 'minimum'), 'Sample')
        length['minimum'] = '10.0'
        self.assertEqual(assumption_origin(recipe, 'sample_1', 'minimum'), 'Edited')

    def test_both_thousand_row_modes_and_source_binding_round_trip(self):
        original = (FIXTURES / 'ten-rows.csv').read_bytes()
        source = list(csv.reader(StringIO(original.decode())))[1:]
        for mode, retained, generated in [('new', 0, 1000), ('extend', 10, 990)]:
            with self.subTest(mode=mode):
                recipe = reference(mode)
                saved = dumps(recipe)
                self.assertEqual(loads(saved), recipe)
                result = generate(loads(saved))
                self.assertEqual(len(result.rows), 1000)
                self.assertEqual(result.headers, ('sample_id', 'length_mm', 'material', 'row_origin'))
                self.assertEqual(preview_rows(result, retained), [row + ['retained'] for row in source[:retained]])
                self.assertEqual([row[-1] for row in result.rows], ['retained'] * retained + ['generated'] * generated)
                self.assertEqual([row[0] for row in result.rows[retained:]], list(range(11, 11+generated)))
                missing = sum(row[1] is None for row in result.rows[retained:])
                self.assertTrue(100 <= missing <= 300)
                self.assertTrue(all(row[1] is None or Decimal('9.8') <= row[1] <= Decimal('12.2') for row in result.rows[retained:]))
                self.assertTrue(all(row[2] in {'A', 'B'} for row in result.rows[retained:]))
                self.assertEqual(csv_text(result), csv_text(generate(recipe)))
                record = run_metadata(result)
                self.assertEqual((record['retained_rows'], record['generated_rows']), (retained, generated))
                self.assertEqual(record['source_sha256'], recipe['sample']['sha256'])
                self.assertEqual(recipe['sample']['csv_utf8'].encode(), original)

    def test_explicit_override_outputs_match_hand_worked_files(self):
        for mode, count, filename in [('new', 2, 'generated-two.expected.csv'), ('extend', 12, 'extend-twelve.expected.csv')]:
            recipe = reference(mode, count)
            recipe['table']['fields'][1].update(minimum='12.2', maximum='12.2', missing_probability='0')
            recipe['table']['fields'][2].update(values=['C'], probabilities=['1'])
            actual = list(csv.reader(StringIO(csv_text(generate(recipe)))))
            expected = list(csv.reader(StringIO((FIXTURES / filename).read_text(encoding='utf-8'))))
            self.assertEqual(actual, expected)

    def test_zero_new_and_too_small_total_preserve_state(self):
        state = Workspace(reference('extend', 10, confirmed=False))
        state.result = generate(state.recipe)
        self.assertEqual(len(state.result.rows), 10)
        self.assertTrue(all(row[-1] == 'retained' for row in state.result.rows))
        saved, result = state.save_recipe(), state.result
        state.table_draft['row_count'] = '9'
        with self.assertRaisesRegex(ValidationError, 'never truncated'):
            state.apply()
        self.assertEqual(dumps(state.recipe), saved)
        self.assertIs(state.result, result)
        self.assertEqual(state.table_draft['row_count'], '9')

    def test_identifiers_need_confirmation_and_collision_free_policy(self):
        recipe = reference(confirmed=False)
        with self.assertRaisesRegex(ValidationError, 'Confirm'):
            generate(recipe)
        state = Workspace(recipe)
        state.select('sample_0')
        state.confirm_identifier()
        generate(state.recipe)
        state.field_draft['start'] = '1'
        state.apply()
        self.assertEqual(state.recipe['sample']['confirmed'], [])
        state.confirm_identifier()
        with self.assertRaisesRegex(ValidationError, 'collide'):
            generate(state.recipe)
        for text in ['id,x\n1,A\n1,B\n', 'id,x\n,A\n2,B\n']:
            with self.subTest(text=text), self.assertRaisesRegex(ValidationError, 'nonempty and unique'):
                generate(profile(text, confirm_identifiers=True))

    def test_bom_delimiters_quoted_unicode_na_space_and_leading_zeroes(self):
        raw = '\ufeffsample_id;code;note\r\n001;NA;" Grüße\nWelt "\r\n002; ;"a;\"\"b\"\""\r\n'
        recipe = profile(raw, ';', 'extend', 4, confirm_identifiers=True)
        self.assertEqual(recipe['table']['fields'][0]['kind'], 'text_id')
        result = generate(loads(dumps(recipe)))
        self.assertEqual(result.rows[0], ('001', 'NA', ' Grüße\nWelt ', 'retained'))
        self.assertEqual(result.rows[1], ('002', ' ', 'a;"b"', 'retained'))
        self.assertEqual([r[0] for r in result.rows[2:]], ['003', '004'])
        self.assertEqual(recipe['sample']['csv_utf8'], raw)
        self.assertEqual(recipe['table']['fields'][1]['missing_probability'], '0')
        tab = profile('id\tvalue\n1\tA\n', '\t', count=1, confirm_identifiers=True)
        self.assertEqual(generate(tab).rows[0], (2, 'A', 'generated'))

    def test_malformed_source_and_tampering_are_rejected_without_replacing_state(self):
        state = Workspace(reference())
        state.result = generate(state.recipe)
        state.field_draft['name'] = 'draft'
        before, result = deepcopy(state.recipe), state.result
        for payload in [b'', b'a,a\n1,2\n', b'a,b\n1\n', b'row_origin\nx\n', b'a\n"unterminated', b'a\n\xff', b'x'*(MAX_BYTES+1)]:
            with self.subTest(payload=payload[:40]), self.assertRaises(ValidationError):
                profile(payload)
        for key, value in [('sha256', '0'*64), ('csv_utf8', 'id\n1\n'), ('suggestions', {})]:
            candidate = deepcopy(before)
            candidate['sample'][key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                state.replace(candidate)
            self.assertEqual(state.recipe, before)
            self.assertIs(state.result, result)
            self.assertEqual(state.field_draft['name'], 'draft')

    def test_probability_remainders_and_missing_only_are_valid(self):
        recipe = profile('x,y\nA,\nB,\nC,\n', count=20)
        probabilities = recipe['table']['fields'][0]['probabilities']
        self.assertEqual(sum(map(Decimal, probabilities)), 1)
        self.assertEqual(probabilities, ['0.333333333334', '0.333333333333', '0.333333333333'])
        self.assertTrue(all(row[1] is None for row in generate(recipe).rows))

    def test_addition_is_stable_and_retained_source_column_removal_is_atomic(self):
        state = Workspace(reference('extend', 12))
        original = generate(state.recipe)
        state.add()
        extended = generate(state.recipe)
        self.assertEqual([row[:3]+row[-1:] for row in extended.rows], list(original.rows))
        self.assertEqual([row[3] for row in extended.rows[:10]], [None]*10)
        state.select('sample_0')
        before = deepcopy(state.recipe)
        with self.assertRaisesRegex(ValidationError, 'keep every source column'):
            state.remove()
        self.assertEqual(state.recipe, before)

    def test_serialized_source_is_counted_before_accepting_recipe(self):
        # Tiny input expands substantially because both source and suggestions are saved.
        source = ('x\n' + '\\'*190 + '\n') * 1
        recipe = profile(source, count=1)
        recipe['sample']['csv_utf8'] += '\n' * MAX_BYTES
        with self.assertRaises(ValidationError):
            loads(json.dumps(recipe))

    def test_cli_profile_generate_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            recipe, output = folder / 'sample.json', folder / 'sample.csv'
            command = [sys.executable, '-m', 'ravel', 'sample', str(FIXTURES/'ten-rows.csv'),
                       '--recipe', str(recipe), '--mode', 'extend', '--rows', '12', '--confirm-identifiers']
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            again = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            generated = subprocess.run([sys.executable, '-m', 'ravel', 'generate', str(recipe), '--csv', str(output)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(output.read_bytes(), csv_text(generate(loads(recipe.read_bytes()))).encode())


if __name__ == '__main__':
    unittest.main()
