"""Shared handling of the ``--include`` option used by Translator CLIs.

A CLI declares the extra fields it can add to its output as a list of
:class:`IncludeField`s wrapped in a :class:`FieldRegistry`. This module then
takes care of accepting them on the command line: matching user-typed names
(case-insensitively, treating ``-`` and ``_`` alike) to fields, supporting
aliases, and turning field values into output cells.

This module is tool-agnostic -- the actual fields live in each CLI's module.
"""
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass


def split_values(values: Iterable[str]) -> list[str]:
    """Flatten repeated and comma-separated option values into one list.

    Click hands us a tuple for a multi-valued option; this lets the user write
    either ``--include label --include type`` or ``--include label,type`` (or
    any mix of the two).
    """
    result = []
    for value in values:
        for piece in value.split(','):
            piece = piece.strip()
            if piece:
                result.append(piece)
    return result


def canonical(token: str) -> str:
    """Normalize a name so case and ``-``/``_`` differences don't matter."""
    return token.strip().lower().replace('_', '-')


@dataclass
class IncludeField:
    """One field a CLI can add to its output, e.g. ``label`` or ``type``."""

    name: str
    "The canonical name of the field."

    help: str
    "A short description, shown in the command's help text."

    extract: Callable
    "A function that pulls this field's value out of a per-item result."

    aliases: tuple[str, ...] = ()
    "Alternate names the user may type instead of ``name``."

    default: bool = False
    "Whether this field is included even when the user passes no ``--include``."


class FieldRegistry:
    """An ordered collection of :class:`IncludeField`s, looked up by name or alias."""

    def __init__(self, fields: list[IncludeField]):
        self.fields = fields
        self._by_name: dict[str, IncludeField] = {}
        for field in fields:
            for token in (field.name, *field.aliases):
                self._by_name[canonical(token)] = field

    @property
    def defaults(self) -> list[IncludeField]:
        """The fields included when the user passes no ``--include`` option."""
        return [field for field in self.fields if field.default]

    def resolve(self, names: Iterable[str]) -> list[IncludeField]:
        """Turn user-supplied ``--include`` names into :class:`IncludeField`s.

        The default fields always come first. Unknown names raise
        :class:`ValueError` with a message listing the valid names.
        """
        chosen = list(self.defaults)
        for name in names:
            field = self._by_name.get(canonical(name))
            if field is None:
                valid = ', '.join(sorted(self._by_name))
                raise ValueError(f"unknown field '{name}'. Valid fields are: {valid}")
            if field not in chosen:
                chosen.append(field)
        return chosen

    def help_text(self) -> str:
        """A human-readable list of the available fields, for use in ``--help``."""
        lines = []
        for field in self.fields:
            names = ' / '.join((field.name, *field.aliases))
            suffix = '  [added by default]' if field.default else ''
            lines.append(f"  {names}{suffix}")
            lines.append(f"      {field.help}")
        return '\n'.join(lines)


def render_value(value, fmt: str, list_separator: str = '|'):
    """Prepare a field value for writing in the given output format.

    For JSON output, values keep their native type (lists stay lists, etc.).
    For CSV/TSV, every value becomes a single string cell: lists are joined with
    ``list_separator`` and dicts are written as compact JSON.
    """
    if fmt == 'json':
        return value
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, list):
        return list_separator.join('' if item is None else str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
