import json
import os
from datetime import datetime


TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Growth Projections</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
  <script src=\"https://cdn.plot.ly/plotly-2.26.0.min.js\"></script>
  <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
  <style>
    body { background: #f8f9fa; }
    .container { margin-top: 40px; }
    .section { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 24px;}
    .small-muted { color: #6c757d; font-size: 0.9rem; }
    .summary-card { background: #f8f9fa; border-radius: 8px; padding: 16px; }
    .scenario { font-weight: 600; }
    .kpi { font-size: 1.1rem; }
    .filter-bar { margin-bottom: 16px; }
  </style>
  <script>
    const data = __PROJECTIONS_JSON__;
    function formatNumber(x) { return x === null || isNaN(x) ? '—' : Math.round(x).toLocaleString(); }
    function nextMonth(monthStr) {
      const [year, month] = monthStr.split('-').map(Number);
      const date = new Date(year, month - 1, 1);
      date.setMonth(date.getMonth() + 1);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    }
    function subsetData(category, cloud) {
      if (category === 'All' && cloud === 'All') return data;
      if (category === 'All' && cloud !== 'All') return (data.by_cloud_provider || {})[cloud];
      if (category !== 'All' && cloud === 'All') return (data.by_category || {})[category];
      const key = `${category}::${cloud}`;
      return (data.by_category_and_cloud_provider || {})[key];
    }
    function updateView() {
      const category = document.getElementById('category-select').value;
      const cloud = document.getElementById('cloud-select').value;
      const d = subsetData(category, cloud);
      if (!d) {
        document.getElementById('chart').innerHTML = '<div class=\"text-muted\">No data available for this selection.</div>';
        document.getElementById('kpi-body').innerHTML = '';
        return;
      }
      const actual = d.actual;
      const overlay = d.actual_overlay || [];
      const monthsActual = actual.map(p => p.month);
      const valuesActual = actual.map(p => p.activated_instances);
      const traces = [{ x: monthsActual, y: valuesActual, type: 'scatter', mode: 'lines+markers', name: 'Actual (Current Year)', line: { color: '#212529', width: 3 }, connectgaps: true }];
      if (overlay.length) {
        traces.push({ x: overlay.map(p => p.month), y: overlay.map(p => p.activated_instances), type: 'scatter', mode: 'lines', name: 'Actual (All-Time)', line: { color: '#adb5bd', width: 2, dash: 'dot' }, hoverinfo: 'skip' });
      }
      const gapPoints = actual.filter(p => p.is_gap);
      if (gapPoints.length) {
        traces.push({ x: gapPoints.map(p => p.month), y: gapPoints.map(p => p.activated_instances), type: 'scatter', mode: 'markers', name: 'Data Gap (carried forward)', marker: { symbol: 'circle-open', color: '#dc3545', size: 9 }, showlegend: true });
      }
      const colors = { linear: '#0d6efd', decay: '#dc3545', avg_last3: '#198754' };
      Object.entries(d.scenarios || {}).forEach(([key, sc]) => {
        traces.push({ x: sc.series.map(p => p.month), y: sc.series.map(p => p.activated_instances), type: 'scatter', mode: 'lines+markers', name: sc.name, line: { color: colors[key] || undefined, dash: 'dash' } });
      });
      const shapes = [];
      (d.data_gaps || []).forEach(g => {
        shapes.push({ type: 'rect', xref: 'x', yref: 'paper', x0: g.start, x1: nextMonth(g.end), y0: 0, y1: 1, fillcolor: 'rgba(220,53,69,0.12)', line: { width: 0 } });
      });
      const layout = { title: 'Activated Instances: Actuals and Projections', xaxis: { title: 'Month' }, yaxis: { title: 'Cumulative Activated Instances' }, legend: { orientation: 'h' }, margin: { l: 60, r: 20, t: 50, b: 60 }, shapes };
      Plotly.newPlot('chart', traces, layout, { responsive: true });
      const tbody = document.getElementById('kpi-body');
      tbody.innerHTML = '';
      const base = actual[actual.length-1].activated_instances;
      Object.entries(d.scenarios || {}).forEach(([key, sc]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td class=\"scenario\">${sc.name}</td>
          <td class=\"kpi\">${formatNumber(sc.EOY_2025)}</td>
          <td class=\"kpi\">${formatNumber(sc.EOY_2026)}</td>
          <td class=\"kpi\">${formatNumber(sc.EOY_2025 - base)}</td>
          <td class=\"kpi\">${formatNumber(sc.EOY_2026 - base)}</td>
        `;
        tbody.appendChild(row);
      });
    }
    function render() {
      const ts = new Date().toLocaleString();
      document.getElementById('timestamp').textContent = `Generated on: ${ts}`;
      const cpSelect = document.getElementById('cloud-select');
      const catSelect = document.getElementById('category-select');
      const cpKeys = ['All'].concat(Object.keys(data.by_cloud_provider || {}));
      cpSelect.innerHTML = cpKeys.map(k => `<option value=\"${k}\">${k}</option>`).join('');
      const catKeys = ['All','common services','mission partners'];
      catSelect.innerHTML = catKeys.map(k => `<option value=\"${k}\">${k}</option>`).join('');
      cpSelect.addEventListener('change', updateView);
      catSelect.addEventListener('change', updateView);
      updateView();
    }
    window.addEventListener('load', render);
  </script>
</head>
<body>
  <div class=\"container\">
    <h1 class=\"mb-2\">Growth Projections</h1>
    <div id=\"timestamp\" class=\"small-muted mb-3\"></div>
    <div class=\"filter-bar d-flex align-items-center flex-wrap\"> 
      <div class=\"me-3\">
        <label class=\"form-label me-2\" for=\"category-select\">Service Category:</label>
        <select id=\"category-select\" class=\"form-select d-inline-block\" style=\"width:auto;\"></select>
      </div>
      <div>
        <label class=\"form-label me-2\" for=\"cloud-select\">Cloud Provider:</label>
        <select id=\"cloud-select\" class=\"form-select d-inline-block\" style=\"width:auto;\"></select>
      </div>
    </div>
    <div class=\"section\">
      <div id=\"chart\"></div>
    </div>
    <div class=\"section\">
      <h4 class=\"mb-3\">End-of-Year Projections</h4>
      <div class=\"table-responsive\">
        <table class=\"table table-bordered\">
          <thead class=\"table-light\">
            <tr>
              <th>Scenario</th>
              <th>EOY 2025</th>
              <th>EOY 2026</th>
              <th>Growth from Current to EOY 2025</th>
              <th>Growth from Current to EOY 2026</th>
            </tr>
          </thead>
          <tbody id=\"kpi-body\"></tbody>
        </table>
      </div>
      <p class=\"small-muted mb-0\">Notes: Linear Trend fits a straight line to cumulative totals. Geometric Decay reduces monthly adds by the median recent ratio (conservative). Rolling Avg uses the average of the last 3 monthly adds (optimistic). Use the selectors above to view Overall, by Cloud, and by Service Category combinations.</p>
    </div>
  </div>
</body>
</html>
"""


def write_projection_html(projections: dict, output_path: str) -> None:
    html = TEMPLATE.replace("__PROJECTIONS_JSON__", json.dumps(projections))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render growth projections HTML")
    parser.add_argument("--projections", default="output/projections.json", help="Path to projections.json")
    parser.add_argument("--out", default="output/growth_projections.html", help="Output HTML path")
    args = parser.parse_args()

    with open(args.projections, "r", encoding="utf-8") as f:
        projections = json.load(f)

    write_projection_html(projections, args.out)
    print(f"Wrote HTML to {args.out}")


if __name__ == "__main__":
    main()
