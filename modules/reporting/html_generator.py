import os

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
        <h2>Common Services Metrics</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.by_service_category['common services'].overall.total_instances | default(0) }}</div>
                <div class="metric-label">Total Unique Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.by_service_category['common services'].overall.activated_instances | default(0) }}</div>
                <div class="metric-label">Activated Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.by_service_category['common services'].overall.inactive_instances | default(0) }}</div>
                <div class="metric-label">Inactive Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "{:,.1f}".format(metrics.by_service_category['common services'].overall.total_hours | default(0.0) | round(1)) }}</div>
                <div class="metric-label">Total Hours</div>
            </div>
        </div>
    </div>
    <div class="section">
        <h2>Mission Partners Metrics</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.by_service_category['mission partners'].overall.total_instances | default(0) }}</div>
                <div class="metric-label">Total Unique Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.by_service_category['mission partners'].overall.activated_instances | default(0) }}</div>
                <div class="metric-label">Activated Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.by_service_category['mission partners'].overall.inactive_instances | default(0) }}</div>
                <div class="metric-label">Inactive Instances</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "{:,.1f}".format(metrics.by_service_category['mission partners'].overall.total_hours | default(0.0) | round(1)) }}</div>
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
    <div class="visualization">
        <h3>Activated Instances Comparison: Common Services vs. Mission Partners</h3>
        <img src="service_category_comparison.png" alt="Service Category Comparison">
    </div>

    <div class="section">
        <h2>Module Usage Analysis: Common Services</h2>
        <div class="visualization">
            <h3>Security Module Usage by Environment (Common Services)</h3>
            <img src="module_usage_common_services.png" alt="Module Usage Common Services">
        </div>
        <div class="visualization">
            <h3>Environment Distribution (Common Services)</h3>
            <img src="environment_distribution_common_services.png" alt="Environment Distribution Common Services">
        </div>
        <div class="visualization">
            <h3>Activated Instances Seen Monthly (Common Services)</h3>
            <img src="activated_instances_growth_common_services.png" alt="Growth of Activated Instances Common Services">
        </div>
    </div>

    <div class="section">
        <h2>Module Usage Analysis: Mission Partners</h2>
        <div class="visualization">
            <h3>Security Module Usage by Environment (Mission Partners)</h3>
            <img src="module_usage_mission_partners.png" alt="Module Usage Mission Partners">
        </div>
        <div class="visualization">
            <h3>Environment Distribution (Mission Partners)</h3>
            <img src="environment_distribution_mission_partners.png" alt="Environment Distribution Mission Partners">
        </div>
        <div class="visualization">
            <h3>Activated Instances Seen Monthly (Mission Partners)</h3>
            <img src="activated_instances_growth_mission_partners.png" alt="Growth of Activated Instances Mission Partners">
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


def write_interactive_report_html_embedded(metrics: dict, output_dir: str) -> None:
    """
    Write the interactive HTML report with metrics embedded as a JS variable.
    Args:
        metrics (dict): The metrics data to embed
        output_dir (str): Path to the output directory
    """
    import json
    metrics_json = json.dumps(metrics)
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DSUA Interactive Report</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{ background: #f8f9fa; }}
        .container {{ margin-top: 40px; }}
        .section {{ background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 32px;}}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 10px 0; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .table-responsive {{ margin-top: 20px; }}
        .chart-container {{ background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 32px; }}
        .timestamp {{ color: #666; font-style: italic; margin-bottom: 20px; }}
    </style>
</head>
<body>
<div class="container">
    <h1 class="mb-4">Deep Security Usage Analyzer Interactive Report</h1>
    <p class="timestamp" id="timestamp"></p>
    <div class="section" id="overall-metrics"></div>
    <div class="section" id="common-services-metrics"></div>
    <div class="section" id="mission-partners-metrics"></div>
    <div class="section" id="environment-distribution"></div>
    <div class="section" id="module-usage-analysis"></div>
    <div class="section" id="service-category-comparison"></div>
    <div class="section" id="statistics-summary"></div>
    <div class="section" id="monthly-data-analysis"></div>
    <div class="section" id="unknown-environment-analysis"></div>
</div>
<script>
const metrics = {metrics_json};
window.onload = function() {{
    document.getElementById('timestamp').textContent = "Generated on: " + new Date().toLocaleString();
    let overall = metrics.overall;
    document.getElementById('overall-metrics').innerHTML = `
        <h2>Overall Metrics</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${{overall.total_instances}}</div><div class="metric-label">Total Unique Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{overall.activated_instances}}</div><div class="metric-label">Activated Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{overall.inactive_instances}}</div><div class="metric-label">Inactive Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{overall.total_hours.toFixed(1)}}</div><div class="metric-label">Total Hours</div></div>
        </div>
    `;
    let cs = metrics.by_service_category['common services'].overall;
    document.getElementById('common-services-metrics').innerHTML = `
        <h2>Common Services Metrics</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${{cs.total_instances}}</div><div class="metric-label">Total Unique Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{cs.activated_instances}}</div><div class="metric-label">Activated Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{cs.inactive_instances}}</div><div class="metric-label">Inactive Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{cs.total_hours.toFixed(1)}}</div><div class="metric-label">Total Hours</div></div>
        </div>
    `;
    let mp = metrics.by_service_category['mission partners'].overall;
    document.getElementById('mission-partners-metrics').innerHTML = `
        <h2>Mission Partners Metrics</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${{mp.total_instances}}</div><div class="metric-label">Total Unique Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{mp.activated_instances}}</div><div class="metric-label">Activated Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{mp.inactive_instances}}</div><div class="metric-label">Inactive Instances</div></div>
            <div class="metric-card"><div class="metric-value">${{mp.total_hours.toFixed(1)}}</div><div class="metric-label">Total Hours</div></div>
        </div>
    `;
    let envRows = Object.entries(metrics.by_environment).map(([env, data]) => `
        <tr>
            <td>${{env}}</td>
            <td>${{data.total_instances}}</td>
            <td>${{data.activated_instances}}</td>
            <td>${{data.most_common_module}}</td>
            <td>${{data.max_concurrent ?? 'None'}}</td>
            <td>${{data.total_utilization_hours !== undefined ? data.total_utilization_hours.toFixed(1) : 'N/A'}}</td>
        </tr>
    `).join('');
    document.getElementById('environment-distribution').innerHTML = `
        <h2>Environment Distribution</h2>
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Environment</th>
                        <th>Total Hosts</th>
                        <th>Activated Hosts</th>
                        <th>Most Used Module</th>
                        <th>Max Concurrent</th>
                        <th>Total Hours</th>
                    </tr>
                </thead>
                <tbody>${{envRows}}</tbody>
            </table>
        </div>
    `;
    document.getElementById('module-usage-analysis').innerHTML = `
        <h2>Module Usage Analysis</h2>
        <div id="module-usage-chart" class="chart-container"></div>
    `;
    let moduleUsage = overall.module_usage;
    let modules = Object.keys(moduleUsage);
    let usageCounts = Object.values(moduleUsage);
    Plotly.newPlot('module-usage-chart', [{{
        x: modules,
        y: usageCounts,
        type: 'bar',
        marker: {{ color: '#0d6efd' }}
    }}], {{
        title: 'Security Module Usage (Overall)',
        yaxis: {{ title: 'Usage Count' }}
    }}, {{responsive: true}});
    let activatedCounts = [
        cs.activated_instances,
        mp.activated_instances
    ];
    Plotly.newPlot('service-category-comparison', [{{
        labels: ['Common Services', 'Mission Partners'],
        values: activatedCounts,
        type: 'pie',
        textinfo: 'label+percent+value'
    }}], {{
        title: 'Activated Instances Comparison: Common Services vs. Mission Partners'
    }}, {{responsive: true}});
    document.getElementById('statistics-summary').innerHTML = `
        <h2>Statistics Summary</h2>
        <div class="table-responsive">
            <table class="table table-bordered">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Unique Instances</td><td>${{overall.total_instances}}</td></tr>
                <tr><td>Instances Running at Least One Module</td><td>${{overall.activated_instances}}</td></tr>
                <tr><td>Instances Not Running Any Modules</td><td>${{overall.inactive_instances}}</td></tr>
                <tr><td>Total Hours</td><td>${{overall.total_hours.toFixed(1)}}</td></tr>
                <tr><td>Hours for Instances with Modules</td><td>${{overall.activated_hours.toFixed(1)}}</td></tr>
                <tr><td>Hours for Instances without Modules</td><td>${{overall.inactive_hours.toFixed(1)}}</td></tr>
                <tr><td>Average Monthly Growth (Activated Instances)</td><td>${{metrics.monthly.average_monthly_growth.toFixed(1)}} instances</td></tr>
                <tr><td>Unknown Environment Instances</td><td>${{metrics.by_environment.Unknown ? metrics.by_environment.Unknown.total_instances : 0}}</td></tr>
            </table>
        </div>
    `;
    let monthlyRows = (metrics.monthly.data || []).map(month => `
        <tr>
            <td>${{month.month}}</td>
            <td>${{month.activated_instances}}</td>
            <td>${{month.max_concurrent}}</td>
            <td>${{month.avg_modules_per_host.toFixed(2)}}</td>
        </tr>
    `).join('');
    document.getElementById('monthly-data-analysis').innerHTML = `
        <h2>Monthly Data Analysis</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${{metrics.monthly.total_months}}</div><div class="metric-label">Total Months with Data</div></div>
            <div class="metric-card"><div class="metric-value">${{metrics.monthly.date_range}}</div><div class="metric-label">Date Range</div></div>
        </div>
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>Activated Instances</th>
                        <th>Max Concurrent Instances</th>
                        <th>Avg Modules/Host</th>
                    </tr>
                </thead>
                <tbody>${{monthlyRows}}</tbody>
            </table>
        </div>
    `;
    if (metrics.by_environment.Unknown && metrics.by_environment.Unknown.total_instances > 0) {{
        let patterns = (metrics.by_environment.Unknown.patterns || []).map(p => `<li>${{p}}</li>`).join('');
        document.getElementById('unknown-environment-analysis').innerHTML = `
            <div class="alert alert-warning">
                <h2>Unknown Environment Analysis</h2>
                <p>Number of hosts in unknown environment: ${{metrics.by_environment.Unknown.total_instances}}</p>
                <p>Common patterns found in unknown hosts:</p>
                <ul>${{patterns}}</ul>
            </div>
        `;
    }}
}};
</script>
</body>
</html>
'''
    output_path = os.path.join(output_dir, 'interactive_report.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def write_interactive_report_html(output_dir: str) -> None:
    """
    Write the interactive HTML report template to the output directory.
    Args:
        output_dir (str): Path to the output directory
    """
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DSUA Interactive Report</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body { background: #f8f9fa; }
        .container { margin-top: 40px; }
        .section { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 32px;}
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 10px 0; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #666; font-size: 14px; margin-top: 5px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .table-responsive { margin-top: 20px; }
        .chart-container { background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 32px; }
        .timestamp { color: #666; font-style: italic; margin-bottom: 20px; }
    </style>
</head>
<body>
<div class="container">
    <h1 class="mb-4">Deep Security Usage Analyzer Interactive Report</h1>
    <p class="timestamp" id="timestamp"></p>
    <div class="section" id="overall-metrics"></div>
    <div class="section" id="common-services-metrics"></div>
    <div class="section" id="mission-partners-metrics"></div>
    <div class="section" id="environment-distribution"></div>
    <div class="section" id="module-usage-analysis"></div>
    <div class="section" id="service-category-comparison"></div>
    <div class="section" id="statistics-summary"></div>
    <div class="section" id="monthly-data-analysis"></div>
    <div class="section" id="unknown-environment-analysis"></div>
</div>
<script>
async function loadMetrics() {
    let response = await fetch('metrics.json');
    let metrics = await response.json();
    renderReport(metrics);
}
function renderReport(metrics) {
    document.getElementById('timestamp').textContent = "Generated on: " + new Date().toLocaleString();
    let overall = metrics.overall;
    document.getElementById('overall-metrics').innerHTML = `
        <h2>Overall Metrics</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${overall.total_instances}</div><div class="metric-label">Total Unique Instances</div></div>
            <div class="metric-card"><div class="metric-value">${overall.activated_instances}</div><div class="metric-label">Activated Instances</div></div>
            <div class="metric-card"><div class="metric-value">${overall.inactive_instances}</div><div class="metric-label">Inactive Instances</div></div>
            <div class="metric-card"><div class="metric-value">${overall.total_hours.toFixed(1)}</div><div class="metric-label">Total Hours</div></div>
        </div>
    `;
    let cs = metrics.by_service_category['common services'].overall;
    document.getElementById('common-services-metrics').innerHTML = `
        <h2>Common Services Metrics</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${cs.total_instances}</div><div class="metric-label">Total Unique Instances</div></div>
            <div class="metric-card"><div class="metric-value">${cs.activated_instances}</div><div class="metric-label">Activated Instances</div></div>
            <div class="metric-card"><div class="metric-value">${cs.inactive_instances}</div><div class="metric-label">Inactive Instances</div></div>
            <div class="metric-card"><div class="metric-value">${cs.total_hours.toFixed(1)}</div><div class="metric-label">Total Hours</div></div>
        </div>
    `;
    let mp = metrics.by_service_category['mission partners'].overall;
    document.getElementById('mission-partners-metrics').innerHTML = `
        <h2>Mission Partners Metrics</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${mp.total_instances}</div><div class="metric-label">Total Unique Instances</div></div>
            <div class="metric-card"><div class="metric-value">${mp.activated_instances}</div><div class="metric-label">Activated Instances</div></div>
            <div class="metric-card"><div class="metric-value">${mp.inactive_instances}</div><div class="metric-label">Inactive Instances</div></div>
            <div class="metric-card"><div class="metric-value">${mp.total_hours.toFixed(1)}</div><div class="metric-label">Total Hours</div></div>
        </div>
    `;
    let envRows = Object.entries(metrics.by_environment).map(([env, data]) => `
        <tr>
            <td>${env}</td>
            <td>${data.total_instances}</td>
            <td>${data.activated_instances}</td>
            <td>${data.most_common_module}</td>
            <td>${data.max_concurrent ?? 'None'}</td>
            <td>${data.total_utilization_hours !== undefined ? data.total_utilization_hours.toFixed(1) : 'N/A'}</td>
        </tr>
    `).join('');
    document.getElementById('environment-distribution').innerHTML = `
        <h2>Environment Distribution</h2>
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Environment</th>
                        <th>Total Hosts</th>
                        <th>Activated Hosts</th>
                        <th>Most Used Module</th>
                        <th>Max Concurrent</th>
                        <th>Total Hours</th>
                    </tr>
                </thead>
                <tbody>${envRows}</tbody>
            </table>
        </div>
    `;
    document.getElementById('module-usage-analysis').innerHTML = `
        <h2>Module Usage Analysis</h2>
        <div id="module-usage-chart" class="chart-container"></div>
    `;
    let moduleUsage = overall.module_usage;
    let modules = Object.keys(moduleUsage);
    let usageCounts = Object.values(moduleUsage);
    Plotly.newPlot('module-usage-chart', [{
        x: modules,
        y: usageCounts,
        type: 'bar',
        marker: { color: '#0d6efd' }
    }], {
        title: 'Security Module Usage (Overall)',
        yaxis: { title: 'Usage Count' }
    }, {responsive: true});
    let activatedCounts = [
        cs.activated_instances,
        mp.activated_instances
    ];
    Plotly.newPlot('service-category-comparison', [{
        labels: ['Common Services', 'Mission Partners'],
        values: activatedCounts,
        type: 'pie',
        textinfo: 'label+percent+value'
    }], {
        title: 'Activated Instances Comparison: Common Services vs. Mission Partners'
    }, {responsive: true});
    document.getElementById('statistics-summary').innerHTML = `
        <h2>Statistics Summary</h2>
        <div class="table-responsive">
            <table class="table table-bordered">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Unique Instances</td><td>${overall.total_instances}</td></tr>
                <tr><td>Instances Running at Least One Module</td><td>${overall.activated_instances}</td></tr>
                <tr><td>Instances Not Running Any Modules</td><td>${overall.inactive_instances}</td></tr>
                <tr><td>Total Hours</td><td>${overall.total_hours.toFixed(1)}</td></tr>
                <tr><td>Hours for Instances with Modules</td><td>${overall.activated_hours.toFixed(1)}</td></tr>
                <tr><td>Hours for Instances without Modules</td><td>${overall.inactive_hours.toFixed(1)}</td></tr>
                <tr><td>Average Monthly Growth (Activated Instances)</td><td>${metrics.monthly.average_monthly_growth.toFixed(1)} instances</td></tr>
                <tr><td>Unknown Environment Instances</td><td>${metrics.by_environment.Unknown ? metrics.by_environment.Unknown.total_instances : 0}</td></tr>
            </table>
        </div>
    `;
    let monthlyRows = (metrics.monthly.data || []).map(month => `
        <tr>
            <td>${month.month}</td>
            <td>${month.activated_instances}</td>
            <td>${month.max_concurrent}</td>
            <td>${month.avg_modules_per_host.toFixed(2)}</td>
        </tr>
    `).join('');
    document.getElementById('monthly-data-analysis').innerHTML = `
        <h2>Monthly Data Analysis</h2>
        <div class="grid">
            <div class="metric-card"><div class="metric-value">${metrics.monthly.total_months}</div><div class="metric-label">Total Months with Data</div></div>
            <div class="metric-card"><div class="metric-value">${metrics.monthly.date_range}</div><div class="metric-label">Date Range</div></div>
        </div>
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>Activated Instances</th>
                        <th>Max Concurrent Instances</th>
                        <th>Avg Modules/Host</th>
                    </tr>
                </thead>
                <tbody>${monthlyRows}</tbody>
            </table>
        </div>
    `;
    if (metrics.by_environment.Unknown && metrics.by_environment.Unknown.total_instances > 0) {
        let patterns = (metrics.by_environment.Unknown.patterns || []).map(p => `<li>${p}</li>`).join('');
        document.getElementById('unknown-environment-analysis').innerHTML = `
            <div class="alert alert-warning">
                <h2>Unknown Environment Analysis</h2>
                <p>Number of hosts in unknown environment: ${metrics.by_environment.Unknown.total_instances}</p>
                <p>Common patterns found in unknown hosts:</p>
                <ul>${patterns}</ul>
            </div>
        `;
    }
}
window.onload = loadMetrics;
</script>
</body>
</html>
'''
    output_path = os.path.join(output_dir, 'interactive_report.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def export_metrics_json(metrics: Dict, output_path: str) -> None:
    """
    Export the metrics dictionary as a JSON file for use in interactive reports.
    Args:
        metrics (Dict): The metrics data to export
        output_path (str): Path to the output JSON file
    """
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)



def generate_modern_interactive_report(metrics: dict, template_path: str, output_path: str) -> None:
    """
    Generate a modern interactive HTML report by embedding metrics into the template.
    Args:
        metrics (dict): The metrics data to embed
        template_path (str): Path to the HTML template file
        output_path (str): Path to write the final HTML report
    """
    import json
    with open(template_path, 'r', encoding='utf-8') as f:
        template_html = f.read()
    # Replace the placeholder for metrics assignment
    metrics_json = json.dumps(metrics)
    html_out = template_html.replace('let metrics = null; // Will be replaced with embedded JSON', f'let metrics = {metrics_json};')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_out)
