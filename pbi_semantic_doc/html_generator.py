"""
HTML generator — produces a self-contained, printable HTML document from a
SemanticModel and/or ReportMetrics.

Features:
- Zero external dependencies (pure stdlib: html, re, datetime)
- All CSS and JS embedded — single file, no external assets
- Collapsible <details>/<summary> sections (same structure as .md output)
- @media print: all sections expand automatically — Ctrl+P → PDF works
- Sticky sidebar with search, active-section tracking, expand/collapse buttons
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
    --surface:      #f3f4f6;
    --border:       #d0d7de;
    --text:         #24292f;
    --muted:        #656d76;
    --code-bg:      #f6f8fa;
    --shadow:       0 1px 3px rgba(0,0,0,.08);
    --sidebar-w:    270px;
}
*, *::before, *::after { box-sizing: border-box; }

/* ── skip link ─────────────────────────────────────────────────────────── */
.skip-link {
    position: absolute; left: -9999px; top: 0; z-index: 9999;
    background: var(--accent); color: #fff; font-weight: 700;
    padding: .5em 1.2em; border-radius: 0 0 4px 4px; text-decoration: none;
}
.skip-link:focus { left: 0; }

/* ── layout ────────────────────────────────────────────────────────────── */
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 15px; line-height: 1.6; color: var(--text); background: var(--bg); }
.layout { display: flex; min-height: 100vh; }

/* ── sidebar ───────────────────────────────────────────────────────────── */
.sidebar {
    width: var(--sidebar-w);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: var(--surface);
    border-right: 1px solid var(--border);
}
.sidebar-header {
    padding: .9rem 1.1rem .7rem;
    background: var(--accent);
    flex-shrink: 0;
}
.sidebar-title {
    font-weight: 700; font-size: .9rem; color: #fff;
    display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar-subtitle { font-size: .72rem; color: rgba(255,255,255,.75); margin-top: .15em; }
.sidebar-search {
    padding: .5rem .8rem; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.sidebar-search input {
    width: 100%; padding: .3em .6em; border: 1px solid var(--border);
    border-radius: 4px; font-size: .82em; background: var(--bg); color: var(--text);
}
.sidebar-search input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.sidebar-nav { flex: 1; overflow-y: auto; padding: .4rem 0; }
.sidebar-nav ul { list-style: none; margin: 0; padding: 0; }
.sidebar-nav li { margin: 0; }
.sidebar-nav a {
    display: block; padding: .28em 1.1em;
    font-size: .83em; color: var(--text); text-decoration: none;
    border-left: 3px solid transparent; transition: background .12s, border-color .12s;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar-nav a:hover { background: var(--accent-light); color: var(--accent); border-left-color: var(--accent); }
.sidebar-nav a.active { background: var(--accent-light); color: var(--accent); border-left-color: var(--accent); font-weight: 600; }
.nav-group-label {
    display: block; padding: .55em 1.1em .2em;
    font-size: .72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: var(--muted);
}
/* nav-level collapsible (tables group) — no card style, no shadow */
.nav-details { border: none; box-shadow: none; background: transparent; margin: 0; border-radius: 0; }
.nav-details[open] { background: transparent; }
.nav-details > summary.nav-group-summary {
    display: block; padding: .5em 1.1em .2em;
    font-size: .72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: var(--muted);
    border-radius: 0; border-left: 3px solid transparent;
    cursor: pointer; user-select: none; list-style: none;
}
.nav-details > summary.nav-group-summary::-webkit-details-marker { display: none; }
.nav-details > summary.nav-group-summary::before { content: "\\25B6\\00A0"; font-size: .72em; }
.nav-details[open] > summary.nav-group-summary::before { content: "\\25BC\\00A0"; }
.nav-details > summary.nav-group-summary:hover { color: var(--accent); background: var(--accent-light); border-left-color: var(--accent); }
.nav-sub a { padding-left: 2em; }
.sidebar-footer {
    padding: .6rem .8rem; border-top: 1px solid var(--border);
    display: flex; gap: .35em; flex-shrink: 0;
}
.sidebar-footer button {
    flex: 1; background: var(--bg); border: 1px solid var(--border);
    border-radius: 4px; padding: .28em .4em; cursor: pointer;
    font-size: .75em; color: var(--text); transition: background .1s;
}
.sidebar-footer button:hover { background: var(--accent-light); border-color: var(--accent); color: var(--accent); }

/* ── main content ──────────────────────────────────────────────────────── */
.main-content {
    flex: 1; min-width: 0;
    padding: 2rem 2.5rem 4rem;
    max-width: 980px;
}
.doc-header { margin-bottom: 1.5rem; }
.doc-header h1 {
    font-size: 1.75rem;
    border-bottom: 3px solid var(--accent);
    padding-bottom: .35em; margin: 0 0 .3em;
}
.doc-meta { color: var(--muted); font-size: .82em; margin: 0; }

/* ── typography ────────────────────────────────────────────────────────── */
h2 { font-size: 1.25rem; border-bottom: 1px solid var(--border); padding-bottom: .2em; margin-top: 2.2rem; }
h3 { font-size: 1.05rem; margin-top: 1.4rem; }
h4 { font-size: .95rem; margin-top: .9rem; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
blockquote { border-left: 4px solid var(--accent); margin: .6em 0; padding: .2em .9em; background: var(--accent-light); border-radius: 0 4px 4px 0; color: var(--muted); }
p { margin: .45em 0; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* ── code ──────────────────────────────────────────────────────────────── */
code { font-family: "Cascadia Code", Consolas, "SFMono-Regular", monospace; font-size: .875em; background: var(--code-bg); border: 1px solid var(--border); border-radius: 4px; padding: .1em .4em; }
pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px; padding: .9em 1.2em; overflow-x: auto; margin: .6em 0; }
pre code { background: none; border: none; padding: 0; font-size: .85em; }

/* ── tables ────────────────────────────────────────────────────────────── */
table { border-collapse: collapse; width: 100%; margin: .6em 0; font-size: .9em; }
thead tr { background: var(--accent); color: #fff; }
th { padding: .4em .75em; text-align: left; font-weight: 600; white-space: nowrap; }
td { padding: .3em .75em; border-bottom: 1px solid var(--border); vertical-align: top; }
tbody tr:nth-child(even) td { background: var(--surface); }
tbody tr:hover td { background: var(--accent-light); transition: background .1s; }

/* ── details / summary ─────────────────────────────────────────────────── */
details { border: 1px solid var(--border); border-radius: 6px; margin: .4em 0; background: var(--bg); box-shadow: var(--shadow); }
details[open] { background: var(--surface); }
summary { cursor: pointer; font-weight: 500; padding: .55em 1em; list-style: none; user-select: none; border-radius: 5px; }
summary::-webkit-details-marker { display: none; }
summary::before { content: "\\25B6\\00A0"; font-size: .75em; color: var(--muted); }
details[open] > summary::before { content: "\\25BC\\00A0"; }
.details-body { padding: .7em 1em 1em; border-top: 1px solid var(--border); }

/* ── folder groups (inside Measures section) ───────────────────────────── */
details.folder-group {
    border: 1px solid var(--border);
    border-left: 3px solid #8ab4f8;
    border-radius: 6px;
    margin: .5em 0 .7em;
    box-shadow: none;
    background: var(--bg);
}
details.folder-group[open] { background: var(--bg); }
details.folder-group > summary {
    font-size: .9em; font-weight: 700;
    padding: .5em .9em;
    display: flex; align-items: center; gap: .4em;
    border-radius: 5px;
    color: var(--text);
}
.folder-body {
    padding: .3em .5em .5em 1.2em;
}
.badge-count {
    background: var(--code-bg); color: var(--muted);
    border: 1px solid var(--border); border-radius: 10px;
    padding: .05em .5em; font-size: .72em; font-weight: 500;
    margin-left: auto;
}

/* ── measure cards ─────────────────────────────────────────────────────── */
details.measure-card {
    border-left: 3px solid var(--accent);
    margin: .35em 0;
}
details.measure-card > summary {
    display: flex; align-items: center; gap: .5em; flex-wrap: wrap;
    font-size: .92em;
}
.measure-card-name { font-weight: 600; }
.measure-card-badges { display: flex; gap: .3em; margin-left: auto; flex-wrap: wrap; align-items: center; }
.badge-fmt { background: var(--code-bg); color: var(--muted); border: 1px solid var(--border); border-radius: 3px; padding: .05em .45em; font-size: .75em; font-family: "Cascadia Code", Consolas, monospace; }
.badge-hidden { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 3px; padding: .05em .35em; font-size: .72em; }
.badge-folder { background: var(--accent-light); color: var(--accent); border: 1px solid #b3d4ef; border-radius: 3px; padding: .05em .35em; font-size: .72em; }

/* ── lineage badges ────────────────────────────────────────────────────── */
.lineage-row { display: flex; flex-wrap: wrap; gap: .35em; align-items: center; margin: .3em 0; font-size: .83em; }
.lineage-label { color: var(--muted); font-weight: 600; min-width: 7em; }
.badge-compatible { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 3px; padding: .1em .4em; font-size: .78em; }
.badge-incompatible { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 3px; padding: .1em .4em; font-size: .78em; }
.badge-removed { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 3px; padding: .1em .4em; font-size: .78em; }
.badge-dep { background: var(--code-bg); color: var(--muted); border: 1px solid var(--border); border-radius: 3px; padding: .1em .4em; font-size: .78em; }

/* ── back-to-top ───────────────────────────────────────────────────────── */
.back-to-top {
    position: fixed; bottom: 1.5rem; right: 1.5rem;
    width: 2.4rem; height: 2.4rem; border-radius: 50%;
    background: var(--accent); color: #fff; border: none;
    font-size: 1.1rem; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,.22);
    opacity: 0; transition: opacity .2s; z-index: 100; line-height: 1;
}
.back-to-top.visible { opacity: 1; }
.back-to-top:hover { background: #005a9e; }

/* ── footer ────────────────────────────────────────────────────────────── */
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: .82em; text-align: center; }

/* ── responsive ────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .layout { flex-direction: column; }
    .sidebar { width: 100%; height: auto; position: relative; border-right: none; border-bottom: 1px solid var(--border); }
    .sidebar-nav { max-height: 240px; }
    .main-content { padding: 1.25rem 1.1rem 3rem; }
}

/* ── print ─────────────────────────────────────────────────────────────── */
@media print {
    .sidebar, .back-to-top, .skip-link { display: none !important; }
    .layout { display: block; }
    .main-content { padding: 0; max-width: 100%; }
    .doc-header h1 { font-size: 18pt; }
    details { display: block !important; border: none; box-shadow: none; padding: 0; border-left: none !important; }
    summary { display: none !important; }
    .details-body { padding: 0; border: none; }
    h2 { font-size: 14pt; margin-top: 1.5em; page-break-after: avoid; }
    table, pre, blockquote { page-break-inside: avoid; }
    thead { display: table-header-group; }
    a[href^="#"]::after { content: ""; }
    body { font-size: 11pt; }
    tbody tr:hover td { background: inherit; }
}
"""

# ── embedded JS ───────────────────────────────────────────────────────────

_JS = """\
// Expand / collapse all
function toggleAll(open) {
    document.querySelectorAll('details').forEach(function(d) { d.open = open; });
}

// Back-to-top button
(function () {
    var btn = document.getElementById('back-to-top');
    if (!btn) return;
    var onScroll = function () { btn.classList.toggle('visible', window.scrollY > 320); };
    window.addEventListener('scroll', onScroll, { passive: true });
    btn.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
}());

// Active section in sidebar (IntersectionObserver)
(function () {
    var links = document.querySelectorAll('.sidebar-nav a[href^="#"]');
    if (!links.length || !window.IntersectionObserver) return;
    var map = {};
    links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var current = '';
    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
            if (e.isIntersecting) {
                current = e.target.id;
                Object.values(map).forEach(function (a) { a.classList.remove('active'); });
                if (map[current]) {
                    map[current].classList.add('active');
                    // scroll link into sidebar view
                    map[current].scrollIntoView({ block: 'nearest' });
                }
            }
        });
    }, { rootMargin: '-8% 0px -80% 0px', threshold: 0 });
    Object.keys(map).forEach(function (id) {
        var el = document.getElementById(id);
        if (el) observer.observe(el);
    });
}());

// Sidebar search filter
(function () {
    var inp = document.getElementById('sidebar-search');
    if (!inp) return;
    inp.addEventListener('input', function () {
        var q = this.value.toLowerCase();
        document.querySelectorAll('.sidebar-nav li').forEach(function (li) {
            li.style.display = li.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
}());
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


def _html_page(title: str, sidebar: str, main: str) -> str:
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
        '<a href="#main-content" class="skip-link">Skip to content</a>\n'
        '<div class="layout">\n'
        f'<aside class="sidebar no-print" aria-label="Document navigation">\n{sidebar}\n</aside>\n'
        f'<main id="main-content" class="main-content">\n{main}\n</main>\n'
        "</div>\n"
        '<button id="back-to-top" class="back-to-top no-print" aria-label="Back to top">↑</button>\n'
        f"<script>\n{_JS}</script>\n"
        "</body>\n"
        "</html>\n"
    )


def _sidebar_html(title: str, subtitle: str, nav_html: str) -> str:
    """Render the sidebar: header + search + nav + expand/collapse buttons."""
    return (
        f'<div class="sidebar-header">'
        f'<span class="sidebar-title">{_e(title)}</span>'
        f'<span class="sidebar-subtitle">{_e(subtitle)}</span>'
        f'</div>\n'
        f'<div class="sidebar-search">'
        f'<input type="search" id="sidebar-search" placeholder="🔍 Filter…" aria-label="Filter navigation">'
        f'</div>\n'
        f'<nav class="sidebar-nav" aria-label="Table of contents">\n{nav_html}\n</nav>\n'
        f'<div class="sidebar-footer">'
        f'<button onclick="toggleAll(true)" title="Expand all sections">⊞ Expand</button>'
        f'<button onclick="toggleAll(false)" title="Collapse all sections">⊟ Collapse</button>'
        f'</div>'
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
        try:
            self._lineage_map: dict = ModelLineage(model).resolve_all()
        except Exception:
            self._lineage_map = {}

        # Build sidebar
        nav_html = self._model_sidebar_nav(model)
        sidebar = _sidebar_html(model.name, "Semantic Model", nav_html)

        # Build main content
        parts: list[str] = []
        parts.append(
            f'<div class="doc-header">'
            f'<h1>{_e(model.name)} — Semantic Model</h1>'
            f'<p class="doc-meta">Generated by pbi-semantic-doc</p>'
            f'</div>'
        )
        parts.append(self._model_inner(model, heading_offset=0))
        parts.append(self._footer())
        main = "\n\n".join(parts)

        self._lineage_map = {}
        return _html_page(title=f"DOC — {model.name}", sidebar=sidebar, main=main)

    def generate_report(self, metrics) -> str:
        """Generate a self-contained HTML document for a report."""
        self._lineage_map = {}

        nav_html = self._report_sidebar_nav(metrics)
        sidebar = _sidebar_html(metrics.report_name, "Report Analysis", nav_html)

        parts: list[str] = []
        parts.append(
            f'<div class="doc-header">'
            f'<h1>{_e(metrics.report_name)} — Report Analysis</h1>'
            f'<p class="doc-meta">Generated by pbi-semantic-doc</p>'
            f'</div>'
        )
        parts.append(self._report_inner(metrics, heading_offset=0))
        parts.append(self._footer())
        main = "\n\n".join(parts)

        return _html_page(title=f"DOC — {metrics.report_name}", sidebar=sidebar, main=main)

    def generate_combined(
        self,
        model: Optional[SemanticModel],
        report_metrics,
        project_name: str,
    ) -> str:
        """Generate a unified HTML document covering both model and report."""
        # Build combined sidebar nav
        nav_items: list[str] = []
        if model:
            nav_items.append('<li><span class="nav-group-label">Semantic Model</span>')
            nav_items.append('<ul class="nav-sub">')
            nav_items.append('<li><a href="#sm-overview">Overview</a></li>')
            ds = model.data_sources
            if ds:
                nav_items.append('<li><a href="#sm-data-sources">Data Sources</a></li>')
            if model.relationships:
                nav_items.append('<li><a href="#sm-relationships">Relationships</a></li>')
            if model.roles:
                nav_items.append('<li><a href="#sm-row-level-security">Row Level Security</a></li>')
            for table in model.visible_tables:
                raw_anchor = _section_anchor(f"Table: `{table.name}`")
                anchor = f"sm-{raw_anchor}"
                icon = _MODE_ICON.get(table.effective_mode, "📋")
                nav_items.append(
                    f'<li><a href="#{_attr(anchor)}" title="{_attr(table.name)}">'
                    f'{icon} {_e(table.name)}</a></li>'
                )
            if model.all_measures:
                n = len(model.all_measures)
                nav_items.append(f'<li><a href="#sm-measures-index-az">📋 Measures ({n})</a></li>')
            nav_items.append('</ul></li>')

        if report_metrics:
            nav_items.append('<li><span class="nav-group-label">Report</span>')
            nav_items.append('<ul class="nav-sub">')
            nav_items.append('<li><a href="#rpt-overview">Overview</a></li>')
            if report_metrics.visual_types_count:
                nav_items.append('<li><a href="#rpt-visual-types-distribution">Visual Types</a></li>')
            if report_metrics.custom_visuals:
                nav_items.append('<li><a href="#rpt-custom-visuals">Custom Visuals</a></li>')
            if report_metrics.has_bookmarks:
                nav_items.append('<li><a href="#rpt-bookmarks">Bookmarks</a></li>')
            if report_metrics.has_report_extensions:
                nav_items.append('<li><a href="#rpt-report-extensions">Report Extensions</a></li>')
            nav_items.append('<li><a href="#rpt-advanced-metrics">Advanced Metrics</a></li>')
            nav_items.append('</ul></li>')

        nav_html = f'<ul>\n{"".join(nav_items)}\n</ul>'
        sidebar = _sidebar_html(project_name, "Power BI Documentation", nav_html)

        # Build main content
        parts: list[str] = []
        parts.append(
            f'<div class="doc-header">'
            f'<h1>{_e(project_name)} — Power BI Documentation</h1>'
            f'<p class="doc-meta">Generated by pbi-semantic-doc</p>'
            f'</div>'
        )

        if model:
            try:
                self._lineage_map = ModelLineage(model).resolve_all()
            except Exception:
                self._lineage_map = {}
            parts.append('<section id="semantic-model">')
            parts.append('<h2>Semantic Model</h2>')
            parts.append(self._model_inner_prefixed(model, prefix="sm-"))
            parts.append("</section>")
            self._lineage_map = {}

        if model and report_metrics:
            parts.append("<hr>")

        if report_metrics:
            parts.append('<section id="report">')
            parts.append('<h2>Report</h2>')
            parts.append(self._report_inner_prefixed(report_metrics, prefix="rpt-"))
            parts.append("</section>")

        parts.append(self._footer())
        main = "\n\n".join(parts)

        return _html_page(title=f"DOC — {project_name}", sidebar=sidebar, main=main)

    # ── model body (standalone) ───────────────────────────────────────────

    def _model_body(self, model: SemanticModel) -> str:
        # This is used internally but generate() now calls _html_page directly
        # Keep for backward compatibility
        nav_html = self._model_sidebar_nav(model)
        sidebar = _sidebar_html(model.name, "Semantic Model", nav_html)
        parts: list[str] = []
        parts.append(
            f'<div class="doc-header">'
            f'<h1>{_e(model.name)} — Semantic Model</h1>'
            f'<p class="doc-meta">Generated by pbi-semantic-doc</p>'
            f'</div>'
        )
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

    def _model_inner_prefixed(self, model: SemanticModel, prefix: str = "") -> str:
        """Model content with section IDs prefixed (for combined doc to avoid anchor collisions)."""
        # We temporarily override _overview_section and _table_section anchors
        # by using heading_offset=0 but passing the prefix through the section id
        # Simple approach: generate normal inner, then do a string replace on section ids
        raw = self._model_inner(model, heading_offset=0)
        # Prefix section IDs: id="overview" -> id="sm-overview", href="#overview" -> href="#sm-overview"
        if prefix:
            raw = re.sub(r' id="([^"]+)"', lambda m: f' id="{prefix}{m.group(1)}"', raw)
            raw = re.sub(r' href="#([^"]+)"', lambda m: f' href="#{prefix}{m.group(1)}"', raw)
        return raw

    def _report_inner_prefixed(self, metrics, prefix: str = "") -> str:
        """Report content with section IDs prefixed."""
        raw = self._report_inner(metrics, heading_offset=0)
        if prefix:
            raw = re.sub(r' id="([^"]+)"', lambda m: f' id="{prefix}{m.group(1)}"', raw)
            raw = re.sub(r' href="#([^"]+)"', lambda m: f' href="#{prefix}{m.group(1)}"', raw)
        return raw

    # ── report body (standalone) ──────────────────────────────────────────

    def _report_body(self, metrics) -> str:
        nav_html = self._report_sidebar_nav(metrics)
        sidebar = _sidebar_html(metrics.report_name, "Report Analysis", nav_html)
        parts: list[str] = []
        parts.append(
            f'<div class="doc-header">'
            f'<h1>{_e(metrics.report_name)} — Report Analysis</h1>'
            f'<p class="doc-meta">Generated by pbi-semantic-doc</p>'
            f'</div>'
        )
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

    # ── sidebar nav builders ──────────────────────────────────────────────

    def _model_sidebar_nav(self, model: SemanticModel, h_offset: int = 0) -> str:
        """Build sidebar navigation list for the model."""
        items: list[str] = []

        # Top-level sections
        items.append(f'<li><a href="#overview">Overview</a></li>')

        ds = model.data_sources
        if ds:
            items.append(f'<li><a href="#data-sources">Data Sources</a></li>')

        if model.relationships:
            items.append(f'<li><a href="#relationships">Relationships</a></li>')

        if model.roles:
            items.append(f'<li><a href="#row-level-security">Row Level Security</a></li>')

        # Tables group — collapsible so 150+ tables don't flood the sidebar
        if model.visible_tables:
            n_tables = len(model.visible_tables)
            table_links: list[str] = []
            for table in model.visible_tables:
                anchor = _section_anchor(f"Table: `{table.name}`")
                mode = table.effective_mode
                icon = _MODE_ICON.get(mode, "🧮" if mode == "calculated" else "📋")
                n_meas = len(table.measures)
                meas_note = f" · {n_meas}m" if n_meas else ""
                table_links.append(
                    f'<li><a href="#{_attr(anchor)}" title="{_attr(table.name)}">'
                    f'{icon} {_e(table.name)}{_e(meas_note)}</a></li>'
                )
            table_list = "\n".join(table_links)
            items.append(
                f'<li class="nav-tables-group">'
                f'<details class="nav-details">'
                f'<summary class="nav-group-summary">📊 Tables ({n_tables})</summary>'
                f'<ul class="nav-sub">{table_list}</ul>'
                f'</details></li>'
            )

        # Measures index
        if model.all_measures:
            n = len(model.all_measures)
            items.append(f'<li><a href="#measures-index-az">📋 Measures Index ({n})</a></li>')

        return f'<ul>\n{"".join(items)}\n</ul>'

    def _report_sidebar_nav(self, metrics) -> str:
        """Build sidebar navigation list for the report."""
        items: list[str] = []
        items.append('<li><a href="#overview">Overview</a></li>')
        if metrics.visual_types_count:
            items.append('<li><a href="#visual-types-distribution">Visual Types</a></li>')
        if metrics.custom_visuals:
            items.append('<li><a href="#custom-visuals">Custom Visuals</a></li>')
        if metrics.has_bookmarks:
            items.append('<li><a href="#bookmarks">Bookmarks</a></li>')
        if metrics.has_report_extensions:
            items.append('<li><a href="#report-extensions">Report Extensions</a></li>')
        items.append('<li><a href="#advanced-metrics">Advanced Metrics</a></li>')
        return f'<ul>\n{"".join(items)}\n</ul>'

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
            content_parts.append(self._measures_section_html(table.measures, h, table.name))

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

    def _measure_html(self, measure: Measure, h: int = 0, table_name: str = "",
                      show_folder: bool = True) -> str:
        # Build summary line
        hidden_badge = ' <span class="badge-hidden">hidden</span>' if measure.is_hidden else ""
        fmt_badge = (
            f' <span class="badge-fmt">{_e(measure.format_string)}</span>'
            if measure.format_string
            else ""
        )
        folder_badge = (
            f' <span class="badge-folder">📁 {_e(measure.display_folder)}</span>'
            if measure.display_folder and show_folder
            else ""
        )
        summary_html = (
            f'<span class="measure-card-name">{_code(measure.name)}</span>'
            f'<span class="measure-card-badges">{fmt_badge}{folder_badge}{hidden_badge}</span>'
        )

        # Build body content
        content_parts: list[str] = []

        if measure.description:
            content_parts.append(f"<p>{_e(measure.description)}</p>")

        auto_desc = measure.auto_description()
        if auto_desc and not measure.description:
            content_parts.append(f"<p><em>{_e(auto_desc)}</em></p>")

        if measure.expression:
            content_parts.append(_pre(measure.expression, lang="dax"))

        # Lineage section
        if table_name and hasattr(self, "_lineage_map"):
            lin = self._lineage_map.get((table_name, measure.name))
            if lin and lin.has_lineage_info:
                content_parts.append(self._measure_lineage_html(lin))

        body_html = "\n".join(content_parts) if content_parts else "<p><em>No expression.</em></p>"

        return (
            f'<details class="measure-card">\n'
            f'<summary>{summary_html}</summary>\n'
            f'<div class="details-body">\n{body_html}\n</div>\n'
            f'</details>'
        )

    # ── folder-tree helpers ────────────────────────────────────────────────

    @staticmethod
    def _build_folder_tree(measures) -> dict:
        """Build a nested dict from display_folder paths.

        Tree shape: {segment: subtree_dict}
        At each level, key None holds the list of Measure objects that live
        directly in that folder (i.e. their display_folder ends here).
        """
        tree: dict = {}
        for m in sorted(measures, key=lambda x: x.name.lower()):
            raw = (m.display_folder or "").replace("\\", "/")
            parts = [p for p in raw.split("/") if p]
            node = tree
            for part in parts:
                if part not in node:
                    node[part] = {}
                node = node[part]
            node.setdefault(None, []).append(m)
        return tree

    @staticmethod
    def _count_tree_measures(tree: dict) -> int:
        """Count total measures in a subtree."""
        count = len(tree.get(None, []))
        for k, v in tree.items():
            if k is not None:
                count += HtmlGenerator._count_tree_measures(v)
        return count

    def _render_folder_tree(self, tree: dict, h: int, table_name: str) -> str:
        """Recursively render a folder tree as nested <details> groups."""
        parts: list[str] = []

        # Measures at this level (no sub-folder)
        for m in tree.get(None, []):
            parts.append(self._measure_html(m, h, table_name, show_folder=False))

        # Sub-folders
        for folder_name in sorted(k for k in tree if k is not None):
            subtree = tree[folder_name]
            count = self._count_tree_measures(subtree)
            inner = self._render_folder_tree(subtree, h, table_name)
            parts.append(
                f'<details class="folder-group" open>\n'
                f'<summary>📁 <strong>{_e(folder_name)}</strong>'
                f' <span class="badge-count">{count}</span></summary>\n'
                f'<div class="folder-body">{inner}</div>\n'
                f'</details>'
            )

        return "\n".join(parts)

    def _measures_section_html(self, measures, h: int, table_name: str) -> str:
        """Render measures grouped by folder (or flat if no folders used)."""
        has_folders = any(m.display_folder for m in measures)
        if not has_folders:
            return "\n".join(
                self._measure_html(m, h, table_name)
                for m in sorted(measures, key=lambda m: m.name.lower())
            )
        tree = self._build_folder_tree(measures)
        return self._render_folder_tree(tree, h, table_name)

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
        summary_html = f"📋 {n} measure{'s' if n != 1 else ''} — click to expand"

        cards: list[str] = []
        for table_name, measure in model.all_measures:
            # Table badge before each measure card
            cards.append(
                f'<p style="margin:.6em 0 .1em;font-size:.78em;color:var(--muted);">'
                f'Table: {_code(table_name)}</p>'
            )
            cards.append(self._measure_html(measure, h=0, table_name=table_name))

        body_html = "\n".join(cards)

        return (
            '<section id="measures-index-az">\n'
            + _heading(2 + h, "Measures Index (A\u2013Z)")
            + "\n"
            + _details(summary_html, body_html)
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
