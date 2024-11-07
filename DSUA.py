"""
Trend Micro Deep Security Usage Analyzer (DSUA)

This script analyzes Trend Micro Deep Security module usage across different environments
and generates comprehensive reports, including metrics, visualizations, and an HTML report.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from jinja2 import Template
from io import BytesIO
from reportlab.lib import colors
import sys
import logging

from modules.logger import setup_logging
from modules.data_loader import DataLoader
from modules.metrics_calculator import MetricsCalculator
from modules.visualization import VisualizationCreator
from modules.reporting import ReportGenerator

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
        if not overall_metric:
            logger.error("Metric calculation failed due to missing columns.")
            sys.exit(1)
        
        # Create Visualizations
        visualizer = VisualizationCreator(metrics=metrics_calculator, logger=logger)
        visualizations = visualizer.create_visualizations()
        
        # Generate Report
        report_generator = ReportGenerator()
        report_generator.generate_report(overall_metric, visualizations)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()