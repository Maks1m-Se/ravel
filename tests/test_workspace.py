"""State transitions protect applied rules, drafts and generated exports."""

from copy import deepcopy
import unittest

from ravel.engine import generate
from ravel.recipe import ValidationError, loads, new_recipe
from ravel.workspace import Workspace


class WorkspaceTests(unittest.TestCase):
    def test_unsaved_warning_tracks_recipe_drafts_output_and_successful_saves(self):
        state = Workspace()
        self.assertFalse(state.has_unsaved)
        state.field_draft['maximum'] = '200'
        self.assertTrue(state.has_unsaved)
        state.discard()
        self.assertFalse(state.has_unsaved)
        state.result = generate(state.recipe)
        self.assertTrue(state.has_unsaved)
        state.mark_exported()
        self.assertFalse(state.has_unsaved)
        state.field_draft['maximum'] = '200'
        state.apply()
        self.assertTrue(state.has_unsaved)
        state.mark_saved()
        self.assertFalse(state.has_unsaved)
        state.replace(state.recipe, saved=False)
        self.assertTrue(state.has_unsaved)

    def test_invalid_apply_is_atomic_and_unapplied_edits_block_actions(self):
        state = Workspace()
        state.result = generate(state.recipe_for_run())
        original, result = deepcopy(state.recipe), state.result
        state.field_draft['minimum'] = '200'
        for action in [state.recipe_for_run, state.save_recipe, state.export_csv, state.add, state.duplicate, state.remove]:
            with self.subTest(action=action.__name__), self.assertRaises(ValidationError):
                action()
        with self.assertRaisesRegex(ValidationError, 'Minimum'):
            state.apply()
        self.assertEqual(state.recipe, original)
        self.assertIs(state.result, result)
        self.assertEqual(state.field_draft['minimum'], '200')
        state.field_draft['minimum'] = '5'
        state.table_draft['row_count'] = '0'
        with self.assertRaises(ValidationError):
            state.apply()
        self.assertEqual(state.recipe, original)
        state.table_draft['row_count'] = '1000'
        state.apply()
        self.assertFalse(state.has_drafts)
        self.assertFalse(state.current)
        with self.assertRaises(ValidationError):
            state.export_csv()
        state.result = generate(state.recipe_for_run())
        self.assertTrue(state.current)
        self.assertEqual(len(state.result.rows), 1000)

    def test_discard_and_view_selection_do_not_change_current_result(self):
        state = Workspace()
        state.result = generate(state.recipe)
        original = state.export_csv()
        state.field_draft['name'] = 'unfinished'
        state.select('row_id')
        self.assertTrue(state.has_drafts)
        state.select('value')
        self.assertEqual(state.field_draft['name'], 'unfinished')
        state.discard()
        self.assertEqual(state.export_csv(), original)

    def test_multiple_field_drafts_apply_together_and_failure_is_atomic(self):
        state = Workspace()
        state.result = generate(state.recipe)
        original, result = deepcopy(state.recipe), state.result
        state.field_draft['maximum'] = '20'
        state.select('row_id')
        state.field_draft['start'] = 'not a number'
        state.table_draft.update(name='test_measurements', row_count='12', seed='42')
        with self.assertRaises(ValidationError):
            state.apply()
        self.assertEqual(state.recipe, original)
        self.assertIs(state.result, result)
        state.select('value')
        self.assertEqual(state.field_draft['maximum'], '20')
        state.select('row_id')
        self.assertEqual(state.field_draft['start'], 'not a number')
        state.field_draft['start'] = '1'
        state.apply()
        self.assertEqual(state.table['fields'][1]['maximum'], 20)
        self.assertEqual(state.table['row_count'], 12)
        self.assertEqual(state.recipe['seed'], 42)
        self.assertFalse(state.has_drafts)
        with self.assertRaises(ValidationError):
            state.export_csv()

    def test_hidden_drafts_block_generation_export_and_save_until_exact_revert(self):
        state = Workspace()
        state.result = generate(state.recipe)
        state.field_draft['maximum'] = '20'
        state.select('row_id')
        for operation in [state.recipe_for_run, state.export_csv, state.save_recipe]:
            with self.assertRaises(ValidationError):
                operation()
        state.select('value')
        state.field_draft['maximum'] = '100'
        self.assertFalse(state.has_drafts)
        self.assertTrue(state.current)

    def test_discard_restores_all_field_drafts_without_changing_selection_or_result(self):
        state = Workspace()
        state.result = generate(state.recipe)
        result = state.result
        state.field_draft['maximum'] = '20'
        state.select('row_id')
        state.field_draft['start'] = '5'
        state.table_draft['seed'] = '42'
        state.discard()
        self.assertEqual(state.selected, 'row_id')
        self.assertEqual(state.field_draft['start'], '1')
        state.select('value')
        self.assertEqual(state.field_draft['maximum'], '100')
        self.assertIs(state.result, result)
        self.assertTrue(state.current)

    def test_hidden_rule_promotions_keep_every_changed_field(self):
        state = Workspace()
        state.change_kind('boolean')
        state.field_draft['probability'] = '1'
        state.select('row_id')
        state.change_kind('text_id')
        state.field_draft.update(prefix='T', width='2', start='1')
        state.select('value')
        state.apply()
        self.assertEqual(state.recipe['format'], 'ravel-single-table/3')
        state.table_draft['row_count'] = '2'
        state.apply()
        self.assertEqual(generate(state.recipe).rows, (('T01', True), ('T02', True)))

    def test_hidden_sample_identifier_edit_invalidates_only_its_confirmation(self):
        from ravel.sample import profile
        state = Workspace(profile(b'id,value\n1,4\n2,5\n', confirm_identifiers=True))
        identifier = state.recipe['sample']['identifiers'][0]
        state.select(identifier)
        state.field_draft['start'] = '10'
        value_id = next(field['id'] for field in state.table['fields'] if field['id'] != identifier)
        state.select(value_id)
        state.field_draft['maximum'] = '8'
        state.apply()
        self.assertNotIn(identifier, state.recipe['sample']['confirmed'])
        self.assertEqual(state.table['fields'][0]['start'], 10)
        self.assertEqual(state.table['fields'][1]['maximum'], 8)

    def test_added_duplicate_removed_columns_have_stable_independent_ids(self):
        state = Workspace()
        state.result = generate(state.recipe)
        original = state.result.rows
        state.add()
        added = state.selected
        self.assertFalse(state.current)
        state.duplicate()
        duplicate = state.selected
        self.assertNotEqual(added, duplicate)
        state.result = generate(state.recipe)
        self.assertEqual(tuple(row[:2] for row in state.result.rows), original)
        state.remove()
        self.assertEqual([f['id'] for f in state.recipe['table']['fields']], ['row_id', 'value', added])
        state.remove()
        state.remove()
        self.assertEqual(len(state.recipe['table']['fields']), 1)
        with self.assertRaisesRegex(ValidationError, 'between 1 and 50'):
            state.remove()
        self.assertEqual(len(state.recipe['table']['fields']), 1)

    def test_kind_category_validation_and_explicit_rule_change(self):
        state = Workspace()
        identity = state.selected
        state.change_kind('category')
        state.field_draft.update(name='arm', categories='"A, one",0.25\nB,0.75')
        state.apply()
        self.assertEqual(state.field['id'], identity)
        self.assertEqual(state.field['values'], ['A, one', 'B'])
        state.field_draft['categories'] = 'A,0.2\nB,0.3'
        with self.assertRaisesRegex(ValidationError, 'sum exactly'):
            state.apply()
        state.field_draft['categories'] = 'broken'
        with self.assertRaisesRegex(ValidationError, 'pair per CSV line'):
            state.apply()

    def test_valid_replace_clears_result_invalid_replace_preserves_everything(self):
        state = Workspace()
        saved = state.save_recipe()
        state.result = generate(state.recipe)
        state.field_draft['name'] = 'unfinished'
        original, result = deepcopy(state.recipe), state.result
        with self.assertRaises(ValidationError):
            state.replace({'format': 'ravel-workbook-experiment/1'})
        self.assertEqual(state.recipe, original)
        self.assertIs(state.result, result)
        self.assertEqual(state.field_draft['name'], 'unfinished')
        state.replace(loads(saved))
        self.assertIsNone(state.result)
        self.assertFalse(state.has_drafts)
        self.assertEqual(state.save_recipe(), saved)

    def test_recipe_size_rejection_preserves_applied_table_and_current_result(self):
        recipe = new_recipe()
        recipe['table']['row_count'] = 1
        recipe['table']['fields'] = [dict(id=f'field{i}', name=f'column{i}', kind='category',
            missing_probability='0', values=[str(j).zfill(3) + 'x' * 197 for j in range(100)],
            probabilities=['0.01'] * 100) for i in range(44)]
        state = Workspace(recipe)
        state.result = generate(recipe)
        saved, selected, result = state.save_recipe(), state.selected, state.result
        before = state.export_csv()
        with self.assertRaisesRegex(ValidationError, '1 MiB'):
            state.duplicate()
        self.assertEqual(state.save_recipe(), saved)
        self.assertEqual(state.selected, selected)
        self.assertIs(state.result, result)
        self.assertTrue(state.current)
        self.assertEqual(state.export_csv(), before)

    def test_changes_during_generation_make_snapshot_result_stale(self):
        state = Workspace()
        snapshot = state.recipe_for_run()
        state.table_draft['seed'] = '42'
        state.apply()
        state.result = generate(snapshot)
        self.assertFalse(state.current)
        with self.assertRaisesRegex(ValidationError, 'current result'):
            state.export_csv()


if __name__ == '__main__':
    unittest.main()
