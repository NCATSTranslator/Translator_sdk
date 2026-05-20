"""Renders the ``translator`` CLI's help as a Markdown reference document.

``make docs`` runs this module to regenerate ``docs/cli-reference.md``, and
``tests/test_cli_docs.py`` checks that the committed file still matches -- so the
reference can never silently drift from the CLI.
"""
import click

from .main import cli

_HEADER = """<!-- Generated from the translator CLI by `make docs`. Do not edit by hand. -->

# `translator` command reference

This page lists every command and option. It is generated automatically from the
CLI, so it always matches the current version. For a friendly, example-driven
introduction, see the [command-line tools guide](command-line-tools.md)."""


def _command_section(command: click.Command, path: str) -> str:
    """Render one command's ``--help`` output as a Markdown section."""
    # A fixed terminal width keeps the output identical regardless of the
    # terminal `make docs` happens to run in, so the freshness test is stable.
    context = click.Context(command, info_name=path, terminal_width=80)
    return f"## `{path}`\n\n```\n{command.get_help(context).rstrip()}\n```"


def render_reference() -> str:
    """Return the full Markdown reference for the ``translator`` CLI."""
    sections = [_HEADER, _command_section(cli, 'translator')]
    for name, command in sorted(cli.commands.items()):
        sections.append(_command_section(command, f'translator {name}'))
    return '\n\n'.join(sections) + '\n'


if __name__ == '__main__':
    print(render_reference(), end='')
