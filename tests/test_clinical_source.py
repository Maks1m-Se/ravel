"""Invented source boundaries and reference transcription, without derivations."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path
import shutil
import tempfile
import unittest

from ravel.clinical import source
from ravel.clinical.review import source_case
from ravel.recipe import ValidationError, loads as recipe_loads
from scripts.check_clinical_review import check_source_contract

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'examples/clinical-review'


def fixture(case='C2', filename='baseline-four-cases.json'):
    return source_case(source.loads((FIXTURES / filename).read_bytes()), case,
                       'examples/clinical-review/' + filename)


class ClinicalSourceTests(unittest.TestCase):
    def test_compact_serialization_preserves_supported_size_unicode_and_deep_input(self):
        for text in ['"' + 'a' * (1_048_576 - 2) + '"', '"' + 'é' * 200_000 + '"',
                     '[' * 700 + '-0.00e+01' + ']' * 700]:
            value = source.loads(text)
            encoded = source.dumps(value)
            self.assertLessEqual(len(encoded.encode('utf-8')), 1_048_576)
            self.assertEqual(source.dumps(source.loads(encoded)), encoded)
        nested = '[' * 10_000 + '0' + ']' * 10_000
        try:
            parsed = source.loads(nested)
        except source.SourceParseError as error:
            self.assertEqual(error.diagnostic['check'], 'json')
        else:
            self.assertEqual(source.dumps(source.loads(source.dumps(parsed))), nested)
        cyclic = []
        cyclic.append(cyclic)
        with self.assertRaisesRegex(TypeError, 'Circular'):
            source.dumps(cyclic)

    def test_ambiguous_declarations_and_unavailable_registries_suppress_reference_conclusions(self):
        for collection in ['subjects', 'parameters', 'treatments']:
            document = fixture()
            document[collection].append(deepcopy(document[collection][0]))
            report = source.validate(document)
            self.assertIn('duplicate_id', [item['check'] for item in report['failures']])
            self.assertTrue(any(collection + '.identity_unique' in item['prerequisites'] for item in report['not_evaluated']))
        document = fixture('crossed-pair', 'negative-illustrations.json')
        document['parameters'].append(deepcopy(document['parameters'][1]))
        report = source.validate(document)
        self.assertNotIn('UNDECLARED_GROUP', [item['code'] for item in report['failures']])
        document['parameters'] = None
        report = source.validate(document)
        self.assertNotIn('reference', [item['check'] for item in report['failures']])
        self.assertTrue(any('parameters.identities_available' in item['prerequisites'] for item in report['not_evaluated']))

    def test_malformed_review_adapter_uses_validation_errors_without_coercion_or_information_loss(self):
        for malformed in [dict(format='ravel-clinical-review/1', cases=None),
                          dict(format='ravel-clinical-review/1', cases=[None]),
                          dict(format='ravel-clinical-review/1', cases=[dict(id='x')])]:
            with self.assertRaises(ValidationError):
                source_case(malformed, 'x', 'invented')
        review = source.loads((FIXTURES / 'baseline-four-cases.json').read_bytes())
        review['cases'][0]['records'][0]['provenance'] = dict(source='must-not-disappear')
        with self.assertRaisesRegex(ValidationError, 'silently dropped'):
            source_case(review, 'C1', 'invented')

    def test_numeric_lexemes_timestamp_spelling_ids_order_and_provenance_round_trip(self):
        document = fixture()
        document['records'][0]['timestamp'] = '2026-01-01T11:00:00+02:00'
        for token in ['-0', '1.2300e+02', '0.000000000000000001', '1e99999999', '123456789012345678901234567890']:
            with self.subTest(token=token):
                document['records'][0]['value'] = source.loads(token)
                text = source.dumps(document)
                self.assertIn('"value":' + token, text)
                rebuilt = source.loads(text)
                self.assertEqual(rebuilt, document)
                self.assertEqual(source.validate(rebuilt)['status'], 'passed')
        self.assertEqual(document['records'][0]['timestamp'], '2026-01-01T11:00:00+02:00')
        self.assertEqual([r['id'] for r in document['records']], ['C2-M1', 'C2-M2', 'C2-D1', 'C2-M3'])
        self.assertEqual(document['records'][0]['provenance'], dict(source='examples/clinical-review/baseline-four-cases.json', pointer='/cases/1/records/0'))
        with self.assertRaises(FrozenInstanceError):
            document['records'][0]['value'].token = '7'

    def test_review_adapter_rejects_deep_record_containers_before_copying(self):
        original = source.loads((FIXTURES / 'baseline-four-cases.json').read_bytes())
        original['cases'][0]['records'][0]['value'] = source.loads('-0.00e+01')
        valid_text = source.dumps(original)
        for field in ['value', 'timestamp', 'kind']:
            with self.subTest(field=field):
                review = source.loads(valid_text)
                review['cases'][0]['records'][0][field] = source.loads('[' * 700 + '0' + ']' * 700)
                review = source.loads(source.dumps(review))
                before = source.dumps(review)
                with self.assertRaises(ValidationError) as caught:
                    source_case(review, 'C1', 'invented-review.json')
                self.assertEqual(caught.exception.path, 'review./cases/0/records/0/' + field)
                self.assertIn('scalar', caught.exception.message)
                self.assertEqual(source.dumps(review), before)

        adapted = source_case(original, 'C1', 'invented-review.json')
        self.assertEqual(source.dumps(original), valid_text)
        self.assertEqual(adapted['records'][0]['value'].token, '-0.00e+01')
        self.assertEqual([row['id'] for row in adapted['records']], ['C1-M1', 'C1-D1', 'C1-M2'])
        self.assertEqual([row['provenance'] for row in adapted['records']],
                         [dict(source='invented-review.json', pointer=f'/cases/0/records/{i}') for i in range(3)])
        self.assertEqual(source.validate(adapted)['status'], 'passed')
        adapted['records'][0]['value'] = None
        adapted['records'][0]['provenance']['pointer'] = '/changed'
        self.assertEqual(source.dumps(original), valid_text)

    def test_explicit_null_absent_and_malformed_values_remain_distinct(self):
        document = fixture()
        record = document['records'][1]
        self.assertIsNone(record['value'])
        self.assertEqual(source.validate(document)['status'], 'passed')
        del record['value']
        failures = source.validate(document)['failures']
        self.assertEqual([(f['check'], f['source_ids']) for f in failures], [('required_field', ['C2-M2'])])
        for raw in ['"not-a-number"', '"0.3"', '"\\ud800"', 'true', '{}', '[]']:
            record['value'] = source.loads(raw)
            before = deepcopy(document)
            report = source.validate(document)
            self.assertEqual([(f['check'], f['path'], f['source_ids']) for f in report['failures']],
                             [('value_type', 'records.1.value', ['C2-M2'])])
            self.assertEqual(document, before)
            self.assertEqual(source.loads(source.dumps(document)), document)
        for value in [0.3, 10]:
            record['value'] = value
            self.assertEqual(source.validate(document)['status'], 'failed')
            with self.assertRaises(TypeError):
                source.dumps(document)

    def test_json_parser_refuses_duplicate_keys_nonjson_numbers_invalid_encoding_and_bad_tokens(self):
        for payload in ['{"id":"first","id":"second"}', 'NaN', 'Infinity', '-Infinity',
                        '[01]', b'\xff', '{"value":', '1' * (1_048_576 + 1)]:
            with self.subTest(payload=str(payload)[:25]), self.assertRaises(source.SourceParseError) as caught:
                source.loads(payload)
            self.assertEqual(caught.exception.diagnostic['code'], 'GENERIC_VALIDATION_FAILED')
        for token in ['01', 'NaN', '1;null', '١', '+1']:
            with self.subTest(token=token), self.assertRaises(ValueError):
                source.NumberToken(token)

    def test_record_ids_are_unique_across_exposures_and_measurements(self):
        document = fixture()
        document['records'][2]['id'] = 'C2-M1'
        report = source.validate(document)
        self.assertEqual([(f['check'], f['path'], f['source_ids']) for f in report['failures']],
                         [('duplicate_id', 'records.2.id', ['C2-M1'])])
        self.assertIn('records.0.id', report['failures'][0]['message'])

    def test_broken_references_skip_membership_but_keep_independent_errors(self):
        document = fixture()
        document['records'][0]['subject'] = 'UNKNOWN-SUBJECT'
        document['records'][0]['parameter'] = 'UNKNOWN-PARAMETER'
        document['records'][0]['value'] = 'malformed'
        report = source.validate(document)
        self.assertEqual([(f['check'], f['path']) for f in report['failures']],
                         [('value_type', 'records.0.value'), ('reference', 'records.0.subject'), ('reference', 'records.0.parameter')])
        self.assertEqual(report['not_evaluated'][0]['prerequisites'], ['subject_reference', 'parameter_reference'])
        self.assertEqual(report['not_evaluated'][0]['source_ids'], ['C2-M1'])
        self.assertEqual(report['not_evaluated'][0]['scope'], dict(record='C2-M1'))
        self.assertEqual(report['failures'][0]['scope'], dict(record='C2-M1'))
        self.assertNotIn('UNDECLARED_GROUP', [f['code'] for f in report['failures']])
        self.assertEqual(report, source.validate(dict(reversed(list(document.items())))))

    def test_known_references_do_not_authorize_crossed_pair(self):
        document = fixture('crossed-pair', 'negative-illustrations.json')
        report = source.validate(document)
        self.assertEqual(report['stage'], 'source_structure')
        self.assertEqual(report['status'], 'failed')
        failure, = report['failures']
        self.assertEqual((failure['code'], failure['scope'], failure['source_ids']),
                         ('UNDECLARED_GROUP', dict(subject='S-A', parameter='BX-2'), ['X-M1']))
        self.assertEqual(len(document['pairs']), 2)
        self.assertEqual(report['clinical_policy'], 'not_evaluated')

    def test_empty_collections_unequal_schedules_and_explicit_groups_are_preserved(self):
        one, two = fixture('C1'), fixture('C2')
        document = deepcopy(one)
        for key in ['subjects', 'pairs', 'records']:
            document[key] += two[key]
        # An explicit empty third group creates no measurements.
        document['subjects'].append(dict(id='S-EMPTY', treatment='TX-1', provenance=dict(source='invented', pointer='/empty')))
        document['pairs'].append(dict(subject='S-EMPTY', parameter='BX-1', provenance=dict(source='invented', pointer='/empty-pair')))
        self.assertEqual(source.validate(document)['status'], 'passed')
        self.assertEqual(len(document['records']), 7)
        self.assertEqual(source.loads(source.dumps(document)), document)
        document['records'] = []
        self.assertEqual(source.validate(document)['status'], 'passed')

    def test_required_declarations_provenance_duplicate_pairs_and_references(self):
        document = fixture()
        document['subjects'][0]['treatment'] = 'UNKNOWN-TREATMENT'
        document['parameters'].append(deepcopy(document['parameters'][0]))
        document['pairs'].append(deepcopy(document['pairs'][0]))
        document['records'][0]['provenance'] = {}
        report = source.validate(document)
        self.assertEqual([f['check'] for f in report['failures']],
                         ['duplicate_id', 'reference', 'provenance', 'provenance'])
        self.assertTrue(any('parameter_reference' in item['prerequisites'] for item in report['not_evaluated']))
        self.assertEqual(report['failures'][-1]['source_ids'], ['C2-M1'])
        document = fixture()
        del document['subjects']
        self.assertEqual(source.validate(document)['failures'][0]['path'], 'source.subjects')

    def test_versions_and_reference_sheets_never_enter_generic_loader(self):
        document = fixture()
        for format_name in ['ravel-clinical-source/2', 'clinical-baseline/1', 'ravel-clinical-review/1', None]:
            document['format'] = format_name
            report = source.validate(document)
            self.assertEqual([f['check'] for f in report['failures']], ['version'])
            self.assertIn(source.FORMAT, report['failures'][0]['message'])
        document = fixture()
        with self.assertRaises(ValidationError):
            recipe_loads(source.dumps(document))
        for name in ['baseline-four-cases.json', 'negative-illustrations.json']:
            with self.assertRaises(ValidationError):
                recipe_loads((FIXTURES / name).read_bytes())
        review = source.loads((FIXTURES / 'baseline-four-cases.json').read_bytes())
        before = deepcopy(review)
        source_case(review, 'C1', 'invented')
        self.assertEqual(review, before)
        with self.assertRaisesRegex(ValidationError, 'exactly one'):
            source_case(review, 'absent', 'invented')
        review['format'] = 'ravel-clinical-review/2'
        with self.assertRaisesRegex(ValidationError, 'review/1'):
            source_case(review, 'C1', 'invented')

    def test_unavailable_pair_declarations_do_not_become_an_undeclared_pair_finding(self):
        for malformed in [None, [{}], [dict(subject='S-C2', parameter='UNKNOWN', provenance=dict(source='invented', pointer='/bad'))]]:
            with self.subTest(pairs=malformed):
                document = fixture()
                document['pairs'] = malformed
                report = source.validate(document)
                self.assertEqual(report['status'], 'failed')
                self.assertNotIn('UNDECLARED_GROUP', [failure['code'] for failure in report['failures']])
                for skipped in report['not_evaluated']:
                    self.assertEqual(skipped['prerequisites'], ['pair_declarations'])

    def test_kinds_missing_identity_and_independent_required_fields_have_source_diagnostics(self):
        document = fixture()
        document['records'][0]['kind'] = 'implicit-clinical-event'
        del document['records'][0]['timestamp']
        del document['records'][1]['id']
        report = source.validate(document)
        self.assertEqual(report['failures'][0]['code'], 'INVALID_RECORD_KIND')
        self.assertEqual(report['failures'][0]['source_ids'], ['C2-M1'])
        self.assertTrue(any(f['path'] == 'records.0.timestamp' for f in report['failures']))
        missing_id = next(f for f in report['failures'] if f['path'] == 'records.1.id')
        self.assertEqual(missing_id['source_ids'], [])
        self.assertEqual(missing_id['scope'], dict(subject='S-C2', parameter='BX-1'))

    def test_clinical_policy_illustrations_are_preserved_without_being_marked_validated(self):
        for case in ['a', 'b', 'c']:
            with self.subTest(case=case):
                document = fixture(case, 'negative-illustrations.json')
                report = source.validate(document)
                self.assertEqual((report['status'], report['clinical_policy']), ('passed', 'not_evaluated'))
        malformed_time = fixture('c', 'negative-illustrations.json')['records'][0]
        self.assertEqual(malformed_time['timestamp'], 'not-a-time')
        document = fixture()
        document['records'][2]['status'] = 'unknown-status'
        document['records'][2]['value'] = None
        self.assertEqual(source.validate(document)['status'], 'passed')
        self.assertEqual(document['records'][2]['status'], 'unknown-status')

    def test_references_are_checked_against_written_authority_and_hand_results(self):
        self.assertEqual(check_source_contract()['source_cases'], 8)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'docs').mkdir()
            shutil.copytree(FIXTURES, root / 'examples/clinical-review')
            authority = (ROOT / 'docs/baseline-specification.md').read_text(encoding='utf-8')
            authority = authority.replace('| C4-M3 | measurement | S-C4 | BX-1 | 2026-01-01T11:00:00Z | 15 |',
                                          '| C4-M3 | measurement | S-C4 | BX-1 | 2026-01-01T11:00:00Z | 16 |')
            (root / 'docs/baseline-specification.md').write_text(authority, encoding='utf-8')
            with self.assertRaisesRegex(AssertionError, 'C4-M3'):
                check_source_contract(root)


if __name__ == '__main__':
    unittest.main()
