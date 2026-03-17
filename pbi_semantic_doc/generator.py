"""
Markdown generator — takes a SemanticModel object and produces
a well-structured, navigable Markdown document.

Features:
- Table of Contents with anchor links to every section
- Collapsible table, relationship and measures sections (<details>/<summary>)
- Renders natively on GitHub and GitLab
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from .parser import (
    SemanticModel, ModelMetrics, Table, Measure, Relationship,
    Partition, Role, MQueryAnalysis,
)
from .lineage import ModelLineage, MeasureLineage

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
    Generates a single navigable Markdown file documenting a SemanticModel.

    Usage:
        gen = MarkdownGenerator()
        output = gen.generate(model)
        Path(f"DOC_{model.name}.md").write_text(output)
    """

    def generate(self, model: SemanticModel) -> str:
        # Build lineage map (defensive — never let it crash the generator)
        try:
            self._lineage_map: dict = ModelLineage(model).resolve_all()
        except Exception:
            self._lineage_map = {}

        sections: list[str] = []

        sections.append(self._header(model))
        sections.append(self._toc(model))
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
    # Table of Contents
    # ------------------------------------------------------------------

    def _toc(self, model: SemanticModel) -> str:
        lines = ["## Contents", ""]

        lines.append("- [Overview](#overview)")

        ds = model.data_sources
        if ds:
            n = len(ds)
            lines.append(
                f"- [Data Sources](#data-sources)"
                f" — {n} connector{'s' if n != 1 else ''}"
            )

        if model.relationships:
            n = len(model.relationships)
            lines.append(
                f"- [Relationships](#relationships)"
                f" — {n} relationship{'s' if n != 1 else ''}"
            )

        if model.roles:
            n = len(model.roles)
            lines.append(
                f"- [Row Level Security](#row-level-security)"
                f" — {n} role{'s' if n != 1 else ''}"
            )

        if model.visible_tables:
            lines.append("- **Tables**")
            for table in model.visible_tables:
                anchor = self._heading_anchor(f"Table: `{table.name}`")
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
                detail = " · ".join(parts)
                lines.append(f"  - [{table.name}](#{anchor}) — {detail}")

        if model.all_measures:
            n = len(model.all_measures)
            lines.append(
                f"- [Measures Index](#measures-index-az)"
                f" — {n} measure{'s' if n != 1 else ''}"
            )

        return "\n".join(lines)

    @staticmethod
    def _heading_anchor(heading: str) -> str:
        """Convert a heading string to a GitHub-style anchor id."""
        # Strip markdown formatting (backticks, asterisks, etc.)
        text = re.sub(r"[`*_~]", "", heading)
        # Lowercase
        text = text.lower()
        # Remove anything that is not a letter, number, space, or hyphen
        text = re.sub(r"[^\w\s-]", "", text)
        # Collapse whitespace → hyphens
        text = re.sub(r"\s+", "-", text.strip())
        # Collapse multiple hyphens
        text = re.sub(r"-+", "-", text)
        return text

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

        cx = metrics.complexity_index
        cx_icon = "🟢" if cx < 0.25 else ("🟡" if cx < 0.60 else "🔴")
        lines.append(f"| **Complexity Index** | **{cx_icon} {cx:.0%}** |")

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
        n = len(relationships)
        summary = f"🔗 {n} relationship{'s' if n != 1 else ''} — click to expand"

        rows = [
            "| From | | To | Cardinality | Cross-filter | Active |",
            "|---|---|---|---|---|---|",
        ]
        for r in relationships:
            active_icon = "✅" if r.is_active else "⬜"
            from_ref = f"`{r.from_table}`[{r.from_column}]"
            to_ref   = f"`{r.to_table}`[{r.to_column}]"
            rows.append(
                f"| {from_ref} | → | {to_ref} | {r.cardinality} | {r.cross_filter} | {active_icon} |"
            )

        inner = "\n".join(rows)
        return (
            "## Relationships\n\n"
            f"<details>\n"
            f"<summary>{summary}</summary>\n\n"
            f"{inner}\n\n"
            f"</details>"
        )

    def _rls_section(self, model: SemanticModel) -> str:
        """Row Level Security section — always visible (security-critical)."""
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
        heading = f"## Table: `{table.name}`"

        # Build summary line for the <details> toggle
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

        # Add folding status if we have partitions
        for p in table.partitions:
            qa = p.query_analysis
            if qa and qa.connector:
                f_icon = _FOLDING_ICON.get(qa.query_folding_status, "❓")
                f_label = _FOLDING_LABEL.get(qa.query_folding_status, qa.query_folding_status)
                summary_parts.append(f"Folding: {f_icon} {f_label}")
                break

        summary = " · ".join(summary_parts) + " — click to expand"

        # Build inner content
        content: list[str] = []

        if table.description:
            content += ["", table.description]

        # Partition / source info badge
        badge = self._partition_badge(table)
        if badge:
            content += ["", badge]

        # Columns — collapsible (nested inside the table details)
        if table.columns:
            visible_cols = [c for c in table.columns if not c.is_hidden]
            hidden_cols  = [c for c in table.columns if c.is_hidden]
            if visible_cols:
                content += [""]
                content.append(self._collapsible_columns(visible_cols, hidden_cols))

        # Measures
        if table.measures:
            content += ["", "### Measures", ""]
            for measure in sorted(table.measures, key=lambda m: m.name.lower()):
                content.append(self._measure_block(measure, table.name))

        # M expression — collapsible per partition
        for partition in table.partitions:
            if partition.expression and partition.type == "m":
                content += [""]
                content.append(self._collapsible_m_expression(partition))

        if not content:
            return heading

        inner = "\n".join(content).strip()
        details = (
            f"<details>\n"
            f"<summary>{summary}</summary>\n\n"
            f"{inner}\n\n"
            f"</details>"
        )
        return f"{heading}\n\n{details}"

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

    def _measure_block(self, measure: Measure, table_name: str = "",
                       show_table: bool = False) -> str:
        lines: list[str] = []
        hidden_tag = " *(hidden)*" if measure.is_hidden else ""
        folder_tag = f" · 📁 `{measure.display_folder}`" if measure.display_folder else ""
        table_tag  = f" · 📋 `{table_name}`" if show_table and table_name else ""

        lines.append(f"#### `{measure.name}`{hidden_tag}{folder_tag}{table_tag}")

        if measure.description:
            lines += ["", measure.description]

        auto_desc = measure.auto_description()
        if auto_desc and not measure.description:
            lines += ["", f"*{auto_desc}*"]

        if measure.format_string:
            lines += ["", f"**Format:** `{measure.format_string}`"]

        if measure.expression:
            lines += ["", "```dax", measure.expression, "```"]

        # Lineage (only available after generate() has been called)
        if table_name and hasattr(self, "_lineage_map"):
            lin = self._lineage_map.get((table_name, measure.name))
            if lin and lin.has_lineage_info:
                lines += ["", self._measure_lineage_md(lin)]

        return "\n".join(lines)

    def _measure_lineage_md(self, lin: MeasureLineage) -> str:
        """Render a collapsible lineage block in Markdown."""
        parts: list[str] = []

        if lin.all_base_tables:
            tables = ", ".join(f"`{t}`" for t in sorted(lin.all_base_tables))
            parts.append(f"📊 **Aggregates:** {tables}")

        if lin.all_measure_deps:
            deps = ", ".join(f"`[{m}]`" for m in lin.all_measure_deps)
            parts.append(f"🔗 **Depends on:** {deps}")

        if lin.filter_removed_tables:
            tables = ", ".join(f"`{t}`" for t in sorted(lin.filter_removed_tables))
            parts.append(f"⚠️ **Filter removed (ALL/ALLEXCEPT):** {tables}")

        if lin.compatible_tables:
            tables = ", ".join(f"`{t}`" for t in sorted(lin.compatible_tables))
            parts.append(f"✅ **Compatible slicers:** {tables}")

        if lin.incompatible_tables:
            tables = ", ".join(f"`{t}`" for t in sorted(lin.incompatible_tables))
            parts.append(f"❌ **Non-correlated:** {tables}")

        flags: list[str] = []
        if lin.uses_time_intelligence:
            flags.append("⏱️ Time intelligence")
        if lin.uses_inactive_relationship:
            flags.append("🔀 Inactive relationship")
        if lin.has_cycle:
            flags.append("⚠️ Circular dependency")
        if flags:
            parts.append(f"🏷️ **Flags:** {', '.join(flags)}")

        if not parts:
            return ""

        inner = "\n\n".join(parts)
        return (
            f"<details>\n"
            f"<summary>🔗 Lineage — click to expand</summary>\n\n"
            f"{inner}\n\n"
            f"</details>"
        )

    def _measures_index(self, model: SemanticModel) -> str:
        n = len(model.all_measures)

        blocks: list[str] = []
        for table_name, measure in model.all_measures:
            blocks.append(self._measure_block(measure, table_name, show_table=True))

        inner = "\n\n---\n\n".join(blocks)
        return (
            "## Measures Index (A–Z)\n\n"
            f"<details>\n"
            f"<summary>📋 {n} measure{'s' if n != 1 else ''} — click to expand</summary>\n\n"
            f"{inner}\n\n"
            f"</details>"
        )

    def _footer(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return (
            "---\n\n"
            f"*Generated by [pbi-semantic-doc](https://github.com/ViciusLio/pbi-semantic-doc) · {ts}*"
        )
