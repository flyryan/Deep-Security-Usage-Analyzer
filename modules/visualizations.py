"""
Visualization creation functionality for the Deep Security Usage Analyzer.
"""
from typing import Dict
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_visualizations(metrics: Dict, output_dir: Path) -> Dict[str, plt.Figure]:
    """
    Create visualizations to represent module usage, environment distribution, and growth of activated instances.

    Args:
        metrics (Dict): Dictionary containing all metrics data
        output_dir (Path): Directory to save the visualization files

    Returns:
        Dict[str, plt.Figure]: A dictionary of visualization figures
    """
    visualizations = {}
    
    try:
        # Set Seaborn style
        sns.set_style('darkgrid')
        
        # Define a color palette for consistency
        color_palette = sns.color_palette("Set2")
        
        # 1. Security Module Usage by Environment (Stacked Bar Chart)
        fig1, ax1 = plt.subplots(figsize=(12, 8))
        module_cols = ['AM', 'WRS', 'DC', 'AC', 'IM', 'LI', 'FW', 'DPI', 'SAP']
        env_data = {}
        for env in ['Production', 'Development', 'Test', 'Staging', 'Integration', 'DR', 'UAT']:
            if env in metrics['by_environment']:
                env_data[env] = metrics['by_environment'][env]['module_usage']
        module_usage_df = pd.DataFrame(env_data).fillna(0)
        module_usage_df = module_usage_df[module_usage_df.columns[::-1]]  # Reverse for better stacking
        module_usage_df.plot(kind='bar', stacked=True, ax=ax1, color=color_palette[:len(module_cols)])
        ax1.set_title('Security Module Usage Across Environments', fontsize=16, pad=20)
        ax1.set_xlabel('Security Modules', fontsize=12)
        ax1.set_ylabel('Usage Count', fontsize=12)
        ax1.legend(title='Environment', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        visualizations['module_usage'] = fig1

        # 2. Environment Distribution (Pie Chart)
        fig2, ax2 = plt.subplots(figsize=(8, 8))
        env_counts = pd.Series(metrics['overall']['environment_distribution'])
        if env_counts.sum() > 0:  # Ensure we have data to plot
            colors_env = sns.color_palette("pastel")[0:len(env_counts)]
            wedges, texts, autotexts = ax2.pie(env_counts.values, 
                                              labels=env_counts.index, 
                                              autopct='%1.1f%%',
                                              colors=colors_env, 
                                              startangle=140)
            ax2.set_title('Distribution of Activated Instances by Environment', fontsize=16)
            # Enhance legend readability
            legend_labels = [f'{env}' for env in env_counts.index]
            ax2.legend(wedges, legend_labels,
                      title="Environments",
                      loc="center left",
                      bbox_to_anchor=(1, 0, 0.5, 1))
        else:
            ax2.text(0.5, 0.5, 'No activated instances found',
                     ha='center', va='center')
        plt.tight_layout()
        visualizations['environment_distribution'] = fig2

        # 3. Growth of Activated Instances Over Time (Line Chart)
        if 'monthly' in metrics and 'data' in metrics['monthly']:
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            monthly_data = sorted(metrics['monthly']['data'], key=lambda x: x['month'])
            months = [datetime.strptime(month['month'], '%Y-%m') for month in monthly_data]
            activated_instances = [month['activated_instances'] for month in monthly_data]
            
            # Plot cumulative growth
            sns.lineplot(x=months, y=activated_instances, marker='o', ax=ax3, color='teal')
            
            # Add average monthly growth annotation
            avg_growth = metrics['monthly'].get('average_monthly_growth', 0)
            ax3.text(0.02, 0.98, f'Average Monthly Growth: {avg_growth:.1f} instances',
                    transform=ax3.transAxes, fontsize=10, verticalalignment='top',
                    bbox=dict(facecolor='white', alpha=0.8))
            
            ax3.set_title('Total Activated Instances Seen by Month', fontsize=16, pad=20)
            ax3.set_xlabel('Month', fontsize=12)
            ax3.set_ylabel('Total Activated Instances', fontsize=12)
            ax3.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            visualizations['activated_instances_growth'] = fig3
        else:
            logger.warning("Monthly data not available. Skipping 'activated_instances_growth' visualization.")

        # Save all visualizations
        for name, fig in visualizations.items():
            fig_path = output_dir / f'{name}.png'
            fig.savefig(fig_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
            logger.debug(f"Saved visualization '{name}' to '{fig_path}'")
        
        print(f"✓ Created {len(visualizations)} visualizations:")
        for name in visualizations.keys():
            print(f"  - {name.replace('_', ' ').title()}")
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {str(e)}")
        raise
    
    return visualizations
