"""
Data loading and preprocessing functionality for the Deep Security Usage Analyzer.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from tqdm import tqdm
import json
import os

from ..utils import (
    VALID_EXTENSIONS,
    MODULE_COLUMNS,
    classify_environment,
    filter_time_range
)

logger = logging.getLogger(__name__)

# Load selectors from config.json or use defaults
DEFAULT_SELECTORS = [
    "cce-aws-isobar",
    "gcss-common-test",
    "gcss-common-prod",
    "CMNSVC",
    "CMSVC"
]
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
try:
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        COMMON_SERVICES_SELECTORS = config.get("common_services_selectors", DEFAULT_SELECTORS)
except Exception as e:
    logger.warning(f"Could not load config.json, using default selectors. Error: {e}")
    COMMON_SERVICES_SELECTORS = DEFAULT_SELECTORS

def preprocess_df(df: pd.DataFrame, file_name: str = "") -> pd.DataFrame:
    """
    Centralized preprocessing for a single DataFrame:
    - Adds missing module columns with zeros
    - Fills NaNs and converts to int for module columns
    - Adds 'has_modules' column
    - Logs invalid values in module columns
    - Adds 'service_category' column based on Computer Group selectors
    """
    # Standardize column names
    df.columns = df.columns.str.strip()
    # Add missing module columns and fill NaNs
    for col in MODULE_COLUMNS:
        if col not in df.columns:
            df[col] = 0
            logger.debug(f"Added missing module column {col} to {file_name}")
        else:
            df[col] = df[col].fillna(0).astype(int)
        # Check for invalid values
        invalid_values = df[col][(df[col] != 0) & (df[col] != 1)].unique()
        if len(invalid_values) > 0:
            logger.warning(f"Invalid values {invalid_values} found in column {col} of {file_name}. Setting them to 0.")
            df.loc[(df[col] != 0) & (df[col] != 1), col] = 0
    # Add 'has_modules' column
    df['has_modules'] = df[MODULE_COLUMNS].sum(axis=1) > 0

    # Add 'service_category' column
    def categorize_service(computer_group):
        if pd.isna(computer_group) or not isinstance(computer_group, str):
            return "mission partners"
        cg_lower = computer_group.lower()
        for selector in COMMON_SERVICES_SELECTORS:
            if selector.lower() in cg_lower:
                return "common services"
        return "mission partners"

    df['service_category'] = df.get('Computer Group', pd.Series([None]*len(df))).apply(categorize_service)
    return df

def load_and_preprocess_data(directory: Path, start_date: Optional[pd.Timestamp] = None,
                           end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """
    Load data from files in the specified directory and preprocess it for analysis.

    Args:
        directory (Path): Directory containing the data files
        start_date (Optional[pd.Timestamp]): Start date for filtering
        end_date (Optional[pd.Timestamp]): End date for filtering

    Returns:
        pd.DataFrame: The combined and cleaned data.
    """
    # Initialize tqdm for pandas
    tqdm.pandas()
    
    files = [f for f in directory.glob('*') if f.suffix in VALID_EXTENSIONS]
    if not files:
        raise ValueError(f"No valid files found in {directory}")
    
    print(f"\nFound {len(files)} files to process")
    dfs = []
    
    for i, file in enumerate(files, 1):
        try:
            print(f"\rProcessing file {i}/{len(files)}: {file.name}" + " " * 50, end='')
            
            if file.suffix == '.csv':
                df = pd.read_csv(file, low_memory=False)
            else:
                df = pd.read_excel(file)
            
            # Centralized preprocessing
            df = preprocess_df(df, file.name)
            
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
    if start_date or end_date:
        logger.info(f"Applying time range filter: {start_date} to {end_date + pd.Timedelta(days=1,seconds=-1)}")
        combined_df = filter_time_range(combined_df, start_date, end_date)
        
        # Log the effect of filtering
        logger.info(f"Records after time range filtering: {len(combined_df)}")
        logger.info(f"Date range in filtered data: "
                   f"{combined_df['start_datetime'].min()} to "
                   f"{combined_df['stop_datetime'].max()}")
    
    return combined_df
