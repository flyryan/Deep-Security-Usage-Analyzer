#!/usr/bin/env python3
"""Find instances that might be duplicated across service categories."""

import pandas as pd
from pathlib import Path
from modules.analyzer.data_loader import load_and_preprocess_data
from modules.analyzer.metrics_calculator import ACTIVATION_MIN_SECONDS
from collections import defaultdict

print("Loading data...")
data_dir = Path('.')
data = load_and_preprocess_data(data_dir)

print(f"\nTotal rows: {len(data)}")
print(f"Unique hostnames: {len(data['Hostname'].unique())}")

# Check for hostnames that appear in multiple service categories
hostname_categories = defaultdict(set)
for _, row in data.iterrows():
    hostname_categories[row['Hostname']].add(row['service_category'])

# Find hostnames in multiple categories
multi_category_hosts = {h: cats for h, cats in hostname_categories.items() if len(cats) > 1}

if multi_category_hosts:
    print(f"\nFound {len(multi_category_hosts)} hostnames in multiple service categories:")
    for hostname, categories in list(multi_category_hosts.items())[:10]:
        print(f"  {hostname}: {categories}")
        # Show some records for this hostname
        host_data = data[data['Hostname'] == hostname][['Hostname', 'service_category', 'Computer Group', 'Cloud_Provider']].drop_duplicates()
        for _, row in host_data.head(3).iterrows():
            print(f"    -> Category: {row['service_category']}, Group: {row['Computer Group']}, Cloud: {row['Cloud_Provider']}")
else:
    print("\nNo hostnames found in multiple service categories")

# Calculate activated instances for each category and check for duplicates
print("\n" + "="*50)
print("\nCalculating activated instances by service category:")

common_activated = set()
mission_activated = set()

# Common services
cs_data = data[data['service_category'] == 'common services']
if not cs_data.empty:
    cs_module_data = cs_data[cs_data['has_modules']]
    cs_module_time = cs_module_data.groupby('Hostname')['Duration (Seconds)'].sum()
    common_activated = set(cs_module_time[cs_module_time >= ACTIVATION_MIN_SECONDS].index)
    print(f"\nCommon services activated: {len(common_activated)}")

# Mission partners
mp_data = data[data['service_category'] == 'mission partners']
if not mp_data.empty:
    mp_module_data = mp_data[mp_data['has_modules']]
    mp_module_time = mp_module_data.groupby('Hostname')['Duration (Seconds)'].sum()
    mission_activated = set(mp_module_time[mp_module_time >= ACTIVATION_MIN_SECONDS].index)
    print(f"Mission partners activated: {len(mission_activated)}")

# Check for overlap
overlap = common_activated & mission_activated
if overlap:
    print(f"\nFound {len(overlap)} activated instances in BOTH categories:")
    for hostname in list(overlap)[:10]:
        print(f"  {hostname}")
        # Show details
        host_data = data[data['Hostname'] == hostname]
        categories = host_data['service_category'].unique()
        groups = host_data['Computer Group'].unique()
        print(f"    Categories: {categories}")
        print(f"    Computer Groups: {groups[:5]}...")  # Show first 5

# Calculate overall activated (should match metrics.json)
all_module_data = data[data['has_modules']]
all_module_time = all_module_data.groupby('Hostname')['Duration (Seconds)'].sum()
all_activated = set(all_module_time[all_module_time >= ACTIVATION_MIN_SECONDS].index)

print(f"\n" + "="*50)
print(f"\nOverall activated: {len(all_activated)}")
print(f"Sum of categories: {len(common_activated) + len(mission_activated)}")
print(f"Union of categories: {len(common_activated | mission_activated)}")
print(f"Overlap count: {len(overlap)}")
print(f"\nExpected discrepancy: {len(common_activated) + len(mission_activated) - len(all_activated)}")

# Verify the math
if len(overlap) > 0:
    print(f"\nThe {len(overlap)} overlapping instances are being counted twice in the service category totals,")