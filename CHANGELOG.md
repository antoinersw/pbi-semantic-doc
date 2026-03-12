# Changelog

All notable changes to this project will be documented in this file.

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
