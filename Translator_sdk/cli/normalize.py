"""The ``translator normalize`` subcommand: normalize CURIEs with NodeNorm.

This is the NodeNorm-specific half of the CLI. It owns the command's options,
the registry of fields it can add (:data:`FIELDS`), and how a CURIE is turned
into a result. Everything format- or column-related lives in the shared
:mod:`.tables` and :mod:`.fields` modules; everything NodeNorm-API-related lives
in :mod:`Translator_sdk.node_normalizer`.
"""
from dataclasses import dataclass

import click
import requests

from ..node_normalizer import _node_from_response, get_normalized_nodes_raw
from ..translator_node import TranslatorNode
from .fields import FieldRegistry, IncludeField, render_value, split_values
from .tables import TableError, infer_format, read_table, write_table

# NodeNorm accepts large POST batches; this keeps each request comfortably sized.
_BATCH_SIZE = 900

# The conflation options the user may pass to --conflation.
_CONFLATION_CHOICES = ('gene-protein', 'drug-chemical', 'all', 'none')


@dataclass
class CurieResult:
    """The outcome of normalizing one CURIE.

    Exactly one of (a normalized ``node``) or (an ``error`` message) is set.
    """

    node: TranslatorNode | None = None
    raw: dict | None = None
    error: str | None = None


def _node_attr(getter):
    """Wrap a node getter so it yields ``None`` when there is no normalized node."""
    return lambda result: getter(result.node) if result.node is not None else None


#: Every field ``translator normalize`` can add, keyed by name and aliases.
FIELDS = FieldRegistry([
    IncludeField(
        'normalized', 'the preferred (normalized) CURIE',
        _node_attr(lambda n: n.curie),
        aliases=('id', 'curie', 'identifier'), default=True,
    ),
    IncludeField(
        'errors', 'a message if the CURIE could not be normalized (empty otherwise)',
        lambda result: result.error,
        aliases=('error',), default=True,
    ),
    IncludeField(
        'label', 'the preferred name of the normalized node',
        _node_attr(lambda n: n.label),
        aliases=('name', 'preferred-name'),
    ),
    IncludeField(
        'description', 'a human-readable description of the node',
        _node_attr(lambda n: n.description),
        aliases=('desc', 'descriptions'),
    ),
    IncludeField(
        'type', 'the most specific biolink type of the node',
        _node_attr(lambda n: n.types[0] if n.types else None),
        aliases=('category',),
    ),
    IncludeField(
        'types', 'every biolink type of the node',
        _node_attr(lambda n: n.types),
        aliases=('categories', 'all-types'),
    ),
    IncludeField(
        'taxa', 'the taxa (organisms) associated with the node',
        _node_attr(lambda n: n.taxa),
        aliases=('taxon', 'taxonomy'),
    ),
    IncludeField(
        'information-content', "NodeNorm's information content score (higher is more specific)",
        _node_attr(lambda n: n.information_content),
        aliases=('ic', 'info-content'),
    ),
    IncludeField(
        'equivalent-identifiers', 'every CURIE NodeNorm considers equivalent to this one',
        _node_attr(lambda n: n.curie_synonyms),
        aliases=('synonyms', 'eq-ids'),
    ),
    IncludeField(
        'json', 'the complete raw NodeNorm response for the CURIE',
        lambda result: result.raw,
        aliases=('raw',),
    ),
])


def _resolve_conflation(values: list[str]) -> tuple[bool, bool]:
    """Turn ``--conflation`` values into NodeNorm's two conflation booleans.

    With no values, NodeNorm's defaults are used (gene/protein on, drug/chemical
    off). Otherwise the result is exactly the set of conflations the user named.
    """
    if not values:
        return True, False
    conflate = drug_chemical = False
    for raw in values:
        value = raw.strip().lower().replace('_', '-')
        if value == 'all':
            conflate = drug_chemical = True
        elif value == 'none':
            conflate = drug_chemical = False
        elif value == 'gene-protein':
            conflate = True
        elif value == 'drug-chemical':
            drug_chemical = True
        else:
            raise click.BadParameter(
                f"'{raw}' is not valid. Choose from: {', '.join(_CONFLATION_CHOICES)}.",
                param_hint='--conflation',
            )
    return conflate, drug_chemical


def _normalize_curies(curies: list[str], *, conflate: bool, drug_chemical_conflate: bool,
                      description: bool, individual_types: bool) -> dict[str, CurieResult]:
    """Normalize a list of unique CURIEs, returning a dict from CURIE to result.

    A CURIE NodeNorm has never heard of, and a CURIE in a batch whose request
    failed, both come back as a :class:`CurieResult` carrying an ``error`` --
    one bad batch never aborts the whole run.
    """
    results: dict[str, CurieResult] = {}
    for start in range(0, len(curies), _BATCH_SIZE):
        batch = curies[start:start + _BATCH_SIZE]
        try:
            raw_nodes = get_normalized_nodes_raw(
                batch, mode='post',
                conflate=conflate, drug_chemical_conflate=drug_chemical_conflate,
                description=description, individual_types=individual_types,
            )
        except requests.RequestException as exc:
            for curie in batch:
                results[curie] = CurieResult(error=f'NodeNorm request failed: {exc}')
            continue
        for curie in batch:
            raw_node = raw_nodes.get(curie)
            if raw_node is None:
                results[curie] = CurieResult(error='not found in NodeNorm')
            else:
                results[curie] = CurieResult(node=_node_from_response(raw_node), raw=raw_node)
    return results


@click.command(
    epilog='\b\nFields available for --include / -i:\n' + FIELDS.help_text(),
)
@click.argument(
    'input_file', metavar='INPUT', required=False, default='-',
    type=click.Path(exists=True, dir_okay=False, allow_dash=True),
)
@click.option(
    '-c', '--column', 'columns', multiple=True, required=True,
    help='Input column holding CURIEs to normalize. Repeatable; '
         'comma-separated values also work.',
)
@click.option(
    '-i', '--include', 'includes', multiple=True,
    help="Extra field(s) to add for each normalized CURIE (see the list below). "
         "Repeatable; comma-separated values also work. "
         "'normalized' and 'errors' are always added.",
)
@click.option(
    '-o', '--output', default='-', type=click.Path(dir_okay=False, allow_dash=True),
    help='Where to write the result. Defaults to standard output.',
)
@click.option(
    '--format', 'fmt_override', type=click.Choice(['csv', 'tsv', 'json']),
    help='Input/output format. Inferred from the file extension when not given; '
         'required when reading from standard input.',
)
@click.option(
    '--conflation', 'conflation', multiple=True,
    help="NodeNorm conflation to apply: 'gene-protein', 'drug-chemical', 'all' "
         "or 'none'. Repeatable. Default: gene-protein only.",
)
@click.option(
    '--individual-types', is_flag=True,
    help='Ask NodeNorm to include the biolink type of each equivalent identifier '
         '(visible via --include json).',
)
@click.option(
    '--list-separator', default='|', show_default=True,
    help='String used to join list-valued cells in CSV/TSV output.',
)
def normalize(input_file, columns, includes, output, fmt_override, conflation,
              individual_types, list_separator):
    """Normalize CURIEs in a CSV, TSV or JSON file using NodeNorm.

    INPUT is the file to read, or '-' to read from standard input. The output is
    the same table with extra columns added for the CURIEs in each --column.
    Added columns are named <column>_<field>, for example id_normalized and
    id_label.

    \b
    Examples:
      translator normalize genes.csv --column gene_id --include label,type
      translator normalize ids.json -c curie -i label -o normalized.json
      cat ids.tsv | translator normalize - --format tsv -c id
    """
    # Read the input table.
    try:
        fmt = infer_format(input_file, fmt_override)
        rows, fieldnames = read_table(input_file, fmt)
    except TableError as exc:
        raise click.ClickException(str(exc))

    # Validate the requested columns and --include fields.
    columns = split_values(columns)
    missing = [column for column in columns if column not in fieldnames]
    if missing:
        raise click.ClickException(
            f"input has no column(s): {', '.join(missing)}. "
            f"Available columns: {', '.join(fieldnames) or '(none)'}."
        )
    try:
        chosen_fields = FIELDS.resolve(split_values(includes))
    except ValueError as exc:
        raise click.ClickException(str(exc))

    conflate, drug_chemical_conflate = _resolve_conflation(split_values(conflation))
    # Descriptions are only in the response when we ask NodeNorm for them.
    want_description = any(field.name == 'description' for field in chosen_fields)

    # Gather every CURIE that appears in a selected column, then normalize once.
    curies = sorted({
        cell
        for row in rows for column in columns
        if (cell := (row.get(column) or '').strip())
    })
    results = _normalize_curies(
        curies,
        conflate=conflate, drug_chemical_conflate=drug_chemical_conflate,
        description=want_description, individual_types=individual_types,
    )

    # Add a <column>_<field> column for every selected column and chosen field.
    # A name that already exists is refreshed in place, so re-running is safe.
    new_fieldnames = [
        f'{column}_{field.name}'
        for column in columns for field in chosen_fields
    ]
    for row in rows:
        for column in columns:
            curie = (row.get(column) or '').strip()
            result = results.get(curie) if curie else None
            for field in chosen_fields:
                value = field.extract(result) if result is not None else None
                row[f'{column}_{field.name}'] = render_value(value, fmt, list_separator)

    output_fieldnames = fieldnames + [
        name for name in new_fieldnames if name not in fieldnames
    ]
    write_table(rows, output_fieldnames, output, fmt)
