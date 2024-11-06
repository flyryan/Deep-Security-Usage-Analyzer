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
- [License](#license)

## Overview

DSUA aims to provide a clear understanding of module usage patterns by analyzing data exported from Deep Security. It handles large datasets by deduplicating files and entries, ensuring accurate and efficient analysis.

## Prerequisites

- Python 3.7 or higher
- Required Python packages:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - jinja2

Install the necessary packages using:

```bash
pip install -r requirements.txt
```

## Deduplication Process

The deduplication process is a critical step to ensure efficiency and accuracy:

1. **File Deduplication (Optional but Recommended):**
   - Use the provided `dedupe.py` script to remove duplicate files in the input directory.
   - This can significantly reduce processing time, especially with large datasets.
   - The script removes duplicate files based on their SHA-256 hash values.

2. **Entry Deduplication:**
   - DSUA also performs deduplication of individual entries within the data files.
   - It combines data from all files, removes duplicate rows, and standardizes the data for analysis.

By performing file deduplication first using `dedupe.py`, you can expedite the analysis, but DSUA will handle duplicate entries regardless.

## Usage

1. **Prepare Data:**
   - Place all usage data files (`.csv`, `.xlsx`, or `.xls`) exported from Deep Security into the input directory.
   - Ensure the input directory contains only the files you wish to analyze.

2. **Run File Deduplication (Optional but Recommended):**

   ```bash
   python dedupe.py
   ```

   - Run the script in the directory containing your data files.
   - The script will scan for duplicate files and remove them automatically.
   - **Note:** It's advisable to backup your data before running the script.

3. **Run DSUA:**

   ```bash
   python DSUA.py
   ```

   - The script will automatically detect and process all valid files in the input directory.
   - It creates an `output` directory to store the generated reports and visualizations.

## Workflow

The DSUA script follows these key steps to analyze the data:

1. **Initialization:**
   - Sets up the input and output directories.
   - Checks for valid input files to process.

2. **Data Loading and Preprocessing:**
   - Loads data from all valid files in the input directory.
   - Standardizes column names and handles date parsing.
   - Combines data into a single DataFrame.
   - Removes duplicate entries to ensure data integrity.

3. **Environment Classification:**
   - Classifies each hostname into environments (e.g., Production, Development) based on predefined patterns.
   - Unknown environments are flagged for further analysis.

4. **Metric Calculation:**
   - Calculates usage metrics across different environments and modules.
   - Determines active and inactive instances.
   - Computes module usage percentages and identifies the most common modules.
   - Generates correlation matrices for module usage.

5. **Enhanced Metrics and Trends:**
   - Calculates enhanced metrics such as maximum concurrent instances and utilization hours.
   - Analyzes monthly trends and patterns in module usage.

6. **Visualization:**
   - Generates visualizations like bar charts and pie charts to represent module usage and environment distribution.
   - Saves visualizations in the `output` directory.

7. **Report Generation:**
   - Compiles all metrics and visualizations into a comprehensive HTML report.
   - Highlights key findings and provides an accessible summary of the analysis.

8. **Output:**
   - Saves the HTML report, metrics JSON, and processed data CSV in the `output` directory.
   - Provides console output summarizing the analysis process and results.

## Output

After running DSUA, the following outputs are generated in the `output` directory:

- `report.html`: A comprehensive report detailing the analysis.
- `metrics.json`: A JSON file containing all calculated metrics.
- `processed_data.csv`: The cleaned and combined dataset used for analysis.
- Visualization images (e.g., `module_usage.png`, `environment_distribution.png`).

## Contributing

Contributions to improve DSUA are welcome. Please submit a pull request or open an issue on GitHub with your suggestions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.