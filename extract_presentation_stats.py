#!/usr/bin/env python3
"""
Extract presentation statistics from metrics.json file
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

def load_metrics(file_path):
    """Load metrics from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def extract_stats(metrics):
    """Extract and print all requested statistics"""
    
    # 1. Distribution across clouds
    print_section("DISTRIBUTION ACROSS CLOUDS (Activated Instances)")
    cloud_dist = metrics['overall']['cloud_provider_distribution']
    total_activated = sum(cloud_dist.values())
    
    for cloud, count in sorted(cloud_dist.items()):
        percentage = (count / total_activated * 100) if total_activated > 0 else 0
        print(f"{cloud}: {count:,} ({percentage:.1f}%)")
    print(f"\nTotal Activated Instances: {total_activated:,}")
    
    # 2. Distribution between common services and mission partners
    print_section("DISTRIBUTION: COMMON SERVICES vs MISSION PARTNERS")
    
    # Check by_service_category first
    if 'by_service_category' in metrics:
        service_cats = metrics['by_service_category']
        
        # Look for activated instances in the overall section
        cs_activated = 0
        mp_activated = 0
        
        if 'common services' in service_cats and 'overall' in service_cats['common services']:
            cs_activated = service_cats['common services']['overall'].get('activated_instances', 0)
        
        if 'mission partners' in service_cats and 'overall' in service_cats['mission partners']:
            mp_activated = service_cats['mission partners']['overall'].get('activated_instances', 0)
        
        total_service = cs_activated + mp_activated
        
        if total_service > 0:
            cs_pct = (cs_activated / total_service * 100)
            mp_pct = (mp_activated / total_service * 100)
            print(f"Common Services: {cs_activated:,} ({cs_pct:.1f}%)")
            print(f"Mission Partners: {mp_activated:,} ({mp_pct:.1f}%)")
            print(f"\nTotal: {total_service:,}")
        else:
            print("No service category data available")
    else:
        print("No service category data available")
    
    # 3. Month-by-month growth stats
    print_section("MONTHLY GROWTH STATISTICS")
    
    # Get months from the top-level monthly data
    if 'monthly' in metrics and 'data' in metrics['monthly']:
        monthly_data = metrics['monthly']['data']
        
        # Combined view
        print("\nCOMBINED (All Clouds):")
        print("Month\t\tActivated Instances\tCumulative Total")
        print("-" * 60)
        
        combined_totals = []
        cumulative_total = 0
        for month_entry in monthly_data:
            month = month_entry['month']
            count = month_entry['activated_instances']
            cumulative_total = count  # The activated_instances is already cumulative
            combined_totals.append((month, count))
            print(f"{month}\t{count:,}\t\t{cumulative_total:,}")
        
        # Calculate growth
        if len(combined_totals) > 1:
            print("\nMonth-over-month growth:")
            for i in range(1, len(combined_totals)):
                growth = combined_totals[i][1] - combined_totals[i-1][1]
                growth_pct = (growth / combined_totals[i-1][1] * 100) if combined_totals[i-1][1] > 0 else 0
                print(f"{combined_totals[i][0]}: {growth:+,} ({growth_pct:+.1f}%)")
    
    # Per cloud provider - extract from by_cloud_provider section
    cloud_providers = ['AWS', 'Azure', 'GCP', 'OCI']
    
    if 'by_cloud_provider' in metrics:
        for cloud in cloud_providers:
            if cloud in metrics['by_cloud_provider'] and 'monthly' in metrics['by_cloud_provider'][cloud]:
                print(f"\n{cloud}:")
                print("Month\t\tActivated Instances\tCumulative Total")
                print("-" * 60)
                
                monthly_data = metrics['by_cloud_provider'][cloud]['monthly'].get('data', [])
                cloud_totals = []
                
                for month_entry in monthly_data:
                    month = month_entry['month']
                    count = month_entry['activated_instances']
                    cloud_totals.append((month, count))
                    print(f"{month}\t{count:,}\t\t{count:,}")
                
                # Calculate growth for this cloud
                if len(cloud_totals) > 1:
                    print(f"\n{cloud} Month-over-month growth:")
                    for i in range(1, len(cloud_totals)):
                        growth = cloud_totals[i][1] - cloud_totals[i-1][1]
                        growth_pct = (growth / cloud_totals[i-1][1] * 100) if cloud_totals[i-1][1] > 0 else 0
                        print(f"{cloud_totals[i][0]}: {growth:+,} ({growth_pct:+.1f}%)")
            else:
                print(f"\n{cloud}:")
                print("No monthly data available for this cloud provider")
    
    # 4. Total DSMs count and host breakdown
    print_section("TOTAL DSMs AND HOSTS IN DATA")
    
    # Count files to determine DSMs
    import glob
    # Look for CSV and Excel files with cloud provider names
    csv_files = glob.glob("*.csv")
    excel_files = glob.glob("*.xlsx")
    data_files = [f for f in csv_files + excel_files if any(cloud in f for cloud in ['AWS', 'Azure', 'GCP', 'OCI'])]
    dsm_count = len(data_files)
    
    print(f"Total data files processed: {dsm_count}")
    print(f"(Multiple files may come from the same DSM for different time periods)")
    print(f"Note: The actual number of unique DSMs cannot be determined from the data alone")
    
    # Count unique hosts across all environments
    total_unique_hosts = 0
    
    # Try to get from overall stats first
    if 'overall' in metrics:
        if 'total_instances' in metrics['overall']:
            total_unique_hosts = metrics['overall']['total_instances']
            print(f"\nTotal unique hosts/instances in dataset: {total_unique_hosts:,}")
    
    # Also show breakdown by environment if available
    if 'by_environment' in metrics:
        print("\nHost/instance breakdown by environment:")
        env_total = 0
        for env, data in sorted(metrics['by_environment'].items()):
            if isinstance(data, dict) and 'total_instances' in data:
                count = data['total_instances']
                env_total += count
                print(f"  {env}: {count:,}")
        
        if env_total > 0 and total_unique_hosts == 0:
            print(f"\nTotal across environments: {env_total:,}")
            print("(Note: This may include duplicates if hosts appear in multiple environments)")

def main():
    # Default to output/metrics.json
    metrics_file = Path("output/metrics.json")
    
    if len(sys.argv) > 1:
        metrics_file = Path(sys.argv[1])
    
    if not metrics_file.exists():
        print(f"Error: Metrics file not found: {metrics_file}")
        sys.exit(1)
    
    print(f"Loading metrics from: {metrics_file}")
    
    try:
        metrics = load_metrics(metrics_file)
        extract_stats(metrics)
        
        print("\n" + "="*60)
        print("Stats extraction complete!")
        print("="*60)
        
    except Exception as e:
        print(f"Error processing metrics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()