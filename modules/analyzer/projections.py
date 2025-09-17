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


def _value_at_series(series: List[Dict[str, float]], target_month: str) -> float:
    for point in series:
        if point["month"] == target_month:
            return float(point["activated_instances"])
    return float("nan")


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

    scenarios = {
        "linear": {"name": "Linear Trend", "series": to_series(lin_display)},
        "decay": {"name": "Geometric Decay (Conservative)", "series": to_series(dec_display)},
        "avg_last3": {"name": "Rolling Avg Last 3 Months (Optimistic)", "series": to_series(avg_display)},
    }
    for _, sc in scenarios.items():
        series = sc["series"]
        sc["EOY_2025"] = _value_at_series(series, "2025-12")
        sc["EOY_2026"] = _value_at_series(series, "2026-12")

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


def _clamp_projection_to_parents(projection: Dict, parents: List[Dict]) -> None:
    """Clamp projection scenario values so they never exceed parent projections."""
    valid_parents = [p for p in parents if p and p.get("scenarios")]
    if not valid_parents:
        return

    for scenario_key, scenario in projection.get("scenarios", {}).items():
        parent_caps: Dict[str, float] = {}
        for parent in valid_parents:
            parent_scenario = parent.get("scenarios", {}).get(scenario_key)
            if not parent_scenario:
                continue
            for entry in parent_scenario.get("series", []):
                month = entry["month"]
                cap = entry["activated_instances"]
                if month not in parent_caps:
                    parent_caps[month] = cap
                else:
                    parent_caps[month] = min(parent_caps[month], cap)

        for entry in scenario.get("series", []):
            cap = parent_caps.get(entry["month"])
            if cap is not None and entry["activated_instances"] > cap:
                entry["activated_instances"] = cap

        scenario["EOY_2025"] = _value_at_series(scenario.get("series", []), "2025-12")
        scenario["EOY_2026"] = _value_at_series(scenario.get("series", []), "2026-12")


def _lookup_with_carry(series: List[Dict[str, float]], month: str) -> float:
    last = 0.0
    for point in series:
        if point["month"] > month:
            break
        last = float(point["activated_instances"])
        if point["month"] == month:
            return last
    return last


def _aggregate_overall_from_clouds(overall: Dict, clouds: Dict[str, Dict]) -> None:
    if not overall or not overall.get("actual") or not clouds:
        return

    months = [entry["month"] for entry in overall["actual"]]

    # Sum actuals with carry-forward for months a cloud lacks
    actual_totals = []
    for month in months:
        total = 0.0
        for cloud in clouds.values():
            total += _lookup_with_carry(cloud.get("actual", []), month)
        actual_totals.append(total)
    for entry, value in zip(overall["actual"], actual_totals):
        entry["activated_instances"] = value

    if overall.get("actual_overlay"):
        overlay_totals = []
        for month in months:
            total = 0.0
            for cloud in clouds.values():
                total += _lookup_with_carry(cloud.get("actual_overlay", []), month)
            overlay_totals.append(total)
        for entry, value in zip(overall["actual_overlay"], overlay_totals):
            entry["activated_instances"] = value

    # Combine gap ranges (unique)
    gap_set = set()
    for cloud in clouds.values():
        for gap in cloud.get("data_gaps", []):
            gap_set.add((gap["start"], gap["end"]))
    if gap_set:
        overall["data_gaps"] = [
            {"start": start, "end": end}
            for start, end in sorted(gap_set)
        ]

    # Sum scenario series month-by-month
    for scenario_key, scenario in overall.get("scenarios", {}).items():
        series = scenario.get("series", [])
        for entry in series:
            month = entry["month"]
            total = 0.0
            for cloud in clouds.values():
                cloud_series = cloud.get("scenarios", {}).get(scenario_key, {}).get("series", [])
                total += _lookup_with_carry(cloud_series, month)
            entry["activated_instances"] = total
        scenario["EOY_2025"] = _value_at_series(series, "2025-12")
        scenario["EOY_2026"] = _value_at_series(series, "2026-12")


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
            _clamp_projection_to_parents(out_breakdowns[cat], [result])
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
        _aggregate_overall_from_clouds(result, out_by_cp)

    # By service category and cloud provider
    by_cat_cp = metrics.get("by_service_category_and_cloud_provider", {})
    out_by_cat_cp = {}
    for key, scp_metrics in by_cat_cp.items():
        scp_monthly = scp_metrics.get("monthly", {}).get("data", [])
        if scp_monthly:
            out_by_cat_cp[key] = _compute_from_monthly(scp_monthly, end_month=end_month)
            parents = [result]
            if "::" in key:
                cat_key, cp_key = key.split("::", 1)
                if (result.get("by_category") or {}).get(cat_key):
                    parents.append(result["by_category"][cat_key])
                if (result.get("by_cloud_provider") or {}).get(cp_key):
                    parents.append(result["by_cloud_provider"][cp_key])
            _clamp_projection_to_parents(out_by_cat_cp[key], parents)
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
