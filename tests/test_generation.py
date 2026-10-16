"""Hand arithmetic, independent properties and shared adapter contracts."""

from copy import deepcopy
import csv
from decimal import Decimal, localcontext
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ravel.engine import csv_text, generate, preview_rows, run_metadata
from ravel.recipe import ValidationError, dumps, duplicate_field, loads, new_field, new_recipe, validate

ROOT = Path(__file__).resolve().parents[1]


def reference():
    return loads((ROOT / 'examples/three-rows.recipe.json').read_bytes())


def random_recipe(count=1000):
    recipe = new_recipe()
    recipe['table']['row_count'] = count
    for kind in ['decimal', 'category', 'constant', 'sequence']:
        field = new_field(kind, recipe['table']['fields'])
        field['name'] = kind
        field['id'] = kind
        recipe['table']['fields'].append(field)
    recipe['table']['fields'][2].update(minimum='-2.00', maximum='3.00')
    recipe['table']['fields'][3].update(values=['A', 'B', 'never'], probabilities=['0.25', '0.75', '0'])
    return recipe


class GenerationTests(unittest.TestCase):
    def test_hand_worked_reference_and_csv(self):
        result = generate(reference())
        self.assertEqual(result.rows, ((1, 'demo', 10), (2, 'demo', 12), (3, 'demo', 14)))
        self.assertEqual(csv_text(result), '"id","group","value"\n"1","demo","10"\n"2","demo","12"\n"3","demo","14"\n')

    def test_1000_types_bounds_categories_and_exact_decimal_grid(self):
        result = generate(random_recipe())
        self.assertEqual(len(result.rows), 1000)
        for index, (identifier, integer, decimal, category, constant, sequence) in enumerate(result.rows):
            self.assertEqual(identifier, index + 1)
            self.assertIs(type(integer), int)
            self.assertTrue(0 <= integer <= 100)
            self.assertIsInstance(decimal, Decimal)
            self.assertTrue(Decimal('-2') <= decimal <= Decimal('3'))
            self.assertEqual(decimal.as_tuple().exponent, -2)
            self.assertIn(category, {'A', 'B'})
            self.assertEqual(constant, 'demo')
            self.assertEqual(sequence, 10 + index * 2)

    def test_probability_endpoints_and_independent_binomial_properties(self):
        recipe = random_recipe(10000)
        recipe['table']['fields'][1]['missing_probability'] = '0.2'
        result = generate(recipe)
        missing = sum(row[1] is None for row in result.rows)
        # Bernoulli .2: E=2000, SD=40; deliberately broad six-SD interval.
        self.assertTrue(1760 <= missing <= 2240, missing)
        a_count = sum(row[3] == 'A' for row in result.rows)
        # Bernoulli .25: E=2500, SD=sqrt(1875)<44; broad six-SD interval.
        self.assertTrue(2236 <= a_count <= 2764, a_count)
        recipe['table']['fields'][1]['missing_probability'] = '1'
        self.assertTrue(all(row[1] is None for row in generate(recipe).rows))
        recipe['table']['fields'][1]['missing_probability'] = '0'
        self.assertTrue(all(row[1] is not None for row in generate(recipe).rows))
        recipe['table']['fields'][3]['probabilities'] = ['0', '1', '0']
        self.assertEqual({row[3] for row in generate(recipe).rows}, {'B'})

    def test_inclusive_bounds_singleton_and_negative_zero_step_sequence(self):
        recipe = new_recipe()
        recipe['table']['fields'][1].update(minimum=-1, maximum=0)
        self.assertEqual({r[1] for r in generate(recipe).rows}, {-1, 0})
        recipe['table']['fields'][1].update(minimum=-1, maximum=-1)
        self.assertEqual({r[1] for r in generate(recipe).rows}, {-1})
        recipe = reference()
        recipe['table']['fields'][2]['step'] = -2
        self.assertEqual([r[2] for r in generate(recipe).rows], [10, 8, 6])
        recipe['table']['fields'][2]['step'] = 0
        self.assertEqual([r[2] for r in generate(recipe).rows], [10, 10, 10])

    def test_save_reload_repeatability_and_no_input_mutation(self):
        recipe = random_recipe()
        original = deepcopy(recipe)
        first = generate(recipe)
        second = generate(loads(dumps(recipe)))
        self.assertEqual(csv_text(first), csv_text(second))
        self.assertEqual(first.recipe_json, second.recipe_json)
        self.assertEqual(run_metadata(first), run_metadata(second))
        self.assertEqual(recipe, original)
        recipe['seed'] += 1
        self.assertNotEqual(generate(recipe).rows, first.rows)

    def test_field_addition_reorder_rename_and_duplicate_identity(self):
        recipe = random_recipe()
        original = generate(recipe)
        field = new_field('integer', recipe['table']['fields'])
        recipe['table']['fields'].insert(0, field)
        self.assertEqual(tuple(row[1:] for row in generate(recipe).rows), original.rows)
        recipe['table']['fields'].pop(0)
        recipe['table']['fields'][1]['name'] = 'renamed'
        self.assertEqual(generate(recipe).rows, original.rows)
        recipe['table']['fields'].reverse()
        self.assertEqual(tuple(tuple(reversed(row)) for row in generate(recipe).rows), original.rows)
        source = next(f for f in recipe['table']['fields'] if f['id'] == 'value')
        duplicate = duplicate_field(source, recipe['table']['fields'])
        self.assertNotEqual(duplicate['id'], source['id'])
        recipe['table']['fields'].append(duplicate)
        result = generate(recipe)
        original_index = result.headers.index('renamed')
        self.assertNotEqual([r[original_index] for r in result.rows], [r[-1] for r in result.rows])
        self.assertEqual(result.rows, generate(loads(dumps(recipe))).rows)

    def test_missingness_does_not_shift_value_stream(self):
        recipe = new_recipe()
        full = generate(recipe)
        recipe['table']['fields'][1]['missing_probability'] = '0.5'
        sparse = generate(recipe)
        for complete, partial in zip(full.rows, sparse.rows):
            if partial[1] is not None:
                self.assertEqual(complete[1], partial[1])

    def test_decimal_arithmetic_does_not_depend_on_callers_context(self):
        recipe = random_recipe()
        expected = csv_text(generate(recipe))
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(csv_text(generate(recipe)), expected)
            recipe['table']['fields'][3]['probabilities'] = ['0.334', '0.333', '0.332']
            with self.assertRaisesRegex(ValidationError, 'sum exactly'):
                validate(recipe)

    def test_preview_csv_agreement_quoting_and_missing(self):
        recipe = random_recipe()
        recipe['table']['fields'][4]['value'] = 'comma, quote" and\r\nUnicode λ\rreturn'
        recipe['table']['fields'][2]['missing_probability'] = '1'
        result = generate(recipe)
        parsed = list(csv.reader(StringIO(csv_text(result))))
        self.assertEqual(parsed[0], list(result.headers))
        self.assertEqual(parsed[1:101], preview_rows(result))
        self.assertEqual(parsed[1][2], '')
        self.assertEqual(parsed[1][4], 'comma, quote" and\r\nUnicode λ\rreturn')

    def test_strict_validation_actionable_impossible_and_unsupported(self):
        cases = [
            (lambda p: p.update(seed=True), 'seed'),
            (lambda p: p.update(seed=-1), 'seed'),
            (lambda p: p.update(relationships=[]), 'Unsupported'),
            (lambda p: p['table'].update(row_count=0), 'row_count'),
            (lambda p: p['table'].update(row_count=100001), 'row_count'),
            (lambda p: p['table']['fields'][0].update(missing_probability='0.1'), 'cannot be missing'),
            (lambda p: p['table']['fields'][0].update(start=10**12), 'start'),
            (lambda p: p['table']['fields'][1].update(minimum=101), 'Minimum'),
            (lambda p: p['table']['fields'][1].update(maximum=0.5), 'whole number'),
            (lambda p: p['table']['fields'][1].update(missing_probability='NaN'), 'decimal'),
            (lambda p: p['table']['fields'][1].update(missing_probability='1.01'), 'from 0 to 1'),
            (lambda p: p['table']['fields'][1].update(name='id'), 'names must be unique'),
            (lambda p: p['table']['fields'][1].update(id='row_id'), 'identities must be unique'),
            (lambda p: p['table']['fields'][1].update(kind='normal'), 'supported rule'),
            (lambda p: p['table']['fields'][2].update(minimum='0.001'), 'decimal places'),
            (lambda p: p['table']['fields'][3].update(probabilities=['0.2', '0.3', '0']), 'sum exactly'),
            (lambda p: p['table']['fields'][3].update(values=['A','A','B']), 'distinct'),
            (lambda p: p['table']['fields'][4].update(value=''), 'nonempty'),
        ]
        for mutate, message in cases:
            with self.subTest(message=message):
                recipe = random_recipe()
                mutate(recipe)
                with self.assertRaisesRegex(ValidationError, message):
                    generate(recipe)

    def test_old_unknown_malformed_and_oversized_json(self):
        for payload, message in [
            ('{"format":"ravel-workbook-experiment/1"}', 'Old workbook'),
            ('{"format":"future/2"}', 'Supported format'),
            ('{"seed":1,"seed":2}', 'Duplicate'),
            ('{"seed":NaN}', 'Unsupported JSON'),
            ('[', 'valid UTF-8 JSON'), (b'\xff', 'valid UTF-8 JSON'),
            (' ' * 1048577, '1 MiB'),
        ]:
            with self.subTest(message=message), self.assertRaisesRegex(ValidationError, message):
                loads(payload)

    def test_cli_matches_engine_and_records_recipe_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'rows.csv'
            command = [sys.executable, '-m', 'ravel', 'generate', str(ROOT/'examples/three-rows.recipe.json'), '--csv', str(output)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = generate(reference())
            self.assertEqual(output.read_bytes(), csv_text(result).encode())
            self.assertEqual(output.with_suffix('.recipe.json').read_bytes(), result.recipe_json.encode())
            self.assertEqual(json.loads(output.with_suffix('.run.json').read_text()), run_metadata(result))
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 2)
            self.assertIn('already exists', completed.stderr)

    def test_cli_invalid_input_and_input_output_collision_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'recipe.json'
            source.write_text('{"format":"ravel-workbook-experiment/1"}')
            original = source.read_bytes()
            command = [sys.executable, '-m', 'ravel', 'generate', str(source), '--csv', str(Path(directory)/'data.csv')]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 2)
            self.assertIn('Old workbook', completed.stderr)
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse((Path(directory)/'data.csv').exists())
            source.write_text(dumps(reference()))
            original = source.read_bytes()
            completed = subprocess.run(command[:-1]+[str(source)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(source.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
