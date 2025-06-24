# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

The Trend Micro Deep Security Usage Analyzer (DSUA) is a comprehensive Python application that analyzes Trend Micro Deep Security module usage across different cloud environments. It processes usage reports, generates visualizations, and creates detailed HTML/PDF reports with interactive filtering capabilities.

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

### config.json
```json
{
  "common_services_selectors": [
    "cce-aws-isobar",
    "gcss-common-test",
    "gcss-common-prod",
    "CMNSVC",
    "CMSVC"
  ],
  "activation_min_hours": 24
}
```

- `common_services_selectors`: Patterns to identify "common services" vs "mission partners" based on Computer Group
- `activation_min_hours`: Minimum cumulative online hours for an instance to be considered "activated"

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

## Recent Critical Fixes (Completed)

1. **Cloud Provider + Service Category Filtering**: Fixed filtering logic to use correct metric splits
2. **Growth Chart Data Consistency**: Fixed cumulative calculation to match overall statistics
3. **Environment Distribution Charts**: Fixed chart rendering for filtered views

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