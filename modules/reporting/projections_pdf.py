import json
from pathlib import Path
from typing import Dict, List, Tuple, Callable

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.units import inch

from .projections_plot import save_projection_subset_png
from datetime import datetime


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
            make_header("Scenario"),
            make_header("EOY 2025"),
            make_header("Δ vs License<br/>(2025)"),
            make_header("EOY 2026"),
            make_header("Δ vs License<br/>(2026)"),
        ]
    else:
        header = [
            make_header("Scenario"),
            make_header("EOY 2025"),
            make_header("Δ vs Current<br/>(2025)"),
            make_header("EOY 2026"),
            make_header("Δ vs Current<br/>(2026)"),
        ]

    rows: List[List[object]] = [header]
    for key in ["linear", "decay", "avg_last3"]:
        sc = subset["scenarios"][key]
        eoy25 = sc.get("EOY_2025")
        eoy26 = sc.get("EOY_2026")
        if include_license:
            row: List[object] = [
                fmt_text(sc["name"]),
                fmt_int(eoy25) if eoy25 is not None else "—",
                fmt_delta((eoy25 - license_cap) if eoy25 is not None else 0.0) if eoy25 is not None else "—",
                fmt_int(eoy26) if eoy26 is not None else "—",
                fmt_delta((eoy26 - license_cap) if eoy26 is not None else 0.0) if eoy26 is not None else "—",
            ]
        else:
            row = [
                fmt_text(sc["name"]),
                fmt_int(eoy25) if eoy25 is not None else "—",
                fmt_delta((eoy25 - base) if eoy25 is not None else 0.0) if eoy25 is not None else "—",
                fmt_int(eoy26) if eoy26 is not None else "—",
                fmt_delta((eoy26 - base) if eoy26 is not None else 0.0) if eoy26 is not None else "—",
            ]
        rows.append(row)
    return rows


def _most_likely_scenario(subset: Dict) -> Tuple[str, str]:
    """
    Choose most likely scenario by matching the median of the next-3 predicted monthly adds
    to the median of the last-3 observed monthly adds.
    Returns (scenario_key, scenario_name).
    """
    actual = subset["actual"]
    vals = [p["activated_instances"] for p in actual]
    if len(vals) < 4:
        # Not enough data: default to rolling average as balanced
        sc = subset["scenarios"]["avg_last3"]
        return ("avg_last3", sc["name"])
    last3_adds = [vals[-3] - vals[-4], vals[-2] - vals[-3], vals[-1] - vals[-2]]
    median_last3 = sorted(last3_adds)[1]
    best_key = None
    best_diff = float("inf")
    for key in ["linear", "decay", "avg_last3"]:
        sc = subset["scenarios"][key]
        series = [p["activated_instances"] for p in sc["series"]]
        if not series:
            continue
        # Build the first 3 predicted increments
        first_inc = series[0] - vals[-1]
        next_inc = (series[1] - series[0]) if len(series) > 1 else first_inc
        third_inc = (series[2] - series[1]) if len(series) > 2 else next_inc
        pred_med = sorted([first_inc, next_inc, third_inc])[1]
        diff = abs(pred_med - median_last3)
        if diff < best_diff:
            best_diff = diff
            best_key = key
    name = subset["scenarios"][best_key]["name"] if best_key else "Rolling Avg Last 3 Months (Optimistic)"
    return (best_key or "avg_last3", name)


def _table(data: List[List[str]], col_widths: List[float] = None) -> Table:
    kwargs = {"hAlign": 'LEFT'}
    if col_widths:
        kwargs["colWidths"] = col_widths
    t = Table(data, **kwargs)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.black),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('ALIGN',(1,1),(-1,-1),'RIGHT'),
        ('ALIGN',(0,0),(0,-1),'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
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

    doc = SimpleDocTemplate(out_pdf, pagesize=letter, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=36)
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    h1 = styles['Title']
    h2 = styles['Heading2']
    h3 = styles['Heading3']

    story = []

    header_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'], alignment=1, fontName='Helvetica-Bold'
    )
    body_left_style = ParagraphStyle(
        'TableBodyLeft', parent=styles['Normal'], alignment=0
    )
    body_right_style = ParagraphStyle(
        'TableBodyRight', parent=styles['Normal'], alignment=2
    )
    delta_style = ParagraphStyle(
        'TableDelta', parent=styles['Normal'], alignment=2
    )

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
            color = "#198754"
        elif val < 0:
            sign = "-"
            color = "#dc3545"
            val = abs(val)
        else:
            sign = ""
            color = "#6c757d"
        return Paragraph(
            f'<para align="right"><font color="{color}"><b>{sign}{val:,}</b></font></para>',
            delta_style,
        )

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
    story.append(Paragraph("Growth Outlook", h1))
    story.append(Spacer(1, 6))
    intro_line = "This summary projects activated instance growth using your current usage patterns."
    story.append(Paragraph(intro_line, normal))
    if data_window:
        story.append(Paragraph(f"Data through {fmt_mon(last_m)} (coverage: {data_window}).", normal))
    story.append(Spacer(1, 12))

    # Methodology
    story.append(Paragraph("How We Forecast", h2))
    story.append(Paragraph("We provide three simple, transparent views of the road ahead:", normal))
    story.append(Paragraph("• Linear: extends the overall trend we’ve seen so far.", normal))
    story.append(Paragraph("• Conservative: assumes monthly growth keeps slowing from recent levels.", normal))
    story.append(Paragraph("• Optimistic: assumes the last 3 months are a good guide for the near future.", normal))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Picking a ‘Most Likely’ view: we compare each forecast to your most recent momentum and choose the one that best matches it.", normal))
    story.append(Paragraph("Red shaded regions in the charts highlight months with no underlying data; we carry forward the prior counts so the gap is visible without inflating growth.", normal))
    story.append(Spacer(1, 18))

    # Executive Summary (Overall)
    overall_key, overall_name = _most_likely_scenario(proj)
    base = proj["actual"][-1]["activated_instances"]
    e25 = proj["scenarios"][overall_key].get("EOY_2025")
    e26 = proj["scenarios"][overall_key].get("EOY_2026")
    story.append(Paragraph("What This Means", h2))
    story.append(Paragraph(f"Most likely (overall): {overall_name}", h3))
    if last_m:
        story.append(Paragraph(f"Where you are now (as of {fmt_mon(last_m)}): {round(base):,} activated instances.", normal))
    else:
        story.append(Paragraph(f"Where you are now: {round(base):,} activated instances.", normal))
    story.append(Paragraph(f"Current license assumption: {round(license_cap):,} seats. Current delta: {round(base - license_cap):,}.", normal))
    if e25 is not None:
        story.append(Paragraph(f"By end of 2025: about {round(e25):,} (roughly +{round(e25 - base):,} from today)", normal))
    if e26 is not None:
        story.append(Paragraph(f"By end of 2026: about {round(e26):,} (roughly +{round(e26 - base):,} from today)", normal))
    story.append(Spacer(1, 18))

    # Helper to add a section for a subset
    def add_section(title: str, subset: Dict, img_name: str, first: bool = False):
        # Build a cohesive block and keep together to avoid awkward splits
        flow = []
        flow.append(Paragraph(title, h2))
        img_path = out_dir / img_name
        save_projection_subset_png(subset, str(img_path), title)
        flow.append(Image(str(img_path), width=6.5*inch, height=3.8*inch))
        flow.append(Spacer(1, 6))
        include_license = title == "Overall"
        summary_rows = [[make_header("Summary"), make_header("Value")]] + _summary_rows(
            subset, license_cap, fmt_int, fmt_delta, include_license
        )
        flow.append(_table(summary_rows, col_widths=[130, 90]))
        flow.append(Spacer(1, 4))
        rows = _eoY_rows(subset, license_cap, make_header, fmt_text, fmt_int, fmt_delta, include_license)
        if include_license:
            col_widths = [150, 70, 90, 90, 70, 90]
        else:
            col_widths = [150, 80, 100, 80, 100]
        flow.append(_table(rows, col_widths=col_widths))
        flow.append(Spacer(1, 6))
        key, name = _most_likely_scenario(subset)
        flow.append(Paragraph(f"Most likely view here: {name}", h3))
        flow.append(Paragraph("Tip: use this as the planning baseline; keep the other two as guardrails.", normal))
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

    doc.build(story)


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
