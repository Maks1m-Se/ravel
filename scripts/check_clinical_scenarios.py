"""Check declared scenario coverage and references, never clinical derivation."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ravel.clinical import source
from ravel.clinical.review import source_case

NAMES=('ordinary baseline','multiple eligible measurements','latest pre-dose value missing',
       'no eligible baseline','measurement exactly at first dose','post-dose measurement labelled baseline',
       'duplicate eligible timestamps','out-of-order input','missing actual dose','incompatible units',
       'no usable measurements','multiple subjects/parameters with correct grouping')


def check(root=ROOT):
    folder=root/'examples/clinical-review'
    coverage=json.loads((folder/'scenario-coverage.json').read_text(encoding='utf-8'))
    assert coverage['format']=='ravel-clinical-coverage/1'
    assert [row['requirement'] for row in coverage['scenarios']]==list(range(1,13))
    assert [row['name'] for row in coverage['scenarios']]==list(NAMES)
    selections=[]
    for row in coverage['scenarios']:
        filename=row['file']
        assert filename in {'baseline-four-cases.json','negative-illustrations.json','additional-scenarios.json'}
        sheet=source.loads((folder/filename).read_bytes())
        matches=[case for case in sheet['cases'] if case['id']==row['case']]
        assert len(matches)==1,(filename,row['case'])
        case=matches[0]
        document=case['source'] if filename=='additional-scenarios.json' else source_case(sheet,case['id'],'examples/clinical-review/'+filename)
        report=source.validate(document)
        assert report['status']=='passed',report
        assert source.loads(source.dumps(document))==document
        assert row['hand_explanation'] and row['executable_now'] and 'derivation' in row['pending']
        records={record['id']:record for record in document['records']}
        expected=case.get('expected')
        if row['classification']=='intentionally-invalid':
            assert case['expected_clinical_status']=='failed'
            assert case['successful_groups']==case['successful_changes']==[]
            for failure in case['expected_failures']:
                assert set(failure['source_ids'])<=records.keys()
            assert case['not_evaluated']
        else:
            assert row['classification'] in ('valid-ordinary','valid-unusual')
            assert expected['status']=='passed'
            groups={group['id']:group for group in expected['groups']}
            pairs={(pair['subject'],pair['parameter']) for pair in document['pairs']}
            assert {(group['subject'],group['parameter']) for group in groups.values()}==pairs
            for group in groups.values():
                for key in ('dose_id','baseline_id'):
                    identity=group[key]
                    if identity is not None:
                        record=records[identity]
                        assert record['subject']==group['subject'],(case['id'],identity,'subject')
                        assert record['kind']==('exposure' if key=='dose_id' else 'measurement')
                        if key=='baseline_id':
                            assert record['parameter']==group['parameter'],(case['id'],identity,'parameter')
                assert group['baseline_value'] is None or isinstance(group['baseline_value'],source.NumberToken)
            for change in expected['changes']:
                group=groups[change['group_id']]
                target=records[change['target_id']]
                assert (target['subject'],target['parameter'])==(group['subject'],group['parameter'])
                assert (change['dose_id'],change['baseline_id'])==(group['dose_id'],group['baseline_id'])
                assert change['change'] is None or isinstance(change['change'],source.NumberToken)
            for diagnostic in expected['record_diagnostics']:
                assert diagnostic['source_id'] in records
        selections.append((filename,case['id']))
    assert len(set(selections))==12
    return dict(requirements=12,unique_source_cases=12,clinical_policy='not_evaluated',derivation='not_implemented',
                scope='transcription/structure/reference coverage only')


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
