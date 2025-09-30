"""
Cost Comparison Visualization Module.

Generates professional charts for Deep Security vs Vision One SPC comparison.
Consistent with existing DSUA visualization style.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# Color palette - government/professional appropriate
COLORS = {
    "deep_security": "#6b7280",  # Gray for DS
    "vision_one_spc": "#d71920",  # Trend Micro red for SPC
    "savings": "#059669",  # Green for savings
    "baseline_2025": "#3b82f6",  # Blue for 2025 baseline
    "partnership_value": "#8b5cf6",  # Purple for partnership value
    "accent": "#f59e0b",  # Amber for accents
}


def _setup_figure(title: str, figsize=(12, 7)) -> tuple:
    """Create figure with consistent styling."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#f4f6fb")
    ax.set_facecolor("#ffffff")
    ax.grid(which="major", color="#e5e7eb", linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#d1d5db")
        ax.spines[spine].set_linewidth(1.1)

    ax.tick_params(colors="#4b5563", labelsize=10)
    ax.set_title(title, fontsize=14, fontweight="bold", color="#1f2937", pad=20)

    return fig, ax


def _format_currency(value: float) -> str:
    """Format currency values."""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.0f}K"
    else:
        return f"${value:,.0f}"


def plot_growth_value_timeline(data: Dict[str, Any], output_path: str) -> None:
    """
    Grouped bar chart showing 2025 baseline, then year-by-year comparison.

    Shows:
    - 2025: Licensed vs Actual with partnership value annotation
    - 2026-2028: Deep Security vs Vision One SPC with savings
    """
    fig, ax = _setup_figure("Cost Comparison Timeline: 2025 Baseline to Future Years")

    # Extract data
    baseline = data['baseline_2025']
    yearly = data['yearly_comparison']

    # Prepare data for plotting
    years_labels = ['2025\n(Licensed)', '2025\n(Actual)'] + [str(y) for y in yearly['years']]
    x_pos = np.arange(len(years_labels))

    # Bar width
    width = 0.35

    # 2025 data
    licensed_2025 = baseline['annual_cost']
    actual_eoy_2025 = baseline['eoy_endpoints']
    ds_per_endpoint = data['pricing']['deep_security']['per_endpoint']
    actual_cost_2025 = actual_eoy_2025 * ds_per_endpoint

    # Build bars
    costs_series1 = [licensed_2025, actual_cost_2025] + yearly['deep_security']['annual_costs']
    costs_series2 = [0, 0] + yearly['vision_one_spc']['annual_costs']

    # Create bars
    bars1 = ax.bar(x_pos[:2], costs_series1[:2], width*2, label='2025 Baseline',
                   color=COLORS['baseline_2025'], alpha=0.8)

    bars2 = ax.bar(x_pos[2:] - width/2, costs_series1[2:], width,
                   label='Deep Security', color=COLORS['deep_security'], alpha=0.8)

    bars3 = ax.bar(x_pos[2:] + width/2, costs_series2[2:], width,
                   label='Vision One SPC', color=COLORS['vision_one_spc'], alpha=0.8)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       _format_currency(height),
                       ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Add savings annotations for future years
    for i, (year_idx, saving) in enumerate(zip(range(len(yearly['years'])), yearly['savings']['annual'])):
        x = x_pos[2 + year_idx]
        y = max(costs_series1[2 + year_idx], costs_series2[2 + year_idx])
        ax.annotate(f'Save\n{_format_currency(saving)}',
                   xy=(x, y * 1.05),
                   ha='center', va='bottom',
                   fontsize=9, color=COLORS['savings'], fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                            edgecolor=COLORS['savings'], linewidth=1.5))

    # Add partnership value annotation for 2025
    partnership_value = baseline.get('partnership_value', 0)
    if partnership_value > 0:
        ax.annotate(f'Partnership Value:\n{_format_currency(partnership_value)}',
                   xy=(1, actual_cost_2025),
                   xytext=(1.5, actual_cost_2025 * 1.15),
                   ha='left', va='bottom',
                   fontsize=9, color=COLORS['partnership_value'], fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#faf5ff',
                            edgecolor=COLORS['partnership_value'], linewidth=1.5),
                   arrowprops=dict(arrowstyle='->', color=COLORS['partnership_value'], lw=1.5))

    ax.set_xlabel('Year', fontsize=12, fontweight='bold', color='#374151')
    ax.set_ylabel('Annual Cost', fontsize=12, fontweight='bold', color='#374151')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(years_labels, fontsize=10)

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: _format_currency(y)))

    ax.legend(loc='upper left', framealpha=0.95, fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()


def plot_tco_comparison(data: Dict[str, Any], output_path: str) -> None:
    """
    Line chart showing cumulative TCO over years.
    Shows cumulative costs with shaded savings area.
    """
    fig, ax = _setup_figure("Total Cost of Ownership Comparison (Cumulative)")

    yearly = data['yearly_comparison']
    years = yearly['years']

    # Calculate cumulative costs
    ds_cumulative = np.cumsum(yearly['deep_security']['annual_costs'])
    spc_cumulative = np.cumsum(yearly['vision_one_spc']['annual_costs'])

    # Plot lines
    ax.plot(years, ds_cumulative, marker='o', linewidth=3, markersize=8,
           label='Deep Security', color=COLORS['deep_security'])

    ax.plot(years, spc_cumulative, marker='s', linewidth=3, markersize=8,
           label='Vision One SPC', color=COLORS['vision_one_spc'])

    # Fill area between lines (savings)
    ax.fill_between(years, ds_cumulative, spc_cumulative,
                    where=(ds_cumulative >= spc_cumulative),
                    interpolate=True, alpha=0.3,
                    color=COLORS['savings'], label='Cumulative Savings')

    # Add annotations at each year
    for i, year in enumerate(years):
        savings = ds_cumulative[i] - spc_cumulative[i]
        mid_y = (ds_cumulative[i] + spc_cumulative[i]) / 2
        ax.annotate(_format_currency(savings),
                   xy=(year, mid_y),
                   ha='center', va='center',
                   fontsize=10, color=COLORS['savings'], fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                            edgecolor=COLORS['savings'], linewidth=2))

    ax.set_xlabel('Year', fontsize=12, fontweight='bold', color='#374151')
    ax.set_ylabel('Cumulative Cost', fontsize=12, fontweight='bold', color='#374151')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: _format_currency(y)))

    ax.legend(loc='upper left', framealpha=0.95, fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()


def plot_per_endpoint_breakdown(data: Dict[str, Any], output_path: str) -> None:
    """
    Side-by-side bar chart comparing per-endpoint costs.
    Shows component breakdown for SPC.
    """
    fig, ax = _setup_figure("Per-Endpoint Cost Comparison")

    # Use first year endpoints for calculation
    endpoints = data['yearly_comparison']['endpoints'][0]
    pricing = data['pricing']

    # Deep Security - components (license + support)
    ds_per_endpoint = pricing['deep_security']['per_endpoint']
    ds_support_amortized = pricing['deep_security']['platinum_support']['amount'] / endpoints

    # Vision One SPC - components
    spc_endpoint_security = pricing['vision_one_spc']['per_endpoint']['endpoint_security_pro']
    spc_crem = pricing['vision_one_spc']['per_endpoint']['crem']
    spc_edr = pricing['vision_one_spc']['per_endpoint']['edr_xdr']
    spc_base_amortized = pricing['vision_one_spc']['base_platform']['amount'] / endpoints
    spc_support_amortized = pricing['vision_one_spc']['dedicated_support']['amount'] / endpoints

    # Bar positions
    x_pos = np.array([0, 1.5])
    width = 0.6

    # Deep Security bar - stacked (license + support)
    ds_components = [ds_per_endpoint, ds_support_amortized]
    ds_labels = ['License', 'Platinum Support\n(amortized)']
    ds_colors = ['#4b5563', '#9ca3af']  # Gray shades

    bottom = 0
    for component, label, color in zip(ds_components, ds_labels, ds_colors):
        ax.bar(x_pos[0], component, width, bottom=bottom, label=label,
              color=color, alpha=0.9)
        if component > 3:  # Only label if segment is big enough
            ax.text(x_pos[0], bottom + component/2, f'${component:.2f}',
                   ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        bottom += component

    ds_total = sum(ds_components)
    ax.text(x_pos[0], ds_total + 5, f'${ds_total:.2f}',
           ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Vision One SPC - stacked components (including support)
    spc_components = [spc_endpoint_security, spc_crem, spc_edr, spc_base_amortized, spc_support_amortized]
    spc_labels = ['Endpoint\nSecurity Pro', 'CREM', 'EDR/XDR', 'Base Platform', 'Support']
    spc_colors = ['#ef4444', '#f59e0b', '#10b981', '#6366f1', '#8b5cf6']

    bottom = 0
    for component, label, color in zip(spc_components, spc_labels, spc_colors):
        ax.bar(x_pos[1], component, width, bottom=bottom, label=label,
              color=color, alpha=0.85)
        # Add value label in the middle of segment
        if component > 5:  # Only label if segment is big enough
            ax.text(x_pos[1], bottom + component/2, f'${component:.2f}',
                   ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        bottom += component

    # Total SPC label
    spc_total = sum(spc_components)
    ax.text(x_pos[1], spc_total + 5, f'${spc_total:.2f}',
           ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Add savings annotation - compare total costs including support
    savings_per_endpoint = ds_total - spc_total
    savings_pct = (savings_per_endpoint / ds_total) * 100
    ax.annotate(f'Save ${savings_per_endpoint:.2f}/endpoint\n({savings_pct:.1f}% lower)',
               xy=(x_pos[1], spc_total * 0.5),
               xytext=(x_pos[1] + 1, spc_total * 0.7),
               ha='left', va='center',
               fontsize=11, color=COLORS['savings'], fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                        edgecolor=COLORS['savings'], linewidth=2),
               arrowprops=dict(arrowstyle='->', color=COLORS['savings'], lw=2))

    ax.set_xticks(x_pos)
    ax.set_xticklabels(['Deep Security', 'Vision One SPC'], fontsize=11, fontweight='bold')
    ax.set_ylabel('Cost per Endpoint ($/year)', fontsize=12, fontweight='bold', color='#374151')
    ax.set_ylim(0, max(ds_total, spc_total) * 1.25)

    ax.legend(loc='upper right', framealpha=0.95, fontsize=9, ncol=1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()


def plot_2025_growth_story(projections_data: Dict[str, Any], output_path: str) -> None:
    """
    Chart showing 2025 actual data (Jan-Aug) + 2025 projection (Sep-Dec) + 2026 projection.
    Similar to growth projections report style, with 15K license line on 2025 portion.
    """
    fig, ax = _setup_figure("2025 Growth Story & 2026 Projection", figsize=(16, 7))

    # Get actual data (Jan-Aug)
    actual_data = projections_data.get('actual', [])

    # Get decay scenario for projections
    decay_scenario = projections_data.get('scenarios', {}).get('decay', {}).get('series', [])
    projection_2025 = [m for m in decay_scenario if m['month'].startswith('2025')]
    projection_2026 = [m for m in decay_scenario if m['month'].startswith('2026')]

    # Build complete timeline (2025 + 2026)
    months = []
    values_actual = []
    values_projected_2025 = []
    values_projected_2026 = []

    # Jan-Aug 2025 actuals
    for entry in actual_data:
        month = entry['month']
        months.append(month)
        values_actual.append(entry['activated_instances'])
        values_projected_2025.append(None)
        values_projected_2026.append(None)

    # Sep-Dec 2025 projections
    for entry in projection_2025:
        month = entry['month']
        if month not in months:
            months.append(month)
            values_actual.append(None)
            values_projected_2025.append(entry['activated_instances'])
            values_projected_2026.append(None)

    # 2026 projections (all monthly points for smooth curve)
    for entry in projection_2026:
        month = entry['month']
        months.append(month)
        values_actual.append(None)
        values_projected_2025.append(None)
        values_projected_2026.append(entry['activated_instances'])

    # Convert month strings to labels
    month_labels = []
    for m in months:
        parts = m.split('-')
        year = parts[0]
        month_num = parts[1]
        if year == '2025':
            month_labels.append(f"{month_num}/{year[-2:]}")
        else:  # 2026
            month_labels.append(f"{month_num}/{year[-2:]}")

    x_pos = range(len(months))

    # Find index where 2026 starts
    idx_2026_start = len([m for m in months if m.startswith('2025')]) - 1

    # Plot actual data (Jan-Aug 2025) as solid line
    actual_x = [i for i, v in enumerate(values_actual) if v is not None]
    actual_y = [v for v in values_actual if v is not None]
    ax.plot(actual_x, actual_y, marker='o', linewidth=3, markersize=8,
           color='#1f2937', label='Actual (Jan-Aug 2025)', zorder=3)

    # Plot 2025 projected data (Sep-Dec) as dashed line
    if actual_y and values_projected_2025:
        proj_start_idx = len(actual_y) - 1
        proj_2025_x = [i for i in range(proj_start_idx, idx_2026_start + 1) if i == proj_start_idx or values_projected_2025[i] is not None]
        proj_2025_y = [actual_y[-1]] + [v for v in values_projected_2025 if v is not None]

        ax.plot(proj_2025_x, proj_2025_y, marker='o', linewidth=3, markersize=8,
               linestyle='--', color=COLORS['vision_one_spc'],
               label='Projected 2025 (Conservative)', zorder=3, alpha=0.8)

    # Plot 2026 projection as dashed line
    if values_projected_2026:
        eoy_2025_val = proj_2025_y[-1] if proj_2025_y else actual_y[-1]
        proj_2026_x = [idx_2026_start] + [i for i in range(idx_2026_start + 1, len(months)) if values_projected_2026[i] is not None]
        proj_2026_y = [eoy_2025_val] + [v for v in values_projected_2026 if v is not None]

        ax.plot(proj_2026_x, proj_2026_y, marker='s', linewidth=3, markersize=8,
               linestyle='--', color=COLORS['accent'],
               label='Projected 2026', zorder=3, alpha=0.8)

    # Add 15,000 license line for 2025 portion only
    ax.hlines(y=15000, xmin=-0.5, xmax=idx_2026_start + 0.5,
             color=COLORS['deep_security'], linestyle=':', linewidth=2.5,
             label='2025 Licensed (15,000)', alpha=0.7, zorder=2)

    # Add value labels
    all_values = values_actual + values_projected_2025 + values_projected_2026
    max_val = max([v for v in all_values if v is not None])

    for i, (x, y_actual, y_proj_2025, y_proj_2026) in enumerate(zip(x_pos, values_actual, values_projected_2025, values_projected_2026)):
        y = y_actual if y_actual is not None else (y_proj_2025 if y_proj_2025 is not None else y_proj_2026)
        if y is not None:
            ax.text(x, y + max_val * 0.02,
                   f'{y:,.0f}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Timeline (2025-2026)', fontsize=12, fontweight='bold', color='#374151')
    ax.set_ylabel('Cumulative Activated Instances', fontsize=12, fontweight='bold', color='#374151')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(month_labels, fontsize=9, rotation=45, ha='right')

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{int(y):,}'))
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)

    ax.legend(loc='upper left', framealpha=0.95, fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()


def plot_endpoint_growth_trajectory(data: Dict[str, Any], output_path: str) -> None:
    """
    Line chart showing endpoint growth trajectory.
    Marks license cap and key milestones.
    """
    fig, ax = _setup_figure("Endpoint Growth Trajectory")

    baseline = data['baseline_2025']
    yearly = data['yearly_comparison']

    # Build timeline
    years_labels = ['Aug 2025\n(Current)', 'EOY 2025'] + [f'EOY {y}' for y in yearly['years']]
    endpoints = [
        baseline['current_endpoints_aug'],
        baseline['eoy_endpoints']
    ] + yearly['endpoints']

    x_pos = range(len(years_labels))

    # Plot growth line
    ax.plot(x_pos, endpoints, marker='o', linewidth=3, markersize=10,
           color=COLORS['vision_one_spc'], label='Projected Growth', zorder=3)

    # Add 2025 license cap line for reference (only shown at 2025 positions)
    license_cap = baseline['licensed_endpoints']
    # Draw line only for 2025 timeframe (first two points)
    ax.hlines(y=license_cap, xmin=-0.5, xmax=1.5,
             color=COLORS['deep_security'], linestyle='--',
             linewidth=2, label=f'2025 License ({license_cap:,})', alpha=0.6, zorder=2)

    # Add value labels for all points
    for i, (x, y) in enumerate(zip(x_pos, endpoints)):
        ax.text(x, y + max(endpoints) * 0.02, f'{y:,}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Timeline', fontsize=12, fontweight='bold', color='#374151')
    ax.set_ylabel('Activated Endpoints', fontsize=12, fontweight='bold', color='#374151')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(years_labels, fontsize=10)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{int(y):,}'))

    ax.legend(loc='upper left', framealpha=0.95, fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()


def plot_scenario_comparison(data: Dict[str, Any], output_path: str) -> None:
    """
    Grouped bar chart showing Year 1 savings under different growth scenarios.
    """
    fig, ax = _setup_figure("Year 1 Savings by Growth Scenario")

    scenarios = data['scenario_analysis']

    # Sort by endpoints (ascending)
    sorted_scenarios = sorted(scenarios.items(), key=lambda x: x[1]['endpoints'])

    names = [s[1]['name'] for s in sorted_scenarios]
    endpoints = [s[1]['endpoints'] for s in sorted_scenarios]
    savings = [s[1]['savings'] for s in sorted_scenarios]

    x_pos = np.arange(len(names))
    colors_list = [COLORS['vision_one_spc'], COLORS['accent'], COLORS['savings']]

    bars = ax.bar(x_pos, savings, color=colors_list, alpha=0.85, width=0.6)

    # Add value labels
    for bar, endpoint_count, saving in zip(bars, endpoints, savings):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{_format_currency(saving)}\n({endpoint_count:,} endpoints)',
               ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add growth advantage annotation
    if len(savings) > 1:
        additional_savings = savings[-1] - savings[0]
        pct_increase = (additional_savings / savings[0]) * 100
        ax.annotate(f'Growth Upside:\n+{_format_currency(additional_savings)}\n({pct_increase:.0f}% more)',
                   xy=(len(names)-1, savings[-1] * 0.5),
                   xytext=(len(names)-1 + 0.5, savings[-1] * 0.65),
                   ha='left', va='center',
                   fontsize=10, color=COLORS['savings'], fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                            edgecolor=COLORS['savings'], linewidth=2),
                   arrowprops=dict(arrowstyle='->', color=COLORS['savings'], lw=2))

    ax.set_xlabel('Growth Scenario', fontsize=12, fontweight='bold', color='#374151')
    ax.set_ylabel('Year 1 Savings (SPC vs DS)', fontsize=12, fontweight='bold', color='#374151')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, fontsize=10, rotation=15, ha='right')

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: _format_currency(y)))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()


def plot_savings_accumulation(data: Dict[str, Any], output_path: str) -> None:
    """
    Area chart showing cumulative savings over time.
    """
    fig, ax = _setup_figure("Cumulative Savings Over Time")

    yearly = data['yearly_comparison']
    years = yearly['years']
    cumulative_savings = yearly['savings']['cumulative']

    # Plot area
    ax.fill_between(years, 0, cumulative_savings,
                    alpha=0.4, color=COLORS['savings'], label='Cumulative Savings')
    ax.plot(years, cumulative_savings, marker='o', linewidth=3, markersize=10,
           color=COLORS['savings'], label='Savings Total')

    # Add value labels
    for year, saving in zip(years, cumulative_savings):
        ax.text(year, saving, f'  {_format_currency(saving)}',
               ha='left', va='center', fontsize=11, fontweight='bold',
               color=COLORS['savings'])

    # Add annual increment annotations
    annual_savings = yearly['savings']['annual']
    for i in range(len(years)):
        if i == 0:
            y_pos = cumulative_savings[i] / 2
        else:
            y_pos = (cumulative_savings[i] + cumulative_savings[i-1]) / 2

        ax.text(years[i], y_pos, f'Year {i+1}:\n{_format_currency(annual_savings[i])}',
               ha='center', va='center', fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                        edgecolor=COLORS['savings'], linewidth=1.5))

    ax.set_xlabel('Year', fontsize=12, fontweight='bold', color='#374151')
    ax.set_ylabel('Cumulative Savings', fontsize=12, fontweight='bold', color='#374151')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: _format_currency(y)))

    ax.set_ylim(0, max(cumulative_savings) * 1.15)

    ax.legend(loc='upper left', framealpha=0.95, fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()


def generate_all_charts(comparison_data: Dict[str, Any], projections_data: Dict[str, Any], output_dir: str) -> None:
    """
    Generate all cost comparison visualization charts.

    Args:
        comparison_data: Cost comparison data from analyzer
        projections_data: Raw projections data for 2025 growth chart
        output_dir: Directory to save chart images
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("  📊 Generating 2025 growth story chart...")
    plot_2025_growth_story(projections_data, str(output_path / "2025_growth_story.png"))

    print("  📊 Generating growth & value timeline chart...")
    plot_growth_value_timeline(comparison_data, str(output_path / "growth_value_timeline.png"))

    print("  📊 Generating TCO comparison chart...")
    plot_tco_comparison(comparison_data, str(output_path / "tco_comparison.png"))

    print("  📊 Generating per-endpoint breakdown chart...")
    plot_per_endpoint_breakdown(comparison_data, str(output_path / "per_endpoint_breakdown.png"))

    print("  📊 Generating endpoint growth trajectory chart...")
    plot_endpoint_growth_trajectory(comparison_data, str(output_path / "endpoint_growth_trajectory.png"))

    # Scenario comparison chart removed - focusing on conservative projection only
    # print("  📊 Generating scenario comparison chart...")
    # plot_scenario_comparison(comparison_data, str(output_path / "scenario_comparison.png"))

    print("  📊 Generating savings accumulation chart...")
    plot_savings_accumulation(comparison_data, str(output_path / "savings_accumulation.png"))

    print(f"  ✅ All charts saved to {output_dir}")
