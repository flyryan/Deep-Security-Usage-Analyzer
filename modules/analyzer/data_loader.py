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
    - Adds 'cloud_provider' column based on filename/hostname patterns
    """
    # Standardize column names
    df.columns = df.columns.str.strip()
    # Add missing module columns and fill NaNs
    for col in MODULE_COLUMNS:
        if col not in df.columns:
            df[col] = 0
            logger.debug(f"Added missing module column {col} to {file_name}")
        else:
            # Convert to numeric, replacing non-numeric values with 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
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

    # Add 'cloud_provider' column
    def classify_cloud_provider(row):
        # Priority: Source_Cloud_Provider, then filename, then hostname
        provider = None
        # Check Source_Cloud_Provider if present
        if 'Source_Cloud_Provider' in row and pd.notna(row['Source_Cloud_Provider']):
            provider = row['Source_Cloud_Provider']
        # Check filename if available
        elif 'File_Name' in row and isinstance(row['File_Name'], str):
            fname = row['File_Name'].lower()
            if 'aws' in fname:
                provider = 'AWS'
            elif 'azure' in fname:
                provider = 'Azure'
            elif 'gcp' in fname:
                provider = 'GCP'
            elif 'oci' in fname:
                provider = 'OCI'
        # Check hostname if available
        elif 'Hostname' in row and isinstance(row['Hostname'], str):
            h = row['Hostname'].lower()
            if 'aws' in h:
                provider = 'AWS'
            elif 'azure' in h:
                provider = 'Azure'
            elif 'gcp' in h:
                provider = 'GCP'
            elif 'oci' in h:
                provider = 'OCI'
        if provider is None:
            provider = 'Unknown'
        return provider

    # If File_Name column is not present, add it for row-wise classification
    if 'File_Name' not in df.columns:
        df['File_Name'] = file_name

    # If Source_Cloud_Provider is not present, fill with None
    if 'Source_Cloud_Provider' not in df.columns:
        df['Source_Cloud_Provider'] = None

    df['cloud_provider'] = df.apply(classify_cloud_provider, axis=1)
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
                # First, try to detect delimiter by reading first line
                with open(file, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline()
                    if '\t' in first_line and ',' not in first_line:
                        # Tab-delimited file
                        df = pd.read_csv(file, sep='\t', low_memory=False, encoding='utf-8-sig')
                    else:
                        # Comma-delimited file
                        df = pd.read_csv(file, low_memory=False, encoding='utf-8-sig')
                
                # Check for duplicate header rows within the data
                header_cols = df.columns.tolist()
                duplicate_header_mask = df.apply(lambda row: all(str(row[col]) == col for col in header_cols if col in row.index), axis=1)
                if duplicate_header_mask.any():
                    logger.warning(f"Found {duplicate_header_mask.sum()} duplicate header rows in {file.name}, removing them")
                    df = df[~duplicate_header_mask]
            else:
                df = pd.read_excel(file)
            
            # Extract cloud provider from filename
            cloud_provider = None
            filename = file.name.lower()
            if 'aws' in filename:
                cloud_provider = 'AWS'
            elif 'azure' in filename:
                cloud_provider = 'Azure'
            elif 'gcp' in filename:
                cloud_provider = 'GCP'
            elif 'oci' in filename:
                cloud_provider = 'OCI'
            else:
                cloud_provider = 'Unknown'

            # Centralized preprocessing
            df = preprocess_df(df, file.name)
            # Add 'Source_Cloud_Provider' column
            df['Source_Cloud_Provider'] = cloud_provider

            # Handle date columns
            date_columns_found = False
            
            # Check for various date column formats
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
                    date_columns_found = True
                except Exception as e:
                    logger.error(f"Error converting date/time columns in {file.name}: {str(e)}")
            elif 'Start' in df.columns:
                try:
                    df['start_datetime'] = pd.to_datetime(df['Start'], errors='coerce')
                    if 'Stop' in df.columns:
                        df['stop_datetime'] = pd.to_datetime(df['Stop'], errors='coerce')
                    date_columns_found = True
                except Exception as e:
                    logger.error(f"Error converting Start/Stop columns in {file.name}: {str(e)}")
            else:
                # Try to find date columns with different naming conventions
                start_candidates = [col for col in df.columns if 'start' in col.lower() and 'date' in col.lower()]
                stop_candidates = [col for col in df.columns if 'stop' in col.lower() and 'date' in col.lower()]
                
                if start_candidates and stop_candidates:
                    try:
                        df['start_datetime'] = pd.to_datetime(df[start_candidates[0]], errors='coerce')
                        df['stop_datetime'] = pd.to_datetime(df[stop_candidates[0]], errors='coerce')
                        date_columns_found = True
                        logger.info(f"Using alternative date columns: {start_candidates[0]}, {stop_candidates[0]}")
                    except Exception as e:
                        logger.error(f"Error converting alternative date columns in {file.name}: {str(e)}")
            
            if not date_columns_found:
                logger.error(f"No valid datetime columns found in {file.name}")
                logger.debug(f"Available columns: {df.columns.tolist()}")
                continue
            
            # Remove rows with invalid dates
            invalid_dates = df['start_datetime'].isna() | df['stop_datetime'].isna()
            if invalid_dates.any():
                logger.debug(f"Removing {invalid_dates.sum()} rows with invalid dates from {file.name}")
                df = df[~invalid_dates]
            
            # Extract environment from filename
            env = None
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

    # Add progress meter for cloud provider classification
    def classify_cloud_provider_final(row):
        # Priority: cloud_provider column (from preprocessing), then Source_Cloud_Provider, then hostname
        provider = None
        if 'cloud_provider' in row and pd.notna(row['cloud_provider']):
            provider = row['cloud_provider']
        elif 'Source_Cloud_Provider' in row and pd.notna(row['Source_Cloud_Provider']):
            provider = row['Source_Cloud_Provider']
        elif 'Hostname' in row and isinstance(row['Hostname'], str):
            h = row['Hostname'].lower()
            if 'aws' in h:
                provider = 'AWS'
            elif 'azure' in h:
                provider = 'Azure'
            elif 'gcp' in h:
                provider = 'GCP'
            elif 'oci' in h:
                provider = 'OCI'
        if provider is None:
            provider = 'Unknown'
        return provider

    combined_df['Cloud_Provider'] = combined_df.progress_apply(classify_cloud_provider_final, axis=1)
    
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
    logger.info(f"Cloud Providers found: {', '.join(sorted(combined_df['Cloud_Provider'].unique()))}")

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
