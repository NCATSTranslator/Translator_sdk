# AGENTS.md

This file provides guidance to coding agents (Claude Code, Codex, etc.) when working with code in this repository.

## Commands

This project uses `uv` for dependency management and `make` for common tasks.

```bash
make install      # Install development dependencies (uv sync --dev)
make test         # Run tests with coverage
make lint         # Run ruff linting
make lint-fix     # Run ruff with automatic fixes
make format       # Format code with ruff
make spell        # Run codespell
make check        # Run all checks (lint, spell, test)
```

Run a single test file:
```bash
uv run pytest tests/test_nameres.py -v
```

Run a single test by name:
```bash
uv run pytest tests/test_nameres.py::test_nameres_status -v
```

Type checking:
```bash
uv run mypy Translator_sdk/
```

## Project context

This SDK was extracted from **[NCATSTranslator/Translator_component_toolkit](https://github.com/NCATSTranslator/Translator_component_toolkit)** (TCT). TCT is a broader Python library for exploring and using Translator Knowledge Graphs (KGs); all the modules in `Translator_sdk/` currently exist as duplicates inside `TCT/` in that repo.

The long-term goal is to **remove the duplicated code from TCT** and have TCT (and any other Translator component) import these shared utilities from `Translator_sdk` instead. When making changes here, keep in mind that the same logic may still exist in TCT and may need to be updated in sync until the migration is complete.

## Architecture

This is the **Translator SDK** — a Python library (`Translator_sdk` package) that wraps several NCATS Biomedical Data Translator REST APIs. The SDK provides typed Python interfaces to query knowledge provider (KP) APIs using TRAPI (Translator Reasoner API) format.

### Core data model (`translator_node.py`)
- `TranslatorNode`: represents a biomedical entity with a CURIE identifier, label, biolink types, synonyms, and attributes. This is the primary return type across all API wrappers.
- `TranslatorEdge`: represents a subject–predicate–object relationship.
- `TranslatorAttribute`: key-value attribute attached to nodes or edges.

### API wrappers
Each module wraps one external Translator service:

| Module | Service | Purpose |
|--------|---------|---------|
| `name_resolver.py` | NameRes (https://name-lookup.ci.transltr.io) | Convert human-readable names → CURIEs |
| `node_normalizer.py` | NodeNorm (https://nodenorm.ci.transltr.io) | Normalize CURIEs to preferred identifiers |
| `node_annotator.py` | Node Annotator (https://annotator.transltr.io) | Fetch annotations for CURIEs |
| `translator_query.py` | KP APIs via TRAPI | Build and dispatch TRAPI queries |
| `translator_metakg.py` | SmartAPI metaKG (https://smart-api.info) | Discover KP metadata and predicates |
| `translator_kpinfo.py` | SmartAPI (https://smart-api.info) | List available KPs and their URLs |

### Query flow (`translator_query.py`)
1. `get_translator_API_predicates()` — discovers all KPs and their supported predicates via SmartAPI
2. `build_query_json()` — constructs a TRAPI 1.5.0 query dict (subject IDs → predicates → object categories)
3. `optimize_query_json()` — filters predicates to those supported by a specific KP
4. `query_KP()` — sends a TRAPI query to one KP and returns the knowledge graph result
5. `parallel_api_query()` — queries multiple KPs concurrently and merges their edge results

### Command-line interface (`Translator_sdk/cli/`)
The SDK ships a `translator` command (the `[project.scripts]` entry point; also
runnable as `python -m Translator_sdk.cli`). It is an umbrella `click` group
with one subcommand per tool — currently `translator normalize` (NodeNorm).

The package is split so that adding a CLI for another tool is a new module plus
one `cli.add_command(...)` line in `cli/main.py`:
- `cli/tables.py` — tool-agnostic CSV/TSV/JSON record file I/O (stdlib `csv`/`json`, not pandas, so input is echoed back unchanged except for added columns).
- `cli/fields.py` — tool-agnostic `--include` handling: an `IncludeField`/`FieldRegistry` pair that resolves user-typed field names/aliases and renders values.
- `cli/normalize.py` — the NodeNorm-specific subcommand: its options, its `FIELDS` registry, and the per-CURIE result type.

`translator normalize` reads a CSV/TSV/JSON file, normalizes the CURIEs in the
`--column`(s) chosen by the user, and writes the same table back with
`<column>_<field>` columns appended for each `--include` field. Knowledge of the
NodeNorm request/response shape stays in `node_normalizer.py` — the CLI calls
`get_normalized_nodes_raw()` + `_node_from_response()` there.

### Tests
Tests make live network calls to external Translator endpoints. There are no mocks. Depending on wrapper defaults, those calls may go to CI-hosted services and/or non-CI/production Translator services (for example, NameRes and NodeNorm default to `*.ci.transltr.io`, while NodeAnnotator defaults to `https://annotator.transltr.io/`). Tests are in `tests/` and cover NameRes, NodeNorm, and NodeAnnotator wrappers, so expect external-service dependency and potential flakiness.

## Agent notes

- Always run `make check` before committing (runs lint, spell check, and tests).
- Do not break TCT compatibility without a migration plan — the same logic lives in `TCT/` until the migration is complete.
- `CLAUDE.md` is a symlink to this file; edit `AGENTS.md` directly.
