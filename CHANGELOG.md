# Changelog

All notable changes to this project will be documented in this file.

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
