"""Explicit adapter for the invented review sheets; no clinical derivation."""

from copy import deepcopy

from ..recipe import ValidationError
from .source import FORMAT


def source_case(review, case_id, source):
    if not isinstance(review, dict) or review.get('format') != 'ravel-clinical-review/1':
        raise ValidationError('review.format', 'Expected the explicit ravel-clinical-review/1 reference sheet.')
    def require(condition, path, message):
        if not condition:
            raise ValidationError('review.' + path, message)

    def text(value):
        return isinstance(value, str) and bool(value) and '\x00' not in value

    require(text(source), 'source', 'Supply explicit source provenance.')
    cases = review.get('cases')
    require(isinstance(cases, list), 'cases', 'Expected an ordered case collection.')
    require(all(isinstance(case, dict) and text(case.get('id')) for case in cases),
            'cases', 'Every case requires a text identity.')
    matches = [(index, case) for index, case in enumerate(cases) if case.get('id') == case_id]
    if len(matches) != 1:
        raise ValidationError('review.cases', f'Expected exactly one declared case {case_id!r}.')
    index, case = matches[0]
    declarations = review.get('declarations')
    require(isinstance(declarations, dict), 'declarations', 'Expected treatment/unit/parameter declarations.')
    for key in ['treatment', 'dose_unit']:
        require(text(declarations.get(key)), 'declarations.' + key, 'Required declaration is absent or malformed.')
    parameters = declarations.get('parameters')
    require(isinstance(parameters, dict) and all(text(key) and text(unit) for key, unit in parameters.items()),
            'declarations.parameters', 'Expected explicit parameter/unit declarations.')
    prefix = f'/cases/{index}'
    require(isinstance(case.get('declared_subjects'), list) and all(text(identity) for identity in case['declared_subjects']),
            prefix + '/declared_subjects', 'Expected explicit subject identities.')
    require(isinstance(case.get('declared_groups'), list) and all(isinstance(pair, list) and len(pair) == 2 and all(text(value) for value in pair)
            for pair in case['declared_groups']), prefix + '/declared_groups', 'Expected explicit subject/parameter pairs.')
    require(isinstance(case.get('records'), list), prefix + '/records', 'Expected supplied source records.')
    required = {'id', 'kind', 'subject', 'parameter', 'timestamp', 'value', 'unit'}
    for i, record in enumerate(case['records']):
        require(isinstance(record, dict) and set(record) == required, prefix + f'/records/{i}',
                'Expected exactly the review source fields; no source fields may be silently dropped.')
        for field in ['id', 'kind', 'subject', 'parameter', 'timestamp', 'value', 'unit']:
            require(not isinstance(record[field], (dict, list)), prefix + f'/records/{i}/{field}',
                    'Expected a scalar review source field; nested objects or arrays are malformed.')

    def provenance(pointer):
        return dict(source=source, pointer=pointer)

    treatment = declarations['treatment']
    document = dict(format=FORMAT, provenance=provenance(prefix),
                    treatments=[dict(id=treatment, unit=declarations['dose_unit'], provenance=provenance('/declarations'))],
                    parameters=[dict(id=identity, unit=unit, provenance=provenance('/declarations/parameters/' + identity.replace('~', '~0').replace('/', '~1')))
                                for identity, unit in declarations['parameters'].items()],
                    subjects=[dict(id=identity, treatment=treatment, provenance=provenance(f'{prefix}/declared_subjects/{i}'))
                              for i, identity in enumerate(case['declared_subjects'])],
                    pairs=[dict(subject=subject, parameter=parameter, provenance=provenance(f'{prefix}/declared_groups/{i}'))
                           for i, (subject, parameter) in enumerate(case['declared_groups'])],
                    records=[])
    for i, original in enumerate(case['records']):
        row = deepcopy(original)
        if original['kind'] in ('actual-dose', 'planned-dose', 'not-administered'):
            row['kind'] = 'exposure'
            row['status'] = original['kind']
            row['treatment'] = row.pop('parameter')
        elif original['kind'] != 'measurement':
            raise ValidationError(f'{prefix}/records/{i}/kind', f'Unsupported review record kind {original["kind"]!r}; no status inferred.')
        row['provenance'] = provenance(f'{prefix}/records/{i}')
        document['records'].append(row)
    return document
