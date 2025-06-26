#!/usr/bin/env python3
"""Check the discrepancy in metrics.json between cloud provider and service category totals."""

import json

# Load metrics
with open('output/metrics.json', 'r') as f:
    metrics = json.load(f)

# Get overall metrics
overall = metrics['overall']
by_cloud = metrics['by_cloud_provider']
by_service = metrics['by_service_category']

# Check cloud provider distribution
print("Cloud Provider Distribution:")
cloud_total = 0
for provider, count in overall['cloud_provider_distribution'].items():
    print(f"  {provider}: {count}")
    cloud_total += count
print(f"Total from cloud providers: {cloud_total}")
print(f"Overall activated instances: {overall['activated_instances']}")
print(f"Match: {cloud_total == overall['activated_instances']}")

print("\n" + "="*50 + "\n")

# Check service category totals
print("Service Category Distribution:")
service_total = 0
for category in ['common services', 'mission partners']:
    if category in by_service:
        activated = by_service[category]['overall']['activated_instances']
        print(f"  {category}: {activated}")
        service_total += activated
print(f"Total from service categories: {service_total}")

print("\n" + "="*50 + "\n")

# Compare totals
print(f"Discrepancy: {service_total} - {cloud_total} = {service_total - cloud_total} instances")

# Check if there are any other service categories
print("\nAll service categories in metrics:")
for category in by_service.keys():
    print(f"  - {category}")

# Check individual cloud providers vs service categories
print("\n" + "="*50 + "\n")
print("Checking by_service_category_and_cloud_provider splits:")

# Get all service category + cloud provider combinations
sc_cp_metrics = metrics.get('by_service_category_and_cloud_provider', {})
sc_cp_total = 0
for key, data in sc_cp_metrics.items():
    activated = data.get('activated_instances', 0)
    print(f"  {key}: {activated}")
    sc_cp_total += activated
    
print(f"\nTotal from service_category + cloud_provider splits: {sc_cp_total}")

# Check if the sum of cloud providers equals the overall for each service category
print("\n" + "="*50 + "\n")
print("Checking if cloud provider splits sum correctly for each service category:")

for category in ['common services', 'mission partners']:
    cat_total = by_service[category]['overall']['activated_instances']
    cat_cloud_sum = 0
    print(f"\n{category}:")
    print(f"  Overall: {cat_total}")
    
    for cp in ['AWS', 'Azure', 'GCP', 'OCI']:
        key = f"{category}::{cp}"
        if key in sc_cp_metrics:
            count = sc_cp_metrics[key]['activated_instances']
            cat_cloud_sum += count
            print(f"  {cp}: {count}")
    
    print(f"  Sum of cloud providers: {cat_cloud_sum}")
    print(f"  Match: {cat_cloud_sum == cat_total}")
    if cat_cloud_sum != cat_total:
        print(f"  MISMATCH: Difference = {cat_total - cat_cloud_sum}")

# Look for Unknown cloud provider
print("\n" + "="*50 + "\n")
print("Checking for 'Unknown' cloud provider:")
if 'Unknown' in by_cloud:
    unknown_count = by_cloud['Unknown']['activated_instances']
    print(f"Found Unknown cloud provider with {unknown_count} activated instances")
    
    # Check if Unknown appears in service category splits
    for category in ['common services', 'mission partners']:
        key = f"{category}::Unknown"
        if key in sc_cp_metrics:
            cat_unknown = sc_cp_metrics[key]['activated_instances']
            print(f"  {category} has {cat_unknown} Unknown instances")
else:
    print("No 'Unknown' cloud provider found in by_cloud_provider")