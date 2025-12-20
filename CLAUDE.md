# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

The Trend Micro Deep Security Usage Analyzer (DSUA) is a Python application designed to **aid in determining license utilization when Deep Security is deployed in closed and/or airgapped environments**.

### Purpose

In environments where Deep Security cannot connect to Trend Micro's cloud services (airgapped, sovereign, or restricted networks), standard license usage reporting is unavailable. DSUA fills this gap by:

1. **Analyzing Security Module Usage Reports** exported from Deep Security Manager
2. **Calculating license utilization metrics** to determine how many instances are actively using protection
3. **Distinguishing activated vs inactive instances** using a configurable activation threshold
4. **Supporting licensing decisions** with auditable, transparent calculations

### Why Airgapped Operation Matters

DSUA operates completely offline with no external API calls or network connectivity required:
- All data processing is performed locally
- No telemetry or usage data is transmitted externally
- Suitable for IL4, IL5, and other restricted classification environments
- Reports can be generated on isolated systems and shared via secure channels

## Key Commands

### Running the Application
```bash
# Optional: Run deduplication first to remove duplicate files
python dedupe.py

# Main analysis
python DSUA.py
```

### Development Setup
```bash
# Create virtual environment (Python 3.7-3.12 required)
python -m venv dsua-env

# Activate virtual environment
source dsua-env/bin/activate  # On macOS/Linux
# or
dsua-env\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Testing & Linting
Currently, there are no specific test files or linting configurations in the project. When implementing tests or linting:
- Consider adding pytest for testing
- Consider adding flake8 or ruff for linting
- Update this file with the appropriate commands when added

## Architecture Overview

### Core Components

1. **Main Entry Point**: `DSUA.py` - Orchestrates the entire analysis workflow
2. **File Deduplication**: `dedupe.py` - Removes duplicate files using SHA-256 hashing

### Module Structure

```
modules/
├── analyzer/          # Data processing and analysis
│   ├── analyzer.py    # Main analysis orchestration
│   ├── data_loader.py # Centralized data loading & preprocessing
│   ├── metrics_calculator.py # Metrics computation with validation
│   └── concurrent_calculator.py # Concurrent usage analysis
├── reporting/         # Report generation
│   ├── html_generator.py # HTML report creation
│   ├── pdf_generator.py  # PDF report creation
│   ├── interactive_report_template.html # Interactive report with filtering
│   └── image_handler.py  # Image processing for reports
├── visualizations.py  # Chart generation (matplotlib/seaborn)
├── utils.py          # Common utilities
└── logging_config.py # Logging configuration
```

### Key Data Flow

1. **Data Loading & Preprocessing** (`data_loader.py`)
   - Loads CSV/Excel files
   - Centralizes all preprocessing: adds/fixes module columns, fills NaNs, logs/corrects invalids
   - Adds `has_modules` column for instances with security modules
   - Adds `service_category` based on "Computer Group" patterns in config.json

2. **Metrics Calculation** (`metrics_calculator.py`)
   - Calculates metrics split by multiple dimensions:
     - Overall, by environment, by service category, by month
     - Multi-dimensional splits for interactive filtering (cloud provider + environment + service category)
   - Implements configurable activation threshold (only instances with cumulative online time ≥ threshold are "activated")
   - Strict validation with exceptions for data integrity issues

3. **Report Generation**
   - Creates static HTML/PDF reports with embedded visualizations
   - Generates interactive HTML report with dynamic filtering
   - All charts generated for each service category + comparison charts

## Configuration

Configuration is stored in `config.json` (gitignored). Copy `config.template.json` to `config.json` and customize for your environment.

### Core Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `common_services_selectors` | Array of patterns (case-insensitive) to match against Computer Group for categorizing instances as "Common Services" vs "Mission Partners" | `["shared-infra", "common-svc"]` |
| `activation_min_hours` | Minimum cumulative online hours with ANY security module enabled for an instance to be counted as "activated" | `72` |

### Activation Threshold (Critical for Licensing)

The `activation_min_hours` parameter is fundamental to license utilization calculations:

- **What it does**: Filters out transient, test, or briefly-online instances from activated counts
- **Why it matters**: Prevents inflating license counts with instances that were only briefly protected
- **How to set it**: Should align with your licensing contract terms (e.g., 24, 72, or 168 hours)
- **Calculation**: Cumulative time across all records where the instance had at least one security module enabled

**Example**: With `activation_min_hours: 72`, an instance must have been online with protection for a total of 72+ hours during the analysis period to count as "activated" for licensing purposes.

## Input Data Requirements

DSUA processes **Deep Security Security Module Usage Reports** exported from Deep Security Manager.

### Supported File Formats
- CSV (tab or comma delimited, auto-detected)
- Excel (.xlsx, .xls)

### Required Columns

| Column | Description |
|--------|-------------|
| `Hostname` | Unique identifier for the protected instance |
| `Start Date` | Date when the usage period began |
| `Start Time` | Time when the usage period began |
| `Stop Date` | Date when the usage period ended |
| `Stop Time` | Time when the usage period ended |
| `Duration (Seconds)` | Total seconds in the usage period |

### Security Module Columns (Binary 0/1)

| Column | Module Name |
|--------|-------------|
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

| Column | Description |
|--------|-------------|
| `Computer Group` | Used for service category classification |
| `Cloud Account` | Cloud provider account identifier |
| `Source_Cloud_Provider` | Explicit cloud provider (AWS, Azure, GCP, OCI) |

### Data Preprocessing

During loading, DSUA automatically:
1. Adds missing module columns (set to 0)
2. Converts non-binary module values to 0 (logged as warnings)
3. Fills NaN values appropriately
4. Detects and removes duplicate header rows
5. Adds derived columns: `has_modules`, `service_category`, `cloud_provider`

## Licensing Decision Support

DSUA provides metrics specifically designed to support licensing decisions:

### Key Metrics for Licensing

| Metric | Description | Licensing Relevance |
|--------|-------------|---------------------|
| **Activated Instances** | Instances with cumulative online time ≥ activation threshold AND at least one module enabled | Primary count for license true-up |
| **Inactive Instances** | Total instances minus activated instances | Potential license optimization opportunity |
| **Max Concurrent** | Peak simultaneous instances at any point in time | May affect burst licensing or capacity planning |
| **Activated Hours** | Total hours of protection across all activated instances | Validates sustained usage |

### How Metrics Are Calculated

1. **Total Instances**: Count of unique hostnames in the dataset
2. **Activated Instances**: Unique hostnames where `SUM(Duration)` for records with `has_modules=True` ≥ `activation_min_hours * 3600`
3. **Concurrent Usage**: Timeline algorithm that tracks +1 at each start time and -1 at each stop time, returning the maximum concurrent count

### Audit Trail

All calculations are logged to `security_analysis.log` with:
- Data quality warnings (invalid values corrected)
- Preprocessing steps applied
- Metric calculation results
- Any exceptions or errors encountered

## Important Patterns & Conventions

### Environment Classification
The system uses multi-level pattern matching to classify environments:
- **File-based**: First attempts to determine from filename patterns
- **Hostname-based**: Falls back to hostname patterns (prod, dev, test, etc.)
- **Domain-based**: Uses network patterns as additional context
- **Default**: Marks as "Unknown" if no pattern matches

### Data Quality & Validation
- Centralized preprocessing ensures data consistency before any analysis
- All metrics functions raise exceptions for critical validation failures
- Explicit handling of empty DataFrames and missing columns
- Invalid module values are logged and corrected during preprocessing

### Interactive Report Architecture
The `interactive_report_template.html` is critical - it implements:
- Dynamic filtering by environment, module, cloud provider, and service category
- Correct data source selection based on active filters
- Real-time chart and metric updates without page reload

## Working with the Codebase

### Adding New Features
1. Review existing patterns in similar modules
2. Follow the centralized preprocessing approach in `data_loader.py`
3. Add appropriate validation and error handling in metrics calculations
4. Update both static and interactive reports when adding new visualizations

### Debugging Tips
- Check `security_analysis.log` for detailed execution logs
- Use the logging framework (with emoji indicators) for debugging
- Validate data at each pipeline stage
- Test with different activation threshold values in config.json

### Performance Considerations
- Large datasets can consume significant memory (8GB+ recommended)
- All data is loaded into memory for analysis
- File deduplication significantly improves performance
- Environment classification and concurrent calculations are computationally intensive