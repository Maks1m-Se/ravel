"""Coverage and reference-integrity checks are not a clinical calculation."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from ravel.clinical import source
from ravel.recipe import ValidationError,loads
from scripts.check_clinical_scenarios import check

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'examples/clinical-review'


class ScenarioTests(unittest.TestCase):
    def test_all_twelve_requirements_are_explicit_with_no_implicit_clinical_execution(self):
        result=check()
        self.assertEqual(result['requirements'],12)
        self.assertEqual(result['derivation'],'not_implemented')
        self.assertEqual(result['clinical_policy'],'not_evaluated')
        for name in ['scenario-coverage.json','additional-scenarios.json']:
            with self.assertRaises(ValidationError):
                loads((FOLDER/name).read_bytes())

    def test_grouping_has_three_declared_pairs_and_label_is_preserved_as_source_annotation(self):
        sheet=source.loads((FOLDER/'additional-scenarios.json').read_bytes())
        by_id={case['id']:case for case in sheet['cases']}
        grouping=by_id['grouping']
        self.assertEqual(len(grouping['source']['subjects']),2)
        self.assertEqual(len(grouping['source']['parameters']),2)
        self.assertEqual(len(grouping['expected']['groups']),3)
        label=by_id['labelled-followup']['source']['records'][-1]
        self.assertEqual(label['provenance']['visit_label'],'baseline')
        self.assertEqual(source.loads(source.dumps(label)),label)
        self.assertEqual([r['id'] for r in by_id['out-of-order']['source']['records']],['O-M3','O-M2','O-D1','O-M1'])

    def test_missing_coverage_and_cross_subject_expected_references_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            shutil.copytree(FOLDER,root/'examples/clinical-review')
            folder=root/'examples/clinical-review'
            coverage=json.loads((folder/'scenario-coverage.json').read_text(encoding='utf-8'))
            coverage['scenarios'].pop()
            (folder/'scenario-coverage.json').write_text(json.dumps(coverage),encoding='utf-8')
            with self.assertRaises(AssertionError):
                check(root)
            shutil.copyfile(FOLDER/'scenario-coverage.json',folder/'scenario-coverage.json')
            sheet=json.loads((folder/'additional-scenarios.json').read_text(encoding='utf-8'))
            sheet['cases'][-1]['expected']['groups'][0]['baseline_id']='G-BX1'
            (folder/'additional-scenarios.json').write_text(json.dumps(sheet),encoding='utf-8')
            with self.assertRaisesRegex(AssertionError,'subject'):
                check(root)
