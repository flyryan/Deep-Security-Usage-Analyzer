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

DSUA aims to provide a clear understanding of module usage patterns by analyzing data exported from Deep Security. It handles large datasets by deduplicating files and entries, ensuring accurate and efficient analysis. It generates various reports, including metrics summaries, visualizations, and comprehensive, single-file, HTML and PDF reports to present the analysis results effectively.

## Prerequisites

- Python 3.7 or higher
- Required Python packages:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - jinja2
  - reportlab

Install the necessary packages using:

```bash
pip install -r requirements.txt
```

## Features

- **Comprehensive Analysis:** DSUA processes usage data from multiple environments at the same time and generates detailed reports.
- **Deduplication:** Automatically removes duplicate files and entries, ensuring accurate analysis without redundancy. This feature allows you to dump in any and every usage report you have without having to worry about overlapping or duplicate data.
- **Environment Classification:** Classifies data entries into environments like Production, Development, Test, etc., based on hostname and IP patterns.
- **Module Usage Metrics:** Calculates usage metrics for various Deep Security modules, providing insights into their utilization.
- **Visualizations:** Generates visual representations of module usage and environment distribution.
- **HTML and PDF Reports:** Creates comprehensive reports in both HTML and PDF formats for easy sharing and review.
- **Error Handling:** Robust error handling and logging to ensure smooth execution and easy troubleshooting.
- **Customizable:** Adjustable parameters for environment patterns and module definitions to fit specific needs.

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

## Detailed Workflow

The DSUA script performs a comprehensive analysis of Trend Micro Deep Security module usage. Below is a step-by-step walkthrough of the entire process, detailing the logic behind each decision to facilitate auditing.

### 1. Data Collection

- **Input Directory Scanning:**
  - The script scans a specified input directory for data files.
  - **Valid File Types:** Only files with extensions `.csv`, `.xlsx`, or `.xls` are considered to ensure compatibility.
- **File Handling:**
  - Each valid file is read and loaded into a data structure for processing.
  - **Error Handling:** Files that cannot be read (due to corruption or unsupported formats) are logged and skipped.

### 2. File Deduplication (Optional but Recommended)

- **Purpose:** To eliminate duplicate files that may contain redundant data.
- **Method:**
  - Calculates the SHA-256 hash for each file in the input directory.
  - Compares hash values to identify identical files.
- **Outcome:**
  - Duplicate files are removed, reducing processing time and avoiding duplicate data entries.

### 3. Data Merging and Entry Deduplication

- **Data Concatenation:**
  - All individual data files are merged into a single dataset.
- **Entry Deduplication Logic:**
  - **Criteria:** Duplicate rows are identified based on a unique combination of all columns.
  - **Process:**
    - Sorts the data to group potential duplicates together.
    - Uses a defined key to compare rows and remove duplicates.
- **Standardization:**
  - Data fields are standardized (e.g., trimming whitespace, standardizing case) to ensure consistent comparison.

### 4. Environment Classification

- **Objective:** To categorize entries into environments like Production, Development, etc.
- **Logic:**
  - **Hostname and IP Analysis:**
    - Hostnames and IP addresses are matched against predefined patterns for each environment.
  - **Patterns Used:**
    - **Production:** Keywords like `prod`, `production`, patterns like `prd\d+`.
    - **Development:** Keywords like `dev`, `development`, patterns like `dev\d+`.
    - **Other Environments:** Similar patterns for Test, Staging, DR, UAT, Integration.
  - **Domain Patterns:**
    - Recognizes internal domains (e.g., `.internal`, `.local`) and DMZ configurations.
- **Assignment:**
  - Each entry is assigned an environment tag based on the first matching pattern.
  - **Unclassified Entries:**
    - Entries that do not match any pattern are labeled as `Unknown`.

### 5. Module Usage Analysis

- **Modules Analyzed:**
  - Anti-Malware (AM), Web Reputation Service (WRS), Deep Packet Inspection (DPI), Firewall (FW), etc.
- **Usage Calculation:**
  - **Binary Indicators:**
    - Each module usage is represented as a binary value (e.g., `1` for enabled, `0` for disabled).
  - **Aggregation:**
    - Totals are calculated by summing the binary values across all entries.
- **Percentage Utilization:**
  - **Formula:**
    - Percentage for each module = (Total Enabled Instances / Total Instances) * 100%
  - **Environment-Specific Metrics:**
    - Calculations are performed separately for each environment to provide granular insights.

### 6. Reporting and Visualization

- **Metric Generation:**
  - Key statistics are compiled, such as total number of instances per environment, module usage counts, and percentages. (See [Metric Calculation Logic](#metric-calculation-logic))

- **Visualization:**
  - Graphs and charts are created to visually represent module usage across environments.
  - **Tools Used:**
    - Visualization libraries (e.g., Matplotlib, Seaborn) generate bar charts, pie charts, etc.
- **HTML Report Creation:**
  - **Template Rendering:**
    - An HTML template is populated with the calculated metrics and visualizations.
  - **Report Contents:**
    - Summary of findings.
    - Interactive charts and graphs.
    - Detailed tables with drill-down capability.
- **PDF Report Creation:**
  - **Template Rendering:**
    - A PDF template is populated with the calculated metrics and visualizations.
  - **Report Contents:**
    - Summary of findings.
    - Interactive charts and graphs.
    - Detailed tables with drill-down capability.
- **Output:**
  - The final report is saved as `deep_security_usage_report.html` and `deep_security_usage_report.pdf` for easy sharing and review.

### 7. Logging and Audit Trail

- **Logging Mechanism:**
  - The script maintains detailed logs of its operations.
  - **Levels:**
    - **INFO:** General process updates.
    - **DEBUG:** Detailed information useful for diagnosing issues.
    - **ERROR:** Records any errors encountered during execution.
- **Log Files:**
  - Logs are written to security_analysis.log, providing a time-stamped record of the script's activities.
- **Purpose for Auditing:**
  - Enables auditors to trace the script's execution flow.
  - Assists in verifying that all steps were performed correctly.

### 8. Error Handling and Validation

- **Data Validation:**
  - Checks for missing or inconsistent data in critical fields.
  - **Actions:**
    - Invalid entries are logged and excluded from analysis.
- **Exception Handling:**
  - The script captures and logs exceptions without terminating unexpectedly.
  - Provides informative messages to facilitate troubleshooting.

### 9. Configuration and Customization

- **Adjustable Parameters:**
  - **Environment Patterns:** Can be modified to match specific naming conventions.
  - **Module Definitions:** Ability to update which modules are analyzed.
- **Usage Instructions:**
  - Parameters can be set via command-line arguments or a configuration file.

### Metric Calculation Logic

- **Total Number of Instances per Environment:**
  - We aggregate the total number of instances by summing up the `active_instances` and `inactive_instances` for each environment.
  - Example:

    ### Metric Calculation Logic

    The determination of active and inactive instances is based on the status and activity logs of each instance. Here’s how DSUA differentiates between them:

  - **Active Instances:**
    - Instances that are currently running and providing services.
    - Identified by checking the latest status logs and ensuring the instance is marked as active.
    - Instances with recent activity logs indicating ongoing operations.

  - **Inactive Instances:**
    - Instances that are not currently running or providing services.
    - Identified by checking the latest status logs and finding the instance marked as inactive or stopped.
    - Instances with no recent activity logs or logs indicating the instance has been shut down.

    The script processes the status and activity logs to classify each instance accurately. This classification helps in understanding the current utilization and availability of resources.

  - **Total Number of Instances per Environment:**
    - We aggregate the total number of instances by summing up the `active_instances` and `inactive_instances` for each environment.
    - Example:
      ```json
      "Development": {
        "active_instances": 6142,
        "inactive_instances": 106,
        "total_instances": 6218
      }
    ```json
    "Development": {
      "active_instances": 6142,
      "inactive_instances": 106,
      "total_instances": 6218
    }
    ```

- **Module Usage Counts:**
  - We count the number of instances where each module is enabled. This is done by summing the binary indicators (1 for enabled, 0 for disabled) for each module across all instances.
  - Example:
    ```json
    "module_usage": {
      "AM": 22519.0,
      "WRS": 69.0,
      "DC": 0.0,
      "AC": 4.0,
      "IM": 10057.0,
     
        ``` "LI": 8976.0,
      "FW": 628.0,
      "DPI": 22076.0,
      "SAP": 0.0
    }
    ```

- **Module Usage Percentages:**
    - We calculate the percentage of instances using each module by dividing the module usage count by the total number of instances and multiplying by 100.
    - Formula: `Percentage = (Module Usage Count / Total Instances) * 100`
    - Example:
        ```json
        "module_usage_percentage": {
            "AM": 36.22,
            "WRS": 0.69,
            "DC": 0.0,
            "AC": 0.04,
            "IM": 16.18,
            "LI": 14.52,
            "FW": 1.02,
            "DPI": 35.52,
            "SAP": 0.0
        }
        ```

- **Most Common Module:**
  - We determine the most common module by identifying the module with the highest usage count.
  - Example:
    ```json
    "most_common_module": "AM"
    ```

- **Average Modules per Host:**
  - We calculate the average number of modules enabled per host by dividing the total module usage count by the total number of instances.
  - Example:
    ```json
    "avg_modules_per_host": 2.4001286587327115
    ```

- **Max Concurrent Instances:**
    - We identify the maximum number of instances that were active concurrently.
    - **Method:**
        - The script processes the start and stop times of each instance to determine periods of activity.
        - It creates a timeline of events, marking the start and stop of each instance.
        - By iterating through this timeline, the script calculates the number of active instances at any given time.
        - The maximum value encountered during this iteration is recorded as the maximum concurrent instances.
    - Example:
        ```json
        "max_concurrent": 117
        ```

- **Total Utilization Hours:**
  - We sum the total utilization hours for all instances.
  - Example:
    ```json
    "total_utilization_hours": 17774512.72833333
    ```

These calculations are performed using the data extracted from the various CSV and JSON files, as detailed in the earlier steps.

## Output

After running DSUA, the following outputs are generated in the `output` directory:

- `report.html`: A comprehensive report detailing the analysis.
- `report.pdf`: A PDF version of the comprehensive report.
- `metrics.json`: A JSON file containing all calculated metrics.
- `processed_data.csv`: The cleaned and combined dataset used for analysis.
- Visualization images (e.g., `module_usage.png`, `environment_distribution.png`).

## Contributing

Contributions to improve DSUA are welcome. Please submit a pull request or open an issue on GitHub with your suggestions.