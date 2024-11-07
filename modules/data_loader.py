import os
import pandas as pd
import logging

class DataLoader:
    def __init__(self, directory: str, logger: logging.Logger):
        self.directory = directory
        self.logger = logger
        self.VALID_EXTENSIONS = ['.csv', '.xlsx', '.xls']

    def load_data(self) -> pd.DataFrame:
        self.logger.info("Loading data from directory: %s", self.directory)
        data_frames = []
        for file in os.listdir(self.directory):
            if any(file.endswith(ext) for ext in self.VALID_EXTENSIONS):
                file_path = os.path.join(self.directory, file)
                self.logger.debug("Loading file: %s", file_path)
                try:
                    if file.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)
                    if 'status' not in df.columns:
                        self.logger.warning("'status' column not found. Adding default 'status' with value 'active'.")
                        df['status'] = 'active'
                    data_frames.append(df)
                    self.logger.info("Loaded file: %s", file)
                except Exception as e:
                    self.logger.error("Failed to load file %s: %s", file, e)
        if not data_frames:
            self.logger.error("No valid input files found in directory: %s", self.directory)
            raise ValueError("No valid input files found.")
        combined_data = pd.concat(data_frames, ignore_index=True)
        self.logger.info("Data loaded successfully. Total records: %d", len(combined_data))
        return combined_data
