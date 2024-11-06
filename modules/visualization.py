import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from typing import Dict
import re
import logging
import pandas as pd
from metrics_calculator import MetricsCalculator  # Update to absolute import if needed

class Visualizer:
    """Creates visualizations for the report."""

    def __init__(self, metrics: Dict, logger: logging.Logger):
        self.metrics = metrics
        self.logger = logger

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
            module_cols = self.metrics['overall']['module_usage'].keys()
            usage_counts = self.metrics['overall']['module_usage'].values()
            
            ax1.bar(module_cols, usage_counts, color=[colors.get(env, 'gray') for env in module_cols])
            ax1.set_title('Security Module Usage Across Environments', pad=20)
            ax1.set_xlabel('Security Modules')
            ax1.set_ylabel('Usage Count')
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
            
            # Save all visualizations without logging again
            for name, fig in visualizations.items():
                img_path = f"{name}.png"
                fig.savefig(img_path, bbox_inches='tight')
                self.logger.debug(f"Saved visualization: {img_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
            raise
        
        return visualizations

    def embed_images_in_html(self, html_content: str) -> str:
        """
        Embed images directly into the HTML content as base64 strings.

        Parameters:
            html_content (str): The HTML content to embed images into.

        Returns:
            str: The HTML content with embedded images.
        """
        for name in ['module_usage', 'environment_distribution']:
            try:
                with open(f"{name}.png", "rb") as image_file:
                    img_str = base64.b64encode(image_file.read()).decode('utf-8')
                img_tag = f'data:image/png;base64,{img_str}'
                html_content = re.sub(
                    rf'<img\s+src=["\']{re.escape(name)}\.png["\']\s+alt=["\'].*?["\']\s*/?>',
                    f'<img src="{img_tag}" alt="{name.replace("_", " ").title()}">',
                    html_content,
                    flags=re.IGNORECASE
                )
                self.logger.debug(f"Embedded image for {name}")
            except FileNotFoundError:
                self.logger.warning(f"Visualization image {name}.png not found.")
        
        return html_content
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from typing import Dict
import re
import logging
import pandas as pd  # Ensure pandas is imported
from metrics_calculator import MetricsCalculator  # Update to absolute import if needed

class Visualizer:
    """Creates visualizations for the report."""

    def __init__(self, metrics: Dict, logger: logging.Logger):
        self.metrics = metrics
        self.logger = logger

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
            module_cols = self.metrics['overall']['module_usage'].keys()
            usage_counts = self.metrics['overall']['module_usage'].values()
            
            ax1.bar(module_cols, usage_counts, color=[colors.get(env, 'gray') for env in module_cols])
            ax1.set_title('Security Module Usage Across Environments', pad=20)
            ax1.set_xlabel('Security Modules')
            ax1.set_ylabel('Usage Count')
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
            
            # Save all visualizations without logging again
            for name, fig in visualizations.items():
                img_path = f"{name}.png"
                fig.savefig(img_path, bbox_inches='tight')
                self.logger.debug(f"Saved visualization: {img_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
            raise
        
        return visualizations

    def embed_images_in_html(self, html_content: str) -> str:
        """
        Embed images directly into the HTML content as base64 strings.

        Parameters:
            html_content (str): The HTML content to embed images into.

        Returns:
            str: The HTML content with embedded images.
        """
        for name in ['module_usage', 'environment_distribution']:
            try:
                with open(f"{name}.png", "rb") as image_file:
                    img_str = base64.b64encode(image_file.read()).decode('utf-8')
                img_tag = f'data:image/png;base64,{img_str}'
                html_content = re.sub(
                    rf'<img\s+src=["\']{re.escape(name)}\.png["\']\s+alt=["\'].*?["\']\s*/?>',
                    f'<img src="{img_tag}" alt="{name.replace("_", " ").title()}">',
                    html_content,
                    flags=re.IGNORECASE
                )
                self.logger.debug(f"Embedded image for {name}")
            except FileNotFoundError:
                self.logger.warning(f"Visualization image {name}.png not found.")
        
        return html_content
