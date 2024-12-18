"""
Report generation functionality for the Deep Security Usage Analyzer.
"""
from typing import Dict
import logging
import base64
import re
from pathlib import Path
from datetime import datetime
from jinja2 import Template
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# HTML report template
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Deep Security Usage Analyzer Report</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6;
            color: #333;
        }
        .section { 
            margin-bottom: 30px; 
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1, h2 { 
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0; 
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }
        th { 
            background-color: #f5f5f5; 
            color: #2c3e50;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        .visualization { 
            margin: 20px 0;
            text-align: center;
        }
        .visualization img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .highlight { 
            background-color: #fff3cd; 
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .timestamp {
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>Deep Security Usage Analyzer Report</h1>
    <p class="timestamp">Generated on: {{ timestamp }}</p>
    
    <div class="section">
        <h2>Overall Metrics</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.overall.total_instances | default(0) }}</div>
                <div class="metric-label">Total Unique Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.overall.activated_instances | default(0) }}</div>
                <div class="metric-label">Activated Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.overall.inactive_instances | default(0) }}</div>
                <div class="metric-label">Inactive Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "{:,.1f}".format(metrics.overall.total_hours | default(0.0) | round(1)) }}</div>
                <div class="metric-label">Total Hours</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Environment Distribution</h2>
        <table>
            <tr>
                <th>Environment</th>
                <th>Total Hosts</th>
                <th>Activated Hosts</th>
                <th>Most Used Module</th>
                <th>Max Concurrent</th>
                <th>Total Hours</th>
            </tr>
            {% for env, data in metrics.by_environment.items() %}
            <tr>
                <td>{{ env }}</td>
                <td>{{ data.total_instances }}</td>
                <td>{{ data.activated_instances }}</td>
                <td>{{ data.most_common_module }}</td>
                <td>{{ data.max_concurrent if data.max_concurrent else 'None' }}</td>
                <td>
                    {% if data.total_utilization_hours is defined and data.total_utilization_hours != 'N/A' %}
                        {{ "{:,.1f}".format(data.total_utilization_hours) }}
                    {% else %}
                        N/A
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="section">
        <h2>Module Usage Analysis</h2>
        <div class="visualization">
            <h3>Security Module Usage by Environment</h3>
            <img src="module_usage.png" alt="Module Usage Distribution">
        </div>
        <div class="visualization">
            <h3>Environment Distribution</h3>
            <img src="environment_distribution.png" alt="Environment Distribution">
        </div>
        <div class="visualization">
            <h3>Activated Instances Seen Monthly</h3>
            <img src="activated_instances_growth.png" alt="Growth of Activated Instances">
        </div>
    </div>
    
    <div class="section">
        <h2>Statistics Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Unique Instances</td>
                <td>{{ "{:,}".format(metrics.overall.total_instances) }}</td>
            </tr>
            <tr>
                <td>Instances Running at Least One Module</td>
                <td>{{ "{:,}".format(metrics.overall.activated_instances) }}</td>
            </tr>
            <tr>
                <td>Instances Not Running Any Modules</td>
                <td>{{ "{:,}".format(metrics.overall.inactive_instances) }}</td>
            </tr>
            <tr>
                <td>Total Hours</td>
                <td>{{ "{:,.1f}".format(metrics.overall.total_hours) }}</td>
            </tr>
            <tr>
                <td>Hours for Instances with Modules</td>
                <td>{{ "{:,.1f}".format(metrics.overall.activated_hours) }}</td>
            </tr>
            <tr>
                <td>Hours for Instances without Modules</td>
                <td>{{ "{:,.1f}".format(metrics.overall.inactive_hours) }}</td>
            </tr>
            <tr>
                <td>Average Monthly Growth (Activated Instances)</td>
                <td>{{ "%.1f"|format(metrics.monthly.average_monthly_growth) }} instances</td>
            </tr>
            <tr>
                <td>Unknown Environment Instances</td>
                <td>{{ "{:,}".format(metrics.by_environment.Unknown.total_instances if metrics.by_environment.Unknown else 0) }}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>Monthly Data Analysis</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.monthly.total_months }}</div>
                <div class="metric-label">Total Months with Data</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.monthly.date_range }}</div>
                <div class="metric-label">Date Range</div>
            </div>
        </div>
        
        <table>
            <tr>
                <th>Month</th>
                <th>Activated Instances</th>
                <th>Max Concurrent Instances</th>
                <th>Avg Modules/Host</th>
            </tr>
            {% if metrics.monthly and metrics.monthly.data %}
                {% for month in metrics.monthly.data %}
                <tr>
                    <td>{{ month.month | default('None') }}</td>
                    <td>
                        {{ month.activated_instances | default(0) }}
                    </td>
                    <td>{{ month.max_concurrent | default(0) }}</td>
                    <td>{{ "%.2f"|format(month.avg_modules_per_host | default(0.0)) }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr>
                    <td colspan="5">No monthly data available</td>
                </tr>
            {% endif %}
        </table>
    </div>

    {% if metrics.by_environment.Unknown and metrics.by_environment.Unknown.total_instances > 0 %}
    <div class="section highlight">
        <h2>Unknown Environment Analysis</h2>
        <p>Number of hosts in unknown environment: {{ "{:,}".format(metrics.by_environment.Unknown.total_instances) }}</p>
        <p>Common patterns found in unknown hosts:</p>
        <ul>
        {% for pattern in unknown_patterns %}
            <li>{{ pattern }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

</body>
</html>
"""

def embed_images_in_html(html_content: str, output_dir: Path, visualizations: Dict[str, plt.Figure]) -> str:
    """
    Embed existing PNG files from the output directory into the HTML content as base64 strings.

    Args:
        html_content (str): The HTML content to embed images into
        output_dir (Path): Directory containing the PNG files
        visualizations (Dict[str, plt.Figure]): Dictionary of visualization names

    Returns:
        str: The HTML content with embedded images
    """
    for name in visualizations.keys():
        try:
            # Get the path to the existing PNG file
            png_path = output_dir / f'{name}.png'
            
            if png_path.exists():
                # Read the existing PNG file
                with open(png_path, 'rb') as img_file:
                    img_data = img_file.read()
                
                # Encode the image as base64
                img_str = base64.b64encode(img_data).decode('utf-8')
                img_tag = f'data:image/png;base64,{img_str}'
                
                logger.debug(f"Embedding existing PNG for {name}")

                # Replace image source with embedded base64 string
                html_content = re.sub(
                    rf'<img\s+src=["\']{re.escape(name)}\.png["\']\s+alt=["\'].*?["\']\s*/?>',
                    f'<img src="{img_tag}" alt="{name.replace("_", " ").title()}">',
                    html_content,
                    flags=re.IGNORECASE
                )
            else:
                logger.warning(f"PNG file not found for {name}: {png_path}")
                
        except Exception as e:
            logger.error(f"Error embedding image {name}: {str(e)}")
            continue

    return html_content

def create_pdf_report(context: Dict, pdf_path: Path) -> None:
    """
    Create a PDF report using ReportLab.

    Args:
        context (Dict): The context data for the report
        pdf_path (Path): The file path to save the PDF
    """
    try:
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Center', alignment=1))

        # Title
        story.append(Paragraph("Deep Security Usage Analyzer Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Timestamp
        story.append(Paragraph(f"Generated on: {context['timestamp']}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Overall Metrics
        story.append(Paragraph("Overall Metrics", styles['Heading2']))
        overall_data = [
            ["Total Unique Instances", f"{context['metrics']['overall']['total_instances']:,}"],
            ["Activated Instances", f"{context['metrics']['overall']['activated_instances']:,}"],
            ["Inactive Instances", f"{context['metrics']['overall']['inactive_instances']:,}"],
            ["Total Hours", f"{context['metrics']['overall']['total_hours']:.1f}"],
            ["Activated Hours", f"{context['metrics']['overall']['activated_hours']:.1f}"],
            ["Inactive Hours", f"{context['metrics']['overall']['inactive_hours']:.1f}"]
        ]
        table = Table(overall_data, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 24))

        # Environment Distribution
        story.append(Paragraph("Environment Distribution", styles['Heading2']))
        env_data = [["Environment", "Total Hosts", "Activated Hosts", "Most Used Module", "Max Concurrent", "Total Hours"]]
        for env, data in context['metrics']['by_environment'].items():
            env_data.append([
                env,
                f"{data['total_instances']}",
                f"{data['activated_instances']}",
                data['most_common_module'],
                f"{data['max_concurrent'] if data['max_concurrent'] else 'None'}",
                f"{data['total_utilization_hours']:.1f}" if isinstance(data['total_utilization_hours'], (int, float)) else "None"
            ])
        table = Table(env_data, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 24))

        # Module Usage Analysis
        story.append(Paragraph("Module Usage Analysis", styles['Heading2']))
        # Embed Module Usage Image
        if (Path.cwd() / 'output' / 'module_usage.png').exists():
            img_path = Path.cwd() / 'output' / 'module_usage.png'
            story.append(Image(str(img_path), width=6*inch, height=4*inch))
            story.append(Spacer(1, 12))
        # Embed Environment Distribution Image
        if (Path.cwd() / 'output' / 'environment_distribution.png').exists():
            img_path = Path.cwd() / 'output' / 'environment_distribution.png'
            story.append(Image(str(img_path), width=6*inch, height=6*inch))
            story.append(Spacer(1, 12))
        # Embed Activated Instances Growth Image
        if (Path.cwd() / 'output' / 'activated_instances_growth.png').exists():
            img_path = Path.cwd() / 'output' / 'activated_instances_growth.png'
            story.append(Paragraph("Growth of Activated Instances Over Time", styles['Heading3']))
            story.append(Image(str(img_path), width=6*inch, height=4*inch))
            story.append(Spacer(1, 12))

        # Statistics Summary
        story.append(Paragraph("Statistics Summary", styles['Heading2']))
        stats_data = [
            ["Metric", "Value"],
            ["Total Unique Instances", f"{context['metrics']['overall']['total_instances']:,}"],
            ["Instances Running at Least One Module", f"{context['metrics']['overall']['activated_instances']:,}"],
            ["Instances Not Running Any Modules", f"{context['metrics']['overall']['inactive_instances']:,}"],
            ["Total Hours", f"{context['metrics']['overall']['total_hours']:.1f}"],
            ["Hours for Instances with Modules", f"{context['metrics']['overall']['activated_hours']:.1f}"],
            ["Hours for Instances without Modules", f"{context['metrics']['overall']['inactive_hours']:.1f}"],
            ["Max Concurrent Usage", f"{context['metrics']['overall_metrics']['max_concurrent_overall']:,}"],
            ["Unknown Environment Instances", f"{context['metrics']['by_environment'].get('Unknown', {}).get('total_instances', 0):,}"]
        ]
        table = Table(stats_data, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 24))

        # Monthly Data Analysis
        story.append(Paragraph("Monthly Data Analysis", styles['Heading2']))
        monthly_data = [
            ["Month", "Activated Instances", "Max Concurrent", "Avg Modules/Host", "Total Hours"]
        ]
        for month in context['metrics']['monthly']['data']:
            monthly_data.append([
                month['month'],
                month['activated_instances'],
                month['max_concurrent'],
                f"{month['avg_modules_per_host']:.2f}",
                f"{month['total_hours']:.1f}"
            ])
        table = Table(monthly_data, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 24))

        # Data Gaps
        if context['metrics']['monthly']['data_gaps']:
            story.append(Paragraph("Data Gaps Detected", styles['Heading2']))
            for gap in context['metrics']['monthly']['data_gaps']:
                story.append(Paragraph(f"- {gap}", styles['Normal']))
            story.append(Spacer(1, 12))

        # Unknown Environment Analysis
        if context['metrics']['by_environment'].get('Unknown') and \
           context['metrics']['by_environment']['Unknown']['total_instances'] > 0:
            story.append(Paragraph("Unknown Environment Analysis", styles['Heading2']))
            story.append(Paragraph(f"Number of hosts in unknown environment: {context['metrics']['by_environment']['Unknown']['total_instances']:,}", styles['Normal']))
            story.append(Paragraph("Common patterns found in unknown hosts:", styles['Normal']))
            for pattern in context['unknown_patterns']:
                story.append(Paragraph(f"- {pattern}", styles['Normal']))
            story.append(Spacer(1, 12))

        doc.build(story)

    except Exception as e:
        logger.error(f"Failed to create PDF report: {str(e)}")

def generate_report(metrics: Dict, output_dir: Path, visualizations: Dict[str, plt.Figure]) -> None:
    """
    Generate comprehensive HTML and PDF reports of the analysis.

    Args:
        metrics (Dict): Dictionary containing all metrics data
        output_dir (Path): Directory to save the reports
        visualizations (Dict[str, plt.Figure]): Dictionary of visualization figures
    """
    try:
        # Create report context
        report_context = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': metrics,
            'unknown_patterns': []
        }
        
        # Add unknown patterns if they exist
        if 'Unknown' in metrics.get('by_environment', {}):
            report_context['unknown_patterns'] = metrics['by_environment']['Unknown'].get('patterns', [])[:10]
        
        # Render template
        template = Template(REPORT_TEMPLATE)
        report_html = template.render(**report_context)
        
        # Embed existing images in HTML
        report_html = embed_images_in_html(report_html, output_dir, visualizations)
        
        # Save HTML report
        report_path = output_dir / 'report.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        logger.info(f"✓ Saved HTML report to '{report_path}'")
        
        # Create PDF report
        create_pdf_report(report_context, output_dir / 'report.pdf')
        logger.info(f"✓ Saved PDF report to '{output_dir / 'report.pdf'}'")
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        raise
