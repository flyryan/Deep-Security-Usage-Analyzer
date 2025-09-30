#!/usr/bin/env python3
"""
Generate Deep Security vs Vision One SPC cost comparison report.

This script orchestrates the complete cost comparison analysis, generating:
- Detailed cost calculations across multiple years
- Professional visualization charts
- Comprehensive HTML report
- Optional PDF report

Usage:
    python3 GenerateCostComparison.py
    python3 GenerateCostComparison.py --projections output/projections.json --config config.json
    python3 GenerateCostComparison.py --output-dir output --pdf
"""

import argparse
import json
import sys
from pathlib import Path

from modules.analyzer.cost_comparison import generate_cost_comparison_data
from modules.reporting.cost_comparison_plot import generate_all_charts
from modules.reporting.cost_comparison_report import write_cost_comparison_html


def run(projections_path: Path, config_path: Path, output_dir: Path) -> None:
    """
    Main execution flow for cost comparison report generation.

    Generates both HTML and PDF reports by default.

    Args:
        projections_path: Path to projections.json
        config_path: Path to config.json
        output_dir: Directory for output files
    """
    print("\n" + "=" * 70)
    print("  Deep Security vs Vision One SPC - Cost Comparison Report Generator")
    print("=" * 70 + "\n")

    # Validate inputs
    if not projections_path.exists():
        print(f"❌ Error: Projections file not found: {projections_path}")
        print("   Please run 'python3 GenerateProjections.py' first to generate projections.")
        sys.exit(1)

    if not config_path.exists():
        print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)

    # Verify pricing configuration exists
    with config_path.open('r', encoding='utf-8') as f:
        config = json.load(f)
        if 'pricing' not in config:
            print("❌ Error: Pricing configuration not found in config.json")
            print("   Please ensure config.json contains 'pricing' section.")
            sys.exit(1)

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = output_dir / "cost_comparison_charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Input files:")
    print(f"   Projections: {projections_path}")
    print(f"   Config:      {config_path}")
    print(f"\n📁 Output directory: {output_dir}\n")

    # Load projections data for charts
    with projections_path.open('r', encoding='utf-8') as f:
        projections_data = json.load(f)

    # Step 1: Generate cost comparison data
    print("=" * 70)
    print("STEP 1: Calculating Cost Comparisons")
    print("=" * 70)
    try:
        comparison_data = generate_cost_comparison_data(
            str(projections_path),
            str(config_path)
        )
        print("✅ Cost calculations completed successfully")
    except Exception as e:
        print(f"❌ Error during cost calculations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save raw data
    json_path = output_dir / "cost_comparison.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)
    print(f"✅ Data saved: {json_path}\n")

    # Step 2: Generate charts
    print("=" * 70)
    print("STEP 2: Generating Visualization Charts")
    print("=" * 70)
    try:
        generate_all_charts(comparison_data, projections_data, str(charts_dir))
        print()
    except Exception as e:
        print(f"❌ Error generating charts: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 3: Generate HTML report
    print("=" * 70)
    print("STEP 3: Generating HTML Report")
    print("=" * 70)
    html_path = output_dir / "cost_comparison.html"
    try:
        write_cost_comparison_html(comparison_data, str(html_path))
        print()
    except Exception as e:
        print(f"❌ Error generating HTML report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 4: PDF generation (always run by default)
    print("=" * 70)
    print("STEP 4: Generating PDF Report")
    print("=" * 70)
    pdf_path = output_dir / "cost_comparison.pdf"
    try:
        from modules.reporting.cost_comparison_pdf import create_cost_comparison_pdf
        create_cost_comparison_pdf(str(json_path), str(pdf_path), str(charts_dir))
        print(f"✅ PDF report: {pdf_path}\n")
    except ImportError:
        print("⚠️  PDF generation not available (module not implemented yet)")
        print("   HTML report is the primary deliverable.\n")
    except Exception as e:
        print(f"⚠️  Warning: PDF generation failed: {e}")
        print("   HTML report is still available.\n")

    # Summary
    print("\n" + "=" * 70)
    print("  ✅ COST COMPARISON REPORT GENERATED SUCCESSFULLY!")
    print("=" * 70 + "\n")

    print("📊 DELIVERABLES:")
    print(f"   📄 HTML Report:  {html_path}")
    print(f"   📑 PDF Report:   {pdf_path}")
    print(f"   📈 Charts:       {charts_dir}/")
    print(f"   📋 Data (JSON):  {json_path}")

    # Show key metrics
    yearly = comparison_data['yearly_comparison']
    print(f"\n💰 KEY FINDINGS:")
    print(f"   Year 1 Savings:  ${yearly['savings']['annual'][0]:,.0f}")
    if len(yearly['savings']['annual']) > 1:
        print(f"   Year 2 Savings:  ${yearly['savings']['annual'][1]:,.0f}")
    print(f"   {len(yearly['years'])}-Year Total:  ${yearly['savings']['cumulative'][-1]:,.0f}")
    print(f"   Endpoints 2026:  {yearly['endpoints'][0]:,}")

    print("\n" + "=" * 70)
    print(f"  Open the HTML report to view the complete analysis:")
    print(f"  file://{html_path.absolute()}")
    print("=" * 70 + "\n")


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate Deep Security vs Vision One SPC cost comparison report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (generates both HTML and PDF)
  python3 GenerateCostComparison.py

  # Specify custom paths
  python3 GenerateCostComparison.py --projections output/projections.json --config config.json

  # Custom output directory
  python3 GenerateCostComparison.py --output-dir custom_output/

For more information, see CLAUDE.md in the repository root.
        """
    )

    parser.add_argument(
        "--projections",
        type=Path,
        default=Path("output/projections.json"),
        help="Path to projections.json (default: output/projections.json)"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to config.json (default: config.json)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output/)"
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        run(
            projections_path=args.projections,
            config_path=args.config,
            output_dir=args.output_dir
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
