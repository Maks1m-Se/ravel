"""Explicit adapter for the invented review sheets; no clinical derivation."""

from copy import deepcopy

from ..recipe import ValidationError
from .source import FORMAT


def source_case(review, case_id, source):
    if not isinstance(review, dict) or review.get('format') != 'ravel-clinical-review/1':
        raise ValidationError('review.format', 'Expected the explicit ravel-clinical-review/1 reference sheet.')
    cases = review.get('cases', [])
    matches = [(index, case) for index, case in enumerate(cases) if case.get('id') == case_id]
    if len(matches) != 1:
        raise ValidationError('review.cases', f'Expected exactly one declared case {case_id!r}.')
    index, case = matches[0]
    declarations = review['declarations']
    prefix = f'/cases/{index}'

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
