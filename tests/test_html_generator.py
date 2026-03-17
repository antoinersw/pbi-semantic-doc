"""Unit tests for the HtmlGenerator."""

import pytest
from pbi_semantic_doc.html_generator import HtmlGenerator, _e, _code, _table, _details, _section_anchor


# ── helpers ────────────────────────────────────────────────────────────────

class TestHtmlHelpers:
    def test_e_escapes_lt_gt(self):
        assert _e("<b>") == "&lt;b&gt;"

    def test_e_escapes_ampersand(self):
        assert _e("A & B") == "A &amp; B"

    def test_e_does_not_escape_quotes(self):
        # quote=False in body context
        assert _e('"hello"') == '"hello"'

    def test_code_wraps_in_code_tag(self):
        assert _code("MyTable") == "<code>MyTable</code>"

    def test_code_escapes_content(self):
        assert _code("<key>") == "<code>&lt;key&gt;</code>"

    def test_table_has_thead_and_tbody(self):
        html = _table(["A", "B"], [["x", "y"]])
        assert "<thead>" in html
        assert "<tbody>" in html
        assert "<th>A</th>" in html
        assert "<td>x</td>" in html

    def test_table_escapes_headers(self):
        html = _table(["<Col>"], [["val"]])
        assert "&lt;Col&gt;" in html

    def test_details_wraps_correctly(self):
        html = _details("Summary text", "<p>body</p>")
        assert "<details>" in html
        assert "<summary>Summary text</summary>" in html
        assert "details-body" in html
        assert "<p>body</p>" in html
        assert "</details>" in html

    def test_section_anchor_basic(self):
        assert _section_anchor("Overview") == "overview"

    def test_section_anchor_with_backticks(self):
        # Same algorithm as MarkdownGenerator._heading_anchor
        assert _section_anchor("Table: `Sales`") == "table-sales"

    def test_section_anchor_spaces_to_hyphens(self):
        assert _section_anchor("Row Level Security") == "row-level-security"

    def test_section_anchor_strips_special_chars(self):
        assert _section_anchor("Measures Index (A–Z)") == "measures-index-az"


# ── model generation ──────────────────────────────────────────────────────

def _make_minimal_model():
    """Build a minimal SemanticModel for unit testing."""
    from pbi_semantic_doc.parser import (
        SemanticModel, Table, Column, Measure, Relationship
    )
    col = Column(name="ID", data_type="int64")
    measure = Measure(name="Total Sales", expression="SUM(Sales[Amount])")
    table = Table(name="Sales", columns=[col], measures=[measure])
    model = SemanticModel(name="TestModel", tables=[table])
    return model


class TestHtmlGeneratorModel:
    def setup_method(self):
        self.model = _make_minimal_model()
        self.gen = HtmlGenerator()
        self.html = self.gen.generate(self.model)

    def test_returns_string(self):
        assert isinstance(self.html, str)

    def test_valid_html_doctype(self):
        assert self.html.startswith("<!DOCTYPE html>")

    def test_contains_model_name(self):
        assert "TestModel" in self.html

    def test_contains_overview_section(self):
        assert 'id="overview"' in self.html

    def test_contains_table_section(self):
        assert "Sales" in self.html

    def test_contains_measures_inline(self):
        # Single-table model: measures appear inline in the table section,
        # no separate Measures Index (which is only shown for 2+ tables).
        assert "Total Sales" in self.html
        assert "measures-index-az" not in self.html

    def test_contains_toc_nav(self):
        assert 'class="sidebar-nav"' in self.html

    def test_contains_toolbar(self):
        assert "toggleAll" in self.html
        assert "Expand" in self.html

    def test_css_embedded(self):
        assert "<style>" in self.html
        assert "--accent" in self.html

    def test_js_embedded(self):
        assert "<script>" in self.html

    def test_footer_present(self):
        assert "pbi-semantic-doc" in self.html

    def test_print_media_query(self):
        assert "@media print" in self.html

    def test_measures_index_appears_for_multi_table_model(self):
        """Measures Index (A-Z) must appear when measures span 2+ tables."""
        from pbi_semantic_doc.parser import SemanticModel, Table, Column, Measure
        t1 = Table(name="Sales", columns=[Column(name="ID", data_type="int64")],
                   measures=[Measure(name="Total Sales", expression="SUM(Sales[Amount])")])
        t2 = Table(name="Budget", columns=[Column(name="ID", data_type="int64")],
                   measures=[Measure(name="Total Budget", expression="SUM(Budget[Amount])")])
        model = SemanticModel(name="MultiModel", tables=[t1, t2])
        html = HtmlGenerator().generate(model)
        assert "measures-index-az" in html

    def test_table_name_in_code_tag(self):
        assert "<code>Sales</code>" in self.html

    def test_measure_name_in_code_tag(self):
        assert "<code>Total Sales</code>" in self.html

    def test_column_collapsible(self):
        assert "click to expand" in self.html

    def test_m_expression_not_rendered_without_partition(self):
        # No partition with M expression in minimal model
        assert "Power Query" not in self.html

    def test_no_rls_section_when_empty(self):
        assert "row-level-security" not in self.html

    def test_no_relationships_section_when_empty(self):
        assert "relationships" not in self.html or 'id="relationships"' not in self.html

    def test_html_is_self_contained(self):
        # No external stylesheet or script references
        assert 'rel="stylesheet"' not in self.html
        assert 'src="http' not in self.html


class TestHtmlGeneratorWithRelationships:
    def setup_method(self):
        from pbi_semantic_doc.parser import (
            SemanticModel, Table, Column, Relationship
        )
        sales = Table(name="Sales", columns=[Column(name="CustID", data_type="int64")])
        customers = Table(name="Customers", columns=[Column(name="ID", data_type="int64")])
        rel = Relationship(
            from_table="Sales", from_column="CustID",
            to_table="Customers", to_column="ID",
            cardinality="many-to-one",
            cross_filter="single",
            is_active=True,
        )
        self.model = SemanticModel(
            name="WithRels", tables=[sales, customers], relationships=[rel]
        )
        self.html = HtmlGenerator().generate(self.model)

    def test_relationships_section_present(self):
        assert 'id="relationships"' in self.html

    def test_relationship_from_table(self):
        assert "Sales" in self.html

    def test_relationship_to_table(self):
        assert "Customers" in self.html

    def test_active_icon_present(self):
        assert "✅" in self.html


class TestHtmlGeneratorWithRLS:
    def setup_method(self):
        from pbi_semantic_doc.parser import (
            SemanticModel, Table, Column, Role, RoleTablePermission
        )
        table = Table(name="Orders", columns=[Column(name="Region", data_type="string")])
        tp = RoleTablePermission(table_name="Orders", filter_expression="[Region] = \"North\"")
        role = Role(name="NorthRegion", model_permission="read", table_permissions=[tp])
        self.model = SemanticModel(
            name="RLSModel", tables=[table], roles=[role]
        )
        self.html = HtmlGenerator().generate(self.model)

    def test_rls_section_present(self):
        assert 'id="row-level-security"' in self.html

    def test_role_name_present(self):
        assert "NorthRegion" in self.html

    def test_filter_expression_in_code(self):
        assert "<code>" in self.html


# ── report generation ──────────────────────────────────────────────────────

class TestHtmlGeneratorReport:
    def setup_method(self):
        from pbi_semantic_doc.report_models import ReportMetrics
        self.metrics = ReportMetrics(
            report_name="My Report",
            report_format="PBIR",
            total_pages=3,
            hidden_pages_count=0,
            total_visuals=50,
            visuals_per_page_avg=16.7,
            visuals_per_page_min=10,
            visuals_per_page_max=25,
            total_bookmarks=5,
            bookmark_names=["Bookmark1", "Bookmark2"],
            has_bookmarks=True,
            visual_types_count={"barChart": 10, "card": 8},
            visual_types_percentage={"barChart": 20.0, "card": 16.0},
            custom_visuals=["CustomViz"],
            pages_with_drillthrough=1,
            total_filters=12,
            visuals_with_mobile_layout=5,
            report_level_measures=["Measure1"],
            has_report_extensions=True,
        )
        self.html = HtmlGenerator().generate_report(self.metrics)

    def test_returns_string(self):
        assert isinstance(self.html, str)

    def test_valid_html_doctype(self):
        assert self.html.startswith("<!DOCTYPE html>")

    def test_report_name_in_title(self):
        assert "My Report" in self.html

    def test_overview_section(self):
        assert 'id="overview"' in self.html

    def test_visual_types_section(self):
        assert "visual-types-distribution" in self.html

    def test_custom_visuals_section(self):
        assert "custom-visuals" in self.html

    def test_bookmarks_section(self):
        assert "bookmarks" in self.html

    def test_report_extensions_section(self):
        assert "report-extensions" in self.html

    def test_advanced_metrics_section(self):
        assert "advanced-metrics" in self.html

    def test_toc_nav_present(self):
        assert 'class="sidebar-nav"' in self.html

    def test_print_media_query(self):
        assert "@media print" in self.html


# ── combined generation ────────────────────────────────────────────────────

class TestHtmlGeneratorCombined:
    def setup_method(self):
        from pbi_semantic_doc.parser import SemanticModel, Table, Column
        from pbi_semantic_doc.report_models import ReportMetrics
        table = Table(name="Data", columns=[Column(name="X", data_type="int64")])
        self.model = SemanticModel(name="CombinedModel", tables=[table])
        self.metrics = ReportMetrics(
            report_name="CombinedReport",
            report_format="PBIR",
            total_pages=2,
            hidden_pages_count=0,
            total_visuals=10,
            visuals_per_page_avg=5.0,
            visuals_per_page_min=5,
            visuals_per_page_max=5,
            total_bookmarks=0,
            bookmark_names=[],
            has_bookmarks=False,
            visual_types_count={"card": 5},
            visual_types_percentage={"card": 100.0},
            custom_visuals=[],
            pages_with_drillthrough=0,
            total_filters=2,
            visuals_with_mobile_layout=0,
            report_level_measures=[],
            has_report_extensions=False,
        )
        self.html = HtmlGenerator().generate_combined(
            self.model, self.metrics, "CombinedModel"
        )

    def test_valid_html_doctype(self):
        assert self.html.startswith("<!DOCTYPE html>")

    def test_semantic_model_section(self):
        # Combined doc uses flat sm-prefixed sections (no outer wrapper)
        assert 'id="sm-overview"' in self.html

    def test_report_section(self):
        assert 'id="rpt-overview"' in self.html

    def test_combined_toc(self):
        assert "Semantic Model" in self.html
        assert "Report" in self.html

    def test_model_content(self):
        assert "CombinedModel" in self.html

    def test_report_content(self):
        assert "PBIR" in self.html

    def test_toolbar_present(self):
        assert "toggleAll" in self.html

    def test_combined_model_only(self):
        html = HtmlGenerator().generate_combined(self.model, None, "ModelOnly")
        assert 'id="sm-overview"' in html
        assert 'id="rpt-overview"' not in html

    def test_combined_report_only(self):
        html = HtmlGenerator().generate_combined(None, self.metrics, "ReportOnly")
        assert 'id="rpt-overview"' in html
        assert 'id="sm-overview"' not in html


# ── integration with real model (skips if examples not present) ────────────

class TestHtmlGeneratorIntegration:
    def setup_method(self):
        from pathlib import Path
        sample = Path(__file__).parent.parent / "examples" / "sample_model"
        if not sample.exists():
            pytest.skip("examples/sample_model not found")
        from pbi_semantic_doc.parser import TmdlParser
        semantic = sample / "Artificial Intelligence Sample.SemanticModel"
        self.model = TmdlParser().parse(semantic / "definition")
        self.html = HtmlGenerator().generate(self.model)

    def test_returns_complete_html(self):
        assert self.html.startswith("<!DOCTYPE html>")
        assert "</html>" in self.html

    def test_model_name_present(self):
        assert "Artificial Intelligence Sample" in self.html

    def test_all_visible_tables_present(self):
        for name in ("Accounts", "Cases", "Contacts", "Opportunities"):
            assert name in self.html, f"Table '{name}' not found in HTML"

    def test_rls_roles_present(self):
        assert "admin_role" in self.html
        assert "user_role" in self.html

    def test_relationships_section(self):
        assert 'id="relationships"' in self.html

    def test_measures_index(self):
        assert "measures-index-az" in self.html

    def test_quoted_step_names_in_html(self):
        # #"Changed Type" steps should appear in the HTML (escaped)
        assert "Changed Type" in self.html

    def test_html_is_self_contained(self):
        assert 'rel="stylesheet"' not in self.html
        assert "src=http" not in self.html
