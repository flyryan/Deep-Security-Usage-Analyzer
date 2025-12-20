# Trend Micro Deep Security Usage Analyzer (DSUA)

The Trend Micro Deep Security Usage Analyzer (DSUA) is designed to **aid in determining license utilization when Deep Security is deployed in closed and/or airgapped environments**.

## Purpose

In airgapped, sovereign, or restricted network environments where Deep Security cannot connect to Trend Micro's cloud services, standard license usage reporting is unavailable. DSUA fills this gap by processing exported Security Module Usage Reports and generating auditable metrics for licensing decisions.

### Key Capabilities

- **License Utilization Analysis**: Determine how many instances are actively using Deep Security protection
- **Activation Threshold Filtering**: Distinguish genuinely active instances from transient or test deployments
- **Multi-Environment Support**: Analyze usage across AWS, Azure, GCP, OCI, and on-premises environments
- **Auditable Calculations**: Transparent metrics with full logging for license compliance verification

### Offline Operation

DSUA operates completely offline:
- No internet connectivity required
- No external API calls or telemetry
- All data processed locally
- Suitable for IL4, IL5, C1D, and other restricted classification environments

## Table of Contents

- [Use Cases](#use-cases)
- [Activation Threshold](#activation-threshold)
- [Input Data Requirements](#input-data-requirements)
- [Configuration](#configuration)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Workflow](#workflow)
- [Output](#output)
- [Glossary](#glossary)
- [Contributing](#contributing)

## Use Cases

### License Optimization
Identify the difference between **total instances** (all hostnames in usage reports) and **activated instances** (those meeting the activation threshold). The gap represents potential license optimization opportunities.

### Contract Compliance
Verify that instance counts align with licensing contract terms by using the configurable activation threshold to match your contract's definition of "active" protection.

### Capacity Planning
Analyze **maximum concurrent usage** to understand peak protection demand, useful for capacity planning and burst licensing scenarios.

### Growth Trending
Track month-over-month changes in activated instances to forecast future licensing needs.

## Activation Threshold

The activation threshold is the most critical configuration parameter for licensing decisions.

### What It Is

The `activation_min_hours` setting defines the **minimum cumulative online hours** an instance must have (with at least one security module enabled) to be counted as "activated" for licensing purposes.

### Why It Matters

Without a threshold, every instance that appeared briefly in usage reports would count toward licensing—including:
- Test instances spun up for minutes
- Instances that had Deep Security agent installed but never configured
- Decommissioned instances with residual activity

The activation threshold ensures only genuinely protected instances count toward license utilization.

### How It Works

1. DSUA sums all `Duration (Seconds)` for each unique hostname where at least one security module was enabled
2. If this cumulative time ≥ `activation_min_hours × 3600`, the instance is "activated"
3. All metrics, reports, and visualizations reflect this filtered count

### Setting the Threshold

Configure in `config.json`:
```json
{
  "activation_min_hours": 72
}
```

**Recommended values:**
- `24` - Minimum for catching short-lived instances
- `72` - Balanced threshold for most deployments (3 days cumulative)
- `168` - Strict threshold (1 week cumulative)

The value should align with your licensing contract terms for what constitutes "active" protection.

## Input Data Requirements

### Data Source

Export **Security Module Usage Reports** from Deep Security Manager. These reports contain time-series records of when security modules were active on each protected instance.

### Supported File Formats

| Format | Notes |
|--------|-------|
| CSV | Tab or comma delimited (auto-detected) |
| Excel | .xlsx and .xls formats supported |

### Required Columns

| Column | Description |
|--------|-------------|
| `Hostname` | Unique identifier for the protected instance |
| `Start Date` | Date when the usage period began |
| `Start Time` | Time when the usage period began |
| `Stop Date` | Date when the usage period ended |
| `Stop Time` | Time when the usage period ended |
| `Duration (Seconds)` | Total seconds in the usage period |

### Security Module Columns

Each module is represented as a binary column (0 = disabled, 1 = enabled):

| Column | Module |
|--------|--------|
| `AM` | Anti-Malware |
| `WRS` | Web Reputation Service |
| `DC` | Device Control |
| `AC` | Application Control |
| `IM` | Integrity Monitoring |
| `LI` | Log Inspection |
| `FW` | Firewall |
| `DPI` | Deep Packet Inspection |
| `SAP` | Suspicious Activity Prevention |

### Optional Columns

| Column | Purpose |
|--------|---------|
| `Computer Group` | Used for service category classification |
| `Cloud Account` | Cloud provider account identifier |
| `Source_Cloud_Provider` | Explicit cloud provider (AWS, Azure, GCP, OCI) |

### Data Preprocessing

DSUA automatically handles common data quality issues:
- Missing module columns are added (set to 0)
- Non-binary module values are corrected to 0 (logged as warnings)
- Duplicate header rows are detected and removed
- NaN values are filled appropriately

## Configuration

Copy `config.template.json` to `config.json` and customize for your environment.

### Core Parameters

```json
{
  "common_services_selectors": [
    "shared-infra-pattern",
    "common-services-pattern"
  ],
  "activation_min_hours": 72
}
```

| Parameter | Description |
|-----------|-------------|
| `common_services_selectors` | Array of patterns (case-insensitive) to match against `Computer Group` for categorizing instances as "Common Services" vs "Mission Partners" |
| `activation_min_hours` | Minimum cumulative online hours for an instance to count as "activated" (see [Activation Threshold](#activation-threshold)) |

## Prerequisites

- Deep Security Security Module Usage Reports in CSV or Excel format
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
- Install required Python packages using `requirements.txt`:

  ```bash
  pip install -r requirements.txt
  ```

## Project Structure

The project follows a modular architecture for better organization and maintainability:

```
DSUA/
├── DSUA.py                 # Main entry point
├── dedupe.py              # File deduplication utility
├── requirements.txt       # Project dependencies
└── modules/              # Core modules directory
    ├── __init__.py
    ├── logging_config.py  # Logging configuration
    ├── report_generator.py # Report generation orchestration
    ├── utils.py          # Common utilities
    ├── visualizations.py  # Visualization functions
    ├── analyzer/         # Analysis module
    │   ├── __init__.py
    │   ├── analyzer.py   # Main analysis logic
    │   ├── concurrent_calculator.py # Concurrent usage calculations
    │   ├── data_loader.py # Data loading and preprocessing
    │   └── metrics_calculator.py # Metrics computation
    └── reporting/        # Report generation module
        ├── __init__.py
        ├── html_generator.py # HTML report generation
        ├── pdf_generator.py  # PDF report generation
        ├── image_handler.py  # Image processing
        └── report_utils.py   # Common reporting utilities
```

### Core Modules

- **analyzer**: Handles all data analysis operations
  - `analyzer.py`: Main analysis orchestration
  - `data_loader.py`: Data loading and preprocessing
  - `metrics_calculator.py`: Computation of usage metrics
  - `concurrent_calculator.py`: Concurrent usage analysis

- **reporting**: Manages report generation
  - `html_generator.py`: HTML report creation
  - `pdf_generator.py`: PDF report creation
  - `image_handler.py`: Image processing and embedding
  - `report_utils.py`: Shared reporting utilities

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

2. **Optional: Set Time Range Parameters**
   - Locate the `main()` function within the script.
   - Modify the instantiation of the `SecurityModuleAnalyzer` class to include the `start_date` and `end_date` parameters if you wish to filter the data by a specific date range.

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
- `security_analysis.log`: Detailed execution log (includes data quality warnings and calculation audit trail)

## Glossary

Key terms used in DSUA reports and metrics:

| Term | Definition |
|------|------------|
| **Total Instances** | Count of all unique hostnames appearing in the usage data |
| **Activated Instances** | Instances with cumulative online time ≥ activation threshold AND at least one security module enabled |
| **Inactive Instances** | Total instances minus activated instances; may represent optimization opportunities |
| **Activated Hours** | Sum of all duration where the instance had at least one module enabled |
| **Max Concurrent** | Peak number of instances simultaneously active at any point in the analysis period |
| **Service Category** | Classification as "Common Services" (shared infrastructure) or "Mission Partners" (application-specific) based on Computer Group patterns |
| **Cloud Provider** | Detected cloud platform (AWS, Azure, GCP, OCI) based on hostname patterns, filenames, or explicit column |
| **Environment** | Detected deployment stage (Production, Development, Test, Staging, etc.) based on hostname patterns |

## Contributing

Contributions to improve DSUA are welcome. Please submit a pull request or open an issue on GitHub with your suggestions.