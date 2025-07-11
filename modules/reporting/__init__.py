"""
Report generation package for Deep Security Usage Analyzer.
"""
from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
from .html_generator import generate_html_report
from .pdf_generator import generate_pdf_report
from .image_handler import embed_images_in_html

def generate_report(metrics: Dict, output_dir: Path, visualizations: Dict[str, plt.Figure]) -> None:
    """
    Generate comprehensive HTML and PDF reports of the analysis.

    Args:
        metrics (Dict): Dictionary containing all metrics data
        output_dir (Path): Directory to save the reports
        visualizations (Dict[str, plt.Figure]): Dictionary of visualization figures
    """
    # Generate HTML report
    report_html = generate_html_report(metrics)
    
    # Embed images in HTML
    report_html = embed_images_in_html(report_html, output_dir, visualizations)
    
    # Save HTML report
    report_path = output_dir / 'report.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_html)

    # Export metrics as JSON for interactive report
    from .html_generator import export_metrics_json
    metrics_json_path = output_dir / 'metrics.json'

    # Write interactive HTML report template

    # Write interactive HTML report with embedded metrics
    from .html_generator import write_interactive_report_html_embedded
    write_interactive_report_html_embedded(metrics, str(output_dir))


    export_metrics_json(metrics, str(metrics_json_path))


    # Generate modern interactive report
    from .html_generator import generate_modern_interactive_report
    template_path = str(Path(__file__).parent / 'interactive_report_template.html')
    output_path = str(output_dir / 'interactive_report.html')
    generate_modern_interactive_report(metrics, template_path, output_path)

    
    # Generate PDF report
    generate_pdf_report(metrics, output_dir, visualizations)
