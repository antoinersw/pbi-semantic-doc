"""
Tests for pbi-semantic-doc.

Run with:
    python -m pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pbi_semantic_doc.parser import TmdlParser, SemanticModel, Measure
from pbi_semantic_doc.generator import MarkdownGenerator


SAMPLE_MODEL = Path(__file__).parent / "fixtures" / "sample_model"


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestTmdlParser:

    def test_parse_returns_semantic_model(self):
        parser = TmdlParser()
        model = parser.parse(SAMPLE_MODEL)
        assert isinstance(model, SemanticModel)

    def test_model_name_extracted(self):
        parser = TmdlParser()
        model = parser.parse(SAMPLE_MODEL)
        assert model.name == "SalesModel"

    def test_tables_parsed(self):
        parser = TmdlParser()
        model = parser.parse(SAMPLE_MODEL)
        table_names = {t.name for t in model.tables}
        assert "Sales" in table_names
        assert "Calendar" in table_names
        assert "Customer" in table_names

    def test_columns_parsed(self):
        parser = TmdlParser()
        model = parser.parse(SAMPLE_MODEL)
        sales = next(t for t in model.tables if t.name == "Sales")
        col_names = {c.name for c in sales.columns}
        assert "OrderID" in col_names
        assert "SalesAmount" in col_names

    def test_measures_parsed(self):
        parser = TmdlParser()
        model = parser.parse(SAMPLE_MODEL)
        sales = next(t for t in model.tables if t.name == "Sales")
        measure_names = {m.name for m in sales.measures}
        assert "Total Sales" in measure_names
        assert "Sales YTD" in measure_names

    def test_measure_with_description(self):
        parser = TmdlParser()
        model = parser.parse(SAMPLE_MODEL)
        sales = next(t for t in model.tables if t.name == "Sales")
        total_sales = next(m for m in sales.measures if m.name == "Total Sales")
        assert total_sales.description != ""

    def test_relationships_parsed(self):
        parser = TmdlParser()
        model = parser.parse(SAMPLE_MODEL)
        assert len(model.relationships) == 2
        from_tables = {r.from_table for r in model.relationships}
        assert "Sales" in from_tables

    def test_missing_path_raises(self):
        parser = TmdlParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/path"))


# ---------------------------------------------------------------------------
# Measure.auto_description tests
# ---------------------------------------------------------------------------

class TestAutoDescription:

    def _make_measure(self, expression: str) -> Measure:
        return Measure(name="Test", expression=expression)

    def test_sum_detected(self):
        m = self._make_measure("SUM(Sales[Amount])")
        assert "SUM" in m.auto_description()

    def test_time_intelligence_detected(self):
        m = self._make_measure("TOTALYTD([Total Sales], 'Calendar'[Date])")
        assert "Time intelligence" in m.auto_description()

    def test_calculate_detected(self):
        m = self._make_measure("CALCULATE(SUM(Sales[Amount]), ALL(Customer))")
        assert "CALCULATE" in m.auto_description()

    def test_divide_safe(self):
        m = self._make_measure("DIVIDE([A], [B])")
        assert "Safe division" in m.auto_description()

    def test_var_detected(self):
        m = self._make_measure("VAR x = 1 RETURN x")
        assert "variables" in m.auto_description()

    def test_empty_expression(self):
        m = self._make_measure("")
        assert m.auto_description() == ""


# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------

class TestMarkdownGenerator:

    def setup_method(self):
        parser = TmdlParser()
        self.model = parser.parse(SAMPLE_MODEL)
        self.generator = MarkdownGenerator()
        self.output = self.generator.generate(self.model)

    def test_output_is_string(self):
        assert isinstance(self.output, str)
        assert len(self.output) > 100

    def test_model_name_in_output(self):
        assert "SalesModel" in self.output

    def test_tables_in_output(self):
        assert "Sales" in self.output
        assert "Calendar" in self.output
        assert "Customer" in self.output

    def test_measure_dax_in_output(self):
        assert "```dax" in self.output

    def test_relationships_section_present(self):
        assert "## Relationships" in self.output

    def test_measures_index_present(self):
        assert "## Measures Index" in self.output

    def test_footer_present(self):
        assert "pbi-semantic-doc" in self.output
