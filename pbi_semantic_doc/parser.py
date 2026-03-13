"""
TMDL Parser — reads Power BI semantic model definition files
and returns structured Python objects ready for documentation generation.

Handles all real-world TMDL syntax variants:
- Properties with colon:  dataType: int64
- Properties with equals: description = 'text'
- Multi-line DAX expressions (3-tab indent)
- Backtick-fenced expressions (```...```)
- Escaped single quotes in measure names ('it''s fine')
- Relationships with dotted notation: fromColumn: Table.Column
- Auto-generated date tables (LocalDateTable_, DateTableTemplate_)
- Partition blocks with M / Power Query expressions
- RLS roles with table-level DAX filter expressions
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Tables to always exclude from documentation
# ---------------------------------------------------------------------------
EXCLUDED_TABLE_PREFIXES = (
    "LocalDateTable_",
    "DateTableTemplate_",
)

# ---------------------------------------------------------------------------
# Power Query connector name mapping  (M namespace → friendly label)
# Any namespace NOT in this dict is returned as-is (e.g. "AmazonRedshift")
# ---------------------------------------------------------------------------
CONNECTOR_NAMES: dict[str, str] = {
    "Sql":                       "SQL Server",
    "AzureSQL":                  "Azure SQL",
    "AzureSQLDataWarehouse":     "Azure Synapse",
    "AzureSQLManagedInstance":   "Azure SQL Managed Instance",
    "PostgreSQL":                "PostgreSQL",
    "MySql":                     "MySQL",
    "Oracle":                    "Oracle",
    "Teradata":                  "Teradata",
    "DB2":                       "IBM DB2",
    "ODBC":                      "ODBC",
    "OleDB":                     "OLE DB",
    "Snowflake":                 "Snowflake",
    "AmazonRedshift":            "Amazon Redshift",
    "GoogleBigQuery":            "Google BigQuery",
    "AzureDataExplorer":         "Azure Data Explorer",
    "Databricks":                "Databricks",
    "DeltaLake":                 "Delta Lake",
    "Fabric":                    "Microsoft Fabric",
    "PowerBI":                   "Power BI Dataset",
    "AnalysisServices":          "SSAS / AAS",
    "Excel":                     "Excel",
    "Csv":                       "CSV",
    "Json":                      "JSON",
    "Xml":                       "XML",
    "Parquet":                   "Parquet",
    "Folder":                    "Local Folder",
    "SharePoint":                "SharePoint",
    "AzureStorage":              "Azure Storage",
    "Web":                       "Web / REST API",
    "OData":                     "OData",
    "Salesforce":                "Salesforce",
    "Dynamics365":               "Dynamics 365",
    "GraphQL":                   "GraphQL",
    "SapHana":                   "SAP HANA",
    "SapBw":                     "SAP BW",
    "Sybase":                    "Sybase",
}

# Connectors that never support query folding (file-based / non-relational)
NEVER_FOLDS_CONNECTORS: set[str] = {
    "Excel", "CSV", "JSON", "XML", "Parquet",
    "Local Folder", "Web / REST API", "SharePoint",
}

# ---------------------------------------------------------------------------
# Step function catalog: M function name → (transform_type, folding_impact)
# folding_impact: True = folds,  False = breaks folding,  None = depends
# ---------------------------------------------------------------------------
STEP_FUNCTION_CATALOG: dict[str, tuple[str, Optional[bool]]] = {
    "Table.SelectRows":           ("filter",            True),
    "Table.SelectColumns":        ("select_columns",    True),
    "Table.RemoveColumns":        ("remove_columns",    True),
    "Table.RenameColumns":        ("rename",            True),
    "Table.TransformColumnTypes": ("type_cast",         True),
    "Table.Sort":                 ("sort",              True),
    "Table.Distinct":             ("distinct",          True),
    "Table.Skip":                 ("skip",              True),
    "Table.FirstN":               ("top_n",             True),
    "Table.Range":                ("range",             True),
    "Table.AddColumn":            ("add_column",        None),
    "Table.Group":                ("group_by",          None),
    "Table.NestedJoin":           ("merge",             None),
    "Table.Join":                 ("merge",             None),
    "Table.Combine":              ("append",            False),
    "Table.Pivot":                ("pivot",             False),
    "Table.Unpivot":              ("unpivot",           False),
    "Table.UnpivotOtherColumns":  ("unpivot",           False),
    "Table.ExpandTableColumn":    ("expand",            None),
    "Table.ExpandRecordColumn":   ("expand_record",     None),
    "Table.TransformColumns":     ("custom_transform",  False),
    "Table.ReplaceValue":         ("replace",           None),
    "Table.FillDown":             ("fill",              False),
    "Table.FillUp":               ("fill",              False),
    "Table.Buffer":               ("buffer",            False),
    "Table.Last":                 ("last",              None),
    "Table.PromoteHeaders":       ("promote_headers",   False),
    "Table.DemoteHeaders":        ("demote_headers",    False),
    "Table.SplitColumn":          ("split_column",      False),
    "Table.CombineColumns":       ("combine_columns",   False),
    "Value.NativeQuery":          ("native_query",      True),
}


# ---------------------------------------------------------------------------
# Data classes — base model
# ---------------------------------------------------------------------------

@dataclass
class Column:
    name: str
    data_type: str = "unknown"
    description: str = ""
    is_hidden: bool = False
    format_string: str = ""
    display_folder: str = ""


@dataclass
class Measure:
    name: str
    expression: str = ""
    description: str = ""
    format_string: str = ""
    display_folder: str = ""
    is_hidden: bool = False

    def complexity_score(self) -> float:
        """Return a 0–1 complexity score for this measure's DAX expression."""
        if not self.expression:
            return 0.0
        expr = self.expression.upper()

        # Length component (normalized to 500 chars)
        length_score = min(len(self.expression) / 500, 1.0)

        # Pattern count: each distinct category detected adds 1 (max meaningful = 5)
        patterns = 0
        if "CALCULATE(" in expr or "CALCULATETABLE(" in expr:
            patterns += 1
        if re.search(r"\bVAR\b", expr):
            patterns += 1
        ti_fns = ("TOTALYTD", "TOTALMTD", "SAMEPERIODLASTYEAR", "DATEADD", "PARALLELPERIOD",
                  "DATESYTD", "DATESMTD", "DATESQTD")
        if any(fn in expr for fn in ti_fns):
            patterns += 1
        if any(fn + "(" in expr for fn in ("SUMX", "AVERAGEX", "COUNTX", "MAXX", "MINX", "FILTER")):
            patterns += 1
        if any(fn + "(" in expr for fn in ("ALL", "ALLEXCEPT", "ALLSELECTED", "KEEPFILTERS")):
            patterns += 1
        if "USERELATIONSHIP(" in expr:
            patterns += 1
        if "RANKX(" in expr or "TOPN(" in expr:
            patterns += 1
        if "SWITCH(" in expr:
            patterns += 1

        pattern_score = min(patterns / 5, 1.0)
        return round(length_score * 0.4 + pattern_score * 0.6, 3)

    def auto_description(self) -> str:
        """Generate a lightweight description by inspecting the DAX expression."""
        expr = self.expression.upper()
        hints: list[str] = []

        # Aggregations
        for fn in ("SUMX", "AVERAGEX", "COUNTX", "MINX", "MAXX"):
            if fn + "(" in expr:
                hints.append(f"Iterator: {fn}")
                break
        else:
            for fn in ("SUM", "AVERAGE", "COUNT", "DISTINCTCOUNT", "MIN", "MAX", "COUNTA"):
                if fn + "(" in expr:
                    hints.append(f"Aggregation: {fn}")
                    break

        # Time intelligence
        ti_fns = (
            "DATESYTD", "DATESMTD", "DATESQTD",
            "SAMEPERIODLASTYEAR", "DATEADD", "PARALLELPERIOD",
            "TOTALYTD", "TOTALMTD", "TOTALQTD",
        )
        for fn in ti_fns:
            if fn in expr:
                hints.append("Time intelligence")
                break

        # Context modification
        if "CALCULATE(" in expr:
            hints.append("Uses CALCULATE")
        if "ALL(" in expr or "ALLEXCEPT(" in expr or "ALLSELECTED(" in expr:
            hints.append("Removes filters")
        if "KEEPFILTERS(" in expr:
            hints.append("Preserves filters")

        # Variables
        if re.search(r"\bVAR\b", expr):
            hints.append("Uses variables")

        # Division safety
        if "DIVIDE(" in expr:
            hints.append("Safe division")
        elif "/" in expr:
            hints.append("Division (check for zero)")

        # Conditional
        if "SWITCH(" in expr:
            hints.append("SWITCH logic")
        elif re.search(r"\bIF\b\s*\(", expr):
            hints.append("IF logic")

        # Ranking
        if "RANKX(" in expr:
            hints.append("Ranking")
        if "TOPN(" in expr:
            hints.append("Top-N filter")

        # Relationships
        if "USERELATIONSHIP(" in expr:
            hints.append("Inactive relationship")
        if "RELATED(" in expr or "RELATEDTABLE(" in expr:
            hints.append("Cross-table lookup")

        # Filter
        if "FILTER(" in expr:
            hints.append("Row filter")

        return " · ".join(hints) if hints else ""


# ---------------------------------------------------------------------------
# Data classes — Power Query / partitions
# ---------------------------------------------------------------------------

@dataclass
class ConnectorCall:
    """Represents the source connector extracted from an M expression."""
    function_name: str                                    # e.g. "Sql.Database"
    source_type: str                                      # e.g. "SQL Server" or raw namespace
    positional_params: list[str] = field(default_factory=list)   # e.g. ["srv", "db"]
    named_params: dict[str, str] = field(default_factory=dict)   # e.g. {"Query": "SELECT ..."}
    is_parameterized: bool = False   # True if any param is a PQ variable (not a string literal)


@dataclass
class MStep:
    """Represents a single step in a Power Query let...in expression."""
    name: str                           # step name (e.g. "FilteredRows")
    transform_type: str                 # normalized type (e.g. "filter", "merge")
    expression: str                     # raw M expression of this step
    folding_impact: Optional[bool] = None   # True=folds, False=breaks, None=depends


@dataclass
class IncrementalRefreshInfo:
    """Incremental refresh detection for a partition."""
    is_incremental: bool = False
    range_column: Optional[str] = None   # detected date/datetime column name
    has_range_start: bool = False
    has_range_end: bool = False


@dataclass
class MQueryAnalysis:
    """Full analysis of a Power Query M expression."""
    query_type: str                          # m_query | native_sql | direct_table | calculated | entity | unknown
    connector: Optional[ConnectorCall] = None
    step_count: int = 0
    steps: list[MStep] = field(default_factory=list)
    native_query: Optional[str] = None           # extracted SQL if present
    query_folding_status: str = "unknown"         # likely | at_risk | disabled | n/a | unknown
    query_folding_reason: str = ""
    has_merges: bool = False
    has_appends: bool = False
    has_custom_transforms: bool = False
    incremental_refresh: IncrementalRefreshInfo = field(default_factory=IncrementalRefreshInfo)
    unrecognized_functions: list[str] = field(default_factory=list)

    def complexity_score(self) -> float:
        """Return a 0–1 M query complexity score."""
        step_score = min(self.step_count / 20, 1.0) * 0.4
        transform_score = 0.0
        if self.has_merges:            transform_score += 0.3
        if self.has_appends:           transform_score += 0.2
        if self.native_query:          transform_score += 0.1
        if self.has_custom_transforms: transform_score += 0.2
        if self.unrecognized_functions: transform_score += 0.1
        return round(min(step_score + min(transform_score, 1.0) * 0.6, 1.0), 3)


@dataclass
class Partition:
    """Represents a table partition in a TMDL semantic model."""
    name: str
    mode: str = "import"      # import | directQuery | directLake
    type: str = "m"           # m | calculated | entity
    expression: str = ""      # raw M or DAX expression
    query_analysis: Optional[MQueryAnalysis] = None


@dataclass
class DataSourceSummary:
    """Aggregated data source across all tables sharing the same connection."""
    source_type: str
    server: Optional[str]     # server name, file path, or URL
    database: Optional[str]   # database name if applicable
    tables: list[str] = field(default_factory=list)
    modes: list[str] = field(default_factory=list)   # import/directQuery per partition


# ---------------------------------------------------------------------------
# Data classes — RLS
# ---------------------------------------------------------------------------

@dataclass
class RoleTablePermission:
    """A DAX filter applied to a table within an RLS role."""
    table_name: str
    filter_expression: str   # DAX expression, or "true" meaning no row filter


@dataclass
class Role:
    """An RLS role in the semantic model."""
    name: str
    model_permission: str = "read"   # read | readRefresh | admin | none
    table_permissions: list[RoleTablePermission] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Data classes — Table, Relationship, SemanticModel
# ---------------------------------------------------------------------------

@dataclass
class Table:
    name: str
    description: str = ""
    is_hidden: bool = False
    columns: list[Column] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)
    partitions: list[Partition] = field(default_factory=list)

    @property
    def effective_mode(self) -> str:
        """Return data access mode: import / directQuery / mixed / calculated / unknown."""
        if not self.partitions:
            return "unknown"
        modes = {p.mode for p in self.partitions if p.type not in ("calculated", "entity")}
        if not modes:
            return "calculated"
        return modes.pop() if len(modes) == 1 else "mixed"

    @property
    def is_incremental(self) -> bool:
        """True if any partition uses incremental refresh."""
        return any(
            p.query_analysis and p.query_analysis.incremental_refresh.is_incremental
            for p in self.partitions
            if p.query_analysis
        )


@dataclass
class Relationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str = "many-to-one"
    cross_filter: str = "single"
    is_active: bool = True


@dataclass
class ModelMetrics:
    """Computed metrics and complexity index for a SemanticModel."""
    model_name: str
    total_tables: int
    hidden_tables: int
    total_columns: int
    hidden_columns: int
    total_measures: int
    total_relationships: int
    inactive_relationships: int
    avg_measure_complexity: float   # 0–1, average per-measure DAX complexity
    complexity_index: float         # 0–1 normalized model complexity score

    # Reference maxima used for normalization
    _MAX_TABLES        = 30
    _MAX_MEASURES      = 150
    _MAX_RELATIONSHIPS = 50
    _MAX_COLUMNS       = 300

    @classmethod
    def from_model(cls, model: "SemanticModel") -> "ModelMetrics":
        visible = model.visible_tables
        all_measures = [m for t in model.tables for m in t.measures]
        total_cols = sum(len(t.columns) for t in model.tables)
        hidden_cols = sum(sum(1 for c in t.columns if c.is_hidden) for t in model.tables)

        avg_mc = (
            sum(m.complexity_score() for m in all_measures) / len(all_measures)
            if all_measures else 0.0
        )

        ci = round(
            min(len(visible)              / cls._MAX_TABLES,        1.0) * 0.20
            + min(len(all_measures)       / cls._MAX_MEASURES,      1.0) * 0.30
            + avg_mc                                                      * 0.30
            + min(len(model.relationships)/ cls._MAX_RELATIONSHIPS, 1.0) * 0.10
            + min(total_cols              / cls._MAX_COLUMNS,        1.0) * 0.10,
            3,
        )

        return cls(
            model_name=model.name,
            total_tables=len(model.tables),
            hidden_tables=len(model.tables) - len(visible),
            total_columns=total_cols,
            hidden_columns=hidden_cols,
            total_measures=len(all_measures),
            total_relationships=len(model.relationships),
            inactive_relationships=sum(1 for r in model.relationships if not r.is_active),
            avg_measure_complexity=round(avg_mc, 3),
            complexity_index=ci,
        )


@dataclass
class SemanticModel:
    name: str
    tables: list[Table] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience aggregates
    # ------------------------------------------------------------------

    @property
    def all_measures(self) -> list[tuple[str, Measure]]:
        """Returns (table_name, measure) pairs sorted by measure name."""
        pairs = [
            (t.name, m)
            for t in self.tables
            for m in t.measures
        ]
        return sorted(pairs, key=lambda x: x[1].name.lower())

    @property
    def visible_tables(self) -> list[Table]:
        return [t for t in self.tables if not t.is_hidden]

    @property
    def data_sources(self) -> list[DataSourceSummary]:
        """Aggregate unique data sources across all table partitions."""
        source_map: dict[tuple, DataSourceSummary] = {}

        for table in self.tables:
            for partition in table.partitions:
                qa = partition.query_analysis
                if not qa or not qa.connector:
                    continue
                conn = qa.connector
                server = conn.positional_params[0] if conn.positional_params else None
                database = conn.positional_params[1] if len(conn.positional_params) > 1 else None
                key = (conn.source_type, server, database)

                if key not in source_map:
                    source_map[key] = DataSourceSummary(
                        source_type=conn.source_type,
                        server=server,
                        database=database,
                    )
                if table.name not in source_map[key].tables:
                    source_map[key].tables.append(table.name)
                if partition.mode not in source_map[key].modes:
                    source_map[key].modes.append(partition.mode)

        return list(source_map.values())

    def calculate_metrics(self) -> ModelMetrics:
        return ModelMetrics.from_model(self)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class TmdlParser:
    """
    Parses a standard TMDL folder structure:

        <model_root>/
            definition/
                model.tmdl
                tables/
                    <TableName>.tmdl
                    ...
                relationships.tmdl   (optional)
                roles/
                    <RoleName>.tmdl  (optional)
    """

    def parse(self, model_root: Path) -> SemanticModel:
        definition_dir = self._find_definition_dir(model_root)
        model_name = self._extract_model_name(definition_dir / "model.tmdl")
        model = SemanticModel(name=model_name)

        tables_dir = definition_dir / "tables"
        if tables_dir.exists():
            for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
                table = self._parse_table(tmdl_file)
                if table and not self._is_excluded_table(table.name):
                    model.tables.append(table)

        rel_file = definition_dir / "relationships.tmdl"
        if rel_file.exists():
            model.relationships = self._parse_relationships(rel_file)
            # Filter out relationships involving excluded tables
            model.relationships = [
                r for r in model.relationships
                if not self._is_excluded_table(r.from_table)
                and not self._is_excluded_table(r.to_table)
            ]

        model.roles = self._parse_roles(definition_dir)

        return model

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_excluded_table(name: str) -> bool:
        return any(name.startswith(prefix) for prefix in EXCLUDED_TABLE_PREFIXES)

    def _find_definition_dir(self, root: Path) -> Path:
        """
        Accept either:
          - a folder that *is* the SemanticModel root  →  root/definition/
          - a folder that *contains* a .SemanticModel sub-folder
          - the definition/ folder itself
        """
        if (root / "model.tmdl").exists():
            return root

        candidate = root / "definition"
        if candidate.exists():
            return candidate

        for child in root.iterdir():
            if child.is_dir() and child.suffix == ".SemanticModel":
                defn = child / "definition"
                if defn.exists():
                    return defn

        raise FileNotFoundError(
            f"Cannot locate a TMDL definition folder under: {root}\n"
            "Expected one of:\n"
            "  <root>/definition/model.tmdl\n"
            "  <root>/<name>.SemanticModel/definition/model.tmdl"
        )

    def _extract_model_name(self, model_tmdl: Path) -> str:
        semantic_model_dir = model_tmdl.parent.parent
        folder_name = semantic_model_dir.name
        if folder_name.endswith(".SemanticModel"):
            return folder_name[: -len(".SemanticModel")]

        if not model_tmdl.exists():
            return folder_name
        text = model_tmdl.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^model\s+(.+)$", text, re.MULTILINE)
        if m:
            return m.group(1).strip().strip("'\"")
        return folder_name

    # ------------------------------------------------------------------
    # Table / column / measure / partition parsing
    # ------------------------------------------------------------------

    def _parse_table(self, path: Path) -> Optional[Table]:
        text = path.read_text(encoding="utf-8", errors="replace")
        table = Table(name=path.stem)

        m = re.search(r"^table\s+(.+)$", text, re.MULTILINE)
        if m:
            table.name = self._unescape_name(m.group(1).strip())

        table.is_hidden = bool(re.search(r"^\tisHidden\s*$", text, re.MULTILINE))

        table_line = next(
            (l for l in text.splitlines() if re.match(r"^table\s+", l.strip())),
            ""
        )
        table.description = (
            self._extract_triple_slash_comment(text, table_line)
            or self._prop(text, "description")
        )

        table.columns = self._parse_columns(text)
        table.measures = self._parse_measures(text)
        table.partitions = self._parse_partitions(text)

        return table

    def _parse_columns(self, text: str) -> list[Column]:
        columns = []
        for keyword, name_raw, block in self._split_top_level_blocks(text):
            if keyword != "column":
                continue

            col_line = f"\tcolumn {name_raw}"
            triple_desc = self._extract_triple_slash_comment(text, col_line)

            col = Column(
                name=self._unescape_name(name_raw),
                data_type=self._prop(block, "dataType") or "unknown",
                description=triple_desc or self._prop(block, "description"),
                is_hidden=bool(re.search(r"^\t\tisHidden\s*$", block, re.MULTILINE)),
                format_string=self._prop(block, "formatString"),
                display_folder=self._prop(block, "displayFolder"),
            )
            columns.append(col)
        return columns

    def _parse_measures(self, text: str) -> list[Measure]:
        measures = []
        for keyword, name_raw, block in self._split_top_level_blocks(text):
            if keyword != "measure":
                continue

            expression = self._extract_measure_expression(name_raw, text)
            measure_line = f"\tmeasure {name_raw}"
            triple_desc = self._extract_triple_slash_comment(text, measure_line)

            measure = Measure(
                name=self._unescape_name(name_raw),
                expression=expression,
                description=triple_desc or self._prop(block, "description"),
                format_string=self._prop(block, "formatString"),
                display_folder=self._prop(block, "displayFolder"),
                is_hidden=bool(re.search(r"^\t\tisHidden\s*$", block, re.MULTILINE)),
            )
            measures.append(measure)
        return measures

    def _extract_measure_expression(self, name_raw: str, full_text: str) -> str:
        """
        Extract DAX expression. Handles:
        1. Single-line:   measure 'Name' = SUM(T[C])
        2. Multi-line:    measure 'Name' =\n\t\t\tVAR x = ...\n\t\t\tRETURN x
        3. Backtick:      measure 'Name' = ```\n\t\t\tSUM(T[C])\n\t\t\t```
        """
        quoted_name = self._extract_quoted_name(name_raw)
        escaped = re.escape(quoted_name)
        pattern = rf"^\tmeasure\s+{escaped}\s*=\s*(.*?)$"
        m = re.search(pattern, full_text, re.MULTILINE)
        if not m:
            return ""

        first_line = m.group(1).strip()
        rest_start = m.end()

        if first_line.startswith("```"):
            return self._extract_backtick_expression(full_text, rest_start)

        continuation = self._extract_multiline_after(full_text, rest_start)
        if first_line and continuation:
            return (first_line + "\n" + continuation).strip()
        if first_line:
            return first_line
        return continuation

    def _extract_backtick_expression(self, text: str, start: int) -> str:
        rest = text[start:]
        end_match = re.search(r"^\s*```\s*$", rest, re.MULTILINE)
        content = rest[:end_match.start()] if end_match else rest
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        return "\n".join(lines)

    def _extract_multiline_after(self, text: str, start: int) -> str:
        """
        Collect DAX expression lines after the measure = line.
        Expression lines are indented with 3 tabs (properties use 2 tabs).
        Stops at a new top-level block or a 2-tab property line.
        """
        rest = text[start:]
        lines = []
        for line in rest.splitlines():
            if not line.strip():
                if lines:
                    lines.append("")
                continue

            if re.match(r"^\t(measure|column|partition|hierarchy|annotation)\b", line):
                break

            if re.match(r"^\t\t\w[\w.]+\s*[=:]", line) and not re.match(r"^\t\t\t", line):
                break

            if re.match(r"^\t\t", line):
                lines.append(line.strip())

        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Partition parsing
    # ------------------------------------------------------------------

    def _parse_partitions(self, text: str) -> list[Partition]:
        """Parse partition blocks from table TMDL text."""
        partitions = []
        for keyword, name_raw, block in self._split_top_level_blocks(text):
            if keyword != "partition":
                continue

            # Extract partition type (m, calculated, entity…) from "name = type"
            type_match = re.search(r"=\s*(\w+)\s*$", name_raw.strip())
            partition_type = type_match.group(1).lower() if type_match else "m"

            partition_name = self._unescape_name(name_raw)
            mode = self._prop(block, "mode") or "import"
            expression = self._extract_partition_source(block)
            analysis = self._analyze_m_query(expression, partition_type)

            partitions.append(Partition(
                name=partition_name,
                mode=mode,
                type=partition_type,
                expression=expression,
                query_analysis=analysis,
            ))
        return partitions

    def _extract_partition_source(self, block: str) -> str:
        """Extract the M/DAX source expression from a partition block."""
        # Use [ \t]* (not \s*) to avoid consuming newlines before the expression
        src_match = re.search(r"(?m)^\t\tsource[ \t]*=[ \t]*(.*?)$", block)
        if not src_match:
            return ""

        first_line = src_match.group(1).strip()
        rest_start = src_match.end()

        # Backtick-fenced
        if first_line.startswith("```"):
            return self._extract_backtick_expression(block, rest_start)

        # Collect multiline M expression (3+ tab indented lines)
        rest = block[rest_start:]
        lines = [first_line] if first_line else []
        for line in rest.splitlines():
            if not line.strip():
                if lines:
                    lines.append("")
                continue
            # Stop at a new 2-tab property
            if re.match(r"^\t\t\w", line) and not re.match(r"^\t\t\t", line):
                break
            # Stop at a new top-level block
            if re.match(r"^\t(column|measure|partition|hierarchy|annotation)\b", line):
                break
            if re.match(r"^\t\t\t", line):
                lines.append(line.strip())

        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # M expression analysis
    # ------------------------------------------------------------------

    def _analyze_m_query(self, expression: str, partition_type: str) -> MQueryAnalysis:
        """Full analysis of a partition's M or DAX expression."""
        if partition_type == "calculated":
            return MQueryAnalysis(query_type="calculated")
        if partition_type == "entity":
            return MQueryAnalysis(query_type="entity")
        if not expression.strip():
            return MQueryAnalysis(query_type="unknown")

        steps = self._parse_m_steps(expression)
        connector = self._detect_connector(steps)
        native_sql = self._extract_native_query(expression)
        incremental = self._detect_incremental_refresh(expression)
        folding_status, folding_reason = self._assess_query_folding(steps, connector)

        # Determine query type
        if native_sql:
            query_type = "native_sql"
        elif steps:
            non_trivial = [s for s in steps if s.transform_type not in (
                "source", "navigation", "type_cast"
            )]
            query_type = "direct_table" if not non_trivial else "m_query"
        else:
            query_type = "m_query"

        has_merges = any(s.transform_type == "merge" for s in steps)
        has_appends = any(s.transform_type == "append" for s in steps)
        has_custom = any(s.transform_type == "custom_transform" for s in steps)
        unrecognized = [
            s.transform_type.replace("unknown (", "").rstrip(")")
            for s in steps if s.transform_type.startswith("unknown")
        ]

        return MQueryAnalysis(
            query_type=query_type,
            connector=connector,
            step_count=len(steps),
            steps=steps,
            native_query=native_sql,
            query_folding_status=folding_status,
            query_folding_reason=folding_reason,
            has_merges=has_merges,
            has_appends=has_appends,
            has_custom_transforms=has_custom,
            incremental_refresh=incremental,
            unrecognized_functions=unrecognized,
        )

    def _parse_m_steps(self, expression: str) -> list[MStep]:
        """Parse steps from a let...in M expression."""
        expr = expression.strip()

        let_match = re.search(r"(?i)\blet\b", expr)
        if not let_match:
            return []

        body_start = let_match.end()
        body_text = expr[body_start:]

        # Find last top-level 'in' keyword
        in_match = re.search(r"(?m)^[ \t]*\bin\b[ \t]*$", body_text)
        if not in_match:
            # 'in' on same line as result expression
            in_match = re.search(r"(?m)^[ \t]*\bin\b[ \t]+\S", body_text)
        body = body_text[:in_match.start()] if in_match else body_text

        # Parse step definitions
        # Use [ \t]* (0+ whitespace) to handle both indented and stripped lines
        step_pat = re.compile(r'^([ \t]*)((?:\w+|#"[^"]+"))\s*=\s*(.*)')
        lines = body.splitlines()

        steps_raw: list[tuple[str, list[str]]] = []
        base_indent: Optional[int] = None

        for line in lines:
            m = step_pat.match(line)
            if m:
                indent = len(m.group(1).expandtabs(4))
                name = m.group(2)
                first_expr = m.group(3).strip().rstrip(",")

                if base_indent is None or indent <= base_indent:
                    base_indent = indent
                    steps_raw.append((name, [first_expr] if first_expr else []))
                else:
                    # Continuation of current step's expression
                    if steps_raw:
                        steps_raw[-1][1].append(line.strip().rstrip(","))
            elif steps_raw and line.strip():
                steps_raw[-1][1].append(line.strip().rstrip(","))

        result: list[MStep] = []
        for name, expr_lines in steps_raw:
            expr_text = "\n".join(l for l in expr_lines if l).strip()
            transform_type, folding_impact = self._classify_step(name, expr_text)
            result.append(MStep(
                name=name,
                transform_type=transform_type,
                expression=expr_text,
                folding_impact=folding_impact,
            ))
        return result

    def _classify_step(self, step_name: str, step_expr: str) -> tuple[str, Optional[bool]]:
        """Classify a step by looking for known M functions in its expression."""
        # Check known function catalog FIRST (takes priority over navigation heuristic)
        for fn_name, (transform_type, folding_impact) in STEP_FUNCTION_CATALOG.items():
            if (fn_name + "(") in step_expr or (fn_name + " (") in step_expr:
                return transform_type, folding_impact

        # Navigation pattern: {[Schema=..., Item=...]} or {[Name=...]}
        if re.search(r"\{[^}]*(?:Schema|Item|Name)\s*=", step_expr):
            return "navigation", True

        # Connector source step: Namespace.Function(...)
        if re.search(r"\b[A-Z][a-zA-Z]+\.[A-Z][a-zA-Z]+\s*\(", step_expr):
            return "source", True

        # Unknown — try to capture function name for transparency
        fn_match = re.search(r"\b([A-Z][a-zA-Z]+\.[A-Z][a-zA-Z]+)\s*\(", step_expr)
        if fn_match:
            return f"unknown ({fn_match.group(1)})", None

        return "unknown", None

    def _detect_connector(self, steps: list[MStep]) -> Optional[ConnectorCall]:
        """Detect the source connector from the steps (first 'source' step)."""
        for step in steps:
            if step.transform_type == "source":
                return self._parse_connector_call(step.expression)
        return None

    def _parse_connector_call(self, expr: str) -> Optional[ConnectorCall]:
        """Parse a connector function call and extract parameters generically."""
        m = re.match(r"([A-Za-z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*)\s*\(", expr)
        if not m:
            return None

        function_name = m.group(1)
        namespace = function_name.split(".")[0]
        source_type = CONNECTOR_NAMES.get(namespace, namespace)

        # Extract content inside outermost parens
        params_start = m.end()
        depth = 1
        pos = params_start
        while pos < len(expr) and depth > 0:
            if expr[pos] == "(":
                depth += 1
            elif expr[pos] == ")":
                depth -= 1
            pos += 1
        params_str = expr[params_start:pos - 1]

        positional, named, is_param = self._parse_call_params(params_str)

        return ConnectorCall(
            function_name=function_name,
            source_type=source_type,
            positional_params=positional,
            named_params=named,
            is_parameterized=is_param,
        )

    def _parse_call_params(self, params_str: str) -> tuple[list[str], dict[str, str], bool]:
        """Parse function parameters into positional and named."""
        positional: list[str] = []
        named: dict[str, str] = {}
        is_parameterized = False

        # Extract named params from [Key=Value] or [Key="Value"] record
        named_block = re.search(r"\[([^\]]*)\]", params_str)
        if named_block:
            for kv in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', named_block.group(1)):
                named[kv.group(1)] = kv.group(2)

        # Extract positional params (string literals before the record)
        pos_part = params_str[:named_block.start()] if named_block else params_str
        for p in re.findall(r'"([^"]*)"', pos_part):
            positional.append(p)

        # Detect PQ variable params (non-string, non-record tokens)
        remaining = re.sub(r'"[^"]*"', "", pos_part)
        remaining = remaining.strip().strip(",").strip()
        if remaining:
            is_parameterized = True
            for tok in re.split(r"\s*,\s*", remaining):
                tok = tok.strip()
                if tok:
                    positional.append(f"<{tok}>")

        return positional, named, is_parameterized

    def _extract_native_query(self, expression: str) -> Optional[str]:
        """Extract native SQL from M expression (3 patterns)."""
        # Pattern 1: Value.NativeQuery(source, "SELECT ...")
        m = re.search(
            r'Value\.NativeQuery\s*\([^,]+,\s*"([^"]+)"',
            expression, re.DOTALL
        )
        if m:
            return m.group(1).strip()

        # Pattern 2: [Query="SELECT ..."]
        m = re.search(r'\[Query\s*=\s*"([^"]+)"\]', expression, re.DOTALL)
        if m:
            return m.group(1).strip()

        return None

    def _detect_incremental_refresh(self, expression: str) -> IncrementalRefreshInfo:
        """Detect incremental refresh pattern (RangeStart/RangeEnd)."""
        has_start = bool(re.search(r"\bRangeStart\b", expression))
        has_end = bool(re.search(r"\bRangeEnd\b", expression))

        if not (has_start or has_end):
            return IncrementalRefreshInfo()

        # Detect the range column
        range_col: Optional[str] = None
        m = re.search(
            r"each\s+\[([^\]]+)\]\s*(?:>=?|<=?)\s*(?:RangeStart|RangeEnd)",
            expression,
        )
        if m:
            range_col = m.group(1)

        return IncrementalRefreshInfo(
            is_incremental=True,
            range_column=range_col,
            has_range_start=has_start,
            has_range_end=has_end,
        )

    def _assess_query_folding(
        self, steps: list[MStep], connector: Optional[ConnectorCall]
    ) -> tuple[str, str]:
        """Assess query folding status and return (status, reason)."""
        # File-based connectors → folding not applicable
        if connector and connector.source_type in NEVER_FOLDS_CONNECTORS:
            return "n/a", f"{connector.source_type} connector does not support query folding"

        # Definite folding killers
        for step in steps:
            if step.transform_type == "buffer":
                return "disabled", f"Table.Buffer() in step '{step.name}' stops query folding"
            if step.transform_type == "append":
                return "disabled", f"Table.Combine() in step '{step.name}' cannot fold back to source"
            if step.transform_type == "custom_transform":
                return "disabled", f"Custom M transform in step '{step.name}' breaks folding chain"
            if step.transform_type in ("pivot", "unpivot"):
                return "disabled", f"Pivot/Unpivot in step '{step.name}' cannot be folded"

        # At-risk operations
        merge_steps = [s for s in steps if s.transform_type == "merge"]
        if merge_steps:
            return "at_risk", f"Merge in step '{merge_steps[0].name}' — folding depends on connector"

        unknown_steps = [
            s for s in steps
            if s.transform_type.startswith("unknown") and s.folding_impact is None
        ]
        if unknown_steps:
            names = ", ".join(f"'{s.name}'" for s in unknown_steps[:3])
            return "at_risk", f"Unrecognized functions in steps: {names}"

        # All known foldable types
        foldable = {
            "filter", "select_columns", "remove_columns", "rename", "type_cast",
            "sort", "navigation", "source", "native_query", "distinct", "top_n",
            "skip", "range", "add_column",
        }
        if all(s.transform_type in foldable or s.folding_impact is True for s in steps):
            return "likely", "All steps are known foldable operations"

        return "at_risk", "Mix of foldable and non-deterministic steps"

    # ------------------------------------------------------------------
    # RLS role parsing
    # ------------------------------------------------------------------

    def _parse_roles(self, definition_dir: Path) -> list[Role]:
        """Parse RLS roles from roles/ directory or inline in model.tmdl."""
        roles: list[Role] = []

        roles_dir = definition_dir / "roles"
        if roles_dir.exists():
            for role_file in sorted(roles_dir.glob("*.tmdl")):
                role = self._parse_role_file(role_file)
                if role:
                    roles.append(role)
        else:
            # Fallback: roles declared inline in model.tmdl
            model_tmdl = definition_dir / "model.tmdl"
            if model_tmdl.exists():
                text = model_tmdl.read_text(encoding="utf-8", errors="replace")
                roles = self._parse_roles_from_text(text)

        return roles

    def _parse_role_file(self, path: Path) -> Optional[Role]:
        text = path.read_text(encoding="utf-8", errors="replace")
        return self._parse_role_text(text)

    def _parse_roles_from_text(self, text: str) -> list[Role]:
        """Parse all role blocks from a TMDL file."""
        roles = []
        blocks = re.split(r"^role\b", text, flags=re.MULTILINE)
        for block in blocks[1:]:
            role = self._parse_role_text("role" + block)
            if role:
                roles.append(role)
        return roles

    def _parse_role_text(self, text: str) -> Optional[Role]:
        """Parse a single role from TMDL text."""
        name_match = re.search(r"^role\s+(.+)$", text, re.MULTILINE)
        if not name_match:
            return None
        name = self._unescape_name(name_match.group(1).strip())

        perm_match = re.search(r"modelPermission\s*[=:]\s*(\w+)", text)
        model_permission = perm_match.group(1) if perm_match else "read"

        table_permissions: list[RoleTablePermission] = []
        for tp in re.finditer(
            r"^\s+tablePermission\s+(.+?)\s*=\s*(.+)$",
            text,
            re.MULTILINE,
        ):
            table_name = self._unescape_name(tp.group(1).strip())
            filter_expr = tp.group(2).strip()
            table_permissions.append(RoleTablePermission(
                table_name=table_name,
                filter_expression=filter_expr,
            ))

        return Role(
            name=name,
            model_permission=model_permission,
            table_permissions=table_permissions,
        )

    # ------------------------------------------------------------------
    # Relationship parsing
    # ------------------------------------------------------------------

    def _parse_relationships(self, path: Path) -> list[Relationship]:
        text = path.read_text(encoding="utf-8", errors="replace")
        relationships = []

        blocks = re.split(r"^relationship\b", text, flags=re.MULTILINE)
        for block in blocks[1:]:
            from_ref = re.search(r"fromColumn\s*[=:]\s*(.+)", block)
            to_ref   = re.search(r"toColumn\s*[=:]\s*(.+)", block)

            if not from_ref or not to_ref:
                continue

            from_table, from_col = self._split_dotted_ref(from_ref.group(1).strip())
            to_table, to_col     = self._split_dotted_ref(to_ref.group(1).strip())

            if not from_table:
                m = re.search(r"fromTable\s*[=:]\s*(.+)", block)
                if m:
                    from_table = m.group(1).strip().strip("'\"")
            if not to_table:
                m = re.search(r"toTable\s*[=:]\s*(.+)", block)
                if m:
                    to_table = m.group(1).strip().strip("'\"")

            if not from_table or not to_table:
                continue

            cross_filter_match = re.search(r"crossFilteringBehavior\s*[=:]\s*(\w+)", block)
            cardinality_match  = re.search(r"fromCardinality\s*[=:]\s*(\w+)", block)
            is_active_match    = re.search(r"isActive\s*[=:]\s*(true|false)", block, re.IGNORECASE)

            rel = Relationship(
                from_table=from_table,
                from_column=from_col,
                to_table=to_table,
                to_column=to_col,
                cardinality=cardinality_match.group(1) if cardinality_match else "many-to-one",
                cross_filter=cross_filter_match.group(1) if cross_filter_match else "single",
                is_active=(is_active_match.group(1).lower() != "false") if is_active_match else True,
            )
            relationships.append(rel)

        return relationships

    # ------------------------------------------------------------------
    # Tiny helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_quoted_name(name_raw: str) -> str:
        if not name_raw.startswith("'"):
            return name_raw.split()[0] if name_raw else name_raw

        i = 1
        while i < len(name_raw):
            if name_raw[i] == "'":
                if i + 1 < len(name_raw) and name_raw[i + 1] == "'":
                    i += 2
                    continue
                break
            i += 1
        return name_raw[:i + 1]

    @staticmethod
    def _split_dotted_ref(ref: str) -> tuple[str, str]:
        ref = ref.strip().strip("'\"")
        dot_idx = ref.find(".")
        if dot_idx == -1:
            return "", ref
        return ref[:dot_idx].strip(), ref[dot_idx + 1:].strip()

    def _split_top_level_blocks(self, text: str) -> list[tuple[str, str, str]]:
        """Split text into top-level blocks (column, measure, partition, etc.)"""
        results = []
        pattern = re.compile(
            r"^\t(column|measure|partition|hierarchy|annotation)\s*(.*?)$",
            re.MULTILINE,
        )
        matches = list(pattern.finditer(text))
        for i, match in enumerate(matches):
            keyword = match.group(1)
            name_raw = match.group(2).strip()
            block_start = match.end()
            block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[block_start:block_end]
            results.append((keyword, name_raw, block))
        return results

    @staticmethod
    def _unescape_name(raw: str) -> str:
        """Unescape TMDL name (remove quotes, handle escaped quotes)."""
        raw = re.sub(r"\s*=.*$", "", raw).strip()
        if raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1]
            raw = raw.replace("''", "'")
        return raw.strip()

    @staticmethod
    def _extract_triple_slash_comment(text: str, before_keyword: str) -> str:
        lines = text.splitlines()
        result_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(before_keyword.strip()):
                j = i - 1
                comment_lines = []
                while j >= 0:
                    prev = lines[j].strip()
                    if prev.startswith("///"):
                        comment_lines.insert(0, prev[3:].strip())
                        j -= 1
                    elif prev == "":
                        j -= 1
                        if j >= 0 and not lines[j].strip().startswith("///"):
                            break
                    else:
                        break
                if comment_lines:
                    result_lines = comment_lines
                break
        return " ".join(result_lines).strip()

    @staticmethod
    def _prop(text: str, prop: str) -> str:
        m = re.search(
            rf"^\s+{re.escape(prop)}\s*[=:]\s*['\"]?([^'\"\n]+)['\"]?\s*$",
            text,
            re.MULTILINE,
        )
        return m.group(1).strip() if m else ""
