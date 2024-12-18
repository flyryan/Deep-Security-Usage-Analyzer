"""
Utility functions and constants for the Deep Security Usage Analyzer.
"""
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
import warnings
import re

# Valid file extensions for input data
VALID_EXTENSIONS = {'.csv', '.xlsx', '.xls'}

# Module columns that should always be included
MODULE_COLUMNS = ['AM', 'WRS', 'DC', 'AC', 'IM', 'LI', 'FW', 'DPI', 'SAP']

# Enhanced environment patterns with more specific matching
ENVIRONMENT_PATTERNS = {
    'Production': [
        'prod', '-prod', 'prd', 'production',
        r'\bprd\d+\b', r'\bp\d+\b', 'live',
        'prod-', '-prd-', 'production-'
    ],
    'Development': [
        'dev', 'development', r'\bdev\d+\b',
        'develop-', '-dev-', 'development-'
    ],
    'Test': [
        'test', 'tst', 'qa', r'\btst\d+\b',
        'testing-', '-test-', 'qa-', '-qa-'
    ],
    'Staging': [
        'stage', 'staging', 'stg', r'\bstg\d+\b',
        'stage-', '-stg-', 'staging-'
    ],
    'DR': [
        'dr', 'disaster', 'recovery', 'dr-site',
        'disaster-recovery', 'backup-site'
    ],
    'UAT': [
        'uat', 'acceptance', r'\buat\d+\b',
        'uat-', '-uat-', 'user-acceptance'
    ],
    'Integration': [
        'int', 'integration', r'\bint\d+\b',
        'integration-', '-int-'
    ]
}

# Domain patterns for environment classification
DOMAIN_PATTERNS = {
    'Internal': [
        r'10\.\d+\.\d+\.\d+',
        r'192\.168\.\d+\.\d+',
        r'172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+',
        r'\.internal\.',
        r'\.local\.',
        r'\.intranet\.'
    ],
    'DMZ': [
        r'dmz',
        r'perimeter',
        r'\.dmz\.',
        r'border'
    ]
}

def classify_environment(hostname: str, source_env: Optional[str] = None) -> str:
    """
    Classify the environment of a given hostname based on predefined patterns.

    Args:
        hostname (str): The hostname to classify.
        source_env (Optional[str]): The environment inferred from the filename.

    Returns:
        str: The classified environment name.
    """
    if source_env:
        return source_env

    if pd.isna(hostname):
        return 'Unknown'
        
    hostname = str(hostname).lower()
    
    # Suppress the specific warning about regex pattern groups
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning, 
                              message='This pattern is interpreted as a regular expression, and has match groups.*')
        
        # Check specific environment patterns
        for env, patterns in ENVIRONMENT_PATTERNS.items():
            if any(pattern in hostname or pd.Series(hostname).str.contains(pattern, regex=True).iloc[0] 
                   for pattern in patterns):
                return env
        
        # Check domain patterns
        for domain, patterns in DOMAIN_PATTERNS.items():
            if any(pd.Series(hostname).str.contains(pattern, regex=True).iloc[0] 
                   for pattern in patterns):
                return domain
    
    # Additional classification based on naming conventions
    if any(x in hostname for x in ['app', 'api', 'web', 'srv']):
        if 'prod' in hostname or 'prd' in hostname:
            return 'Production'
        elif 'dev' in hostname:
            return 'Development'
    
    # Try to extract environment from hostname structure
    parts = hostname.split('.')
    if len(parts) > 1:
        for part in parts:
            if any(env.lower() in part for env in ENVIRONMENT_PATTERNS.keys()):
                return next(env for env in ENVIRONMENT_PATTERNS.keys() 
                          if env.lower() in part)
    
    # Check for numbered environments
    if any(pattern in hostname for pattern in ['env1', 'env2', 'e1', 'e2']):
        return 'Environment-Specific'
    
    return 'Unknown'

def convert_to_serializable(obj: Union[Dict, List, np.integer, np.floating, np.bool_, pd.Timestamp]) -> Union[Dict, List, int, float, bool, str]:
    """
    Recursively convert NumPy data types to native Python types.
    
    Args:
        obj: The object to convert.
        
    Returns:
        The converted object with native Python types.
    """
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    else:
        return obj

def filter_time_range(df: pd.DataFrame, start_date: Optional[pd.Timestamp] = None, end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """
    Filter and adjust data based on specified time range.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        start_date (Optional[pd.Timestamp]): Start date for filtering
        end_date (Optional[pd.Timestamp]): End date for filtering
            
    Returns:
        pd.DataFrame: Filtered and adjusted DataFrame
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    filtered_df = df.copy()
    
    if start_date:
        # Remove records that end before start_date
        filtered_df = filtered_df[filtered_df['stop_datetime'] >= start_date]
        # Adjust start times that are before start_date
        filtered_df.loc[filtered_df['start_datetime'] < start_date, 'start_datetime'] = start_date
        
    if end_date:
        # Set end_date to 23:59:59 of the last day
        end_date_with_time = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        # Remove records that start after end_date
        filtered_df = filtered_df[filtered_df['start_datetime'] <= end_date_with_time]
        # Adjust stop times that are after end_date
        filtered_df.loc[filtered_df['stop_datetime'] > end_date_with_time, 'stop_datetime'] = end_date_with_time
    
    # Recalculate duration if needed
    if 'Duration (Seconds)' in filtered_df.columns:
        filtered_df['Duration (Seconds)'] = (
        filtered_df['stop_datetime'] - filtered_df['start_datetime']
        ).dt.total_seconds()
    
    return filtered_df
