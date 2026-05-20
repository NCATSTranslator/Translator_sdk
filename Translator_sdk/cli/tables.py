"""Reading and writing the CSV/TSV/JSON record files that Translator CLIs use.

A "table" here is a list of row dicts plus an ordered list of column names.

We deliberately use the standard library's ``csv`` and ``json`` modules rather
than pandas: a CLI must echo its input back unchanged except for the columns it
adds, and ``csv`` keeps every cell exactly as written instead of coercing
numbers, dates and blanks the way pandas would.

This module is tool-agnostic -- it knows about file formats, nothing else.
"""
import csv
import io
import json
import sys
from pathlib import Path


# The delimiter ``csv`` should use for each delimited format. JSON is separate.
_DELIMITERS = {'csv': ',', 'tsv': '\t'}

# Which format a given file extension implies.
_EXTENSIONS = {
    '.csv': 'csv',
    '.tsv': 'tsv',
    '.tab': 'tsv',
    '.json': 'json',
}

#: The formats these CLIs can read and write.
FORMATS = ('csv', 'tsv', 'json')


class TableError(Exception):
    """Raised when an input file cannot be read as a table."""


def infer_format(path: str | None, override: str | None) -> str:
    """Decide which file format to use.

    An explicit ``override`` (from ``--format``) always wins. Otherwise the
    format is taken from the file extension. Reading from stdin without an
    extension and without ``--format`` raises :class:`TableError`.
    """
    if override:
        return override
    if path and path != '-':
        ext = Path(path).suffix.lower()
        if ext in _EXTENSIONS:
            return _EXTENSIONS[ext]
        raise TableError(
            f"cannot tell the format of '{path}' from its extension; "
            f"pass --format (one of: {', '.join(FORMATS)})"
        )
    raise TableError(
        f"reading from standard input requires --format (one of: {', '.join(FORMATS)})"
    )


def read_table(path: str | None, fmt: str) -> tuple[list[dict], list[str]]:
    """Read a table from ``path`` (or stdin when ``path`` is ``None`` or ``'-'``).

    Returns ``(rows, fieldnames)``, where ``rows`` is a list of dicts and
    ``fieldnames`` preserves the input column order.
    """
    text = _read_text(path)
    if fmt == 'json':
        return _read_json(text)
    return _read_delimited(text, _DELIMITERS[fmt])


def write_table(rows: list[dict], fieldnames: list[str], path: str | None, fmt: str) -> None:
    """Write a table to ``path`` (or stdout when ``path`` is ``None`` or ``'-'``)."""
    if fmt == 'json':
        _write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n', path)
    else:
        _write_delimited(rows, fieldnames, path, _DELIMITERS[fmt])


def _read_text(path: str | None) -> str:
    if path in (None, '-'):
        return sys.stdin.read()
    return Path(path).read_text(encoding='utf-8')


def _write_text(content: str, path: str | None) -> None:
    if path in (None, '-'):
        sys.stdout.write(content)
    else:
        Path(path).write_text(content, encoding='utf-8')


def _read_delimited(text: str, delimiter: str) -> tuple[list[dict], list[str]]:
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if reader.fieldnames is None:
        raise TableError('the input file is empty (no header row).')
    fieldnames = list(reader.fieldnames)
    return [dict(row) for row in reader], fieldnames


def _write_delimited(rows: list[dict], fieldnames: list[str], path: str | None, delimiter: str) -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=fieldnames, delimiter=delimiter,
        restval='', extrasaction='ignore', lineterminator='\n',
    )
    writer.writeheader()
    writer.writerows(rows)
    _write_text(buffer.getvalue(), path)


def _read_json(text: str) -> tuple[list[dict], list[str]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TableError(f'the input file is not valid JSON: {exc}')
    if not isinstance(data, list):
        raise TableError('JSON input must be an array of objects (one object per row).')
    rows: list[dict] = []
    fieldnames: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise TableError(
                f'JSON input must be an array of objects; item {index} is a {type(item).__name__}.'
            )
        rows.append(item)
        for key in item:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    return rows, fieldnames
