"""Pre-established date, uniqueness, quota and numeric boundary references."""

from collections import Counter
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import unittest

from ravel.engine import csv_text,generate,preview_rows
from ravel.extended import rounded_normal
from ravel.recipe import ValidationError,dumps,loads,new_field,new_recipe,validate
from ravel.sample import assumption_origin,profile
from ravel.workspace import Workspace

ROOT=Path(__file__).resolve().parents[1]


def recipe_for(kind,count=3,**settings):
    field=new_field(kind)
    field.update(id='reference',name='value',**settings)
    recipe=new_recipe()
    recipe.update(format='ravel-single-table/3')
    recipe['table'].update(row_count=count,fields=[field])
    return recipe


class ExtendedTests(unittest.TestCase):
    def test_hand_leap_day_sequence_reverse_singleton_and_invalid_boundaries(self):
        expected=['2024-02-28','2024-02-29','2024-03-01']
        result=generate(recipe_for('date_sequence'))
        self.assertEqual([row[0] for row in result.rows],expected)
        self.assertEqual([row[0] for row in generate(recipe_for('date_sequence',start='2024-03-01',step=-1)).rows],expected[::-1])
        self.assertEqual([row[0] for row in generate(recipe_for('date',minimum='2024-02-29',maximum='2024-02-29')).rows],['2024-02-29']*3)
        for kind,settings in [('date',{'minimum':'2023-02-29'}),('date_sequence',{'start':'9999-12-31'}),('date',{'maximum':'2024-01-01'}),('date',{'minimum':'20240228'})]:
            with self.subTest(settings=settings),self.assertRaises(ValidationError):
                generate(recipe_for(kind,**settings))

    def test_boolean_probability_endpoints_and_exact_csv_spelling(self):
        for probability,value,text in [('0',False,'false'),('1',True,'true')]:
            result=generate(recipe_for('boolean',probability=probability))
            self.assertEqual([row[0] for row in result.rows],[value]*3)
            self.assertTrue(all(type(row[0]) is bool for row in result.rows))
            self.assertEqual(preview_rows(result),[[text]]*3)
            self.assertIn('"'+text+'"',csv_text(result))

    def test_half_even_rounding_and_normal_range_failure_no_clipping(self):
        for raw,expected in [(1.245,'1.24'),(1.255,'1.26'),(-1.245,'-1.24')]:
            self.assertEqual(rounded_normal(raw,2),Decimal(expected))
        for raw in [10**12+1,float('inf'),float('nan')]:
            with self.assertRaisesRegex(ValidationError,'out-of-range'):
                rounded_normal(raw,2)
        for sd in ['0','-1','1000000000001']:
            with self.subTest(sd=sd),self.assertRaises(ValidationError):
                generate(recipe_for('normal',sd=sd))
        with self.assertRaisesRegex(ValidationError,'out-of-range'):
            generate(recipe_for('normal',count=100,mean='1000000000000',sd='1000000000000'))

    def test_exact_unique_capacity_and_one_beyond_integer_decimal_date(self):
        cases=[('integer',dict(minimum=7,maximum=9),{7,8,9}),
               ('decimal',dict(minimum='1.0',maximum='1.2',places=1),{Decimal('1.0'),Decimal('1.1'),Decimal('1.2')}),
               ('date',{}, {'2024-02-28','2024-02-29','2024-03-01'})]
        for kind,settings,expected in cases:
            with self.subTest(kind=kind):
                recipe=recipe_for(kind,unique=True,**settings)
                self.assertEqual({row[0] for row in generate(recipe).rows},expected)
                recipe['table']['row_count']=4
                with self.assertRaisesRegex(ValidationError,'3 available'):
                    generate(recipe)
        for kind in ['normal','boolean','sequence','constant','category']:
            with self.subTest(kind=kind),self.assertRaisesRegex(ValidationError,'supported'):
                generate(recipe_for(kind,unique=True))

    def test_huge_unique_domains_use_bounded_sampling_without_materialization(self):
        recipe=recipe_for('decimal',count=10,minimum='-1000000000000',maximum='1000000000000',places=6,unique=True)
        values=[row[0] for row in generate(recipe).rows]
        self.assertEqual(len(set(values)),10)
        self.assertTrue(all(abs(value)<=10**12 for value in values))

    def test_final_uniqueness_excludes_originals_and_rejects_duplicate_typed_cells(self):
        recipe=profile('value\n7\n8\n',mode='extend',count=3)
        recipe['format']='ravel-single-table/3'
        recipe['table']['fields'][0].update(maximum=9,unique=True)
        self.assertEqual([row[0] for row in generate(recipe).rows],['7','8',9])
        recipe['table']['row_count']=4
        with self.assertRaisesRegex(ValidationError,'1 available'):
            generate(recipe)
        duplicate=profile('value\n1.0\n1.00\n',mode='extend',count=3)
        duplicate['format']='ravel-single-table/3'
        duplicate['table']['fields'][0].update(unique=True,maximum='2.00')
        with self.assertRaisesRegex(ValidationError,'duplicate typed'):
            generate(duplicate)

    def test_generated_quota_counts_include_explicit_missing_bucket(self):
        recipe=recipe_for('category_quota',count=4,counts=[2,1],missing_count=1)
        result=generate(recipe)
        self.assertEqual(Counter(row[0] for row in result.rows),{'A':2,'B':1,None:1})
        self.assertEqual(result,generate(loads(dumps(recipe))))
        recipe['table']['fields'][0]['missing_probability']='0.2'
        with self.assertRaisesRegex(ValidationError,'exact missing count'):
            generate(recipe)

    def test_final_quota_residual_and_atomic_infeasible_original_counts(self):
        recipe=profile('material\nA\nA\nB\n""\n',mode='extend',count=6)
        recipe['format']='ravel-single-table/3'
        recipe['table']['fields'][0]=dict(id='sample_0',name='material',kind='category_quota',values=['A','B'],counts=[3,2],missing_count=1,scope='final',missing_probability='0')
        state=Workspace(recipe)
        self.assertEqual(assumption_origin(recipe,'sample_0','quotas'),'Edited')
        state.result=generate(recipe)
        self.assertEqual([row[0] for row in state.result.rows[:4]],['A','A','B',''])
        self.assertEqual(Counter(row[0] for row in state.result.rows[4:]),{'A':1,'B':1})
        self.assertEqual([row[-1] for row in state.result.rows],['retained']*4+['generated']*2)
        previous=deepcopy(state.recipe)
        state.field_draft['quotas']='A,1\nB,4'
        with self.assertRaisesRegex(ValidationError,'already exceed'):
            state.apply()
        self.assertEqual(state.recipe,previous)
        state.discard()
        state.table_draft['row_count']='4'
        state.field_draft['quotas']='A,2\nB,1'
        state.apply()
        self.assertTrue(all(row[-1]=='retained' for row in generate(state.recipe).rows))

    def test_versions_reject_new_requests_and_preserve_existing_streams(self):
        recipe=recipe_for('normal')
        recipe['format']='ravel-single-table/2'
        with self.assertRaisesRegex(ValidationError,'requires'):
            validate(recipe)
        original=new_recipe()
        expected=generate(original).rows
        for version in ['ravel-single-table/2','ravel-single-table/3']:
            candidate=deepcopy(original)
            candidate['format']=version
            self.assertEqual(generate(candidate).rows,expected)
        original['format']='ravel-single-table/3'
        original['table']['fields'].append(new_field('normal',original['table']['fields']))
        self.assertEqual(tuple(row[:2] for row in generate(original).rows),expected)

    def test_new_editor_forms_and_version_promotion_preserve_older_input(self):
        for kind,settings in [('normal',{}),('boolean',{}),('date',{}),('date_sequence',{}),('category_quota',{'quotas':'A,2\nB,1'})]:
            state=Workspace()
            state.change_kind(kind)
            state.field_draft.update(settings)
            state.table_draft['row_count']='3'
            state.apply()
            self.assertEqual(state.recipe['format'],'ravel-single-table/3')
            generate(state.recipe)
            self.assertEqual(loads(state.save_recipe()),state.recipe)


if __name__=='__main__':
    unittest.main()
