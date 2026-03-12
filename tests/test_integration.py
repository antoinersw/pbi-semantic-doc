"""Integration tests using the real 'Artificial Intelligence Sample' Power BI project."""

import subprocess
import sys
import json
import tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent
SAMPLE_DIR = ROOT / "examples" / "sample_model"
SEMANTIC_MODEL_DIR = SAMPLE_DIR / "Artificial Intelligence Sample.SemanticModel"
REPORT_DIR = SAMPLE_DIR / "Artificial Intelligence Sample.Report"


def _skip_if_missing():
    if not SAMPLE_DIR.exists():
        pytest.skip("examples/sample_model not found — skipping integration tests")


# ---------------------------------------------------------------------------
# Semantic model integration
# ---------------------------------------------------------------------------

class TestSemanticModelIntegration:
    def setup_method(self):
        _skip_if_missing()
        from pbi_semantic_doc.parser import TmdlParser
        self.parser = TmdlParser()
        self.model = self.parser.parse(SEMANTIC_MODEL_DIR / "definition")

    def test_model_name(self):
        assert self.model.name == "Artificial Intelligence Sample"

    def test_visible_table_count(self):
        visible = [t for t in self.model.tables if not t.is_hidden]
        assert len(visible) == 9

    def test_hidden_table_count(self):
        hidden = [t for t in self.model.tables if t.is_hidden]
        assert len(hidden) == 3

    def test_hidden_table_names(self):
        hidden_names = {t.name for t in self.model.tables if t.is_hidden}
        assert hidden_names == {"Industries", "Opportunity Forecast Adjustment", "Territories"}

    def test_measures_count(self):
        all_measures = [m for t in self.model.tables for m in t.measures]
        assert len(all_measures) == 22

    def test_relationships_count(self):
        assert len(self.model.relationships) == 12

    def test_visible_table_names(self):
        visible_names = {t.name for t in self.model.tables if not t.is_hidden}
        for expected in ("Accounts", "Cases", "Contacts", "Opportunities", "Owners", "Products"):
            assert expected in visible_names, f"Expected table '{expected}' not found"


class TestModelMetricsIntegration:
    def setup_method(self):
        _skip_if_missing()
        from pbi_semantic_doc.parser import TmdlParser
        self.model = TmdlParser().parse(SEMANTIC_MODEL_DIR / "definition")
        self.metrics = self.model.calculate_metrics()

    def test_metrics_model_name(self):
        assert self.metrics.model_name == "Artificial Intelligence Sample"

    def test_metrics_table_counts(self):
        assert self.metrics.total_tables == 12
        assert self.metrics.hidden_tables == 3

    def test_metrics_column_counts(self):
        assert self.metrics.total_columns == 135
        assert self.metrics.hidden_columns == 29

    def test_metrics_measures(self):
        assert self.metrics.total_measures == 22

    def test_metrics_relationships(self):
        assert self.metrics.total_relationships == 12
        assert self.metrics.inactive_relationships == 2

    def test_complexity_normalized(self):
        assert 0.0 <= self.metrics.complexity_index <= 1.0

    def test_complexity_approximate(self):
        # Observed: 0.245 for AI Sample; allow ±0.05
        assert abs(self.metrics.complexity_index - 0.245) < 0.05

    def test_avg_measure_complexity_normalized(self):
        assert 0.0 <= self.metrics.avg_measure_complexity <= 1.0


# ---------------------------------------------------------------------------
# Report integration
# ---------------------------------------------------------------------------

class TestReportIntegration:
    def setup_method(self):
        _skip_if_missing()
        from pbi_semantic_doc.report_parser import ReportParser
        self.parser = ReportParser()
        self.report = self.parser.parse(REPORT_DIR / "definition")
        self.metrics = self.report.calculate_metrics()

    def test_report_name(self):
        assert self.report.name == "Artificial Intelligence Sample"

    def test_page_count(self):
        assert self.metrics.total_pages == 3

    def test_visual_count(self):
        assert self.metrics.total_visuals == 235

    def test_bookmark_count(self):
        assert self.metrics.total_bookmarks == 17

    def test_no_hidden_pages(self):
        assert self.metrics.hidden_pages_count == 0

    def test_complexity_normalized(self):
        assert 0.0 <= self.metrics.complexity_index <= 1.0

    def test_complexity_approximate(self):
        # Observed value: 0.481; allow ±0.05 tolerance
        assert abs(self.metrics.complexity_index - 0.481) < 0.05

    def test_action_button_most_common(self):
        from pbi_semantic_doc.report_models import VisualType
        type_counts = {}
        for page in self.report.pages:
            for visual in page.visuals:
                key = visual.visual_type
                type_counts[key] = type_counts.get(key, 0) + 1
        most_common = max(type_counts, key=type_counts.get)
        assert most_common == VisualType.ACTION_BUTTON

    def test_action_button_count(self):
        from pbi_semantic_doc.report_models import VisualType
        count = sum(
            1 for page in self.report.pages
            for visual in page.visuals
            if visual.visual_type == VisualType.ACTION_BUTTON
        )
        assert count == 193

    def test_known_visual_types_present(self):
        from pbi_semantic_doc.report_models import VisualType
        all_types = {v.visual_type for page in self.report.pages for v in page.visuals}
        for vt in (VisualType.ACTION_BUTTON, VisualType.SHAPE, VisualType.TEXTBOX,
                   VisualType.BAR_CHART, VisualType.IMAGE):
            assert vt in all_types, f"Expected visual type {vt} not found"

    def test_report_format_is_pbir(self):
        from pbi_semantic_doc.report_models import ReportFormat
        assert self.report.format == ReportFormat.PBIR


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def setup_method(self):
        _skip_if_missing()

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, "-m", "pbi_semantic_doc.cli", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=ROOT
        )
        return result

    def test_cli_analyze_report_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = self._run(
            str(REPORT_DIR), "--analyze-report", "--format", "json",
            "--output", out, "--quiet"
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        assert data["report_name"] == "Artificial Intelligence Sample"
        assert data["metrics"]["pages"]["total"] == 3
        assert data["metrics"]["visuals"]["total"] == 235
        assert data["metrics"]["visuals"]["types"]["actionButton"] == 193

    def test_cli_analyze_report_markdown(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            out = f.name
        result = self._run(
            str(REPORT_DIR), "--analyze-report", "--format", "md",
            "--output", out, "--quiet"
        )
        assert result.returncode == 0, result.stderr
        content = Path(out).read_text(encoding="utf-8")
        assert "Artificial Intelligence Sample" in content
        assert "Pages" in content

    def test_cli_combined_markdown(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            out = f.name
        result = self._run(
            str(SAMPLE_DIR), "--combined", "--format", "md",
            "--output", out, "--quiet"
        )
        assert result.returncode == 0, result.stderr
        content = Path(out).read_text(encoding="utf-8")
        assert "Artificial Intelligence Sample" in content

    def test_cli_semantic_model_only(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            out = f.name
        result = self._run(
            str(SEMANTIC_MODEL_DIR), "--format", "md",
            "--output", out, "--quiet"
        )
        assert result.returncode == 0, result.stderr
        content = Path(out).read_text(encoding="utf-8")
        assert "Artificial Intelligence Sample" in content

    def test_cli_analyze_report_text_to_stdout(self):
        result = self._run(
            str(REPORT_DIR), "--analyze-report", "--format", "text", "--quiet"
        )
        assert result.returncode == 0, result.stderr
        assert "Artificial Intelligence Sample" in result.stdout
