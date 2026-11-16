"""Lossless numeric tokens and structural checks for explicitly supplied sources."""

from dataclasses import dataclass
import json
import re

from ..recipe import MAX_BYTES, ValidationError

FORMAT = 'ravel-clinical-source/1'
NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')
COLLECTIONS = ('treatments', 'parameters', 'subjects', 'pairs', 'records')


@dataclass(frozen=True)
class NumberToken:
    token: str

    def __post_init__(self):
        if not isinstance(self.token, str) or not NUMBER.fullmatch(self.token):
            raise ValueError('Expected an original JSON number token.')


class SourceParseError(ValidationError):
    def __init__(self, message):
        super().__init__('source.json', message)
        self.diagnostic = dict(code='GENERIC_VALIDATION_FAILED', check='json',
                               path=self.path, scope={}, source_ids=[], message=message)


def loads(payload):
    """Parse without interpreting timestamps, numeric policy or clinical status."""
    def object_pairs(pairs):
        document = {}
        for key, value in pairs:
            if key in document:
                raise ValueError(f'Duplicate JSON key {key!r}.')
            document[key] = value
        return document

    def constant(token):
        raise ValueError(f'{token} is not a JSON number.')

    try:
        if not isinstance(payload, (str, bytes)):
            raise ValueError('Supply UTF-8 bytes or JSON text.')
        if len(payload.encode('utf-8') if isinstance(payload, str) else payload) > MAX_BYTES:
            raise ValueError('Source JSON must fit within 1 MiB.')
        text = payload.decode('utf-8') if isinstance(payload, bytes) else payload
        return json.loads(text, parse_int=NumberToken, parse_float=NumberToken,
                          parse_constant=constant, object_pairs_hook=object_pairs)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise SourceParseError(str(error)) from error


def dumps(document):
    """Semantic JSON round trip; numeric tokens retain their lexical spelling."""
    def quoted(value):
        # Keep UTF-8 compact while retaining even malformed surrogate tokens.
        return re.sub('[\\ud800-\\udfff]', lambda match: '\\u%04x' % ord(match[0]),
                      json.dumps(value, ensure_ascii=False))

    output, active, stack = [], set(), [('value', document)]
    while stack:
        operation, value = stack.pop()
        if operation == 'text':
            output.append(value)
            continue
        if operation == 'leave':
            active.remove(value)
            continue
        if isinstance(value, NumberToken):
            output.append(value.token)
        elif isinstance(value, str):
            output.append(quoted(value))
        elif value is None or isinstance(value, bool):
            output.append(json.dumps(value))
        elif isinstance(value, (list, dict)):
            identity = id(value)
            if identity in active:
                raise TypeError('Circular source value is not JSON.')
            active.add(identity)
            stack.append(('leave', identity))
            if isinstance(value, dict):
                if not all(isinstance(key, str) for key in value):
                    raise TypeError('Source object keys must be text.')
                jobs = []
                for index, (key, item) in enumerate(value.items()):
                    if index:
                        jobs.append(('text', ','))
                    jobs.extend([('text', quoted(key) + ':'), ('value', item)])
                opening, closing = '{', '}'
            else:
                jobs = []
                for index, item in enumerate(value):
                    if index:
                        jobs.append(('text', ','))
                    jobs.append(('value', item))
                opening, closing = '[', ']'
            output.append(opening)
            stack.append(('text', closing))
            stack.extend(reversed(jobs))
        else:
            raise TypeError('Use parsed source values; native numeric conversions lose original tokens.')
    return ''.join(output)


def validate(document):
    """Report source structure only; never derive or silently repair records."""
    failures, skipped = [], []
    registries, ambiguous, available = {}, {}, {}

    def issue(check, path, message, row=None, code='GENERIC_VALIDATION_FAILED'):
        row = row if isinstance(row, dict) else {}
        identities = [row['id']] if isinstance(row.get('id'), str) else []
        subject, parameter = row.get('subject'), row.get('parameter')
        scope = dict(record=identities[0]) if identities else {}
        if isinstance(subject, str) and subject in registries.get('subjects', {}) and subject not in ambiguous.get('subjects', set()):
            if row.get('kind') == 'exposure':
                scope = dict(subject=subject)
            elif isinstance(parameter, str) and parameter in registries.get('parameters', {}) and parameter not in ambiguous.get('parameters', set()):
                scope = dict(subject=subject, parameter=parameter)
        failures.append(dict(code=code, check=check, path=path, scope=scope,
                             source_ids=identities, message=message))

    def report():
        return dict(stage='source_structure', status='failed' if failures else 'passed',
                    failures=failures, not_evaluated=skipped, clinical_policy='not_evaluated')

    if not isinstance(document, dict) or document.get('format') != FORMAT:
        supplied = document.get('format') if isinstance(document, dict) else type(document).__name__
        issue('version', 'format', f'Unsupported clinical source format {supplied!r}; supported: {FORMAT}.')
        return report()

    def text(value):
        if not isinstance(value, str) or not value or '\x00' in value:
            return False
        try:
            value.encode('utf-8')
        except UnicodeError:
            return False
        return True

    def fields(row, required, path):
        if not isinstance(row, dict):
            issue('type', path, 'Expected a source object.')
            return False
        for key in required:
            if key not in row:
                issue('required_field', path + '.' + key, f'Required field {key!r} is absent.', row)
        for key in sorted(set(row) - set(required), key=str):
            issue('unsupported_field', path + '.' + str(key), f'Unsupported field {key!r}.', row)
        return True

    def strings(row, keys, path):
        for key in keys:
            if key in row and not text(row[key]):
                issue('type', path + '.' + key, f'{key} must be nonempty valid Unicode source text without NUL.', row)

    def provenance(row, path):
        value = row.get('provenance')
        if not isinstance(value, dict):
            if 'provenance' in row:
                issue('provenance', path + '.provenance', 'Expected source and pointer provenance.', row)
            return
        for key in ('source', 'pointer'):
            if not text(value.get(key)):
                issue('provenance', path + '.provenance.' + key, f'Provenance requires {key}.', row)

    fields(document, ('format', 'provenance') + COLLECTIONS, 'source')
    provenance(document, 'source')
    rows = {}
    for collection in COLLECTIONS:
        value = document.get(collection)
        if not isinstance(value, list):
            if collection in document:
                issue('type', collection, 'Expected an ordered collection.')
            value = []
        rows[collection] = value

    for collection, required in [
        ('treatments', ('id', 'unit', 'provenance')),
        ('parameters', ('id', 'unit', 'provenance')),
        ('subjects', ('id', 'treatment', 'provenance')),
    ]:
        registry = {}
        ambiguous[collection] = set()
        available[collection] = isinstance(document.get(collection), list)
        for index, row in enumerate(rows[collection]):
            path = f'{collection}.{index}'
            if not fields(row, required, path):
                available[collection] = False
                continue
            strings(row, required[:-1], path)
            provenance(row, path)
            identity = row.get('id')
            if text(identity):
                if identity in registry:
                    ambiguous[collection].add(identity)
                    issue('duplicate_id', path + '.id', f'Duplicate {collection} ID {identity!r}; first at {registry[identity]}.', row)
                else:
                    registry[identity] = path + '.id'
            else:
                available[collection] = False
        registries[collection] = registry

    def reference(row, key, registry, path):
        value = row.get(key)
        if not text(value):
            return False
        if not available[registry] or value in ambiguous[registry]:
            prerequisite = registry + ('.identity_unique' if value in ambiguous[registry] else '.identities_available')
            identity = row.get('id')
            skipped.append(dict(code='NOT_EVALUATED', check=key + '_reference', path=path + '.' + key,
                                scope=dict(record=identity) if text(identity) else {},
                                source_ids=[identity] if text(identity) else [], prerequisites=[prerequisite]))
            return False
        if value not in registries[registry]:
            issue('reference', path + '.' + key, f'Unknown {key} {value!r}.', row)
            return False
        return True

    for index, row in enumerate(rows['subjects']):
        if isinstance(row, dict):
            reference(row, 'treatment', 'treatments', f'subjects.{index}')

    pairs = set()
    pair_failures_before = len(failures)
    pair_skipped_before = len(skipped)
    for index, row in enumerate(rows['pairs']):
        path = f'pairs.{index}'
        if not fields(row, ('subject', 'parameter', 'provenance'), path):
            continue
        strings(row, ('subject', 'parameter'), path)
        provenance(row, path)
        subject = reference(row, 'subject', 'subjects', path)
        parameter = reference(row, 'parameter', 'parameters', path)
        if subject and parameter:
            pair = (row['subject'], row['parameter'])
            if pair in pairs:
                issue('duplicate_pair', path, f'Duplicate declared pair {pair!r}.', row)
            pairs.add(pair)
    pairs_available = (isinstance(document.get('pairs'), list) and len(failures) == pair_failures_before
                       and len(skipped) == pair_skipped_before)

    record_ids = {}
    for index, row in enumerate(rows['records']):
        path = f'records.{index}'
        if not isinstance(row, dict):
            issue('type', path, 'Expected a source record.')
            continue
        kind = row.get('kind')
        common = ('id', 'kind', 'subject', 'timestamp', 'value', 'unit', 'provenance')
        if kind not in ('measurement', 'exposure'):
            issue('record_kind', path + '.kind', f'Unsupported source record kind {kind!r}.', row, 'INVALID_RECORD_KIND')
            required = common
        else:
            required = common + (('parameter',) if kind == 'measurement' else ('treatment', 'status'))
        fields(row, required, path)
        strings(row, tuple(key for key in required if key not in ('value', 'provenance')), path)
        provenance(row, path)
        identity = row.get('id')
        if text(identity):
            if identity in record_ids:
                issue('duplicate_id', path + '.id', f'Duplicate source ID {identity!r}; first at {record_ids[identity]}.', row)
            else:
                record_ids[identity] = path + '.id'
        if 'value' in row and row['value'] is not None and not isinstance(row['value'], NumberToken):
            issue('value_type', path + '.value', 'Preserve a JSON number token or explicit null; malformed values are not missing.', row)
        subject = reference(row, 'subject', 'subjects', path)
        if kind == 'exposure':
            reference(row, 'treatment', 'treatments', path)
        elif kind == 'measurement':
            parameter = reference(row, 'parameter', 'parameters', path)
            if subject and parameter and pairs_available:
                pair = (row['subject'], row['parameter'])
                if pair not in pairs:
                    issue('pair_membership', path, f'Undeclared subject/parameter pair {pair!r}.', row, 'UNDECLARED_GROUP')
            else:
                skipped.append(dict(code='NOT_EVALUATED', check='pair_membership', path=path,
                                    scope=dict(record=identity) if text(identity) else {},
                                    source_ids=[identity] if text(identity) else [],
                                    prerequisites=[key for key, valid in [('subject_reference', subject), ('parameter_reference', parameter),
                                                                          ('pair_declarations', pairs_available)] if not valid]))
    return report()
