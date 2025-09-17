import json
import os
from typing import Dict, List, Optional

import matplotlib.pyplot as plt


COLORS = {
    "actual": "#212529",
    "overlay": "#adb5bd",
    "linear": "#0d6efd",
    "decay": "#dc3545",
    "avg_last3": "#198754",
}


def _build_gap_ranges(actual: List[Dict]) -> List[Dict[str, int]]:
    gaps: List[Dict[str, int]] = []
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    for idx, point in enumerate(actual):
        if point.get("is_gap"):
            if start_idx is None:
                start_idx = idx
            end_idx = idx
        else:
            if start_idx is not None:
                gaps.append({"start": start_idx, "end": end_idx})
                start_idx = None
                end_idx = None
    if start_idx is not None:
        gaps.append({"start": start_idx, "end": end_idx})
    return gaps


def _plot(projections: Dict, title: str):
    actual = projections["actual"]
    overlay = projections.get("actual_overlay") or []

    months_actual = [p["month"] for p in actual]
    y_actual = [p["activated_instances"] for p in actual]

    # Build combined month labels for actual + forecast
    forecast_months: List[str] = []
    for sc in projections.get("scenarios", {}).values():
        forecast_months = [p["month"] for p in sc["series"]]
        break
    month_labels = months_actual + forecast_months

    x_actual = list(range(len(months_actual)))

    fig, ax = plt.subplots(figsize=(12, 6))

    # Highlight gap months with a light red band
    for gap in _build_gap_ranges(actual):
        ax.axvspan(gap["start"] - 0.5, gap["end"] + 0.5, color="#f8d7da", alpha=0.25, zorder=0)

    ax.plot(x_actual, y_actual, label="Actual (Current Year)", color=COLORS["actual"], linewidth=2.5)

    if overlay:
        y_overlay = [p["activated_instances"] for p in overlay]
        ax.plot(x_actual, y_overlay, label="Actual (All-Time)", color=COLORS["overlay"], linestyle=":", linewidth=2)

    start_idx = len(months_actual)
    for key in ["linear", "decay", "avg_last3"]:
        sc = projections.get("scenarios", {}).get(key)
        if not sc:
            continue
        months = [p["month"] for p in sc["series"]]
        vals = [p["activated_instances"] for p in sc["series"]]
        x_vals = list(range(start_idx, start_idx + len(months)))
        ax.plot(x_vals, vals, label=sc["name"], color=COLORS[key], linestyle="--")

    ax.set_title(title or "Activated Instances: Actuals and Projections")
    ax.set_xlabel("Month")
    ax.set_ylabel("Cumulative Activated Instances")
    ax.set_xticks(range(len(month_labels)))
    ax.set_xticklabels(month_labels, rotation=45, ha="right")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    return plt


def save_projection_png(projections: Dict, out_path: str, title: Optional[str] = None) -> None:
    fig = _plot(projections, title or "Activated Instances: Actuals and Projections")
    plt.savefig(out_path, dpi=160)
    plt.close()


def save_projection_subset_png(subset: Dict, out_path: str, title: Optional[str] = None) -> None:
    """Save a PNG for a subset projection dict with keys: actual, scenarios."""
    fig = _plot(subset, title or "Activated Instances: Actuals and Projections")
    plt.savefig(out_path, dpi=160)
    plt.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Save projections chart to PNG")
    parser.add_argument("--projections", default="output/projections.json")
    parser.add_argument("--out-png", default="output/growth_projections.png")
    args = parser.parse_args()

    with open(args.projections, "r", encoding="utf-8") as f:
        projections = json.load(f)
    save_projection_png(projections, args.out_png)
    print(f"Wrote PNG to {args.out_png}")


if __name__ == "__main__":
    main()
