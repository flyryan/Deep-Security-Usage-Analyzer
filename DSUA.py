"""
Trend Micro Deep Security Usage Analyzer (DSUA)

This script analyzes Trend Micro Deep Security module usage across different environments
and generates comprehensive reports, including metrics, visualizations, and an HTML report.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import sys
import logging
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from jinja2 import Template
import base64
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re  # Add this import at the top of the file if not already present
from tqdm import tqdm  # Add this import at the top of the file if not already present

# Custom logging formatter with colors and symbols
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and symbols"""
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(symbol)s %(message)s"

    FORMATS = {
        logging.DEBUG: (grey, "🔍"),
        logging.INFO: (grey, "ℹ️"),
        logging.WARNING: (yellow, "⚠️"),
        logging.ERROR: (red, "❌"),
        logging.CRITICAL: (bold_red, "🚨")
    }

    def format(self, record):
        color, symbol = self.FORMATS.get(record.levelno, (self.reset, "•"))
        record.symbol = f"{symbol}"
        record.msg = f"{color}{record.msg}{self.reset}"
        return logging.Formatter(self.format_str).format(record)

# Create console handler with custom formatter
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter())
console_handler.setLevel(logging.INFO)  # Only show INFO and above in console

# Create file handler with detailed formatting
file_handler = logging.FileHandler('security_analysis.log')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
file_handler.setLevel(logging.DEBUG)  # Log everything to file

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

class SecurityModuleAnalyzer:
    """
    Trend Micro Deep Security Usage Analyzer.

    Analyzes Trend Micro Deep Security module usage across different environments and generates comprehensive reports.
    """
    
    # Class-level constants
    VALID_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
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
    
    # Add this as a class constant at the top of your SecurityModuleAnalyzer class
    REPORT_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Deep Security Usage Analyzer Report</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                line-height: 1.6;
                color: #333;
            }
            .section { 
                margin-bottom: 30px; 
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1, h2 { 
                color: #2c3e50;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin: 20px 0; 
            }
            th, td { 
                border: 1px solid #ddd; 
                padding: 12px; 
                text-align: left; 
            }
            th { 
                background-color: #f5f5f5; 
                color: #2c3e50;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .metric-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                margin: 10px 0;
                transition: transform 0.2s;
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
            .metric-label {
                color: #666;
                font-size: 14px;
                margin-top: 5px;
            }
            .visualization { 
                margin: 20px 0;
                text-align: center;
            }
            .visualization img {
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .highlight { 
                background-color: #fff3cd; 
                padding: 15px;
                border-left: 4px solid #ffc107;
                margin: 20px 0;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .timestamp {
                color: #666;
                font-style: italic;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Deep Security Usage Analyzer Report</h1>
        <p class="timestamp">Generated on: {{ timestamp }}</p>
        
        <div class="section">
            <h2>Overall Metrics</h2>
            <div class="grid">
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall.total_instances | default(0) }}</div>
                    <div class="metric-label">Total Unique Instances</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall.activated_instances | default(0) }}</div>
                    <div class="metric-label">Activated Instances</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall.inactive_instances | default(0) }}</div>
                    <div class="metric-label">Inactive Instances</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall.total_hours | default(0.0) | round(1) }}</div>
                    <div class="metric-label">Total Hours</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Environment Distribution</h2>
            <table>
                <tr>
                    <th>Environment</th>
                    <th>Total Hosts</th>
                    <th>Activated Hosts</th>
                    <th>Most Used Module</th>
                    <th>Max Concurrent</th>
                    <th>Total Hours</th>
                </tr>
                {% for env, data in metrics.by_environment.items() %}
                <tr>
                    <td>{{ env }}</td>
                    <td>{{ data.total_instances }}</td>
                    <td>{{ data.activated_instances }}</td>
                    <td>{{ data.most_common_module }}</td>
                    <td>{{ data.max_concurrent if data.max_concurrent else 'None' }}</td>
                    <td>
                        {% if data.total_utilization_hours is defined and data.total_utilization_hours != 'N/A' %}
                            {{ "%.1f"|format(data.total_utilization_hours) }}
                        {% else %}
                            N/A
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="section">
            <h2>Module Usage Analysis</h2>
            <div class="visualization">
                <h3>Security Module Usage by Environment</h3>
                <img src="module_usage.png" alt="Module Usage Distribution">
            </div>
            <div class="visualization">
                <h3>Environment Distribution</h3>
                <img src="environment_distribution.png" alt="Environment Distribution">
            </div>
            <div class="visualization">
                <h3>Activated Instances Seen Monthly</h3>
                <img src="activated_instances_growth.png" alt="Growth of Activated Instances">
            </div>
        </div>
        
        <div class="section">
            <h2>Statistics Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Unique Instances</td>
                    <td>{{ "{:,}".format(metrics.overall.total_instances) }}</td>
                </tr>
                <tr>
                    <td>Instances Running at Least One Module</td>
                    <td>{{ "{:,}".format(metrics.overall.activated_instances) }}</td>
                </tr>
                <tr>
                    <td>Instances Not Running Any Modules</td>
                    <td>{{ "{:,}".format(metrics.overall.inactive_instances) }}</td>
                </tr>
                <tr>
                    <td>Total Hours</td>
                    <td>{{ "{:,.1f}".format(metrics.overall.total_hours) }}</td>
                </tr>
                <tr>
                    <td>Hours for Instances with Modules</td>
                    <td>{{ "{:,.1f}".format(metrics.overall.activated_hours) }}</td>
                </tr>
                <tr>
                    <td>Hours for Instances without Modules</td>
                    <td>{{ "{:,.1f}".format(metrics.overall.inactive_hours) }}</td>
                </tr>
                <tr>
                    <td>Max Concurrent Usage</td>
                    <td>{{ "{:,}".format(metrics.overall_metrics.max_concurrent_overall) }}</td>
                </tr>
                <tr>
                    <td>Average Monthly Growth (Activated Instances)</td>
                    <td>{{ "%.1f"|format(metrics.monthly.average_monthly_growth) }} instances</td>
                </tr>
                <tr>
                    <td>Unknown Environment Instances</td>
                    <td>{{ "{:,}".format(metrics.by_environment.Unknown.total_instances if metrics.by_environment.Unknown else 0) }}</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Monthly Data Analysis</h2>
            <div class="grid">
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.monthly.total_months }}</div>
                    <div class="metric-label">Total Months with Data</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.monthly.date_range }}</div>
                    <div class="metric-label">Date Range</div>
                </div>
            </div>
            
            <table>
                <tr>
                    <th>Month</th>
                    <th>Activated Instances</th>
                    <th>Max Concurrent Instances</th>
                    <th>Avg Modules/Host</th>
                </tr>
                {% if metrics.monthly and metrics.monthly.data %}
                    {% for month in metrics.monthly.data %}
                    <tr>
                        <td>{{ month.month | default('None') }}</td>
                        <td>
                            {{ month.activated_instances | default(0) }}
                        </td>
                        <td>{{ month.max_concurrent | default(0) }}</td>
                        <td>{{ "%.2f"|format(month.avg_modules_per_host | default(0.0)) }}</td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="5">No monthly data available</td>
                    </tr>
                {% endif %}
            </table>
        </div>

        {% if metrics.by_environment.Unknown and metrics.by_environment.Unknown.total_instances > 0 %}
        <div class="section highlight">
            <h2>Unknown Environment Analysis</h2>
            <p>Number of hosts in unknown environment: {{ "{:,}".format(metrics.by_environment.Unknown.total_instances) }}</p>
            <p>Common patterns found in unknown hosts:</p>
            <ul>
            {% for pattern in unknown_patterns %}
                <li>{{ pattern }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}

    </body>
    </html>
    """
    
    def __init__(self):
        """
        Initialize the Trend Micro Deep Security Usage Analyzer.
        Sets up directories for input and output, and prepares data structures for analysis.
        """
        # Use current directory as default
        self.directory = Path.cwd()
        self.output_dir = self.directory / 'output'
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data and metrics attributes
        self.data = None
        self.metrics = None
        
        # Define module columns - these should always be included
        self.MODULE_COLUMNS = ['AM', 'WRS', 'DC', 'AC', 'IM', 'LI', 'FW', 'DPI', 'SAP']
        
        # Check for input files
        input_files = [f for f in self.directory.glob('*') if f.suffix in self.VALID_EXTENSIONS]
        if not input_files:
            raise ValueError(f"No valid input files found in {self.directory}")
        
        # Load first file to check available columns
        test_file = input_files[0]
        try:
            if test_file.suffix == '.csv':
                test_df = pd.read_csv(test_file)
            else:
                test_df = pd.read_excel(test_file)
            
            # Add missing module columns with zeros
            for col in self.MODULE_COLUMNS:
                if col not in test_df.columns:
                    test_df[col] = 0
                    logger.debug(f"Added missing module column: {col}")
            
            logger.info(f" Initialized with modules: {', '.join(self.MODULE_COLUMNS)}")
            logger.info(f" Output will be saved to: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error initializing analyzer: {str(e)}")
            raise
        
        tqdm.pandas()  # Initialize tqdm for pandas

    def classify_environment(self, hostname: str, source_env: Optional[str] = None) -> str:
        """
        Classify the environment of a given hostname based on predefined patterns.

        Parameters:
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
            for env, patterns in self.ENVIRONMENT_PATTERNS.items():
                if any(pattern in hostname or pd.Series(hostname).str.contains(pattern, regex=True).iloc[0] 
                       for pattern in patterns):
                    return env
            
            # Check domain patterns
            for domain, patterns in self.DOMAIN_PATTERNS.items():
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
                if any(env.lower() in part for env in self.ENVIRONMENT_PATTERNS.keys()):
                    return next(env for env in self.ENVIRONMENT_PATTERNS.keys() 
                              if env.lower() in part)
        
        # Check for numbered environments
        if any(pattern in hostname for pattern in ['env1', 'env2', 'e1', 'e2']):
            return 'Environment-Specific'
        
        return 'Unknown'

    def load_and_preprocess_data(self) -> pd.DataFrame:
        """
        Load data from files in the specified directory and preprocess it for analysis.

        Returns:
            pd.DataFrame: The combined and cleaned data.
        """
        files = [f for f in self.directory.glob('*') if f.suffix in self.VALID_EXTENSIONS]
        if not files:
            raise ValueError(f"No valid files found in {self.directory}")
        
        print(f"\nFound {len(files)} files to process")
        dfs = []
        
        # Suppress date parsing warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            for i, file in enumerate(files, 1):
                try:
                    print(f"\rProcessing file {i}/{len(files)}: {file.name}" + " " * 50, end='')
                    
                    if file.suffix == '.csv':
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)
                    
                    # Standardize column names and handle dates
                    df.columns = df.columns.str.strip()
                    
                    # Add missing module columns with zeros and handle NaN values
                    for col in self.MODULE_COLUMNS:
                        if col not in df.columns:
                            df[col] = 0
                            logger.debug(f"Added missing module column {col} to {file.name}")
                        else:
                            # Fill NaN values with 0 and convert to int
                            df[col] = df[col].fillna(0).astype(int)
                    
                    # Handle date columns
                    if 'Start Date' in df.columns and 'Start Time' in df.columns:
                        try:
                            df['start_datetime'] = pd.to_datetime(
                                df['Start Date'].astype(str) + ' ' + 
                                df['Start Time'].astype(str),
                                format='mixed',
                                errors='coerce'
                            )
                            df['stop_datetime'] = pd.to_datetime(
                                df['Stop Date'].astype(str) + ' ' + 
                                df['Stop Time'].astype(str),
                                format='mixed',
                                errors='coerce'
                            )
                        except Exception as e:
                            logger.error(f"Error converting date/time columns in {file.name}: {str(e)}")
                            continue
                    elif 'Start' in df.columns:
                        try:
                            df['start_datetime'] = pd.to_datetime(df['Start'], errors='coerce')
                            if 'Stop' in df.columns:
                                df['stop_datetime'] = pd.to_datetime(df['Stop'], errors='coerce')
                        except Exception as e:
                            logger.error(f"Error converting Start/Stop columns in {file.name}: {str(e)}")
                            continue
                    else:
                        logger.error(f"No valid datetime columns found in {file.name}")
                        continue
                    
                    # Remove rows with invalid dates
                    invalid_dates = df['start_datetime'].isna() | df['stop_datetime'].isna()
                    if invalid_dates.any():
                        logger.debug(f"Removing {invalid_dates.sum()} rows with invalid dates from {file.name}")
                        df = df[~invalid_dates]
                    
                    # Extract environment from filename
                    env = None
                    filename = file.name.lower()
                    if re.search(r'(dev|development)', filename):
                        env = 'Development'
                    elif re.search(r'(prod|production)', filename):
                        env = 'Production'
                    elif re.search(r'(test|qa|tst)', filename):
                        env = 'Test'
                    elif re.search(r'(int|integration)', filename):
                        env = 'Integration'
                    elif re.search(r'(stage|staging)', filename):
                        env = 'Staging'
                    elif re.search(r'(uat|acceptance)', filename):
                        env = 'UAT'
                    elif re.search(r'(dr|disaster|recovery)', filename):
                        env = 'DR'

                    # Debug logging to confirm environment extraction
                    logger.debug(f"File '{file.name}' assigned to environment '{env}'")
                    
                    # Add 'Source_Environment' column
                    df['Source_Environment'] = env
                    
                    # Verify module columns contain valid values (0 or 1)
                    for col in self.MODULE_COLUMNS:
                        invalid_values = df[col][(df[col] != 0) & (df[col] != 1)].unique()
                        if len(invalid_values) > 0:
                            logger.debug(f"Converting invalid values in {col} column of {file.name}")
                            df[col] = df[col].map(lambda x: 1 if x == 1 else 0)
                    
                    if len(df) > 0:
                        dfs.append(df)
                    else:
                        logger.warning(f"No valid data remained in {file.name} after preprocessing")
                    
                except Exception as e:
                    print(f"\n⚠️  Error processing {file.name}: {str(e)}")
                    logger.error(f"Error processing {file.name}: {str(e)}")
                    logger.debug("Error details:", exc_info=True)
        
        print("\nCombining, classifying, and cleaning data...")
        
        if not dfs:
            raise ValueError("No valid data loaded from any files")
        
        # Combine all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Add progress meter for environment classification
        combined_df['Environment'] = combined_df.progress_apply(
            lambda row: self.classify_environment(row['Hostname'], row['Source_Environment']),
            axis=1
        )
        
        # Remove duplicates
        original_len = len(combined_df)
        combined_df = combined_df.drop_duplicates()
        if original_len > len(combined_df):
            removed = original_len - len(combined_df)
            print(f"✓ Removed {removed:,} duplicate rows ({(removed/original_len)*100:.1f}%)")
        
        # Verify data quality
        null_hostnames = combined_df['Hostname'].isnull().sum()
        if null_hostnames > 0:
            logger.warning(f"Found {null_hostnames} rows with null hostnames")
        
        # Final verification of module values
        for col in self.MODULE_COLUMNS:
            invalid = combined_df[col][(combined_df[col] != 0) & (combined_df[col] != 1)].count()
            if invalid > 0:
                logger.debug(f"Final cleanup: Converting {invalid} invalid values in {col}")
                combined_df[col] = combined_df[col].map(lambda x: 1 if x == 1 else 0)
        
        # Ensure stop_datetime is after start_datetime
        invalid_duration = combined_df['stop_datetime'] < combined_df['start_datetime']
        if invalid_duration.any():
            logger.warning(f"Removing {invalid_duration.sum()} rows where stop_datetime is before start_datetime")
            combined_df = combined_df[~invalid_duration]
        
        print(f"✓ Final dataset: {len(combined_df):,} records from {len(combined_df['Hostname'].unique()):,} unique hosts")
        
        # Log summary statistics
        logger.info(f"Total records: {len(combined_df):,}")
        logger.info(f"Unique hosts: {len(combined_df['Hostname'].unique()):,}")
        logger.info(f"Date range: {combined_df['start_datetime'].min()} to {combined_df['start_datetime'].max()}")
        logger.info(f"Environments found: {', '.join(sorted(combined_df['Environment'].unique()))}")
        
        return combined_df
    
    def _calculate_concurrent_usage(self, df: pd.DataFrame, start_date=None, end_date=None) -> int:
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

    def calculate_monthly_metrics(self) -> Dict:
        """Calculate monthly metrics including cumulative growth."""
        monthly_metrics = {
            'data': [],
            'data_gaps': [],
            'total_months': 0,
            'date_range': '',
            'average_monthly_growth': 0  # New field for average growth
        }
        
        try:
            # Get all activated instances (these are instances that have any modules at any time)
            activated_mask = self.data[self.MODULE_COLUMNS].sum(axis=1) > 0
            activated_instances = set(self.data[activated_mask]['Hostname'].unique())
            
            # Get date range
            min_date = self.data['start_datetime'].min()
            max_date = self.data['start_datetime'].max()
            monthly_metrics['date_range'] = f"{min_date.strftime('%Y-%m')} to {max_date.strftime('%Y-%m')}"
            
            # Generate all months
            all_months = pd.date_range(
                start=min_date.replace(day=1),
                end=max_date.replace(day=1),
                freq='MS'
            )
            
            monthly_data = []
            cumulative_instances = set()  # Track cumulative instances
            previous_month_count = 0  # For calculating monthly growth
            total_growth = 0  # For calculating average growth
            growth_months = 0  # Count months with growth
            
            for month_start in all_months:
                month_end = month_start + pd.offsets.MonthEnd(1)
                
                # Get all records for this month
                month_mask = (
                    (self.data['start_datetime'] <= month_end) & 
                    (self.data['stop_datetime'] >= month_start)
                )
                month_data = self.data[month_mask].copy()
                
                if not month_data.empty:
                    # Get activated instances for this month
                    activated_month_data = month_data[month_data[self.MODULE_COLUMNS].sum(axis=1) > 0]['Hostname']
                    activated_month_data = month_data[month_data['has_modules']]
                    activated_instances_current = set(activated_month_data['Hostname'].unique())

                    # Calculate duration per instance without double counting
                    duration_per_instance = activated_month_data.groupby('Hostname')['Duration (Seconds)'].sum()
                    total_hours = duration_per_instance.sum() / 3600

                    # Calculate average modules per host
                    if not activated_month_data.empty:
                        avg_modules_per_host = activated_month_data[self.MODULE_COLUMNS].sum(axis=1).mean()
                    else:
                        avg_modules_per_host = 0.0

                    # Max concurrent instances in the month
                    max_concurrent = self._calculate_concurrent_usage(activated_month_data)

                    # Calculate new and lost instances
                    new_instances = activated_instances_current - cumulative_instances
                    lost_instances = cumulative_instances - activated_instances_current

                    # Update cumulative instances
                    cumulative_instances.update(activated_instances_current)

                    # Calculate monthly growth
                    current_month_count = len(activated_instances_current)
                    growth = current_month_count - previous_month_count
                    if growth > 0:
                        total_growth += growth
                        growth_months += 1
                    previous_month_count = current_month_count

                    # Append metrics for the month
                    monthly_data.append({
                        'month': month_start.strftime('%Y-%m'),
                        'activated_instances': current_month_count,
                        'new_instances': len(new_instances),
                        'lost_instances': len(lost_instances),
                        'max_concurrent': max_concurrent,
                        'avg_modules_per_host': avg_modules_per_host,
                        'total_hours': total_hours,
                    })
            # Calculate average monthly growth
            if growth_months > 0:
                monthly_metrics['average_monthly_growth'] = total_growth / growth_months
            
            monthly_metrics['data'] = sorted(monthly_data, key=lambda x: x['month'])
            monthly_metrics['total_months'] = len(monthly_data)
            
            return monthly_metrics
            
        except Exception as e:
            logger.error(f"Error calculating monthly metrics: {str(e)}")
            return monthly_metrics

    def _calculate_max_concurrent(self, df: pd.DataFrame, show_progress: bool = False) -> int:
        max_concurrent = 0
        try:
            if 'start_datetime' in df.columns and 'stop_datetime' in df.columns:
                # Create timeline events for both start and stop times
                timeline = []
                for _, row in df.iterrows():
                    if pd.notna(row['start_datetime']) and pd.notna(row['stop_datetime']):
                        timeline.append((row['start_datetime'], 1))  # Start event
                        timeline.append((row['stop_datetime'], -1))  # Stop event
                
                if timeline:
                    timeline.sort(key=lambda x: x[0])
                    current_count = 0
                    for _, count_change in timeline:
                        current_count += count_change
                        max_concurrent = max(max_concurrent, current_count)
        
        except Exception as e:
            logger.warning(f"Error calculating max concurrent: {str(e)}")
        
        return max_concurrent

    def calculate_metrics(self) -> Dict:
        if self.data is None:
            raise ValueError("No data loaded for analysis")
        
        logger.info("Calculating comprehensive metrics...")
        
        # Add has_modules column to the dataframe
        self.data['has_modules'] = self.data[self.MODULE_COLUMNS].sum(axis=1) > 0
        
        # Calculate activated instances ONCE and store the result
        activated_hosts = set(self.data[self.data['has_modules']]['Hostname'].unique())
        total_hosts = set(self.data['Hostname'].unique())
        
        # Initialize metrics dictionary
        metrics = {
            'by_environment': {},
            'overall': {},
            'trends': {},
            'overall_metrics': {}
        }
        
        # Calculate overall metrics first
        metrics['overall'] = {
            'total_instances': len(total_hosts),
            'activated_instances': len(activated_hosts),
            'inactive_instances': len(total_hosts - activated_hosts),
            'total_hours': self.data['Duration (Seconds)'].sum() / 3600 if 'Duration (Seconds)' in self.data.columns else 0,
            'activated_hours': self.data[self.data['has_modules']]['Duration (Seconds)'].sum() / 3600 if 'Duration (Seconds)' in self.data.columns else 0,
        }
        metrics['overall']['inactive_hours'] = metrics['overall']['total_hours'] - metrics['overall']['activated_hours']
        
        # Calculate correlation matrix
        correlation_matrix = self.data[self.MODULE_COLUMNS].corr()
        metrics['overall']['correlation_matrix'] = correlation_matrix.to_dict()
        
        # Calculate module usage
        metrics['overall']['module_usage'] = {
            col: int(self.data[col].sum()) for col in self.MODULE_COLUMNS
        }
        
        # Calculate environment distribution
        environments = sorted(self.data['Environment'].unique())
        env_distribution = {}
        
        logger.info("Calculating environment-specific metrics...")
        for env in environments:
            env_data = self.data[self.data['Environment'] == env]
            env_activated_hosts = set(env_data[env_data['has_modules']]['Hostname'].unique())
            env_total_hosts = set(env_data['Hostname'].unique())
            
            # Calculate module usage for this environment
            module_usage_counts = {
                col: set(env_data[env_data[col] > 0]['Hostname']) for col in self.MODULE_COLUMNS
            }
            
            # Calculate module usage percentage
            module_usage_percentage = {}
            for module, instances in module_usage_counts.items():
                unique_instance_count = len(instances)
                percentage = (unique_instance_count / len(env_total_hosts)) * 100 if env_total_hosts else 0
                module_usage_percentage[module] = percentage
            
            # Calculate max concurrent instances for environment
            max_concurrent = self._calculate_concurrent_usage(env_data)
            
            # Calculate total utilization hours
            total_hours = (env_data['Duration (Seconds)'].sum() / 3600) if 'Duration (Seconds)' in env_data.columns else 0
            
            metrics['by_environment'][env] = {
                'total_instances': len(env_total_hosts),
                'activated_instances': len(env_activated_hosts),
                'inactive_instances': len(env_total_hosts - env_activated_hosts),
                'module_usage': {col: len(module_usage_counts[col]) for col in self.MODULE_COLUMNS},
                'module_usage_percentage': module_usage_percentage,
                'most_common_module': max(
                    self.MODULE_COLUMNS,
                    key=lambda col: len(module_usage_counts[col])
                ) if sum(len(instances) for instances in module_usage_counts.values()) > 0 else "None",
                'avg_modules_per_host': env_data[self.MODULE_COLUMNS].sum(axis=1).mean(),
                'max_concurrent': max_concurrent,
                'total_utilization_hours': total_hours,
                'correlation_matrix': env_data[self.MODULE_COLUMNS].corr().to_dict()
            }
            
            env_distribution[env] = len(env_total_hosts)
        
        metrics['overall']['environment_distribution'] = env_distribution
        
        # Calculate overall max concurrent by checking each month
        logger.info("Calculating overall max concurrent usage...")
        overall_max_concurrent = self._calculate_concurrent_usage(self.data)
        
        metrics['overall_metrics'] = {
            'max_concurrent_overall': overall_max_concurrent,
            'total_unique_instances': len(total_hosts),
            'total_activated_instances': len(activated_hosts),
            'total_inactive_instances': len(total_hosts - activated_hosts)
        }
        
        # Validate metrics
        try:
            assert metrics['overall']['total_instances'] == metrics['overall']['activated_instances'] + metrics['overall']['inactive_instances'], \
                "Total instances does not equal sum of activated and inactive instances"
            
            assert metrics['overall']['total_hours'] >= metrics['overall']['activated_hours'], \
                "Total hours should be greater than or equal to activated hours"
            
            for key, value in metrics['overall'].items():
                if isinstance(value, (int, float)):
                    assert value >= 0, f"Negative value found in {key}: {value}"
            
            logger.info("Metrics validation passed")
            
        except AssertionError as e:
            logger.warning(f"Metrics validation failed: {str(e)}")
        
        return metrics
  
    def calculate_overall_max_concurrent(self, df: pd.DataFrame, progress_bar=None) -> int:
        """Calculate the true overall max concurrent instances."""
        max_concurrent = 0
        try:
            if 'stop_datetime' in df.columns:
                unique_hostnames = df['Hostname'].unique()
                timeline = []
                
                # Iterate over hostnames directly, don't use progress_bar as iterator
                for hostname in unique_hostnames:
                    host_data = df[df['Hostname'] == hostname]
                    start = host_data['start_datetime'].min()
                    stop = host_data['stop_datetime'].max()
                    
                    if pd.notna(start) and pd.notna(stop):
                        timeline.append((start, 1))
                        timeline.append((stop, -1))
                    
                    if progress_bar is not None:
                        progress_bar.update(1)
                
                if timeline:
                    if progress_bar is not None:
                        progress_bar.set_description("      Calculating concurrent usage")
                    timeline.sort(key=lambda x: x[0])
                    current_count = 0
                    for _, count_change in timeline:
                        current_count += count_change
                        max_concurrent = max(max_concurrent, current_count)
        
        except Exception as e:
            logger.warning(f"Error calculating max concurrent: {str(e)}")
        
        return max_concurrent

    def calculate_enhanced_metrics(self) -> Dict:
        """Calculate comprehensive metrics including utilization and realm statistics."""
        if self.data is None:
            raise ValueError("No data loaded for analysis")
        
        print("\nCalculating enhanced metrics...")
        
        # Convert datetime columns with proper error handling
        try:
            print("  ↳ Processing datetime columns...")
            if 'Start Date' in self.data.columns and 'Start Time' in self.data.columns:
                # Convert date and time separately then combine
                self.data['start_datetime'] = pd.to_datetime(
                    self.data['Start Date'].astype(str) + ' ' + 
                    self.data['Start Time'].astype(str),
                    format='mixed',
                    errors='coerce'
                )
                self.data['stop_datetime'] = pd.to_datetime(
                    self.data['Stop Date'].astype(str) + ' ' + 
                    self.data['Stop Time'].astype(str),
                    format='mixed',
                    errors='coerce'
                )
            elif 'Start' in self.data.columns:
                self.data['start_datetime'] = pd.to_datetime(self.data['Start'], errors='coerce')
                if 'Stop' in self.data.columns:
                    self.data['stop_datetime'] = pd.to_datetime(self.data['Stop'], errors='coerce')
        except Exception as e:
            logger.warning(f"Error processing datetime columns: {str(e)}")
            self.data['start_datetime'] = pd.NaT
            self.data['stop_datetime'] = pd.NaT
        
        enhanced_metrics = {
            'realm_metrics': {},
            'overall_metrics': {},
            'utilization_metrics': {}
        }
        
        # Get all computer groups (realms)
        realms = self.data['Computer Group'].fillna('Unknown').unique()
        total_realms = len(realms)
        print(f"  ↳ Processing {total_realms} realms...")
        
        # Main progress bar for realms
        with tqdm(total=total_realms, desc="    Processing realms", ncols=100, position=0, leave=True) as pbar:
            for realm in realms:
                # Get data for this realm
                realm_data = self.data[self.data['Computer Group'].fillna('Unknown') == realm]
                
                # Update description with current realm
                display_realm = realm[:40] + "..." if len(realm) > 43 else realm
                pbar.set_description(f"    Processing {display_realm}")
                
                try:
                    # Calculate module usage
                    module_columns = ['AM', 'WRS', 'DC', 'AC', 'IM', 'LI', 'FW', 'DPI', 'SAP']
                    has_modules = realm_data[module_columns].sum(axis=1) > 0
                    
                    # Calculate unique instances
                    unique_instances = realm_data['Hostname'].nunique()
                    activated_instances = realm_data[has_modules]['Hostname'].nunique()
                    inactive_instances = unique_instances - activated_instances
                    
                    # Calculate maximum concurrent instances with nested progress bar for large datasets
                    max_concurrent = 0
                    if 'start_datetime' in realm_data.columns and not realm_data['start_datetime'].isna().all():
                        unique_hostnames = realm_data['Hostname'].unique()
                        
                        if len(unique_hostnames) > 1000:
                            with tqdm(total=len(unique_hostnames), desc="      Building timeline", 
                                    ncols=100, position=1, leave=False) as timeline_pbar:
                                timeline = []
                                for hostname in unique_hostnames:
                                    host_data = realm_data[realm_data['Hostname'] == hostname]
                                    start = host_data['start_datetime'].min()
                                    stop = host_data['stop_datetime'].max()
                                    
                                    if pd.notna(start) and pd.notna(stop):
                                        timeline.append((start, 1))
                                        timeline.append((stop, -1))
                                    timeline_pbar.update(1)
                                
                                if timeline:
                                    timeline.sort(key=lambda x: x[0])
                                    current_count = 0
                                    for _, count_change in timeline:
                                        current_count += count_change
                                        max_concurrent = max(max_concurrent, current_count)
                        else:
                            # Process without progress bar for smaller datasets
                            timeline = []
                            for hostname in unique_hostnames:
                                host_data = realm_data[realm_data['Hostname'] == hostname]
                                start = host_data['start_datetime'].min()
                                stop = host_data['stop_datetime'].max()
                                
                                if pd.notna(start) and pd.notna(stop):
                                    timeline.append((start, 1))
                                    timeline.append((stop, -1))
                            
                            if timeline:
                                timeline.sort(key=lambda x: x[0])
                                current_count = 0
                                for _, count_change in timeline:
                                    current_count += count_change
                                    max_concurrent = max(max_concurrent, current_count)
                    
                    # Update metrics
                    enhanced_metrics['realm_metrics'][realm] = {
                        'unique_instances': unique_instances,
                        'activated_instances': activated_instances,
                        'inactive_instances': inactive_instances,
                        'max_concurrent': max_concurrent,
                        'total_utilization_hours': (
                            realm_data[has_modules]['Duration (Seconds)'].sum() / 3600
                            if 'Duration (Seconds)' in realm_data.columns
                            else 0
                        )
                    }
                    
                except Exception as e:
                    logger.warning(f"Error processing realm {realm}: {str(e)}")
                    enhanced_metrics['realm_metrics'][realm] = {
                        'unique_instances': 0,
                        'activated_instances': 0,
                        'inactive_instances': 0,
                        'max_concurrent': 0,
                        'total_utilization_hours': 0
                    }
                
                pbar.update(1)

        print("  ↳ Calculating utilization metrics...")
        # Calculate utilization metrics
        total_utilization = 0
        try:
            # Calculate total unique instances first
            total_unique_instances = self.data['Hostname'].nunique()
            
            if 'Duration (Seconds)' in self.data.columns:
                # Group by hostname and take max duration to avoid double counting
                total_utilization = self.data.groupby('Hostname')['Duration (Seconds)'].max().sum() / 3600
            elif 'stop_datetime' in self.data.columns and not self.data['stop_datetime'].isna().all():
                # Calculate from datetime fields
                duration = (self.data['stop_datetime'] - self.data['start_datetime'])
                total_utilization = duration.dt.total_seconds().sum() / 3600
        except Exception as e:
            logger.warning(f"Error calculating total utilization: {str(e)}")
            total_utilization = 0
            total_unique_instances = 0

        enhanced_metrics['utilization_metrics'] = {
            'total_hours': total_utilization,
            'average_hours_per_instance': total_utilization / total_unique_instances if total_unique_instances > 0 else 0
        }
        
        print("  ↳ Calculating overall metrics...")
        try:
            # Create a progress bar for overall metrics calculation
            metrics_steps = ['Max Concurrent', 'Instance Counts', 'Module Status']
            with tqdm(total=len(metrics_steps), desc="    Processing metrics", ncols=100, position=0, leave=True) as metrics_pbar:
                # Calculate max concurrent overall with nested progress
                metrics_pbar.set_description("    Calculating max concurrent")
                unique_hostnames = self.data['Hostname'].unique()
                
                if len(unique_hostnames) > 1000:
                    with tqdm(total=len(unique_hostnames), desc="      Processing instances", 
                            ncols=100, position=1, leave=False) as instance_pbar:
                        overall_max_concurrent = self.calculate_overall_max_concurrent(
                            self.data, 
                            progress_bar=instance_pbar
                        )
                else:
                    overall_max_concurrent = self.calculate_overall_max_concurrent(self.data)
                metrics_pbar.update(1)

                # Calculate instance counts
                metrics_pbar.set_description("    Calculating instance counts")
                total_unique_instances = self.data['Hostname'].nunique()
                total_activated_instances = self.data[self.data['has_modules']]['Hostname'].nunique()
                total_inactive_instances = total_unique_instances - total_activated_instances
                metrics_pbar.update(1)

                # Calculate module status
                metrics_pbar.set_description("    Processing module status")
                enhanced_metrics['overall_metrics'] = {
                    'max_concurrent_overall': overall_max_concurrent,
                    'total_unique_instances': total_unique_instances,
                    'total_activated_instances': total_activated_instances,
                    'total_inactive_instances': total_inactive_instances
                }
                metrics_pbar.update(1)

        except Exception as e:
            logger.warning(f"Error calculating overall metrics: {str(e)}")
            enhanced_metrics['overall_metrics'] = {
                'max_concurrent_overall': 0,
                'total_unique_instances': 0,
                'total_activated_instances': 0,
                'total_inactive_instances': 0
            }

        print("  ↳ Enhanced metrics calculation complete")
        return enhanced_metrics

    def create_visualizations(self) -> Dict[str, plt.Figure]:
        """
        Create visualizations to represent module usage, environment distribution, and growth of activated instances.

        Returns:
            Dict[str, plt.Figure]: A dictionary of visualization figures.
        """
        visualizations = {}
        
        try:
            # Set Seaborn style
            sns.set_style('darkgrid')  # Use Seaborn's 'darkgrid' style
            
            # Define a color palette for consistency
            color_palette = sns.color_palette("Set2")
            
            # 1. Security Module Usage by Environment (Stacked Bar Chart)
            fig1, ax1 = plt.subplots(figsize=(12, 8))
            module_cols = self.MODULE_COLUMNS
            env_data = {}
            for env in ['Production', 'Development', 'Test', 'Staging', 'Integration', 'DR', 'UAT']:
                if env in self.metrics['by_environment']:
                    env_data[env] = self.metrics['by_environment'][env]['module_usage']
            module_usage_df = pd.DataFrame(env_data).fillna(0)
            module_usage_df = module_usage_df[module_usage_df.columns[::-1]]  # Reverse for better stacking
            module_usage_df.plot(kind='bar', stacked=True, ax=ax1, color=color_palette[:len(self.MODULE_COLUMNS)])
            ax1.set_title('Security Module Usage Across Environments', fontsize=16, pad=20)
            ax1.set_xlabel('Security Modules', fontsize=12)
            ax1.set_ylabel('Usage Count', fontsize=12)
            ax1.legend(title='Environment', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)
            plt.tight_layout()
            visualizations['module_usage'] = fig1

            # 2. Environment Distribution (Pie Chart)
            fig2, ax2 = plt.subplots(figsize=(8, 8))
            env_counts = pd.Series(self.metrics['overall']['environment_distribution'])
            colors_env = sns.color_palette("pastel")[0:len(env_counts)]
            ax2.pie(env_counts.values, labels=env_counts.index, autopct='%1.1f%%', colors=colors_env, startangle=140)
            ax2.set_title('Distribution of Environments', fontsize=16)
            plt.tight_layout()
            visualizations['environment_distribution'] = fig2

            # 3. Growth of Activated Instances Over Time (Line Chart)  # **New Visualization**
            if 'monthly' in self.metrics and 'data' in self.metrics['monthly']:
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                monthly_data = sorted(self.metrics['monthly']['data'], key=lambda x: x['month'])
                months = [datetime.strptime(month['month'], '%Y-%m') for month in monthly_data]
                activated_instances = [month['activated_instances'] for month in monthly_data]
                
                # Plot cumulative growth
                sns.lineplot(x=months, y=activated_instances, marker='o', ax=ax3, color='teal')
                
                # Add average monthly growth annotation
                avg_growth = self.metrics['monthly'].get('average_monthly_growth', 0)
                ax3.text(0.02, 0.98, f'Average Monthly Growth: {avg_growth:.1f} instances',
                        transform=ax3.transAxes, fontsize=10, verticalalignment='top',
                        bbox=dict(facecolor='white', alpha=0.8))
                
                ax3.set_title('Total Activated Instances Seen by Month', fontsize=16, pad=20)
                ax3.set_xlabel('Month', fontsize=12)
                ax3.set_ylabel('Total Activated Instances', fontsize=12)
                ax3.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m'))
                plt.xticks(rotation=45)
                plt.tight_layout()
                visualizations['activated_instances_growth'] = fig3
            else:
                logger.warning("Monthly data not available. Skipping 'activated_instances_growth' visualization.")

            # Save all visualizations
            for name, fig in visualizations.items():
                fig_path = self.output_dir / f'{name}.png'
                fig.savefig(fig_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                logger.debug(f"Saved visualization '{name}' to '{fig_path}'")
            
            print(f"✓ Created {len(visualizations)} visualizations:")
            for name in visualizations.keys():
                print(f"  - {name.replace('_', ' ').title()}")
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            raise
        
        return visualizations

    def embed_images_in_html(self, html_content: str, visualizations: Dict[str, plt.Figure]) -> str:
        """
        Embed images directly into the HTML content as base64 strings.

        Parameters:
            html_content (str): The HTML content to embed images into.
            visualizations (Dict[str, plt.Figure]): The visualizations to embed.

        Returns:
            str: The HTML content with embedded images.
        """
        for name, img in visualizations.items():
            buffer = BytesIO()
            plt.imsave(buffer, img, format='png')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.read()).decode('utf-8')
            img_tag = f'data:image/png;base64,{img_str}'
            logger.debug(f"Embedding image for {name}: {img_tag[:100]}...")  # Log the first 100 characters of the base64 string

            # Replace image source with embedded base64 string
            html_content = re.sub(
                rf'<img\s+src=["\']{re.escape(name)}\.png["\']\s+alt=["\'].*?["\']\s*/?>',
                f'<img src="{img_tag}" alt="{name.replace("_", " ").title()}">',
                html_content,
                flags=re.IGNORECASE
            )
        
        return html_content

    def create_pdf_report(self, context: Dict, pdf_path: Path) -> None:
        """
        Create a PDF report using ReportLab.

        Parameters:
            context (Dict): The context data for the report.
            pdf_path (Path): The file path to save the PDF.
        """
        try:
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                    rightMargin=72, leftMargin=72,
                                    topMargin=72, bottomMargin=18)
            story = []
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Center', alignment=1))

            # Title
            story.append(Paragraph("Deep Security Usage Analyzer Report", styles['Title']))
            story.append(Spacer(1, 12))

            # Timestamp
            story.append(Paragraph(f"Generated on: {context['timestamp']}", styles['Normal']))
            story.append(Spacer(1, 12))

            # Overall Metrics
            story.append(Paragraph("Overall Metrics", styles['Heading2']))
            overall_data = [
                ["Total Unique Instances", f"{context['metrics']['overall']['total_instances']:,}"],
                ["Activated Instances", f"{context['metrics']['overall']['activated_instances']:,}"],
                ["Inactive Instances", f"{context['metrics']['overall']['inactive_instances']:,}"],
                ["Total Hours", f"{context['metrics']['overall']['total_hours']:.1f}"],
                ["Activated Hours", f"{context['metrics']['overall']['activated_hours']:.1f}"],
                ["Inactive Hours", f"{context['metrics']['overall']['inactive_hours']:.1f}"]
            ]
            table = Table(overall_data, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            story.append(table)
            story.append(Spacer(1, 24))

            # Environment Distribution
            story.append(Paragraph("Environment Distribution", styles['Heading2']))
            env_data = [["Environment", "Total Hosts", "Activated Hosts", "Most Used Module", "Max Concurrent", "Total Hours"]]
            for env, data in context['metrics']['by_environment'].items():
                env_data.append([
                    env,
                    f"{data['total_instances']}",
                    f"{data['activated_instances']}",
                    data['most_common_module'],
                    f"{data['max_concurrent'] if data['max_concurrent'] else 'None'}",
                    f"{data['total_utilization_hours']:.1f}" if isinstance(data['total_utilization_hours'], (int, float)) else "None"
                ])
            table = Table(env_data, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            story.append(table)
            story.append(Spacer(1, 24))

            # Module Usage Analysis
            story.append(Paragraph("Module Usage Analysis", styles['Heading2']))
            # Embed Module Usage Image
            if (self.output_dir / 'module_usage.png').exists():
                img_path = self.output_dir / 'module_usage.png'
                story.append(Image(str(img_path), width=6*inch, height=4*inch))
                story.append(Spacer(1, 12))
            # Embed Environment Distribution Image
            if (self.output_dir / 'environment_distribution.png').exists():
                img_path = self.output_dir / 'environment_distribution.png'
                story.append(Image(str(img_path), width=6*inch, height=6*inch))
                story.append(Spacer(1, 12))
            # Embed Activated Instances Growth Image  # **New Visualization**
            if (self.output_dir / 'activated_instances_growth.png').exists():
                img_path = self.output_dir / 'activated_instances_growth.png'
                story.append(Paragraph("Growth of Activated Instances Over Time", styles['Heading3']))
                story.append(Image(str(img_path), width=6*inch, height=4*inch))
                story.append(Spacer(1, 12))

            # Statistics Summary
            story.append(Paragraph("Statistics Summary", styles['Heading2']))
            stats_data = [
                ["Metric", "Value"],
                ["Total Unique Instances", f"{context['metrics']['overall']['total_instances']:,}"],
                ["Instances Running at Least One Module", f"{context['metrics']['overall']['activated_instances']:,}"],
                ["Instances Not Running Any Modules", f"{context['metrics']['overall']['inactive_instances']:,}"],
                ["Total Hours", f"{context['metrics']['overall']['total_hours']:.1f}"],
                ["Hours for Instances with Modules", f"{context['metrics']['overall']['activated_hours']:.1f}"],
                ["Hours for Instances without Modules", f"{context['metrics']['overall']['inactive_hours']:.1f}"],
                ["Max Concurrent Usage", f"{context['metrics']['overall_metrics']['max_concurrent_overall']:,}"],
                ["Unknown Environment Instances", f"{context['metrics']['by_environment'].get('Unknown', {}).get('total_instances', 0):,}"]
            ]
            table = Table(stats_data, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            story.append(table)
            story.append(Spacer(1, 24))

            # Monthly Data Analysis
            story.append(Paragraph("Monthly Data Analysis", styles['Heading2']))
            monthly_data = [
                ["Month", "Activated Instances", "Max Concurrent", "Avg Modules/Host", "Total Hours"]
            ]
            for month in context['metrics']['monthly']['data']:
                monthly_data.append([
                    month['month'],
                    month['activated_instances'],
                    month['max_concurrent'],
                    f"{month['avg_modules_per_host']:.2f}",
                    f"{month['total_hours']:.1f}"
                ])
            table = Table(monthly_data, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            story.append(table)
            story.append(Spacer(1, 24))

            # Data Gaps
            if context['metrics']['monthly']['data_gaps']:
                story.append(Paragraph("Data Gaps Detected", styles['Heading2']))
                for gap in context['metrics']['monthly']['data_gaps']:
                    story.append(Paragraph(f"- {gap}", styles['Normal']))
                story.append(Spacer(1, 12))

            # Unknown Environment Analysis
            if context['metrics']['by_environment'].get('Unknown') and \
               context['metrics']['by_environment']['Unknown']['total_instances'] > 0:
                story.append(Paragraph("Unknown Environment Analysis", styles['Heading2']))
                story.append(Paragraph(f"Number of hosts in unknown environment: {context['metrics']['by_environment']['Unknown']['total_instances']:,}", styles['Normal']))
                story.append(Paragraph("Common patterns found in unknown hosts:", styles['Normal']))
                for pattern in context['unknown_patterns']:
                    story.append(Paragraph(f"- {pattern}", styles['Normal']))
                story.append(Spacer(1, 12))

            doc.build(story)

        except Exception as e:
            logger.error(f"Failed to create PDF report: {str(e)}")

    def generate_report(self) -> None:
        """Generate a comprehensive HTML and PDF report of the analysis."""
        try:
            # Calculate enhanced metrics
            enhanced_metrics = self.calculate_enhanced_metrics()
            logger.debug(f"Enhanced Metrics: {enhanced_metrics}")
            
            # Calculate monthly metrics separately
            monthly_metrics = self.calculate_monthly_metrics()
            logger.debug(f"Monthly Metrics: {monthly_metrics}")
            
            # Prepare metrics for template
            combined_metrics = {
                'overall_metrics': enhanced_metrics.get('overall_metrics', {}),
                'utilization_metrics': enhanced_metrics.get('utilization_metrics', {}),
                'realm_metrics': enhanced_metrics.get('realm_metrics', {}),
                'by_environment': self.metrics.get('by_environment', {}),
                'overall': self.metrics.get('overall', {})
            }
            
            # Create report context
            report_context = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'metrics': {
                    'overall': combined_metrics['overall'],
                    'overall_metrics': combined_metrics['overall_metrics'],
                    'by_environment': combined_metrics['by_environment'],
                    'monthly': monthly_metrics
                },
                'unknown_patterns': []
            }
            
            # Debug log the monthly metrics before rendering
            logger.debug("Monthly metrics in report context:")
            if monthly_metrics and 'data' in monthly_metrics:
                for month_data in monthly_metrics['data']:
                    logger.debug(
                        f"Month: {month_data['month']}, "
                        f"Activated: {month_data['activated_instances']}, "
                        f"Max Concurrent: {month_data['max_concurrent']}"
                    )
            
            # Add unknown patterns if they exist
            if 'Unknown' in self.metrics.get('by_environment', {}):
                unknown_patterns = list(self.data[self.data['Environment'] == 'Unknown']['Hostname'].unique())[:10]
                report_context['unknown_patterns'] = unknown_patterns
            
            # Convert metrics to serializable types
            serializable_context = self._convert_to_serializable(report_context)
            
            # Render template
            template = Template(self.REPORT_TEMPLATE)
            report_html = template.render(**serializable_context)
            
            # Save HTML report
            report_path = self.output_dir / 'report.html'
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_html)
            logger.info(f"✓ Saved HTML report to '{report_path}'")
            
            # Create PDF report
            self.create_pdf_report(serializable_context, self.output_dir / 'report.pdf')
            logger.info(f"✓ Saved PDF report to '{self.output_dir / 'report.pdf'}'")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            raise

    def _convert_to_serializable(self, obj):
        """
        Recursively convert NumPy data types to native Python types.
        
        Parameters:
            obj: The object to convert.
            
        Returns:
            The converted object.
        """
        if isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
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
            self.data = self.load_and_preprocess_data()

            # Step 2: Calculate metrics
            update_progress("Calculating basic metrics...")
            self.metrics = self.calculate_metrics()

            # Step 3: Calculate monthly metrics
            update_progress("Analyzing monthly trends...")
            monthly_metrics = self.calculate_monthly_metrics()
            
            # **Integrate monthly_metrics into self.metrics**
            self.metrics['monthly'] = monthly_metrics
            logger.debug(f"Integrated monthly_metrics into self.metrics: {self.metrics['monthly']}")

            # Step 4: Create visualizations
            update_progress("Generating visualizations...")
            visualizations = self.create_visualizations()

            # Step 5: Generate report
            update_progress("Generating final report...")
            self.generate_report()

            # Convert metrics to serializable types
            serializable_metrics = self._convert_to_serializable(self.metrics)

            # Save metrics to JSON
            with open(self.output_dir / 'metrics.json', 'w') as json_file:
                json.dump(serializable_metrics, json_file, indent=4)
                logger.info(f"✓ Saved metrics to '{self.output_dir / 'metrics.json'}'")

            # Single summary at the end
            results = {
                'metrics': self.metrics,
                'monthly_metrics': monthly_metrics,
                'visualizations': visualizations,
                'raw_data': self.data,
                'analysis_timestamp': datetime.now().isoformat()
            }

            # Print final summary
            print("\nAnalysis Complete!")
            print(f"✓ Processed {len(self.data):,} records from {len(self.data['Hostname'].unique()):,} unique hosts")
            print(f"✓ Report and visualizations saved to: {self.output_dir}")

            if 'Unknown' in self.metrics['by_environment']:
                unknown_count = self.metrics['by_environment']['Unknown']['total_instances']
                print(f"⚠️  {unknown_count:,} hosts in unknown environment")

            return results

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
            raise

def main():
    """
    Main function to run the Trend Micro Deep Security Usage Analyzer.
    """
    try:
        analyzer = SecurityModuleAnalyzer()
        analyzer.analyze()
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()