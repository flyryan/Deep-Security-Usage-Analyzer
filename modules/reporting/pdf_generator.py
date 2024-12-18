"""
PDF report generation functionality for Deep Security Usage Analyzer.
"""
from typing import Dict
from pathlib import Path
import logging
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

def generate_pdf_report(metrics: Dict, output_dir: Path, visualizations: Dict[str, plt.Figure]) -> None:
    """
    Create a PDF report using ReportLab.

    Args:
        metrics (Dict): Dictionary containing all metrics data
        output_dir (Path): Directory containing visualization images
        visualizations (Dict[str, plt.Figure]): Dictionary of visualization figures
    """
    try:
        pdf_path = output_dir / 'report.pdf'
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Center', alignment=1))

        # Title
        story.append(Paragraph("Deep Security Usage Analyzer Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Overall Metrics
        story.append(Paragraph("Overall Metrics", styles['Heading2']))
        overall_data = [
            ["Total Unique Instances", f"{metrics['overall']['total_instances']:,}"],
            ["Activated Instances", f"{metrics['overall']['activated_instances']:,}"],
            ["Inactive Instances", f"{metrics['overall']['inactive_instances']:,}"],
            ["Total Hours", f"{metrics['overall']['total_hours']:.1f}"],
            ["Activated Hours", f"{metrics['overall']['activated_hours']:.1f}"],
            ["Inactive Hours", f"{metrics['overall']['inactive_hours']:.1f}"]
        ]
        table = _create_table(overall_data)
        story.append(table)
        story.append(Spacer(1, 24))

        # Environment Distribution
        story.append(Paragraph("Environment Distribution", styles['Heading2']))
        env_data = [["Environment", "Total Hosts", "Activated Hosts", "Most Used Module", "Max Concurrent", "Total Hours"]]
        for env, data in metrics['by_environment'].items():
            env_data.append([
                env,
                f"{data['total_instances']}",
                f"{data['activated_instances']}",
                data['most_common_module'],
                f"{data['max_concurrent'] if data['max_concurrent'] else 'None'}",
                f"{data['total_utilization_hours']:.1f}" if isinstance(data['total_utilization_hours'], (int, float)) else "None"
            ])
        table = _create_table(env_data)
        story.append(table)
        story.append(Spacer(1, 24))

        # Module Usage Analysis
        story.append(Paragraph("Module Usage Analysis", styles['Heading2']))
        _add_visualizations(story, output_dir, visualizations)

        # Statistics Summary
        story.append(Paragraph("Statistics Summary", styles['Heading2']))
        stats_data = [
            ["Metric", "Value"],
            ["Total Unique Instances", f"{metrics['overall']['total_instances']:,}"],
            ["Instances Running at Least One Module", f"{metrics['overall']['activated_instances']:,}"],
            ["Instances Not Running Any Modules", f"{metrics['overall']['inactive_instances']:,}"],
            ["Total Hours", f"{metrics['overall']['total_hours']:.1f}"],
            ["Hours for Instances with Modules", f"{metrics['overall']['activated_hours']:.1f}"],
            ["Hours for Instances without Modules", f"{metrics['overall']['inactive_hours']:.1f}"],
            ["Max Concurrent Usage", f"{metrics['overall_metrics']['max_concurrent_overall']:,}"],
            ["Unknown Environment Instances", f"{metrics['by_environment'].get('Unknown', {}).get('total_instances', 0):,}"]
        ]
        table = _create_table(stats_data)
        story.append(table)
        story.append(Spacer(1, 24))

        # Monthly Data Analysis
        story.append(Paragraph("Monthly Data Analysis", styles['Heading2']))
        monthly_data = [
            ["Month", "Activated Instances", "Max Concurrent", "Avg Modules/Host", "Total Hours"]
        ]
        for month in metrics['monthly']['data']:
            monthly_data.append([
                month['month'],
                month['activated_instances'],
                month['max_concurrent'],
                f"{month['avg_modules_per_host']:.2f}",
                f"{month['total_hours']:.1f}"
            ])
        table = _create_table(monthly_data)
        story.append(table)
        story.append(Spacer(1, 24))

        # Data Gaps
        if metrics['monthly']['data_gaps']:
            story.append(Paragraph("Data Gaps Detected", styles['Heading2']))
            for gap in metrics['monthly']['data_gaps']:
                story.append(Paragraph(f"- {gap}", styles['Normal']))
            story.append(Spacer(1, 12))

        # Unknown Environment Analysis
        if metrics['by_environment'].get('Unknown') and \
           metrics['by_environment']['Unknown']['total_instances'] > 0:
            story.append(Paragraph("Unknown Environment Analysis", styles['Heading2']))
            story.append(Paragraph(
                f"Number of hosts in unknown environment: {metrics['by_environment']['Unknown']['total_instances']:,}",
                styles['Normal']
            ))
            story.append(Paragraph("Common patterns found in unknown hosts:", styles['Normal']))
            for pattern in metrics['by_environment']['Unknown'].get('patterns', []):
                story.append(Paragraph(f"- {pattern}", styles['Normal']))
            story.append(Spacer(1, 12))

        doc.build(story)
        logger.info(f"✓ Saved PDF report to '{pdf_path}'")

    except Exception as e:
        logger.error(f"Failed to create PDF report: {str(e)}")
        raise

def _create_table(data: list) -> Table:
    """
    Create a formatted table for the PDF report.

    Args:
        data (list): List of rows for the table

    Returns:
        Table: Formatted ReportLab Table object
    """
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    return table

def _add_visualizations(story: list, output_dir: Path, visualizations: Dict[str, plt.Figure]) -> None:
    """
    Add visualization images to the PDF report.

    Args:
        story (list): List of PDF elements
        output_dir (Path): Directory containing visualization images
        visualizations (Dict[str, plt.Figure]): Dictionary of visualization figures
    """
    # Module Usage Image
    if (output_dir / 'module_usage.png').exists():
        img_path = output_dir / 'module_usage.png'
        story.append(Image(str(img_path), width=6*inch, height=4*inch))
        story.append(Spacer(1, 12))

    # Environment Distribution Image
    if (output_dir / 'environment_distribution.png').exists():
        img_path = output_dir / 'environment_distribution.png'
        story.append(Image(str(img_path), width=6*inch, height=6*inch))
        story.append(Spacer(1, 12))

    # Activated Instances Growth Image
    if (output_dir / 'activated_instances_growth.png').exists():
        img_path = output_dir / 'activated_instances_growth.png'
        story.append(Paragraph("Growth of Activated Instances Over Time", getSampleStyleSheet()['Heading3']))
        story.append(Image(str(img_path), width=6*inch, height=4*inch))
        story.append(Spacer(1, 12))
