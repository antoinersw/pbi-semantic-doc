"""
JSON serialization for semantic models — depth comparable to MarkdownGenerator output.

Produces a nested dict suitable for json.dumps(...): overview metrics, data-source
connectivity, relationships, RLS, per-table columns/measures/partitions with M analysis,
measure lineage, unused columns, and hidden objects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .lineage import MeasureLineage, ModelLineage
from .parser import (
    Column,
    ConnectorCall,
    DataSourceSummary,
    Measure,
    MQueryAnalysis,
    MStep,
    Partition,
    Relationship,
    Role,
    RoleTablePermission,
    SemanticModel,
    Table,
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connector_to_dict(conn: ConnectorCall) -> dict[str, Any]:
    return {
        "function_name": conn.function_name,
        "source_type": conn.source_type,
        "positional_params": list(conn.positional_params),
        "named_params": dict(conn.named_params),
        "is_parameterized": conn.is_parameterized,
    }


def _m_step_to_dict(step: MStep) -> dict[str, Any]:
    return {
        "name": step.name,
        "transform_type": step.transform_type,
        "folding_impact": step.folding_impact,
        "expression": step.expression,
    }


def _m_query_analysis_to_dict(qa: MQueryAnalysis) -> dict[str, Any]:
    ir = qa.incremental_refresh
    return {
        "query_type": qa.query_type,
        "connector": _connector_to_dict(qa.connector) if qa.connector else None,
        "step_count": qa.step_count,
        "steps": [_m_step_to_dict(s) for s in qa.steps],
        "native_query": qa.native_query,
        "query_folding_status": qa.query_folding_status,
        "query_folding_reason": qa.query_folding_reason,
        "has_merges": qa.has_merges,
        "has_appends": qa.has_appends,
        "has_custom_transforms": qa.has_custom_transforms,
        "incremental_refresh": {
            "is_incremental": ir.is_incremental,
            "range_column": ir.range_column,
            "has_range_start": ir.has_range_start,
            "has_range_end": ir.has_range_end,
        },
        "unrecognized_functions": list(qa.unrecognized_functions),
        "complexity_score": qa.complexity_score(),
    }


def _partition_to_dict(partition: Partition) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": partition.name,
        "mode": partition.mode,
        "type": partition.type,
        "expression": partition.expression,
        "query_analysis": (
            _m_query_analysis_to_dict(partition.query_analysis)
            if partition.query_analysis
            else None
        ),
    }
    return out


def _column_to_dict(col: Column) -> dict[str, Any]:
    return {
        "name": col.name,
        "data_type": col.data_type,
        "description": col.description,
        "is_hidden": col.is_hidden,
        "format_string": col.format_string,
        "display_folder": col.display_folder,
    }


def _measure_to_dict(measure: Measure) -> dict[str, Any]:
    return {
        "name": measure.name,
        "expression": measure.expression,
        "description": measure.description,
        "format_string": measure.format_string,
        "display_folder": measure.display_folder,
        "is_hidden": measure.is_hidden,
        "complexity_score": measure.complexity_score(),
        "auto_description": measure.auto_description(),
    }


def _measure_lineage_to_dict(lin: MeasureLineage) -> dict[str, Any]:
    return {
        "measure_name": lin.measure_name,
        "home_table": lin.home_table,
        "aggregated_tables": sorted(lin.aggregated_tables),
        "referenced_tables": sorted(lin.referenced_tables),
        "all_base_tables": sorted(lin.all_base_tables),
        "compatible_tables": sorted(lin.compatible_tables),
        "incompatible_tables": sorted(lin.incompatible_tables),
        "filter_removed_tables": sorted(lin.filter_removed_tables),
        "direct_measure_deps": list(lin.direct_measure_deps),
        "all_measure_deps": list(lin.all_measure_deps),
        "referenced_columns": [
            {"table": t, "column": c} for t, c in sorted(lin.referenced_columns)
        ],
        "uses_time_intelligence": lin.uses_time_intelligence,
        "uses_inactive_relationship": lin.uses_inactive_relationship,
        "uses_treatas": lin.uses_treatas,
        "has_cycle": lin.has_cycle,
        "has_lineage_info": lin.has_lineage_info,
    }


def _relationship_to_dict(r: Relationship) -> dict[str, Any]:
    return {
        "from_table": r.from_table,
        "from_column": r.from_column,
        "to_table": r.to_table,
        "to_column": r.to_column,
        "cardinality": r.cardinality,
        "cross_filter": r.cross_filter,
        "is_active": r.is_active,
    }


def _role_table_perm_to_dict(tp: RoleTablePermission) -> dict[str, Any]:
    return {
        "table_name": tp.table_name,
        "filter_expression": tp.filter_expression,
        "is_open": tp.filter_expression.strip().lower() == "true",
    }


def _role_to_dict(role: Role) -> dict[str, Any]:
    return {
        "name": role.name,
        "model_permission": role.model_permission,
        "table_permissions": [_role_table_perm_to_dict(tp) for tp in role.table_permissions],
    }


def _data_source_summary_to_dict(ds: DataSourceSummary) -> dict[str, Any]:
    return {
        "source_type": ds.source_type,
        "server": ds.server,
        "database": ds.database,
        "tables": list(ds.tables),
        "modes": list(ds.modes),
    }


def _partition_connectivity_rows(model: SemanticModel) -> list[dict[str, Any]]:
    """Mirror MarkdownGenerator._data_sources_section row semantics."""
    rows: list[dict[str, Any]] = []

    for table in model.tables:
        for partition in table.partitions:
            qa = partition.query_analysis
            if not qa:
                continue

            if qa.query_type == "calculated":
                rows.append(
                    {
                        "table": table.name,
                        "connector": None,
                        "server": None,
                        "database": None,
                        "mode_label": "Calculated (DAX)",
                        "steps": None,
                        "query_folding_status": None,
                        "incremental_refresh": False,
                        "notes": "calculated_table",
                    }
                )
                continue
            if qa.query_type == "entity":
                rows.append(
                    {
                        "table": table.name,
                        "connector": None,
                        "server": None,
                        "database": None,
                        "mode_label": "DirectLake Entity",
                        "steps": None,
                        "query_folding_status": None,
                        "incremental_refresh": False,
                        "notes": "directlake_entity",
                    }
                )
                continue
            if not qa.connector:
                continue

            conn = qa.connector
            server = conn.positional_params[0] if conn.positional_params else None
            database = conn.positional_params[1] if len(conn.positional_params) > 1 else None
            if conn.is_parameterized and server is not None:
                server = f"{server} *(param)*"

            rows.append(
                {
                    "table": table.name,
                    "partition": partition.name,
                    "connector": conn.source_type,
                    "server": server,
                    "database": database,
                    "mode": partition.mode,
                    "steps": qa.step_count if qa.step_count > 0 else None,
                    "query_folding_status": qa.query_folding_status,
                    "query_folding_reason": qa.query_folding_reason or None,
                    "native_sql": bool(qa.native_query),
                    "incremental_refresh": qa.incremental_refresh.is_incremental,
                }
            )

    return rows


def _table_documentation_dict(table: Table) -> dict[str, Any]:
    cols_sorted = sorted(table.columns, key=lambda c: c.name.lower())
    return {
        "name": table.name,
        "description": table.description,
        "is_hidden": table.is_hidden,
        "effective_mode": table.effective_mode,
        "is_incremental": table.is_incremental,
        "columns": [_column_to_dict(c) for c in cols_sorted],
        "measures": [_measure_to_dict(m) for m in sorted(table.measures, key=lambda x: x.name.lower())],
        "partitions": [_partition_to_dict(p) for p in table.partitions],
    }


def build_semantic_model_payload(model: SemanticModel) -> dict[str, Any]:
    """
    Build the full semantic-model structure shared by standalone and combined JSON output.
    """
    lineage_map: dict[tuple[str, str], MeasureLineage] = {}
    model_lineage: Optional[ModelLineage] = None
    try:
        model_lineage = ModelLineage(model)
        lineage_map = model_lineage.resolve_all()
    except Exception:
        lineage_map = {}
        model_lineage = None

    metrics = model.calculate_metrics()
    visible_tables = sorted(model.visible_tables, key=lambda t: t.name.lower())

    measures_index: list[dict[str, Any]] = []
    for table_name, measure in model.all_measures:
        entry: dict[str, Any] = {
            "table": table_name,
            "measure": _measure_to_dict(measure),
        }
        lin = lineage_map.get((table_name, measure.name))
        if lin and lin.has_lineage_info:
            entry["lineage"] = _measure_lineage_to_dict(lin)
        measures_index.append(entry)

    unused_columns: list[dict[str, str]] = []
    if model_lineage is not None:
        try:
            raw_unused = model_lineage.unused_columns(lineage_map)
            col_type: dict[tuple[str, str], str] = {}
            for t in model.tables:
                for c in t.columns:
                    col_type[(t.name, c.name)] = c.data_type
            for tbl, col in raw_unused:
                unused_columns.append(
                    {
                        "table": tbl,
                        "column": col,
                        "data_type": col_type.get((tbl, col), ""),
                    }
                )
        except Exception:
            unused_columns = []

    hidden_tables = sorted([t.name for t in model.tables if t.is_hidden])
    hidden_columns: list[dict[str, str]] = []
    for t in model.tables:
        for c in t.columns:
            if c.is_hidden:
                hidden_columns.append(
                    {"table": t.name, "column": c.name, "data_type": c.data_type}
                )
    hidden_columns.sort(key=lambda x: (x["table"].lower(), x["column"].lower()))

    # Enrich per-table measures with lineage (same info as measures_index, convenient for consumers)
    tables_out: list[dict[str, Any]] = []
    for table in visible_tables:
        tdict = _table_documentation_dict(table)
        for md in tdict["measures"]:
            mname = md["name"]
            lin = lineage_map.get((table.name, mname))
            if lin and lin.has_lineage_info:
                md["lineage"] = _measure_lineage_to_dict(lin)
        tables_out.append(tdict)

    payload: dict[str, Any] = {
        "name": model.name,
        "overview": metrics.to_dict(),
        "aggregated_data_sources": [
            _data_source_summary_to_dict(ds) for ds in model.data_sources
        ],
        "partition_connectivity": _partition_connectivity_rows(model),
        "relationships": [_relationship_to_dict(r) for r in model.relationships],
        "roles": [_role_to_dict(role) for role in model.roles],
        "tables": tables_out,
        "measures_index": measures_index,
        "unused_columns": unused_columns,
        "hidden_objects": {
            "tables": hidden_tables,
            "columns": hidden_columns,
        },
    }
    return payload


def semantic_model_document(model: SemanticModel) -> dict[str, Any]:
    """Top-level document wrapper for standalone semantic-model JSON."""
    return {
        "document_type": "semantic_model",
        "generated_at": _iso_now(),
        "generator": "pbi-semantic-doc",
        "semantic_model": build_semantic_model_payload(model),
    }


def combined_project_document(
    project_name: str,
    model: SemanticModel | None,
    report_metrics_dict: dict | None,
) -> dict[str, Any]:
    """Unified JSON for --combined mode."""
    doc: dict[str, Any] = {
        "document_type": "combined",
        "generated_at": _iso_now(),
        "generator": "pbi-semantic-doc",
        "project_name": project_name,
    }
    if model:
        doc["semantic_model"] = build_semantic_model_payload(model)
    if report_metrics_dict is not None:
        doc["report"] = report_metrics_dict
    return doc
