"""
Report generation functionality for the Deep Security Usage Analyzer.
"""
from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
from .reporting import generate_report

def generate_reports(metrics: Dict, output_dir: Path, visualizations: Dict[str, plt.Figure]) -> None:
    """
    Generate comprehensive HTML and PDF reports of the analysis.
    This is a wrapper around the reporting package's generate_report function.

    Args:
        metrics (Dict): Dictionary containing all metrics data
        output_dir (Path): Directory to save the reports
        visualizations (Dict[str, plt.Figure]): Dictionary of visualization figures
    """
    generate_report(metrics, output_dir, visualizations)
