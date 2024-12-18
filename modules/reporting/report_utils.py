"""
Utility functions for report generation in Deep Security Usage Analyzer.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def format_number(value: Any, decimal_places: Optional[int] = None) -> str:
    """
    Format a number with thousand separators and optional decimal places.

    Args:
        value: The number to format
        decimal_places: Number of decimal places (if None, no decimal formatting)

    Returns:
        str: Formatted number string
    """
    try:
        if decimal_places is not None:
            return f"{float(value):,.{decimal_places}f}"
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)

def ensure_output_directory(output_dir: Path) -> None:
    """
    Ensure the output directory exists, create if it doesn't.

    Args:
        output_dir: Path to the output directory
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create output directory: {str(e)}")
        raise

def validate_metrics(metrics: Dict) -> bool:
    """
    Validate the metrics dictionary has all required keys and data.

    Args:
        metrics: Dictionary containing metrics data

    Returns:
        bool: True if metrics are valid, False otherwise
    """
    required_keys = ['overall', 'by_environment', 'monthly']
    
    try:
        # Check for required top-level keys
        if not all(key in metrics for key in required_keys):
            logger.error("Missing required keys in metrics dictionary")
            return False
            
        # Validate overall metrics
        if not all(key in metrics['overall'] for key in ['total_instances', 'activated_instances', 'inactive_instances']):
            logger.error("Missing required overall metrics")
            return False
            
        # Validate monthly data
        if not isinstance(metrics['monthly'].get('data', []), list):
            logger.error("Monthly data must be a list")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating metrics: {str(e)}")
        return False
