"""
Pretty PDF Report Generator for Deep Security vs Vision One SPC Cost Comparison.

Generates a beautiful PDF that matches the HTML report styling exactly.
Uses WeasyPrint to convert HTML to PDF with full CSS3 support.
"""

import json
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from weasyprint import HTML, CSS


def _format_currency(value: float) -> str:
    """Format currency values for display."""
    return f"${value:,.0f}"


def _format_currency_short(value: float) -> str:
    """Format currency values in short form (M/K)."""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.0f}K"
    else:
        return f"${value:,.0f}"


def _embed_image_as_base64(image_path: str) -> str:
    """Convert image to base64 for embedding in HTML."""
    try:
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""


def write_cost_comparison_pretty_pdf(comparison_data: Dict[str, Any], charts_dir: str, output_path: str) -> None:
    """
    Generate beautiful PDF cost comparison report from HTML with WeasyPrint.

    Args:
        comparison_data: Cost comparison data from analyzer
        charts_dir: Directory containing chart images
        output_path: Path to save PDF file
    """
    # Extract data
    metadata = comparison_data.get('metadata', {})
    customer_name = metadata.get('customer_name', 'Federal Customer')
    baseline = comparison_data['baseline_2025']
    proposal = comparison_data.get('proposal', {})
    pricing = comparison_data['pricing']
    yearly = comparison_data['yearly_comparison']
    scenarios = comparison_data['scenario_analysis']

    # Build year-by-year table HTML (use rounded numbers for display)
    yearly_table_rows = ""
    for i, year in enumerate(yearly['years']):
        endpoints_exact = yearly['endpoints'][i]  # Exact for charts
        endpoints_rounded = yearly['endpoints_rounded'][i]  # Rounded for cost table
        ds_cost = yearly['deep_security']['annual_costs'][i]
        spc_cost = yearly['vision_one_spc']['annual_costs'][i]
        saving = yearly['savings']['annual'][i]
        cumulative = yearly['savings']['cumulative'][i]

        yearly_table_rows += f"""
        <tr>
            <td><strong>{year}</strong></td>
            <td>{endpoints_rounded:,}</td>
            <td>{_format_currency(ds_cost)}</td>
            <td>{_format_currency(spc_cost)}</td>
            <td class="savings-cell">{_format_currency(saving)}</td>
            <td class="savings-cell"><strong>{_format_currency(cumulative)}</strong></td>
        </tr>
        """

    # Get chart directory
    charts_path = Path(charts_dir)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # HTML Template - optimized for PDF printing
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Deep Security vs Vision One SPC - Cost Comparison</title>
    <style>
        @page {{
            size: letter;
            margin: 0.5in 0.4in;
        }}

        body {{
            background: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #1f2937;
        }}

        /* Hero Section */
        .hero-section {{
            background: radial-gradient(circle at center, #D71920 0%, #CC0000 100%);
            color: white;
            padding: 30px 20px;
            margin-bottom: 20px;
            text-align: center;
            page-break-after: avoid;
        }}

        .hero-section h1 {{
            font-size: 28pt;
            font-weight: bold;
            margin: 0 0 8px 0;
        }}

        .hero-section h2 {{
            font-size: 18pt;
            margin: 0 0 12px 0;
        }}

        .hero-section .lead {{
            font-size: 12pt;
            opacity: 0.95;
            margin: 0;
        }}

        .hero-section p {{
            opacity: 0.9;
            margin: 8px 0 0 0;
        }}

        /* Container */
        .container {{
            width: 100%;
            max-width: 100%;
        }}

        /* Metric Cards */
        .metric-row {{
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            page-break-inside: avoid;
        }}

        .metric-card {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px;
            flex: 1;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .metric-card h4 {{
            font-size: 8pt;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0 0 8px 0;
        }}

        .savings-highlight {{
            color: #059669;
            font-weight: bold;
            font-size: 18pt;
            margin: 4px 0;
        }}

        .metric-value {{
            font-size: 16pt;
            font-weight: bold;
            color: #1f2937;
        }}

        .metric-subtext {{
            font-size: 8pt;
            color: #6b7280;
            margin-top: 4px;
        }}

        /* Section */
        .section {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }}

        .section h3 {{
            color: #1f2937;
            font-weight: bold;
            font-size: 14pt;
            margin: 0 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 3px solid #d71920;
        }}

        .section p.lead {{
            font-size: 11pt;
            font-weight: 600;
            margin-bottom: 12px;
        }}

        /* Charts */
        .chart-container {{
            margin: 16px 0;
            text-align: center;
            page-break-inside: avoid;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 9pt;
            page-break-inside: avoid;
        }}

        table thead {{
            background: #d71920;
            color: white;
        }}

        table thead th {{
            font-weight: 600;
            padding: 8px;
            text-align: center;
            border: 1px solid #b71518;
        }}

        table tbody td {{
            padding: 8px;
            border: 1px solid #e5e7eb;
        }}

        table tbody tr:nth-child(even) {{
            background: #f8fafc;
        }}

        .savings-cell {{
            color: #059669;
            font-weight: 600;
        }}

        /* Highlight boxes */
        .highlight-box {{
            background: #f4f4f4;
            border-left: 4px solid #D71920;
            padding: 12px;
            border-radius: 6px;
            margin: 12px 0;
            page-break-inside: avoid;
        }}

        .highlight-box strong {{
            color: #53565a;
        }}

        /* Value cards */
        .value-card {{
            background: #f9fafb;
            border-left: 4px solid #d71920;
            padding: 14px;
            margin-bottom: 12px;
            border-radius: 6px;
            page-break-inside: avoid;
        }}

        .value-card h5 {{
            color: #1f2937;
            font-weight: bold;
            margin: 0 0 8px 0;
            font-size: 10pt;
        }}

        .value-card p {{
            color: #4b5563;
            margin: 0 0 8px 0;
            font-size: 9pt;
        }}

        .value-card ul {{
            margin: 4px 0 0 0;
            padding-left: 20px;
            font-size: 8pt;
        }}

        .value-card li {{
            margin-bottom: 2px;
        }}

        /* Recommendation box */
        .recommendation-box {{
            background: linear-gradient(135deg, #dcfce7 0%, #d1fae5 100%);
            border: 2px solid #059669;
            border-radius: 8px;
            padding: 20px;
            margin: 16px 0;
            page-break-inside: avoid;
        }}

        .recommendation-box h3 {{
            color: #065f46;
            border-bottom: none;
            margin-bottom: 12px;
        }}

        .recommendation-box .lead {{
            color: #047857;
            font-size: 12pt;
            font-weight: 600;
        }}

        .recommendation-box ul {{
            color: #065f46;
            font-size: 9pt;
            margin: 8px 0;
            padding-left: 20px;
        }}

        .recommendation-box ul li {{
            margin-bottom: 4px;
        }}

        .recommendation-box h5 {{
            color: #065f46;
            font-weight: bold;
            margin: 12px 0 8px 0;
        }}

        /* Special styling for proposal section */
        .proposal-section {{
            border: 3px solid #d71920;
            background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
        }}

        .proposal-section h3 {{
            color: #d71920;
        }}

        /* Grid layouts for metrics */
        .metrics-grid {{
            display: flex;
            gap: 16px;
            margin: 16px 0;
            page-break-inside: avoid;
        }}

        .metrics-grid > div {{
            flex: 1;
            text-align: center;
        }}

        .metrics-grid h5 {{
            font-size: 9pt;
            margin: 0 0 8px 0;
            color: #6b7280;
        }}

        .metrics-grid .big-number {{
            font-size: 18pt;
            font-weight: bold;
            color: #D71920;
        }}

        .metrics-grid small {{
            font-size: 8pt;
            color: #6b7280;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 16px;
            color: #6b7280;
            font-size: 8pt;
            margin-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}

        /* Page breaks */
        .page-break {{
            page-break-after: always;
        }}

        /* Comparison tables */
        .comparison-table td {{
            padding: 10px;
        }}

        .comparison-table .check-mark {{
            color: #059669;
            font-size: 11pt;
        }}

        .comparison-table .cross-mark {{
            color: #dc2626;
            font-size: 11pt;
        }}
    </style>
</head>
<body>

    <!-- Hero Section -->
    <div class="hero-section">
        <h1>Deep Security vs Vision One SPC</h1>
        <h2>Cost Comparison & Strategic Analysis</h2>
        <p class="lead">{customer_name} | Data Sovereignty Required</p>
        <p>Multi-Year Total Cost of Ownership Comparison with Growth Projections</p>
    </div>

    <!-- Executive Summary - Key Metrics -->
    <div class="container">
        <div class="metric-row">
            <div class="metric-card">
                <h4>Year 1 Savings (2026)</h4>
                <div class="savings-highlight">{_format_currency_short(yearly['savings']['annual'][0])}</div>
                <div class="metric-subtext">Even with upfront platform & deployment costs</div>
            </div>
            <div class="metric-card">
                <h4>{len(yearly['years'])}-Year Total Savings</h4>
                <div class="savings-highlight">{_format_currency_short(yearly['savings']['cumulative'][-1])}</div>
                <div class="metric-subtext">With projected growth to {yearly['endpoints_rounded'][-1]:,} endpoints</div>
            </div>
        </div>

        <div class="metric-row">
            <div class="metric-card">
                <h4>Per-Endpoint Annual Savings</h4>
                <div class="savings-highlight">${(yearly['deep_security']['annual_costs'][0] / yearly['endpoints'][0]) - yearly['vision_one_spc']['per_endpoint_effective'][0]:.2f}</div>
                <div class="metric-subtext">SPC vs Deep Security per endpoint</div>
            </div>
            <div class="metric-card" style="border: 2px solid #d71920;">
                <h4 style="color: #d71920;">💼 Proposed 2026 Licensing</h4>
                <div class="metric-value" style="color: #d71920;">{proposal['endpoints']:,}</div>
                <div class="metric-subtext"><strong>Conservative projection-based</strong> (40,891 rounded up)</div>
            </div>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- 2025 Growth Story & 2026 Projection -->
    <div class="container">
        <div class="section">
            <h3>📈 2025 Growth Story & 2026 Projection</h3>
            <p class="lead">From 15K licensed to 24.7K (2025) to 41K proposed (2026)</p>

            <div class="highlight-box">
                <strong>Partnership Value in 2025:</strong> Air Force Cloud One grew from <strong>{baseline['licensed_endpoints']:,} licensed endpoints</strong> to <strong>{baseline['eoy_endpoints']:,} projected endpoints</strong> by EOY 2025, receiving <strong>{_format_currency(baseline['partnership_value'])}</strong> in coverage value beyond your license agreement. This flexible partnership approach supported Cloud One's rapid expansion.
            </div>

            <div class="chart-container">
                <img src="{_embed_image_as_base64(str(charts_path / '2025_growth_story.png'))}" alt="2025 Growth Story">
            </div>

            <div class="metrics-grid">
                <div>
                    <h5>2025 Licensed</h5>
                    <div class="big-number">{baseline['licensed_endpoints']:,}</div>
                    <small>Original agreement</small>
                </div>
                <div>
                    <h5>Aug 2025 Actual</h5>
                    <div class="big-number" style="color: #53565a;">{baseline['current_endpoints_aug']:,}</div>
                    <small>+{baseline['current_endpoints_aug'] - baseline['licensed_endpoints']:,} over</small>
                </div>
                <div>
                    <h5>EOY 2025 Projected</h5>
                    <div class="big-number">{baseline['eoy_endpoints']:,}</div>
                    <small>+{baseline['eoy_endpoints'] - baseline['licensed_endpoints']:,} over</small>
                </div>
                <div>
                    <h5>2026 Proposed</h5>
                    <div class="big-number" style="color: #53565a;">{proposal['endpoints']:,}</div>
                    <small>Conservative projection</small>
                </div>
            </div>

            <div class="highlight-box" style="background: #fee2e2; border-left-color: #D71920;">
                <strong>2026 Proposal:</strong> Based on our conservative projection (40,891 endpoints by EOY 2026), we propose licensing for <strong>41,000 endpoints</strong> - representing the most conservative growth scenario and providing a buffer for coverage.
            </div>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- Proposed Licensing -->
    <div class="container">
        <div class="section proposal-section">
            <h3>💼 Proposed 2026 Licensing: 41,000 Endpoints</h3>
            <p class="lead"><strong>Conservative Projection-Based Proposal</strong></p>

            <div class="highlight-box" style="background: #fee2e2; border-left-color: #D71920;">
                <strong>Proposal Basis:</strong> Our conservative projection model (Geometric Decay) forecasts <strong>40,891 endpoints</strong> by EOY 2026.
                We propose licensing for <strong>41,000 endpoints</strong> (rounded up for coverage buffer), representing the most conservative growth scenario.
            </div>

            <table>
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Product Description</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Extended Price</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>VONF0247</strong></td>
                        <td>Trend Vision One - SPC - Software Platform (Base) per Deployment Site Federal 1+ New</td>
                        <td style="text-align: center;">1</td>
                        <td style="text-align: right;">{_format_currency(pricing['vision_one_spc']['base_platform']['amount'])}</td>
                        <td style="text-align: right;"><strong>{_format_currency(pricing['vision_one_spc']['base_platform']['amount'])}</strong></td>
                        <td>Annual</td>
                    </tr>
                    <tr>
                        <td><strong>PSNF0043</strong></td>
                        <td>Trend Vision One - SPC - Dedicated Support Federal 1+ New</td>
                        <td style="text-align: center;">1</td>
                        <td style="text-align: right;">{_format_currency(pricing['vision_one_spc']['dedicated_support']['amount'])}</td>
                        <td style="text-align: right;"><strong>{_format_currency(pricing['vision_one_spc']['dedicated_support']['amount'])}</strong></td>
                        <td>Annual</td>
                    </tr>
                    <tr>
                        <td><strong>VONF0246</strong></td>
                        <td>Trend Vision One - SPC - Endpoint Security (Pro) Federal 25,001+ New</td>
                        <td style="text-align: center;">{proposal['endpoints']:,}</td>
                        <td style="text-align: right;">${pricing['vision_one_spc']['per_endpoint']['endpoint_security_pro']:.2f}</td>
                        <td style="text-align: right;"><strong>{_format_currency(proposal['endpoints'] * pricing['vision_one_spc']['per_endpoint']['endpoint_security_pro'])}</strong></td>
                        <td>Annual</td>
                    </tr>
                    <tr>
                        <td><strong>VONF0256</strong></td>
                        <td>Trend Vision One - SPC - Cyber Risk Exposure Management - Core Federal 25,001+ New</td>
                        <td style="text-align: center;">{proposal['endpoints']:,}</td>
                        <td style="text-align: right;">${pricing['vision_one_spc']['per_endpoint']['crem']:.2f}</td>
                        <td style="text-align: right;"><strong>{_format_currency(proposal['endpoints'] * pricing['vision_one_spc']['per_endpoint']['crem'])}</strong></td>
                        <td>Annual</td>
                    </tr>
                    <tr>
                        <td><strong>VONF0269</strong></td>
                        <td>Trend Vision One - SPC - EDR/XDR Add-on: Endpoint, Server, Cloud Workload Federal 5,001+ New</td>
                        <td style="text-align: center;">{proposal['endpoints']:,}</td>
                        <td style="text-align: right;">${pricing['vision_one_spc']['per_endpoint']['edr_xdr']:.2f}</td>
                        <td style="text-align: right;"><strong>{_format_currency(proposal['endpoints'] * pricing['vision_one_spc']['per_endpoint']['edr_xdr'])}</strong></td>
                        <td>Annual</td>
                    </tr>
                    <tr style="background: #f9fafb;">
                        <td><strong>PDNN0013</strong></td>
                        <td>Trend Vision One - SPC - Deployment Service 1+ New</td>
                        <td style="text-align: center;">1</td>
                        <td style="text-align: right;">{_format_currency(pricing['vision_one_spc']['deployment_service']['amount'])}</td>
                        <td style="text-align: right;"><strong>{'WAIVED' if pricing['vision_one_spc']['deployment_service'].get('waived', False) else _format_currency(pricing['vision_one_spc']['deployment_service']['amount'])}</strong></td>
                        <td><strong>One-Time {'(Waived)' if pricing['vision_one_spc']['deployment_service'].get('waived', False) else ''}</strong></td>
                    </tr>
                    <tr style="background: #d1fae5;">
                        <td colspan="4" style="text-align: right;"><strong>Year 1 Total (2026):</strong></td>
                        <td style="text-align: right;"><strong style="color: #059669;">{_format_currency(proposal['vision_one_spc']['year_1_cost'])}</strong></td>
                        <td></td>
                    </tr>
                </tbody>
            </table>

            <div style="margin-top: 12px; padding: 12px; background: #f4f4f4; border-radius: 6px; border-left: 4px solid #D71920;">
                <p style="margin: 0; color: #53565a;"><strong>📊 Why 41,000 Endpoints?</strong> Based on the <strong>most conservative</strong> of three growth projections (Geometric Decay), which forecasts 40,891 endpoints. Rounded to 41,000 for licensing coverage buffer.</p>
            </div>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- 2026 and Beyond: Growth Projections -->
    <div class="container">
        <div class="section">
            <h3>🔮 2026 and Beyond: Growth Projections</h3>
            <p>Out-year endpoint growth projections from 2026 through {yearly['years'][-1]} based on conservative estimates.</p>

            <div class="chart-container">
                <img src="{_embed_image_as_base64(str(charts_path / 'endpoint_growth_trajectory.png'))}" alt="Growth Trajectory">
            </div>

            <div class="highlight-box">
                <strong>Projection Methodology:</strong> Charts show exact conservative projections (40,891 → 58,030 → 82,353 endpoints). Cost calculations use rounded figures (41K → 58K → 82K) for cleaner proposal numbers.
            </div>
        </div>
    </div>

    <!-- Cost Comparison Analysis -->
    <div class="container">
        <div class="section">
            <h3>💰 Cost Comparison Analysis</h3>
            <p>Comprehensive cost comparison showing Deep Security vs Vision One SPC pricing across the projection horizon.</p>

            <table>
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Endpoints<br/>(Rounded)</th>
                        <th>Deep Security Cost</th>
                        <th>Vision One SPC Cost</th>
                        <th>Annual Savings</th>
                        <th>Cumulative Savings</th>
                    </tr>
                </thead>
                <tbody>
                    {yearly_table_rows}
                </tbody>
            </table>

            <div class="chart-container">
                <img src="{_embed_image_as_base64(str(charts_path / 'tco_comparison.png'))}" alt="TCO Comparison">
            </div>

            <div class="chart-container">
                <img src="{_embed_image_as_base64(str(charts_path / 'savings_accumulation.png'))}" alt="Savings">
            </div>

            <div class="highlight-box">
                <strong>Growth Advantage:</strong> Each additional 1,000 endpoints saves $34,460 annually with Vision One SPC vs Deep Security. The more you grow, the more you save.
            </div>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- Per-Endpoint Analysis -->
    <div class="container">
        <div class="section">
            <h3>🔍 Per-Endpoint Cost Analysis</h3>
            <p>Understanding the economics behind the savings.</p>

            <div class="chart-container">
                <img src="{_embed_image_as_base64(str(charts_path / 'per_endpoint_breakdown.png'))}" alt="Per-Endpoint">
            </div>

            <div style="display: flex; gap: 16px; margin-top: 16px;">
                <div class="value-card" style="flex: 1;">
                    <h5>Deep Security (Effective)</h5>
                    <p><strong>${(yearly['deep_security']['annual_costs'][0] / yearly['endpoints'][0]):.2f}/endpoint</strong></p>
                    <p><small>Includes:</small></p>
                    <ul>
                        <li>Per-Endpoint License: ${pricing['deep_security']['per_endpoint']:.2f}</li>
                        <li>Platinum Support (amortized): ${(pricing['deep_security']['platinum_support']['amount'] / yearly['endpoints'][0]):.2f}</li>
                    </ul>
                </div>
                <div class="value-card" style="flex: 1;">
                    <h5>Vision One SPC (Effective)</h5>
                    <p>
                        <strong>${yearly['vision_one_spc']['per_endpoint_effective'][0]:.2f}/endpoint</strong>
                        <span class="savings-cell"> (Save ${(yearly['deep_security']['annual_costs'][0] / yearly['endpoints'][0]) - yearly['vision_one_spc']['per_endpoint_effective'][0]:.2f}/endpoint)</span>
                    </p>
                    <p><small>Includes:</small></p>
                    <ul>
                        <li>Endpoint Security Pro: ${pricing['vision_one_spc']['per_endpoint']['endpoint_security_pro']:.2f}</li>
                        <li>CREM: ${pricing['vision_one_spc']['per_endpoint']['crem']:.2f}</li>
                        <li>EDR/XDR: ${pricing['vision_one_spc']['per_endpoint']['edr_xdr']:.2f}</li>
                        <li>Base Platform (amortized): ${(pricing['vision_one_spc']['base_platform']['amount'] / yearly['endpoints'][0]):.2f}</li>
                        <li>Dedicated Support (amortized): ${(pricing['vision_one_spc']['dedicated_support']['amount'] / yearly['endpoints'][0]):.2f}</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- Platform Comparison -->
    <div class="container">
        <div class="section">
            <h3>⚖️ Platform Capabilities Comparison</h3>
            <p>Beyond cost savings, Vision One SPC provides enhanced security capabilities.</p>

            <table class="comparison-table">
                <thead>
                    <tr>
                        <th style="width: 40%;">Feature / Capability</th>
                        <th style="width: 30%;">Deep Security</th>
                        <th style="width: 30%;">Vision One SPC</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Deployment Model</strong></td>
                        <td>On-premises</td>
                        <td>On-premises (containerized)</td>
                    </tr>
                    <tr>
                        <td><strong>Data Sovereignty</strong></td>
                        <td><span class="check-mark">✓</span> Yes</td>
                        <td><span class="check-mark">✓</span> Yes (100% including metadata)</td>
                    </tr>
                    <tr>
                        <td><strong>Architecture</strong></td>
                        <td>Point solution</td>
                        <td><strong>Unified XDR platform</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Endpoint Security</strong></td>
                        <td><span class="check-mark">✓</span></td>
                        <td><span class="check-mark">✓</span> (Pro tier)</td>
                    </tr>
                    <tr>
                        <td><strong>Cloud Workload Protection</strong></td>
                        <td><span class="check-mark">✓</span></td>
                        <td><span class="check-mark">✓</span></td>
                    </tr>
                    <tr>
                        <td><strong>EDR/XDR (Advanced Detection & Response)</strong></td>
                        <td><span class="cross-mark">✗</span> Not available</td>
                        <td><span class="check-mark">✓</span> <strong>Included</strong></td>
                    </tr>
                    <tr>
                        <td><strong>CREM (Cyber Risk Exposure Management)</strong></td>
                        <td><span class="cross-mark">✗</span> Not available</td>
                        <td><span class="check-mark">✓</span> <strong>Included</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Unified Single Pane of Glass</strong></td>
                        <td>Limited</td>
                        <td><span class="check-mark">✓</span> Comprehensive</td>
                    </tr>
                    <tr>
                        <td><strong>Air-Gap Capable</strong></td>
                        <td><span class="check-mark">✓</span></td>
                        <td><span class="check-mark">✓</span> (Designed for it)</td>
                    </tr>
                    <tr>
                        <td><strong>Federal Compliance</strong></td>
                        <td><span class="check-mark">✓</span></td>
                        <td><span class="check-mark">✓</span> (Purpose-built for gov)</td>
                    </tr>
                    <tr>
                        <td><strong>Containerized Modern Architecture</strong></td>
                        <td><span class="cross-mark">✗</span></td>
                        <td><span class="check-mark">✓</span></td>
                    </tr>
                    <tr style="background: #f0fdf4;">
                        <td><strong>Effective Annual Cost per Endpoint</strong></td>
                        <td><strong>${pricing['deep_security']['per_endpoint']:.2f}</strong></td>
                        <td><strong>${yearly['vision_one_spc']['per_endpoint_effective'][0]:.2f}</strong> <span class="savings-cell">({((pricing['deep_security']['per_endpoint'] - yearly['vision_one_spc']['per_endpoint_effective'][0]) / pricing['deep_security']['per_endpoint'] * 100):.1f}% lower)</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- Value Propositions -->
    <div class="container">
        <div class="section">
            <h3>✨ Why Vision One SPC for Federal Missions</h3>

            <div class="value-card">
                <h5>💰 Immediate & Growing Savings</h5>
                <p>{_format_currency_short(yearly['savings']['annual'][0])} in Year 1, {_format_currency_short(yearly['savings']['annual'][1] if len(yearly['savings']['annual']) > 1 else 0)}+ annually thereafter. Savings grow as your endpoint count increases. Multi-year TCO advantage of {_format_currency_short(yearly['savings']['cumulative'][-1])} over {len(yearly['years'])} years.</p>
            </div>

            <div class="value-card">
                <h5>🔒 Data Sovereignty Maintained</h5>
                <p>Vision One SPC is our entire XDR platform containerized for on-premises deployment. 100% of your data—including metadata—stays within your sovereign boundaries. Deploy to AWS GovCloud, Azure Government, or your datacenters. Air-gap ready for sensitive environments.</p>
            </div>

            <div class="value-card">
                <h5>🎯 Unified XDR Platform</h5>
                <p>Move from Deep Security point solution to Vision One unified XDR platform. Better visibility across your entire environment, unified security operations, streamlined management. Single pane of glass for comprehensive threat detection and response.</p>
            </div>

            <div class="value-card">
                <h5>⚡ Enhanced Capabilities Included</h5>
                <p>EDR/XDR for advanced detection and response, plus CREM for cyber risk exposure management—both included in SPC. These capabilities are not available in Deep Security, requiring separate products and significantly higher costs.</p>
            </div>

            <div class="value-card">
                <h5>📈 Scale Efficiency Advantage</h5>
                <p>Cloud One's rapid 144% growth over 2 years makes SPC's better per-endpoint economics increasingly valuable. Each additional 1,000 endpoints saves $34,460 vs Deep Security. The base platform cost amortizes across more endpoints as you scale. Growth becomes an economic advantage, not a burden.</p>
            </div>

            <div class="value-card">
                <h5>🏛️ Federal-Ready Architecture</h5>
                <p>Purpose-built for government and regulated industries. Containerized deployment provides modern flexibility while maintaining complete control over your data and infrastructure.</p>
            </div>
        </div>
    </div>

    <!-- Strategic Recommendation -->
    <div class="container">
        <div class="recommendation-box">
            <h3>🎯 Strategic Recommendation</h3>
            <p class="lead">Migrate to Vision One Sovereign and Private Cloud for your 2026 renewal</p>

            <div style="display: flex; gap: 20px; margin-top: 16px;">
                <div style="flex: 1;">
                    <h5>Financial Benefits:</h5>
                    <ul>
                        <li><strong>{_format_currency_short(yearly['savings']['annual'][0])}</strong> immediate savings in Year 1</li>
                        <li><strong>{_format_currency_short(yearly['savings']['annual'][1] if len(yearly['savings']['annual']) > 1 else 0)}+</strong> annual recurring savings Year 2+</li>
                        <li><strong>{_format_currency_short(yearly['savings']['cumulative'][-1])}</strong> total savings over {len(yearly['years'])} years</li>
                        <li>Savings grow with your endpoint count</li>
                    </ul>
                </div>
                <div style="flex: 1;">
                    <h5>Strategic Benefits:</h5>
                    <ul>
                        <li>Unified XDR platform vs point solution</li>
                        <li>EDR/XDR and CREM capabilities included</li>
                        <li>100% data sovereignty maintained</li>
                        <li>Modern containerized architecture</li>
                        <li>Purpose-built for federal compliance</li>
                        <li>Growth becomes an economic advantage</li>
                    </ul>
                </div>
            </div>

            <h5>Implementation Timeline:</h5>
            <ul>
                <li><strong>Q4 2025:</strong> Final decision and procurement process</li>
                <li><strong>Q1 2026:</strong> Vision One SPC platform deployment and configuration</li>
                <li><strong>Q1-Q2 2026:</strong> Phased migration from Deep Security to Vision One SPC</li>
                <li><strong>Q2 2026 onwards:</strong> Full operation on unified XDR platform with cost savings realized</li>
            </ul>

            <p style="margin-top: 12px;"><strong>Risk Mitigation:</strong> Phased migration approach minimizes operational disruption. Trend Micro deployment services ensure smooth transition. Parallel operation capability during migration period. Federal compliance maintained throughout.</p>
        </div>
    </div>

    <!-- Footer -->
    <div class="container">
        <div class="footer">
            <p>Report generated on {timestamp}</p>
            <p>Based on conservative growth projections (Geometric Decay scenario)</p>
            <p style="margin-top: 12px;">
                <strong>Vision One Sovereign and Private Cloud (SPC)</strong><br>
                On-premises XDR platform • 100% Data Sovereignty • Federal Compliance Ready
            </p>
        </div>
    </div>

</body>
</html>
"""

    # Generate PDF using WeasyPrint
    HTML(string=html).write_pdf(output_path)
    print(f"  ✅ Pretty PDF report saved to {output_path}")
