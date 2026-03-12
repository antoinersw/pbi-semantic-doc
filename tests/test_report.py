"""
Tests for report analysis components:
- ReportParser
- ReportMetrics / ReportModels
- ReportGenerator
- CLI report commands

Run with:
    python -m pytest tests/test_report.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pbi_semantic_doc.report_parser import ReportParser
from pbi_semantic_doc.report_models import (
    Report,
    ReportPage,
    ReportMetrics,
    Visual,
    VisualType,
    ReportFormat,
    Bookmark,
    ReportExtensions,
)
from pbi_semantic_doc.report_generator import ReportGenerator
from pbi_semantic_doc.cli import main as cli_main


# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"
PBIR_REPORT   = FIXTURES / "pbir_report"
LEGACY_REPORT = FIXTURES / "legacy_report"
EMPTY_REPORT  = FIXTURES / "empty_report"
MALFORMED_REPORT = FIXTURES / "malformed_report"


# ===========================================================================
# ReportParser — PBIR format
# ===========================================================================

class TestReportParserPBIR:

    def setup_method(self):
        self.parser = ReportParser()
        self.report = self.parser.parse(PBIR_REPORT)

    def test_parse_returns_report(self):
        assert isinstance(self.report, Report)

    def test_format_detected_as_pbir(self):
        assert self.report.format == ReportFormat.PBIR

    def test_pages_count(self):
        assert len(self.report.pages) == 2

    def test_page_names(self):
        names = {p.name for p in self.report.pages}
        assert "page_home" in names
        assert "page_hidden" in names

    def test_page_display_name(self):
        home = next(p for p in self.report.pages if p.name == "page_home")
        assert home.display_name == "Home"

    def test_hidden_page_detected(self):
        hidden = next(p for p in self.report.pages if p.name == "page_hidden")
        assert hidden.is_hidden is True

    def test_visible_page_not_hidden(self):
        home = next(p for p in self.report.pages if p.name == "page_home")
        assert home.is_hidden is False

    def test_drillthrough_detected(self):
        hidden = next(p for p in self.report.pages if p.name == "page_hidden")
        assert hidden.has_drillthrough is True

    def test_visuals_parsed(self):
        home = next(p for p in self.report.pages if p.name == "page_home")
        assert len(home.visuals) == 2

    def test_visual_types_detected(self):
        home = next(p for p in self.report.pages if p.name == "page_home")
        types = {v.visual_type for v in home.visuals}
        assert VisualType.BAR_CHART in types
        assert VisualType.CARD in types

    def test_bookmarks_parsed(self):
        assert len(self.report.bookmarks) == 2

    def test_bookmark_display_names(self):
        names = {b.display_name for b in self.report.bookmarks}
        assert "Overview Bookmark" in names
        assert "Detail View" in names

    def test_bookmark_page_link(self):
        bk = next(b for b in self.report.bookmarks if b.name == "bk_overview")
        assert bk.page_name == "page_home"

    def test_report_extensions_parsed(self):
        assert self.report.extensions is not None
        assert self.report.extensions.has_extensions is True

    def test_report_level_measures(self):
        measures = self.report.extensions.measures
        assert "ReportMeasure1" in measures
        assert "ReportMeasure2" in measures

    def test_version_parsed(self):
        assert self.report.version == "1.0"

    def test_page_dimensions(self):
        home = next(p for p in self.report.pages if p.name == "page_home")
        assert home.width == 1280
        assert home.height == 720

    def test_page_filters_parsed(self):
        home = next(p for p in self.report.pages if p.name == "page_home")
        assert len(home.filters) == 1


# ===========================================================================
# ReportParser — Legacy format
# ===========================================================================

class TestReportParserLegacy:

    def setup_method(self):
        self.parser = ReportParser()
        self.report = self.parser.parse(LEGACY_REPORT)

    def test_format_detected_as_legacy(self):
        assert self.report.format == ReportFormat.PBIR_LEGACY

    def test_pages_count(self):
        assert len(self.report.pages) == 2

    def test_page_display_names(self):
        names = {p.display_name for p in self.report.pages}
        assert "Main Page" in names
        assert "Detail" in names

    def test_visuals_in_legacy_pages(self):
        main = next(p for p in self.report.pages if p.name == "pg_main")
        assert len(main.visuals) == 2

    def test_legacy_visual_types(self):
        main = next(p for p in self.report.pages if p.name == "pg_main")
        types = {v.visual_type for v in main.visuals}
        assert VisualType.MATRIX in types
        assert VisualType.SLICER in types

    def test_legacy_bookmarks(self):
        assert len(self.report.bookmarks) == 2
        names = {b.display_name for b in self.report.bookmarks}
        assert "Bookmark A" in names
        assert "Bookmark B" in names

    def test_filters_in_legacy_pages(self):
        detail = next(p for p in self.report.pages if p.name == "pg_detail")
        assert len(detail.filters) == 1


# ===========================================================================
# ReportParser — Edge cases
# ===========================================================================

class TestReportParserEdgeCases:

    def test_missing_path_raises(self):
        parser = ReportParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/path"))

    def test_empty_report_parsed(self):
        """Report with pages/ dir but no pages returns empty page list."""
        parser = ReportParser()
        report = parser.parse(EMPTY_REPORT)
        assert isinstance(report, Report)
        assert len(report.pages) == 0

    def test_malformed_json_graceful_degradation(self):
        """Malformed page.json returns page with fallback name, not crash."""
        parser = ReportParser()
        report = parser.parse(MALFORMED_REPORT)
        assert isinstance(report, Report)
        # The page should be parsed with fallback name (folder name)
        assert len(report.pages) == 1
        assert report.pages[0].name == "pg1"


# ===========================================================================
# Visual.extract_type
# ===========================================================================

class TestVisualExtractType:

    def test_bar_chart(self):
        config = {"singleVisual": {"visualType": "barChart"}}
        assert Visual.extract_type(config) == VisualType.BAR_CHART

    def test_line_chart(self):
        config = {"singleVisual": {"visualType": "lineChart"}}
        assert Visual.extract_type(config) == VisualType.LINE_CHART

    def test_matrix(self):
        config = {"singleVisual": {"visualType": "matrix"}}
        assert Visual.extract_type(config) == VisualType.MATRIX

    def test_slicer(self):
        config = {"singleVisual": {"visualType": "slicer"}}
        assert Visual.extract_type(config) == VisualType.SLICER

    def test_scatter_chart_alias(self):
        config = {"singleVisual": {"visualType": "scatterChart"}}
        assert Visual.extract_type(config) == VisualType.SCATTER

    def test_unknown_type(self):
        config = {"singleVisual": {"visualType": "someUnknownType"}}
        assert Visual.extract_type(config) == VisualType.UNKNOWN

    def test_empty_config(self):
        assert Visual.extract_type({}) == VisualType.UNKNOWN

    def test_legacy_format_config(self):
        """PBIR-Legacy may have visualType directly in config."""
        config = {"visualType": "pieChart"}
        assert Visual.extract_type(config) == VisualType.PIE_CHART

    def test_new_pbir_format_direct_visual_type(self):
        """Nuovo formato PBIR: visualType direttamente in visual{}."""
        visual_data = {"visualType": "textbox"}
        assert Visual.extract_type(visual_data) == VisualType.TEXTBOX

    def test_action_button_type(self):
        visual_data = {"visualType": "actionButton"}
        assert Visual.extract_type(visual_data) == VisualType.ACTION_BUTTON

    def test_page_navigator_type(self):
        visual_data = {"visualType": "pageNavigator"}
        assert Visual.extract_type(visual_data) == VisualType.PAGE_NAVIGATOR

    def test_clustered_column_chart(self):
        visual_data = {"visualType": "clusteredColumnChart"}
        assert Visual.extract_type(visual_data) == VisualType.CLUSTERED_COLUMN_CHART


# ===========================================================================
# ReportMetrics
# ===========================================================================

class TestReportMetrics:

    def _make_report(self, pages=None, bookmarks=None, extensions=None):
        return Report(
            name="TestReport",
            format=ReportFormat.PBIR,
            pages=pages or [],
            bookmarks=bookmarks or [],
            extensions=extensions,
        )

    def _make_page(self, name="pg1", visuals=None, is_hidden=False, has_drillthrough=False, filters=None):
        return ReportPage(
            name=name,
            display_name=name,
            visuals=visuals or [],
            is_hidden=is_hidden,
            has_drillthrough=has_drillthrough,
            filters=filters or [],
        )

    def _make_visual(self, vtype=VisualType.BAR_CHART):
        return Visual(name="v", visual_type=vtype)

    def test_empty_report_metrics(self):
        report = self._make_report()
        metrics = report.calculate_metrics()
        assert metrics.total_pages == 0
        assert metrics.total_visuals == 0
        assert metrics.complexity_index == 0.0

    def test_total_pages(self):
        pages = [self._make_page(f"pg{i}") for i in range(3)]
        report = self._make_report(pages=pages)
        metrics = report.calculate_metrics()
        assert metrics.total_pages == 3

    def test_total_visuals(self):
        visuals = [self._make_visual() for _ in range(4)]
        pages = [self._make_page(visuals=visuals)]
        report = self._make_report(pages=pages)
        metrics = report.calculate_metrics()
        assert metrics.total_visuals == 4

    def test_visuals_per_page_stats(self):
        p1 = self._make_page("p1", visuals=[self._make_visual(), self._make_visual()])
        p2 = self._make_page("p2", visuals=[self._make_visual()])
        report = self._make_report(pages=[p1, p2])
        metrics = report.calculate_metrics()
        assert metrics.visuals_per_page_min == 1
        assert metrics.visuals_per_page_max == 2
        assert metrics.visuals_per_page_avg == 1.5

    def test_hidden_pages_count(self):
        p1 = self._make_page("p1", is_hidden=True)
        p2 = self._make_page("p2", is_hidden=False)
        report = self._make_report(pages=[p1, p2])
        metrics = report.calculate_metrics()
        assert metrics.hidden_pages_count == 1

    def test_drillthrough_pages(self):
        p1 = self._make_page("p1", has_drillthrough=True)
        p2 = self._make_page("p2")
        report = self._make_report(pages=[p1, p2])
        metrics = report.calculate_metrics()
        assert metrics.pages_with_drillthrough == 1

    def test_total_filters(self):
        p1 = self._make_page("p1", filters=[{"f": 1}, {"f": 2}])
        p2 = self._make_page("p2", filters=[{"f": 3}])
        report = self._make_report(pages=[p1, p2])
        metrics = report.calculate_metrics()
        assert metrics.total_filters == 3

    def test_visual_type_distribution(self):
        v_bar = self._make_visual(VisualType.BAR_CHART)
        v_bar2 = self._make_visual(VisualType.BAR_CHART)
        v_card = self._make_visual(VisualType.CARD)
        page = self._make_page(visuals=[v_bar, v_bar2, v_card])
        report = self._make_report(pages=[page])
        metrics = report.calculate_metrics()
        assert metrics.visual_types_count["barChart"] == 2
        assert metrics.visual_types_count["card"] == 1

    def test_visual_type_percentage(self):
        v_bar = self._make_visual(VisualType.BAR_CHART)
        v_card = self._make_visual(VisualType.CARD)
        page = self._make_page(visuals=[v_bar, v_card])
        report = self._make_report(pages=[page])
        metrics = report.calculate_metrics()
        assert metrics.visual_types_percentage["barChart"] == pytest.approx(50.0)
        assert metrics.visual_types_percentage["card"] == pytest.approx(50.0)

    def test_custom_visual_detected(self):
        v = Visual(name="cv", visual_type=VisualType.CUSTOM, custom_visual_name="myCustomViz")
        page = self._make_page(visuals=[v])
        report = self._make_report(pages=[page])
        metrics = report.calculate_metrics()
        assert "myCustomViz" in metrics.custom_visuals

    def test_mobile_layout_count(self):
        v1 = Visual(name="v1", visual_type=VisualType.CARD, has_mobile_layout=True)
        v2 = Visual(name="v2", visual_type=VisualType.BAR_CHART, has_mobile_layout=False)
        page = self._make_page(visuals=[v1, v2])
        report = self._make_report(pages=[page])
        metrics = report.calculate_metrics()
        assert metrics.visuals_with_mobile_layout == 1

    def test_bookmarks_detected(self):
        bookmarks = [Bookmark("bk1", "Bookmark 1"), Bookmark("bk2", "Bookmark 2")]
        report = self._make_report(bookmarks=bookmarks)
        metrics = report.calculate_metrics()
        assert metrics.has_bookmarks is True
        assert metrics.total_bookmarks == 2
        assert "Bookmark 1" in metrics.bookmark_names

    def test_no_bookmarks(self):
        report = self._make_report()
        metrics = report.calculate_metrics()
        assert metrics.has_bookmarks is False
        assert metrics.total_bookmarks == 0

    def test_report_extensions_detected(self):
        ext = ReportExtensions(measures=["M1", "M2"], has_extensions=True)
        report = self._make_report(extensions=ext)
        metrics = report.calculate_metrics()
        assert metrics.has_report_extensions is True
        assert "M1" in metrics.report_level_measures

    def test_complexity_index_is_normalized(self):
        """complexity deve essere tra 0 e 1."""
        pages = [self._make_page(f"p{i}", visuals=[self._make_visual(), self._make_visual()]) for i in range(2)]
        bookmarks = [Bookmark("b1", "B1")]
        ext = ReportExtensions(measures=["M1"], has_extensions=True)
        report = self._make_report(pages=pages, bookmarks=bookmarks, extensions=ext)
        metrics = report.calculate_metrics()
        assert 0.0 <= metrics.complexity_index <= 1.0

    def test_complexity_index_zero_for_empty(self):
        report = self._make_report()
        metrics = report.calculate_metrics()
        assert metrics.complexity_index == 0.0

    def test_complexity_index_capped_at_one(self):
        """Un report enorme non deve superare 1.0."""
        pages = [self._make_page(f"p{i}", visuals=[self._make_visual() for _ in range(20)]) for i in range(100)]
        bookmarks = [Bookmark(f"b{i}", f"B{i}") for i in range(100)]
        ext = ReportExtensions(measures=[f"M{i}" for i in range(50)], has_extensions=True)
        report = self._make_report(pages=pages, bookmarks=bookmarks, extensions=ext)
        metrics = report.calculate_metrics()
        assert metrics.complexity_index == pytest.approx(1.0)

    def test_report_name_in_metrics(self):
        report = self._make_report()
        metrics = report.calculate_metrics()
        assert metrics.report_name == "TestReport"

    def test_report_format_in_metrics(self):
        report = self._make_report()
        metrics = report.calculate_metrics()
        assert metrics.report_format == "pbir"


# ===========================================================================
# ReportMetrics — round-trip serialization
# ===========================================================================

class TestReportMetricsRoundTrip:

    def _make_full_metrics(self):
        ext = ReportExtensions(measures=["M1", "M2"], has_extensions=True)
        report = Report(
            name="RoundTripReport",
            format=ReportFormat.PBIR,
            pages=[
                ReportPage(
                    name="pg1", display_name="Page 1",
                    visuals=[
                        Visual(name="v1", visual_type=VisualType.BAR_CHART),
                        Visual(name="v2", visual_type=VisualType.CARD, has_mobile_layout=True),
                    ],
                    filters=[{"f": 1}],
                    is_hidden=False,
                    has_drillthrough=False,
                ),
                ReportPage(
                    name="pg2", display_name="Page 2 (hidden)",
                    visuals=[],
                    is_hidden=True,
                    has_drillthrough=True,
                ),
            ],
            bookmarks=[Bookmark("bk1", "Bookmark 1", page_name="pg1")],
            extensions=ext,
            version="1.0",
        )
        return report.calculate_metrics()

    def test_round_trip_preserves_pages(self):
        original = self._make_full_metrics()
        restored = ReportMetrics.from_dict(original.to_dict())
        assert restored.total_pages == original.total_pages
        assert restored.hidden_pages_count == original.hidden_pages_count
        assert restored.pages_with_drillthrough == original.pages_with_drillthrough

    def test_round_trip_preserves_visuals(self):
        original = self._make_full_metrics()
        restored = ReportMetrics.from_dict(original.to_dict())
        assert restored.total_visuals == original.total_visuals
        assert restored.visuals_per_page_min == original.visuals_per_page_min
        assert restored.visuals_per_page_max == original.visuals_per_page_max
        assert restored.visuals_with_mobile_layout == original.visuals_with_mobile_layout

    def test_round_trip_preserves_bookmarks(self):
        original = self._make_full_metrics()
        restored = ReportMetrics.from_dict(original.to_dict())
        assert restored.has_bookmarks == original.has_bookmarks
        assert restored.total_bookmarks == original.total_bookmarks
        assert restored.bookmark_names == original.bookmark_names

    def test_round_trip_preserves_extensions(self):
        original = self._make_full_metrics()
        restored = ReportMetrics.from_dict(original.to_dict())
        assert restored.has_report_extensions == original.has_report_extensions
        assert restored.report_level_measures == original.report_level_measures

    def test_round_trip_preserves_complexity(self):
        original = self._make_full_metrics()
        restored = ReportMetrics.from_dict(original.to_dict())
        assert restored.complexity_index == pytest.approx(original.complexity_index)

    def test_to_dict_is_json_serializable(self):
        metrics = self._make_full_metrics()
        json_str = json.dumps(metrics.to_dict())
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["report_name"] == "RoundTripReport"


# ===========================================================================
# ReportGenerator
# ===========================================================================

class TestReportGenerator:

    def setup_method(self):
        self.gen = ReportGenerator()
        ext = ReportExtensions(measures=["RM1"], has_extensions=True)
        report = Report(
            name="GenTestReport",
            format=ReportFormat.PBIR,
            pages=[
                ReportPage(
                    name="pg1", display_name="Dashboard",
                    visuals=[
                        Visual(name="v1", visual_type=VisualType.BAR_CHART),
                        Visual(name="v2", visual_type=VisualType.MATRIX),
                    ],
                    filters=[],
                ),
            ],
            bookmarks=[Bookmark("bk1", "Main View")],
            extensions=ext,
        )
        self.metrics = report.calculate_metrics()

    def test_generate_json_is_valid_json(self):
        output = self.gen.generate_json(self.metrics)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_generate_json_has_report_name(self):
        data = json.loads(self.gen.generate_json(self.metrics))
        assert data["report_name"] == "GenTestReport"

    def test_generate_json_has_metrics_structure(self):
        data = json.loads(self.gen.generate_json(self.metrics))
        assert "metrics" in data
        assert "pages" in data["metrics"]
        assert "visuals" in data["metrics"]
        assert "bookmarks" in data["metrics"]

    def test_generate_markdown_is_string(self):
        output = self.gen.generate_markdown(self.metrics)
        assert isinstance(output, str)
        assert len(output) > 100

    def test_generate_markdown_has_header(self):
        output = self.gen.generate_markdown(self.metrics)
        assert "GenTestReport" in output
        assert "# " in output

    def test_generate_markdown_has_overview(self):
        output = self.gen.generate_markdown(self.metrics)
        assert "## Overview" in output

    def test_generate_markdown_has_visual_types(self):
        output = self.gen.generate_markdown(self.metrics)
        assert "## Visual Types Distribution" in output
        assert "barChart" in output

    def test_generate_markdown_has_bookmarks(self):
        output = self.gen.generate_markdown(self.metrics)
        assert "## Bookmarks" in output
        assert "Main View" in output

    def test_generate_markdown_has_report_extensions(self):
        output = self.gen.generate_markdown(self.metrics)
        assert "## Report Extensions" in output
        assert "RM1" in output

    def test_generate_markdown_has_advanced_metrics(self):
        output = self.gen.generate_markdown(self.metrics)
        assert "## Advanced Metrics" in output

    def test_generate_markdown_has_footer(self):
        output = self.gen.generate_markdown(self.metrics)
        assert "pbi-semantic-doc" in output

    def test_generate_text_is_string(self):
        output = self.gen.generate_text(self.metrics)
        assert isinstance(output, str)
        assert "GenTestReport" in output

    def test_generate_text_has_overview(self):
        output = self.gen.generate_text(self.metrics)
        assert "Overview:" in output
        assert "Pages:" in output
        assert "Visuals:" in output

    def test_generate_markdown_with_error(self):
        from pbi_semantic_doc.report_models import ReportMetrics
        metrics = ReportMetrics(error_message="Test error occurred")
        output = self.gen.generate_markdown(metrics)
        assert "Test error occurred" in output

    def test_generate_markdown_no_bookmarks_section_when_empty(self):
        from pbi_semantic_doc.report_models import ReportMetrics
        metrics = ReportMetrics(report_name="Empty", has_bookmarks=False, total_bookmarks=0)
        output = self.gen.generate_markdown(metrics)
        assert "## Bookmarks" not in output


# ===========================================================================
# CLI — report commands
# ===========================================================================

class TestCLIReport:

    def test_analyze_report_cli_returns_zero(self, tmp_path):
        out = tmp_path / "out.md"
        ret = cli_main([
            str(PBIR_REPORT),
            "--analyze-report",
            "--output", str(out),
            "--quiet",
        ])
        assert ret == 0

    def test_analyze_report_cli_creates_file(self, tmp_path):
        out = tmp_path / "out.md"
        cli_main([str(PBIR_REPORT), "--analyze-report", "--output", str(out), "--quiet"])
        assert out.exists()
        assert out.stat().st_size > 0

    def test_analyze_report_cli_json_format(self, tmp_path):
        out = tmp_path / "out.json"
        ret = cli_main([
            str(PBIR_REPORT),
            "--analyze-report",
            "--output", str(out),
            "--format", "json",
            "--quiet",
        ])
        assert ret == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "metrics" in data

    def test_analyze_report_cli_legacy(self, tmp_path):
        out = tmp_path / "out.md"
        ret = cli_main([
            str(LEGACY_REPORT),
            "--analyze-report",
            "--output", str(out),
            "--quiet",
        ])
        assert ret == 0

    def test_analyze_report_cli_nonexistent_path(self):
        ret = cli_main(["--analyze-report", "/nonexistent/path", "--quiet"])
        assert ret == 1

    def test_combined_analysis_cli(self, tmp_path):
        """Combined analysis requires both .SemanticModel and .Report in the same folder."""
        # Create a temp project folder with SemanticModel + Report
        project = tmp_path / "MyProject"
        sm = project / "MyModel.SemanticModel"
        (sm / "definition" / "tables").mkdir(parents=True)
        (sm / "definition" / "model.tmdl").write_text("model MyModel\n")
        rp = project / "MyReport.Report"
        rp.mkdir()
        # Copy pbir_report definition
        import shutil
        shutil.copytree(PBIR_REPORT / "definition", rp / "definition")

        out = tmp_path / "combined.md"
        ret = cli_main([
            str(project),
            "--combined",
            "--output", str(out),
            "--quiet",
        ])
        assert ret == 0
        assert out.exists()
