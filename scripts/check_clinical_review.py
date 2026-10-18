"""Check review-sheet references, not clinical selection, arithmetic or validation."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    folder = ROOT / 'examples/clinical-review'
    valid = json.loads((folder/'baseline-four-cases.json').read_text(encoding='utf-8'))
    negative = json.loads((folder/'negative-illustrations.json').read_text(encoding='utf-8'))
    assert valid['format'] == negative['format'] == 'ravel-clinical-review/1'
    assert [case['id'] for case in valid['cases']] == ['C1', 'C2', 'C3', 'C4']
    counts = {'records': 0, 'doses': 0, 'measurements': 0, 'groups': 0, 'changes': 0}
    for case in valid['cases']:
        records = {record['id']: record for record in case['records']}
        assert len(records) == len(case['records'])
        counts['records'] += len(records)
        counts['doses'] += sum(record['kind'] == 'actual-dose' for record in records.values())
        counts['measurements'] += sum(record['kind'] == 'measurement' for record in records.values())
        expected = case['expected']
        assert expected['status'] == 'passed'
        groups = {row['id']: row for row in expected['groups']}
        counts['groups'] += len(groups)
        counts['changes'] += len(expected['changes'])
        for group in groups.values():
            assert [group['subject'], group['parameter']] in case['declared_groups']
            assert records[group['dose_id']]['kind'] == 'actual-dose'
            if group['baseline_id'] is not None:
                assert records[group['baseline_id']]['kind'] == 'measurement'
        for change in expected['changes']:
            assert change['group_id'] in groups
            assert records[change['target_id']]['kind'] == 'measurement'
            assert change['baseline_id'] == groups[change['group_id']]['baseline_id']
        for diagnostic in expected['record_diagnostics']:
            assert diagnostic['source_id'] in records
    assert counts == dict(records=14, doses=4, measurements=10, groups=4, changes=4), counts
    assert [case['id'] for case in negative['cases']] == ['a', 'b', 'c', 'crossed-pair']
    for case in negative['cases']:
        identities = {record['id'] for record in case['records']}
        assert case['expected_clinical_status'] == 'failed'
        assert case['generic_validation_required'] is True
        assert case['successful_groups'] == case['successful_changes'] == []
        assert case['expected_failures'] and case['not_evaluated']
        for failure in case['expected_failures']:
            assert failure['source_ids'] and set(failure['source_ids']) <= identities
            assert failure['code'] != 'NOT_EVALUATED'
    return counts


if __name__ == '__main__':
    print('Review-sheet structural references passed:', check())
    print('No clinical derivation, numeric policy adoption or clinical validation was performed.')
