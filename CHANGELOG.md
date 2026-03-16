# Changelog

All notable changes to this project will be documented in this file.

---

## [0.5.2] — 2026-03-16

### Fixed
- **Native SQL extraction — two-step positional approach**: replaced the single-regex strategy for `Value.NativeQuery()` with a more robust two-step method: (1) locate the opening `"` of the SQL string using a paren-aware regex; (2) locate the closing `"` by scanning forward for `", null` or `", [` — the same approach proven in production. This eliminates potential backtracking failures on very large SQL strings (multi-CTE queries with hundreds of columns). After extraction, trims any preamble before `WITH`/`SELECT` for a clean SQL block.

### Tests
- 329 tests — all passing

---

## [0.5.1] — 2026-03-16

### Fixed
- **Native SQL extraction — nested-parens source argument**: `Value.NativeQuery()` calls where the first argument itself contains parentheses with commas (e.g. `AmazonRedshift.Database(host, db)`) were silently skipped — `[^,]+` stopped at the comma inside the nested call, so the SQL was never extracted and only the raw M expression was shown. Fixed with a 1-level paren-aware pattern `(?:[^(),]|\([^()]*\))*`.
- **Native SQL extraction — M `""` double-quote escape**: SQL column aliases written as `""Name""` in the M string literal (M's escape for a literal `"`) were left as `""Name""` in the output instead of being converted to `"Name"`. Fixed by matching `((?:[^"]|"")*)` for the SQL string content and adding `s.replace('""', '"')` as the final step in `_unescape_m_string()`.
- Both fixes apply to Pattern 1 (`Value.NativeQuery(...)`) and Pattern 2 (`[Query="..."]`).

### Tests
- 329 tests — all passing (+3 new regression tests for the two bugs above)

---

## [0.5.0] — 2026-03-16

### Added
- **Measure Lineage** — automatic compatibility analysis for every measure in the semantic model, surfaced in the HTML output as a collapsible "Lineage" section inside each measure:
  - **Base tables**: the fact/dimension tables directly aggregated by the measure (including transitive dependencies through nested measures)
  - **Compatible tables**: all tables reachable via the model's relationship graph — these are the dimensions you *can* use as slicers
  - **Incompatible tables**: tables with no relationship path to the measure's base tables — using them as slicers has no effect or gives wrong results
  - **Filter-removed tables**: tables explicitly cleared with `ALL()`, `ALLEXCEPT()`, or `ALLSELECTED()`
  - **Measure dependencies**: direct and transitive `[MeasureName]` references, resolved via BFS (cycle-safe)
  - **Flags**: time intelligence usage, `USERELATIONSHIP`, `TREATAS`
  - Works entirely from the model's relationship graph — no naming conventions required, no manual annotations
- **`dax_analyzer.py`** — new Layer 1 stateless module: regex-based extraction of `Table[Col]` refs, bare `[Measure]` refs, `ALL()`-removed tables, aggregated base tables (`SUM`, `COUNTROWS`, iterator functions `SUMX`/`AVERAGEX`/etc.), time intelligence flags, `USERELATIONSHIP`, `TREATAS`
- **`lineage.py`** — new Layer 2+3 model-aware module: `ModelLineage` builds an undirected relationship graph + measure index at construction time; `resolve()` performs BFS over nested measure dependencies (cycle-safe via `_visiting` frozenset); `MeasureLineage` dataclass carries all results; `resolve_all()` never raises (defensive wrapper keeps doc generation safe)

### Tests
- 326 tests — all passing (+59 new lineage tests: `test_dax_analyzer.py` × 34, `test_lineage.py` × 25)

---

## [0.4.2] — 2026-03-16

### Fixed
- **Native SQL display**: M language escape sequences (`#(lf)`, `#(tab)`, `#(cr,lf)`, `#(#)`, `#(HHHH)` Unicode) inside hand-written native queries are now converted to real characters before display — `Value.NativeQuery(...)` and `[Query="..."]` both benefit. The SQL now renders as clean, readable multi-line code instead of a wall of `#(lf)` tokens.

### Tests
- 267 tests — all passing (+8 new unescape tests)

---

## [0.4.1] — 2026-03-16

### Added
- **HTML output** (`--format html`): generates a single self-contained `.html` file — all CSS and JavaScript embedded, no external assets, zero new dependencies
  - Same collapsible `<details>/<summary>` structure as the Markdown output
  - **Print-friendly**: `@media print` CSS automatically expands all sections — `Ctrl+P → Save as PDF` produces a complete, fully-formatted document
  - **"Expand All / Collapse All"** toolbar buttons for quick navigation in the browser
  - Clean design with Power BI blue (`#0078d4`) accent, zebra-striped tables, monospace code blocks, hover effects
  - Supports all three modes: `--format html` (model), `--analyze-report --format html` (report), `--combined --format html` (unified model + report)
  - Default output filename follows the same `DOC_<name>.html` convention, placed next to the input folder
- **`HtmlGenerator`** class in `pbi_semantic_doc/html_generator.py` — mirrors `MarkdownGenerator` in structure, fully parallel API (`generate()`, `generate_report()`, `generate_combined()`)

### Tests
- 259 tests — all passing (+66 new HTML generator tests)

---

## [0.3.3] — 2026-03-13

### Fixed
- **Combined mode filename**: `--combined` now uses the real model/report name (e.g. `DOC_Artificial_Intelligence_Sample.md`) instead of the parent folder name (`DOC_sample_model.md`). Achieved by parsing both components first, then determining the output path.

### Tests
- 193 tests — all passing

---

## [0.3.2] — 2026-03-13

### Added
- **Report sections now collapsible**: Visual Types Distribution, Custom Visuals, Bookmarks, and Report Extensions are wrapped in collapsible blocks — consistent with the semantic model's navigable structure
- **Report TOC**: Table of Contents with anchor links added to the report markdown output
- **Complexity Index with colour indicator**: both semantic model and report now show a coloured dot next to the complexity percentage (green below 25%, yellow 25–59%, red 60%+) for at-a-glance readability
- **Report Overview enriched**: visual min/avg/max per page shown inline; hidden pages count included

### Tests
- 193 tests — all passing

---

## [0.3.1] — 2026-03-13

### Added
- **Navigable documentation**: Table of Contents with GitHub-compatible anchor links at the top of every generated document — links directly to each table, the Relationships section, RLS, and the Measures Index
- **Collapsible sections**: Table sections, Relationships, and Measures Index are wrapped in `<details>/<summary>` HTML — renders as expandable blocks on GitHub/GitLab, keeping long documents readable
- **Unified combined document** (`--combined`): instead of two concatenated files, generates a single structured document with a shared header, a combined Table of Contents, and clearly separated `## Semantic Model` / `## Report` sections

### Fixed
- **`#"Step Name"` Power Query identifiers**: Power BI Desktop wraps M step names containing spaces in `#"..."` syntax (e.g. `#"Changed Type"`, `#"Removed Columns"`, `#"Renamed Columns"`). These were silently merged into the preceding step's expression. The parser now correctly recognises both plain identifiers and `#"..."` quoted identifiers as step boundaries.
- **Output file placement**: `DOC_<name>.md` is now written **next to** the `.SemanticModel` / `.Report` folder (at the project level), not inside it. Combined mode output continues to land in the project root folder.
- **Output filename**: default filename is now `DOC_<ModelName>.md` (e.g. `DOC_Artificial_Intelligence_Sample.md`) instead of the generic `MODEL_DOC.md`, making it immediately identifiable and unique per project.

### Tests
- 193 tests — all passing

---

## [0.2.0] — 2026-03-12

### Added
- **Report analysis** for PBIR (folder-based) and PBIR-Legacy (`report.json`) formats
- `ReportParser` — parses `.Report/definition/` folder structure
- `ReportMetrics` — comprehensive metrics: pages, visuals, bookmarks, filters, mobile layouts, custom visuals
- `ReportGenerator` — outputs Markdown, JSON, and plain text
- `VisualType` enum covering all standard Power BI visual types plus custom marketplace visuals
- **Complexity index**: normalized 0–1 score (pages 25%, visuals 45%, bookmarks 20%, report-level measures 10%)
- CLI flags: `--analyze-report`, `--combined`, `--format json|md|text`
- Windows Unicode fix (`sys.stdout.reconfigure` for cp1252 terminals)
- Integration test suite against the Microsoft "Artificial Intelligence Sample" report (23 tests)
- 130 total tests (unit + integration), all passing

### Fixed
- `_parse_relationships`: added fallback for separate `fromTable`/`fromColumn` TMDL properties (non-dotted notation)
- `_unescape_name`: regex now correctly strips inline single-line DAX expressions
- `_extract_model_name`: now prefers the `.SemanticModel` folder name over internal `model.tmdl` content
- Report name now taken from the `.Report` folder name, not from an ancestor path

---

## [0.1.0] — initial release

### Added
- `TmdlParser` — parses TMDL folder structure into `SemanticModel` dataclasses
- `MarkdownGenerator` — generates structured Markdown documentation
- Tables, columns, measures (with full DAX), relationships
- Automatic DAX pattern descriptions (time intelligence, aggregations, CALCULATE, DIVIDE, etc.)
- Alphabetical measures index
- CLI entry point `pbi-semantic-doc`
- Zero external dependencies (stdlib only)
