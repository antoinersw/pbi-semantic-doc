"""
Measure Lineage — Layer 2+3 (stateful, model-aware).

Given a complete SemanticModel, ModelLineage:
  1. Builds an undirected relationship graph (table ↔ table)
  2. Resolves each measure's DAX references (via dax_analyzer.py)
  3. Follows nested [MeasureName] references transitively (BFS, cycle-safe)
  4. Computes which tables are compatible (reachable via relationships)
     and which are incompatible (no relationship path) — the governance signal.

Usage:
    from pbi_semantic_doc.lineage import ModelLineage

    ml = ModelLineage(model)
    lineages = ml.resolve_all()           # dict[(table, measure) → MeasureLineage]

    # or for a single measure:
    lin = ml.resolve("Sales", some_measure)
    print(lin.compatible_tables)          # {'DimCliente', 'Calendar', ...}
    print(lin.incompatible_tables)        # {'HR_Employees', 'Budget'}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parser import Measure, SemanticModel

from .dax_analyzer import extract_dax_refs

# Auto-generated Power BI tables — excluded from lineage output
_SYSTEM_TABLE_PREFIXES = ("LocalDateTable_", "DateTableTemplate_")


def _is_system_table(name: str) -> bool:
    return any(name.startswith(p) for p in _SYSTEM_TABLE_PREFIXES)


# ── MeasureLineage dataclass ──────────────────────────────────────────────────

@dataclass
class MeasureLineage:
    """Full resolved lineage for a single measure."""

    measure_name: str
    home_table: str

    # Tables directly aggregated in this measure's own expression
    # e.g. SUM(Sales[Amount]) → "Sales"
    aggregated_tables: set[str] = field(default_factory=set)

    # All Table[Column] tables referenced anywhere in this expression
    referenced_tables: set[str] = field(default_factory=set)

    # Union of aggregated_tables + contributions from all nested measures
    # This is the "grain anchor" — what the measure is ultimately built on
    all_base_tables: set[str] = field(default_factory=set)

    # Model tables reachable via the relationship graph from all_base_tables,
    # excluding the base tables themselves.
    # These are the dimensions you CAN use as slicers for this measure.
    compatible_tables: set[str] = field(default_factory=set)

    # Model tables with NO relationship path to any base table.
    # Using these as slicers has no effect (or gives wrong results).
    incompatible_tables: set[str] = field(default_factory=set)

    # Tables explicitly cleared with ALL() / ALLEXCEPT() / ALLSELECTED()
    # (may overlap with compatible_tables — the filter IS there but gets removed)
    filter_removed_tables: set[str] = field(default_factory=set)

    # Direct [MeasureName] references in this expression only
    direct_measure_deps: list[str] = field(default_factory=list)

    # Full transitive dependency chain (BFS order, deduplicated)
    all_measure_deps: list[str] = field(default_factory=list)

    # Flags
    uses_time_intelligence: bool = False
    uses_inactive_relationship: bool = False
    uses_treatas: bool = False
    has_cycle: bool = False   # circular measure dependency detected

    @property
    def has_lineage_info(self) -> bool:
        """True if there is any meaningful lineage to display."""
        return bool(
            self.all_base_tables
            or self.compatible_tables
            or self.incompatible_tables
            or self.filter_removed_tables
            or self.all_measure_deps
            or self.uses_time_intelligence
            or self.uses_inactive_relationship
        )


# ── ModelLineage ──────────────────────────────────────────────────────────────

class ModelLineage:
    """
    Resolves the lineage for every measure in a SemanticModel.

    Builds an undirected relationship graph once at construction time, then
    uses BFS to compute table reachability for each measure.
    """

    def __init__(self, model: "SemanticModel") -> None:
        self._model = model

        # Undirected graph: table_name → set[connected_table_names]
        self._rel_graph: dict[str, set[str]] = self._build_rel_graph()

        # Measure index: measure_name → (home_table_name, Measure)
        # If the same name appears in multiple tables, last writer wins
        # (duplicates are rare and not critical for lineage display)
        self._measure_index: dict[str, tuple[str, "Measure"]] = (
            self._build_measure_index()
        )

        # Visible (non-system) table names
        self._all_table_names: set[str] = {
            t.name
            for t in model.tables
            if not _is_system_table(t.name)
        }

    # ── public API ────────────────────────────────────────────────────────────

    def resolve_all(self) -> dict[tuple[str, str], MeasureLineage]:
        """
        Resolve and return the lineage for every measure in the model.

        Returns a dict keyed by (table_name, measure_name).
        Never raises — individual failures produce a minimal lineage entry.
        """
        result: dict[tuple[str, str], MeasureLineage] = {}
        for table in self._model.tables:
            if _is_system_table(table.name):
                continue
            for measure in table.measures:
                try:
                    result[(table.name, measure.name)] = self.resolve(
                        table.name, measure
                    )
                except Exception:
                    # Defensive: never let lineage crash the doc generator
                    result[(table.name, measure.name)] = MeasureLineage(
                        measure_name=measure.name,
                        home_table=table.name,
                    )
        return result

    def resolve(
        self,
        home_table: str,
        measure: "Measure",
        _visiting: frozenset = frozenset(),
    ) -> MeasureLineage:
        """
        Resolve the full lineage for a single measure.

        _visiting is used internally to detect and break circular
        measure-to-measure dependencies.
        """
        key = (home_table, measure.name)

        # Cycle guard
        if key in _visiting:
            return MeasureLineage(
                measure_name=measure.name,
                home_table=home_table,
                has_cycle=True,
            )

        visiting = _visiting | {key}
        refs = extract_dax_refs(measure.expression)

        # Seed: tables directly referenced in this expression
        referenced_tables: set[str] = set(refs.aggregated_tables)
        referenced_tables.update(t for t, _ in refs.table_column_refs)

        # Base tables start from direct aggregations
        all_base_tables: set[str] = set(refs.aggregated_tables)

        # ── BFS over nested measures ──────────────────────────────────────────
        all_measure_deps: list[str] = []
        visited_measures: set[str] = set()
        queue: list[str] = list(refs.nested_measure_names)
        _has_cycle: bool = False

        while queue:
            dep_name = queue.pop(0)
            if dep_name in visited_measures:
                continue
            visited_measures.add(dep_name)
            all_measure_deps.append(dep_name)

            if dep_name in self._measure_index:
                dep_home, dep_measure = self._measure_index[dep_name]
                dep_lineage = self.resolve(dep_home, dep_measure, visiting)
                if dep_lineage.has_cycle:
                    _has_cycle = True
                all_base_tables |= dep_lineage.all_base_tables
                referenced_tables |= dep_lineage.referenced_tables
                for further_dep in dep_lineage.direct_measure_deps:
                    if further_dep not in visited_measures:
                        queue.append(further_dep)

        # ── Fallbacks when no aggregation found ───────────────────────────────
        # Some measures are pure expressions (DIVIDE, IF, VAR/RETURN) with no
        # direct aggregation call.  Use all referenced tables as the base.
        if not all_base_tables:
            all_base_tables = set(referenced_tables)

        # Last resort: anchor to the measure's home table
        if not all_base_tables:
            all_base_tables = {home_table}

        # ── Relationship graph traversal ──────────────────────────────────────
        reachable = self._reachable_from(all_base_tables)

        # Compatible = reachable tables that are NOT base tables themselves,
        # filtered to visible (non-system) model tables
        compatible = (reachable - all_base_tables) & self._all_table_names

        # Incompatible = visible model tables with no path to any base table
        incompatible = self._all_table_names - reachable

        # ALL-removed: only include tables that actually exist in the model
        filter_removed = refs.all_removed_tables & self._all_table_names

        return MeasureLineage(
            measure_name=measure.name,
            home_table=home_table,
            aggregated_tables=refs.aggregated_tables & self._all_table_names,
            referenced_tables=referenced_tables & self._all_table_names,
            all_base_tables=all_base_tables & self._all_table_names,
            compatible_tables=compatible,
            incompatible_tables=incompatible,
            filter_removed_tables=filter_removed,
            direct_measure_deps=list(refs.nested_measure_names),
            all_measure_deps=all_measure_deps,
            uses_time_intelligence=refs.uses_time_intelligence,
            uses_inactive_relationship=refs.uses_inactive_relationship,
            uses_treatas=refs.uses_treatas,
            has_cycle=_has_cycle,
        )

    # ── private helpers ───────────────────────────────────────────────────────

    def _build_rel_graph(self) -> dict[str, set[str]]:
        """Build undirected table-connectivity graph from model relationships."""
        graph: dict[str, set[str]] = {}
        for rel in self._model.relationships:
            graph.setdefault(rel.from_table, set()).add(rel.to_table)
            graph.setdefault(rel.to_table, set()).add(rel.from_table)
        return graph

    def _build_measure_index(self) -> dict[str, tuple[str, "Measure"]]:
        """Map measure_name → (home_table_name, Measure) for transitive lookup."""
        index: dict[str, tuple[str, "Measure"]] = {}
        for table in self._model.tables:
            for measure in table.measures:
                index[measure.name] = (table.name, measure)
        return index

    def _reachable_from(self, start_tables: set[str]) -> set[str]:
        """BFS: return all tables reachable from start_tables via relationships."""
        visited: set[str] = set(start_tables)
        queue: list[str] = [t for t in start_tables if t in self._rel_graph]
        while queue:
            current = queue.pop(0)
            for neighbor in self._rel_graph.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return visited
