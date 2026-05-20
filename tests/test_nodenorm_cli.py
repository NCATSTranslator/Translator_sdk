"""End-to-end tests for the `translator normalize` CLI.

Like the rest of this repo's tests, these make live calls to NodeNorm -- there
are no mocks, so expect external-service dependency and occasional flakiness.
"""
import csv
import io
import json
from pathlib import Path

from click.testing import CliRunner

from Translator_sdk.cli import cli

DATA = Path(__file__).parent / 'data'


def run(*args, **kwargs):
    """Invoke the translator CLI and return the click Result."""
    return CliRunner().invoke(cli, list(args), **kwargs)


def all_text(result):
    """Combined stdout + stderr of a CLI run (click version-agnostic)."""
    text = result.output
    try:
        text += result.stderr
    except (ValueError, AttributeError):
        pass
    return text


def read_csv(text, delimiter=','):
    """Parse CLI CSV/TSV output into (rows, fieldnames)."""
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return list(reader), reader.fieldnames


def test_normalize_csv_adds_prefixed_columns():
    """A CSV is echoed back unchanged, with <column>_<field> columns appended."""
    result = run('normalize', str(DATA / 'sample.csv'),
                 '--column', 'curie', '--include', 'label,type')
    assert result.exit_code == 0, all_text(result)
    rows, fieldnames = read_csv(result.output)

    # Original columns are preserved, in order, before the added ones.
    assert fieldnames == ['gene_symbol', 'curie', 'source',
                          'curie_normalized', 'curie_errors',
                          'curie_label', 'curie_type']
    assert [r['gene_symbol'] for r in rows] == ['water', 'DMD', 'unknown']

    # A resolvable CURIE is normalized; the error cell is empty.
    assert rows[0]['curie_normalized'] == 'CHEBI:15377'
    assert rows[0]['curie_label'] == 'Water'
    assert rows[0]['curie_type'] == 'biolink:SmallMolecule'
    assert rows[0]['curie_errors'] == ''

    # An unresolvable CURIE yields an error cell rather than crashing.
    assert rows[2]['curie_normalized'] == ''
    assert 'not found' in rows[2]['curie_errors']


def test_normalize_json_keeps_lists_and_passes_through():
    """JSON output keeps native types: list-valued fields stay JSON arrays."""
    result = run('normalize', str(DATA / 'sample.json'),
                 '--column', 'curie', '--include', 'types')
    assert result.exit_code == 0, all_text(result)
    rows = json.loads(result.output)

    assert rows[0]['gene_symbol'] == 'water'
    assert rows[0]['curie_normalized'] == 'CHEBI:15377'
    assert isinstance(rows[0]['curie_types'], list)
    assert 'biolink:SmallMolecule' in rows[0]['curie_types']

    assert rows[2]['curie_normalized'] is None
    assert 'not found' in rows[2]['curie_errors']


def test_normalize_tsv_to_output_file(tmp_path):
    """A TSV in -> a TSV out, written to the --output file."""
    out = tmp_path / 'out.tsv'
    result = run('normalize', str(DATA / 'sample.tsv'),
                 '--column', 'curie', '--output', str(out))
    assert result.exit_code == 0, all_text(result)

    rows, fieldnames = read_csv(out.read_text(), delimiter='\t')
    assert fieldnames == ['gene_symbol', 'curie', 'source',
                          'curie_normalized', 'curie_errors']
    assert rows[0]['curie_normalized'] == 'CHEBI:15377'


def test_reads_from_stdin_with_format():
    """Input can come from stdin when --format says how to read it."""
    result = run('normalize', '-', '--format', 'csv', '--column', 'curie',
                 input='curie\nMESH:D014867\n')
    assert result.exit_code == 0, all_text(result)
    rows, _ = read_csv(result.output)
    assert rows[0]['curie_normalized'] == 'CHEBI:15377'


def test_include_aliases_and_default_columns():
    """`name` is an alias of `label`; `normalized`/`errors` are always added."""
    result = run('normalize', str(DATA / 'sample.csv'),
                 '--column', 'curie', '--include', 'name')
    assert result.exit_code == 0, all_text(result)
    _, fieldnames = read_csv(result.output)
    assert fieldnames == ['gene_symbol', 'curie', 'source',
                          'curie_normalized', 'curie_errors', 'curie_label']


def test_multiple_columns_each_get_their_own_outputs():
    """Each --column is normalized independently into its own prefixed columns."""
    result = run('normalize', '-', '--format', 'csv',
                 '--column', 'a', '--column', 'b',
                 input='a,b\nMESH:D014867,NCBIGene:1756\n')
    assert result.exit_code == 0, all_text(result)
    rows, fieldnames = read_csv(result.output)
    assert fieldnames == ['a', 'b', 'a_normalized', 'a_errors',
                          'b_normalized', 'b_errors']
    assert rows[0]['a_normalized'] == 'CHEBI:15377'
    assert rows[0]['b_normalized'] == 'NCBIGene:1756'


def test_conflation_changes_the_result():
    """Gene/protein conflation is on by default and can be turned off."""
    data = 'curie\nPR:P11532\n'
    default = run('normalize', '-', '--format', 'csv', '--column', 'curie',
                  input=data)
    no_conflation = run('normalize', '-', '--format', 'csv', '--column', 'curie',
                        '--conflation', 'none', input=data)
    assert default.exit_code == 0, all_text(default)
    assert no_conflation.exit_code == 0, all_text(no_conflation)

    default_curie = read_csv(default.output)[0][0]['curie_normalized']
    no_conflation_curie = read_csv(no_conflation.output)[0][0]['curie_normalized']
    assert default_curie == 'NCBIGene:1756'          # gene/protein conflation on
    assert no_conflation_curie == 'UniProtKB:P11532'  # conflation off


def test_empty_cell_is_left_blank():
    """An empty input cell produces blank output cells and no error."""
    result = run('normalize', '-', '--format', 'csv', '--column', 'curie',
                 input='curie,note\n,a row with no curie\n')
    assert result.exit_code == 0, all_text(result)
    rows, _ = read_csv(result.output)
    assert rows[0]['note'] == 'a row with no curie'
    assert rows[0]['curie_normalized'] == ''
    assert rows[0]['curie_errors'] == ''


def test_unknown_column_is_a_friendly_error():
    """An unknown --column fails clearly and lists the available columns."""
    result = run('normalize', str(DATA / 'sample.csv'), '--column', 'nope')
    assert result.exit_code != 0
    message = all_text(result)
    assert 'no column' in message
    assert 'curie' in message


def test_unknown_include_is_a_friendly_error():
    """An unknown --include field fails clearly."""
    result = run('normalize', str(DATA / 'sample.csv'),
                 '--column', 'curie', '--include', 'bogus')
    assert result.exit_code != 0
    assert "unknown field 'bogus'" in all_text(result)


def test_stdin_requires_an_explicit_format():
    """Reading from stdin without --format is a clear error."""
    result = run('normalize', '-', '--column', 'curie',
                 input='curie\nMESH:D014867\n')
    assert result.exit_code != 0
    assert '--format' in all_text(result)
