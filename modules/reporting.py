from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate
from pathlib import Path
from typing import Dict
import logging
import matplotlib.pyplot as plt
from jinja2 import Template
import os

class ReportGenerator:
    def create_pdf_report(self, context: Dict, pdf_path: Path) -> None:
        # ...existing PDF report creation code...
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        elements = []
        # Add elements to PDF
        doc.build(elements)

    def generate_report(self, context: Dict, visualizations: Dict[str, plt.Figure]) -> None:
        # Load the HTML template
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'report_template.html')
        with open(template_path, 'r') as template_file:
            template = Template(template_file.read())
        
        # Save visualizations as images and update paths
        image_dir = os.path.join(os.path.dirname(template_path), 'images')
        os.makedirs(image_dir, exist_ok=True)
        for name, fig in visualizations.items():
            img_path = os.path.join(image_dir, f"{name}.png")
            fig.savefig(img_path, format='png')
            visualizations[name] = f'images/{name}.png'
        
        # Render the HTML with context and visualizations
        report_content = template.render(context=context, visualizations=visualizations)
        with open("report.html", "w") as f:
            f.write(report_content)
