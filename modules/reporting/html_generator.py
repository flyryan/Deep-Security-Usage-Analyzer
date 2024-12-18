"""
HTML report generation functionality for Deep Security Usage Analyzer.
"""
from typing import Dict
from datetime import datetime
from jinja2 import Template

# HTML report template
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Deep Security Usage Analyzer Report</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6;
            color: #333;
        }
        .section { 
            margin-bottom: 30px; 
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1, h2 { 
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0; 
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }
        th { 
            background-color: #f5f5f5; 
            color: #2c3e50;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        .visualization { 
            margin: 20px 0;
            text-align: center;
        }
        .visualization img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .highlight { 
            background-color: #fff3cd; 
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .timestamp {
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>Deep Security Usage Analyzer Report</h1>
    <p class="timestamp">Generated on: {{ timestamp }}</p>
    
    <div class="section">
        <h2>Overall Metrics</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.overall.total_instances | default(0) }}</div>
                <div class="metric-label">Total Unique Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.overall.activated_instances | default(0) }}</div>
                <div class="metric-label">Activated Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.overall.inactive_instances | default(0) }}</div>
                <div class="metric-label">Inactive Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "{:,.1f}".format(metrics.overall.total_hours | default(0.0) | round(1)) }}</div>
                <div class="metric-label">Total Hours</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Environment Distribution</h2>
        <table>
            <tr>
                <th>Environment</th>
                <th>Total Hosts</th>
                <th>Activated Hosts</th>
                <th>Most Used Module</th>
                <th>Max Concurrent</th>
                <th>Total Hours</th>
            </tr>
            {% for env, data in metrics.by_environment.items() %}
            <tr>
                <td>{{ env }}</td>
                <td>{{ data.total_instances }}</td>
                <td>{{ data.activated_instances }}</td>
                <td>{{ data.most_common_module }}</td>
                <td>{{ data.max_concurrent if data.max_concurrent else 'None' }}</td>
                <td>
                    {% if data.total_utilization_hours is defined and data.total_utilization_hours != 'N/A' %}
                        {{ "{:,.1f}".format(data.total_utilization_hours) }}
                    {% else %}
                        N/A
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="section">
        <h2>Module Usage Analysis</h2>
        <div class="visualization">
            <h3>Security Module Usage by Environment</h3>
            <img src="module_usage.png" alt="Module Usage Distribution">
        </div>
        <div class="visualization">
            <h3>Environment Distribution</h3>
            <img src="environment_distribution.png" alt="Environment Distribution">
        </div>
        <div class="visualization">
            <h3>Activated Instances Seen Monthly</h3>
            <img src="activated_instances_growth.png" alt="Growth of Activated Instances">
        </div>
    </div>
    
    <div class="section">
        <h2>Statistics Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Unique Instances</td>
                <td>{{ "{:,}".format(metrics.overall.total_instances) }}</td>
            </tr>
            <tr>
                <td>Instances Running at Least One Module</td>
                <td>{{ "{:,}".format(metrics.overall.activated_instances) }}</td>
            </tr>
            <tr>
                <td>Instances Not Running Any Modules</td>
                <td>{{ "{:,}".format(metrics.overall.inactive_instances) }}</td>
            </tr>
            <tr>
                <td>Total Hours</td>
                <td>{{ "{:,.1f}".format(metrics.overall.total_hours) }}</td>
            </tr>
            <tr>
                <td>Hours for Instances with Modules</td>
                <td>{{ "{:,.1f}".format(metrics.overall.activated_hours) }}</td>
            </tr>
            <tr>
                <td>Hours for Instances without Modules</td>
                <td>{{ "{:,.1f}".format(metrics.overall.inactive_hours) }}</td>
            </tr>
            <tr>
                <td>Average Monthly Growth (Activated Instances)</td>
                <td>{{ "%.1f"|format(metrics.monthly.average_monthly_growth) }} instances</td>
            </tr>
            <tr>
                <td>Unknown Environment Instances</td>
                <td>{{ "{:,}".format(metrics.by_environment.Unknown.total_instances if metrics.by_environment.Unknown else 0) }}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>Monthly Data Analysis</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.monthly.total_months }}</div>
                <div class="metric-label">Total Months with Data</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.monthly.date_range }}</div>
                <div class="metric-label">Date Range</div>
            </div>
        </div>
        
        <table>
            <tr>
                <th>Month</th>
                <th>Activated Instances</th>
                <th>Max Concurrent Instances</th>
                <th>Avg Modules/Host</th>
            </tr>
            {% if metrics.monthly and metrics.monthly.data %}
                {% for month in metrics.monthly.data %}
                <tr>
                    <td>{{ month.month | default('None') }}</td>
                    <td>
                        {{ month.activated_instances | default(0) }}
                    </td>
                    <td>{{ month.max_concurrent | default(0) }}</td>
                    <td>{{ "%.2f"|format(month.avg_modules_per_host | default(0.0)) }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr>
                    <td colspan="5">No monthly data available</td>
                </tr>
            {% endif %}
        </table>
    </div>

    {% if metrics.by_environment.Unknown and metrics.by_environment.Unknown.total_instances > 0 %}
    <div class="section highlight">
        <h2>Unknown Environment Analysis</h2>
        <p>Number of hosts in unknown environment: {{ "{:,}".format(metrics.by_environment.Unknown.total_instances) }}</p>
        <p>Common patterns found in unknown hosts:</p>
        <ul>
        {% for pattern in unknown_patterns %}
            <li>{{ pattern }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

</body>
</html>
"""

def generate_html_report(metrics: Dict) -> str:
    """
    Generate HTML report from metrics data.

    Args:
        metrics (Dict): Dictionary containing all metrics data

    Returns:
        str: Generated HTML report content
    """
    # Create report context
    report_context = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'metrics': metrics,
        'unknown_patterns': []
    }
    
    # Add unknown patterns if they exist
    if 'Unknown' in metrics.get('by_environment', {}):
        report_context['unknown_patterns'] = metrics['by_environment']['Unknown'].get('patterns', [])[:10]
    
    # Render template
    template = Template(REPORT_TEMPLATE)
    return template.render(**report_context)
