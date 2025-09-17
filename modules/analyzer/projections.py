import json
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime

import numpy as np


@dataclass
class MonthlyPoint:
    month: str
    activated_instances: float


def _month_seq(start_month: str, count: int) -> List[str]:
    dt = datetime.strptime(start_month, "%Y-%m")
    months = []
    y, m = dt.year, dt.month
    for _ in range(count):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def _next_month(month: str) -> str:
    y, m = map(int, month.split("-"))
    m += 1
    if m > 12:
        m = 1
        y += 1
    return f"{y:04d}-{m:02d}"


def linear_projection(x: np.ndarray, y: np.ndarray, future_steps: int) -> np.ndarray:
    coeffs = np.polyfit(x, y, 1)
    a, b = coeffs[0], coeffs[1]
    x_future = np.arange(x[-1] + 1, x[-1] + 1 + future_steps)
    y_future = a * x_future + b
    # Ensure cumulative non-decreasing
    y_future = np.maximum.accumulate(y_future)
    # Clip to be at least last actual
    y_future = np.maximum(y_future, y[-1])
    return y_future


def geometric_decay_projection(y: np.ndarray, future_steps: int) -> np.ndarray:
    # Work on increments, model inc_{t+1} = r * inc_t with r estimated robustly
    diffs = np.diff(y)
    diffs = diffs[diffs > 0]
    if len(diffs) < 2:
        # Not enough signal; fall back to flat increment of last observed (or zero)
        last_inc = diffs[-1] if len(diffs) == 1 else 0.0
        return y[-1] + np.cumsum(np.full(future_steps, last_inc))

    ratios = diffs[1:] / np.where(diffs[:-1] == 0, 1e-9, diffs[:-1])
    # Use median ratio to avoid outlier swings
    r = float(np.median(ratios))
    # Dampen extreme ratios into [0.6, 0.95]
    r = max(0.6, min(0.95, r))

    last = float(y[-1])
    inc = float(np.mean(diffs[-2:]))  # start from mean of last 2 months to smooth volatility
    preds = []
    for _ in range(future_steps):
        inc = inc * r
        last = last + inc
        preds.append(last)
    return np.array(preds)


def avg_last3_projection(y: np.ndarray, future_steps: int) -> np.ndarray:
    diffs = np.diff(y)
    inc = float(np.mean(diffs[-3:])) if len(diffs) >= 3 else float(np.mean(diffs)) if len(diffs) else 0.0
    preds = y[-1] + np.cumsum(np.full(future_steps, inc))
    return preds


def _compute_from_monthly(monthly: List[Dict], end_month: str) -> Dict:
    if not monthly:
        raise ValueError("No monthly data provided.")
    months = [m["month"] for m in monthly]
    values_display = [float(m["activated_instances"]) for m in monthly]
    values_overlay = [float(m.get("activated_instances_all_time", m["activated_instances"])) for m in monthly]
    gap_flags = [bool(m.get("is_gap")) for m in monthly]

    y_model = np.array(values_overlay, dtype=float)
    x = np.arange(1, len(y_model) + 1)

    last_month = months[-1]
    forecast_months: List[str] = []
    m = _next_month(last_month)
    while m <= end_month:
        forecast_months.append(m)
        m = _next_month(m)
    future_steps = len(forecast_months)
    if future_steps <= 0:
        raise ValueError("end_month is not after last data point.")

    lin = linear_projection(x, y_model, future_steps)
    dec = geometric_decay_projection(y_model, future_steps)
    avg = avg_last3_projection(y_model, future_steps)

    # Adjust projections to align with displayed (current-year) baseline
    display_last = values_display[-1]
    model_last = values_overlay[-1]
    offset = display_last - model_last
    lin_display = np.maximum(lin + offset, display_last)
    dec_display = np.maximum(dec + offset, display_last)
    avg_display = np.maximum(avg + offset, display_last)

    def to_series(pred: np.ndarray) -> List[Dict[str, float]]:
        return [{"month": forecast_months[i], "activated_instances": float(pred[i])} for i in range(len(pred))]

    def value_at(series: List[Dict[str, float]], target_month: str) -> float:
        for p in series:
            if p["month"] == target_month:
                return float(p["activated_instances"])
        return float("nan")

    scenarios = {
        "linear": {"name": "Linear Trend", "series": to_series(lin_display)},
        "decay": {"name": "Geometric Decay (Conservative)", "series": to_series(dec_display)},
        "avg_last3": {"name": "Rolling Avg Last 3 Months (Optimistic)", "series": to_series(avg_display)},
    }
    for _, sc in scenarios.items():
        series = sc["series"]
        sc["EOY_2025"] = value_at(series, "2025-12")
        sc["EOY_2026"] = value_at(series, "2026-12")

    gap_ranges: List[Dict[str, str]] = []
    gap_start = None
    gap_end = None
    for idx, flag in enumerate(gap_flags):
        if flag:
            if gap_start is None:
                gap_start = months[idx]
            gap_end = months[idx]
        else:
            if gap_start is not None:
                gap_ranges.append({"start": gap_start, "end": gap_end})
                gap_start = None
                gap_end = None
    if gap_start is not None:
        gap_ranges.append({"start": gap_start, "end": gap_end})

    return {
        "basis_last_month": last_month,
        "actual": [
            {
                "month": months[i],
                "activated_instances": float(values_display[i]),
                "is_gap": gap_flags[i],
            }
            for i in range(len(months))
        ],
        "actual_overlay": [
            {
                "month": months[i],
                "activated_instances": float(values_overlay[i]),
                "is_gap": gap_flags[i],
            }
            for i in range(len(months))
        ],
        "data_gaps": gap_ranges,
        "scenarios": scenarios,
    }


def compute_projections_from_metrics(metrics: Dict, end_month: str = "2026-12") -> Dict:
    monthly_overall = metrics.get("monthly", {}).get("data", [])
    if not monthly_overall:
        raise ValueError("No monthly data found in metrics.")

    result = _compute_from_monthly(monthly_overall, end_month=end_month)

    # Optional breakdowns (if present)
    by_cat = metrics.get("by_service_category", {})
    out_breakdowns = {}
    for cat in ("common services", "mission partners"):
        cat_m = by_cat.get(cat, {}).get("monthly", {}).get("data", [])
        if cat_m:
            out_breakdowns[cat] = _compute_from_monthly(cat_m, end_month=end_month)
    if out_breakdowns:
        result["by_category"] = out_breakdowns

    # By cloud provider (AWS/Azure/GCP/OCI, etc.)
    by_cp = metrics.get("by_cloud_provider", {})
    out_by_cp = {}
    for cp, cp_metrics in by_cp.items():
        cp_monthly = cp_metrics.get("monthly", {}).get("data", [])
        if cp_monthly:
            out_by_cp[cp] = _compute_from_monthly(cp_monthly, end_month=end_month)
    if out_by_cp:
        result["by_cloud_provider"] = out_by_cp

    # By service category and cloud provider
    by_cat_cp = metrics.get("by_service_category_and_cloud_provider", {})
    out_by_cat_cp = {}
    for key, scp_metrics in by_cat_cp.items():
        scp_monthly = scp_metrics.get("monthly", {}).get("data", [])
        if scp_monthly:
            out_by_cat_cp[key] = _compute_from_monthly(scp_monthly, end_month=end_month)
    if out_by_cat_cp:
        result["by_category_and_cloud_provider"] = out_by_cat_cp
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compute growth projections from metrics.json")
    parser.add_argument("--metrics", default="output/metrics.json", help="Path to metrics.json")
    parser.add_argument("--out-json", default="output/projections.json", help="Where to write projections JSON")
    parser.add_argument("--end-month", default="2026-12", help="Forecast through this YYYY-MM")
    args = parser.parse_args()

    with open(args.metrics, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    proj = compute_projections_from_metrics(metrics, end_month=args.end_month)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(proj, f, indent=2)

    print(f"Wrote projections to {args.out_json}")


if __name__ == "__main__":
    main()
