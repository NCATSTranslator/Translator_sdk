# The `translator` command-line tool

A guide to adding standardized identifiers, names, and types to a spreadsheet of
biomedical data — no programming required.

## What this tool does

Biomedical data uses *identifiers* (also called CURIEs) to refer to genes,
diseases, drugs, and other concepts — short codes like `MESH:D014867` or
`NCBIGene:1756`. The same real-world thing usually has many different
identifiers, depending on which database it came from.

The `translator` tool takes a spreadsheet (CSV, TSV, or JSON) that has a column
of these identifiers and, for each one, looks it up in **NodeNorm** — a service
that knows which identifiers refer to the same thing and which one is
"preferred". It then writes your spreadsheet back out, unchanged, with **extra
columns added**: the preferred identifier, its name, its category, and anything
else you ask for.

Your original file is never modified — you get a fresh copy (or printed output)
with the extra columns.

## Trying it without installing anything

If you have [`uv`](https://docs.astral.sh/uv/) installed, you can run the tool
without installing it. `uvx` downloads it into a temporary, throwaway
environment and runs it straight away:

```
uvx --from translator-sdk translator normalize genes.csv --column curie
```

Nothing is permanently installed, and later runs reuse a cache.

> **Note:** the tool is not on PyPI yet, so `translator-sdk` is a placeholder
> name. This guide will be updated with the final name once it is published.

## Installing it

If you expect to use the tool regularly, install it once. With `uv`:

```
uv tool install translator-sdk
```

or with `pip`:

```
pip install translator-sdk
```

Either way, you then have a `translator` command you can run directly:

```
translator normalize genes.csv --column curie
```

The rest of this guide uses the short `translator …` form. If you prefer `uvx`,
just put `uvx --from translator-sdk` in front of every command.

## Your first run

Suppose you have a file `genes.csv`:

```
gene_symbol,curie
water,MESH:D014867
dystrophin,NCBIGene:1756
```

Run:

```
translator normalize genes.csv --column curie --include label,type
```

You will see:

```
gene_symbol,curie,curie_normalized,curie_errors,curie_label,curie_type
water,MESH:D014867,CHEBI:15377,,Water,biolink:SmallMolecule
dystrophin,NCBIGene:1756,NCBIGene:1756,,DMD,biolink:Gene
```

Your two original columns are untouched, and four new columns were added:

- `curie_normalized` — the preferred identifier NodeNorm chose,
- `curie_errors` — empty here, because both lookups succeeded,
- `curie_label` — the preferred name,
- `curie_type` — the kind of thing it is.

By default the result is printed to the screen. To save it to a file instead,
use `--output` (described below).

## The options you will use most

### Choosing which column(s) to normalize: `--column`

`--column` (or `-c`) tells the tool which column holds identifiers. It is
required. To normalize more than one column, repeat it:

```
translator normalize data.csv --column subject_id --column object_id
```

Each column is looked up separately and gets its own set of new columns.

### Choosing what to add: `--include`

`--include` (or `-i`) picks the extra columns. List them separated by commas, or
repeat the option — these two commands do the same thing:

```
translator normalize genes.csv --column curie --include label,type,description
translator normalize genes.csv --column curie -i label -i type -i description
```

Two columns are **always** added — `normalized` (the preferred identifier) and
`errors` — so you never lose track of what happened.

Field names are forgiving: you can write `name` or `label`, `type` or
`category`, and capitalization or `-`/`_` do not matter. The most useful fields
are:

| Ask for | You get |
|---|---|
| `label` (or `name`) | the preferred name, e.g. `Water` |
| `type` (or `category`) | the kind of thing, e.g. `biolink:Gene` |
| `description` | a sentence describing it |
| `taxa` | the organism(s) it belongs to |
| `equivalent-identifiers` (or `synonyms`) | every other identifier for the same thing |
| `json` | the complete raw NodeNorm response |

For the full list, run `translator normalize --help`.

### Saving the result: `--output`

By default the new table is printed to the screen. Use `--output` (or `-o`) to
write it to a file:

```
translator normalize genes.csv --column curie --output genes_normalized.csv
```

### CSV, TSV, and JSON

The tool reads and writes three formats: comma-separated (`.csv`), tab-separated
(`.tsv`), and `.json`. It works out the format from the file's extension, and
the output is always in the same format as the input.

When you read from a pipe instead of a file (see below) there is no extension to
go by, so add `--format csv` (or `tsv`, or `json`).

### Conflation: `--conflation`

"Conflation" means treating closely related things as a single entry. NodeNorm
can do two kinds:

- **Gene/protein conflation** treats a gene and the protein it codes for as the
  same entry. It is **on by default**, because it is usually what you want.
- **Drug/chemical conflation** treats a drug and its underlying chemical as the
  same entry. It is **off by default**.

Most of the time you do not need to change this. If you do, `--conflation`
accepts any of `gene-protein`, `drug-chemical`, `all`, or `none`:

```
translator normalize genes.csv --column curie --conflation all
translator normalize genes.csv --column curie --conflation none
```

Whatever you list is exactly what gets turned on — so `--conflation drug-chemical`
turns gene/protein conflation *off* and drug/chemical conflation *on*.

## Using it in a pipeline

The tool can read from another program instead of a file. Use `-` in place of
the filename, and tell it the format:

```
cat genes.csv | translator normalize - --format csv --column curie
```

This makes it easy to drop into a larger workflow — for example, producing a
list of identifiers with one command and normalizing it with the next.

## Understanding the new columns

Every added column is named `<column>_<field>` — the name of the column you
normalized, an underscore, then the field. Normalizing a column called `curie`
and asking for `label` gives you `curie_label`; normalizing `subject_id` gives
`subject_id_label`. This keeps things clear when you normalize several columns at
once.

If a column with that name already exists (for example, because you ran the tool
twice), it is refreshed in place rather than duplicated — so re-running is safe.

## When something goes wrong

The `errors` column is the first place to look. For a row that worked it is
empty; otherwise it explains what happened:

- **`not found in NodeNorm`** — NodeNorm has no record of that identifier. Check
  it for typos, and make sure it includes its prefix (for example
  `MESH:D014867`, not just `D014867`).
- **`NodeNorm request failed: …`** — the tool could not reach the NodeNorm
  service. This is usually a temporary network problem; try again.

A blank cell in your input column is left blank in the output, with no error.

## Seeing every option

This guide covers the common cases. For the complete list of every command and
option, see the **[command reference](cli-reference.md)**, or run:

```
translator --help
translator normalize --help
```
