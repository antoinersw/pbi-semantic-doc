"""
HTML generator — produces a self-contained, printable HTML document from a
SemanticModel and/or ReportMetrics.

Features:
- Zero external dependencies (pure stdlib: html, re, datetime)
- All CSS and JS embedded — single file, no external assets
- Collapsible <details>/<summary> sections (same structure as .md output)
- @media print: all sections expand automatically — Ctrl+P → PDF works
- "Expand All / Collapse All" JavaScript buttons
- Power BI blue (#0078d4) accent colour
"""

from __future__ import annotations

import html as _html
import re
from datetime import datetime, timezone
from typing import Optional

from .parser import SemanticModel, Table, Measure, Partition, Role, Relationship
from .lineage import ModelLineage, MeasureLineage

# ── lookup tables (mirrored from generator.py) ────────────────────────────

_FOLDING_ICON = {
    "likely":   "✅",
    "at_risk":  "⚠️",
    "disabled": "❌",
    "n/a":      "—",
    "unknown":  "❓",
}

_FOLDING_LABEL = {
    "likely":   "Likely",
    "at_risk":  "At Risk",
    "disabled": "Disabled",
    "n/a":      "N/A",
    "unknown":  "Unknown",
}

_MODE_LABEL = {
    "import":       "Import",
    "directQuery":  "DirectQuery",
    "directLake":   "DirectLake",
    "mixed":        "Mixed",
    "calculated":   "Calculated",
    "unknown":      "—",
}

_MODE_ICON = {
    "import":       "📥",
    "directQuery":  "🔄",
    "directLake":   "⚡",
    "mixed":        "🔀",
}

# ── embedded CSS ──────────────────────────────────────────────────────────

_CSS = """\
:root {
    --accent:       #0078d4;
    --accent-light: #deecf9;
    --bg:           #ffffff;
    --surface:      #f8f9fa;
    --border:       #d0d7de;
    --text:         #24292f;
    --muted:        #656d76;
    --code-bg:      #f6f8fa;
    --shadow:       0 1px 3px rgba(0,0,0,.08);
}
*, *::before, *::after { box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 15px;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg);
    max-width: 1080px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
}

/* ── typography ───────────────────────────────────────────────────────── */
h1 {
    font-size: 1.85rem;
    border-bottom: 3px solid var(--accent);
    padding-bottom: .4em;
    margin-bottom: .5em;
}
h2 {
    font-size: 1.3rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: .25em;
    margin-top: 2.5rem;
}
h3 { font-size: 1.05rem; margin-top: 1.5rem; }
h4 { font-size: 1rem;    margin-top: 1rem;   }

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

blockquote {
    border-left: 4px solid var(--accent);
    margin: .75em 0;
    padding: .25em .9em;
    background: var(--accent-light);
    border-radius: 0 4px 4px 0;
    color: var(--muted);
}
p { margin: .5em 0; }

/* ── code ─────────────────────────────────────────────────────────────── */
code {
    font-family: "Cascadia Code", Consolas, "SFMono-Regular", monospace;
    font-size: .875em;
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: .1em .4em;
}
pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1em 1.25em;
    overflow-x: auto;
    margin: .75em 0;
}
pre code { background: none; border: none; padding: 0; font-size: .85em; }

/* ── tables ───────────────────────────────────────────────────────────── */
table { border-collapse: collapse; width: 100%; margin: .75em 0; font-size: .9em; }
thead tr { background: var(--accent); color: #fff; }
th { padding: .45em .75em; text-align: left; font-weight: 600; white-space: nowrap; }
td { padding: .35em .75em; border-bottom: 1px solid var(--border); vertical-align: top; }
tbody tr:nth-child(even) td { background: var(--surface); }
tbody tr:hover td { background: var(--accent-light); transition: background .1s; }

/* ── details / summary ───────────────────────────────────────────────── */
details {
    border: 1px solid var(--border);
    border-radius: 6px;
    margin: .5em 0;
    background: var(--bg);
    box-shadow: var(--shadow);
}
details[open] { background: var(--surface); }
summary {
    cursor: pointer;
    font-weight: 500;
    padding: .6em 1em;
    list-style: none;
    user-select: none;
    border-radius: 5px;
}
summary::-webkit-details-marker { display: none; }
summary::before {
    content: "\\25B6\\00A0";
    font-size: .75em;
    color: var(--muted);
}
details[open] > summary::before { content: "\\25BC\\00A0"; }
.details-body { padding: .75em 1em 1em; border-top: 1px solid var(--border); }

/* ── table of contents ───────────────────────────────────────────────── */
.toc {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin: 1.5rem 0 2rem;
    box-shadow: var(--shadow);
}
.toc .toc-label {
    font-size: .8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--muted);
    display: block;
    margin-bottom: .5em;
}
.toc ul  { margin: .25em 0; padding-left: 1.5em; }
.toc > ul { padding-left: 1em; }
.toc li  { margin: .2em 0; }

/* ── toolbar ──────────────────────────────────────────────────────────── */
.toolbar {
    display: flex;
    gap: .5em;
    justify-content: flex-end;
    margin-bottom: 1rem;
}
.toolbar button {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: .3em .8em;
    cursor: pointer;
    font-size: .85em;
    color: var(--text);
}
.toolbar button:hover {
    background: var(--accent-light);
    border-color: var(--accent);
    color: var(--accent);
}

/* ── footer ───────────────────────────────────────────────────────────── */
footer {
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: .85em;
    text-align: center;
}

/* ── lineage badges ──────────────────────────────────────────────────── */
.lineage-row { display: flex; flex-wrap: wrap; gap: .35em; align-items: center; margin: .3em 0; font-size: .85em; }
.lineage-label { color: var(--muted); font-weight: 600; min-width: 7em; }
.badge-compatible { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 3px; padding: .1em .4em; font-size: .78em; }
.badge-incompatible { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 3px; padding: .1em .4em; font-size: .78em; }
.badge-removed { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 3px; padding: .1em .4em; font-size: .78em; }
.badge-dep { background: var(--code-bg); color: var(--muted); border: 1px solid var(--border); border-radius: 3px; padding: .1em .4em; font-size: .78em; }

/* ── print ────────────────────────────────────────────────────────────── */
@media print {
    .no-print { display: none !important; }
    details { display: block !important; border: none; box-shadow: none; padding: 0; }
    summary { display: none !important; }
    .details-body { padding: 0; border: none; }
    h1, h2 { page-break-after: avoid; }
    table, pre, blockquote { page-break-inside: avoid; }
    thead { display: table-header-group; }
    a[href^="#"]::after { content: ""; }
    body { max-width: 100%; font-size: 11pt; }
    h1 { font-size: 18pt; }
    h2 { font-size: 14pt; margin-top: 1.5em; }
    tbody tr:hover td { background: inherit; }
}
"""

# ── embedded JS ───────────────────────────────────────────────────────────

_JS = """\
function toggleAll(open) {
    document.querySelectorAll('details').forEach(function(d) { d.open = open; });
}
"""

# ── low-level HTML helpers ────────────────────────────────────────────────


def _e(text: str) -> str:
    """Escape text for HTML body context."""
    return _html.escape(str(text), quote=False)


def _attr(text: str) -> str:
    """Escape text for use inside an HTML attribute value."""
    return _html.escape(str(text), quote=True)


def _code(text: str) -> str:
    return f"<code>{_e(text)}</code>"


def _pre(content: str, lang: str = "") -> str:
    cls = f' class="language-{_attr(lang)}"' if lang else ""
    return f"<pre><code{cls}>{_e(content)}</code></pre>"


def _heading(level: int, text: str, anchor: Optional[str] = None) -> str:
    id_attr = f' id="{_attr(anchor)}"' if anchor else ""
    return f"<h{level}{id_attr}>{text}</h{level}>"


def _details(summary_html: str, body_html: str) -> str:
    return (
        f"<details>\n"
        f"<summary>{summary_html}</summary>\n"
        f'<div class="details-body">\n{body_html}\n</div>\n'
        f"</details>"
    )


def _table(headers: list[str], rows: list[list[str]]) -> str:
    """
    Build an HTML table.
    All cell values in *rows* are treated as pre-formed HTML strings (not escaped).
    Header values are plain text and will be escaped here.
    """
    head = "".join(f"<th>{_e(h)}</th>" for h in headers)
    body_rows = "\n".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return (
        f"<table>\n"
        f"<thead><tr>{head}</tr></thead>\n"
        f"<tbody>\n{body_rows}\n</tbody>\n"
        f"</table>"
    )


def _section_anchor(heading: str) -> str:
    """Same algorithm as MarkdownGenerator._heading_anchor() for consistent cross-links."""
    text = re.sub(r"[`*_~]", "", heading)
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def _html_page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"<title>{_attr(title)}</title>\n"
        f"<style>\n{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        f"<script>\n{_JS}</script>\n"
        "</body>\n"
        "</html>\n"
    )


# ── main class ────────────────────────────────────────────────────────────


class HtmlGenerator:
    """
    Generates a self-contained HTML document from a SemanticModel,
    a ReportMetrics object, or both combined.

    Usage (model only):
        gen = HtmlGenerator()
        html = gen.generate(model)
        Path("DOC_MyModel.html").write_text(html, encoding="utf-8")

    Usage (combined):
        html = gen.generate_combined(model, report_metrics, "My Project")
    """

    # ── public API ────────────────────────────────────────────────────────

    def generate(self, model: SemanticModel) -> str:
        """Generate a self-contained HTML document for a semantic model."""
        # Build measure lineage once for the whole model; failures are silent
        try:
            self._lineage_map: dict = ModelLineage(model).resolve_all()
        except Exception:
            self._lineage_map = {}
        body = self._model_body(model)
        self._lineage_map = {}
        return _html_page(title=f"DOC — {model.name}", body=body)

    def generate_report(self, metrics) -> str:
        """Generate a self-contained HTML document for a report."""
        self._lineage_map = {}
        body = self._report_body(metrics)
        return _html_page(title=f"DOC — {metrics.report_name}", body=body)

    def generate_combined(
        self,
        model: Optional[SemanticModel],
        report_metrics,
        project_name: str,
    ) -> str:
        """Generate a unified HTML document covering both model and report."""
        parts: list[str] = []

        # Toolbar
        parts.append(
            '<div class="toolbar no-print">'
            '<button onclick="toggleAll(true)">⊞ Expand All</button>'
            '<button onclick="toggleAll(false)">⊟ Collapse All</button>'
            "</div>"
        )

        # Title
        parts.append(_heading(1, f"{_e(project_name)} &mdash; Power BI Documentation"))

        # Combined TOC
        parts.append(self._combined_toc(model, report_metrics))

        # Semantic model section
        if model:
            try:
                self._lineage_map = ModelLineage(model).resolve_all()
            except Exception:
                self._lineage_map = {}
            parts.append('<section id="semantic-model">')
            parts.append(_heading(2, "Semantic Model"))
            parts.append(self._model_inner(model, heading_offset=1))
            parts.append("</section>")
            self._lineage_map = {}

        # Horizontal rule between sections
        if model and report_metrics:
            parts.append("<hr>")

        # Report section
        if report_metrics:
            parts.append('<section id="report">')
            parts.append(_heading(2, "Report"))
            parts.append(self._report_inner(report_metrics, heading_offset=1))
            parts.append("</section>")

        parts.append(self._footer())

        body = "\n\n".join(parts)
        return _html_page(title=f"DOC — {project_name}", body=body)

    # ── model body (standalone) ───────────────────────────────────────────

    def _model_body(self, model: SemanticModel) -> str:
        parts: list[str] = []

        parts.append(
            '<div class="toolbar no-print">'
            '<button onclick="toggleAll(true)">⊞ Expand All</button>'
            '<button onclick="toggleAll(false)">⊟ Collapse All</button>'
            "</div>"
        )
        parts.append(
            _heading(1, f"{_e(model.name)} &mdash; Semantic Model Documentation")
        )
        parts.append(self._model_toc(model))
        parts.append(self._model_inner(model, heading_offset=0))
        parts.append(self._footer())
        return "\n\n".join(parts)

    def _model_inner(self, model: SemanticModel, heading_offset: int = 0) -> str:
        """Model content sections — heading_offset=1 means h2→h3 (for combined doc)."""
        h = heading_offset
        parts: list[str] = []

        parts.append(self._overview_section(model, h))

        ds_html = self._data_sources_section(model, h)
        if ds_html:
            parts.append(ds_html)

        if model.relationships:
            parts.append(self._relationships_section(model.relationships, h))

        if model.roles:
            parts.append(self._rls_section(model, h))

        for table in model.visible_tables:
            parts.append(self._table_section(table, h))

        if model.all_measures:
            parts.append(self._measures_index(model, h))

        return "\n\n".join(parts)

    # ── report body (standalone) ──────────────────────────────────────────

    def _report_body(self, metrics) -> str:
        parts: list[str] = []

        parts.append(
            '<div class="toolbar no-print">'
            '<button onclick="toggleAll(true)">⊞ Expand All</button>'
            '<button onclick="toggleAll(false)">⊟ Collapse All</button>'
            "</div>"
        )
        parts.append(
            _heading(1, f"{_e(metrics.report_name)} &mdash; Report Analysis")
        )
        parts.append(self._report_toc(metrics))
        parts.append(self._report_inner(metrics, heading_offset=0))
        parts.append(self._footer())
        return "\n\n".join(parts)

    def _report_inner(self, metrics, heading_offset: int = 0) -> str:
        h = heading_offset
        parts: list[str] = []

        parts.append(self._report_overview_section(metrics, h))

        if metrics.visual_types_count:
            parts.append(self._visual_types_section(metrics, h))

        if metrics.custom_visuals:
            parts.append(self._custom_visuals_section(metrics, h))

        if metrics.has_bookmarks:
            parts.append(self._bookmarks_section(metrics, h))

        if metrics.has_report_extensions:
            parts.append(self._report_extensions_section(metrics, h))

        parts.append(self._advanced_metrics_section(metrics, h))

        if metrics.error_message:
            parts.append(
                f'<section>\n'
                f'{_heading(2 + h, "Errors")}\n'
                f"<p>⚠️ {_e(metrics.error_message)}</p>\n"
                f"</section>"
            )

        return "\n\n".join(parts)

    # ── TOC helpers ───────────────────────────────────────────────────────

    def _model_toc(self, model: SemanticModel) -> str:
        items: list[str] = []
        items.append('<li><a href="#overview">Overview</a></li>')

        ds = model.data_sources
        if ds:
            n = len(ds)
            items.append(
                f'<li><a href="#data-sources">Data Sources</a>'
                f" &mdash; {n} connector{'s' if n != 1 else ''}</li>"
            )

        if model.relationships:
            n = len(model.relationships)
            items.append(
                f'<li><a href="#relationships">Relationships</a>'
                f" &mdash; {n} relationship{'s' if n != 1 else ''}</li>"
            )

        if model.roles:
            n = len(model.roles)
            items.append(
                f'<li><a href="#row-level-security">Row Level Security</a>'
                f" &mdash; {n} role{'s' if n != 1 else ''}</li>"
            )

        if model.visible_tables:
            table_items: list[str] = []
            for table in model.visible_tables:
                anchor = _section_anchor(f"Table: `{table.name}`")
                n_cols = len([c for c in table.columns if not c.is_hidden])
                n_meas = len(table.measures)
                mode = table.effective_mode
                mode_icon = _MODE_ICON.get(mode, "🧮" if mode == "calculated" else "")
                parts = []
                if mode_icon:
                    parts.append(f"{mode_icon} {_MODE_LABEL.get(mode, mode)}")
                parts.append(f"{n_cols} col{'s' if n_cols != 1 else ''}")
                if n_meas:
                    parts.append(f"{n_meas} measure{'s' if n_meas != 1 else ''}")
                detail = " &middot; ".join(_e(p) for p in parts)
                table_items.append(
                    f'<li><a href="#{_attr(anchor)}">{_e(table.name)}</a>'
                    f" &mdash; {detail}</li>"
                )
            items.append(
                f"<li><strong>Tables</strong>"
                f"<ul>\n{''.join(table_items)}\n</ul></li>"
            )

        if model.all_measures:
            n = len(model.all_measures)
            items.append(
                f'<li><a href="#measures-index-az">Measures Index</a>'
                f" &mdash; {n} measure{'s' if n != 1 else ''}</li>"
            )

        list_html = "\n".join(items)
        return (
            '<nav class="toc">\n'
            '<span class="toc-label">Contents</span>\n'
            f"<ul>\n{list_html}\n</ul>\n"
            "</nav>"
        )

    def _report_toc(self, metrics) -> str:
        items: list[str] = []
        items.append('<li><a href="#overview">Overview</a></li>')

        if metrics.visual_types_count:
            n = len(metrics.visual_types_count)
            items.append(
                f'<li><a href="#visual-types-distribution">Visual Types Distribution</a>'
                f" &mdash; {n} type{'s' if n != 1 else ''}</li>"
            )
        if metrics.custom_visuals:
            n = len(metrics.custom_visuals)
            items.append(
                f'<li><a href="#custom-visuals">Custom Visuals</a>'
                f" &mdash; {n} marketplace visual{'s' if n != 1 else ''}</li>"
            )
        if metrics.has_bookmarks:
            n = metrics.total_bookmarks
            items.append(
                f'<li><a href="#bookmarks">Bookmarks</a>'
                f" &mdash; {n} bookmark{'s' if n != 1 else ''}</li>"
            )
        if metrics.has_report_extensions:
            n = len(metrics.report_level_measures)
            items.append(
                f'<li><a href="#report-extensions">Report Extensions</a>'
                f" &mdash; {n} report-level measure{'s' if n != 1 else ''}</li>"
            )
        items.append('<li><a href="#advanced-metrics">Advanced Metrics</a></li>')

        list_html = "\n".join(items)
        return (
            '<nav class="toc">\n'
            '<span class="toc-label">Contents</span>\n'
            f"<ul>\n{list_html}\n</ul>\n"
            "</nav>"
        )

    def _combined_toc(self, model, report_metrics) -> str:
        items: list[str] = []
        if model:
            tables = len(model.visible_tables)
            measures = sum(len(t.measures) for t in model.visible_tables)
            rels = len(model.relationships)
            items.append(
                f'<li><a href="#semantic-model">Semantic Model</a>'
                f" &mdash; {tables} table{'s' if tables != 1 else ''},"
                f" {measures} measure{'s' if measures != 1 else ''},"
                f" {rels} relationship{'s' if rels != 1 else ''}</li>"
            )
        if report_metrics:
            pages = report_metrics.total_pages
            visuals = report_metrics.total_visuals
            items.append(
                f'<li><a href="#report">Report</a>'
                f" &mdash; {pages} page{'s' if pages != 1 else ''},"
                f" {visuals} visual{'s' if visuals != 1 else ''}</li>"
            )
        list_html = "\n".join(items)
        return (
            '<nav class="toc">\n'
            '<span class="toc-label">Contents</span>\n'
            f"<ul>\n{list_html}\n</ul>\n"
            "</nav>"
        )

    # ── semantic model sections ───────────────────────────────────────────

    def _overview_section(self, model: SemanticModel, h: int = 0) -> str:
        metrics = model.calculate_metrics()
        visible = model.visible_tables
        visible_cols = sum(
            sum(1 for c in t.columns if not c.is_hidden) for t in visible
        )

        rows = [
            [_e("Tables"), _e(f"{len(visible)} visible, {metrics.hidden_tables} hidden")],
            [_e("Columns"), _e(f"{visible_cols} visible, {metrics.hidden_columns} hidden")],
            [_e("Measures"), _e(str(metrics.total_measures))],
            [
                _e("Relationships"),
                _e(f"{metrics.total_relationships} ({metrics.inactive_relationships} inactive)"),
            ],
        ]
        if model.roles:
            rows.append([_e("RLS Roles"), _e(str(len(model.roles)))])

        cx = metrics.complexity_index
        cx_icon = "🟢" if cx < 0.25 else ("🟡" if cx < 0.60 else "🔴")
        rows.append([
            f"<strong>{_e('Complexity Index')}</strong>",
            f"<strong>{_e(cx_icon)} {_e(f'{cx:.0%}')}</strong>",
        ])

        table_html = _table(["", ""], rows)
        return (
            '<section id="overview">\n'
            + _heading(2 + h, "Overview")
            + "\n"
            + table_html
            + "\n</section>"
        )

    def _data_sources_section(self, model: SemanticModel, h: int = 0) -> str:
        rows_html: list[list[str]] = []

        for table in model.tables:
            for partition in table.partitions:
                qa = partition.query_analysis
                if not qa:
                    continue

                if qa.query_type == "calculated":
                    rows_html.append([
                        _code(table.name), "—", "—", "—",
                        "Calculated (DAX)", "—", "—",
                    ])
                    continue
                if qa.query_type == "entity":
                    rows_html.append([
                        _code(table.name), "—", "—", "—",
                        "DirectLake Entity", "—", "—",
                    ])
                    continue
                if not qa.connector:
                    continue

                conn = qa.connector
                server = conn.positional_params[0] if conn.positional_params else "—"
                database = (
                    conn.positional_params[1]
                    if len(conn.positional_params) > 1
                    else "—"
                )
                param_note = " <em>(param)</em>" if conn.is_parameterized else ""
                mode = _e(_MODE_LABEL.get(partition.mode, partition.mode))
                steps = _e(str(qa.step_count)) if qa.step_count > 0 else "—"

                f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
                f_label = _FOLDING_LABEL.get(qa.query_folding_status, qa.query_folding_status)
                folding = f"{f_icon} {_e(f_label)}"
                if qa.query_type == "native_sql":
                    folding += " <em>(native SQL)</em>"

                incr = " 🔄" if qa.incremental_refresh.is_incremental else ""

                rows_html.append([
                    _code(table.name) + incr,
                    _e(conn.source_type),
                    _e(server) + param_note,
                    _e(database),
                    mode,
                    steps,
                    folding,
                ])

        if not rows_html:
            return ""

        headers = ["Table", "Connector", "Server / Path", "Database", "Mode", "Steps", "Query Folding"]
        table_html = _table(headers, rows_html)
        return (
            '<section id="data-sources">\n'
            + _heading(2 + h, "Data Sources")
            + "\n"
            + table_html
            + "\n</section>"
        )

    def _relationships_section(self, relationships: list, h: int = 0) -> str:
        n = len(relationships)
        summary_html = f"🔗 {n} relationship{'s' if n != 1 else ''} — click to expand"

        headers = ["From", "", "To", "Cardinality", "Cross-filter", "Active"]
        rows = []
        for r in relationships:
            active = "✅" if r.is_active else "⬜"
            rows.append([
                f"{_code(r.from_table)}[{_e(r.from_column)}]",
                "→",
                f"{_code(r.to_table)}[{_e(r.to_column)}]",
                _e(r.cardinality),
                _e(r.cross_filter),
                active,
            ])

        details_html = _details(_e(summary_html), _table(headers, rows))
        return (
            '<section id="relationships">\n'
            + _heading(2 + h, "Relationships")
            + "\n"
            + details_html
            + "\n</section>"
        )

    def _rls_section(self, model: SemanticModel, h: int = 0) -> str:
        headers = ["Role", "Permission", "Table", "Filter"]
        rows = []
        for role in model.roles:
            if not role.table_permissions:
                rows.append([
                    f"<strong>{_e(role.name)}</strong>",
                    _e(role.model_permission),
                    "<em>(no table filters)</em>",
                    "—",
                ])
                continue
            for i, tp in enumerate(role.table_permissions):
                role_cell = f"<strong>{_e(role.name)}</strong>" if i == 0 else ""
                perm_cell = _e(role.model_permission) if i == 0 else ""
                if tp.filter_expression.lower() == "true":
                    filter_cell = "<em>(no row filter)</em>"
                else:
                    filter_cell = _code(tp.filter_expression)
                rows.append([role_cell, perm_cell, _code(tp.table_name), filter_cell])

        return (
            '<section id="row-level-security">\n'
            + _heading(2 + h, "Row Level Security")
            + "\n"
            + _table(headers, rows)
            + "\n</section>"
        )

    def _table_section(self, table: Table, h: int = 0) -> str:
        anchor = _section_anchor(f"Table: `{table.name}`")

        # Summary line for <details> toggle
        n_cols = len([c for c in table.columns if not c.is_hidden])
        n_meas = len(table.measures)
        mode = table.effective_mode

        summary_parts: list[str] = []
        if mode == "calculated":
            summary_parts.append("🧮 Calculated (DAX)")
        elif mode == "entity":
            summary_parts.append("⚡ DirectLake")
        elif mode in _MODE_ICON:
            summary_parts.append(f"{_MODE_ICON[mode]} {_MODE_LABEL[mode]}")

        summary_parts.append(f"{n_cols} col{'s' if n_cols != 1 else ''}")
        if n_meas:
            summary_parts.append(f"{n_meas} measure{'s' if n_meas != 1 else ''}")

        for p in table.partitions:
            qa = p.query_analysis
            if qa and qa.connector:
                f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
                f_label = _FOLDING_LABEL.get(qa.query_folding_status, qa.query_folding_status)
                summary_parts.append(f"Folding: {f_icon} {f_label}")
                break

        summary_html = (
            " &middot; ".join(_e(p) for p in summary_parts)
            + " &mdash; click to expand"
        )

        # Body content
        content_parts: list[str] = []

        if table.description:
            content_parts.append(f"<p>{_e(table.description)}</p>")

        badge = self._partition_badge(table)
        if badge:
            content_parts.append(badge)

        if table.columns:
            visible_cols = [c for c in table.columns if not c.is_hidden]
            hidden_cols  = [c for c in table.columns if c.is_hidden]
            if visible_cols:
                content_parts.append(self._columns_html(visible_cols, hidden_cols))

        if table.measures:
            content_parts.append(_heading(3 + h, "Measures"))
            for measure in sorted(table.measures, key=lambda m: m.name.lower()):
                content_parts.append(self._measure_html(measure, h, table.name))

        for partition in table.partitions:
            if partition.expression and partition.type == "m":
                content_parts.append(self._m_expression_html(partition))

        section_heading = _heading(
            2 + h,
            f"Table: {_code(table.name)}",
            anchor=anchor,
        )

        if not content_parts:
            return f'<section id="{_attr(anchor)}">\n{section_heading}\n</section>'

        body_html = "\n".join(content_parts)
        return (
            f'<section id="{_attr(anchor)}">\n'
            + section_heading
            + "\n"
            + _details(summary_html, body_html)
            + "\n</section>"
        )

    def _partition_badge(self, table: Table) -> str:
        parts: list[str] = []
        for p in table.partitions:
            qa = p.query_analysis
            if not qa:
                continue
            if qa.query_type == "calculated":
                parts.append(
                    "<blockquote>🧮 <strong>Calculated table</strong> (DAX)</blockquote>"
                )
            elif qa.query_type == "entity":
                parts.append(
                    "<blockquote>⚡ <strong>DirectLake Entity</strong></blockquote>"
                )
            elif qa.connector:
                conn = qa.connector
                server = conn.positional_params[0] if conn.positional_params else "?"
                db_part = (
                    f" → {_e(conn.positional_params[1])}"
                    if len(conn.positional_params) > 1
                    else ""
                )
                param_note = " <em>(parameterized)</em>" if conn.is_parameterized else ""
                mode_icon = _MODE_ICON.get(p.mode, "")
                f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
                f_label = _FOLDING_LABEL.get(qa.query_folding_status, qa.query_folding_status)
                incr_note = (
                    " &middot; 🔄 Incremental Refresh"
                    if qa.incremental_refresh.is_incremental
                    else ""
                )
                native_note = (
                    " &middot; Native SQL" if qa.query_type == "native_sql" else ""
                )
                parts.append(
                    f"<blockquote>{mode_icon} <strong>{_e(conn.source_type)}</strong>"
                    f" ({_e(server)}{db_part}){param_note}"
                    f"{incr_note}{native_note}"
                    f" &middot; Query Folding: {f_icon} {_e(f_label)}</blockquote>"
                )
        return "\n".join(parts)

    def _columns_html(self, visible: list, hidden: list) -> str:
        hidden_note = f", {len(hidden)} hidden" if hidden else ""
        summary_html = (
            f"<strong>Columns "
            f"({len(visible)} visible{_e(hidden_note)} &mdash; click to expand)"
            f"</strong>"
        )
        headers = ["Column", "Type", "Description", "Format", "Hidden"]
        rows = []
        for col in visible:
            fmt = _code(col.format_string) if col.format_string else ""
            rows.append([
                _code(col.name), _e(col.data_type), _e(col.description), fmt, "",
            ])
        for col in hidden:
            fmt = _code(col.format_string) if col.format_string else ""
            rows.append([
                _code(col.name), _e(col.data_type), _e(col.description), fmt, "✗",
            ])
        return _details(summary_html, _table(headers, rows))

    def _measure_html(self, measure: Measure, h: int = 0, table_name: str = "") -> str:
        parts: list[str] = []
        hidden_tag = " <em>(hidden)</em>" if measure.is_hidden else ""
        folder_tag = (
            f" &middot; 📁 {_code(measure.display_folder)}"
            if measure.display_folder
            else ""
        )
        parts.append(_heading(4 + h, f"{_code(measure.name)}{hidden_tag}{folder_tag}"))

        if measure.description:
            parts.append(f"<p>{_e(measure.description)}</p>")

        auto_desc = measure.auto_description()
        if auto_desc and not measure.description:
            parts.append(f"<p><em>{_e(auto_desc)}</em></p>")

        if measure.format_string:
            parts.append(
                f"<p><strong>Format:</strong> {_code(measure.format_string)}</p>"
            )

        if measure.expression:
            parts.append(_pre(measure.expression, lang="dax"))

        # Lineage section — only when lineage data is available
        if table_name and hasattr(self, "_lineage_map"):
            lin = self._lineage_map.get((table_name, measure.name))
            if lin and lin.has_lineage_info:
                parts.append(self._measure_lineage_html(lin))

        return "\n".join(parts)

    def _measure_lineage_html(self, lin: MeasureLineage) -> str:
        """Render a collapsible lineage card for a single measure."""
        rows: list[str] = []

        def _badges(names: set[str], css_class: str) -> str:
            return " ".join(
                f'<span class="{css_class}">{_e(n)}</span>'
                for n in sorted(names)
            )

        # Base tables (what the measure aggregates)
        if lin.all_base_tables:
            badges = _badges(lin.all_base_tables, "badge-dep")
            rows.append(
                f'<div class="lineage-row">'
                f'<span class="lineage-label">📊 Aggrega</span>{badges}</div>'
            )

        # Flags
        flags: list[str] = []
        if lin.uses_time_intelligence:
            flags.append("📅 Time intelligence")
        if lin.uses_inactive_relationship:
            flags.append("🔀 USERELATIONSHIP")
        if lin.uses_treatas:
            flags.append("🔗 TREATAS")
        if lin.has_cycle:
            flags.append("⚠️ Ciclo rilevato")
        if flags:
            rows.append(
                f'<div class="lineage-row">'
                + "".join(f'<span class="badge-dep">{_e(f)}</span>' for f in flags)
                + "</div>"
            )

        # Nested measure dependencies
        if lin.all_measure_deps:
            badges = " ".join(
                f'<span class="badge-dep">[{_e(d)}]</span>'
                for d in lin.all_measure_deps
            )
            rows.append(
                f'<div class="lineage-row">'
                f'<span class="lineage-label">🔗 Dipende da</span>{badges}</div>'
            )

        # Compatible dimensions
        if lin.compatible_tables:
            badges = _badges(lin.compatible_tables, "badge-compatible")
            rows.append(
                f'<div class="lineage-row">'
                f'<span class="lineage-label">✅ Compatibile</span>{badges}</div>'
            )

        # Incompatible (no relationship)
        if lin.incompatible_tables:
            badges = _badges(lin.incompatible_tables, "badge-incompatible")
            rows.append(
                f'<div class="lineage-row">'
                f'<span class="lineage-label">❌ Non correlato</span>{badges}</div>'
            )

        # ALL-removed
        if lin.filter_removed_tables:
            badges = _badges(lin.filter_removed_tables, "badge-removed")
            rows.append(
                f'<div class="lineage-row">'
                f'<span class="lineage-label">⚠️ Filtro rimosso</span>{badges}</div>'
            )

        if not rows:
            return ""

        body_html = "\n".join(rows)
        return _details("🔗 <strong>Lineage</strong> — click to expand", body_html)

    def _m_expression_html(self, partition: Partition) -> str:
        qa = partition.query_analysis
        step_count = qa.step_count if qa else 0
        summary_html = (
            f"🔌 <strong>Power Query</strong>"
            f" &mdash; {step_count} step{'s' if step_count != 1 else ''}"
        )

        content_parts: list[str] = []

        if qa and qa.steps:
            headers = ["#", "Step", "Type", "Foldable"]
            rows = []
            for i, step in enumerate(qa.steps, 1):
                fold_icon = {True: "✅", False: "❌", None: "❓"}.get(
                    step.folding_impact, "❓"
                )
                rows.append([
                    _e(str(i)), _code(step.name), _e(step.transform_type), fold_icon,
                ])
            content_parts.append(_table(headers, rows))

        if qa and qa.query_folding_reason:
            f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
            content_parts.append(
                f"<p><strong>Query Folding:</strong> {f_icon} {_e(qa.query_folding_reason)}</p>"
            )

        if qa and qa.native_query:
            content_parts.append("<p><strong>Native Query:</strong></p>")
            content_parts.append(_pre(qa.native_query, lang="sql"))

        if qa and qa.incremental_refresh.is_incremental:
            ir = qa.incremental_refresh
            col_info = f" on {_code(ir.range_column)}" if ir.range_column else ""
            content_parts.append(
                f"<p>🔄 <strong>Incremental Refresh</strong> detected{col_info}</p>"
            )

        content_parts.append("<p><strong>Full M Expression:</strong></p>")
        content_parts.append(_pre(partition.expression, lang="m"))

        return _details(summary_html, "\n".join(content_parts))

    def _measures_index(self, model: SemanticModel, h: int = 0) -> str:
        n = len(model.all_measures)
        summary_html = (
            f"📋 {n} measure{'s' if n != 1 else ''} &mdash; click to expand"
        )
        headers = ["Measure", "Table", "Folder"]
        rows = []
        for table_name, measure in model.all_measures:
            folder = _e(measure.display_folder) if measure.display_folder else ""
            rows.append([_code(measure.name), _code(table_name), folder])

        return (
            '<section id="measures-index-az">\n'
            + _heading(2 + h, "Measures Index (A\u2013Z)")
            + "\n"
            + _details(summary_html, _table(headers, rows))
            + "\n</section>"
        )

    # ── report sections ───────────────────────────────────────────────────

    def _report_overview_section(self, metrics, h: int = 0) -> str:
        cx = metrics.complexity_index
        cx_icon = "🟢" if cx < 0.25 else ("🟡" if cx < 0.60 else "🔴")

        rows = [
            [_e("Report Format"), _e(metrics.report_format)],
            [
                _e("Total Pages"),
                _e(f"{metrics.total_pages} (hidden: {metrics.hidden_pages_count})"),
            ],
            [
                _e("Total Visuals"),
                _e(
                    f"{metrics.total_visuals}"
                    f" (avg {metrics.visuals_per_page_avg:.1f}/page,"
                    f" min {metrics.visuals_per_page_min},"
                    f" max {metrics.visuals_per_page_max})"
                ),
            ],
            [_e("Bookmarks"), _e(str(metrics.total_bookmarks))],
            [
                _e("Report-Level Measures"),
                _e(str(len(metrics.report_level_measures))),
            ],
            [
                f"<strong>{_e('Complexity Index')}</strong>",
                f"<strong>{cx_icon} {_e(f'{cx:.0%}')}</strong>",
            ],
        ]

        return (
            '<section id="overview">\n'
            + _heading(2 + h, "Overview")
            + "\n"
            + _table(["", ""], rows)
            + "\n</section>"
        )

    def _visual_types_section(self, metrics, h: int = 0) -> str:
        n = len(metrics.visual_types_count)
        total = metrics.total_visuals
        summary_html = (
            f"📊 {n} visual type{'s' if n != 1 else ''}"
            f" across {total} visuals &mdash; click to expand"
        )
        rows = []
        for vtype, count in sorted(
            metrics.visual_types_count.items(), key=lambda x: x[1], reverse=True
        ):
            pct = metrics.visual_types_percentage.get(vtype, 0.0)
            rows.append([_e(vtype), _e(str(count)), _e(f"{pct:.1f}%")])

        return (
            '<section id="visual-types-distribution">\n'
            + _heading(2 + h, "Visual Types Distribution")
            + "\n"
            + _details(summary_html, _table(["Visual Type", "Count", "Percentage"], rows))
            + "\n</section>"
        )

    def _custom_visuals_section(self, metrics, h: int = 0) -> str:
        n = len(metrics.custom_visuals)
        summary_html = (
            f"🔌 {n} marketplace visual{'s' if n != 1 else ''} &mdash; click to expand"
        )
        items = "\n".join(f"<li>{_code(v)}</li>" for v in metrics.custom_visuals)
        body_html = f"<ul>\n{items}\n</ul>"
        return (
            '<section id="custom-visuals">\n'
            + _heading(2 + h, "Custom Visuals")
            + "\n"
            + _details(summary_html, body_html)
            + "\n</section>"
        )

    def _bookmarks_section(self, metrics, h: int = 0) -> str:
        n = metrics.total_bookmarks
        summary_html = (
            f"🔖 {n} bookmark{'s' if n != 1 else ''} &mdash; click to expand"
        )
        items_html = ""
        if metrics.bookmark_names:
            items = "\n".join(f"<li>{_e(b)}</li>" for b in metrics.bookmark_names)
            items_html = f"<ul>\n{items}\n</ul>"
        body_html = f"<p>Total: {n}</p>\n{items_html}"
        return (
            '<section id="bookmarks">\n'
            + _heading(2 + h, "Bookmarks")
            + "\n"
            + _details(summary_html, body_html)
            + "\n</section>"
        )

    def _report_extensions_section(self, metrics, h: int = 0) -> str:
        n = len(metrics.report_level_measures)
        summary_html = (
            f"📐 {n} report-level measure{'s' if n != 1 else ''} &mdash; click to expand"
        )
        items_html = ""
        if metrics.report_level_measures:
            items = "\n".join(
                f"<li>{_code(m)}</li>" for m in metrics.report_level_measures
            )
            items_html = f"<ul>\n{items}\n</ul>"
        body_html = f"<p>Report-level measures: {n}</p>\n{items_html}"
        return (
            '<section id="report-extensions">\n'
            + _heading(2 + h, "Report Extensions")
            + "\n"
            + _details(summary_html, body_html)
            + "\n</section>"
        )

    def _advanced_metrics_section(self, metrics, h: int = 0) -> str:
        rows = [
            [_e("Pages with Drillthrough"), _e(str(metrics.pages_with_drillthrough))],
            [_e("Total Filters"), _e(str(metrics.total_filters))],
            [_e("Visuals with Mobile Layout"), _e(str(metrics.visuals_with_mobile_layout))],
        ]
        return (
            '<section id="advanced-metrics">\n'
            + _heading(2 + h, "Advanced Metrics")
            + "\n"
            + _table(["Metric", "Value"], rows)
            + "\n</section>"
        )

    # ── shared footer ─────────────────────────────────────────────────────

    @staticmethod
    def _footer() -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return (
            "<footer>\n"
            "<p><em>Generated by "
            '<a href="https://github.com/ViciusLio/pbi-semantic-doc">pbi-semantic-doc</a>'
            f" &middot; {_e(ts)}</em></p>\n"
            "</footer>"
        )
