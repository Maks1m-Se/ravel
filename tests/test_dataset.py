"""Hand-defined structural results, global state and complete export failures."""

from copy import deepcopy
import csv
from hashlib import sha256
from io import BytesIO,StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from ravel.dataset import payloads,template,write_outputs,zip_bytes
from ravel.engine import csv_text,generate,run_metadata
from ravel.recipe import ValidationError,dumps,loads,new_field,validate
from ravel.workspace import Workspace

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'examples/linked/devices-measurements.recipe.json'


class DatasetTests(unittest.TestCase):
    def test_hand_devices_measurements_keys_slots_counts_and_round_trip(self):
        recipe=template()
        expected=json.loads((ROOT/'examples/linked/structural.expected.json').read_text())
        result=generate(loads(dumps(recipe)))
        self.assertEqual([row[0] for row in result.table('devices').rows],expected['device_keys'])
        rows=result.table('measurements').rows
        self.assertEqual([row[0] for row in rows],expected['measurement_keys'])
        self.assertEqual([[row[1],row[2]] for row in rows],expected['device_slot_pairs'])
        self.assertEqual({key:len(table.rows) for key,table in result.tables},expected['row_counts'])
        self.assertEqual(result,generate(recipe))

    def test_missing_references_duplicate_primary_and_contradictory_counts_fail(self):
        for mutation,fragment in [
            (lambda recipe:recipe['relationships'][0].update(foreign_key='missing'),'Parent key column'),
            (lambda recipe:recipe['relationships'][0].update(parent_key='missing'),'declared primary key'),
            (lambda recipe:recipe['relationships'][0].update(parent='missing'),'existing tables'),
            (lambda recipe:recipe['tables'][1].update(row_count=5),'requires 6'),
            (lambda recipe:recipe['tables'][0]['fields'].__setitem__(0,dict(id='device_key',name='device_id',kind='constant',value='D01',missing_probability='0')),'duplicate constant'),
        ]:
            recipe=template()
            mutation(recipe)
            with self.subTest(fragment=fragment),self.assertRaisesRegex(ValidationError,fragment):
                generate(recipe)

    def test_cycle_and_orphan_structural_columns_fail_before_success(self):
        recipe=template()
        recipe['tables'][1]['row_count']=3
        recipe['relationships'][0]['children_per_parent']=1
        field=new_field('foreign_key',recipe['tables'][0]['fields'])
        recipe['tables'][0]['fields'].append(field)
        recipe['relationships'].append(dict(id='reverse',parent='measurements',parent_key='measurement_key',child='devices',foreign_key=field['id'],children_per_parent=1))
        with self.assertRaisesRegex(ValidationError,'acyclic'):
            validate(recipe)
        recipe=template()
        recipe['relationships']=[]
        with self.assertRaisesRegex(ValidationError,'no relationship'):
            validate(recipe)

    def test_independent_fields_tables_order_and_names_preserve_streams(self):
        recipe=template()
        original=generate(recipe)
        recipe['tables'][1]['fields'].append(new_field('normal',recipe['tables'][1]['fields']))
        recipe['tables'].reverse()
        recipe['tables'][0]['name']='Renamed measurements'
        changed=generate(recipe)
        self.assertEqual(changed.table('devices').rows,original.table('devices').rows)
        self.assertEqual(tuple(row[:-1] for row in changed.table('measurements').rows),original.table('measurements').rows)

    def test_complete_payloads_dictionary_validation_hashes_and_deterministic_zip(self):
        result=generate(template())
        files=payloads(result)
        self.assertEqual(set(files),{'devices.csv','measurements.csv','recipe.json','dictionary.json','run.json'})
        self.assertEqual(loads(files['recipe.json']),template())
        dictionary=json.loads(files['dictionary.json'])
        self.assertEqual(dictionary['tables'][1]['primary_key'],'measurement_key')
        metadata=run_metadata(result)
        self.assertEqual(metadata['validation']['status'],'passed')
        for identity,table in result.tables:
            self.assertEqual(metadata['tables'][identity]['csv_sha256'],sha256(files[identity+'.csv']).hexdigest())
            self.assertEqual(files[identity+'.csv'],csv_text(table).encode())
        with zipfile.ZipFile(BytesIO(zip_bytes(result))) as archive:
            self.assertEqual({name:archive.read(name) for name in archive.namelist()},files)
        self.assertEqual(zip_bytes(result),zip_bytes(result))

    def test_staged_export_no_overwrite_and_failed_write_cleans_only_own_stage(self):
        result=generate(template())
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            destination=folder/'dataset'
            written=write_outputs(destination,result)
            before={path.name:path.read_bytes() for path in written}
            with self.assertRaises(FileExistsError):
                write_outputs(destination,result)
            self.assertEqual({path.name:path.read_bytes() for path in written},before)
            original=Path.write_bytes
            def fail_dictionary(path,content):
                if path.name=='dictionary.json':
                    raise OSError('Injected full-set write failure')
                return original(path,content)
            with patch.object(Path,'write_bytes',new=fail_dictionary),self.assertRaisesRegex(OSError,'Injected'):
                write_outputs(folder/'failed',result)
            self.assertFalse((folder/'failed').exists())
            self.assertEqual(list(folder.glob('.*-staging-*')),[])
            self.assertEqual({path.name:path.read_bytes() for path in written},before)

    def test_workspace_global_freshness_switching_drafts_and_atomic_invalid_counts(self):
        state=Workspace(template())
        state.result=generate(state.recipe)
        state.select('device_key')
        state.select_table('measurements')
        self.assertEqual(len(state.table_result.rows),6)
        previous,state_result=state.save_recipe(),state.result
        state.table_draft['row_count']='5'
        with self.assertRaisesRegex(ValidationError,'requires 6'):
            state.apply()
        with self.assertRaisesRegex(ValidationError,'Apply or discard'):
            state.select_table('devices')
        self.assertEqual(dumps(state.recipe),previous)
        self.assertIs(state.result,state_result)
        with self.assertRaises(ValidationError):
            state.export_dataset()
        state.discard()
        state.select_table('devices')
        self.assertEqual(state.selected,'device_key')
        self.assertTrue(state.current)
        self.assertEqual(len(state.table_result.rows),3)

    def test_add_table_converts_explicit_recipe_without_changing_existing_values(self):
        state=Workspace()
        state.result=generate(state.recipe)
        old=state.result.rows
        state.add_table()
        new_identity=state.table_id
        self.assertTrue(state.is_dataset)
        self.assertIsNone(state.table_result)
        self.assertFalse(state.current)
        state.result=generate(state.recipe)
        self.assertEqual(state.result.table('main').rows,old)
        self.assertEqual(len(state.result.table(new_identity).rows),1000)

    def test_relationship_editor_cascades_explicit_counts_and_cycle_failure_is_atomic(self):
        state=Workspace(template())
        state.select_table('measurements')
        state.set_relationship('devices',3)
        self.assertEqual(state.table['row_count'],9)
        state.add_table()
        last=state.table_id
        state.set_relationship('measurements',2)
        self.assertEqual(state.table['row_count'],18)
        state.select_table('measurements')
        preview=state.relationship_candidate('devices',4)
        self.assertEqual({table['id']:table['row_count'] for table in preview['tables']},{'devices':3,'measurements':12,last:24})
        self.assertEqual(state.table['row_count'],9)
        state.set_relationship('devices',4)
        state.select_table('devices')
        before=dumps(state.recipe)
        with self.assertRaisesRegex(ValidationError,'acyclic'):
            state.set_relationship('measurements',1)
        self.assertEqual(dumps(state.recipe),before)
        generated=generate(state.recipe)
        self.assertEqual(len(generated.table(last).rows),24)

    def test_export_warning_is_cleared_only_after_all_tables_or_complete_zip(self):
        state=Workspace(template())
        state.result=generate(state.recipe)
        state.mark_exported()
        self.assertTrue(state.has_unsaved)
        state.select_table('measurements')
        state.mark_exported()
        self.assertFalse(state.has_unsaved)
        state.result=generate(state.recipe)
        self.assertTrue(state.has_unsaved)
        state.export_dataset()
        state.mark_exported(all_tables=True)
        self.assertFalse(state.has_unsaved)

    def test_cli_directory_exports_match_engine_and_invalid_input_has_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            destination=folder/'dataset'
            command=[sys.executable,'-m','ravel','generate',str(FIXTURE),'--directory',str(destination)]
            run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual({path.name:path.read_bytes() for path in destination.iterdir()},payloads(generate(template())))
            self.assertEqual(subprocess.run(command,cwd=ROOT,capture_output=True).returncode,2)
            bad=template()
            bad['tables'][1]['row_count']=5
            path=folder/'invalid.json'
            path.write_text(json.dumps(bad),encoding='utf-8')
            run=subprocess.run([sys.executable,'-m','ravel','generate',str(path),'--directory',str(folder/'invalid-output')],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(run.returncode,2)
            self.assertIn('requires 6',run.stderr)
            self.assertFalse((folder/'invalid-output').exists())


if __name__=='__main__':
    unittest.main()
