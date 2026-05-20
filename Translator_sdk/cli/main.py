"""The ``translator`` command -- an umbrella for the Translator SDK's CLIs.

Each Translator service gets its own subcommand. Today there is one,
``normalize`` (NodeNorm); adding another is a new module plus one
``cli.add_command`` line here.
"""
import click

from .normalize import normalize


@click.group()
@click.version_option(package_name='Translator_sdk')
def cli():
    """Command-line tools for the NCATS Biomedical Data Translator SDK.

    Each subcommand wraps one Translator service. Run `translator COMMAND
    --help` for details on a specific command.
    """


cli.add_command(normalize)
