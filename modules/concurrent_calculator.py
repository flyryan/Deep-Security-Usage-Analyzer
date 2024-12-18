"""
Concurrent usage calculation functionality for the Deep Security Usage Analyzer.
"""
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def calculate_concurrent_usage(df: pd.DataFrame, start_date: Optional[pd.Timestamp] = None, 
                            end_date: Optional[pd.Timestamp] = None) -> int:
    """
    Calculate the maximum concurrent usage from a DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame containing start_datetime and stop_datetime columns
        start_date (Optional[pd.Timestamp]): Start date for calculation
        end_date (Optional[pd.Timestamp]): End date for calculation

    Returns:
        int: Maximum concurrent usage
    """
    max_concurrent = 0
    try:
        timeline = []
        for _, row in df.iterrows():
            start = row['start_datetime']
            stop = row['stop_datetime']
            
            # Clip to period boundaries if specified
            if start_date is not None:
                start = max(start, start_date)
            if end_date is not None:
                stop = min(stop, end_date)
            
            if pd.notna(start) and pd.notna(stop) and start <= stop:
                timeline.append((start, 1))
                timeline.append((stop, -1))
        
        if timeline:
            timeline.sort(key=lambda x: x[0])
            current_count = 0
            for _, count_change in timeline:
                current_count += count_change
                max_concurrent = max(max_concurrent, current_count)
    
    except Exception as e:
        logger.error(f"Error calculating concurrent usage: {str(e)}")
        logger.debug("Error details:", exc_info=True)
    
    return max_concurrent
