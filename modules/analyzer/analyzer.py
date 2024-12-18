"""
Core analyzer functionality for the Deep Security Usage Analyzer.
"""
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional

from .data_loader import load_and_preprocess_data
from .metrics_calculator import calculate_all_metrics
from ..utils import convert_to_serializable
from ..visualizations import create_visualizations
from ..report_generator import generate_reports

logger = logging.getLogger(__name__)

class SecurityModuleAnalyzer:
    """
    Trend Micro Deep Security Usage Analyzer.

    Analyzes Trend Micro Deep Security module usage across different environments and generates comprehensive reports.
    """
    
    def __init__(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Initialize the Trend Micro Deep Security Usage Analyzer.
        Sets up directories for input and output, and prepares data structures for analysis.

        Args:
            start_date (Optional[str]): Start date for analysis in YYYY-MM-DD format
            end_date (Optional[str]): End date for analysis in YYYY-MM-DD format
        """
        # Use current directory as default
        self.directory = Path.cwd()
        self.output_dir = self.directory / 'output'
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data and metrics attributes
        self.data = None
        self.metrics = None
        
        # Add time range parameters
        self.start_date = pd.to_datetime(start_date) if start_date else None
        self.end_date = pd.to_datetime(end_date) if end_date else None

    def analyze(self) -> None:
        """
        Perform the complete analysis workflow.

        This includes loading data, calculating metrics, creating visualizations, and generating the report.
        """
        try:
            total_steps = 5
            current_step = 0

            def update_progress(step_name: str):
                nonlocal current_step
                current_step += 1
                print(f"\n[{current_step}/{total_steps}] {step_name}")
                logger.info(f" Starting: {step_name}")

            # Step 1: Load and preprocess data
            update_progress("Loading and preprocessing data...")
            self.data = load_and_preprocess_data(self.directory, self.start_date, self.end_date)

            # Step 2: Calculate metrics
            update_progress("Calculating metrics...")
            self.metrics = calculate_all_metrics(self.data)

            # Step 3: Create visualizations
            update_progress("Generating visualizations...")
            visualizations = create_visualizations(self.metrics, self.output_dir)

            # Step 4: Generate report
            update_progress("Generating final report...")
            generate_reports(self.metrics, self.output_dir, visualizations)

            # Step 5: Save metrics to JSON
            update_progress("Saving metrics...")
            serializable_metrics = convert_to_serializable(self.metrics)
            with open(self.output_dir / 'metrics.json', 'w') as json_file:
                json.dump(serializable_metrics, json_file, indent=4)
                logger.info(f"✓ Saved metrics to '{self.output_dir / 'metrics.json'}'")

            # Print final summary
            print("\nAnalysis Complete!")
            print(f"✓ Processed {len(self.data):,} records from {len(self.data['Hostname'].unique()):,} unique hosts")
            print(f"✓ Report and visualizations saved to: {self.output_dir}")

            if 'Unknown' in self.metrics['by_environment']:
                unknown_count = self.metrics['by_environment']['Unknown']['total_instances']
                print(f"⚠️  {unknown_count:,} hosts in unknown environment")

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
            raise
