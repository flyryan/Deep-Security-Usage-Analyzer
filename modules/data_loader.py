import pandas as pd
import warnings
from pathlib import Path
from typing import List
from metrics_calculator import MetricsCalculator  # Update to absolute import if needed

class DataLoader:
    """Handles loading and preprocessing of data."""

    VALID_EXTENSIONS = {'.csv', '.xlsx', '.xls'}

    def __init__(self, directory: str, logger):
        self.directory = Path(directory)
        self.logger = logger

    def load_data(self) -> pd.DataFrame:
        """Load data from files in the specified directory and preprocess it."""
        files = [f for f in self.directory.glob('*') if f.suffix in self.VALID_EXTENSIONS]
        if not files:
            self.logger.error(f"No valid input files found in {self.directory}")
            raise ValueError(f"No valid input files found in {self.directory}")
        
        self.logger.info(f"Found {len(files)} files to process")
        dfs = []
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for file in files:
                self.logger.debug(f"Loading file: {file}")
                if file.suffix == '.csv':
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                dfs.append(df)
        
        self.logger.info("Combining and cleaning data...")
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates
        original_len = len(combined_df)
        combined_df = combined_df.drop_duplicates()
        if original_len > len(combined_df):
            removed = original_len - len(combined_df)
            self.logger.info(f"✓ Removed {removed:,} duplicate rows ({(removed/original_len)*100:.1f}%)")
        
        self.logger.info(f"✓ Final dataset: {len(combined_df):,} records from {len(combined_df['Hostname'].unique()):,} unique hosts")
        
        return combined_df
