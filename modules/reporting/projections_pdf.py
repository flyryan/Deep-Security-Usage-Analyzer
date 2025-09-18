import json
from pathlib import Path
from typing import Dict, List, Callable

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
    ListFlowable,
    ListItem,
)
from reportlab.lib import colors
from reportlab.lib.units import inch

from .projections_plot import save_projection_subset_png, SCENARIO_LABELS
from datetime import datetime


BRAND_RED = colors.HexColor("#d71920")
SLATE_900 = colors.HexColor("#111827")
SLATE_700 = colors.HexColor("#374151")
SLATE_500 = colors.HexColor("#6b7280")
COOL_GREY = colors.HexColor("#f4f6fb")
CARD_BORDER = colors.HexColor("#e5e7eb")
TABLE_HEADER_BG = colors.HexColor("#d71920")
TABLE_HEADER_TEXT = colors.white
ROW_ALT_BG = colors.HexColor("#f8fafc")

SCENARIO_NAMES = {
    key: value for key, value in SCENARIO_LABELS.items()
}

SCENARIO_ORDER = ["decay", "linear", "avg_last3"]

def _summary_rows(subset: Dict, license_cap: float,
                  fmt_int: Callable[[float], object],
                  fmt_delta: Callable[[float], object],
                  include_license: bool) -> List[List[object]]:
    base = subset["actual"][-1]["activated_instances"]
    rows: List[List[object]] = [["Current Count", fmt_int(base)]]
    if include_license:
        rows.insert(0, ["Current License", fmt_int(license_cap)])
        rows.append(["Delta vs License", fmt_delta(base - license_cap)])
    return rows


def _eoY_rows(subset: Dict, license_cap: float,
              make_header: Callable[[str], object],
              fmt_text: Callable[[str], object],
              fmt_int: Callable[[float], object],
              fmt_delta: Callable[[float], object],
              include_license: bool) -> List[List[object]]:
    base = subset["actual"][-1]["activated_instances"]
    if include_license:
        header = [
            make_header("Forecast Model"),
            make_header("EOY 2025 Projection"),
            make_header("Δ vs License Cap<br/>(2025)"),
            make_header("EOY 2026 Projection"),
            make_header("Δ vs License Cap<br/>(2026)"),
        ]
    else:
        header = [
            make_header("Forecast Model"),
            make_header("EOY 2025 Projection"),
            make_header("Δ vs Current Level<br/>(2025)"),
            make_header("EOY 2026 Projection"),
            make_header("Δ vs Current Level<br/>(2026)"),
        ]

    rows: List[List[object]] = [header]
    for key in SCENARIO_ORDER:
        sc = subset["scenarios"].get(key)
        if not sc:
            continue
        display_name = SCENARIO_NAMES.get(key, sc.get("name", key))
        eoy25 = sc.get("EOY_2025")
        eoy26 = sc.get("EOY_2026")
        if include_license:
            row: List[object] = [
                fmt_text(display_name),
                fmt_int(eoy25) if eoy25 is not None else "—",
                fmt_delta((eoy25 - license_cap) if eoy25 is not None else 0.0) if eoy25 is not None else "—",
                fmt_int(eoy26) if eoy26 is not None else "—",
                fmt_delta((eoy26 - license_cap) if eoy26 is not None else 0.0) if eoy26 is not None else "—",
            ]
        else:
            row = [
                fmt_text(display_name),
                fmt_int(eoy25) if eoy25 is not None else "—",
                fmt_delta((eoy25 - base) if eoy25 is not None else 0.0) if eoy25 is not None else "—",
                fmt_int(eoy26) if eoy26 is not None else "—",
                fmt_delta((eoy26 - base) if eoy26 is not None else 0.0) if eoy26 is not None else "—",
            ]
        rows.append(row)
    return rows


def _table(data: List[List[str]], col_widths: List[float] = None) -> Table:
    kwargs = {"hAlign": 'LEFT'}
    if col_widths:
        kwargs["colWidths"] = col_widths
    t = Table(data, **kwargs)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER_BG),
        ('TEXTCOLOR',(0,0),(-1,0),TABLE_HEADER_TEXT),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN',(0,0),(-1,0),'LEFT'),
        ('ALIGN',(1,1),(-1,-1),'RIGHT'),
        ('ALIGN',(0,1),(0,-1),'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, ROW_ALT_BG]),
        ('TEXTCOLOR', (0,1), (-1,-1), SLATE_900),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.6, CARD_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor('#f1f5f9')),
    ]))
    return t


def create_projections_pdf(
    projections_path: str,
    out_pdf: str,
    work_dir: str = "output",
    license_cap: float = 15000.0,
) -> None:
    with open(projections_path, "r", encoding="utf-8") as f:
        proj = json.load(f)

    out_dir = Path(work_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=letter,
        rightMargin=48,
        leftMargin=48,
        topMargin=54,
        bottomMargin=42,
        title="Deep Security Growth Outlook",
    )
    styles = getSampleStyleSheet()

    base_body = ParagraphStyle(
        'BaseBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.5,
        leading=14, textColor=SLATE_700, spaceAfter=4
    )
    normal = base_body
    small = ParagraphStyle('Small', parent=base_body, fontSize=9, textColor=SLATE_500, spaceAfter=2)
    h1 = ParagraphStyle('ReportTitle', parent=styles['Title'], fontName='Helvetica-Bold',
                         fontSize=24, leading=28, textColor=SLATE_900, spaceAfter=6)
    h2 = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold',
                         fontSize=16, leading=20, textColor=BRAND_RED, spaceBefore=14, spaceAfter=8)
    h3 = ParagraphStyle('SubHeading', parent=styles['Heading3'], fontName='Helvetica-Bold',
                         fontSize=12, leading=16, textColor=SLATE_900, spaceBefore=8, spaceAfter=4)
    caption = ParagraphStyle('Caption', parent=small, fontSize=9, leading=12, textColor=SLATE_500)
    hero_body = ParagraphStyle('HeroBody', parent=base_body, textColor=SLATE_700, spaceAfter=2)
    hero_title = ParagraphStyle('HeroTitle', parent=h1, textColor=SLATE_900)
    hero_meta = ParagraphStyle('HeroMeta', parent=small, alignment=2)
    hero_body_right = ParagraphStyle('HeroBodyRight', parent=small, alignment=2, textColor=SLATE_500)
    stat_label = ParagraphStyle('StatLabel', parent=small, alignment=1, textColor=SLATE_500)
    stat_value = ParagraphStyle('StatValue', parent=styles['Title'], fontName='Helvetica-Bold',
                                fontSize=17, leading=20, textColor=SLATE_900, alignment=1, spaceAfter=2)
    stat_note = ParagraphStyle('StatNote', parent=small, alignment=1)
    block_title_style = ParagraphStyle(
        'BlockTitle', parent=h3, alignment=1, fontSize=13, leading=18,
        textColor=colors.white, spaceBefore=0, spaceAfter=4
    )
    header_style = ParagraphStyle(
        'TableHeader',
        parent=small,
        alignment=0,
        fontName='Helvetica-Bold',
        textColor=TABLE_HEADER_TEXT,
    )
    body_left_style = ParagraphStyle('TableBodyLeft', parent=base_body, alignment=0)
    body_right_style = ParagraphStyle('TableBodyRight', parent=base_body, alignment=2)
    delta_style = ParagraphStyle('TableDelta', parent=base_body, alignment=2, fontName='Helvetica-Bold')

    story = []

    def make_header(text: str) -> Paragraph:
        return Paragraph(text, header_style)

    def fmt_text(text: str) -> Paragraph:
        return Paragraph(text, body_left_style)

    def fmt_int(value: float) -> Paragraph:
        val = int(round(value))
        return Paragraph(f'<para align="right">{val:,}</para>', body_right_style)

    def fmt_delta(value: float) -> Paragraph:
        val = int(round(value))
        if val > 0:
            sign = "+"
            color = "#059669"  # Emerald
        elif val < 0:
            sign = "-"
            color = "#dc2626"  # Red
            val = abs(val)
        else:
            sign = ""
            color = "#6b7280"
        return Paragraph(
            f'<para align="right"><font color="{color}"><b>{sign}{val:,}</b></font></para>',
            delta_style,
        )

    def format_signed(value: float) -> str:
        val = int(round(value))
        if val > 0:
            return f"+{val:,}"
        if val < 0:
            return f"{val:,}"
        return "0"

    def delta_color(value: float) -> str:
        if value > 0:
            return "#dc2626"
        if value < 0:
            return "#059669"
        return "#6b7280"

    def stat_card(title: str, value: str, note: str = "", tone: str = "neutral") -> Table:
        note_colors = {
            "positive": "#0f766e",
            "negative": "#b91c1c",
            "neutral": "#6b7280",
        }
        rows: List[List[Paragraph]] = [
            [Paragraph(title, stat_label)],
            [Paragraph(value, stat_value)],
        ]
        if note:
            color = note_colors.get(tone, note_colors["neutral"])
            rows.append([Paragraph(f"<font color='{color}'>{note}</font>", stat_note)])
        card = Table(rows, hAlign='LEFT')
        card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('BOX', (0,0), (-1,-1), 0.6, CARD_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        return card

    # Derive data window (e.g., Jan–Jun 2025)
    actual_series = proj.get("actual", [])
    first_m = actual_series[0]["month"] if actual_series else None
    last_m = proj.get("basis_last_month") or (actual_series[-1]["month"] if actual_series else None)
    def fmt_mon(m):
        try:
            dt = datetime.strptime(m, "%Y-%m")
            return dt.strftime("%b %Y")
        except Exception:
            return m or ""
    data_window = None
    if first_m and last_m:
        same_year = first_m[:4] == last_m[:4]
        if same_year:
            # e.g., Jan–Jun 2025
            data_window = f"{datetime.strptime(first_m, '%Y-%m').strftime('%b')}–{datetime.strptime(last_m, '%Y-%m').strftime('%b %Y')}"
        else:
            data_window = f"{fmt_mon(first_m)} to {fmt_mon(last_m)}"

    # Cover / Intro
    intro_line = "Projected activated instance growth based on current Trend Micro usage."
    coverage_text = ""
    if data_window and last_m:
        coverage_text = f"Data through {fmt_mon(last_m)}<br/>Coverage: {data_window}"
    elif last_m:
        coverage_text = f"Data through {fmt_mon(last_m)}"

    report_date = datetime.now().strftime("%b %d, %Y")
    hero = Table(
        [
            [
                Paragraph("Deep Security Growth Outlook", hero_title),
                Paragraph(report_date, hero_meta),
            ],
            [
                Paragraph(intro_line, hero_body),
                Paragraph(coverage_text or "&nbsp;", hero_body_right),
            ],
        ],
        colWidths=[doc.width * 0.68, doc.width * 0.32],
        hAlign='LEFT',
    )
    hero.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('LINEABOVE', (0,0), (-1,0), 3, BRAND_RED),
        ('BOX', (0,0), (-1,-1), 0.6, CARD_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(hero)
    story.append(Spacer(1, 16))

    # Methodology
    story.append(Paragraph("How We Forecast", h2))
    method_points = [
        ListItem(Paragraph("<b>Linear Trend</b> extends the run rate observed across the full time series.", normal), bulletColor=BRAND_RED),
        ListItem(Paragraph("<b>Geometric Decay (Most Conservative)</b> allows growth to taper month over month, following recent slowdowns.", normal), bulletColor=BRAND_RED),
        ListItem(Paragraph("<b>Rolling Avg Last 3 Months</b> leans on the momentum from your three most recent submissions.", normal), bulletColor=BRAND_RED),
    ]
    story.append(ListFlowable(
        method_points,
        bulletType='bullet',
        start='circle',
        bulletFontName='Helvetica',
        bulletFontSize=8,
        bulletColor=BRAND_RED,
        leftIndent=14,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Muted bands in each chart highlight where we carried forward prior counts to bridge missing submissions.", caption))
    story.append(Spacer(1, 14))

    # Executive Summary (Overall)
    actual_points = proj.get("actual") or []
    base = actual_points[-1]["activated_instances"] if actual_points else 0
    scenarios = proj.get("scenarios") or {}

    story.append(Paragraph("What This Means", h2))

    base_note = f"As of {fmt_mon(last_m)}" if last_m else "Latest submission"
    license_delta = base - license_cap
    cards = [
        stat_card("Current Activated", f"{int(round(base)):,}", base_note),
        stat_card(
            "Δ vs License",
            f"<font color='{delta_color(license_delta)}'><b>{format_signed(license_delta)}</b></font>",
            f"License cap {int(round(license_cap)):,}",
            tone='negative' if license_delta > 0 else ('positive' if license_delta < 0 else 'neutral'),
        ),
    ]

    cards_table = Table([cards], colWidths=[doc.width / len(cards)] * len(cards), hAlign='LEFT') if cards else None
    if cards_table:
        cards_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(cards_table)

    story.append(Spacer(1, 14))

    story.append(Paragraph(
        "Growth Estimate Focus",
        h3,
    ))

    sc = scenarios.get("decay") or {}
    eoy25 = sc.get("EOY_2025")
    eoy26 = sc.get("EOY_2026")
    label = SCENARIO_NAMES.get("decay", sc.get('name', 'Geometric Decay'))

    def growth_color(value: float) -> str:
        return "#059669" if value >= 0 else "#dc2626"

    def license_delta_color(value: float) -> str:
        return "#dc2626" if value > 0 else ("#059669" if value < 0 else "#6b7280")

    rows: List[List[Paragraph]] = [
        [
            Paragraph("Horizon", header_style),
            Paragraph("Activated Instances", header_style),
            Paragraph("Δ vs Today", header_style),
            Paragraph("Δ vs License Cap (15K)", header_style),
        ]
    ]

    def add_row(label_txt: str, value: float) -> None:
        if value is None:
            return
        delta_today = value - base
        delta_license = value - license_cap
        rows.append([
            Paragraph(label_txt, body_left_style),
            Paragraph(f"{int(round(value)):,}", body_right_style),
            Paragraph(
                f"<font color='{growth_color(delta_today)}'>{format_signed(delta_today)}</font>",
                body_right_style,
            ),
            Paragraph(
                f"<font color='{license_delta_color(delta_license)}'>{format_signed(delta_license)}</font>",
                body_right_style,
            ),
        ])

    add_row("EOY 2025 Projection", eoy25)
    add_row("EOY 2026 Projection", eoy26)

    title_para = Paragraph(f"<b>{label}</b>", block_title_style)
    header_card = Table([[title_para]], colWidths=[doc.width], hAlign='LEFT')
    header_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BRAND_RED),
        ('BOX', (0,0), (-1,-1), 0.8, BRAND_RED),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))

    col_widths = [doc.width * 0.30, doc.width * 0.22, doc.width * 0.24, doc.width * 0.24]
    data_table = Table(rows, colWidths=col_widths)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0,0), (-1,0), TABLE_HEADER_TEXT),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, ROW_ALT_BG]),
        ('BOX', (0,0), (-1,-1), 0.6, CARD_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor('#f1f5f9')),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))

    story.append(header_card)
    story.append(Spacer(1, 10))
    story.append(data_table)
    story.append(Spacer(1, 6))

    if eoy26 is not None:
        story.append(Paragraph("Use the EOY 2026 projection as the estimate for renewal sizing.", caption))
    story.append(Spacer(1, 16))

    # Helper to add a section for a subset
    def add_section(title: str, subset: Dict, img_name: str, first: bool = False):
        # Build a cohesive block and keep together to avoid awkward splits
        flow = []
        flow.append(Paragraph(title, h2))
        img_path = out_dir / img_name
        save_projection_subset_png(subset, str(img_path), title)
        chart_width = doc.width
        chart_height = 3.6 * inch
        flow.append(Image(str(img_path), width=chart_width, height=chart_height))
        flow.append(Paragraph("Actual & Forecasted Activated Instances", caption))
        flow.append(Spacer(1, 10))
        include_license = title == "Overall"
        summary_rows = [[make_header("Metric"), make_header("Activated Instances")]] + _summary_rows(
            subset, license_cap, fmt_int, fmt_delta, include_license
        )
        flow.append(Paragraph("Snapshot", h3))
        summary_widths = [doc.width * 0.45, doc.width * 0.35]
        flow.append(_table(summary_rows, col_widths=summary_widths))
        flow.append(Spacer(1, 6))
        rows = _eoY_rows(subset, license_cap, make_header, fmt_text, fmt_int, fmt_delta, include_license)
        base_widths = [0.28, 0.18, 0.18, 0.18, 0.18]
        col_widths = [doc.width * w for w in base_widths]
        flow.append(Paragraph("Growth Estimates", h3))
        flow.append(_table(rows, col_widths=col_widths))
        flow.append(Spacer(1, 16))
        if not first:
            story.append(PageBreak())
        story.append(KeepTogether(flow))

    # Overall
    add_section("Overall", proj, "proj_overall.png", first=True)

    # By cloud provider
    for cp, subset in (proj.get("by_cloud_provider") or {}).items():
        add_section(f"By Cloud: {cp}", subset, f"proj_cloud_{cp}.png")

    # By service category
    for cat_key in ["common services", "mission partners"]:
        subset = (proj.get("by_category") or {}).get(cat_key)
        if subset:
            add_section(f"Service Category: {cat_key.title()}", subset, f"proj_cat_{cat_key.replace(' ', '_')}.png")

    # By category and cloud provider (compact list)
    catcp = proj.get("by_category_and_cloud_provider") or {}
    for key, subset in catcp.items():
        add_section(f"Category x Cloud: {key}", subset, f"proj_{key.replace(' ', '_').replace(':','_')}.png")

    def _draw_header_footer(canvas, doc_obj):
        canvas.saveState()
        top_y = doc_obj.height + doc_obj.topMargin + 6
        canvas.setFillColor(BRAND_RED)
        canvas.rect(doc_obj.leftMargin, top_y, doc_obj.width, 2, fill=1, stroke=0)
        canvas.setFillColor(SLATE_500)
        canvas.setFont("Helvetica", 9)
        canvas.drawString(doc_obj.leftMargin, doc_obj.bottomMargin - 18, f"Prepared {report_date}")
        canvas.drawRightString(doc_obj.leftMargin + doc_obj.width, doc_obj.bottomMargin - 18, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create projections PDF report")
    parser.add_argument("--projections", default="output/projections.json")
    parser.add_argument("--out", default="output/growth_projections.pdf")
    parser.add_argument("--work-dir", default="output")
    parser.add_argument("--license-cap", type=float, default=15000.0)
    args = parser.parse_args()

    create_projections_pdf(args.projections, args.out, args.work_dir, args.license_cap)
    print(f"Wrote PDF to {args.out}")


if __name__ == "__main__":
    main()
