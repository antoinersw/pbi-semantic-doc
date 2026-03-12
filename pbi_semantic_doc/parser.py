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
# Data classes
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


@dataclass
class Table:
    name: str
    description: str = ""
    is_hidden: bool = False
    columns: list[Column] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)


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

    # Convenience aggregates
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

        return model

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_excluded_table(name: str) -> bool:
        """Check if table should be excluded from documentation"""
        return any(name.startswith(prefix) for prefix in EXCLUDED_TABLE_PREFIXES)

    def _find_definition_dir(self, root: Path) -> Path:
        """
        Accept either:
          - a folder that *is* the SemanticModel root  →  root/definition/
          - a folder that *contains* a .SemanticModel sub-folder
          - the definition/ folder itself
        """
        # Already the definition folder?
        if (root / "model.tmdl").exists():
            return root

        # Standard layout: root/definition/
        candidate = root / "definition"
        if candidate.exists():
            return candidate

        # Maybe root contains a *.SemanticModel child
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
        # Prefer the .SemanticModel folder name (e.g. "MyModel.SemanticModel" → "MyModel")
        semantic_model_dir = model_tmdl.parent.parent  # definition/ → SemanticModel root
        folder_name = semantic_model_dir.name
        if folder_name.endswith(".SemanticModel"):
            return folder_name[: -len(".SemanticModel")]

        # Fallback: read from model.tmdl
        if not model_tmdl.exists():
            return folder_name
        text = model_tmdl.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^model\s+(.+)$", text, re.MULTILINE)
        if m:
            return m.group(1).strip().strip("'\"")
        return folder_name

    # ------------------------------------------------------------------
    # Table / column / measure parsing
    # ------------------------------------------------------------------

    def _parse_table(self, path: Path) -> Optional[Table]:
        text = path.read_text(encoding="utf-8", errors="replace")
        table = Table(name=path.stem)

        # Override name if explicitly declared
        m = re.search(r"^table\s+(.+)$", text, re.MULTILINE)
        if m:
            table.name = self._unescape_name(m.group(1).strip())

        table.is_hidden = bool(re.search(r"^\tisHidden\s*$", text, re.MULTILINE))

        # Description: prefer /// doc-comment above table keyword, fallback to description property
        table_line = next(
            (l for l in text.splitlines() if re.match(r"^table\s+", l.strip())),
            ""
        )
        table.description = (
            self._extract_triple_slash_comment(text, table_line)
            or self._prop(text, "description")
        )

        # Extract column and measure blocks
        table.columns = self._parse_columns(text)
        table.measures = self._parse_measures(text)

        return table

    def _parse_columns(self, text: str) -> list[Column]:
        columns = []
        for keyword, name_raw, block in self._split_top_level_blocks(text):
            if keyword != "column":
                continue

            # Build the keyword line to find the /// comment above it
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
        # Extract only the quoted name portion for the regex
        quoted_name = self._extract_quoted_name(name_raw)
        escaped = re.escape(quoted_name)
        pattern = rf"^\tmeasure\s+{escaped}\s*=\s*(.*?)$"
        m = re.search(pattern, full_text, re.MULTILINE)
        if not m:
            return ""

        first_line = m.group(1).strip()
        rest_start = m.end()

        # Backtick-fenced
        if first_line.startswith("```"):
            return self._extract_backtick_expression(full_text, rest_start)

        # Single-line with possible continuation
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

            # New top-level block
            if re.match(r"^\t(measure|column|partition|hierarchy|annotation)\b", line):
                break

            # 2-tab property (formatString:, lineageTag:, etc.) — stop
            if re.match(r"^\t\t\w[\w.]+\s*[=:]", line) and not re.match(r"^\t\t\t", line):
                break

            # Expression content at 2+ tab indent
            if re.match(r"^\t\t", line):
                lines.append(line.strip())

        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Relationship parsing
    # ------------------------------------------------------------------

    def _parse_relationships(self, path: Path) -> list[Relationship]:
        text = path.read_text(encoding="utf-8", errors="replace")
        relationships = []

        # Each relationship block starts with `relationship`
        blocks = re.split(r"^relationship\b", text, flags=re.MULTILINE)
        for block in blocks[1:]:
            from_ref = re.search(r"fromColumn\s*[=:]\s*(.+)", block)
            to_ref   = re.search(r"toColumn\s*[=:]\s*(.+)", block)

            if not from_ref or not to_ref:
                continue

            from_table, from_col = self._split_dotted_ref(from_ref.group(1).strip())
            to_table, to_col     = self._split_dotted_ref(to_ref.group(1).strip())

            # Fallback: separate fromTable / toTable properties (non-dotted notation)
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
        """
        Extract just the quoted name portion from name_raw.
        e.g. "'Giorni Indisponibilità' = ```"  →  "'Giorni Indisponibilità'"
             "'it''s' ="                        →  "'it''s'"
             "SimpleColumn"                     →  "SimpleColumn"
        """
        if not name_raw.startswith("'"):
            return name_raw.split()[0] if name_raw else name_raw

        i = 1
        while i < len(name_raw):
            if name_raw[i] == "'":
                if i + 1 < len(name_raw) and name_raw[i + 1] == "'":
                    i += 2  # skip escaped quote
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
        """Split text into top-level blocks (column, measure, etc.)"""
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
        """Unescape TMDL name (remove quotes, handle escaped quotes)"""
        # Strip = and everything after it (handles "'Name' = expr", "'Name' = ```", "'Name' =")
        raw = re.sub(r"\s*=.*$", "", raw).strip()
        if raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1]
            raw = raw.replace("''", "'")
        return raw.strip()

    @staticmethod
    def _extract_triple_slash_comment(text: str, before_keyword: str) -> str:
        """
        Extract /// doc-comment lines that appear immediately before a keyword line.
        Example:
            /// First line of description.
            /// Second line.
            column myColumn
        Returns the concatenated comment text, stripped of /// prefix.
        """
        lines = text.splitlines()
        result_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(before_keyword.strip()):
                # Walk backwards collecting /// lines
                j = i - 1
                comment_lines = []
                while j >= 0:
                    prev = lines[j].strip()
                    if prev.startswith("///"):
                        comment_lines.insert(0, prev[3:].strip())
                        j -= 1
                    elif prev == "":
                        j -= 1  # allow blank lines between comments
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
