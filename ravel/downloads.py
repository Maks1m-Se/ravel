"""Portable browser download names; export contents stay with their serializers."""

import re
import unicodedata

from .exports import reserved_name


def table_stem(name):
    normalized = unicodedata.normalize('NFKC', name).casefold()
    normalized = ''.join(c if c.isalnum() or c in '_-' else '_' for c in normalized)
    stem = re.sub('_+', '_', normalized).strip('_-')[:80].rstrip('_-') or 'table'
    if reserved_name(stem):
        stem = 'table_' + stem
    return stem
