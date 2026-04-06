# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
| `name_resolver.py` | NameRes (name-lookup.ci.transltr.io) | Convert human-readable names → CURIEs |
| `node_normalizer.py` | NodeNorm (nodenorm.ci.transltr.io) | Normalize CURIEs to preferred identifiers |
| `node_annotator.py` | Node Annotator (annotator.transltr.io) | Fetch annotations for CURIEs |
| `translator_query.py` | KP APIs via TRAPI | Build and dispatch TRAPI queries |
| `translator_metakg.py` | SmartAPI metaKG | Discover KP metadata and predicates |
| `translator_kpinfo.py` | SmartAPI | List available KPs and their URLs |

### Query flow (`translator_query.py`)
1. `get_translator_API_predicates()` — discovers all KPs and their supported predicates via SmartAPI
2. `build_query_json()` — constructs a TRAPI 1.5.0 query dict (subject IDs → predicates → object categories)
3. `optimize_query_json()` — filters predicates to those supported by a specific KP
4. `query_KP()` — sends a TRAPI query to one KP and returns the knowledge graph result
5. `parallel_api_query()` — queries multiple KPs concurrently and merges their edge results

### Tests
Tests make live network calls to the Translator CI environment. There are no mocks. Tests are in `tests/` and cover NameRes, NodeNorm, and NodeAnnotator wrappers.
