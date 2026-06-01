# Translator SDK

A Python library that wraps several [NCATS Biomedical Data Translator](https://ncats.nih.gov/translator)
REST APIs (NodeNorm, NameRes, Node Annotator, and others) behind typed,
consistent Python interfaces.

## Command-line tool

The SDK also ships a `translator` command for normalizing biomedical
identifiers in a spreadsheet — no Python required:

```
translator normalize genes.csv --column curie --include label,type
```

- **[Command-line tools guide](docs/command-line-tools.md)** — start here: a
  friendly, example-driven walkthrough of installing and using the tool.
- **[Command reference](docs/cli-reference.md)** — every command and option.

## Development

See [AGENTS.md](AGENTS.md) for the architecture overview, common `make` tasks,
and contributor notes. In short: `make install`, then `make check`.
