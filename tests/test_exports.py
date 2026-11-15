"""Portable output refusal, atomicity and pre-repair stream compatibility."""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ravel.dataset import payloads,template,write_outputs,zip_bytes
from ravel.engine import csv_text,generate
from ravel.exports import validate_names
from ravel.recipe import ValidationError,dumps,new_recipe
from ravel.workspace import Workspace

ROOT=Path(__file__).resolve().parents[1]


def renamed_dataset(ids):
    recipe=template()
    mapping=dict(zip([table['id'] for table in recipe['tables']],ids))
    for table,identity in zip(recipe['tables'],ids):table['id']=identity
    for link in recipe['relationships']:
        for key in ['parent','child']:link[key]=mapping[link[key]]
    return recipe


class ExportTests(unittest.TestCase):
    def test_portable_names_and_device_aliases_are_checked_independent_of_os(self):
        validate_names(['devices.csv','measurements.csv','recipe.json','dictionary.json','run.json'])
        validate_names(['CONifer.csv','COM10.csv','my.data.csv','table_con.csv'])
        for names,fragment in [
            (['DATA.csv','data.csv'],'collide'),
            (['CON.csv'],'Reserved Windows'),(['con.recipe.json'],'Reserved Windows'),
            (['AUX.csv'],'Reserved Windows'),(['NUL.csv'],'Reserved Windows'),
            (['PRN.csv'],'Reserved Windows'),(['COM1.csv'],'Reserved Windows'),
            (['CONIN$.csv'],'Reserved Windows'),(['CONOUT$.recipe.json'],'Reserved Windows'),
            (['LPT9.csv'],'Reserved Windows'),(['COM¹.csv'],'Reserved Windows'),
            (['LPT².csv'],'Reserved Windows'),(['CON .csv'],'Reserved Windows'),
            (['trailing.'],'Nonportable'),(['trailing '],'Nonportable'),
            (['stream:part.csv'],'Nonportable'),(['../other.csv'],'Nonportable'),
            (['bad\x00.csv'],'Nonportable'),(['bad\\name.csv'],'Nonportable'),
        ]:
            with self.subTest(names=names),self.assertRaisesRegex(ValidationError,fragment):validate_names(names)

    def test_dataset_csv_zip_and_directory_refuse_whole_namespace_before_writing(self):
        for ids in [('DATA','data'),('CON','measurements')]:
            recipe=renamed_dataset(ids);result=generate(recipe)
            state=Workspace(recipe);state.result=result
            with self.subTest(ids=ids),tempfile.TemporaryDirectory() as temporary:
                folder=Path(temporary)
                with self.assertRaisesRegex(ValidationError,'export.files'):payloads(result)
                with patch('ravel.dataset.zipfile.ZipFile') as archive:
                    with self.assertRaisesRegex(ValidationError,'export.files'):zip_bytes(result)
                    archive.assert_not_called()
                with patch('ravel.dataset.tempfile.mkdtemp') as stage:
                    with self.assertRaisesRegex(ValidationError,'export.files'):write_outputs(folder/'dataset',result)
                    stage.assert_not_called()
                for identity in ids:
                    state.select_table(identity)
                    with self.assertRaisesRegex(ValidationError,'export.files'):state.export_csv()
                with self.assertRaisesRegex(ValidationError,'export.files'):state.export_dataset()
                self.assertEqual(list(folder.iterdir()),[])
                self.assertIs(state.result,result)
                self.assertTrue(state.current)
                self.assertEqual(dumps(state.recipe),dumps(recipe))

    def test_refusal_keeps_exact_eed69c6_ids_recipe_and_csv_values(self):
        # Frozen eed69c6 compatibility fingerprints, captured before the repair.
        for ids,recipe_hash,csv_hashes in [
            (('DATA','data'),'2b39286dc37677d41be2c7e78d1df35b20bd8c5075ec894b673ca5e22c0aa608',
             ['e9fe86c3c1360b814677bd0d5e04d8b51abf633e39fb44eb89933acdd225fd1c','a4c96d35b06cfec77bc8b7857663158b712ff0f30a0177d3950ec9b913019342']),
            (('CON','measurements'),'6c9cf74332c8b7dba222d0d53b45de4e6ca2e65e3dc0af16809f04d1c1955b54',
             ['e9fe86c3c1360b814677bd0d5e04d8b51abf633e39fb44eb89933acdd225fd1c','c7564991cd21ad2340748f0cc01a02aede4a5344e2a8a55b8e8ed14eb8c102e6']),
        ]:
            result=generate(renamed_dataset(ids))
            with self.subTest(ids=ids):
                self.assertEqual(tuple(identity for identity,_ in result.tables),ids)
                self.assertEqual(sha256(result.recipe_json.encode()).hexdigest(),recipe_hash)
                self.assertEqual([sha256(csv_text(table).encode()).hexdigest() for _,table in result.tables],csv_hashes)
                with self.assertRaises(ValidationError):payloads(result)
                self.assertEqual([sha256(csv_text(table).encode()).hexdigest() for _,table in result.tables],csv_hashes)

    def test_cli_dataset_refusal_leaves_no_destination_staging_or_partial_outputs(self):
        for ids,fragment in [(('DATA','data'),'collide'),(('CON','measurements'),'Reserved Windows')]:
            with self.subTest(ids=ids),tempfile.TemporaryDirectory() as temporary:
                folder=Path(temporary);recipe=folder/'input.json'
                before=dumps(renamed_dataset(ids)).encode();recipe.write_bytes(before)
                run=subprocess.run([sys.executable,'-m','ravel','generate',str(recipe),'--directory',str(folder/'dataset')],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(run.returncode,2,run.stdout)
                self.assertIn(fragment,run.stderr)
                self.assertEqual([p.name for p in folder.iterdir()],['input.json'])
                self.assertEqual(recipe.read_bytes(),before)

    def test_cli_single_table_refuses_reserved_invalid_and_input_alias_before_any_output(self):
        for name,fragment in [('CON.csv','Reserved Windows'),('AUX.csv','Reserved Windows'),
                              ('bad:name.csv','Nonportable'),('bad.','Nonportable'),
                              ('input.csv','distinct')]:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temporary:
                folder=Path(temporary);source=folder/'INPUT.recipe.json'
                before=dumps(new_recipe()).encode();source.write_bytes(before)
                run=subprocess.run([sys.executable,'-m','ravel','generate',str(source),'--csv',str(folder/name)],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(run.returncode,2,run.stdout)
                self.assertIn(fragment,run.stderr)
                self.assertEqual([p.name for p in folder.iterdir()],['INPUT.recipe.json'])
                self.assertEqual(source.read_bytes(),before)

    def test_cli_sample_recipe_and_dataset_destination_follow_same_filename_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);source=folder/'sample.csv';source.write_bytes(b'id,value\n1,7\n2,9\n')
            run=subprocess.run([sys.executable,'-m','ravel','sample',str(source),'--recipe',str(folder/'CON.json')],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(run.returncode,2)
            self.assertIn('Reserved Windows',run.stderr)
            with self.assertRaisesRegex(ValidationError,'Reserved Windows'):write_outputs(folder/'NUL',generate(template()))
            self.assertEqual([p.name for p in folder.iterdir()],['sample.csv'])


if __name__=='__main__':unittest.main()
