"""
Markdown generator — takes a SemanticModel object and produces
a well-structured Markdown document.

Uses HTML <details>/<summary> for collapsible column sections,
which renders natively in GitHub and GitLab.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .parser import (
    SemanticModel, ModelMetrics, Table, Measure, Relationship,
    Partition, Role, MQueryAnalysis,
)

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

        # Data Sources (only if any partition has a connector)
        ds_section = self._data_sources_section(model)
        if ds_section:
            sections.append(ds_section)

        if model.relationships:
            sections.append(self._relationships_section(model.relationships))

        # RLS Roles
        if model.roles:
            sections.append(self._rls_section(model))

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
        ]

        if model.roles:
            lines.append(f"| RLS Roles | {len(model.roles)} |")

        lines.append(f"| **Complexity Index** | **{metrics.complexity_index:.0%}** |")

        return "\n".join(lines)

    def _data_sources_section(self, model: SemanticModel) -> str:
        """Global data sources table — one row per table/partition with a connector."""
        rows: list[tuple] = []

        for table in model.tables:
            for partition in table.partitions:
                qa = partition.query_analysis
                if not qa:
                    continue

                if qa.query_type == "calculated":
                    rows.append((table.name, "—", "—", "—", "Calculated (DAX)", "—", "—", ""))
                    continue
                if qa.query_type == "entity":
                    rows.append((table.name, "—", "—", "—", "DirectLake Entity", "—", "—", ""))
                    continue
                if not qa.connector:
                    continue

                conn = qa.connector
                server = conn.positional_params[0] if conn.positional_params else "—"
                database = conn.positional_params[1] if len(conn.positional_params) > 1 else "—"

                if conn.is_parameterized:
                    server = f"{server} *(param)*"

                mode = _MODE_LABEL.get(partition.mode, partition.mode)
                steps = str(qa.step_count) if qa.step_count > 0 else "—"

                f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
                f_label = _FOLDING_LABEL.get(qa.query_folding_status, qa.query_folding_status)
                folding = f"{f_icon} {f_label}"
                if qa.query_type == "native_sql":
                    folding += " *(native SQL)*"

                incremental = " 🔄" if qa.incremental_refresh.is_incremental else ""

                rows.append((
                    table.name, conn.source_type, server, database,
                    mode, steps, folding, incremental,
                ))

        if not rows:
            return ""

        lines = [
            "## Data Sources",
            "",
            "| Table | Connector | Server / Path | Database | Mode | Steps | Query Folding |",
            "|-------|-----------|--------------|----------|------|-------|---------------|",
        ]
        for name, source_type, server, database, mode, steps, folding, incr in rows:
            lines.append(
                f"| `{name}`{incr} | {source_type} | {server} | {database} "
                f"| {mode} | {steps} | {folding} |"
            )

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

    def _rls_section(self, model: SemanticModel) -> str:
        """Row Level Security section."""
        lines = ["## Row Level Security", ""]
        lines.append("| Role | Permission | Table | Filter |")
        lines.append("|------|-----------|-------|--------|")

        for role in model.roles:
            if not role.table_permissions:
                lines.append(
                    f"| **{role.name}** | {role.model_permission} "
                    f"| *(no table filters)* | — |"
                )
                continue
            for i, tp in enumerate(role.table_permissions):
                role_display = f"**{role.name}**" if i == 0 else ""
                perm_display = role.model_permission if i == 0 else ""
                if tp.filter_expression.lower() == "true":
                    filter_display = "*(no row filter)*"
                else:
                    filter_display = f"`{tp.filter_expression}`"
                lines.append(
                    f"| {role_display} | {perm_display} "
                    f"| `{tp.table_name}` | {filter_display} |"
                )

        return "\n".join(lines)

    def _table_section(self, table: Table) -> str:
        lines = [f"## Table: `{table.name}`"]

        if table.description:
            lines += ["", table.description]

        # Partition / source info badge
        badge = self._partition_badge(table)
        if badge:
            lines += ["", badge]

        # Columns — collapsible
        if table.columns:
            visible_cols = [c for c in table.columns if not c.is_hidden]
            hidden_cols  = [c for c in table.columns if c.is_hidden]
            if visible_cols:
                lines += [""]
                lines.append(self._collapsible_columns(visible_cols, hidden_cols))

        # Measures
        if table.measures:
            lines += ["", "### Measures", ""]
            for measure in sorted(table.measures, key=lambda m: m.name.lower()):
                lines.append(self._measure_block(measure))

        # M expression — collapsible per partition
        for partition in table.partitions:
            if partition.expression and partition.type == "m":
                lines += [""]
                lines.append(self._collapsible_m_expression(partition))

        return "\n".join(lines)

    def _partition_badge(self, table: Table) -> str:
        """Compact source info line(s) shown just below the table heading."""
        parts: list[str] = []
        for p in table.partitions:
            qa = p.query_analysis
            if not qa:
                continue
            if qa.query_type == "calculated":
                parts.append("> 🧮 **Calculated table** (DAX)")
            elif qa.query_type == "entity":
                parts.append("> ⚡ **DirectLake Entity**")
            elif qa.connector:
                conn = qa.connector
                server = conn.positional_params[0] if conn.positional_params else "?"
                db_part = f" → {conn.positional_params[1]}" if len(conn.positional_params) > 1 else ""
                param_note = " *(parameterized)*" if conn.is_parameterized else ""

                mode_icon = _MODE_ICON.get(p.mode, "")
                f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
                f_label = _FOLDING_LABEL.get(qa.query_folding_status, qa.query_folding_status)
                incr_note = " · 🔄 Incremental Refresh" if qa.incremental_refresh.is_incremental else ""
                native_note = " · Native SQL" if qa.query_type == "native_sql" else ""

                parts.append(
                    f"> {mode_icon} **{conn.source_type}** ({server}{db_part}){param_note}"
                    f"{incr_note}{native_note} · "
                    f"Query Folding: {f_icon} {f_label}"
                )
        return "\n".join(parts)

    def _collapsible_columns(self, visible: list, hidden: list) -> str:
        hidden_note = f", {len(hidden)} hidden" if hidden else ""
        summary = f"### Columns ({len(visible)} visible{hidden_note} — click to expand)"

        rows = [
            "| Column | Type | Description | Format | Hidden |",
            "|---|---|---|---|---|",
        ]
        for col in visible:
            fmt = f"`{col.format_string}`" if col.format_string else ""
            rows.append(f"| `{col.name}` | {col.data_type} | {col.description} | {fmt} | |")
        for col in hidden:
            fmt = f"`{col.format_string}`" if col.format_string else ""
            rows.append(f"| `{col.name}` | {col.data_type} | {col.description} | {fmt} | ✗ |")

        table_md = "\n".join(rows)
        return (
            f"<details>\n"
            f"<summary>{summary}</summary>\n\n"
            f"{table_md}\n\n"
            f"</details>"
        )

    def _collapsible_m_expression(self, partition: Partition) -> str:
        """Collapsible section with step table + optional native SQL + full M expression."""
        qa = partition.query_analysis
        step_count = qa.step_count if qa else 0
        summary = f"🔌 Power Query — {step_count} step{'s' if step_count != 1 else ''}"

        content: list[str] = []

        # Step table
        if qa and qa.steps:
            content.append("| # | Step | Type | Foldable |")
            content.append("|---|------|------|----------|")
            for i, step in enumerate(qa.steps, 1):
                fold_icon = {True: "✅", False: "❌", None: "❓"}.get(step.folding_impact, "❓")
                content.append(
                    f"| {i} | `{step.name}` | {step.transform_type} | {fold_icon} |"
                )
            content.append("")

        # Folding reason
        if qa and qa.query_folding_reason:
            f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
            content.append(
                f"**Query Folding:** {f_icon} {qa.query_folding_reason}"
            )
            content.append("")

        # Native SQL
        if qa and qa.native_query:
            content.append("**Native Query:**")
            content.append("")
            content.append("```sql")
            content.append(qa.native_query)
            content.append("```")
            content.append("")

        # Incremental refresh
        if qa and qa.incremental_refresh.is_incremental:
            ir = qa.incremental_refresh
            col_info = f" on `{ir.range_column}`" if ir.range_column else ""
            content.append(f"🔄 **Incremental Refresh** detected{col_info}")
            content.append("")

        # Full M expression
        content.append("**Full M Expression:**")
        content.append("")
        content.append("```m")
        content.append(partition.expression)
        content.append("```")

        inner = "\n".join(content)
        return (
            f"<details>\n"
            f"<summary>{summary}</summary>\n\n"
            f"{inner}\n\n"
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
            f"*Generated by [pbi-semantic-doc](https://github.com/ViciusLio/pbi-semantic-doc) · {ts}*"
        )
