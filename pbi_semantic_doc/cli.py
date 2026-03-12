"""
CLI entry point for pbi-semantic-doc.

Usage:
    pbi-semantic-doc <model_path> [--output <path>] [--format md]

Examples:
    pbi-semantic-doc ./MyReport.SemanticModel
    pbi-semantic-doc ./MyReport.SemanticModel --output ./docs/MODEL.md
    pbi-semantic-doc . --output MODEL.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .parser import TmdlParser
from .generator import MarkdownGenerator
from .report_parser import ReportParser
from .report_generator import ReportGenerator


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pbi-semantic-doc",
        description="Generate documentation from a Power BI semantic model (TMDL format) or analyze report structure.",
    )
    p.add_argument(
        "model_path",
        metavar="PATH",
        help=(
            "Path to analyze. Accepts:\n"
            "  - a *.SemanticModel directory (for model documentation)\n"
            "  - a *.Report directory (for report analysis with --analyze-report)\n"
            "  - a .pbip project folder (for combined analysis with --combined)\n"
            "  - a parent folder containing the above"
        ),
    )
    p.add_argument(
        "--analyze-report",
        action="store_true",
        help="Analyze report structure instead of semantic model",
    )
    p.add_argument(
        "--combined",
        action="store_true",
        help="Analyze both semantic model and report (for .pbip projects)",
    )
    p.add_argument(
        "--output", "-o",
        metavar="OUTPUT_PATH",
        default=None,
        help="Where to write the output file. Defaults to MODEL_DOC.md or REPORT_ANALYSIS.md",
    )
    p.add_argument(
        "--format", "-f",
        choices=["md", "json", "text"],
        default="md",
        help="Output format. Default: md",
    )
    p.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress informational output.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    # Ensure stdout can handle Unicode on Windows (cp1252 terminals)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = build_parser().parse_args(argv)

    # Logica di routing
    if args.combined:
        return analyze_combined(args)
    elif args.analyze_report:
        return analyze_report(args)
    else:
        return analyze_semantic_model(args)


def analyze_semantic_model(args) -> int:
    """Analizza solo il modello semantico (comportamento originale)"""
    model_path = Path(args.model_path).resolve()
    if not model_path.exists():
        print(f"Error: path does not exist: {model_path}", file=sys.stderr)
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = model_path / "MODEL_DOC.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse
    try:
        parser = TmdlParser()
        model = parser.parse(model_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error while parsing: {exc}", file=sys.stderr)
        return 1

    # Generate
    generator = MarkdownGenerator()
    content = generator.generate(model)

    output_path.write_text(content, encoding="utf-8")

    if not args.quiet:
        tables = len(model.visible_tables)
        measures = sum(len(t.measures) for t in model.visible_tables)
        relationships = len(model.relationships)
        print(
            f"✓ Documentation generated: {output_path}\n"
            f"  Model   : {model.name}\n"
            f"  Tables  : {tables}\n"
            f"  Measures: {measures}\n"
            f"  Rels    : {relationships}"
        )

    return 0


def analyze_report(args) -> int:
    """Analizza solo il report"""
    report_path = Path(args.model_path).resolve()
    if not report_path.exists():
        print(f"Error: path does not exist: {report_path}", file=sys.stderr)
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        if args.format == "json":
            output_path = report_path / "REPORT_ANALYSIS.json"
        elif args.format == "text":
            output_path = None  # Print to console
        else:
            output_path = report_path / "REPORT_ANALYSIS.md"

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse
    try:
        parser = ReportParser()
        report = parser.parse(report_path)
        metrics = report.calculate_metrics()
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error while parsing: {exc}", file=sys.stderr)
        return 1

    # Generate
    generator = ReportGenerator()
    
    if args.format == "json":
        content = generator.generate_json(metrics)
    elif args.format == "text":
        content = generator.generate_text(metrics)
    else:  # markdown
        content = generator.generate_markdown(metrics)

    # Output
    if output_path:
        output_path.write_text(content, encoding="utf-8")
        if not args.quiet:
            print(f"✓ Report analysis saved: {output_path}")
    else:
        print(content)

    if not args.quiet and output_path:
        print(
            f"  Report  : {metrics.report_name}\n"
            f"  Format  : {metrics.report_format}\n"
            f"  Pages   : {metrics.total_pages}\n"
            f"  Visuals : {metrics.total_visuals}\n"
            f"  Complexity: {metrics.complexity_index:.0%}"
        )

    return 0


def analyze_combined(args) -> int:
    """Analizza sia modello semantico che report"""
    project_path = Path(args.model_path).resolve()
    if not project_path.exists():
        print(f"Error: path does not exist: {project_path}", file=sys.stderr)
        return 1

    # Trova cartelle .SemanticModel e .Report
    semantic_model_path = None
    report_path = None

    for child in project_path.iterdir():
        if child.is_dir():
            if ".SemanticModel" in child.name:
                semantic_model_path = child
            elif ".Report" in child.name:
                report_path = child

    if not semantic_model_path and not report_path:
        print(
            f"Error: No .SemanticModel or .Report folders found in: {project_path}\n"
            f"Expected a .pbip project structure",
            file=sys.stderr
        )
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        if args.format == "json":
            output_path = project_path / "COMBINED_ANALYSIS.json"
        else:
            output_path = project_path / "COMBINED_ANALYSIS.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse both
    model = None
    report_metrics = None

    if semantic_model_path:
        try:
            parser = TmdlParser()
            model = parser.parse(semantic_model_path)
        except Exception as exc:
            print(f"Warning: Failed to parse semantic model: {exc}", file=sys.stderr)

    if report_path:
        try:
            parser = ReportParser()
            report = parser.parse(report_path)
            report_metrics = report.calculate_metrics()
        except Exception as exc:
            print(f"Warning: Failed to parse report: {exc}", file=sys.stderr)

    # Generate combined output
    if args.format == "json":
        combined = {}
        if model:
            combined["semantic_model"] = {
                "name": model.name,
                "tables": len(model.visible_tables),
                "measures": sum(len(t.measures) for t in model.visible_tables),
                "relationships": len(model.relationships),
            }
        if report_metrics:
            combined["report"] = report_metrics.to_dict()
        
        content = json.dumps(combined, indent=2, ensure_ascii=False)
    else:  # markdown
        sections = []
        
        if model:
            gen = MarkdownGenerator()
            sections.append(gen.generate(model))
        
        if report_metrics:
            gen = ReportGenerator()
            sections.append(gen.generate_markdown(report_metrics))
        
        content = "\n\n---\n\n".join(sections)

    output_path.write_text(content, encoding="utf-8")

    if not args.quiet:
        print(f"✓ Combined analysis saved: {output_path}")
        if model:
            print(f"  Model: {model.name} ({len(model.visible_tables)} tables)")
        if report_metrics:
            print(f"  Report: {report_metrics.report_name} ({report_metrics.total_pages} pages)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
