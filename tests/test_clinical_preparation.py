"""Keep the proposed domain boundary explicit without implementing derivations."""

import json
from pathlib import Path
import unittest

from ravel.engine import generate, run_metadata
from ravel.recipe import ValidationError, loads
from ravel.workspace import Workspace
from scripts.check_clinical_review import check

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT/'examples/clinical-review'


class ClinicalPreparationTests(unittest.TestCase):
    def test_clinical_looking_generic_names_do_not_activate_derivations(self):
        recipe = loads((FIXTURES/'structure-only.recipe.json').read_bytes())
        result = generate(recipe)
        measurements = result.table('measurements')
        self.assertEqual(measurements.headers[-1], 'baseline')
        self.assertEqual(measurements.rows[0][-1], 'ordinary literal text')
        self.assertEqual({identity: len(table.rows) for identity, table in result.tables},
                         {'subjects': 1, 'exposures': 1, 'measurements': 1})
        self.assertNotIn('clinical', run_metadata(result))
        self.assertEqual(result.recipe_json, generate(recipe).recipe_json)

    def test_review_sheets_have_intact_references_and_are_not_loadable_recipes(self):
        self.assertEqual(check()['records'], 14)
        state = Workspace()
        before = state.save_recipe()
        for name in ['baseline-four-cases.json', 'negative-illustrations.json']:
            review = (FIXTURES/name).read_bytes()
            self.assertEqual(json.loads(review)['format'], 'ravel-clinical-review/1')
            with self.subTest(name=name), self.assertRaises(ValidationError):
                state.replace(loads(review))
            self.assertEqual(state.save_recipe(), before)


if __name__ == '__main__':
    unittest.main()
