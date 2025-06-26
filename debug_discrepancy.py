#!/usr/bin/env python3
"""Debug script to find the discrepancy between cloud provider and service category totals."""

import pandas as pd
import json
import os
from pathlib import Path
from modules.analyzer.data_loader import load_and_preprocess_data
from modules.analyzer.metrics_calculator import ACTIVATION_MIN_SECONDS

# Load the data
print("Loading data...")
data_dir = Path('.')  # Root directory where CSV files are
data = load_and_preprocess_data(data_dir)

print(f"\nTotal rows in data: {len(data)}")
print(f"Unique hostnames: {len(data['Hostname'].unique())}")

# Check for instances with modules
activated_mask = data['has_modules'] == True
print(f"\nRows with modules: {activated_mask.sum()}")

# Calculate activated instances using the same logic as metrics_calculator
module_time = data[data['has_modules']].groupby('Hostname')['Duration (Seconds)'].sum()
activated_hosts = set(module_time[module_time >= ACTIVATION_MIN_SECONDS].index)
print(f"\nActivated instances (overall): {len(activated_hosts)}")

# Group by cloud provider
cloud_totals = {}
for cp in data['Cloud_Provider'].unique():
    cp_data = data[data['Cloud_Provider'] == cp]
    cp_module_time = cp_data[cp_data['has_modules']].groupby('Hostname')['Duration (Seconds)'].sum()
    cp_activated = set(cp_module_time[cp_module_time >= ACTIVATION_MIN_SECONDS].index)
    cloud_totals[cp] = len(cp_activated)
    print(f"  {cp}: {len(cp_activated)}")

print(f"\nTotal from cloud providers: {sum(cloud_totals.values())}")

# Group by service category
service_totals = {}
for sc in data['service_category'].unique():
    sc_data = data[data['service_category'] == sc]
    sc_module_time = sc_data[sc_data['has_modules']].groupby('Hostname')['Duration (Seconds)'].sum()
    sc_activated = set(sc_module_time[sc_module_time >= ACTIVATION_MIN_SECONDS].index)
    service_totals[sc] = len(sc_activated)
    print(f"\nService category '{sc}': {len(sc_activated)}")
    
print(f"\nTotal from service categories: {sum(service_totals.values())}")

# Find instances that might be counted differently
print("\n\nAnalyzing potential issues...")

# Check for instances that appear in multiple cloud providers
print("\n1. Checking for instances in multiple cloud providers:")
hostname_to_clouds = {}
for hostname in data['Hostname'].unique():
    host_data = data[data['Hostname'] == hostname]
    clouds = set(host_data['Cloud_Provider'].unique())
    if len(clouds) > 1:
        hostname_to_clouds[hostname] = clouds
        
if hostname_to_clouds:
    print(f"Found {len(hostname_to_clouds)} instances in multiple cloud providers:")
    for hostname, clouds in list(hostname_to_clouds.items())[:5]:
        print(f"  {hostname}: {clouds}")
else:
    print("  No instances found in multiple cloud providers")

# Check for instances that appear in multiple service categories
print("\n2. Checking for instances in multiple service categories:")
hostname_to_categories = {}
for hostname in data['Hostname'].unique():
    host_data = data[data['Hostname'] == hostname]
    categories = set(host_data['service_category'].unique())
    if len(categories) > 1:
        hostname_to_categories[hostname] = categories
        
if hostname_to_categories:
    print(f"Found {len(hostname_to_categories)} instances in multiple service categories:")
    for hostname, categories in list(hostname_to_categories.items())[:5]:
        print(f"  {hostname}: {categories}")
else:
    print("  No instances found in multiple service categories")

# Check if the activated hosts are the same across both calculations
print("\n3. Checking if activated hosts differ between calculations:")

# Recalculate for verification
overall_activated = activated_hosts.copy()

# Calculate all cloud provider activated hosts combined
all_cloud_activated = set()
for cp in data['Cloud_Provider'].unique():
    cp_data = data[data['Cloud_Provider'] == cp]
    cp_module_time = cp_data[cp_data['has_modules']].groupby('Hostname')['Duration (Seconds)'].sum()
    cp_activated = set(cp_module_time[cp_module_time >= ACTIVATION_MIN_SECONDS].index)
    all_cloud_activated.update(cp_activated)

# Calculate all service category activated hosts combined
all_service_activated = set()
for sc in data['service_category'].unique():
    sc_data = data[data['service_category'] == sc]
    sc_module_time = sc_data[sc_data['has_modules']].groupby('Hostname')['Duration (Seconds)'].sum()
    sc_activated = set(sc_module_time[sc_module_time >= ACTIVATION_MIN_SECONDS].index)
    all_service_activated.update(sc_activated)

print(f"\nOverall activated: {len(overall_activated)}")
print(f"Union of cloud provider activated: {len(all_cloud_activated)}")
print(f"Union of service category activated: {len(all_service_activated)}")

# Find differences
only_in_overall = overall_activated - all_cloud_activated
only_in_cloud = all_cloud_activated - overall_activated
only_in_service = all_service_activated - overall_activated

if only_in_overall:
    print(f"\nInstances only in overall but not in cloud providers: {len(only_in_overall)}")
    for hostname in list(only_in_overall)[:5]:
        host_data = data[data['Hostname'] == hostname]
        print(f"  {hostname}: Cloud={host_data['Cloud_Provider'].unique()}")

if only_in_cloud:
    print(f"\nInstances only in cloud providers but not in overall: {len(only_in_cloud)}")
    for hostname in list(only_in_cloud)[:5]:
        host_data = data[data['Hostname'] == hostname]
        print(f"  {hostname}: Cloud={host_data['Cloud_Provider'].unique()}")

if only_in_service:
    print(f"\nInstances only in service categories but not in overall: {len(only_in_service)}")
    for hostname in list(only_in_service)[:5]:
        host_data = data[data['Hostname'] == hostname]
        print(f"  {hostname}: Service={host_data['service_category'].unique()}")

# Compare cloud vs service totals
service_not_cloud = all_service_activated - all_cloud_activated
cloud_not_service = all_cloud_activated - all_service_activated

if service_not_cloud:
    print(f"\n\nInstances in service categories but not in cloud providers: {len(service_not_cloud)}")
    for hostname in list(service_not_cloud)[:10]:
        host_data = data[data['Hostname'] == hostname]
        print(f"  {hostname}:")
        print(f"    Cloud: {host_data['Cloud_Provider'].unique()}")
        print(f"    Service: {host_data['service_category'].unique()}")
        print(f"    Has modules: {host_data['has_modules'].any()}")
        module_seconds = host_data[host_data['has_modules']]['Duration (Seconds)'].sum()
        print(f"    Module seconds: {module_seconds} (threshold: {ACTIVATION_MIN_SECONDS})")

print(f"\nDifference in totals: {len(all_service_activated) - len(all_cloud_activated)} instances")