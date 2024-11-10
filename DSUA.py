"""
Trend Micro Deep Security Usage Analyzer (DSUA)

This script analyzes Trend Micro Deep Security module usage across different environments
and generates comprehensive reports, including metrics, visualizations, and an HTML report.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
                    <div class="metric-value">{{ metrics.overall.total_instances }}</div>
                    <div class="metric-label">Total Unique Instances</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall.activated_instances }}</div>
                    <div class="metric-label">Activated Instances</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall.inactive_instances }}</div>
                    <div class="metric-label">Inactive Instances</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall.total_hours | round(1) }}</div>
                    <div class="metric-label">Total Hours</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.overall_metrics.max_concurrent_overall }}</div>
                    <div class="metric-label">Max Concurrent Overall</div>
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
                    <td>{{ data.max_concurrent if data.max_concurrent else 'N/A' }}</td>
                    <td>{{ "%.1f"|format(data.total_utilization_hours) if data.total_utilization_hours != "N/A" else "N/A" }}</td>
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
                    <th>Max Concurrent</th>
                    <th>Avg Modules/Host</th>
                    <th>Total Hours</th>
                </tr>
                {% for month in metrics.monthly.data %}
                <tr>
                    <td>{{ month.month }}</td>
                    <td>{{ month.activated_instances }}</td>
                    <td>{{ month.max_concurrent }}</td>
                    <td>{{ "%.2f"|format(month.avg_modules_per_host) }}</td>
                    <td>{{ "%.1f"|format(month.total_hours) }}</td>
                </tr>
                {% endfor %}
            </table>

            {% if metrics.monthly.data_gaps %}
            <div class="highlight">
                <h3>Data Gaps Detected</h3>
                <p>The following periods have missing or incomplete data:</p>
                <ul>
                {% for gap in metrics.monthly.data_gaps %}
                    <li>{{ gap }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
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
        
        # Check for input files
        input_files = [f for f in self.directory.glob('*') if f.suffix in self.VALID_EXTENSIONS]
        if not input_files:
            raise ValueError(f"No valid input files found in {self.directory}")
        
        logger.info(f"Initialized Trend Micro Deep Security Usage Analyzer with input directory: {self.directory}")
        logger.info(f"Output will be saved to: {self.output_dir}")
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
                    if 'Start' in df.columns:
                        df['Start'] = pd.to_datetime(df['Start'], errors='coerce')
                    if 'Stop' in df.columns:
                        df['Stop'] = pd.to_datetime(df['Stop'], errors='coerce')
                    
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
                    
                    dfs.append(df)
                    
                except Exception as e:
                    print(f"\n⚠️  Error processing {file.name}: {str(e)}")
        
        print("\n\nCombining and cleaning data...")
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
        
        print(f"✓ Final dataset: {len(combined_df):,} records from {len(combined_df['Hostname'].unique()):,} unique hosts")
        
        return combined_df

    def calculate_monthly_metrics(self) -> Dict:
        """
        Calculate monthly metrics to identify trends and data gaps.

        Returns:
            Dict: A dictionary containing monthly metrics and data gaps.
        """
        monthly_metrics = {
            'data': [],
            'data_gaps': [],
            'total_months': 0,
            'date_range': ''
        }
        
        try:
            # Handle different date column formats
            if 'Start Date' in self.data.columns and 'Start Time' in self.data.columns:
                self.data['start_datetime'] = pd.to_datetime(
                    self.data['Start Date'].astype(str) + ' ' + 
                    self.data['Start Time'].astype(str),
                    format='mixed',
                    errors='coerce'
                )
            elif 'Start' in self.data.columns:
                self.data['start_datetime'] = pd.to_datetime(self.data['Start'], errors='coerce')
            
            if not 'start_datetime' in self.data.columns or self.data['start_datetime'].isna().all():
                logger.warning("No valid date information found")
                return monthly_metrics
            
            # Get date range
            min_date = self.data['start_datetime'].min()
            max_date = self.data['start_datetime'].max()
            monthly_metrics['date_range'] = f"{min_date.strftime('%Y-%m')} to {max_date.strftime('%Y-%m')}"
            
            # Generate all months between min and max date
            all_months = pd.date_range(
                start=min_date.replace(day=1),
                end=max_date.replace(day=1),
                freq='MS'
            ).to_period('M')
            
            # Group by month
            self.data['month'] = self.data['start_datetime'].dt.to_period('M')
            months_with_data = set(self.data['month'].unique())
            
            # Track data gaps
            for month in all_months:
                if month not in months_with_data:
                    monthly_metrics['data_gaps'].append(month.strftime('%Y-%m'))
            
            # Calculate metrics for each month
            monthly_data = []
            for month in months_with_data:
                month_data = self.data[self.data['month'] == month]
                
                # Calculate metrics for the month
                activated_instances = len(month_data[month_data[self.MODULE_COLUMNS].sum(axis=1) > 0]['Hostname'].unique())
                
                # Calculate maximum concurrent for the month
                max_concurrent = self._calculate_max_concurrent(month_data)
                
                data = {
                    'month': str(month),
                    'activated_instances': activated_instances,
                    'max_concurrent': max_concurrent,
                    'avg_modules_per_host': month_data[self.MODULE_COLUMNS].sum(axis=1).mean(),
                    'total_hours': (month_data['Duration (Seconds)'].sum() / 3600) if 'Duration (Seconds)' in month_data.columns else 0
                }
                monthly_data.append(data)
            
            # Sort monthly data by month string (should be in YYYY-MM format)
            monthly_metrics['data'] = sorted(monthly_data, key=lambda x: x['month'], reverse=True)
            monthly_metrics['total_months'] = len(monthly_data)
            
            return monthly_metrics
            
        except Exception as e:
            logger.warning(f"Error calculating monthly metrics: {str(e)}")
            return monthly_metrics

    def _calculate_max_concurrent(self, df: pd.DataFrame) -> int:
        """Helper method to calculate maximum concurrent instances."""
        max_concurrent = 0
        try:
            if 'stop_datetime' in df.columns:
                timeline = []
                for _, row in df.iterrows():
                    if pd.notna(row['start_datetime']) and pd.notna(row['stop_datetime']):
                        timeline.append((row['start_datetime'], 1))
                        timeline.append((row['stop_datetime'], -1))
                
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
        """
        Calculate usage metrics across different environments and modules.

        Returns:
            Dict: A dictionary containing metrics and statistics.
        """
        if self.data is None:
            raise ValueError("No data loaded for analysis")
        
        print("\nClassifying environments and calculating metrics...")
        total_records = len(self.data)
        classify_progress = 0

        # Initialize the 'Environment' column
        self.data['Environment'] = 'Unknown'

        for idx, row in self.data.iterrows():
            env = self.classify_environment(row['Hostname'], row.get('Source_Environment'))
            self.data.at[idx, 'Environment'] = env

            classify_progress += 1
            if classify_progress % 9 == 0 or classify_progress == total_records:
                percentage = (classify_progress / total_records) * 100
                sys.stdout.write(f"\rProgress: {percentage:.1f}% ({classify_progress:,}/{total_records:,} records)")
                sys.stdout.flush()

        print()  # Move to the next line after progress completion

        environments = sorted(self.data['Environment'].unique())
        print(f"Calculating metrics for {len(environments)} environments...")

        metrics = {
            'by_environment': {},
            'overall': {},
            'trends': {}
        }
        
        # Calculate module status and hours
        self.data['has_modules'] = self.data[self.MODULE_COLUMNS].sum(axis=1) > 0
        
        # Calculate hours for activated and inactive instances
        if 'Duration (Seconds)' in self.data.columns:
            activated_hours = (self.data[self.data['has_modules']]['Duration (Seconds)'].sum()) / 3600
            inactive_hours = (self.data[~self.data['has_modules']]['Duration (Seconds)'].sum()) / 3600
            total_hours = activated_hours + inactive_hours
        else:
            activated_hours = 0
            inactive_hours = 0
            total_hours = 0
        
        # Calculate overall metrics first
        total_instances = len(self.data['Hostname'].unique())
        activated_instances = len(self.data[self.data['has_modules']]['Hostname'].unique())
        inactive_instances = total_instances - activated_instances
        
        metrics['overall'].update({
            'total_instances': total_instances,
            'activated_instances': activated_instances,
            'inactive_instances': inactive_instances,
            'total_hours': total_hours,
            'activated_hours': activated_hours,
            'inactive_hours': inactive_hours
        })
        
        # Calculate correlation matrix first
        correlation_matrix = self.data[self.MODULE_COLUMNS].corr()
        metrics['overall']['correlation_matrix'] = correlation_matrix.to_dict()
        
        # Calculate metrics for each environment
        environments = sorted(self.data['Environment'].unique())
        print(f"\nCalculating metrics for {len(environments)} environments...")
        
        for env in environments:
            env_df = self.data[self.data['Environment'] == env]
            activated_instances = env_df[env_df[self.MODULE_COLUMNS].sum(axis=1) > 0]
            inactive_instances = env_df[env_df[self.MODULE_COLUMNS].sum(axis=1) == 0]
            
            total_instances = len(env_df['Hostname'].unique())
            module_usage_counts = {col: set(env_df[env_df[col] > 0]['Hostname']) for col in self.MODULE_COLUMNS}
            
            # Calculate module usage percentage
            module_usage_percentage = {}
            for module, instances in module_usage_counts.items():
                unique_instance_count = len(instances)
                percentage = (unique_instance_count / total_instances) * 100
                module_usage_percentage[module] = percentage
            
            # Calculate max concurrent instances
            max_concurrent = 0
            if 'Duration (Seconds)' in env_df.columns:
                grouped = env_df.groupby('Hostname')
                max_concurrent = max(len(g) for _, g in grouped)
                total_hours = env_df['Duration (Seconds)'].sum() / 3600
            else:
                total_hours = 0
            
            metrics['by_environment'][env] = {
                'activated_instances': len(activated_instances['Hostname'].unique()),
                'inactive_instances': len(inactive_instances['Hostname'].unique()),
                'total_instances': total_instances,
                'module_usage': {col: len(module_usage_counts[col]) for col in self.MODULE_COLUMNS},
                'module_usage_percentage': module_usage_percentage,
                'most_common_module': max(
                    self.MODULE_COLUMNS,
                    key=lambda col: len(module_usage_counts[col])
                ) if sum(len(instances) for instances in module_usage_counts.values()) > 0 else "None",
                'avg_modules_per_host': env_df[self.MODULE_COLUMNS].sum(axis=1).mean(),
                'max_concurrent': max_concurrent,
                'total_utilization_hours': total_hours,
                'correlation_matrix': env_df[self.MODULE_COLUMNS].corr().to_dict()  # Add per-environment correlation
            }
        
        # Calculate overall metrics
        total_activated = len(self.data[self.data[self.MODULE_COLUMNS].sum(axis=1) > 0]['Hostname'].unique())
        total_instances = len(self.data['Hostname'].unique())
        
        # Calculate hours with more detailed breakdown
        activated_hours = 0
        inactive_hours = 0
        if 'Duration (Seconds)' in self.data.columns:
            # Add column indicating if instance has any modules
            self.data['has_modules'] = self.data[self.MODULE_COLUMNS].sum(axis=1) > 0
            
            # Group by hostname and calculate max duration and module status
            instance_hours = (self.data.groupby('Hostname')
                             .agg({
                                 'Duration (Seconds)': 'max',
                                 'has_modules': 'any'
                             }))
            
            # Calculate hours for activated and inactive instances
            activated_hours = (instance_hours[instance_hours['has_modules']]['Duration (Seconds)'].sum()) / 3600
            inactive_hours = (instance_hours[~instance_hours['has_modules']]['Duration (Seconds)'].sum()) / 3600
        
        metrics['overall'].update({
            'activated_instances': total_activated,
            'inactive_instances': total_instances - total_activated,
            'total_instances': total_instances,
            'total_hours': activated_hours + inactive_hours,
            'activated_hours': activated_hours,
            'inactive_hours': inactive_hours,
            'module_usage': {col: self.data[col].sum() for col in self.MODULE_COLUMNS},
            'environment_distribution': {
                env: metrics['by_environment'][env]['total_instances'] 
                for env in environments
            }
        })
        
        return metrics

    def calculate_enhanced_metrics(self) -> Dict:
        """Calculate comprehensive metrics including utilization and realm statistics."""
        if self.data is None:
            raise ValueError("No data loaded for analysis")
        
        # Convert datetime columns with proper error handling
        try:
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
        
        # Calculate metrics for each realm
        for realm in realms:
            realm_data = self.data[self.data['Computer Group'].fillna('Unknown') == realm]
            
            # Calculate module usage
            module_columns = ['AM', 'WRS', 'DC', 'AC', 'IM', 'LI', 'FW', 'DPI', 'SAP']
            has_modules = realm_data[module_columns].sum(axis=1) > 0
            
            # Calculate unique instances and their states
            unique_instances = realm_data['Hostname'].nunique()
            activated_instances = realm_data[has_modules]['Hostname'].nunique()
            inactive_instances = unique_instances - activated_instances
            
            # Calculate maximum concurrent instances
            max_concurrent = 0
            try:
                if 'start_datetime' in realm_data.columns and not realm_data['start_datetime'].isna().all():
                    # Create timeline of instance counts
                    timeline = []
                    for _, row in realm_data.iterrows():
                        if has_modules[row.name] and pd.notna(row['start_datetime']) and pd.notna(row['stop_datetime']):
                            timeline.append((row['start_datetime'], 1))
                            timeline.append((row['stop_datetime'], -1))
                    
                    if timeline:
                        timeline.sort(key=lambda x: x[0])
                        current_count = 0
                        for _, count_change in timeline:
                            current_count += count_change
                            max_concurrent = max(max_concurrent, current_count)
            except Exception as e:
                logger.warning(f"Error calculating concurrent instances for realm {realm}: {str(e)}")
                max_concurrent = "N/A"
            
            # Calculate total utilization hours
            total_hours = 0
            try:
                if 'Duration (Seconds)' in realm_data.columns:
                    total_hours = realm_data[has_modules]['Duration (Seconds)'].sum() / 3600
                elif 'stop_datetime' in realm_data.columns and not realm_data['stop_datetime'].isna().all():
                    # Calculate duration from datetime fields
                    duration = (realm_data['stop_datetime'] - realm_data['start_datetime'])
                    total_hours = duration[has_modules].dt.total_seconds().sum() / 3600
            except Exception as e:
                logger.warning(f"Error calculating utilization hours for realm {realm}: {str(e)}")
                total_hours = "N/A"
            
            enhanced_metrics['realm_metrics'][realm] = {
                'unique_instances': unique_instances,
                'activated_instances': activated_instances,
                'inactive_instances': inactive_instances,
                'max_concurrent': max_concurrent,
                'total_utilization_hours': total_hours
            }
        
        # Calculate overall metrics
        total_unique_instances = self.data['Hostname'].nunique()
        total_activated = self.data[self.data[module_columns].sum(axis=1) > 0]['Hostname'].nunique()
        
        enhanced_metrics['overall_metrics'] = {
            'total_unique_instances': total_unique_instances,
            'total_activated_instances': total_activated,
            'total_inactive_instances': total_unique_instances - total_activated,
            'max_concurrent_overall': sum(
                metrics['max_concurrent'] 
                for metrics in enhanced_metrics['realm_metrics'].values() 
                if isinstance(metrics['max_concurrent'], (int, float))
            )
        }
        
        # Calculate utilization metrics
        total_utilization = 0
        try:
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
        
        enhanced_metrics['utilization_metrics'] = {
            'total_hours': total_utilization,
            'average_hours_per_instance': total_utilization / total_unique_instances if total_unique_instances > 0 else 0
        }
        
        # Suppress Enhanced Metrics Summary output
        # print("\nEnhanced Metrics Summary:")
        # print(f"Total Unique Instances: {enhanced_metrics['overall_metrics']['total_unique_instances']:,}")
        # print(f"Activated Instances: {enhanced_metrics['overall_metrics']['total_activated_instances']:,}")
        # print(f"Inactive Instances: {enhanced_metrics['overall_metrics']['total_inactive_instances']:,}")
        
        return enhanced_metrics

    def create_visualizations(self) -> Dict[str, plt.Figure]:
        """
        Create visualizations to represent module usage and environment distribution.

        Returns:
            Dict[str, plt.Figure]: A dictionary of visualization figures.
        """
        visualizations = {}
        
        try:
            # Set style parameters
            plt.style.use('default')
            colors = {
                'Production': 'lightcoral',
                'Development': 'lightgreen',
                'Test': 'lightblue',
                'Staging': 'lightsalmon',
                'DR': 'lightgray',
                'UAT': 'plum',
                'Integration': 'wheat'
            }
            
            # 1. Stacked Module Usage Bar Chart
            fig1, ax1 = plt.subplots(figsize=(15, 8))
            module_cols = self.MODULE_COLUMNS
            env_data = {}
            bottom = np.zeros(len(module_cols))
            
            for env in ['Production', 'Development', 'Test', 'Staging', 'Integration']:
                if env in self.metrics['by_environment']:
                    env_data[env] = pd.Series(self.metrics['by_environment'][env]['module_usage'])
                    ax1.bar(module_cols, env_data[env], 
                           label=env, 
                           color=colors.get(env, 'gray'),
                           alpha=0.7,
                           bottom=bottom)
                    bottom += env_data[env]
            
            ax1.set_title('Security Module Usage Across Environments', pad=20)
            ax1.set_xlabel('Security Modules')
            ax1.set_ylabel('Usage Count')
            ax1.legend(loc='upper right')
            plt.xticks(rotation=45)
            plt.tight_layout()
            visualizations['module_usage'] = fig1
            
            # 2. Environment distribution pie chart
            fig2, ax2 = plt.subplots(figsize=(12, 12))
            env_counts = pd.Series(self.metrics['overall']['environment_distribution'])
            wedges, texts, autotexts = ax2.pie(env_counts.values,
                                              labels=env_counts.index,
                                              autopct='%1.1f%%',
                                              colors=[colors.get(env, 'gray') for env in env_counts.index])
            ax2.set_title('Distribution of Environments')
            plt.setp(autotexts, size=8, weight="bold")
            plt.setp(texts, size=10)
            visualizations['environment_distribution'] = fig2
            
            # Save all visualizations
            for name, fig in visualizations.items():
                fig.savefig(self.output_dir / f'{name}.png',
                           dpi=300,
                           bbox_inches='tight',
                           facecolor='white',
                           edgecolor='none')
            
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
                    f"{data['max_concurrent'] if data['max_concurrent'] else 'N/A'}",
                    f"{data['total_utilization_hours']:.1f}" if data['total_utilization_hours'] != "N/A" else "N/A"
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
            if 'module_usage.png' in [f.name for f in self.output_dir.glob('*')]:
                img_path = self.output_dir / 'module_usage.png'
                story.append(Image(str(img_path), width=6*inch, height=4*inch))
                story.append(Spacer(1, 12))
            # Embed Environment Distribution Image
            if 'environment_distribution.png' in [f.name for f in self.output_dir.glob('*')]:
                img_path = self.output_dir / 'environment_distribution.png'
                story.append(Image(str(img_path), width=6*inch, height=6*inch))
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
            if context['metrics']['by_environment'].get('Unknown') and context['metrics']['by_environment']['Unknown']['total_instances'] > 0:
                story.append(Paragraph("Unknown Environment Analysis", styles['Heading2']))
                story.append(Paragraph(f"Number of hosts in unknown environment: {context['metrics']['by_environment']['Unknown']['total_instances']:,}", styles['Normal']))
                story.append(Paragraph("Common patterns found in unknown hosts:", styles['Normal']))
                for pattern in context['unknown_patterns']:
                    story.append(Paragraph(f"- {pattern}", styles['Normal']))
                story.append(Spacer(1, 12))

            doc.build(story)
            logger.info(f"PDF report generated successfully at {pdf_path}")

        except Exception as e:
            logger.error(f"Failed to create PDF report: {str(e)}")

    def generate_report(self) -> None:
        """
        Generate a comprehensive HTML and PDF report of the analysis.

        The report includes overall metrics, environment distribution, module usage analysis, and monthly trends.
        """
        print("\nGenerating report...")
        
        try:
            # Stage 1: Calculate enhanced metrics
            print("  ↳ Calculating enhanced metrics...")
            enhanced_metrics = self.calculate_enhanced_metrics()
            logger.debug(f"Enhanced Metrics: {enhanced_metrics}")
            
            # Stage 2: Prepare metrics for template
            print("  ↳ Preparing template data...")
            combined_metrics = {
                'overall_metrics': enhanced_metrics['overall_metrics'],
                'utilization_metrics': enhanced_metrics['utilization_metrics'],
                'realm_metrics': enhanced_metrics['realm_metrics'],
                'by_environment': self.metrics['by_environment'],
                'overall': self.metrics['overall']
            }
            logger.debug(f"Combined Metrics: {combined_metrics}")
            
            # Stage 3: Calculate unknown patterns
            print("  ↳ Analyzing unknown patterns...")
            unknown_patterns = []
            if 'Unknown' in self.metrics['by_environment']:
                unknown_env = self.metrics['by_environment']['Unknown']
                unknown_patterns = list(self.data[self.data['Environment'] == 'Unknown']['Hostname'].unique())[:10]  # Example extraction
            logger.debug(f"Unknown Patterns: {unknown_patterns}")
            
            # Stage 4: Calculate monthly metrics
            print("  ↳ Processing monthly data...")
            monthly_metrics = self.calculate_monthly_metrics()
            logger.debug(f"Monthly Metrics: {monthly_metrics}")
            
            # Ensure monthly metrics are included in combined metrics
            combined_metrics['monthly'] = monthly_metrics
            
            # Stage 5: Create report context
            print("  ↳ Preparing final report...")
            report_context = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'metrics': combined_metrics,
                'unknown_patterns': unknown_patterns
            }
            logger.debug(f"Report Context: {report_context}")
            
            # Convert metrics to serializable types
            serializable_context = self._convert_to_serializable(report_context)
            
            # Stage 6: Render HTML template
            print("  ↳ Rendering HTML template...")
            template = Template(self.REPORT_TEMPLATE)
            report_html = template.render(**serializable_context)
            
            # Stage 7: Embed existing images in HTML
            print("  ↳ Embedding images in HTML...")
            visualizations = {
                'module_usage': plt.imread(self.output_dir / 'module_usage.png'),
                'environment_distribution': plt.imread(self.output_dir / 'environment_distribution.png')
            }
            report_html = self.embed_images_in_html(report_html, visualizations)
            
            # Stage 8: Save HTML Report
            print("  ↳ Saving HTML report...")
            report_path = self.output_dir / 'report.html'
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_html)
            
            # Stage 9: Generate PDF Report with ReportLab
            print("  ↳ Generating PDF report with ReportLab...")
            self.create_pdf_report(report_context, self.output_dir / 'report.pdf')
            logger.info(f"PDF report generated successfully at {self.output_dir / 'report.pdf'}")
        
        except TypeError as te:
            logger.error(f"Failed to generate report: {str(te)}")
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")

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
                logger.info(f"Starting: {step_name}")

            # Step 1: Load and preprocess data
            update_progress("Loading and preprocessing data...")
            self.data = self.load_and_preprocess_data()

            # Step 2: Calculate metrics
            update_progress("Calculating basic metrics...")
            self.metrics = self.calculate_metrics()

            # Step 3: Calculate monthly metrics
            update_progress("Analyzing monthly trends...")
            monthly_metrics = self.calculate_monthly_metrics()

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