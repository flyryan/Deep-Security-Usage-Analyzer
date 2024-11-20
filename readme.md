# Trend Micro Deep Security Usage Analyzer (DSUA)

The Trend Micro Deep Security Usage Analyzer (DSUA) is a comprehensive tool designed to analyze module usage across different environments within Trend Micro's Deep Security. It processes usage data, deduplicates files and entries for efficiency, and generates detailed reports and visualizations to provide insights into module utilization.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Deduplication Process](#deduplication-process)
- [Usage](#usage)
- [Workflow](#workflow)
- [Output](#output)
- [Contributing](#contributing)

## Overview

DSUA provides a clear understanding of module usage patterns by analyzing data exported from Deep Security. It handles large datasets by deduplicating files and entries, ensuring accurate and efficient analysis. The tool generates comprehensive reports including metrics summaries, visualizations, and detailed HTML and PDF reports with embedded visualizations.

## Prerequisites

- Python 3.7 - 3.12 (some dependencies currently don't support 3.13)
- Required Python packages:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - jinja2
  - openpyxl
  - xlrd
  - reportlab
  - tqdm

## Features

- **Comprehensive Analysis:** Processes usage data from multiple environments simultaneously, generating detailed reports with monthly trend analysis.
- **Deduplication:** Automatically removes duplicate files and entries, ensuring accurate analysis without redundancy.
- **Enhanced Environment Classification:** Classifies data entries into environments using comprehensive pattern matching for hostnames and IP addresses.
- **Module Usage Metrics:** Calculates detailed usage metrics including concurrent usage and monthly trends.
- **Visualizations:** Generates static visualizations embedded in both HTML and PDF reports.
- **Enhanced Logging:** Colored console output with emoji indicators for different log levels, plus detailed log file generation.
- **Progress Tracking:** Visual progress bars for long-running operations.

## Deduplication Process

The deduplication process ensures accuracy and efficiency:

1. **File Deduplication (Optional but Recommended):**
   - Use the provided `dedupe.py` script to remove duplicate files in the current directory
   - Significantly reduces processing time for large datasets
   - Removes duplicate files based on SHA-256 hash values

2. **Entry Deduplication:**
   - Automatically performs deduplication of individual entries within the data files
   - Combines data from all files, removes duplicate rows, and standardizes the data
   - Preserves time-series data integrity while removing redundant entries

## Usage

1. **Prepare Data:**
   - Place all usage data files (`.csv`, `.xlsx`, or `.xls`) in the same directory as the script
   - Ensure only the files you wish to analyze are present
   - *Optional:* Use environment-specific naming patterns in filenames to aid classification

2. **Optional: Set Time Range Parameters*
  - Locate the `main()` function within the script.
  - Modify the instantiation of the `SecurityModuleAnalyzer` class to include the `start_date` and `end_date` parameters if you wish to filter the data by a specific date range.

  Example:
  ```python
  def main():
     analyzer = SecurityModuleAnalyzer(
        start_date="2024-01-01",  # Optional: Filter data from this date
        end_date="2024-12-31"     # Optional: Filter data until this date
     )
     analyzer.run()
  ```

  - Save the changes to `DSUA.py`.
  - This step is optional and can be skipped if you want to analyze all available data without date filtering.

3. **Run File Deduplication (Optional but Recommended):**
   ```bash
   python dedupe.py
   ```
   - Run in the directory containing your data files
   - Automatically identifies and removes duplicate files
   - **Note:** Backup your data before running

4. **Run DSUA:**
   ```bash
   python DSUA.py
   ```
   - Automatically processes all valid files in the current directory
   - Creates an `output` directory for generated reports and visualizations
   - Displays progress bars and colored status messages during execution

## Workflow

### 1. Data Collection and Validation

- **Input Processing:**
  - Scans current directory for valid file types (`.csv`, `.xlsx`, `.xls`)
  - Validates required columns and data types
  - Handles missing values and standardizes formats

### 2. Environment Classification

- **Pattern Matching:**
  - **Production:** `prod`, `-prod`, `prd`, `production`, `\bprd\d+\b`, `\bp\d+\b`, `live`, `prod-`, `-prd-`, `production-`
  - **Development:** `dev`, `development`, `\bdev\d+\b`, `develop-`, `-dev-`, `development-`
  - **Test:** `test`, `tst`, `qa`, `\btst\d+\b`, `testing-`, `-test-`, `qa-`, `-qa-`
  - **Staging:** `stage`, `staging`, `stg`, `\bstg\d+\b`, `stage-`, `-stg-`, `staging-`
  - **DR:** `dr`, `disaster`, `recovery`, `dr-site`, `disaster-recovery`, `backup-site`
  - **UAT:** `uat`, `acceptance`, `\buat\d+\b`, `uat-`, `-uat-`, `user-acceptance`
  - **Integration:** `int`, `integration`, `\bint\d+\b`, `integration-`, `-int-`

- **Domain Classification:**
  - **Internal:** `10\.\d+\.\d+\.\d+`, `192\.168\.\d+\.\d+`, `172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+`, `\.internal\.`, `\.local\.`, `\.intranet\.`
  - **DMZ:** `dmz`, `perimeter`, `\.dmz\.`, `border`

### Environment Classification Patterns

- **File-based Classification**: The analyzer first attempts to determine environment from filename patterns
- **Hostname-based Classification**: Falls back to analyzing hostname patterns
- **Domain-based Classification**: Uses network domain patterns as additional context
- **Default Classification**: Marks as "Unknown" if no pattern matches

### 3. Metric Calculations

- **Basic Metrics:**
  ```json
  {
    "overall": {
      "total_instances": 15000,
      "activated_instances": 12500,
      "inactive_instances": 2500,
      "total_hours": 44640.0,
      "activated_hours": 37200.0,
      "inactive_hours": 7440.0
    }
  }
  ```

- **Monthly Analysis:**
  ```json
  {
    "monthly": {
      "2024-01": {
        "activated_instances": 1250,
        "new_instances": 45,
        "lost_instances": 12,
        "max_concurrent": 82,
        "avg_modules_per_host": 2.4,
        "total_hours": 44640
      }
    }
  }
  ```

- **Concurrent Usage:**
  ```json
  {
    "max_concurrent_overall": 117,
    "max_concurrent_by_env": {
      "Production": 82,
      "Development": 45,
      "Test": 23
    }
  }
  ```

### 4. Report Generation

- **HTML Report:**
  - Static report with embedded visualizations
  - Comprehensive metrics tables
  - Environment distribution charts
  - Module usage analysis
  - Monthly trend data

- **PDF Report:**
  - Static report matching HTML content
  - Embedded charts and graphs
  - Detailed metrics tables
  - Environment analysis
  - Monthly statistics

### 5. Logging and Progress Tracking

- **Console Output:**
  - 🔍 DEBUG: Detailed debugging information
  - ℹ️ INFO: General process updates
  - ⚠️ WARNING: Potential issues
  - ❌ ERROR: Error conditions
  - 🚨 CRITICAL: Critical failures

- **Log File:**
  - Detailed logging to `security_analysis.log`
  - Timestamp for each entry
  - Complete error tracebacks
  - Data validation results

## Analysis Output

### Visualizations
- **Module Usage**: Stacked bar chart showing security module usage across environments
- **Environment Distribution**: Pie chart showing distribution of activated instances
- **Activated Instances Growth**: Line chart showing growth of activated instances over time

### Generated Reports
- `report.html`: HTML report with embedded visualizations
- `report.pdf`: Printer-friendly PDF version
- `metrics.json`: Detailed metrics in JSON format including:
  - Overall metrics
  - Environment-specific metrics
  - Monthly trends
  - Utilization statistics
  - Concurrent usage analysis
- `module_usage.png`: Module usage visualization
- `environment_distribution.png`: Environment distribution chart
- `security_analysis.log`: Detailed execution log

## Contributing

Contributions to improve DSUA are welcome. Please submit a pull request or open an issue on GitHub with your suggestions.