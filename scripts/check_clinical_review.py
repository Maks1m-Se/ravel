"""Check review-sheet references, not clinical selection, arithmetic or validation."""

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ravel.clinical import source
from ravel.clinical.review import source_case


def check(root=ROOT):
    folder = root / 'examples/clinical-review'
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
    check_source_contract(root)
    from scripts.check_clinical_scenarios import check as check_scenarios
    check_scenarios(root)
    return counts


def check_source_contract(root=ROOT):
    """Compare source transcription to the accepted Markdown, not a derivation."""
    folder = root / 'examples/clinical-review'
    authority = (root / 'docs/baseline-specification.md').read_text(encoding='utf-8')
    table_rows = {}
    for line in authority.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) == 7 and re.fullmatch(r'C[1-4]-[MD][0-9]+', cells[0]):
            table_rows[cells[0]] = cells
    assert len(table_rows) == 14, 'Expected the fourteen accepted source table rows.'

    def adapted(review, case, filename):
        document = source_case(review, case['id'], 'examples/clinical-review/' + filename)
        assert [row['id'] for row in document['subjects']] == case['declared_subjects']
        assert [[row['subject'], row['parameter']] for row in document['pairs']] == case['declared_groups']
        assert {row['id']: row['unit'] for row in document['parameters']} == review['declarations']['parameters']
        assert document['treatments'][0]['id'] == review['declarations']['treatment']
        assert document['treatments'][0]['unit'] == review['declarations']['dose_unit']
        for original, row in zip(case['records'], document['records']):
            expected = dict(original)
            if original['kind'] != 'measurement':
                expected.update(kind='exposure', status=original['kind'], treatment=expected.pop('parameter'))
            assert {key: value for key, value in row.items() if key != 'provenance'} == expected, original['id']
        assert len(document['records']) == len(case['records'])
        return document
    valid = source.loads((folder / 'baseline-four-cases.json').read_bytes())
    # Hand expectations fixed in the accepted specification and maintainer task.
    expected = {
        'C1': ('C1-M1', '10', 'C1-M2', '3', []),
        'C2': ('C2-M1', '8', 'C2-M3', '3', []),
        'C3': (None, None, 'C3-M2', None, ['NO_ELIGIBLE_BASELINE']),
        'C4': ('C4-M1', '10', 'C4-M3', '5', []),
    }
    for case in valid['cases']:
        for record in case['records']:
            value = record['value'].token if isinstance(record['value'], source.NumberToken) else 'null'
            actual = [record[key] for key in ('id', 'kind', 'subject', 'parameter', 'timestamp')] + [value, record['unit']]
            assert actual == table_rows[record['id']], record['id']
        baseline_id, baseline, target, change, reasons = expected[case['id']]
        group, outcome = case['expected']['groups'][0], case['expected']['changes'][0]
        token = lambda value: value.token if isinstance(value, source.NumberToken) else value
        assert (group['dose_id'], group['baseline_id'], token(group['baseline_value'])) == (case['id'] + '-D1', baseline_id, baseline), case['id']
        assert (outcome['target_id'], outcome['baseline_id'], token(outcome['change']), outcome['reasons']) == (target, baseline_id, change, reasons), case['id']
        assert group['reasons'] == reasons
        assert len(case['expected']['groups']) == len(case['expected']['changes']) == 1
        for boundary in ('C3-M1', 'C4-M2'):
            if boundary in {record['id'] for record in case['records']}:
                assert dict(source_id=boundary, code='AT_DOSE_BOUNDARY') in case['expected']['record_diagnostics']
                assert boundary not in {row['target_id'] for row in case['expected']['changes']}
        document = adapted(valid, case, 'baseline-four-cases.json')
        report = source.validate(document)
        assert report['status'] == 'passed', report
        assert source.loads(source.dumps(document)) == document
        assert [row['id'] for row in document['records']] == [row['id'] for row in case['records']]

    negative = source.loads((folder / 'negative-illustrations.json').read_bytes())
    expected_failures = {
        'a': [dict(code='INCOMPATIBLE_UNIT', scope=dict(subject='S-DIAG', parameter='BX-1'), source_ids=['A-M2'])],
        'b': [dict(code='BASELINE_TIE', scope=dict(subject='S-DIAG', parameter='BX-1'), source_ids=['B-M1', 'B-M2'])],
        'c': [dict(code='INVALID_TIMESTAMP', scope=dict(subject='S-DIAG'), source_ids=['C-D1'])],
        'crossed-pair': [dict(code='UNDECLARED_GROUP', scope=dict(subject='S-A', parameter='BX-2'), source_ids=['X-M1'])],
    }
    for case in negative['cases']:
        assert case['expected_failures'] == expected_failures[case['id']]
        document = adapted(negative, case, 'negative-illustrations.json')
        assert source.loads(source.dumps(document)) == document
        report = source.validate(document)
        if case['id'] == 'crossed-pair':
            failures = [{key: failure[key] for key in ('code', 'scope', 'source_ids')} for failure in report['failures']]
            assert failures == case['expected_failures'], report
        else:
            assert report['status'] == 'passed', report
        assert report['clinical_policy'] == 'not_evaluated'
    return dict(source_cases=8, clinical_policy='not_evaluated', derivation='not_implemented')


if __name__ == '__main__':
    print('Review-sheet structural references passed:', check())
    print('Source contract checks:', check_source_contract())
    from scripts.check_clinical_scenarios import check as check_scenarios
    print('Twelve-scenario coverage:', check_scenarios())
    print('No clinical derivation, numeric policy adoption or clinical validation was performed.')
