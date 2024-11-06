import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

class MetricsCalculator:
    """Calculates core metrics from security module data."""
    
    def __init__(self, data: pd.DataFrame, logger: logging.Logger):
        """
        Initialize the metrics calculator.
        
        Args:
            data (pd.DataFrame): Preprocessed security module data.
            logger (logging.Logger): Logger instance.
        """
        self.data = data
        self.logger = logger
        self.numeric_column = 'usage_time'  # Replace with your actual column
    
    def compute_overall_metric(self) -> float:
        """
        Compute the 'overall' metric.
        
        Returns:
            float: The calculated overall metric.
        """
        try:
            overall_metric = self.data[self.numeric_column].mean()
            self.logger.debug(f"Computed 'overall' metric: {overall_metric}")
            return overall_metric
        except Exception as e:
            self.logger.error(f"Error computing 'overall' metric: {e}")
            return 0.0
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

class MetricsCalculator:
    """Calculates core metrics from security module data."""
    
    def __init__(self, data: pd.DataFrame, logger: logging.Logger):
        """
        Initialize the metrics calculator.
        
        Args:
            data (pd.DataFrame): Preprocessed security module data.
            logger (logging.Logger): Logger instance.
        """
        self.data = data
        self.logger = logger
        self.numeric_column = 'usage_time'  # Replace with your actual column
    
    def compute_overall_metric(self) -> float:
        """
        Compute the 'overall' metric.
        
        Returns:
            float: The calculated overall metric.
        """
        try:
            overall_metric = self.data[self.numeric_column].mean()
            self.logger.debug(f"Computed 'overall' metric: {overall_metric}")
            return overall_metric
        except Exception as e:
            self.logger.error(f"Error computing 'overall' metric: {e}")
            return 0.0
