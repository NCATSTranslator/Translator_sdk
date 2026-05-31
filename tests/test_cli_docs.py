"""Checks that the generated CLI reference is up to date.

If this test fails, run `make docs` to regenerate docs/cli-reference.md. This
test makes no network calls.
"""
from pathlib import Path

from Translator_sdk.cli.reference import render_reference

REFERENCE_PATH = Path(__file__).parent.parent / 'docs' / 'cli-reference.md'


def test_cli_reference_is_up_to_date():
    """docs/cli-reference.md must match the current CLI; run `make docs` if not."""
    committed = REFERENCE_PATH.read_text(encoding='utf-8')
    assert committed == render_reference(), (
        'docs/cli-reference.md is out of date with the CLI. '
        'Regenerate it with `make docs`.'
    )
