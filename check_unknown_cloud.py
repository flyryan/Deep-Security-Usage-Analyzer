#!/usr/bin/env python3
"""Quick check for Unknown cloud providers in the current run."""

import json
import os

# Check if Unknown exists in the JSON structure somewhere
with open('output/metrics.json', 'r') as f:
    metrics = json.load(f)

# Search for "Unknown" in all cloud provider keys
def find_unknown_in_dict(d, path=""):
    found = []
    if isinstance(d, dict):
        for k, v in d.items():
            if "Unknown" in str(k):
                found.append(f"{path}.{k}")
            if isinstance(v, dict):
                found.extend(find_unknown_in_dict(v, f"{path}.{k}"))
    return found

unknown_paths = find_unknown_in_dict(metrics)
if unknown_paths:
    print("Found 'Unknown' in these paths:")
    for path in unknown_paths:
        print(f"  {path}")
else:
    print("No 'Unknown' found in metrics.json")

# Check specific locations
print("\n" + "="*50)
print("\nChecking specific locations:")

# Check by_cloud_provider
if 'Unknown' in metrics.get('by_cloud_provider', {}):
    unknown_data = metrics['by_cloud_provider']['Unknown']
    print(f"\nFound Unknown in by_cloud_provider:")
    print(f"  Activated instances: {unknown_data.get('activated_instances', 0)}")
    print(f"  Total instances: {unknown_data.get('total_instances', 0)}")

# Check by_service_category_and_cloud_provider
for key in metrics.get('by_service_category_and_cloud_provider', {}):
    if 'Unknown' in key:
        data = metrics['by_service_category_and_cloud_provider'][key]
        print(f"\nFound {key}:")
        print(f"  Activated instances: {data.get('activated_instances', 0)}")

# Check by_cloud_and_environment
for key in metrics.get('by_cloud_and_environment', {}):
    if 'Unknown' in key:
        data = metrics['by_cloud_and_environment'][key]
        print(f"\nFound {key}:")
        print(f"  Activated instances: {data.get('activated_instances', 0)}")

# Calculate what the cloud provider total SHOULD be if Unknown were included
print("\n" + "="*50)
print("\nCalculating expected totals:")

# Sum all by_cloud_provider activated instances (including any that might be filtered)
all_cloud_total = 0
for cp, data in metrics.get('by_cloud_provider', {}).items():
    count = data.get('activated_instances', 0)
    all_cloud_total += count
    print(f"  {cp}: {count}")

print(f"\nTotal from ALL cloud providers in by_cloud_provider: {all_cloud_total}")
print(f"Total from cloud_provider_distribution: {sum(metrics['overall']['cloud_provider_distribution'].values())}")
print(f"Difference: {all_cloud_total - sum(metrics['overall']['cloud_provider_distribution'].values())}")