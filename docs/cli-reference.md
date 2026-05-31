<!-- Generated from the translator CLI by `make docs`. Do not edit by hand. -->

# `translator` command reference

This page lists every command and option. It is generated automatically from the
CLI, so it always matches the current version. For a friendly, example-driven
introduction, see the [command-line tools guide](command-line-tools.md).

## `translator`

```
Usage: translator [OPTIONS] COMMAND [ARGS]...

  Command-line tools for the NCATS Biomedical Data Translator SDK.

  Each subcommand wraps one Translator service. Run `translator COMMAND --help`
  for details on a specific command.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  normalize  Normalize CURIEs in a CSV, TSV or JSON file using NodeNorm.
```

## `translator normalize`

```
Usage: translator normalize [OPTIONS] INPUT

  Normalize CURIEs in a CSV, TSV or JSON file using NodeNorm.

  INPUT is the file to read, or '-' to read from standard input. The output is
  the same table with extra columns added for the CURIEs in each --column. Added
  columns are named <column>_<field>, for example id_normalized and id_label.

  Examples:
    translator normalize genes.csv --column gene_id --include label,type
    translator normalize ids.json -c curie -i label -o normalized.json
    cat ids.tsv | translator normalize - --format tsv -c id

Options:
  -c, --column TEXT        Input column holding CURIEs to normalize. Repeatable;
                           comma-separated values also work.  [required]
  -i, --include TEXT       Extra field(s) to add for each normalized CURIE (see
                           the list below). Repeatable; comma-separated values
                           also work. 'normalized' and 'errors' are always
                           added.
  -o, --output FILE        Where to write the result. Defaults to standard
                           output.
  --format [csv|tsv|json]  Input/output format. Inferred from the file extension
                           when not given; required when reading from standard
                           input.
  --conflation TEXT        NodeNorm conflation to apply: 'gene-protein', 'drug-
                           chemical', 'all' or 'none'. Repeatable. Default:
                           gene-protein only.
  --individual-types       Ask NodeNorm to include the biolink type of each
                           equivalent identifier (visible via --include json).
  --list-separator TEXT    String used to join list-valued cells in CSV/TSV
                           output.  [default: |]
  --url URL                Base URL of the NodeNorm service to use. Defaults to
                           https://nodenorm.ci.transltr.io/. Example:
                           https://nodenormalization-sri.renci.org/ for the
                           RENCI Dev instance.
  --help                   Show this message and exit.

  Fields available for --include / -i:
    normalized / id / curie / identifier  [added by default]
        the preferred (normalized) CURIE
    errors / error  [added by default]
        a message if the CURIE could not be normalized (empty otherwise)
    label / name / preferred-name
        the preferred name of the normalized node
    description / desc / descriptions
        a human-readable description of the node
    type / category
        the most specific biolink type of the node
    types / categories / all-types
        every biolink type of the node
    taxa / taxon / taxonomy
        the taxa (organisms) associated with the node
    information-content / ic / info-content
        NodeNorm's information content score (higher is more specific)
    equivalent-identifiers / synonyms / eq-ids
        every CURIE NodeNorm considers equivalent to this one
    json / raw
        the complete raw NodeNorm response for the CURIE
```
