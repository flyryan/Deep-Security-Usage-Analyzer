"""
Metrics calculation functionality for the Deep Security Usage Analyzer.
"""
import pandas as pd
import logging
from typing import Dict, Set
import json
import os

from ..utils import MODULE_COLUMNS
from .concurrent_calculator import calculate_concurrent_usage

logger = logging.getLogger(__name__)

# Load activation_min_hours from config.json
def _load_activation_min_hours():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return float(config.get("activation_min_hours", 24))
    except Exception as e:
        logger.warning(f"Could not load activation_min_hours from config.json: {e}")
        return 24.0

ACTIVATION_MIN_HOURS = _load_activation_min_hours()
ACTIVATION_MIN_SECONDS = ACTIVATION_MIN_HOURS * 3600

def calculate_overall_metrics(data: pd.DataFrame) -> Dict:
    """Calculate overall metrics from the data."""
    if data.empty:
        logger.warning("Input DataFrame is empty in calculate_overall_metrics. Returning zeros/defaults.")
        return {
            'total_instances': 0,
            'activated_instances': 0,
            'inactive_instances': 0,
            'total_hours': 0,
            'activated_hours': 0,
            'inactive_hours': 0,
            'correlation_matrix': {},
            'module_usage': {col: 0 for col in MODULE_COLUMNS}
        }
    # 'has_modules' is now always present from preprocessing
    total_hosts = set(data['Hostname'].unique())
    # New logic: Only count as activated if cumulative duration with has_modules is True >= threshold
    if 'Duration (Seconds)' in data.columns:
        module_time = data[data['has_modules']].groupby('Hostname')['Duration (Seconds)'].sum()
        activated_hosts = set(module_time[module_time >= ACTIVATION_MIN_SECONDS].index)
    else:
        activated_hosts = set()
    inactive_hosts = total_hosts - activated_hosts

    metrics = {
        'total_instances': len(total_hosts),
        'activated_instances': len(activated_hosts),
        'inactive_instances': len(inactive_hosts),
        'total_hours': data['Duration (Seconds)'].sum() / 3600 if 'Duration (Seconds)' in data.columns else 0,
        'activated_hours': data[data['has_modules']]['Duration (Seconds)'].sum() / 3600 if 'Duration (Seconds)' in data.columns else 0,
    }
    metrics['inactive_hours'] = metrics['total_hours'] - metrics['activated_hours']

    # Calculate correlation matrix
    if not data[MODULE_COLUMNS].empty:
        correlation_matrix = data[MODULE_COLUMNS].corr()
        metrics['correlation_matrix'] = correlation_matrix.to_dict()
    else:
        metrics['correlation_matrix'] = {}

    # Calculate module usage
    metrics['module_usage'] = {
        col: int(data[col].sum()) for col in MODULE_COLUMNS
    }

    return metrics

def calculate_environment_metrics(data: pd.DataFrame, env: str) -> Dict:
    """Calculate metrics for a specific environment."""
    env_data = data[data['Environment'] == env]
    if env_data.empty:
        logger.warning(f"No data for environment '{env}' in calculate_environment_metrics. Returning zeros/defaults.")
        return {
            'total_instances': 0,
            'activated_instances': 0,
            'inactive_instances': 0,
            'module_usage': {col: 0 for col in MODULE_COLUMNS},
            'module_usage_percentage': {col: 0.0 for col in MODULE_COLUMNS},
            'most_common_module': "None",
            'avg_modules_per_host': 0.0,
            'max_concurrent': 0,
            'total_utilization_hours': 0,
            'correlation_matrix': {}
        }
    env_total_hosts = set(env_data['Hostname'].unique())
    # New logic: Only count as activated if cumulative duration with has_modules is True >= threshold
    if 'Duration (Seconds)' in env_data.columns:
        module_time = env_data[env_data['has_modules']].groupby('Hostname')['Duration (Seconds)'].sum()
        env_activated_hosts = set(module_time[module_time >= ACTIVATION_MIN_SECONDS].index)
    else:
        env_activated_hosts = set()
    inactive_hosts = env_total_hosts - env_activated_hosts

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

    # Calculate average modules per host
    avg_modules_per_host = env_data[MODULE_COLUMNS].sum(axis=1).mean() if not env_data.empty else 0.0

    # Calculate correlation matrix
    if not env_data[MODULE_COLUMNS].empty:
        correlation_matrix = env_data[MODULE_COLUMNS].corr().to_dict()
    else:
        correlation_matrix = {}

    return {
        'total_instances': len(env_total_hosts),
        'activated_instances': len(env_activated_hosts),
        'inactive_instances': len(inactive_hosts),
        'module_usage': {col: len(module_usage_counts[col]) for col in MODULE_COLUMNS},
        'module_usage_percentage': module_usage_percentage,
        'most_common_module': max(
            MODULE_COLUMNS,
            key=lambda col: len(module_usage_counts[col])
        ) if sum(len(instances) for instances in module_usage_counts.values()) > 0 else "None",
        'avg_modules_per_host': avg_modules_per_host,
        'max_concurrent': max_concurrent,
        'total_utilization_hours': total_hours,
        'correlation_matrix': correlation_matrix
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
    if data.empty or 'start_datetime' not in data.columns or 'stop_datetime' not in data.columns:
        logger.warning("Input DataFrame is empty or missing date columns in calculate_monthly_metrics. Returning defaults.")
        return monthly_metrics

    try:
        # Get all activated instances
        activated_mask = data[MODULE_COLUMNS].sum(axis=1) > 0
        activated_instances = set(data[activated_mask]['Hostname'].unique())

        # Get date range
        min_date = data['start_datetime'].min()
        max_date = data['start_datetime'].max()
        if pd.isnull(min_date) or pd.isnull(max_date):
            monthly_metrics['date_range'] = ''
            return monthly_metrics
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
                # Get activated instances for this month (using activation threshold)
                activated_month_data = month_data[month_data[MODULE_COLUMNS].sum(axis=1) > 0]
                if 'Duration (Seconds)' in activated_month_data.columns:
                    duration_per_instance = activated_month_data.groupby('Hostname')['Duration (Seconds)'].sum()
                    activated_instances_current = set(duration_per_instance[duration_per_instance >= ACTIVATION_MIN_SECONDS].index)
                else:
                    activated_instances_current = set()
                    duration_per_instance = pd.Series(dtype=float)
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
                    'activated_instances': len(cumulative_instances),  # cumulative total up to this month
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


    print(f"[DEBUG] Entering calculate_all_metrics with ACTIVATION_MIN_HOURS={ACTIVATION_MIN_HOURS}")

def assign_final_service_categories(data: pd.DataFrame) -> pd.DataFrame:
    """
    Assign final service category to each instance based on most recent record.
    This prevents double-counting instances that appear in multiple categories.
    """
    # Create a copy to avoid modifying the original
    data_copy = data.copy()
    
    # Find the most recent record for each hostname
    most_recent_idx = data_copy.groupby('Hostname')['stop_datetime'].idxmax()
    most_recent_records = data_copy.loc[most_recent_idx, ['Hostname', 'service_category']]
    
    # Create a mapping of hostname to its final service category
    hostname_to_category = dict(zip(most_recent_records['Hostname'], most_recent_records['service_category']))
    
    # Apply the final category to all records for each hostname
    data_copy['final_service_category'] = data_copy['Hostname'].map(hostname_to_category)
    
    # Log the impact
    changed_count = (data_copy['service_category'] != data_copy['final_service_category']).sum()
    if changed_count > 0:
        logger.info(f"Updated service category for {changed_count} records based on most recent classification")
    
    return data_copy

def calculate_all_metrics(data: pd.DataFrame) -> Dict:
    """Calculate all metrics from the loaded data, split by service_category and cloud_provider."""
    if data is None or data.empty:
        raise ValueError("No data loaded for analysis or DataFrame is empty.")

    logger.info("Calculating comprehensive metrics...")

    # Assign final service categories based on most recent record
    data = assign_final_service_categories(data)

    # 'has_modules', 'service_category', and 'Cloud_Provider' are now always present from preprocessing

    # Initialize metrics dictionary
    metrics = {
        'by_environment': {},
        'by_cloud_provider': {},
        'by_cloud_and_environment': {},
        'by_service_category_and_cloud_provider': {},
        'by_service_category_and_cloud_and_env': {},
        'overall': {},
        'trends': {},
        'overall_metrics': {},
        'by_service_category': {}
    }

    # Calculate overall metrics

    print(f"[DEBUG] Calculated overall metrics")

    metrics['overall'] = calculate_overall_metrics(data)

    # Calculate environment metrics
    environments = sorted(data['Environment'].unique())
    for env in environments:
        env_data = data[data['Environment'] == env]
        env_metrics = calculate_environment_metrics(data, env)
        # Add monthly metrics for this environment
        env_metrics['monthly'] = calculate_monthly_metrics(env_data)
        metrics['by_environment'][env] = env_metrics

    print(f"[DEBUG] Calculated environment metrics")

    # Calculate cloud provider metrics
    cloud_providers = sorted(data['Cloud_Provider'].unique())
    for cp in cloud_providers:
        cp_data = data[data['Cloud_Provider'] == cp]
        cp_metrics = calculate_overall_metrics(cp_data)
        # Add monthly metrics for this cloud provider
        cp_metrics['monthly'] = calculate_monthly_metrics(cp_data)
        metrics['by_cloud_provider'][cp] = cp_metrics

    print(f"[DEBUG] Calculated cloud provider metrics")

    # Calculate cloud+environment metrics
    for cp in cloud_providers:
        cp_data = data[data['Cloud_Provider'] == cp]
        cp_envs = sorted(cp_data['Environment'].unique())
        for env in cp_envs:
            key = f"{cp}::{env}"
            env_data = cp_data[cp_data['Environment'] == env]
            ce_metrics = calculate_overall_metrics(env_data)
            # Add monthly metrics for this cloud+environment combination
            ce_metrics['monthly'] = calculate_monthly_metrics(env_data)
            metrics['by_cloud_and_environment'][key] = ce_metrics

    print(f"[DEBUG] Calculated cloud+environment metrics")

    # Calculate environment distribution
    metrics['overall']['environment_distribution'] = {
        env: env_data['activated_instances']
        for env, env_data in metrics['by_environment'].items()
        if env_data['activated_instances'] > 0
    }

    # Calculate cloud provider distribution
    metrics['overall']['cloud_provider_distribution'] = {
        cp: cp_data['activated_instances']
        for cp, cp_data in metrics['by_cloud_provider'].items()
        if cp_data['activated_instances'] > 0
    }

    print(f"[DEBUG] Calculated environment and cloud provider distributions")


    # Calculate overall max concurrent
    logger.info("Calculating overall max concurrent usage...")

    print(f"[DEBUG] Calculated overall max concurrent")

    overall_max_concurrent = calculate_concurrent_usage(data)

    # Cache sets for unique/activated/inactive instances
    all_hostnames = set(data['Hostname'].unique())
    activated_hostnames = set(data[data['has_modules']]['Hostname'].unique())
    inactive_hostnames = all_hostnames - activated_hostnames

    print(f"[DEBUG] Calculated overall_metrics")


    metrics['overall_metrics'] = {
        'max_concurrent_overall': overall_max_concurrent,
        'total_unique_instances': len(all_hostnames),
        'total_activated_instances': len(activated_hostnames),
        'total_inactive_instances': len(inactive_hostnames)
    }

    # Calculate monthly metrics

    print(f"[DEBUG] Calculated monthly metrics")

    metrics['monthly'] = calculate_monthly_metrics(data)

    # --- Split by service_category ---
    service_categories = ["common services", "mission partners"]
    for category in service_categories:
        cat_data = data[data['final_service_category'] == category]
        cat_metrics = {
            'overall': calculate_overall_metrics(cat_data),
            'by_environment': {},
            'monthly': calculate_monthly_metrics(cat_data),
            'overall_metrics': {}
        }
        # Environment metrics for this category
        cat_envs = sorted(cat_data['Environment'].unique())
        for env in cat_envs:
            cat_metrics['by_environment'][env] = calculate_environment_metrics(cat_data, env)
        # Environment distribution
        cat_metrics['overall']['environment_distribution'] = {
            env: env_data['activated_instances']
            for env, env_data in cat_metrics['by_environment'].items()
            if env_data['activated_instances'] > 0
        }
        # Max concurrent and instance sets
        cat_max_concurrent = calculate_concurrent_usage(cat_data)
        cat_all_hostnames = set(cat_data['Hostname'].unique())
        cat_activated_hostnames = set(cat_data[cat_data['has_modules']]['Hostname'].unique())
        cat_inactive_hostnames = cat_all_hostnames - cat_activated_hostnames
        cat_metrics['overall_metrics'] = {
            'max_concurrent_overall': cat_max_concurrent,
            'total_unique_instances': len(cat_all_hostnames),
            'total_activated_instances': len(cat_activated_hostnames),
            'total_inactive_instances': len(cat_inactive_hostnames)
        }
        metrics['by_service_category'][category] = cat_metrics

        # --- Service category splits by cloud provider and by cloud+env ---
        for cp in cloud_providers:
            cat_cp_data = data[(data['final_service_category'] == category) & (data['Cloud_Provider'] == cp)]
            key_cp = f"{category}::{cp}"
            scp_metrics = calculate_overall_metrics(cat_cp_data)
            # Add monthly metrics for service category + cloud provider
            scp_metrics['monthly'] = calculate_monthly_metrics(cat_cp_data)
            metrics['by_service_category_and_cloud_provider'][key_cp] = scp_metrics
            
            cp_envs = sorted(cat_cp_data['Environment'].unique())
            for env in cp_envs:
                key_cpe = f"{category}::{cp}::{env}"
                cat_cp_env_data = cat_cp_data[cat_cp_data['Environment'] == env]
                scpe_metrics = calculate_overall_metrics(cat_cp_env_data)
                # Add monthly metrics for service category + cloud provider + environment
                scpe_metrics['monthly'] = calculate_monthly_metrics(cat_cp_env_data)
                metrics['by_service_category_and_cloud_and_env'][key_cpe] = scpe_metrics

    print(f"[DEBUG] Calculated service_category metrics")


    # Validate metrics
    try:
        if metrics['overall']['total_instances'] != metrics['overall']['activated_instances'] + metrics['overall']['inactive_instances']:
            raise ValueError("Total instances does not equal sum of activated and inactive instances")
        if metrics['overall']['total_hours'] < metrics['overall']['activated_hours']:
            raise ValueError("Total hours should be greater than or equal to activated hours")
        for key, value in metrics['overall'].items():
            if isinstance(value, (int, float)) and value < 0:
                raise ValueError(f"Negative value found in {key}: {value}")
        logger.info("Metrics validation passed")


    except Exception as e:
        logger.error(f"Metrics validation failed: {str(e)}")
        print(f"[DEBUG] Metrics validation failed: {str(e)}")
        # Do not raise, just return metrics as-is
    return metrics





def calculate_metrics_for_thresholds(data: pd.DataFrame, thresholds: list) -> dict:
    """
    Calculate metrics for multiple activation thresholds.
    Args:
        data (pd.DataFrame): The input data
        thresholds (list): List of thresholds in hours
    Returns:
        dict: {threshold: metrics_dict}
    """
    results = {}
    for th in thresholds:
        global ACTIVATION_MIN_HOURS, ACTIVATION_MIN_SECONDS
        ACTIVATION_MIN_HOURS = th
        ACTIVATION_MIN_SECONDS = th * 3600
        try:

            metrics = calculate_all_metrics(data)
            print(f"[DEBUG] Metrics for threshold {th}: type={type(metrics)}, keys={list(metrics.keys()) if isinstance(metrics, dict) else 'N/A'}")
            results[str(int(th))] = metrics
        except Exception as e:
            import traceback
            print(f"Error calculating metrics for threshold {th} hours: {e}", flush=True)
            traceback.print_exc()
            results[str(int(th))] = None
    return results

    return metrics
