# Changelog

All notable changes to this project will be documented in this file.

---

## [0.5.11] — 2026-03-17

### Added
- **Full measure details in Markdown Measures Index** (`generator.py`):
  The A–Z Measures Index section now renders complete per-measure information — DAX expression, auto-description, format string, and a collapsible **Lineage** block — matching the richness already available in the HTML output and in the inline table sections. Previously it only showed a flat `| Measure | Table | Folder |` lookup table.
- **Lineage info in Markdown table sections** (`generator.py`):
  Each measure block inside a table section now also includes a collapsible `🔗 Lineage` block (aggregates, compatible slicers, non-correlated tables, filter-removed tables, measure dependencies, and flags for time intelligence / inactive relationships).
- **New `_measure_lineage_md` helper** renders lineage as readable Markdown `<details>` collapsible, consistent with the HTML panel.
- **`_measures_index` uses `_measure_block`** for a DRY layout: table provenance (`· 📋 TableName`) is appended to the measure heading in index view.
- **Combined example doc regenerated** (`examples/sample_model/DOC_Artificial_Intelligence_Sample.html`):
  Now generated with `generate_combined()` and includes both the **Semantic Model** and **Report** sections.
- **MD example doc regenerated** (`examples/sample_model/DOC_Artificial_Intelligence_Sample.md`):
  Reflects the new full-detail Measures Index with DAX + lineage per measure.

### Tests
- 330 tests — all passing

---

## [0.5.10] — 2026-03-17

### Fixed
- **Lineage compatible/incompatible tables now respect filter-flow direction** (`lineage.py`):
  The relationship graph was previously **undirected**, causing all fact tables that share a common dimension to appear "compatible" with every measure — even though they have no filter path to each other.
  The graph is now **directed** following Power BI's actual cross-filter semantics:
  - `single` direction: filter flows from the **one-side** (DIM) → **many-side** (FAT). A slicer on FAT_A cannot filter FAT_B through a shared DIM.
  - `both` directions: filters flow in both directions (bidirectional cross-filter).
  Only **active** relationships are included in the graph.
  The BFS (`_reachable_from`) traverses the *reverse* of the filter-flow graph from each measure's base tables, returning exactly the ancestor tables (DIM + snowflake parents) that can genuinely send filter context to the measure.

### Tests
- 330 tests — all passing (updated `test_rel_graph_built` to assert directed graph semantics)

---

## [0.5.9] — 2026-03-17

### Fixed
- **Measures Index restored for all models**: the A–Z index section and its sidebar link are now always shown when a model has any measures. The previous "2+ tables" restriction (v0.5.5) was too aggressive — for models with 100+ measures in a single dedicated table (e.g. `Misure`) the index is the primary navigation tool. Inline measures inside the table card are still shown; the index is an additional alphabetical hub.

### Tests
- 330 tests — all passing

---

## [0.5.8] — 2026-03-17

### Changed
- Version bump only — 0.5.7 was already occupied on PyPI.

---

## [0.5.7] — 2026-03-17

### Fixed
- **SPA navigation broken in combined doc**: the combined doc wrapped all model/report sections inside `<section id="semantic-model">` / `<section id="report">` outer elements, so inner sections (`sm-overview`, `sm-data-sources`, `table-*`, etc.) were NOT direct children of `<main>`. The CSS selector `main > section` hid everything but `activate()` could never find a match → blank page + broken sidebar links. Fixed by removing the outer `<section>` wrappers and replacing with a lightweight `<div class="section-group-header">` heading. The JS/CSS selector updated from `main > section` to `main section[id]` for robustness.
- Added `.section-group-header` CSS for the "Semantic Model" / "Report" group titles in combined doc.

### Tests
- 330 tests — all passing (updated 4 combined-doc tests to reflect new DOM structure)

---

### Changed — HTML output: master-detail SPA layout

- **SPA navigation**: all `<section>` elements inside `<main>` are hidden by default (`display:none`). Clicking a sidebar link shows only the target section (`.spa-active`) with a subtle fade-in animation. Browser back/forward (`popstate`) and deep-link hashes both work correctly. Scroll resets to top on every section switch. The `IntersectionObserver`-based active-link highlight has been replaced by direct click tracking.
- **Detail panel (right slide-in)**: a new `<div id="detail-panel">` fixed on the right edge slides in (CSS `transform` + `transition`) when the user clicks on any **measure card** summary. The panel shows the measure's full content (DAX expression + lineage + badges) without inline expansion. Main content shrinks (`padding-right: 430px`) to keep content readable when the panel is open. Close with the ✕ button or the Escape key. Responsive: full-width on viewports ≤ 960 px.
- Measure card `summary::after` shows a `↗` arrow hint to signal "opens in panel".
- `back-to-top`, `toggleAll`, and sidebar search filter are unchanged.
- **Zero new dependencies** — all pure CSS + vanilla JS, single self-contained file.

### Tests
- 330 tests — all passing

---

## [0.5.6] — 2026-03-17

### Changed
- Version bump only — 0.5.5 was already occupied on PyPI.

---

## [0.5.5] — 2026-03-17

### Added
- **Measures grouped by display folder** (HTML): measures are now rendered in collapsible `<details class="folder-group">` blocks that mirror the Power BI folder hierarchy (`Economics\Baseline`, `Delivery\Actual`, etc.). Multi-level paths create nested groups. Measures without a folder remain flat. The folder badge is suppressed inside a group (already contextual). The Measures Index (A–Z) keeps folder badges for context.
- New CSS classes `folder-group` and `badge-count` for the folder card style.

### Changed
- **Measures Index (A–Z) is now conditional**: shown only when measures span **2+ tables**. If a model uses a single dedicated measures table (PBI best practice), the index is suppressed — measures are already shown inline, a duplicate would be noise.
- **Combined-doc sidebar — collapsible Tables group**: the Tables list in the combined-doc sidebar now uses the same `<details class="nav-details">` toggle as the standalone sidebar. Large models (150+ tables) no longer flood the nav — click **📊 Tables (N)** to expand.
- Table entries in both sidebars now show measure count badge (`· Nm`).

### Tests
- 330 tests — all passing (updated `test_contains_measures_inline`, added `test_measures_index_appears_for_multi_table_model`)

---

## [0.5.4] — 2026-03-16

### Fixed
- **CSS summary arrows garbled** (`□B6◆A0` visible in all `<details>` summaries): Python was interpreting `\25B6` as octal escape chr(21) instead of passing the literal string `\25B6` to the CSS. Fixed by doubling the backslash (`\\25B6`, `\\25BC`) in all four `content:` rules (main details arrows + nav-details arrows).
- **Sidebar tables flood** with large models (150+ tables): the Tables group in the sidebar is now a `<details class="nav-details">` collapsible. Click "📊 Tables (N)" to expand/collapse the full table list. The nav-details uses a stripped-down style (no card border, no shadow) so it blends naturally into the sidebar.

### Tests
- 329 tests — all passing

---

## [0.5.3] — 2026-03-16

### Changed — HTML output (UX/UI redesign)
- **Two-column layout with sticky sidebar**: navigation panel fixed on the left (270 px), main content scrollable on the right. Sidebar collapses to full-width on mobile (`≤768 px`).
- **Sidebar navigation**: project name in header, live search/filter input (`🔍 Filter…`), grouped TOC links with active-section highlighting via `IntersectionObserver`, expand/collapse buttons in footer.
- **Each measure is now a collapsible card** (`<details class="measure-card">`): DAX expression, auto-description, format badge, folder badge and hidden badge visible at a glance; full body (DAX + lineage) revealed on click.
- **Measures Index (A–Z)** now renders full measure cards with DAX and lineage, not just a flat name/table/folder table.
- **Accessibility**: `<a class="skip-link" href="#main-content">` skip link, `<main id="main-content">` landmark, `<aside aria-label="Document navigation">`, `:focus-visible` outline, `aria-label` on search input and back-to-top button.
- **Back-to-top button**: fixed floating button (`↑`), fades in after 320 px scroll, smooth scroll on click.
- **Print**: sidebar hidden, layout collapses to single column, all `<details>` expand automatically — Ctrl+P → PDF still works.
- **Zero new dependencies** — all CSS/JS embedded, single self-contained file.

### Tests
- 329 tests — all passing (3 HTML tests updated to match new sidebar class names)

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
