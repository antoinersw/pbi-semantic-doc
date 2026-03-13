"""pbi-semantic-doc — automatic documentation generator for Power BI semantic models and report analyzer."""

from .parser import (
    TmdlParser, SemanticModel, ModelMetrics,
    Table, Column, Measure, Relationship,
    Partition, ConnectorCall, MStep, MQueryAnalysis, IncrementalRefreshInfo,
    DataSourceSummary, Role, RoleTablePermission,
)
from .generator import MarkdownGenerator
from .report_parser import ReportParser
from .report_models import Report, ReportPage, Visual, Bookmark, ReportMetrics, ReportFormat, VisualType
from .report_generator import ReportGenerator

__version__ = "0.3.0"
__all__ = [
    # Semantic Model — core
    "TmdlParser",
    "SemanticModel",
    "ModelMetrics",
    "Table",
    "Column",
    "Measure",
    "Relationship",
    "MarkdownGenerator",
    # Semantic Model — Power Query / partitions
    "Partition",
    "ConnectorCall",
    "MStep",
    "MQueryAnalysis",
    "IncrementalRefreshInfo",
    "DataSourceSummary",
    # Semantic Model — RLS
    "Role",
    "RoleTablePermission",
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
