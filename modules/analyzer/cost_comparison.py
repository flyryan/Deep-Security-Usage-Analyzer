"""
Cost Comparison Analyzer for Deep Security vs Vision One SPC.

This module calculates multi-year cost comparisons accounting for endpoint
growth projections, platform fees, and deployment costs.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple


def load_projections(projections_path: str) -> Dict[str, Any]:
    """Load growth projections from projections.json."""
    with open(projections_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration including pricing data."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_conservative_scenario(projections: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract the conservative (Geometric Decay) scenario data.
    Returns list of {month, activated_instances} dicts.
    """
    # Get conservative scenario from overall projections
    decay_scenario = projections.get('scenarios', {}).get('decay', {})
    if not decay_scenario:
        raise ValueError("Conservative (decay) scenario not found in projections")

    return decay_scenario.get('series', [])


def get_eoy_endpoints(series: List[Dict[str, Any]], year: int) -> int:
    """Get end-of-year endpoint count for a given year."""
    eoy_month = f"{year}-12"
    for entry in series:
        if entry['month'] == eoy_month:
            return int(entry['activated_instances'])

    # If specific month not found, return last entry for that year
    year_str = str(year)
    year_entries = [e for e in series if e['month'].startswith(year_str)]
    if year_entries:
        return int(year_entries[-1]['activated_instances'])

    raise ValueError(f"No endpoint data found for year {year}")


def extrapolate_growth(series: List[Dict[str, Any]], target_year: int) -> int:
    """
    Extrapolate endpoint growth beyond available projection data.
    Uses the decay rate from the last few months of data.
    """
    # Get last available year
    last_entry = series[-1]
    last_year = int(last_entry['month'].split('-')[0])
    last_endpoints = int(last_entry['activated_instances'])

    if target_year <= last_year:
        return get_eoy_endpoints(series, target_year)

    # Calculate average growth rate from last 6 months
    if len(series) >= 6:
        recent_entries = series[-6:]
        start_val = recent_entries[0]['activated_instances']
        end_val = recent_entries[-1]['activated_instances']
        monthly_growth_rate = (end_val / start_val) ** (1/5) - 1  # 5 months of growth
    else:
        # Fallback to conservative 2% monthly growth
        monthly_growth_rate = 0.02

    # Extrapolate year by year
    current_endpoints = last_endpoints
    years_to_extrapolate = target_year - last_year

    for _ in range(years_to_extrapolate):
        # Apply 12 months of growth
        current_endpoints *= (1 + monthly_growth_rate) ** 12

    return int(current_endpoints)


def calculate_yearly_costs(projections: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate annual costs for both platforms across projection horizon.

    Returns comprehensive cost comparison data structure.
    """
    pricing = config['pricing']
    options = pricing['options']

    # Extract pricing details
    ds_per_endpoint = pricing['deep_security']['per_endpoint']
    ds_support = pricing['deep_security']['platinum_support']['amount']
    spc_base = pricing['vision_one_spc']['base_platform']['amount']
    spc_support = pricing['vision_one_spc']['dedicated_support']['amount']
    spc_deployment = pricing['vision_one_spc']['deployment_service']['amount']
    spc_deployment_waived = pricing['vision_one_spc']['deployment_service'].get('waived', False)
    spc_per_endpoint = pricing['vision_one_spc']['per_endpoint']['total']

    # Get conservative scenario data
    conservative_series = extract_conservative_scenario(projections)

    # Determine projection years
    projection_years = options.get('projection_years', 3)
    start_year = 2026  # First renewal year
    years = list(range(start_year, start_year + projection_years))

    # Calculate endpoints for each year (exact numbers for charts)
    endpoints_by_year = []
    endpoints_by_year_rounded = []  # Rounded for cost calculations only
    for year in years:
        try:
            endpoints = get_eoy_endpoints(conservative_series, year)
        except ValueError:
            endpoints = extrapolate_growth(conservative_series, year)
        endpoints_by_year.append(endpoints)
        # Round to nearest thousand for cost calculations
        endpoints_rounded = round(endpoints / 1000) * 1000
        endpoints_by_year_rounded.append(endpoints_rounded)

    # Calculate costs
    ds_costs = []
    spc_costs = []
    spc_base_costs = []
    spc_support_costs = []
    spc_deployment_costs = []
    spc_endpoint_costs = []
    spc_effective_per_endpoint = []

    # Use rounded numbers for cost calculations
    for i, (year, endpoints_exact, endpoints_rounded) in enumerate(zip(years, endpoints_by_year, endpoints_by_year_rounded)):
        # Deep Security cost (using rounded numbers) - includes Platinum Support
        ds_cost = (endpoints_rounded * ds_per_endpoint) + ds_support
        ds_costs.append(ds_cost)

        # Vision One SPC cost (using rounded numbers)
        base_cost = spc_base
        support_cost = spc_support  # Annual recurring
        deployment_cost = 0 if spc_deployment_waived else (spc_deployment if i == 0 else 0)  # Only Year 1, unless waived
        endpoint_cost = endpoints_rounded * spc_per_endpoint
        spc_total = base_cost + support_cost + deployment_cost + endpoint_cost

        spc_costs.append(spc_total)
        spc_base_costs.append(base_cost)
        spc_support_costs.append(support_cost)
        spc_deployment_costs.append(deployment_cost)
        spc_endpoint_costs.append(endpoint_cost)
        spc_effective_per_endpoint.append(spc_total / endpoints_rounded)

    # Calculate savings
    annual_savings = [ds - spc for ds, spc in zip(ds_costs, spc_costs)]
    cumulative_savings = []
    cumsum = 0
    for saving in annual_savings:
        cumsum += saving
        cumulative_savings.append(cumsum)

    return {
        "years": years,
        "endpoints": endpoints_by_year,  # Exact numbers for charts
        "endpoints_rounded": endpoints_by_year_rounded,  # Rounded numbers for cost tables
        "deep_security": {
            "annual_costs": ds_costs,
            "platinum_support": [ds_support] * len(years),
            "per_endpoint": [ds_per_endpoint] * len(years)
        },
        "vision_one_spc": {
            "annual_costs": spc_costs,
            "base_platform": spc_base_costs,
            "dedicated_support": spc_support_costs,
            "deployment_service": spc_deployment_costs,
            "endpoint_costs": spc_endpoint_costs,
            "per_endpoint_effective": spc_effective_per_endpoint,
            "per_endpoint_base": [spc_per_endpoint] * len(years)
        },
        "savings": {
            "annual": annual_savings,
            "cumulative": cumulative_savings
        }
    }


def calculate_scenario_analysis(projections: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate Year 1 costs under different growth scenarios.
    Shows how greater growth increases SPC value.
    """
    pricing = config['pricing']

    ds_per_endpoint = pricing['deep_security']['per_endpoint']
    ds_support = pricing['deep_security']['platinum_support']['amount']
    spc_base = pricing['vision_one_spc']['base_platform']['amount']
    spc_support = pricing['vision_one_spc']['dedicated_support']['amount']
    spc_deployment = pricing['vision_one_spc']['deployment_service']['amount']
    spc_deployment_waived = pricing['vision_one_spc']['deployment_service'].get('waived', False)
    spc_per_endpoint = pricing['vision_one_spc']['per_endpoint']['total']

    scenarios = {}
    scenario_names = {
        'decay': 'Conservative (Geometric Decay)',
        'linear': 'Linear Trend',
        'avg_last3': 'Rolling Avg Last 3 Months'
    }

    for scenario_key, scenario_name in scenario_names.items():
        scenario_data = projections.get('scenarios', {}).get(scenario_key, {})
        if not scenario_data:
            continue

        # Get 2026 EOY projection
        eoy_2026 = scenario_data.get('EOY_2026')
        if not eoy_2026:
            continue

        endpoints = int(eoy_2026)

        # Calculate costs - includes support for both platforms
        ds_cost = (endpoints * ds_per_endpoint) + ds_support
        spc_cost = spc_base + spc_support + (0 if spc_deployment_waived else spc_deployment) + (endpoints * spc_per_endpoint)
        savings = ds_cost - spc_cost

        scenarios[scenario_key] = {
            "name": scenario_name,
            "endpoints": endpoints,
            "deep_security_cost": ds_cost,
            "vision_one_spc_cost": spc_cost,
            "savings": savings,
            "spc_effective_per_endpoint": spc_cost / endpoints
        }

    return scenarios


def calculate_monthly_projections(projections: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculate month-by-month cost comparison for 2026.
    Shows progression throughout first year.
    """
    pricing = config['pricing']

    ds_per_endpoint = pricing['deep_security']['per_endpoint']
    ds_support = pricing['deep_security']['platinum_support']['amount']
    spc_base = pricing['vision_one_spc']['base_platform']['amount']
    spc_support = pricing['vision_one_spc']['dedicated_support']['amount']
    spc_deployment = pricing['vision_one_spc']['deployment_service']['amount']
    spc_deployment_waived = pricing['vision_one_spc']['deployment_service'].get('waived', False)
    spc_per_endpoint = pricing['vision_one_spc']['per_endpoint']['total']

    # Get conservative scenario monthly data
    conservative_series = extract_conservative_scenario(projections)

    # Filter to 2026 only
    monthly_data = []
    for entry in conservative_series:
        month = entry['month']
        if not month.startswith('2026'):
            continue

        endpoints = int(entry['activated_instances'])

        # Calculate costs - includes support for both platforms
        ds_cost = (endpoints * ds_per_endpoint) + ds_support

        # SPC cost includes base, support, and deployment (if not waived) for all months in Year 1
        # (they're annual/one-time, but we show them in the calculation)
        spc_cost = spc_base + spc_support + (0 if spc_deployment_waived else spc_deployment) + (endpoints * spc_per_endpoint)

        savings = ds_cost - spc_cost

        monthly_data.append({
            "month": month,
            "endpoints": endpoints,
            "deep_security_cost": ds_cost,
            "vision_one_spc_cost": spc_cost,
            "savings": savings
        })

    return monthly_data


def generate_cost_comparison_data(projections_path: str, config_path: str) -> Dict[str, Any]:
    """
    Main entry point - orchestrates all cost comparison calculations.

    Args:
        projections_path: Path to projections.json
        config_path: Path to config.json

    Returns:
        Comprehensive cost comparison data structure
    """
    # Load data
    projections = load_projections(projections_path)
    config = load_config(config_path)

    # Calculate various analyses
    yearly_costs = calculate_yearly_costs(projections, config)
    scenario_analysis = calculate_scenario_analysis(projections, config)
    monthly_projections = calculate_monthly_projections(projections, config)

    # Get baseline 2025 data and pricing
    customer_context = config.get('customer_context', {})
    baseline_2025 = customer_context.get('baseline_2025', {})
    pricing = config['pricing']

    # Calculate baseline_2025 values dynamically based on DS endpoint price
    licensed_endpoints = baseline_2025.get('licensed_endpoints', 0)
    eoy_endpoints = baseline_2025.get('eoy_endpoints', 0)
    ds_per_endpoint = pricing['deep_security']['per_endpoint']
    ds_support = pricing['deep_security']['platinum_support']['amount']

    # Annual cost for licensed endpoints
    annual_cost = (licensed_endpoints * ds_per_endpoint) + ds_support

    # Partnership value = overage × per-endpoint price
    overage_endpoints = eoy_endpoints - licensed_endpoints
    partnership_value = overage_endpoints * ds_per_endpoint

    # Update baseline_2025 with calculated values
    baseline_2025 = dict(baseline_2025)  # Make a copy to avoid modifying config
    baseline_2025['annual_cost'] = annual_cost
    baseline_2025['partnership_value'] = partnership_value

    # Calculate proposal costs (for 41,000 endpoints)
    proposal = config.get('proposal', {})
    proposal_endpoints = proposal.get('endpoints', 41000)

    proposal_costs = {
        "endpoints": proposal_endpoints,
        "description": proposal.get('description', 'Proposed licensing'),
        "deep_security": {
            "annual_cost": (proposal_endpoints * pricing['deep_security']['per_endpoint']) + pricing['deep_security']['platinum_support']['amount'],
            "platinum_support": pricing['deep_security']['platinum_support']['amount'],
            "per_endpoint": pricing['deep_security']['per_endpoint']
        },
        "vision_one_spc": {
            "year_1_cost": (pricing['vision_one_spc']['base_platform']['amount'] +
                           pricing['vision_one_spc']['dedicated_support']['amount'] +
                           (0 if pricing['vision_one_spc']['deployment_service'].get('waived', False) else pricing['vision_one_spc']['deployment_service']['amount']) +
                           proposal_endpoints * pricing['vision_one_spc']['per_endpoint']['total']),
            "year_2plus_cost": (pricing['vision_one_spc']['base_platform']['amount'] +
                               pricing['vision_one_spc']['dedicated_support']['amount'] +
                               proposal_endpoints * pricing['vision_one_spc']['per_endpoint']['total']),
            "per_endpoint_effective_y1": None,  # Will be calculated
            "per_endpoint_effective_y2plus": None  # Will be calculated
        }
    }

    # Calculate effective per-endpoint costs for proposal
    proposal_costs['vision_one_spc']['per_endpoint_effective_y1'] = (
        proposal_costs['vision_one_spc']['year_1_cost'] / proposal_endpoints
    )
    proposal_costs['vision_one_spc']['per_endpoint_effective_y2plus'] = (
        proposal_costs['vision_one_spc']['year_2plus_cost'] / proposal_endpoints
    )

    # Calculate savings for proposal
    proposal_costs['savings'] = {
        "year_1": proposal_costs['deep_security']['annual_cost'] - proposal_costs['vision_one_spc']['year_1_cost'],
        "year_2plus": proposal_costs['deep_security']['annual_cost'] - proposal_costs['vision_one_spc']['year_2plus_cost']
    }

    # Compile comprehensive result
    result = {
        "metadata": {
            "generated_date": None,  # Will be set by report generator
            "customer_name": customer_context.get('name', 'Federal Customer'),
            "customer_type": customer_context.get('type', 'unknown'),
            "projection_basis": "Conservative (Geometric Decay)",
            "proposal_note": "Licensing proposal based on 41,000 endpoints (conservative projection rounded up)"
        },
        "baseline_2025": baseline_2025,
        "proposal": proposal_costs,
        "pricing": config['pricing'],
        "yearly_comparison": yearly_costs,
        "scenario_analysis": scenario_analysis,
        "monthly_projections_2026": monthly_projections
    }

    return result
