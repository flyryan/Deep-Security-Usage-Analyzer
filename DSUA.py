"""
Trend Micro Deep Security Usage Analyzer (DSUA)

This script analyzes Trend Micro Deep Security module usage across different environments
and generates comprehensive reports, including metrics, visualizations, and an HTML report.
"""

from datetime import datetime
from pathlib import Path
import sys
from modules.logger_setup import setup_logging
from modules.data_loader import DataLoader
from modules.metrics_calculator import MetricsCalculator
from modules.visualization import Visualizer
from modules.report_generator import ReportGenerator

def main():
    """
    Main function to run the Trend Micro Deep Security Usage Analyzer.
    """
    logger = setup_logging()
    try:
        # Initialize Data Loader
        data_loader = DataLoader(directory='.', logger=logger)
        data = data_loader.load_data()
        
        # Calculate Metrics
        metrics_calculator = MetricsCalculator(data=data, logger=logger)
        overall_metric = metrics_calculator.compute_overall_metric()
        
        # Create Visualizations
        visualizer = Visualizer(metrics=metrics_calculator, logger=logger)
        visualizations = visualizer.create_visualizations()
        
        # Generate Report
        report_generator = ReportGenerator(logger=logger)
        report_generator.generate_html_report(metrics=metrics_calculator, visualizations=visualizations, output_path=Path('report.html'))
        report_generator.create_pdf_report(html_path=Path('report.html'), pdf_path=Path('report.pdf'))
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()