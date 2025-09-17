#!/usr/bin/env python3
"""Convenience script to regenerate growth projection artifacts."""
import argparse
import json
import os
from pathlib import Path

from modules.analyzer.projections import compute_projections_from_metrics
from modules.reporting.projections_report import write_projection_html
from modules.reporting.projections_plot import save_projection_png
from modules.reporting.projections_pdf import create_projections_pdf


def _ensure_cache_dirs(base: Path) -> None:
    (base / ".matplotlib_cache").mkdir(parents=True, exist_ok=True)
    (base / ".cache").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(base / ".matplotlib_cache"))
    os.environ.setdefault("XDG_CACHE_HOME", str(base / ".cache"))


def run(metrics_path: Path, out_json: Path, out_html: Path, out_png: Path,
        out_pdf: Path, work_dir: Path, end_month: str, license_cap: float) -> None:
    _ensure_cache_dirs(Path.cwd())

    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    work_dir.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    with metrics_path.open("r", encoding="utf-8") as handle:
        metrics = json.load(handle)

    projections = compute_projections_from_metrics(metrics, end_month=end_month)

    with out_json.open("w", encoding="utf-8") as handle:
        json.dump(projections, handle, indent=2)

    write_projection_html(projections, str(out_html))
    save_projection_png(projections, str(out_png))
    create_projections_pdf(str(out_json), str(out_pdf), str(work_dir), license_cap)

    print("Projections generated:")
    print(f"  JSON: {out_json}")
    print(f"  HTML: {out_html}")
    print(f"  PNG : {out_png}")
    print(f"  PDF : {out_pdf}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate growth projection outputs from metrics.json"
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("output/metrics.json"),
        help="Path to metrics.json (default: output/metrics.json)",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("output/projections.json"),
        help="Where to write projections JSON",
    )
    parser.add_argument(
        "--out-html",
        type=Path,
        default=Path("output/growth_projections.html"),
        help="Where to write the projections HTML report",
    )
    parser.add_argument(
        "--out-png",
        type=Path,
        default=Path("output/growth_projections.png"),
        help="Where to write the projections overview PNG",
    )
    parser.add_argument(
        "--out-pdf",
        type=Path,
        default=Path("output/growth_projections.pdf"),
        help="Where to write the projections PDF report",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("output"),
        help="Working directory for intermediate chart assets",
    )
    parser.add_argument(
        "--end-month",
        default="2026-12",
        help="Forecast horizon in YYYY-MM format (default: 2026-12)",
    )
    parser.add_argument(
        "--license-cap",
        type=float,
        default=15000.0,
        help="Assumed license ceiling for comparison (default: 15000)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(
        metrics_path=args.metrics,
        out_json=args.out_json,
        out_html=args.out_html,
        out_png=args.out_png,
        out_pdf=args.out_pdf,
        work_dir=args.work_dir,
        end_month=args.end_month,
        license_cap=args.license_cap,
    )


if __name__ == "__main__":
    main()
