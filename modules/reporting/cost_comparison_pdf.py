"""
PDF Report Generator for Deep Security vs Vision One SPC Cost Comparison.

Generates formal presentation-ready PDF report using ReportLab.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# Brand colors matching existing DSUA style
BRAND_RED = colors.HexColor("#d71920")
SLATE_900 = colors.HexColor("#111827")
SLATE_700 = colors.HexColor("#374151")
SLATE_500 = colors.HexColor("#6b7280")
COOL_GREY = colors.HexColor("#f4f6fb")
CARD_BORDER = colors.HexColor("#e5e7eb")
TABLE_HEADER_BG = colors.HexColor("#d71920")
TABLE_HEADER_TEXT = colors.white
ROW_ALT_BG = colors.HexColor("#f8fafc")
SAVINGS_GREEN = colors.HexColor("#059669")


def _format_currency(value: float) -> str:
    """Format currency values."""
    return f"${value:,.0f}"


def _format_currency_short(value: float) -> str:
    """Format currency in short form."""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.0f}K"
    else:
        return f"${value:,.0f}"


def _make_table(data: List[List[str]], col_widths: List[float] = None, centered: bool = False) -> Table:
    """Create a styled table.

    Args:
        data: Table data as list of lists
        col_widths: Optional column widths in inches
        centered: If True, center the table on the page (default: False)
    """
    kwargs = {"hAlign": 'CENTER' if centered else 'LEFT'}
    if col_widths:
        kwargs["colWidths"] = [w * inch for w in col_widths]

    t = Table(data, **kwargs)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), TABLE_HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT_BG]),
        ('TEXTCOLOR', (0, 1), (-1, -1), SLATE_900),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.6, CARD_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#f1f5f9')),
    ]))
    return t


def create_cost_comparison_pdf(json_path: str, output_path: str, charts_dir: str) -> None:
    """
    Generate PDF cost comparison report.

    Args:
        json_path: Path to cost_comparison.json
        output_path: Path to save PDF
        charts_dir: Directory containing chart images
    """
    # Load data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    metadata = data.get('metadata', {})
    customer_name = metadata.get('customer_name', 'Federal Customer')
    baseline = data['baseline_2025']
    proposal = data.get('proposal', {})
    pricing = data['pricing']
    yearly = data['yearly_comparison']
    scenarios = data['scenario_analysis']

    charts_path = Path(charts_dir)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=48,
        leftMargin=48,
        topMargin=54,
        bottomMargin=42,
    )

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=SLATE_900,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=SLATE_700,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=BRAND_RED,
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=SLATE_900,
        spaceAfter=10,
        fontName='Helvetica',
    )

    # Small style for table cells with line breaks
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=9,
        textColor=SLATE_900,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )

    # Style for table header cells with line breaks
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,  # White text for red background
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )

    # Build content
    story = []

    # Title Page
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Deep Security vs Vision One SPC", title_style))
    story.append(Paragraph("Cost Comparison & Strategic Analysis", subtitle_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"{customer_name} | Data Sovereignty Required", body_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", body_style))

    # Executive Summary
    story.append(Spacer(1, 0.8 * inch))
    story.append(Paragraph("Executive Summary", heading_style))

    per_endpoint_savings = (yearly['deep_security']['annual_costs'][0] / yearly['endpoints'][0]) - yearly['vision_one_spc']['per_endpoint_effective'][0]

    summary_data = [
        ["Metric", "Value"],
        ["Year 1 Savings (2026)", _format_currency_short(yearly['savings']['annual'][0])],
        [f"{len(yearly['years'])}-Year Total Savings", _format_currency_short(yearly['savings']['cumulative'][-1])],
        ["Per-Endpoint Annual Savings", f"${per_endpoint_savings:.2f}"],
        ["Proposed 2026 Endpoints", f"{proposal['endpoints']:,}"],
        ["SPC Effective Cost/Endpoint", f"${yearly['vision_one_spc']['per_endpoint_effective'][0]:.2f}"],
        ["Deep Security Cost/Endpoint", f"${pricing['deep_security']['per_endpoint']:.2f}"],
    ]

    story.append(_make_table(summary_data, col_widths=[3.5, 2.5]))

    # Page Break
    story.append(PageBreak())

    # 2025 Growth Story & 2026 Projection (combined section)
    story.append(Paragraph("2025 Growth Story & 2026 Projection", heading_style))
    story.append(Paragraph(
        f"Air Force Cloud One grew from <b>{baseline['licensed_endpoints']:,} licensed endpoints</b> to "
        f"<b>{baseline['eoy_endpoints']:,} projected endpoints by EOY 2025</b>, receiving "
        f"<b>{_format_currency(baseline['partnership_value'])}</b> in coverage value beyond your license agreement. "
        f"This flexible partnership approach supported Cloud One's rapid expansion. "
        f"Based on conservative projections, we propose <b>41,000 endpoints</b> for 2026.",
        body_style
    ))

    story.append(Spacer(1, 0.2 * inch))

    # 2025+2026 Growth Chart (Jan-Aug actuals + 2025 projection + 2026 projection)
    growth_2025_chart = charts_path / "2025_growth_story.png"
    if growth_2025_chart.exists():
        story.append(Image(str(growth_2025_chart), width=6.5 * inch, height=3.5 * inch))

    story.append(Spacer(1, 0.2 * inch))

    baseline_data = [
        ["Metric", "Count"],
        ["2025 Licensed Endpoints", f"{baseline['licensed_endpoints']:,}"],
        ["Current (August 2025)", f"{baseline['current_endpoints_aug']:,}"],
        ["EOY 2025 Projection", f"{baseline['eoy_endpoints']:,}"],
        ["2026 Proposed", "41,000"],
        ["Partnership Value (2025)", _format_currency(baseline['partnership_value'])],
    ]

    story.append(_make_table(baseline_data, col_widths=[3.5, 2.5], centered=True))

    # Page Break
    story.append(PageBreak())

    # 2026 and Beyond: Growth Projections
    story.append(Paragraph("2026 and Beyond: Growth Projections", heading_style))
    story.append(Paragraph(
        f"Out-year endpoint growth projections from 2026 through {yearly['years'][-1]} based on conservative estimates. "
        "These precise projections inform our licensing recommendations and cost analysis.",
        body_style
    ))

    # Multi-Year Growth Trajectory Chart
    trajectory_chart = charts_path / "endpoint_growth_trajectory.png"
    if trajectory_chart.exists():
        story.append(Spacer(1, 0.3 * inch))
        story.append(Image(str(trajectory_chart), width=6.5 * inch, height=3.5 * inch))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "Charts show exact conservative projections (40,891 → 58,030 → 82,353 endpoints). "
        "Cost calculations use rounded figures (41K → 58K → 82K) for cleaner proposal numbers.",
        body_style
    ))

    # Page Break
    story.append(PageBreak())

    # Cost Comparison Analysis
    story.append(Paragraph("Cost Comparison Analysis", heading_style))
    story.append(Paragraph(
        "Comprehensive cost comparison showing Deep Security vs Vision One SPC pricing across the projection horizon.",
        body_style
    ))

    story.append(Spacer(1, 0.2 * inch))

    # Build yearly comparison table with rounded numbers
    yearly_data = [["Year", Paragraph("Endpoints<br/>(Rounded)", table_header_style), "Deep Security", "Vision One SPC", "Savings", "Cumulative"]]
    for i, year in enumerate(yearly['years']):
        yearly_data.append([
            str(year),
            f"{yearly['endpoints_rounded'][i]:,}",  # Use rounded numbers
            _format_currency(yearly['deep_security']['annual_costs'][i]),
            _format_currency(yearly['vision_one_spc']['annual_costs'][i]),
            _format_currency(yearly['savings']['annual'][i]),
            _format_currency(yearly['savings']['cumulative'][i]),
        ])

    story.append(_make_table(yearly_data, col_widths=[0.8, 1.1, 1.5, 1.5, 1.2, 1.2]))

    # Timeline Chart
    timeline_comparison = charts_path / "growth_value_timeline.png"
    if timeline_comparison.exists():
        story.append(Spacer(1, 0.3 * inch))
        story.append(Image(str(timeline_comparison), width=6.5 * inch, height=3.5 * inch))

    # Page Break
    story.append(PageBreak())

    # TCO Analysis
    story.append(Paragraph("Total Cost of Ownership Analysis", heading_style))

    tco_chart = charts_path / "tco_comparison.png"
    if tco_chart.exists():
        story.append(Image(str(tco_chart), width=6.5 * inch, height=3.5 * inch))

    story.append(Spacer(1, 0.2 * inch))

    savings_chart = charts_path / "savings_accumulation.png"
    if savings_chart.exists():
        story.append(Image(str(savings_chart), width=6.5 * inch, height=3.5 * inch))

    # Page Break
    story.append(PageBreak())

    # Per-Endpoint Cost Analysis
    story.append(Paragraph("Per-Endpoint Cost Analysis", heading_style))
    story.append(Paragraph(
        "Vision One SPC provides lower effective per-endpoint costs while including enhanced capabilities.",
        body_style
    ))

    per_endpoint_chart = charts_path / "per_endpoint_breakdown.png"
    if per_endpoint_chart.exists():
        story.append(Spacer(1, 0.2 * inch))
        story.append(Image(str(per_endpoint_chart), width=6.5 * inch, height=3.5 * inch))

    story.append(Spacer(1, 0.2 * inch))

    # Cost breakdown table - includes support costs for both platforms
    ds_effective = yearly['deep_security']['annual_costs'][0] / yearly['endpoints'][0]
    spc_effective = yearly['vision_one_spc']['per_endpoint_effective'][0]

    cost_breakdown_data = [
        ["Component", "Deep Security", "Vision One SPC"],
        ["Per-Endpoint License", f"${pricing['deep_security']['per_endpoint']:.2f}", f"${pricing['vision_one_spc']['per_endpoint']['total']:.2f}"],
        ["  - Endpoint Security Pro", "Included", f"${pricing['vision_one_spc']['per_endpoint']['endpoint_security_pro']:.2f}"],
        ["  - CREM", "Not Available", f"${pricing['vision_one_spc']['per_endpoint']['crem']:.2f}"],
        ["  - EDR/XDR", "Not Available", f"${pricing['vision_one_spc']['per_endpoint']['edr_xdr']:.2f}"],
        ["Support (amortized)", f"${pricing['deep_security']['platinum_support']['amount'] / yearly['endpoints'][0]:.2f}", f"${pricing['vision_one_spc']['dedicated_support']['amount'] / yearly['endpoints'][0]:.2f}"],
        ["Base Platform (amortized)", "N/A", f"${pricing['vision_one_spc']['base_platform']['amount'] / yearly['endpoints'][0]:.2f}"],
        ["Effective Total", f"${ds_effective:.2f}", f"${spc_effective:.2f}"],
        ["Savings per Endpoint", "", f"${ds_effective - spc_effective:.2f}"],
    ]

    story.append(_make_table(cost_breakdown_data, col_widths=[2.5, 1.8, 1.8], centered=True))

    # Page Break
    story.append(PageBreak())

    # Platform Comparison
    story.append(Paragraph("Platform Capabilities Comparison", heading_style))

    platform_data = [
        ["Feature", "Deep Security", "Vision One SPC"],
        ["Deployment Model", "On-premises", "On-premises (containerized)"],
        ["Data Sovereignty", "Yes", "Yes (100% incl. metadata)"],
        ["Architecture", "Point solution", "Unified XDR platform"],
        ["Endpoint Security", "✓", "✓ (Pro tier)"],
        ["EDR/XDR", "✗ Not available", "✓ Included"],
        ["CREM", "✗ Not available", "✓ Included"],
        ["Single Pane of Glass", "Limited", "✓ Comprehensive"],
        ["Air-Gap Capable", "✓", "✓ (Designed for it)"],
        ["Federal Compliance", "✓", "✓ (Purpose-built)"],
        ["Containerized", "✗", "✓"],
    ]

    story.append(_make_table(platform_data, col_widths=[2.5, 1.8, 1.8]))

    # Page Break
    story.append(PageBreak())

    # Strategic Recommendation
    story.append(Paragraph("Strategic Recommendation", heading_style))

    story.append(Paragraph(
        "<b>Migrate to Vision One Sovereign and Private Cloud for 2026 renewal</b>",
        body_style
    ))

    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("<b>Financial Benefits:</b>", body_style))
    story.append(Paragraph(
        f"• <b>{_format_currency_short(yearly['savings']['annual'][0])}</b> immediate savings in Year 1<br/>"
        f"• <b>{_format_currency_short(yearly['savings']['annual'][1] if len(yearly['savings']['annual']) > 1 else 0)}+</b> annual recurring savings Year 2+<br/>"
        f"• <b>{_format_currency_short(yearly['savings']['cumulative'][-1])}</b> total savings over {len(yearly['years'])} years<br/>"
        f"• Savings grow with endpoint count",
        body_style
    ))

    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("<b>Strategic Benefits:</b>", body_style))
    story.append(Paragraph(
        "• Unified XDR platform vs point solution<br/>"
        "• EDR/XDR and CREM capabilities included<br/>"
        "• 100% data sovereignty maintained<br/>"
        "• Modern containerized architecture<br/>"
        "• Purpose-built for federal compliance<br/>"
        "• Growth becomes an economic advantage",
        body_style
    ))

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Implementation Timeline:</b>", body_style))
    story.append(Paragraph(
        "• <b>Q4 2025:</b> Final decision and procurement<br/>"
        "• <b>Q1 2026:</b> Vision One SPC platform deployment<br/>"
        "• <b>Q1-Q2 2026:</b> Phased migration from Deep Security<br/>"
        "• <b>Q2 2026+:</b> Full operation with cost savings realized",
        body_style
    ))

    # Build PDF
    doc.build(story)
    print(f"✅ PDF report saved: {output_path}")
