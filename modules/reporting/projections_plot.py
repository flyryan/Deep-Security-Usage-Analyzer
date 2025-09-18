import json
import os
from typing import Dict, List, Optional

import matplotlib.pyplot as plt

# Palette tuned to complement Trend Micro's brand red while keeping scenarios distinct.
COLORS = {
    "actual": "#1f2933",      # Charcoal for observed data
    "overlay": "#94a3b8",     # Muted slate for historical overlay
    "linear": "#d71920",      # Trend Micro red for linear growth
    "decay": "#6366f1",       # Indigo for conservative tapering
    "avg_last3": "#0ea5e9",   # Teal-blue for rolling average outlook
}

SCENARIO_LABELS = {
    "linear": "Linear Trend",
    "decay": "Geometric Decay (Most Conservative)",
    "avg_last3": "Rolling Avg Last 3 Months",
}

SCENARIO_ORDER = ["decay", "linear", "avg_last3"]


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

    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    fig.patch.set_facecolor("#f4f6fb")
    ax.set_facecolor("#ffffff")
    ax.grid(which="major", color="#e5e7eb", linewidth=0.8)
    ax.grid(which="minor", color="#f3f4f6", linewidth=0.5)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#d1d5db")
        ax.spines[spine].set_linewidth(1.1)

    ax.tick_params(colors="#4b5563", labelsize=9)

    # Fade the forecast area so the hand-off from actuals is obvious.
    if forecast_months:
        forecast_start = len(months_actual) - 0.5
        forecast_end = len(months_actual) + len(forecast_months) - 0.5
        ax.axvspan(forecast_start, forecast_end, color="#fee2e2", alpha=0.12, zorder=0)

    # Highlight gap months with a light red band
    for gap in _build_gap_ranges(actual):
        ax.axvspan(gap["start"] - 0.5, gap["end"] + 0.5, color="#fde68a", alpha=0.25, zorder=0)

    ax.plot(
        x_actual,
        y_actual,
        label="Actual (Current Year)",
        color=COLORS["actual"],
        linewidth=2.8,
        marker="o",
        markersize=5,
        markerfacecolor="#ffffff",
        markeredgewidth=1.2,
    )

    if overlay:
        y_overlay = [p["activated_instances"] for p in overlay]
        ax.plot(
            x_actual,
            y_overlay,
            label="Actual (All-Time)",
            color=COLORS["overlay"],
            linestyle=(0, (4, 3)),
            linewidth=1.8,
        )

    start_idx = len(months_actual)
    for key in SCENARIO_ORDER:
        sc = projections.get("scenarios", {}).get(key)
        if not sc:
            continue
        months = [p["month"] for p in sc["series"]]
        vals = [p["activated_instances"] for p in sc["series"]]
        x_vals = list(range(start_idx, start_idx + len(months)))
        display_name = SCENARIO_LABELS.get(key, sc.get("name", key))
        ax.plot(
            x_vals,
            vals,
            label=display_name,
            color=COLORS[key],
            linestyle="--",
            linewidth=2.4,
        )

    chart_title = "Activated Instances: Actual & Forecast"
    context = title.strip() if title else ""
    if context:
        chart_title = f"{chart_title} ({context})"

    ax.set_title(
        chart_title,
        loc="left",
        fontsize=16,
        fontweight="bold",
        color="#111827",
        pad=20,
    )
    ax.set_xlabel("Month", fontsize=11, color="#4b5563", labelpad=12)
    ax.set_ylabel("Cumulative Activated Instances", fontsize=11, color="#4b5563", labelpad=12)
    ax.set_xticks(range(len(month_labels)))
    ax.set_xticklabels(month_labels, rotation=45, ha="right")
    ax.margins(x=0.01)

    legend = ax.legend(
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        borderaxespad=0.6,
        ncol=1,
        frameon=True,
        fontsize=9,
        handlelength=3,
    )
    if legend:
        legend.get_frame().set_facecolor("#ffffff")
        legend.get_frame().set_edgecolor("#e5e7eb")

    fig.tight_layout(pad=2.0)
    return fig


def save_projection_png(projections: Dict, out_path: str, title: Optional[str] = None) -> None:
    fig = _plot(projections, title or "Activated Instances: Actual & Forecast")
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def save_projection_subset_png(subset: Dict, out_path: str, title: Optional[str] = None) -> None:
    """Save a PNG for a subset projection dict with keys: actual, scenarios."""
    fig = _plot(subset, title or "Activated Instances: Actual & Forecast")
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


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
