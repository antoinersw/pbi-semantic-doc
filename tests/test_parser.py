"""
Tests for pbi-semantic-doc.

Run with:
    python -m pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pbi_semantic_doc.parser import (
    TmdlParser, SemanticModel, Measure,
    Partition, MQueryAnalysis, Role, RoleTablePermission,
)
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


# ---------------------------------------------------------------------------
# Partition parsing tests
# ---------------------------------------------------------------------------

class TestPartitionParsing:

    def setup_method(self):
        parser = TmdlParser()
        self.model = parser.parse(SAMPLE_MODEL)
        self.sales = next(t for t in self.model.tables if t.name == "Sales")
        self.calendar = next(t for t in self.model.tables if t.name == "Calendar")
        self.targets = next(t for t in self.model.tables if t.name == "Targets")

    # --- Sales: SQL Server import partition ---

    def test_sales_has_one_partition(self):
        assert len(self.sales.partitions) == 1

    def test_sales_partition_type_is_m(self):
        assert self.sales.partitions[0].type == "m"

    def test_sales_partition_mode_is_import(self):
        assert self.sales.partitions[0].mode == "import"

    def test_sales_partition_has_expression(self):
        assert self.sales.partitions[0].expression != ""

    def test_sales_partition_expression_contains_sql_database(self):
        expr = self.sales.partitions[0].expression
        assert "Sql.Database" in expr

    def test_sales_connector_source_type(self):
        qa = self.sales.partitions[0].query_analysis
        assert qa is not None
        assert qa.connector is not None
        assert qa.connector.source_type == "SQL Server"

    def test_sales_connector_server(self):
        qa = self.sales.partitions[0].query_analysis
        assert qa.connector.positional_params[0] == "srv-dw01"

    def test_sales_connector_database(self):
        qa = self.sales.partitions[0].query_analysis
        assert qa.connector.positional_params[1] == "AdventureWorks"

    def test_sales_steps_parsed(self):
        qa = self.sales.partitions[0].query_analysis
        assert qa.step_count >= 3

    def test_sales_step_names_present(self):
        qa = self.sales.partitions[0].query_analysis
        step_names = [s.name for s in qa.steps]
        assert "Source" in step_names

    def test_sales_query_type_is_m_query(self):
        qa = self.sales.partitions[0].query_analysis
        assert qa.query_type == "m_query"

    def test_sales_folding_not_disabled(self):
        qa = self.sales.partitions[0].query_analysis
        # SQL Server with foldable steps → likely or at_risk, never n/a
        assert qa.query_folding_status in ("likely", "at_risk", "disabled")
        assert qa.query_folding_status != "n/a"

    def test_sales_effective_mode(self):
        assert self.sales.effective_mode == "import"

    def test_sales_is_not_incremental(self):
        assert self.sales.is_incremental is False

    # --- Calendar: calculated partition ---

    def test_calendar_has_one_partition(self):
        assert len(self.calendar.partitions) == 1

    def test_calendar_partition_type_is_calculated(self):
        assert self.calendar.partitions[0].type == "calculated"

    def test_calendar_query_type_is_calculated(self):
        qa = self.calendar.partitions[0].query_analysis
        assert qa is not None
        assert qa.query_type == "calculated"

    def test_calendar_connector_is_none(self):
        qa = self.calendar.partitions[0].query_analysis
        assert qa.connector is None

    def test_calendar_effective_mode(self):
        assert self.calendar.effective_mode == "calculated"

    # --- Targets: Excel file-based partition ---

    def test_targets_has_one_partition(self):
        assert len(self.targets.partitions) == 1

    def test_targets_connector_source_type(self):
        qa = self.targets.partitions[0].query_analysis
        assert qa.connector is not None
        assert qa.connector.source_type == "Excel"

    def test_targets_folding_is_na(self):
        qa = self.targets.partitions[0].query_analysis
        # Excel never supports query folding
        assert qa.query_folding_status == "n/a"

    def test_targets_promote_headers_detected(self):
        qa = self.targets.partitions[0].query_analysis
        step_types = [s.transform_type for s in qa.steps]
        assert "promote_headers" in step_types


# ---------------------------------------------------------------------------
# Native SQL detection tests
# ---------------------------------------------------------------------------

class TestNativeSqlDetection:

    def setup_method(self):
        self.parser = TmdlParser()

    def _make_partition_expression(self, expr: str) -> MQueryAnalysis:
        return self.parser._analyze_m_query(expr, "m")

    def test_value_native_query_detected(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Result = Value.NativeQuery(Source, "SELECT * FROM dbo.Sales WHERE Year = 2024")
in
    Result
"""
        qa = self._make_partition_expression(expr)
        assert qa.native_query is not None
        assert "SELECT" in qa.native_query

    def test_query_named_param_detected(self):
        expr = """
let
    Source = Sql.Database("server", "db", [Query="SELECT Id, Name FROM dbo.Customer"])
in
    Source
"""
        qa = self._make_partition_expression(expr)
        assert qa.native_query is not None
        assert "SELECT" in qa.native_query

    def test_query_type_native_sql(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Result = Value.NativeQuery(Source, "SELECT 1")
in
    Result
"""
        qa = self._make_partition_expression(expr)
        assert qa.query_type == "native_sql"

    def test_no_native_query_returns_none(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Data = Source{[Schema="dbo", Item="Sales"]}[Data]
in
    Data
"""
        qa = self._make_partition_expression(expr)
        assert qa.native_query is None


# ---------------------------------------------------------------------------
# Query folding assessment tests
# ---------------------------------------------------------------------------

class TestQueryFoldingAssessment:

    def setup_method(self):
        self.parser = TmdlParser()

    def _analyze(self, expr: str) -> MQueryAnalysis:
        return self.parser._analyze_m_query(expr, "m")

    def test_table_buffer_disables_folding(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Data = Source{[Schema="dbo", Item="Sales"]}[Data],
    Buffered = Table.Buffer(Data)
in
    Buffered
"""
        qa = self._analyze(expr)
        assert qa.query_folding_status == "disabled"
        assert "Table.Buffer" in qa.query_folding_reason

    def test_table_combine_disables_folding(self):
        expr = """
let
    Source1 = Sql.Database("server", "db"),
    Source2 = Sql.Database("server", "db"),
    Data1 = Source1{[Schema="dbo", Item="Sales2023"]}[Data],
    Data2 = Source2{[Schema="dbo", Item="Sales2024"]}[Data],
    Combined = Table.Combine({Data1, Data2})
in
    Combined
"""
        qa = self._analyze(expr)
        assert qa.query_folding_status == "disabled"

    def test_excel_folding_is_na(self):
        expr = """
let
    Source = Excel.Workbook(File.Contents("C:\\data\\file.xlsx")),
    Sheet = Source{[Item="Sheet1"]}[Data]
in
    Sheet
"""
        qa = self._analyze(expr)
        assert qa.query_folding_status == "n/a"

    def test_merge_gives_at_risk(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Data = Source{[Schema="dbo", Item="Sales"]}[Data],
    Merged = Table.NestedJoin(Data, "CustomerID", Source{[Schema="dbo",Item="Customer"]}[Data], "CustomerID", "Customer", JoinKind.LeftOuter)
in
    Merged
"""
        qa = self._analyze(expr)
        assert qa.query_folding_status == "at_risk"

    def test_foldable_steps_give_likely(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Data = Source{[Schema="dbo", Item="Sales"]}[Data],
    Filtered = Table.SelectRows(Data, each [Year] >= 2020),
    Renamed = Table.RenameColumns(Filtered, {{"OldName", "NewName"}}),
    Typed = Table.TransformColumnTypes(Renamed, {{"Amount", type number}})
in
    Typed
"""
        qa = self._analyze(expr)
        assert qa.query_folding_status == "likely"


# ---------------------------------------------------------------------------
# Incremental refresh detection tests
# ---------------------------------------------------------------------------

class TestIncrementalRefreshDetection:

    def setup_method(self):
        self.parser = TmdlParser()

    def test_incremental_refresh_detected(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Data = Source{[Schema="dbo", Item="Sales"]}[Data],
    Filtered = Table.SelectRows(Data, each [OrderDate] >= RangeStart and [OrderDate] < RangeEnd)
in
    Filtered
"""
        qa = self.parser._analyze_m_query(expr, "m")
        assert qa.incremental_refresh.is_incremental is True
        assert qa.incremental_refresh.has_range_start is True
        assert qa.incremental_refresh.has_range_end is True

    def test_incremental_refresh_column_detected(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Data = Source{[Schema="dbo", Item="Sales"]}[Data],
    Filtered = Table.SelectRows(Data, each [OrderDate] >= RangeStart and [OrderDate] < RangeEnd)
in
    Filtered
"""
        qa = self.parser._analyze_m_query(expr, "m")
        assert qa.incremental_refresh.range_column == "OrderDate"

    def test_no_incremental_refresh(self):
        expr = """
let
    Source = Sql.Database("server", "db"),
    Data = Source{[Schema="dbo", Item="Sales"]}[Data]
in
    Data
"""
        qa = self.parser._analyze_m_query(expr, "m")
        assert qa.incremental_refresh.is_incremental is False


# ---------------------------------------------------------------------------
# RLS role parsing tests
# ---------------------------------------------------------------------------

class TestRlsParsing:

    def setup_method(self):
        parser = TmdlParser()
        self.model = parser.parse(SAMPLE_MODEL)

    def test_roles_parsed(self):
        assert len(self.model.roles) == 1

    def test_role_name(self):
        assert self.model.roles[0].name == "Sales Managers"

    def test_role_model_permission(self):
        assert self.model.roles[0].model_permission == "read"

    def test_role_table_permissions_count(self):
        assert len(self.model.roles[0].table_permissions) == 2

    def test_role_sales_filter(self):
        tp = next(
            p for p in self.model.roles[0].table_permissions
            if p.table_name == "Sales"
        )
        assert "USERPRINCIPALNAME" in tp.filter_expression

    def test_role_customer_no_filter(self):
        tp = next(
            p for p in self.model.roles[0].table_permissions
            if p.table_name == "Customer"
        )
        assert tp.filter_expression == "true"


# ---------------------------------------------------------------------------
# Data source aggregation tests
# ---------------------------------------------------------------------------

class TestDataSources:

    def setup_method(self):
        parser = TmdlParser()
        self.model = parser.parse(SAMPLE_MODEL)

    def test_data_sources_not_empty(self):
        sources = self.model.data_sources
        assert len(sources) > 0

    def test_sql_server_source_present(self):
        sources = self.model.data_sources
        types = [s.source_type for s in sources]
        assert "SQL Server" in types

    def test_excel_source_present(self):
        sources = self.model.data_sources
        types = [s.source_type for s in sources]
        assert "Excel" in types

    def test_sql_server_tables_include_sales(self):
        sources = self.model.data_sources
        sql = next(s for s in sources if s.source_type == "SQL Server")
        assert "Sales" in sql.tables

    def test_excel_tables_include_targets(self):
        sources = self.model.data_sources
        excel = next(s for s in sources if s.source_type == "Excel")
        assert "Targets" in excel.tables


# ---------------------------------------------------------------------------
# Generator v0.3 output tests
# ---------------------------------------------------------------------------

class TestGeneratorV03:

    def setup_method(self):
        parser = TmdlParser()
        self.model = parser.parse(SAMPLE_MODEL)
        self.generator = MarkdownGenerator()
        self.output = self.generator.generate(self.model)

    def test_data_sources_section_present(self):
        assert "## Data Sources" in self.output

    def test_rls_section_present(self):
        assert "## Row Level Security" in self.output

    def test_sql_server_in_output(self):
        assert "SQL Server" in self.output

    def test_excel_in_output(self):
        assert "Excel" in self.output

    def test_role_name_in_output(self):
        assert "Sales Managers" in self.output

    def test_m_expression_collapsible_present(self):
        assert "Power Query" in self.output

    def test_query_folding_status_in_output(self):
        # At least one folding status should appear
        assert any(label in self.output for label in ("Likely", "At Risk", "Disabled", "N/A"))

    def test_rls_filter_expression_in_output(self):
        assert "USERPRINCIPALNAME" in self.output

    def test_overview_includes_rls_count(self):
        assert "RLS Roles" in self.output
