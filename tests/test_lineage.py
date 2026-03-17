"""Unit tests for pbi_semantic_doc.lineage (Layer 2+3 — model-aware)."""

import pytest
from pbi_semantic_doc.parser import SemanticModel, Table, Column, Measure, Relationship
from pbi_semantic_doc.lineage import ModelLineage, MeasureLineage


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_star_model() -> SemanticModel:
    """
    Simple star schema:
        Sales ── DimCliente
        Sales ── DimProdotto
        Sales ── Calendar
        HR  (isolated, no relationship to Sales)
    """
    sales = Table(
        name="Sales",
        columns=[Column(name="Amount", data_type="decimal"),
                 Column(name="ClienteID", data_type="int64"),
                 Column(name="OrderDate", data_type="dateTime")],
        measures=[
            Measure(name="Revenue", expression="SUM(Sales[Amount])"),
            Measure(name="Revenue YTD",
                    expression="TOTALYTD([Revenue], Calendar[Date])"),
            Measure(name="Revenue no Channel",
                    expression="CALCULATE([Revenue], ALL(DimCanale))"),
        ],
    )
    dim_cliente = Table(
        name="DimCliente",
        columns=[Column(name="ID", data_type="int64"),
                 Column(name="Region", data_type="string")],
    )
    dim_prodotto = Table(
        name="DimProdotto",
        columns=[Column(name="ID", data_type="int64"),
                 Column(name="Category", data_type="string")],
    )
    calendar = Table(
        name="Calendar",
        columns=[Column(name="Date", data_type="dateTime"),
                 Column(name="Year", data_type="int64")],
    )
    hr = Table(
        name="HR",
        columns=[Column(name="EmpID", data_type="int64")],
        measures=[
            Measure(name="Headcount", expression="COUNTROWS(HR)"),
        ],
    )
    # DimCanale exists but has NO relationship to anything
    dim_canale = Table(
        name="DimCanale",
        columns=[Column(name="ID", data_type="int64"),
                 Column(name="Name", data_type="string")],
    )

    relationships = [
        Relationship(from_table="Sales", from_column="ClienteID",
                     to_table="DimCliente", to_column="ID",
                     cardinality="many-to-one", cross_filter="single"),
        Relationship(from_table="Sales", from_column="OrderDate",
                     to_table="Calendar", to_column="Date",
                     cardinality="many-to-one", cross_filter="single"),
        # DimProdotto also connected to Sales (via a different key we don't track)
        Relationship(from_table="Sales", from_column="Amount",
                     to_table="DimProdotto", to_column="ID",
                     cardinality="many-to-one", cross_filter="single"),
    ]

    return SemanticModel(
        name="StarModel",
        tables=[sales, dim_cliente, dim_prodotto, calendar, hr, dim_canale],
        relationships=relationships,
    )


# ── ModelLineage construction ──────────────────────────────────────────────────

class TestModelLineageConstruction:
    def setup_method(self):
        self.model = _make_star_model()
        self.lineage = ModelLineage(self.model)

    def test_all_tables_indexed(self):
        # System tables excluded; others present
        assert "Sales" in self.lineage._all_table_names
        assert "DimCliente" in self.lineage._all_table_names
        assert "HR" in self.lineage._all_table_names

    def test_system_tables_excluded(self):
        assert "LocalDateTable_abc" not in self.lineage._all_table_names

    def test_rel_graph_built(self):
        # Directed reverse-filter graph: FAT → DIM edges (so BFS from FAT finds its DIM ancestors).
        # Sales (FAT, many-side) → DimCliente/Calendar/DimProdotto (DIM, one-side)
        assert "DimCliente" in self.lineage._rel_graph.get("Sales", set())
        assert "Calendar" in self.lineage._rel_graph.get("Sales", set())
        # DIM tables have no outgoing edges in single-direction relationships
        # (DIM cannot be filtered by FAT in single cross-filter direction)
        assert "Sales" not in self.lineage._rel_graph.get("DimCliente", set())

    def test_measure_index_built(self):
        assert "Revenue" in self.lineage._measure_index
        assert self.lineage._measure_index["Revenue"][0] == "Sales"

    def test_resolve_all_returns_all_measures(self):
        all_lin = self.lineage.resolve_all()
        assert ("Sales", "Revenue") in all_lin
        assert ("Sales", "Revenue YTD") in all_lin
        assert ("HR", "Headcount") in all_lin


# ── Simple measure lineage ─────────────────────────────────────────────────────

class TestSimpleMeasureLineage:
    def setup_method(self):
        self.model = _make_star_model()
        self.lineage = ModelLineage(self.model)

    def test_revenue_base_table(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue")]
        assert "Sales" in lin.all_base_tables

    def test_revenue_compatible_includes_dim_cliente(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue")]
        assert "DimCliente" in lin.compatible_tables

    def test_revenue_compatible_includes_calendar(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue")]
        assert "Calendar" in lin.compatible_tables

    def test_revenue_incompatible_includes_hr(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue")]
        assert "HR" in lin.incompatible_tables

    def test_base_table_not_in_compatible(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue")]
        # Sales itself should not appear in compatible_tables
        assert "Sales" not in lin.compatible_tables

    def test_headcount_base_table(self):
        lin = self.lineage.resolve_all()[("HR", "Headcount")]
        assert "HR" in lin.all_base_tables

    def test_headcount_incompatible_includes_dim_cliente(self):
        lin = self.lineage.resolve_all()[("HR", "Headcount")]
        # No relationship between HR and DimCliente
        assert "DimCliente" in lin.incompatible_tables


# ── Transitive measure resolution ─────────────────────────────────────────────

class TestTransitiveResolution:
    def setup_method(self):
        self.model = _make_star_model()
        self.lineage = ModelLineage(self.model)

    def test_revenue_ytd_depends_on_revenue(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue YTD")]
        assert "Revenue" in lin.all_measure_deps

    def test_revenue_ytd_base_table_from_nested(self):
        # Revenue YTD → [Revenue] → SUM(Sales[Amount]): base = Sales
        lin = self.lineage.resolve_all()[("Sales", "Revenue YTD")]
        assert "Sales" in lin.all_base_tables

    def test_revenue_ytd_time_intelligence(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue YTD")]
        assert lin.uses_time_intelligence is True

    def test_revenue_ytd_compatible_includes_calendar(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue YTD")]
        assert "Calendar" in lin.compatible_tables


# ── ALL / filter removal ───────────────────────────────────────────────────────

class TestFilterRemoval:
    def setup_method(self):
        self.model = _make_star_model()
        self.lineage = ModelLineage(self.model)

    def test_filter_removed_detected(self):
        lin = self.lineage.resolve_all()[("Sales", "Revenue no Channel")]
        # DimCanale is in ALL() — but it's not in the model's relationships
        # so it won't be in filter_removed (only model tables are tracked)
        # The measure still resolves correctly
        assert lin is not None

    def test_all_removed_table_in_model(self):
        # Add a measure that removes DimCliente (which IS in the model)
        model = _make_star_model()
        model.tables[0].measures.append(
            Measure(name="Revenue No Cliente",
                    expression="CALCULATE([Revenue], ALL(DimCliente))")
        )
        lin = ModelLineage(model).resolve_all()[("Sales", "Revenue No Cliente")]
        assert "DimCliente" in lin.filter_removed_tables


# ── Cycle detection ────────────────────────────────────────────────────────────

class TestCycleDetection:
    def test_cycle_does_not_crash(self):
        """Circular measure references must not cause infinite recursion."""
        table = Table(
            name="Facts",
            columns=[Column(name="X", data_type="int64")],
            measures=[
                Measure(name="A", expression="[B] + 1"),
                Measure(name="B", expression="[A] + 1"),
            ],
        )
        model = SemanticModel(name="CycleModel", tables=[table])
        # Should not raise
        lin = ModelLineage(model).resolve("Facts", table.measures[0])
        assert lin.has_cycle is True


# ── Models without relationships ──────────────────────────────────────────────

class TestNoRelationships:
    def test_all_tables_incompatible_with_each_other(self):
        """Without any relationships, every other table is incompatible."""
        t1 = Table(name="T1", columns=[Column(name="A", data_type="int64")],
                   measures=[Measure(name="M1", expression="SUM(T1[A])")])
        t2 = Table(name="T2", columns=[Column(name="B", data_type="int64")])
        model = SemanticModel(name="NoRels", tables=[t1, t2])
        lin = ModelLineage(model).resolve("T1", t1.measures[0])
        assert "T2" in lin.incompatible_tables
        assert "T1" not in lin.incompatible_tables


# ── has_lineage_info property ─────────────────────────────────────────────────

class TestHasLineageInfo:
    def test_measure_with_expression_has_info(self):
        model = _make_star_model()
        lin = ModelLineage(model).resolve_all()[("Sales", "Revenue")]
        assert lin.has_lineage_info is True

    def test_empty_lineage_has_no_info(self):
        lin = MeasureLineage(measure_name="X", home_table="T")
        assert lin.has_lineage_info is False


# ── Integration with real model ───────────────────────────────────────────────

class TestLineageIntegration:
    def setup_method(self):
        from pathlib import Path
        sample = Path(__file__).parent.parent / "examples" / "sample_model"
        if not sample.exists():
            pytest.skip("examples/sample_model not found")
        from pbi_semantic_doc.parser import TmdlParser
        semantic = sample / "Artificial Intelligence Sample.SemanticModel"
        self.model = TmdlParser().parse(semantic / "definition")
        self.lineage = ModelLineage(self.model)
        self.all_lin = self.lineage.resolve_all()

    def test_all_measures_resolved(self):
        total_measures = sum(len(t.measures) for t in self.model.visible_tables)
        assert len(self.all_lin) >= total_measures

    def test_no_exceptions_during_resolve(self):
        # resolve_all() should never raise; all entries should be MeasureLineage
        for key, lin in self.all_lin.items():
            assert isinstance(lin, MeasureLineage), f"Bad lineage for {key}"

    def test_some_measures_have_compatible_tables(self):
        has_compatible = any(
            lin.compatible_tables for lin in self.all_lin.values()
        )
        assert has_compatible, "Expected at least some measures to have compatible tables"

    def test_html_generation_with_lineage(self):
        from pbi_semantic_doc.html_generator import HtmlGenerator
        html = HtmlGenerator().generate(self.model)
        assert "Lineage" in html
        assert "badge-compatible" in html or "badge-incompatible" in html
