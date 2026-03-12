"""
Report Generator — genera output formattato dalle metriche del report
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .report_models import ReportMetrics


class ReportGenerator:
    """
    Genera output formattato dalle metriche del report.
    
    Supporta tre formati:
    - JSON: per integrazione programmatica
    - Markdown: per documentazione human-readable
    - Text: per output console
    """
    
    def generate_json(self, metrics: ReportMetrics) -> str:
        """
        Genera output JSON.
        
        Args:
            metrics: ReportMetrics da serializzare
            
        Returns:
            Stringa JSON formattata
        """
        return json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False)
    
    def generate_markdown(self, metrics: ReportMetrics) -> str:
        """
        Genera documentazione Markdown strutturata.
        
        Sezioni:
        - Header con nome report e formato
        - Overview con metriche principali
        - Tabella distribuzione tipi visual
        - Sezione bookmarks (se presenti)
        - Sezione report extensions (se presenti)
        - Footer con timestamp
        
        Args:
            metrics: ReportMetrics da documentare
            
        Returns:
            Stringa Markdown formattata
        """
        sections: list[str] = []
        
        # Header
        sections.append(f"# {metrics.report_name} — Report Analysis")
        sections.append("")
        
        # Overview
        sections.append("## Overview")
        sections.append("")
        sections.append(f"| | |")
        sections.append(f"|---|---|")
        sections.append(f"| Report Format | {metrics.report_format} |")
        sections.append(f"| Total Pages | {metrics.total_pages} |")
        sections.append(f"| Hidden Pages | {metrics.hidden_pages_count} |")
        sections.append(f"| Total Visuals | {metrics.total_visuals} |")
        sections.append(f"| Visuals per Page (min/avg/max) | {metrics.visuals_per_page_min} / {metrics.visuals_per_page_avg:.1f} / {metrics.visuals_per_page_max} |")
        sections.append(f"| Bookmarks | {metrics.total_bookmarks} |")
        sections.append(f"| Report-Level Measures | {len(metrics.report_level_measures)} |")
        sections.append(f"| Complexity Index | {metrics.complexity_index:.0%} |")
        sections.append("")
        
        # Visual Types Distribution
        if metrics.visual_types_count:
            sections.append("## Visual Types Distribution")
            sections.append("")
            sections.append("| Visual Type | Count | Percentage |")
            sections.append("|---|---|---|")
            
            for vtype, count in sorted(metrics.visual_types_count.items(), key=lambda x: x[1], reverse=True):
                percentage = metrics.visual_types_percentage.get(vtype, 0.0)
                sections.append(f"| {vtype} | {count} | {percentage:.1f}% |")
            
            sections.append("")
        
        # Custom Visuals
        if metrics.custom_visuals:
            sections.append("## Custom Visuals")
            sections.append("")
            for custom_visual in metrics.custom_visuals:
                sections.append(f"- `{custom_visual}`")
            sections.append("")
        
        # Bookmarks
        if metrics.has_bookmarks:
            sections.append("## Bookmarks")
            sections.append("")
            sections.append(f"Total: {metrics.total_bookmarks}")
            sections.append("")
            if metrics.bookmark_names:
                for bookmark_name in metrics.bookmark_names:
                    sections.append(f"- {bookmark_name}")
                sections.append("")
        
        # Report Extensions
        if metrics.has_report_extensions:
            sections.append("## Report Extensions")
            sections.append("")
            sections.append(f"Report-level measures: {len(metrics.report_level_measures)}")
            sections.append("")
            if metrics.report_level_measures:
                for measure in metrics.report_level_measures:
                    sections.append(f"- `{measure}`")
                sections.append("")
        
        # Advanced Metrics
        sections.append("## Advanced Metrics")
        sections.append("")
        sections.append(f"| Metric | Value |")
        sections.append(f"|---|---|")
        sections.append(f"| Pages with Drillthrough | {metrics.pages_with_drillthrough} |")
        sections.append(f"| Total Filters | {metrics.total_filters} |")
        sections.append(f"| Visuals with Mobile Layout | {metrics.visuals_with_mobile_layout} |")
        sections.append("")
        
        # Error message if present
        if metrics.error_message:
            sections.append("## Errors")
            sections.append("")
            sections.append(f"⚠️ {metrics.error_message}")
            sections.append("")
        
        # Footer
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        sections.append("---")
        sections.append("")
        sections.append(f"*Generated by [pbi-semantic-doc](https://github.com/viciuslios/pbi-semantic-doc) · {ts}*")
        
        return "\n".join(sections) + "\n"
    
    def generate_text(self, metrics: ReportMetrics) -> str:
        """
        Genera output testuale per console.
        Formato compatto e leggibile.
        
        Args:
            metrics: ReportMetrics da formattare
            
        Returns:
            Stringa testuale formattata
        """
        lines: list[str] = []
        
        lines.append(f"Report Analysis: {metrics.report_name}")
        lines.append(f"Format: {metrics.report_format}")
        lines.append("")
        
        lines.append("Overview:")
        lines.append(f"  Pages: {metrics.total_pages} (hidden: {metrics.hidden_pages_count})")
        lines.append(f"  Visuals: {metrics.total_visuals} (avg per page: {metrics.visuals_per_page_avg:.1f})")
        lines.append(f"  Bookmarks: {metrics.total_bookmarks}")
        lines.append(f"  Report-Level Measures: {len(metrics.report_level_measures)}")
        lines.append(f"  Complexity Index: {metrics.complexity_index:.0%}")
        lines.append("")
        
        if metrics.visual_types_count:
            lines.append("Visual Types:")
            for vtype, count in sorted(metrics.visual_types_count.items(), key=lambda x: x[1], reverse=True):
                percentage = metrics.visual_types_percentage.get(vtype, 0.0)
                lines.append(f"  {vtype}: {count} ({percentage:.1f}%)")
            lines.append("")
        
        if metrics.custom_visuals:
            lines.append(f"Custom Visuals: {', '.join(metrics.custom_visuals)}")
            lines.append("")
        
        if metrics.error_message:
            lines.append(f"⚠️  Error: {metrics.error_message}")
            lines.append("")
        
        return "\n".join(lines)
