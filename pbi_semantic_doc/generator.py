"""
Markdown generator — takes a SemanticModel object and produces
a well-structured Markdown document.

Uses HTML <details>/<summary> for collapsible column sections,
which renders natively in GitHub and GitLab.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .parser import SemanticModel, ModelMetrics, Table, Measure, Relationship


class MarkdownGenerator:
    """
    Generates a single Markdown file documenting a SemanticModel.

    Usage:
        gen = MarkdownGenerator()
        output = gen.generate(model)
        Path("MODEL_DOC.md").write_text(output)
    """

    def generate(self, model: SemanticModel) -> str:
        sections: list[str] = []

        sections.append(self._header(model))
        sections.append(self._overview(model))

        if model.relationships:
            sections.append(self._relationships_section(model.relationships))

        for table in model.visible_tables:
            sections.append(self._table_section(table))

        if model.all_measures:
            sections.append(self._measures_index(model))

        sections.append(self._footer())

        return "\n\n".join(sections) + "\n"

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _header(self, model: SemanticModel) -> str:
        return f"# {model.name} — Semantic Model Documentation"

    def _overview(self, model: SemanticModel) -> str:
        metrics = model.calculate_metrics()
        visible = model.visible_tables
        visible_cols = sum(sum(1 for c in t.columns if not c.is_hidden) for t in visible)
        hidden_cols  = metrics.hidden_columns

        lines = [
            "## Overview",
            "",
            "| | |",
            "|---|---|",
            f"| Tables | {len(visible)} visible, {metrics.hidden_tables} hidden |",
            f"| Columns | {visible_cols} visible, {hidden_cols} hidden |",
            f"| Measures | {metrics.total_measures} |",
            f"| Relationships | {metrics.total_relationships} ({metrics.inactive_relationships} inactive) |",
            f"| **Complexity Index** | **{metrics.complexity_index:.0%}** |",
        ]
        return "\n".join(lines)

    def _relationships_section(self, relationships: list[Relationship]) -> str:
        lines = ["## Relationships", ""]
        lines.append("| From | | To | Cardinality | Cross-filter | Active |")
        lines.append("|---|---|---|---|---|---|")

        for r in relationships:
            active_icon = "✅" if r.is_active else "⬜"
            from_ref = f"`{r.from_table}`[{r.from_column}]"
            to_ref   = f"`{r.to_table}`[{r.to_column}]"
            lines.append(
                f"| {from_ref} | → | {to_ref} | {r.cardinality} | {r.cross_filter} | {active_icon} |"
            )

        return "\n".join(lines)

    def _table_section(self, table: Table) -> str:
        lines = [f"## Table: `{table.name}`"]

        if table.description:
            lines += ["", table.description]

        # Columns — collapsible with <details>
        # Only show if there are visible columns (skip placeholder-only tables like "Misure")
        if table.columns:
            visible_cols = [c for c in table.columns if not c.is_hidden]
            hidden_cols  = [c for c in table.columns if c.is_hidden]
            
            # Only show columns section if there are visible columns
            if visible_cols:
                lines += [""]
                lines.append(self._collapsible_columns(visible_cols, hidden_cols))

        # Measures
        if table.measures:
            lines += ["", "### Measures", ""]
            for measure in sorted(table.measures, key=lambda m: m.name.lower()):
                lines.append(self._measure_block(measure))

        return "\n".join(lines)

    def _collapsible_columns(self, visible: list, hidden: list) -> str:
        """Generate collapsible HTML details section for columns"""
        total = len(visible) + len(hidden)
        hidden_note = f", {len(hidden)} hidden" if hidden else ""
        summary = f"### Columns ({len(visible)} visible{hidden_note} — click to expand)"

        rows = []
        rows.append("| Column | Type | Description | Format | Hidden |")
        rows.append("|---|---|---|---|---|")

        for col in visible:
            fmt  = f"`{col.format_string}`" if col.format_string else ""
            rows.append(f"| `{col.name}` | {col.data_type} | {col.description} | {fmt} | |")

        for col in hidden:
            fmt  = f"`{col.format_string}`" if col.format_string else ""
            rows.append(f"| `{col.name}` | {col.data_type} | {col.description} | {fmt} | ✗ |")

        table_md = "\n".join(rows)

        return (
            f"<details>\n"
            f"<summary>{summary}</summary>\n\n"
            f"{table_md}\n\n"
            f"</details>"
        )

    def _measure_block(self, measure: Measure) -> str:
        lines: list[str] = []
        hidden_tag = " *(hidden)*" if measure.is_hidden else ""
        folder_tag = f" · 📁 `{measure.display_folder}`" if measure.display_folder else ""

        lines.append(f"#### `{measure.name}`{hidden_tag}{folder_tag}")

        if measure.description:
            lines += ["", measure.description]

        auto_desc = measure.auto_description()
        if auto_desc and not measure.description:
            lines += ["", f"*{auto_desc}*"]

        if measure.format_string:
            lines += ["", f"**Format:** `{measure.format_string}`"]

        if measure.expression:
            lines += ["", "```dax", measure.expression, "```"]

        return "\n".join(lines)

    def _measures_index(self, model: SemanticModel) -> str:
        lines = ["## Measures Index (A–Z)", ""]
        lines.append("| Measure | Table | Folder |")
        lines.append("|---|---|---|")

        for table_name, measure in model.all_measures:
            folder = measure.display_folder or ""
            lines.append(f"| `{measure.name}` | `{table_name}` | {folder} |")

        return "\n".join(lines)

    def _footer(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return (
            "---\n\n"
            f"*Generated by [pbi-semantic-doc](https://github.com/viciuslios/pbi-semantic-doc) · {ts}*"
        )
