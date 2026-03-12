"""pbi-semantic-doc — automatic documentation generator for Power BI semantic models and report analyzer."""

from .parser import TmdlParser, SemanticModel, ModelMetrics, Table, Column, Measure, Relationship
from .generator import MarkdownGenerator
from .report_parser import ReportParser
from .report_models import Report, ReportPage, Visual, Bookmark, ReportMetrics, ReportFormat, VisualType
from .report_generator import ReportGenerator

__version__ = "0.2.0"
__all__ = [
    # Semantic Model
    "TmdlParser",
    "SemanticModel",
    "ModelMetrics",
    "Table",
    "Column",
    "Measure",
    "Relationship",
    "MarkdownGenerator",
    # Report Analysis
    "ReportParser",
    "Report",
    "ReportPage",
    "Visual",
    "Bookmark",
    "ReportMetrics",
    "ReportFormat",
    "VisualType",
    "ReportGenerator",
]
