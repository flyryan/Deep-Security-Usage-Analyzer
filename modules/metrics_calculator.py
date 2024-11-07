import pandas as pd
import logging
from typing import Dict

class MetricsCalculator:
    def __init__(self, data: pd.DataFrame, logger: logging.Logger):
        self.data = data
        self.logger = logger

    def compute_overall_metric(self) -> Dict:
        required_columns = ['status', 'hours', 'concurrent']
        for column in required_columns:
            if column not in self.data.columns:
                self.logger.error(f"Missing required column: {column}")
                return {}
        
        self.logger.info("Computing overall metrics")
        overall_metric = {
            "total_instances": len(self.data),
            "active_instances": self.data[self.data['status'] == 'active'].shape[0],
            "inactive_instances": self.data[self.data['status'] == 'inactive'].shape[0],
            "total_hours": self.data['hours'].sum(),
            "active_hours": self.data[self.data['status'] == 'active']['hours'].sum(),
            "inactive_hours": self.data[self.data['status'] == 'inactive']['hours'].sum(),
            "max_concurrent_overall": self.data['concurrent'].max()
        }
        return overall_metric
