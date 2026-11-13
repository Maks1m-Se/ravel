"""Reject nonportable export namespaces before creating any output."""

import unicodedata

from .recipe import ValidationError


DEVICES = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


def reserved_name(name):
    stem = unicodedata.normalize('NFKC', name.split('.', 1)[0]).rstrip(' ').upper()
    return stem in DEVICES


def validate_names(names):
    """Check the complete flat namespace, including metadata sidecars."""
    seen = {}
    for name in names:
        if (not name or name[-1] in '. ' or
                any(ord(c) < 32 or c in '<>:"/\\|?*' for c in name)):
            raise ValidationError('export.files', f'Nonportable filename {name!r}; export refused before writing.')
        if reserved_name(name):
            raise ValidationError('export.files', f'Reserved Windows filename {name!r}; use a portable table ID or output filename. Export refused before writing.')
        key = name.casefold()
        if key in seen:
            raise ValidationError('export.files', f'Filenames {seen[key]!r} and {name!r} collide on Windows (case insensitive). Export refused before writing.')
        seen[key] = name
