"""Command-line entry point for the synthetic Expense Tracker App."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from src.expense_tracker import (
    add_features,
    analyze_expenses,
    clean_expenses,
    create_visualizations,
    generate_insights,
    generate_synthetic_expenses,
    save_analysis_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser in one place so it is easy to discover and test."""
    parser = argparse.ArgumentParser(
        description="Generate and analyze synthetic expense data."
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=720,
        help="Number of synthetic raw rows to generate (default: 720).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible data (default: 42).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for CSV, JSON, and text outputs (default: outputs).",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("images"),
        help="Directory for PNG charts (default: images).",
    )
    parser.add_argument(
        "--no-quality-issues",
        action="store_true",
        help="Generate only valid rows and skip the cleaning exercise.",
    )
    return parser


def run_pipeline(
    rows: int = 720,
    seed: int = 42,
    output_dir: str | Path = "outputs",
    image_dir: str | Path = "images",
    include_quality_issues: bool = True,
) -> dict:
    """Run every pipeline step and return its in-memory results."""
    raw = generate_synthetic_expenses(
        n_rows=rows,
        seed=seed,
        include_quality_issues=include_quality_issues,
    )
    cleaned = clean_expenses(raw)
    featured = add_features(cleaned)
    analysis = analyze_expenses(featured)
    insights = generate_insights(featured, analysis)
    image_paths = create_visualizations(
        featured, analysis, output_dir=output_dir, image_dir=image_dir
    )
    output_paths = save_analysis_outputs(
        cleaned, analysis, insights, output_dir=output_dir
    )
    return {
        "raw": raw,
        "cleaned": cleaned,
        "featured": featured,
        "analysis": analysis,
        "insights": insights,
        "image_paths": image_paths,
        "output_paths": output_paths,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run the pipeline, and print a concise report."""
    args = build_parser().parse_args(argv)
    results = run_pipeline(
        rows=args.rows,
        seed=args.seed,
        output_dir=args.output_dir,
        image_dir=args.image_dir,
        include_quality_issues=not args.no_quality_issues,
    )
    kpis = results["analysis"]["kpis"]
    print("Expense Tracker pipeline complete")
    print(f"Rows: {len(results['raw']):,} raw -> {len(results['cleaned']):,} cleaned")
    print(
        f"Total spend: ${kpis['total_spend']:,.2f} | "
        f"Average transaction: ${kpis['average_transaction']:,.2f}"
    )
    print(
        f"Top category: {kpis['top_category'] or 'n/a'} | "
        f"Budget used: {kpis['budget_used_pct']:.1f}%"
    )
    print(
        f"Saved {len(results['output_paths'])} data files to "
        f"{Path(args.output_dir)} and {len(results['image_paths'])} charts to "
        f"{Path(args.image_dir)}."
    )
    print("Insights:")
    for insight in results["insights"][:3]:
        print(f"- {insight}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
