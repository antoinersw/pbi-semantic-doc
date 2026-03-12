# pbi-semantic-doc

**Automatic documentation generator and analyzer for Power BI projects.**

[![PyPI version](https://img.shields.io/pypi/v/pbi-semantic-doc)](https://pypi.org/project/pbi-semantic-doc/)
[![Python 3.9+](https://img.shields.io/pypi/pyversions/pbi-semantic-doc)](https://pypi.org/project/pbi-semantic-doc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-138%20passing-brightgreen)](#)

Built with ❤️ by [ViciusLio](https://github.com/ViciusLio) in collaboration with [Claude AI](https://claude.ai) (Anthropic).

---

If your Power BI project lives in a Git repository as a `.pbip` project, this tool can:

- **Document semantic models** (TMDL format) — tables, columns, measures, relationships, DAX patterns, complexity index
- **Analyze reports** (PBIR and PBIR-Legacy) — pages, visuals, bookmarks, visual type distribution, complexity index

Zero configuration. Zero external dependencies. Drop it into any pipeline.

```bash
pip install pbi-semantic-doc

# Document a semantic model
pbi-semantic-doc ./MyProject.SemanticModel --output docs/MODEL.md

# Analyze a report
pbi-semantic-doc ./MyProject.Report --analyze-report --output docs/REPORT.md

# Both at once (from the .pbip project folder)
pbi-semantic-doc ./MyProject --combined --output docs/FULL.md
```

---

## Why this exists

Power BI semantic models have become real codebases. With `.pbip` projects and TMDL, every table, measure, and relationship is a text file you can version, review, and diff. The tooling around that workflow is still catching up: there is no built-in way to generate human-readable documentation from a semantic model without opening Power BI Desktop or paying for a third-party service.

`pbi-semantic-doc` fills that gap. It is a plain Python CLI tool you can drop into any pipeline — a pre-commit hook, a GitHub Action, a local script — and get documentation that stays in sync with your model automatically.

---

## Installation

```bash
pip install pbi-semantic-doc
```

Or from source:

```bash
git clone https://github.com/ViciusLio/pbi-semantic-doc
cd pbi-semantic-doc
pip install -e .
```

---

## Usage

### Semantic Model Documentation

```bash
# Basic — writes MODEL_DOC.md inside the model folder
pbi-semantic-doc ./MyProject.SemanticModel

# Specify output path
pbi-semantic-doc ./MyProject.SemanticModel --output ./docs/MODEL.md

# Point to the .pbip parent folder (auto-discovers the .SemanticModel subfolder)
pbi-semantic-doc . --output MODEL.md

# Suppress console output (useful in CI)
pbi-semantic-doc ./MyProject.SemanticModel --output ./docs/MODEL.md --quiet
```

### Report Analysis

```bash
# Markdown output (default)
pbi-semantic-doc ./MyProject.Report --analyze-report --output ./docs/REPORT.md

# JSON output for programmatic use
pbi-semantic-doc ./MyProject.Report --analyze-report --format json --output analysis.json

# Text summary to console
pbi-semantic-doc ./MyProject.Report --analyze-report --format text
```

### Combined Analysis

```bash
# Analyze both model and report from a .pbip project folder
pbi-semantic-doc ./MyProject --combined --output ./docs/FULL.md

# JSON combined output
pbi-semantic-doc ./MyProject --combined --format json --output analysis.json
```

### CLI reference

| Flag | Description |
|------|-------------|
| `PATH` | Path to `.SemanticModel`, `.Report`, or `.pbip` project folder |
| `--analyze-report` | Analyze report instead of semantic model |
| `--combined` | Analyze both semantic model and report |
| `--format` | Output format: `md` (default), `json`, `text` |
| `--output`, `-o` | Output file path |
| `--quiet`, `-q` | Suppress console output |

---

## Expected folder structure

```
MyProject/
├── MyProject.pbip
├── MyProject.SemanticModel/
│   └── definition/
│       ├── model.tmdl
│       ├── relationships.tmdl
│       └── tables/
│           ├── Sales.tmdl
│           └── Calendar.tmdl
└── MyProject.Report/
    └── definition/
        ├── version.json
        ├── pages/                    # PBIR format (new)
        │   └── Page1/
        │       ├── page.json
        │       └── visuals/
        │           └── Visual1/
        │               └── visual.json
        ├── bookmarks/
        │   └── Bookmark1.bookmark.json
        ├── reportExtensions.json
        └── report.json               # PBIR-Legacy format (old)
```

---

## Features

### Semantic Model Documentation
- Parses standard TMDL folder structure (`.pbip` projects, Power BI Desktop)
- Documents tables, columns (data types, descriptions, hidden status), measures (full DAX), and relationships
- Generates automatic DAX pattern descriptions when no manual description is present
- Extracts model name from the `.SemanticModel` folder name
- **Complexity Index** — normalized 0–1 score per model (see below)

### Report Analysis
- Supports **PBIR** (folder-based, new) and **PBIR-Legacy** (`report.json`) formats
- Classifies all standard and custom visual types
- Detects mobile layouts, drill-through pages, hidden pages, filters
- Identifies custom marketplace visuals by name
- **Complexity Index** — normalized 0–1 score per report (see below)
- Outputs Markdown, JSON, and plain text

### General
- Zero external dependencies — pure Python 3.9+ stdlib
- Installable via pip; works as a CLI or Python library
- CI/CD ready (GitHub Actions, pre-commit hooks)
- Windows-compatible (Unicode on cp1252 terminals)

---

## Complexity Index

Both the semantic model and the report get a normalized **0–1 complexity score**.

### Semantic Model

| Dimension | Weight | Reference maximum |
|-----------|--------|-------------------|
| Visible tables | 20% | 30 tables |
| Measures | 30% | 150 measures |
| Measure DAX complexity (avg) | 30% | — |
| Relationships | 10% | 50 relationships |
| Columns | 10% | 300 columns |

**Measure DAX complexity** is itself a 0–1 score per measure, combining:
- Expression length (40%) — normalized to 500 characters
- Detected pattern count (60%) — CALCULATE, VAR, time intelligence, iterators, filter modifiers, RANKX, SWITCH, USERELATIONSHIP (max 5 distinct categories)

### Report

| Dimension | Weight | Reference maximum |
|-----------|--------|-------------------|
| Pages | 25% | 50 pages |
| Visuals | 45% | 300 visuals |
| Bookmarks | 20% | 30 bookmarks |
| Report-level measures | 10% | 10 measures |

A score of **0.5 (50%)** indicates a moderately complex model or report. Both scores are always in the 0–1 range.

---

## DAX pattern recognition

Automatic measure descriptions are generated by inspecting DAX expressions. Recognized patterns:

| Category | Functions |
|----------|-----------|
| Aggregations | `SUM`, `AVERAGE`, `COUNT`, `DISTINCTCOUNT`, `MIN`, `MAX` |
| Iterators | `SUMX`, `AVERAGEX`, `COUNTX`, `FILTER` |
| Time intelligence | `TOTALYTD`, `TOTALMTD`, `SAMEPERIODLASTYEAR`, `DATEADD`, `PARALLELPERIOD` |
| Context modification | `CALCULATE`, `ALL`, `ALLEXCEPT`, `KEEPFILTERS` |
| Variables | `VAR`/`RETURN` |
| Safe division | `DIVIDE` |
| Conditional logic | `IF`, `SWITCH` |
| Ranking | `RANKX`, `TOPN` |
| Cross-table | `RELATED`, `USERELATIONSHIP` |

Manual descriptions in Power BI Desktop always take precedence over auto-generated ones.

---

## Roadmap

### v0.3 — Data Sources & Power Query
- **Data source discovery**: extract connection strings, server/database names, SharePoint/OneLake endpoints from TMDL partitions
- **Power Query (M) extraction**: expose the full M expression for each table partition
- **Custom query detection**: flag tables using `Value.NativeQuery` or inline SQL — a common maintenance risk
- **Dataflow & lakehouse references**: identify tables sourced from Power BI Dataflows, Fabric Lakehouses, or Warehouses

### v0.4 — Deep Model Analysis
- **Column lineage**: trace which measures reference which columns across tables
- **Unused columns**: detect columns not referenced in any measure, relationship, or visual
- **Measure dependency graph**: DAG of measure-to-measure dependencies
- **Hidden object inventory**: report on all hidden tables and columns

### v0.5 — Report Deep Dive
- **Visual-to-measure mapping**: detect which measures each visual uses (from `prototypeQuery`)
- **Filter analysis**: page-level and visual-level filters with target fields and values
- **Theme extraction**: color palette and font settings from theme files
- **Tooltip page detection**: pages used exclusively as tooltip layers

### Future
- Interactive single-file HTML output
- Pre-commit hook configuration helper
- VS Code extension wrapper

---

## Contributing

Issues and pull requests are welcome at [github.com/ViciusLio/pbi-semantic-doc](https://github.com/ViciusLio/pbi-semantic-doc).

```bash
pip install pytest
pytest tests/ -v   # 138 tests
```

---

## License

MIT — see [LICENSE](LICENSE).
