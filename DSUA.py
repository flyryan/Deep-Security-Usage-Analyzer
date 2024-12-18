#!/usr/bin/env python3
"""
Trend Micro Deep Security Usage Analyzer (DSUA)

This script analyzes Trend Micro Deep Security module usage across different environments
and generates comprehensive reports, including metrics, visualizations, and an HTML report.
"""
import sys
from modules.logging_config import setup_logging
from modules.analyzer import SecurityModuleAnalyzer

def main():
    """Main function with time range parameters."""
    try:
        # Set up logging
        logger = setup_logging()
        
        # Initialize analyzer with optional time range
        analyzer = SecurityModuleAnalyzer(
            start_date=None,  # Optional: specify start date in 'YYYY-MM-DD' format
            end_date=None     # Optional: specify end date in 'YYYY-MM-DD' format
        )
        
        # Run analysis
        analyzer.analyze()
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
