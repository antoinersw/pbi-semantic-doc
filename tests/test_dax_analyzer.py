"""Unit tests for pbi_semantic_doc.dax_analyzer (Layer 1 — stateless)."""

import pytest
from pbi_semantic_doc.dax_analyzer import extract_dax_refs, DaxRefs


# ── Basic aggregation ──────────────────────────────────────────────────────────

class TestAggregatedTables:
    def test_sum_simple(self):
        refs = extract_dax_refs("SUM(Sales[Amount])")
        assert "Sales" in refs.aggregated_tables

    def test_average(self):
        refs = extract_dax_refs("AVERAGE(Orders[Quantity])")
        assert "Orders" in refs.aggregated_tables

    def test_countrows(self):
        refs = extract_dax_refs("COUNTROWS(Customers)")
        assert "Customers" in refs.aggregated_tables

    def test_sumx(self):
        refs = extract_dax_refs("SUMX(Sales, Sales[Amount] * Sales[Price])")
        assert "Sales" in refs.aggregated_tables

    def test_distinctcount(self):
        refs = extract_dax_refs("DISTINCTCOUNT(Sales[CustomerID])")
        assert "Sales" in refs.aggregated_tables

    def test_quoted_table_name(self):
        refs = extract_dax_refs("SUM('Fact Sales'[Revenue])")
        assert "Fact Sales" in refs.aggregated_tables

    def test_empty_expression(self):
        refs = extract_dax_refs("")
        assert not refs.aggregated_tables


# ── Table[Column] references ───────────────────────────────────────────────────

class TestTableColumnRefs:
    def test_simple_ref(self):
        refs = extract_dax_refs("Sales[Amount]")
        assert ("Sales", "Amount") in refs.table_column_refs

    def test_quoted_table(self):
        refs = extract_dax_refs("'Dim Cliente'[Nome]")
        assert ("Dim Cliente", "Nome") in refs.table_column_refs

    def test_multiple_refs(self):
        refs = extract_dax_refs("Sales[Amount] + Calendar[Year]")
        tables = [t for t, _ in refs.table_column_refs]
        assert "Sales" in tables
        assert "Calendar" in tables

    def test_calculate_with_filter(self):
        refs = extract_dax_refs(
            "CALCULATE(SUM(Sales[Amount]), DimCliente[Region] = \"North\")"
        )
        tables = [t for t, _ in refs.table_column_refs]
        assert "Sales" in tables
        assert "DimCliente" in tables


# ── Nested measure references ──────────────────────────────────────────────────

class TestNestedMeasureNames:
    def test_simple_measure_ref(self):
        refs = extract_dax_refs("[Revenue] / [Quantity]")
        assert "Revenue" in refs.nested_measure_names
        assert "Quantity" in refs.nested_measure_names

    def test_measure_ref_in_calculate(self):
        refs = extract_dax_refs("CALCULATE([Revenue], DimCliente[Region] = \"North\")")
        assert "Revenue" in refs.nested_measure_names

    def test_table_col_not_treated_as_measure(self):
        refs = extract_dax_refs("SUM(Sales[Amount])")
        # "Amount" is a column, not a measure ref
        assert "Amount" not in refs.nested_measure_names

    def test_deduplicated(self):
        refs = extract_dax_refs("[Revenue] + [Revenue] * 2")
        assert refs.nested_measure_names.count("Revenue") == 1

    def test_time_intelligence_measure(self):
        refs = extract_dax_refs("TOTALYTD([Revenue], Calendar[Date])")
        assert "Revenue" in refs.nested_measure_names


# ── ALL / ALLEXCEPT ────────────────────────────────────────────────────────────

class TestAllRemovedTables:
    def test_all_simple(self):
        refs = extract_dax_refs("CALCULATE([Revenue], ALL(DimCliente))")
        assert "DimCliente" in refs.all_removed_tables

    def test_all_with_column(self):
        refs = extract_dax_refs("CALCULATE([Revenue], ALL(DimCliente[Region]))")
        assert "DimCliente" in refs.all_removed_tables

    def test_all_quoted_table(self):
        refs = extract_dax_refs("CALCULATE([Revenue], ALL('Dim Canale'))")
        assert "Dim Canale" in refs.all_removed_tables

    def test_allexcept(self):
        refs = extract_dax_refs(
            "CALCULATE([Revenue], ALLEXCEPT(Sales, Sales[Year]))"
        )
        assert "Sales" in refs.all_removed_tables

    def test_allselected(self):
        refs = extract_dax_refs("CALCULATE([Revenue], ALLSELECTED(DimProdotto))")
        assert "DimProdotto" in refs.all_removed_tables

    def test_multiple_all(self):
        refs = extract_dax_refs(
            "CALCULATE([Revenue], ALL(DimCliente), ALL(DimCanale))"
        )
        assert "DimCliente" in refs.all_removed_tables
        assert "DimCanale" in refs.all_removed_tables


# ── Flags ──────────────────────────────────────────────────────────────────────

class TestFlags:
    def test_time_intelligence_totalytd(self):
        refs = extract_dax_refs("TOTALYTD([Revenue], Calendar[Date])")
        assert refs.uses_time_intelligence is True

    def test_time_intelligence_dateadd(self):
        refs = extract_dax_refs("CALCULATE([Revenue], DATEADD(Calendar[Date], -1, YEAR))")
        assert refs.uses_time_intelligence is True

    def test_time_intelligence_sameperiodlastyear(self):
        refs = extract_dax_refs(
            "CALCULATE([Revenue], SAMEPERIODLASTYEAR(Calendar[Date]))"
        )
        assert refs.uses_time_intelligence is True

    def test_no_time_intelligence(self):
        refs = extract_dax_refs("SUM(Sales[Amount])")
        assert refs.uses_time_intelligence is False

    def test_userelationship(self):
        refs = extract_dax_refs(
            "CALCULATE(SUM(Sales[Amount]), USERELATIONSHIP(Sales[OrderDate], Calendar[Date]))"
        )
        assert refs.uses_inactive_relationship is True

    def test_no_userelationship(self):
        refs = extract_dax_refs("SUM(Sales[Amount])")
        assert refs.uses_inactive_relationship is False

    def test_treatas(self):
        refs = extract_dax_refs(
            "CALCULATE([Revenue], TREATAS({2023}, Calendar[Year]))"
        )
        assert refs.uses_treatas is True


# ── Complex real-world DAX ────────────────────────────────────────────────────

class TestComplexDax:
    def test_var_return_pattern(self):
        dax = """
VAR _sales = SUM(Sales[Amount])
VAR _target = SUM(Budget[Target])
RETURN
    DIVIDE(_sales, _target, 0)
"""
        refs = extract_dax_refs(dax)
        assert "Sales" in refs.aggregated_tables
        assert "Budget" in refs.aggregated_tables

    def test_nested_calculate_with_all(self):
        dax = """
CALCULATE(
    [Revenue],
    ALL(DimCliente),
    DimProdotto[Category] = "Electronics"
)
"""
        refs = extract_dax_refs(dax)
        assert "Revenue" in refs.nested_measure_names
        assert "DimCliente" in refs.all_removed_tables
        tables = [t for t, _ in refs.table_column_refs]
        assert "DimProdotto" in tables

    def test_yoy_measure(self):
        dax = """
VAR _current = [Revenue]
VAR _prev = CALCULATE([Revenue], SAMEPERIODLASTYEAR(Calendar[Date]))
RETURN DIVIDE(_current - _prev, _prev, BLANK())
"""
        refs = extract_dax_refs(dax)
        assert refs.uses_time_intelligence is True
        assert "Revenue" in refs.nested_measure_names
        assert ("Calendar", "Date") in refs.table_column_refs

    def test_rankx_measure(self):
        dax = "RANKX(ALL(DimCliente), [Revenue])"
        refs = extract_dax_refs(dax)
        assert "DimCliente" in refs.all_removed_tables
        assert "Revenue" in refs.nested_measure_names
