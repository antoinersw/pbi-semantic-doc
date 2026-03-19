# pbi-semantic-doc

**Automatic documentation generator and analyzer for Power BI projects.**

[![PyPI version](https://img.shields.io/pypi/v/pbi-semantic-doc)](https://pypi.org/project/pbi-semantic-doc/)
[![Python 3.9+](https://img.shields.io/pypi/pyversions/pbi-semantic-doc)](https://pypi.org/project/pbi-semantic-doc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-345%20passing-brightgreen)](#)
[![Version](https://img.shields.io/badge/version-0.6.2-blue)](#)

Built with ❤️ by [ViciusLio](https://github.com/ViciusLio) in collaboration with [Claude AI](https://claude.ai) (Anthropic).

---

If your Power BI project lives in a Git repository as a `.pbip` project, this tool can:

- **Document semantic models** (TMDL format) — tables, columns, measures, relationships, DAX patterns, complexity index
- **Analyze reports** (PBIR and PBIR-Legacy) — pages, visuals, bookmarks, visual type distribution, complexity index

Zero configuration. Zero external dependencies. Drop it into any pipeline.

```bash
pip install pbi-semantic-doc

# Document a semantic model — writes DOC_MyProject.md next to the .SemanticModel folder
pbi-semantic-doc ./MyProject.SemanticModel

# Same but as a self-contained, printable HTML file
pbi-semantic-doc ./MyProject.SemanticModel --format html

# Analyze a report
pbi-semantic-doc ./MyProject.Report --analyze-report

# Both in one document (from the .pbip project folder)
pbi-semantic-doc ./MyProject --combined
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
# Basic — writes DOC_<ModelName>.md next to the .SemanticModel folder
pbi-semantic-doc ./MyProject.SemanticModel

# Specify a custom output path
pbi-semantic-doc ./MyProject.SemanticModel --output ./docs/MODEL.md

# Point to the .pbip parent folder (auto-discovers the .SemanticModel subfolder)
pbi-semantic-doc . --output MODEL.md

# Suppress console output (useful in CI)
pbi-semantic-doc ./MyProject.SemanticModel --quiet
```

### Report Analysis

```bash
# Markdown output (default) — writes DOC_<ReportName>.md next to the .Report folder
pbi-semantic-doc ./MyProject.Report --analyze-report

# JSON output for programmatic use
pbi-semantic-doc ./MyProject.Report --analyze-report --format json --output analysis.json

# Text summary to console
pbi-semantic-doc ./MyProject.Report --analyze-report --format text
```

### Combined Analysis

```bash
# Single unified document with Semantic Model + Report sections
pbi-semantic-doc ./MyProject --combined

# Custom output path
pbi-semantic-doc ./MyProject --combined --output ./docs/FULL.md

# JSON combined output
pbi-semantic-doc ./MyProject --combined --format json --output analysis.json
```

### CLI reference

| Flag | Description |
|------|-------------|
| `PATH` | Path to `.SemanticModel`, `.Report`, or `.pbip` project folder |
| `--analyze-report` | Analyze report instead of semantic model |
| `--combined` | Produce a single document covering both semantic model and report |
| `--format` | Output format: `md` (default), `html`, `json`, `text` |
| `--output`, `-o` | Output file path (default: `DOC_<name>.md` / `.html` next to the input folder) |
| `--quiet`, `-q` | Suppress console output |

---

## Output

### File naming and placement

| Mode | Default output location |
|------|------------------------|
| Semantic model (md) | `DOC_<ModelName>.md` — **next to** the `.SemanticModel` folder |
| Semantic model (html) | `DOC_<ModelName>.html` — **next to** the `.SemanticModel` folder |
| Report | `DOC_<ReportName>.md` / `.html` — **next to** the `.Report` folder |
| Combined | `DOC_<ProjectName>.md` / `.html` — **inside** the `.pbip` project folder |

Example: running against `Artificial Intelligence Sample.SemanticModel` produces `DOC_Artificial_Intelligence_Sample.md` in the parent folder.

### Document structure

Each generated Markdown document includes:

- **Table of Contents** — GitHub-compatible anchor links to every section and table; always visible at the top
- **Overview** — complexity index, table/column/measure/relationship counts, storage mode summary
- **Data Sources** — connector type, connection string, and Power Query (M) steps per table partition
- **Relationships** — collapsible table with cardinality, cross-filter direction, and active/inactive status
- **Row Level Security** — always visible; DAX filter expression per role
- **Tables** — one collapsible section per table: columns (type, hidden, description), measures (DAX + auto description)
- **Measures Index** — collapsible A–Z index of all measures with full DAX, auto-description, format string and lineage

---

## Expected folder structure

```
MyProject/
├── MyProject.pbip
├── DOC_MyProject.md              ← combined output lands here
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
- Correctly handles Power Query `#"Step Name"` quoted identifiers (e.g. `#"Changed Type"`, `#"Removed Columns"`)
- **Navigable output**: Table of Contents + collapsible `<details>` sections (renders natively on GitHub/GitLab)
- **Complexity Index** — normalized 0–1 score per model (see below)

### Report Analysis
- Supports **PBIR** (folder-based, new) and **PBIR-Legacy** (`report.json`) formats
- Classifies all standard and custom visual types
- Detects mobile layouts, drill-through pages, hidden pages, filters
- Identifies custom marketplace visuals by name
- **Complexity Index** — normalized 0–1 score per report (see below)
- Outputs Markdown, JSON, and plain text

### HTML Output (`--format html`)
- **Self-contained** single `.html` file — all CSS and JavaScript embedded, no external assets
- **Print to PDF**: `@media print` expands all collapsible sections automatically — open in any browser, hit `Ctrl+P`, choose "Save as PDF"
- Collapsible `<details>/<summary>` sections (identical structure to `.md` output)
- "Expand All / Collapse All" toolbar buttons for quick browser navigation
- Covers all modes: model-only, report-only, and combined (`--combined`)

### Measure Lineage (HTML output)
For every measure, the HTML output includes a collapsible **Lineage** section that is computed automatically from the DAX expression and the model's relationship graph — no naming conventions or manual annotations required:
- **Base tables** — fact/dimension tables directly aggregated by this measure (including transitive dependencies through nested `[Measures]`)
- **Compatible tables** — all tables reachable via the relationship graph; these are the dimensions you *can* safely use as slicers for this measure
- **Incompatible tables** — tables with no relationship path to the measure's base tables; using them as slicers has no effect or gives wrong results
- **Filter-removed tables** — tables explicitly cleared with `ALL()`, `ALLEXCEPT()`, or `ALLSELECTED()`
- **Measure dependencies** — direct and transitive `[MeasureName]` references, resolved via BFS (cycle-safe)
- **Flags** — time intelligence, `USERELATIONSHIP`, `TREATAS`

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

### v0.5 ✅ — Measure Lineage
- **Automatic measure lineage**: per-measure compatibility analysis in HTML output — base tables, compatible/incompatible dimensions, filter-removal tracking, transitive measure dependencies, time intelligence flags
- Two new stdlib-only modules: `dax_analyzer.py` (stateless regex Layer 1) and `lineage.py` (model-aware BFS Layer 2+3)
- Zero new dependencies — pure Python stdlib

### v0.4 ✅ — HTML Output
- **Self-contained HTML output** (`--format html`): navigable in browser, printable to PDF via `Ctrl+P`
- Zero new dependencies — pure Python stdlib

### v0.3 ✅ — Data Sources & Power Query
- **Data source discovery**: connection strings, server/database names, SharePoint/OneLake endpoints
- **Power Query (M) extraction**: full M expression per table partition with step-level breakdown
- **Custom query detection**: flag tables using `Value.NativeQuery` or inline SQL
- **Dataflow & lakehouse references**: identify Dataflow, Fabric Lakehouse, Warehouse sources
- **Navigable docs**: Table of Contents + collapsible sections + `DOC_<name>.md` naming
- **Unified combined document**: single file with Semantic Model + Report sections

### v0.6 ✅ — Deep Model Analysis
- **Column lineage**: trace which measures reference which columns across tables
- **Unused columns**: detect columns not referenced in any measure, relationship, or visual
- **Hidden object inventory**: report on all hidden tables and columns

### v0.7 — Report Deep Dive
- **Visual-to-measure mapping**: detect which measures each visual uses (from `prototypeQuery`)
- **Filter analysis**: page-level and visual-level filters with target fields and values
- **Theme extraction**: color palette and font settings from theme files
- **Tooltip page detection**: pages used exclusively as tooltip layers

### Future
- Pre-commit hook configuration helper
- VS Code extension wrapper

---

## Contributing

Issues and pull requests are welcome at [github.com/ViciusLio/pbi-semantic-doc](https://github.com/ViciusLio/pbi-semantic-doc).

```bash
pip install pytest
pytest tests/ -v   # 345 tests
```

---

## License

MIT — see [LICENSE](LICENSE).
