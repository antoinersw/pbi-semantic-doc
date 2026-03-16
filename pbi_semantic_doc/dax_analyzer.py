"""
DAX Analyzer — Layer 1 (stateless, regex-based).

Extracts structured references from a single DAX expression:
  - Table[Column] and 'Quoted Table'[Column] references
  - [MeasureName] references (nested measures, no table prefix)
  - Tables removed by ALL() / ALLEXCEPT() / ALLSELECTED()
  - Aggregated base tables: SUM(Table[Col]), COUNTROWS(Table)
  - Time intelligence function usage
  - USERELATIONSHIP / TREATAS usage

No external DAX parser required — pure regex/string approach consistent
with the existing auto_description() and complexity_score() methods.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Time intelligence functions ───────────────────────────────────────────────
_TI_FUNCTIONS: frozenset[str] = frozenset({
    "TOTALYTD", "TOTALMTD", "TOTALQTD",
    "SAMEPERIODLASTYEAR", "DATEADD", "PARALLELPERIOD",
    "DATESYTD", "DATESMTD", "DATESQTD",
    "PREVIOUSYEAR", "PREVIOUSQUARTER", "PREVIOUSMONTH", "PREVIOUSDAY",
    "NEXTYEAR", "NEXTQUARTER", "NEXTMONTH", "NEXTDAY",
    "FIRSTDATE", "LASTDATE", "DATESBETWEEN", "DATESINPERIOD",
})

# ── Aggregation functions that "anchor" a measure to a base table ─────────────
_AGG_FUNCTIONS: frozenset[str] = frozenset({
    "SUM", "AVERAGE", "MIN", "MAX", "COUNT", "COUNTA", "COUNTBLANK",
    "DISTINCTCOUNT", "SUMX", "AVERAGEX", "MINX", "MAXX", "COUNTX",
    "COUNTROWS",
})

# ── Compiled regexes ───────────────────────────────────────────────────────────

# 'Table With Spaces'[Column]
_QUOTED_TABLE_COL_RE = re.compile(r"'([^']+)'\[([^\]]+)\]")

# Table[Column] — table name contains only word characters (no spaces)
# Negative lookbehind on ] prevents matching continuation like ][Col]
_UNQUOTED_TABLE_COL_RE = re.compile(
    r"(?<!\])\b([A-Za-z_\u00C0-\u024F][A-Za-z0-9_\u00C0-\u024F]*)\[([^\]]+)\]"
)

# [Reference] — any [bracket] span; Table[Col] positions excluded post-hoc
_BARE_REF_RE = re.compile(r"\[([^\]]+)\]")

# SUM/AVERAGE/MIN/MAX/etc.(Table[Col]) — captures the table name before [
_AGG_TABLE_COL_RE = re.compile(
    r"\b(?:" + "|".join(sorted(_AGG_FUNCTIONS, key=len, reverse=True)) + r")\s*"
    r"\(\s*(?:'([^']+)'|([A-Za-z_\u00C0-\u024F][A-Za-z0-9_\u00C0-\u024F]*))\s*\[",
    re.IGNORECASE,
)

# COUNTROWS(Table) — no column bracket
_COUNTROWS_TABLE_RE = re.compile(
    r"\bCOUNTROWS\s*\(\s*(?:'([^']+)'|([A-Za-z_\u00C0-\u024F][A-Za-z0-9_\u00C0-\u024F]*))\s*\)",
    re.IGNORECASE,
)

# SUMX(Table, expr) / AVERAGEX(Table, expr) / etc. — iterator functions where
# the table is the first argument followed by a comma (not a [ bracket)
_ITER_TABLE_RE = re.compile(
    r"\b(?:SUMX|AVERAGEX|MINX|MAXX|COUNTX|RANKX|TOPN|FILTER|ADDCOLUMNS|SELECTCOLUMNS)"
    r"\s*\(\s*(?:'([^']+)'|([A-Za-z_\u00C0-\u024F][A-Za-z0-9_\u00C0-\u024F]*))\s*,",
    re.IGNORECASE,
)

# ALL(Table) / ALL('Table') / ALL(Table[Col]) / ALL('Table'[Col])
_ALL_RE = re.compile(
    r"\bALL\s*\(\s*(?:'([^']+)'|([A-Za-z_\u00C0-\u024F][A-Za-z0-9_\u00C0-\u024F]*))\s*"
    r"(?:\[[^\]]*\])?\s*[,)]",
    re.IGNORECASE,
)

# ALLEXCEPT(Table, ...) / ALLSELECTED(Table)
_ALLEXCEPT_RE = re.compile(
    r"\bALL(?:EXCEPT|SELECTED)\s*\(\s*(?:'([^']+)'|([A-Za-z_\u00C0-\u024F][A-Za-z0-9_\u00C0-\u024F]*))\s*[,)]",
    re.IGNORECASE,
)


# ── Public dataclass ──────────────────────────────────────────────────────────

@dataclass
class DaxRefs:
    """
    Structured references extracted from a single DAX expression.

    All sets/lists contain raw name strings exactly as they appear in the DAX.
    Resolution against the actual model schema (e.g. verifying that a table
    name really exists) is done in the higher-level lineage.py layer.
    """

    # Tables that appear as the first argument of an aggregation:
    # SUM(Sales[Amount]) → "Sales";  COUNTROWS(Orders) → "Orders"
    aggregated_tables: set[str] = field(default_factory=set)

    # All Table[Column] pairs found anywhere in the expression
    # (includes those inside aggregations)
    table_column_refs: list[tuple[str, str]] = field(default_factory=list)

    # [MeasureName] references with no table prefix — these are nested measures
    # (column references like Table[Col] are excluded)
    nested_measure_names: list[str] = field(default_factory=list)

    # Tables explicitly cleared via ALL() / ALLEXCEPT() / ALLSELECTED()
    all_removed_tables: set[str] = field(default_factory=set)

    # True if any time-intelligence function is present in the expression
    uses_time_intelligence: bool = False

    # True if USERELATIONSHIP() is present (activates an inactive relationship)
    uses_inactive_relationship: bool = False

    # True if TREATAS() is present (creates a virtual relationship)
    uses_treatas: bool = False


# ── Public function ───────────────────────────────────────────────────────────

def extract_dax_refs(expression: str) -> DaxRefs:
    """
    Extract all structured references from a DAX expression.

    The result is deterministic and stateless — it knows nothing about the
    broader model schema.  Pass the result to ModelLineage.resolve() to get
    the full compatibility picture.
    """
    refs = DaxRefs()
    if not expression:
        return refs

    expr_upper = expression.upper()

    # ── Flags ────────────────────────────────────────────────────────────────
    refs.uses_time_intelligence = any(fn in expr_upper for fn in _TI_FUNCTIONS)
    refs.uses_inactive_relationship = "USERELATIONSHIP(" in expr_upper
    refs.uses_treatas = "TREATAS(" in expr_upper

    # ── Table[Column] references ──────────────────────────────────────────────
    # Collect the exact string positions of every [ that belongs to a Table[Col]
    # pattern, so we can later exclude them from the bare [Ref] scan.
    table_col_bracket_positions: set[int] = set()

    for m in _QUOTED_TABLE_COL_RE.finditer(expression):
        refs.table_column_refs.append((m.group(1), m.group(2)))
        table_col_bracket_positions.add(m.start(2) - 1)   # position of [

    for m in _UNQUOTED_TABLE_COL_RE.finditer(expression):
        refs.table_column_refs.append((m.group(1), m.group(2)))
        table_col_bracket_positions.add(m.start(2) - 1)

    # ── Aggregated base tables ────────────────────────────────────────────────
    for m in _AGG_TABLE_COL_RE.finditer(expression):
        table = m.group(1) or m.group(2)
        if table:
            refs.aggregated_tables.add(table.strip())

    for m in _COUNTROWS_TABLE_RE.finditer(expression):
        table = m.group(1) or m.group(2)
        if table:
            refs.aggregated_tables.add(table.strip())

    for m in _ITER_TABLE_RE.finditer(expression):
        table = m.group(1) or m.group(2)
        if table:
            refs.aggregated_tables.add(table.strip())

    # ── Bare [MeasureName] references ─────────────────────────────────────────
    # Any [bracket] that is NOT at a known Table[Col] position is a measure ref.
    seen_measures: set[str] = set()
    for m in _BARE_REF_RE.finditer(expression):
        if m.start() not in table_col_bracket_positions:
            name = m.group(1)
            if name not in seen_measures:
                seen_measures.add(name)
                refs.nested_measure_names.append(name)

    # ── ALL / ALLEXCEPT / ALLSELECTED ─────────────────────────────────────────
    for m in _ALL_RE.finditer(expression):
        table = m.group(1) or m.group(2)
        if table:
            refs.all_removed_tables.add(table.strip())

    for m in _ALLEXCEPT_RE.finditer(expression):
        table = m.group(1) or m.group(2)
        if table:
            refs.all_removed_tables.add(table.strip())

    return refs
