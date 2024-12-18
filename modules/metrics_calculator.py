"""
Metrics calculation functionality for the Deep Security Usage Analyzer.
"""
import pandas as pd
import logging
from typing import Dict, Set
from .concurrent_calculator import calculate_concurrent_usage
from .utils import MODULE_COLUMNS

logger = logging.getLogger(__name__)

def calculate_overall_metrics(data: pd.DataFrame) -> Dict:
    """Calculate overall metrics from the data."""
    # Add has_modules column to the dataframe
    data['has_modules'] = data[MODULE_COLUMNS].sum(axis=1) > 0
    
    # Calculate activated instances
    activated_hosts = set(data[data['has_modules']]['Hostname'].unique())
    total_hosts = set(data['Hostname'].unique())
    
    # Calculate overall metrics
    metrics = {
        'total_instances': len(total_hosts),
        'activated_instances': len(activated_hosts),
        'inactive_instances': len(total_hosts - activated_hosts),
        'total_hours': data['Duration (Seconds)'].sum() / 3600 if 'Duration (Seconds)' in data.columns else 0,
        'activated_hours': data[data['has_modules']]['Duration (Seconds)'].sum() / 3600 if 'Duration (Seconds)' in data.columns else 0,
    }
    metrics['inactive_hours'] = metrics['total_hours'] - metrics['activated_hours']
    
    # Calculate correlation matrix
    correlation_matrix = data[MODULE_COLUMNS].corr()
    metrics['correlation_matrix'] = correlation_matrix.to_dict()
    
    # Calculate module usage
    metrics['module_usage'] = {
        col: int(data[col].sum()) for col in MODULE_COLUMNS
    }
    
    return metrics

def calculate_environment_metrics(data: pd.DataFrame, env: str) -> Dict:
    """Calculate metrics for a specific environment."""
    env_data = data[data['Environment'] == env]
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
    max_concurrent = calculate_concurrent_usage(env_data)
    
    # Calculate total utilization hours
    total_hours = (env_data['Duration (Seconds)'].sum() / 3600) if 'Duration (Seconds)' in env_data.columns else 0
    
    return {
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

def calculate_monthly_metrics(data: pd.DataFrame, start_date: pd.Timestamp = None, end_date: pd.Timestamp = None) -> Dict:
    """Calculate monthly metrics including cumulative growth."""
    monthly_metrics = {
        'data': [],
        'data_gaps': [],
        'total_months': 0,
        'date_range': '',
        'average_monthly_growth': 0
    }
    
    try:
        # Get all activated instances
        activated_mask = data[MODULE_COLUMNS].sum(axis=1) > 0
        activated_instances = set(data[activated_mask]['Hostname'].unique())
        
        # Get date range
        min_date = data['start_datetime'].min()
        max_date = data['start_datetime'].max()
        monthly_metrics['date_range'] = f"{min_date.strftime('%Y-%m')} to {max_date.strftime('%Y-%m')}"
        
        # Generate all months
        all_months = pd.date_range(
            start=min_date.replace(day=1),
            end=max_date.replace(day=1),
            freq='MS'
        )
        
        monthly_data = []
        cumulative_instances = set()
        previous_month_count = 0
        total_growth = 0
        growth_months = 0
        
        for month_start in all_months:
            month_end = month_start + pd.offsets.MonthEnd(1)
            
            # Get all records for this month
            month_mask = (
                (data['start_datetime'] <= month_end) & 
                (data['stop_datetime'] >= month_start)
            )
            month_data = data[month_mask].copy()
            
            if not month_data.empty:
                # Get activated instances for this month
                activated_month_data = month_data[month_data[MODULE_COLUMNS].sum(axis=1) > 0]
                activated_instances_current = set(activated_month_data['Hostname'].unique())

                # Calculate duration per instance without double counting
                duration_per_instance = activated_month_data.groupby('Hostname')['Duration (Seconds)'].sum()
                total_hours = duration_per_instance.sum() / 3600

                # Calculate average modules per host
                avg_modules_per_host = activated_month_data[MODULE_COLUMNS].sum(axis=1).mean() if not activated_month_data.empty else 0.0

                # Max concurrent instances in the month
                max_concurrent = calculate_concurrent_usage(activated_month_data)

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

def calculate_all_metrics(data: pd.DataFrame) -> Dict:
    """Calculate all metrics from the loaded data."""
    if data is None:
        raise ValueError("No data loaded for analysis")
    
    logger.info("Calculating comprehensive metrics...")
    
    # Add has_modules column to the dataframe
    data['has_modules'] = data[MODULE_COLUMNS].sum(axis=1) > 0
    
    # Initialize metrics dictionary
    metrics = {
        'by_environment': {},
        'overall': {},
        'trends': {},
        'overall_metrics': {}
    }
    
    # Calculate overall metrics
    metrics['overall'] = calculate_overall_metrics(data)
    
    # Calculate environment metrics
    environments = sorted(data['Environment'].unique())
    for env in environments:
        metrics['by_environment'][env] = calculate_environment_metrics(data, env)
    
    # Calculate environment distribution
    metrics['overall']['environment_distribution'] = {
        env: data['activated_instances']
        for env, data in metrics['by_environment'].items()
        if data['activated_instances'] > 0
    }
    
    # Calculate overall max concurrent
    logger.info("Calculating overall max concurrent usage...")
    overall_max_concurrent = calculate_concurrent_usage(data)
    
    metrics['overall_metrics'] = {
        'max_concurrent_overall': overall_max_concurrent,
        'total_unique_instances': len(set(data['Hostname'].unique())),
        'total_activated_instances': len(set(data[data['has_modules']]['Hostname'].unique())),
        'total_inactive_instances': len(set(data['Hostname'].unique()) - set(data[data['has_modules']]['Hostname'].unique()))
    }
    
    # Calculate monthly metrics
    metrics['monthly'] = calculate_monthly_metrics(data)
    
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
