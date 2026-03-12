"""
Report Models — dataclasses per rappresentare report Power BI
e calcolare metriche di complessità.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ReportFormat(Enum):
    """Formato del report Power BI"""
    PBIR = "pbir"
    PBIR_LEGACY = "pbir-legacy"


class VisualType(Enum):
    """Tipi di visualizzazioni Power BI"""
    BAR_CHART = "barChart"
    CLUSTERED_COLUMN_CHART = "clusteredColumnChart"
    CLUSTERED_BAR_CHART = "clusteredBarChart"
    COLUMN_CHART = "columnChart"
    LINE_CHART = "lineChart"
    AREA_CHART = "areaChart"
    COMBO_CHART = "lineClusteredColumnComboChart"
    PIE_CHART = "pieChart"
    DONUT_CHART = "donutChart"
    TABLE = "table"
    TABLE_EX = "tableEx"
    MATRIX = "matrix"
    PIVOT_TABLE = "pivotTable"
    CARD = "card"
    MULTI_ROW_CARD = "multiRowCard"
    SLICER = "slicer"
    MAP = "map"
    FILLED_MAP = "filledMap"
    SHAPE_MAP = "shapeMap"
    KPI = "kpi"
    GAUGE = "gauge"
    FUNNEL = "funnel"
    SCATTER = "scatter"
    TREEMAP = "treemap"
    WATERFALL = "waterfall"
    RIBBON = "ribbon"
    TEXTBOX = "textbox"
    SHAPE = "shape"
    IMAGE = "image"
    ACTION_BUTTON = "actionButton"
    PAGE_NAVIGATOR = "pageNavigator"
    BOOKMARK_NAVIGATOR = "bookmarkNavigator"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Visual:
    """Rappresenta una visualizzazione in una pagina"""
    name: str
    visual_type: VisualType
    custom_visual_name: Optional[str] = None
    has_mobile_layout: bool = False
    config: dict = field(default_factory=dict)
    
    @staticmethod
    def extract_type(config: dict) -> VisualType:
        """
        Estrae il tipo di visual dal campo config.
        
        Args:
            config: Dizionario config dal visual.json
            
        Returns:
            VisualType corrispondente
        """
        if not config:
            return VisualType.UNKNOWN
        
        # PBIR format: config.singleVisual.visualType
        single_visual = config.get("singleVisual", {})
        visual_type_str = single_visual.get("visualType", "")
        
        # PBIR-Legacy format: config potrebbe avere struttura diversa
        if not visual_type_str:
            visual_type_str = config.get("visualType", "")
        
        # Mapping string → enum (built automatically from enum values + aliases)
        type_mapping: dict[str, VisualType] = {vt.value: vt for vt in VisualType
                                               if vt not in (VisualType.CUSTOM, VisualType.UNKNOWN)}
        # Extra aliases
        type_mapping.update({
            "scatterChart": VisualType.SCATTER,
            "columnChart": VisualType.CLUSTERED_COLUMN_CHART,
            "lineClusteredColumnComboChart": VisualType.COMBO_CHART,
            "lineStackedColumnComboChart": VisualType.COMBO_CHART,
        })

        return type_mapping.get(visual_type_str, VisualType.UNKNOWN)


@dataclass
class ReportPage:
    """Rappresenta una pagina del report"""
    name: str
    display_name: str
    visuals: list[Visual] = field(default_factory=list)
    is_hidden: bool = False
    has_drillthrough: bool = False
    filters: list[dict] = field(default_factory=list)
    width: int = 0
    height: int = 0


@dataclass
class Bookmark:
    """Rappresenta un bookmark del report"""
    name: str
    display_name: str
    page_name: Optional[str] = None


@dataclass
class ReportExtensions:
    """Rappresenta le report extensions (es. report-level measures)"""
    measures: list[str] = field(default_factory=list)
    has_extensions: bool = False


@dataclass
class Report:
    """Rappresenta un report Power BI completo"""
    name: str
    format: ReportFormat
    pages: list[ReportPage] = field(default_factory=list)
    bookmarks: list[Bookmark] = field(default_factory=list)
    extensions: Optional[ReportExtensions] = None
    version: str = ""
    
    def calculate_metrics(self) -> ReportMetrics:
        """Calcola metriche aggregate dal report"""
        return ReportMetrics.from_report(self)


@dataclass
class ReportMetrics:
    """
    Metriche aggregate di complessità del report.
    Questa è la classe principale per l'output dell'analisi.
    """
    # Metriche di base
    total_pages: int = 0
    total_visuals: int = 0
    visuals_per_page_min: int = 0
    visuals_per_page_max: int = 0
    visuals_per_page_avg: float = 0.0
    
    # Tipi di visualizzazioni
    visual_types_count: dict[str, int] = field(default_factory=dict)
    visual_types_percentage: dict[str, float] = field(default_factory=dict)
    custom_visuals: list[str] = field(default_factory=list)
    
    # Bookmarks
    has_bookmarks: bool = False
    total_bookmarks: int = 0
    bookmark_names: list[str] = field(default_factory=list)
    
    # Report Extensions
    has_report_extensions: bool = False
    report_level_measures: list[str] = field(default_factory=list)
    
    # Metriche avanzate
    hidden_pages_count: int = 0
    pages_with_drillthrough: int = 0
    total_filters: int = 0
    visuals_with_mobile_layout: int = 0
    
    # Indice di complessità
    complexity_index: float = 0.0
    
    # Metadata
    report_name: str = ""
    report_format: str = ""
    error_message: Optional[str] = None
    
    @staticmethod
    def from_report(report: Report) -> ReportMetrics:
        """
        Calcola tutte le metriche da un oggetto Report.
        
        Args:
            report: Report da analizzare
            
        Returns:
            ReportMetrics con tutte le metriche calcolate
        """
        metrics = ReportMetrics()
        metrics.report_name = report.name
        metrics.report_format = report.format.value
        
        # Conteggi base
        metrics.total_pages = len(report.pages)
        metrics.total_visuals = sum(len(p.visuals) for p in report.pages)
        
        # Visuals per pagina
        if report.pages:
            visuals_counts = [len(p.visuals) for p in report.pages]
            metrics.visuals_per_page_min = min(visuals_counts)
            metrics.visuals_per_page_max = max(visuals_counts)
            metrics.visuals_per_page_avg = sum(visuals_counts) / len(visuals_counts)
        
        # Tipi di visualizzazioni
        type_counts: dict[str, int] = {}
        custom_visuals_set: set[str] = set()
        mobile_count = 0
        
        for page in report.pages:
            for visual in page.visuals:
                vtype = visual.visual_type.value
                type_counts[vtype] = type_counts.get(vtype, 0) + 1
                
                if visual.visual_type == VisualType.CUSTOM and visual.custom_visual_name:
                    custom_visuals_set.add(visual.custom_visual_name)
                    
                if visual.has_mobile_layout:
                    mobile_count += 1
        
        metrics.visual_types_count = type_counts
        if metrics.total_visuals > 0:
            metrics.visual_types_percentage = {
                vtype: (count / metrics.total_visuals) * 100
                for vtype, count in type_counts.items()
            }
        metrics.custom_visuals = sorted(custom_visuals_set)
        metrics.visuals_with_mobile_layout = mobile_count
        
        # Bookmarks
        metrics.has_bookmarks = len(report.bookmarks) > 0
        metrics.total_bookmarks = len(report.bookmarks)
        metrics.bookmark_names = [b.display_name for b in report.bookmarks]
        
        # Report Extensions
        if report.extensions:
            metrics.has_report_extensions = report.extensions.has_extensions
            metrics.report_level_measures = report.extensions.measures
        
        # Metriche avanzate
        metrics.hidden_pages_count = sum(1 for p in report.pages if p.is_hidden)
        metrics.pages_with_drillthrough = sum(1 for p in report.pages if p.has_drillthrough)
        metrics.total_filters = sum(len(p.filters) for p in report.pages)
        
        # Indice di complessità normalizzato 0-1
        # Soglie di riferimento per un report "massimamente complesso"
        _MAX_PAGES       = 50
        _MAX_VISUALS     = 300
        _MAX_BOOKMARKS   = 30
        _MAX_EXTENSIONS  = 10
        metrics.complexity_index = round(
            min(metrics.total_pages / _MAX_PAGES, 1.0)            * 0.25 +
            min(metrics.total_visuals / _MAX_VISUALS, 1.0)        * 0.45 +
            min(metrics.total_bookmarks / _MAX_BOOKMARKS, 1.0)    * 0.20 +
            min(len(metrics.report_level_measures) / _MAX_EXTENSIONS, 1.0) * 0.10,
            3
        )
        
        return metrics
    
    def to_dict(self) -> dict:
        """Serializza le metriche in un dizionario"""
        return {
            "report_name": self.report_name,
            "report_format": self.report_format,
            "metrics": {
                "pages": {
                    "total": self.total_pages,
                    "hidden": self.hidden_pages_count,
                    "with_drillthrough": self.pages_with_drillthrough,
                },
                "visuals": {
                    "total": self.total_visuals,
                    "per_page_min": self.visuals_per_page_min,
                    "per_page_max": self.visuals_per_page_max,
                    "per_page_avg": round(self.visuals_per_page_avg, 2),
                    "with_mobile_layout": self.visuals_with_mobile_layout,
                    "types": self.visual_types_count,
                    "types_percentage": {
                        k: round(v, 2) for k, v in self.visual_types_percentage.items()
                    },
                    "custom_visuals": self.custom_visuals,
                },
                "bookmarks": {
                    "has_bookmarks": self.has_bookmarks,
                    "total": self.total_bookmarks,
                    "names": self.bookmark_names,
                },
                "report_extensions": {
                    "has_extensions": self.has_report_extensions,
                    "report_level_measures": self.report_level_measures,
                },
                "filters": {
                    "total": self.total_filters,
                },
                "complexity_index": round(self.complexity_index, 2),
            },
            "error": self.error_message,
        }
    
    @staticmethod
    def from_dict(data: dict) -> ReportMetrics:
        """Deserializza le metriche da un dizionario"""
        metrics = ReportMetrics()
        metrics.report_name = data.get("report_name", "")
        metrics.report_format = data.get("report_format", "")
        
        m = data.get("metrics", {})
        
        # Pages
        pages = m.get("pages", {})
        metrics.total_pages = pages.get("total", 0)
        metrics.hidden_pages_count = pages.get("hidden", 0)
        metrics.pages_with_drillthrough = pages.get("with_drillthrough", 0)
        
        # Visuals
        visuals = m.get("visuals", {})
        metrics.total_visuals = visuals.get("total", 0)
        metrics.visuals_per_page_min = visuals.get("per_page_min", 0)
        metrics.visuals_per_page_max = visuals.get("per_page_max", 0)
        metrics.visuals_per_page_avg = visuals.get("per_page_avg", 0.0)
        metrics.visuals_with_mobile_layout = visuals.get("with_mobile_layout", 0)
        metrics.visual_types_count = visuals.get("types", {})
        metrics.visual_types_percentage = visuals.get("types_percentage", {})
        metrics.custom_visuals = visuals.get("custom_visuals", [])
        
        # Bookmarks
        bookmarks = m.get("bookmarks", {})
        metrics.has_bookmarks = bookmarks.get("has_bookmarks", False)
        metrics.total_bookmarks = bookmarks.get("total", 0)
        metrics.bookmark_names = bookmarks.get("names", [])
        
        # Report Extensions
        extensions = m.get("report_extensions", {})
        metrics.has_report_extensions = extensions.get("has_extensions", False)
        metrics.report_level_measures = extensions.get("report_level_measures", [])
        
        # Filters
        filters = m.get("filters", {})
        metrics.total_filters = filters.get("total", 0)
        
        # Complexity
        metrics.complexity_index = m.get("complexity_index", 0.0)
        
        # Error
        metrics.error_message = data.get("error")
        
        return metrics
