"""
Core analyzer functionality for the Deep Security Usage Analyzer.
"""
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from tqdm import tqdm

from .utils import (
    VALID_EXTENSIONS,
    MODULE_COLUMNS,
    classify_environment,
    convert_to_serializable,
    filter_time_range
)
from .visualizations import create_visualizations
from .report_generator import generate_report

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
        
        # Check for input files
        input_files = [f for f in self.directory.glob('*') if f.suffix in VALID_EXTENSIONS]
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
            for col in MODULE_COLUMNS:
                if col not in test_df.columns:
                    test_df[col] = 0
                    logger.debug(f"Added missing module column: {col}")
            
            logger.info(f" Initialized with modules: {', '.join(MODULE_COLUMNS)}")
            logger.info(f" Output will be saved to: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error initializing analyzer: {str(e)}")
            raise
        
        tqdm.pandas()  # Initialize tqdm for pandas

        # Add time range parameters
        self.start_date = pd.to_datetime(start_date) if start_date else None
        self.end_date = pd.to_datetime(end_date) if end_date else None

    def load_and_preprocess_data(self) -> pd.DataFrame:
        """
        Load data from files in the specified directory and preprocess it for analysis.

        Returns:
            pd.DataFrame: The combined and cleaned data.
        """
        files = [f for f in self.directory.glob('*') if f.suffix in VALID_EXTENSIONS]
        if not files:
            raise ValueError(f"No valid files found in {self.directory}")
        
        print(f"\nFound {len(files)} files to process")
        dfs = []
        
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
                for col in MODULE_COLUMNS:
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
                if 'dev' in filename or 'development' in filename:
                    env = 'Development'
                elif 'prod' in filename or 'production' in filename:
                    env = 'Production'
                elif 'test' in filename or 'qa' in filename:
                    env = 'Test'
                elif 'int' in filename or 'integration' in filename:
                    env = 'Integration'
                elif 'stage' in filename or 'staging' in filename:
                    env = 'Staging'
                elif 'uat' in filename or 'acceptance' in filename:
                    env = 'UAT'
                elif 'dr' in filename or 'disaster' in filename:
                    env = 'DR'

                # Debug logging to confirm environment extraction
                logger.debug(f"File '{file.name}' assigned to environment '{env}'")
                
                # Add 'Source_Environment' column
                df['Source_Environment'] = env
                
                # Verify module columns contain valid values (0 or 1)
                for col in MODULE_COLUMNS:
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
            lambda row: classify_environment(row['Hostname'], row['Source_Environment']),
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
        for col in MODULE_COLUMNS:
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

        # After loading and initial preprocessing, apply time range filter
        if self.start_date or self.end_date:
            logger.info(f"Applying time range filter: {self.start_date} to {self.end_date + pd.Timedelta(days=1,seconds=-1)}")
            combined_df = filter_time_range(combined_df, self.start_date, self.end_date)
            
            # Log the effect of filtering
            logger.info(f"Records after time range filtering: {len(combined_df)}")
            logger.info(f"Date range in filtered data: "
                       f"{combined_df['start_datetime'].min()} to "
                       f"{combined_df['stop_datetime'].max()}")
        
        return combined_df

    def _calculate_concurrent_usage(self, df: pd.DataFrame, start_date=None, end_date=None) -> int:
        """
        Calculate the maximum concurrent usage from a DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame
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

    def calculate_monthly_metrics(self) -> Dict:
        """
        Calculate monthly metrics including cumulative growth.

        Returns:
            Dict: Monthly metrics data
        """
        monthly_metrics = {
            'data': [],
            'data_gaps': [],
            'total_months': 0,
            'date_range': '',
            'average_monthly_growth': 0
        }
        
        try:
            # Get all activated instances (these are instances that have any modules at any time)
            activated_mask = self.data[MODULE_COLUMNS].sum(axis=1) > 0
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
                    activated_month_data = month_data[month_data[MODULE_COLUMNS].sum(axis=1) > 0]
                    activated_instances_current = set(activated_month_data['Hostname'].unique())

                    # Calculate duration per instance without double counting
                    duration_per_instance = activated_month_data.groupby('Hostname')['Duration (Seconds)'].sum()
                    total_hours = duration_per_instance.sum() / 3600

                    # Calculate average modules per host
                    if not activated_month_data.empty:
                        avg_modules_per_host = activated_month_data[MODULE_COLUMNS].sum(axis=1).mean()
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

    def calculate_metrics(self) -> Dict:
        """
        Calculate comprehensive metrics from the loaded data.

        Returns:
            Dict: Calculated metrics
        """
        if self.data is None:
            raise ValueError("No data loaded for analysis")
        
        logger.info("Calculating comprehensive metrics...")
        
        # Add has_modules column to the dataframe
        self.data['has_modules'] = self.data[MODULE_COLUMNS].sum(axis=1) > 0
        
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
        correlation_matrix = self.data[MODULE_COLUMNS].corr()
        metrics['overall']['correlation_matrix'] = correlation_matrix.to_dict()
        
        # Calculate module usage
        metrics['overall']['module_usage'] = {
            col: int(self.data[col].sum()) for col in MODULE_COLUMNS
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
                col: set(env_data[env_data[col] > 0]['Hostname']) for col in MODULE_COLUMNS
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
                'module_usage': {col: len(module_usage_counts[col]) for col in MODULE_COLUMNS},
                'module_usage_percentage': module_usage_percentage,
                'most_common_module': max(
                    MODULE_COLUMNS,
                    key=lambda col: len(module_usage_counts[col])
                ) if sum(len(instances) for instances in module_usage_counts.values()) > 0 else "None",
                'avg_modules_per_host': env_data[MODULE_COLUMNS].sum(axis=1).mean(),
                'max_concurrent': max_concurrent,
                'total_utilization_hours': total_hours,
                'correlation_matrix': env_data[MODULE_COLUMNS].corr().to_dict()
            }
            
            env_distribution[env] = len(env_total_hosts)
        
        metrics['overall']['environment_distribution'] = {
            env: data['activated_instances']  # Use activated_instances instead of total_instances
            for env, data in metrics['by_environment'].items()
            if data['activated_instances'] > 0  # Only include environments with activated instances
        }
        
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
            
            # Integrate monthly_metrics into self.metrics
            self.metrics['monthly'] = monthly_metrics
            logger.debug(f"Integrated monthly_metrics into self.metrics: {self.metrics['monthly']}")

            # Step 4: Create visualizations
            update_progress("Generating visualizations...")
            visualizations = create_visualizations(self.metrics, self.output_dir)

            # Step 5: Generate report
            update_progress("Generating final report...")
            generate_report(self.metrics, self.output_dir, visualizations)

            # Convert metrics to serializable types
            serializable_metrics = convert_to_serializable(self.metrics)

            # Save metrics to JSON
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
