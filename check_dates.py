#!/usr/bin/env python3
import pandas as pd
import glob
import os
from datetime import datetime

def extract_date_range(file_path):
    try:
        df = pd.read_csv(file_path, nrows=100)

        date_columns = []
        for col in df.columns:
            if 'date' in col.lower() and 'time' not in col.lower():
                date_columns.append(col)

        # Look for specific date column patterns
        if 'Start Date' in df.columns and 'Stop Date' in df.columns:
            date_columns = ['Start Date', 'Stop Date']
        elif 'Date From' in df.columns and 'Date To' in df.columns:
            date_columns = ['Date From', 'Date To']

        if not date_columns and len(df.columns) > 8:
            for i in range(min(20, len(df.columns))):
                sample = df.iloc[0, i] if len(df) > 0 else None
                if sample and isinstance(sample, str):
                    if '/' in str(sample) and len(str(sample).split('/')) == 3:
                        date_columns.append(df.columns[i])

        dates = []
        for col in date_columns:
            try:
                col_data = pd.to_datetime(df[col], errors='coerce')
                if not col_data.isna().all():
                    dates.extend(col_data.dropna().tolist())
            except:
                pass

        if dates:
            return min(dates), max(dates)
        return None, None
    except Exception as e:
        return None, None

csv_files = glob.glob('*.csv')
results = []

print(f"Analyzing {len(csv_files)} CSV files...\n")

for file in csv_files:
    start_date, end_date = extract_date_range(file)
    if start_date and end_date:
        results.append({
            'file': file,
            'start': start_date,
            'end': end_date,
            'end_month': end_date.month,
            'end_year': end_date.year
        })

august_files = [r for r in results if r['end_month'] == 8 and r['end_year'] == 2025]
august_files.sort(key=lambda x: x['end'])

september_files = [r for r in results if r['end_month'] == 9 and r['end_year'] == 2025]
september_files.sort(key=lambda x: x['end'])

print("Files ending in August 2025:")
print("=" * 80)
for r in august_files:
    has_sep = 'sep' in r['file'].lower() or 'september' in r['file'].lower()
    marker = " <- WARNING: Has 'Sep/September' in filename!" if has_sep else ""
    print(f"{r['file']:<60} Ends: {r['end'].strftime('%Y-%m-%d')}{marker}")

print("\nFiles ending in September 2025:")
print("=" * 80)
for r in september_files:
    print(f"{r['file']:<60} Ends: {r['end'].strftime('%Y-%m-%d')}")

all_relevant = august_files + september_files
if all_relevant:
    print("\n" + "=" * 80)
    earliest_end = min(r['end'] for r in all_relevant)
    print(f"\nEarliest ending date among August/September files: {earliest_end.strftime('%Y-%m-%d')}")

    in_month = "August" if earliest_end.month == 8 else "September"
    print(f"This date is in {in_month} 2025")
    print(f"\n>>> You should restrict your report to data up to: {earliest_end.strftime('%Y-%m-%d')} <<<")

    print(f"\nAll files with this earliest ending date ({earliest_end.strftime('%Y-%m-%d')}):")
    for r in all_relevant:
        if r['end'] == earliest_end:
            print(f"  - {r['file']}")