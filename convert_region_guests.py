#!/usr/bin/env python3
"""
Region-Based Guest Account Converter
====================================
Different regions ke guest accounts ko convert aur manage karta hai

Usage:
    python convert_region_guests.py <input_file> <region>
    
Example:
    python convert_region_guests.py BD_ACC.json BD
"""

import json
import sys
import os

def convert_region_guests(input_file, region):
    """
    Guest accounts ko region-specific format mein convert karta hai
    
    Args:
        input_file: Input JSON file path
        region: Region code (BD, IND, BR, US, etc.)
    """
    # Output directory
    output_dir = "guests_manager/region_based"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load input file
    try:
        with open(input_file, 'r') as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Convert to standard format
    converted_guests = []
    total_count = 0
    
    for item in raw_data:
        if "guest_account_info" in item:
            info = item["guest_account_info"]
            uid = info.get("com.garena.msdk.guest_uid")
            password = info.get("com.garena.msdk.guest_password")
            
            if uid and password:
                converted_guests.append({
                    "uid": uid,
                    "password": password,
                    "region": region.upper()
                })
                total_count += 1
    
    # Save region-specific file
    output_file = os.path.join(output_dir, f"{region.upper()}_guests.json")
    with open(output_file, 'w') as f:
        json.dump(converted_guests, f, indent=2)
    
    print(f"✅ Successfully converted {total_count} {region.upper()} guest accounts!")
    print(f"📁 Saved to: {output_file}")
    
    # Update master region list
    update_region_list(region.upper(), total_count)

def update_region_list(region, count):
    """Master region list ko update karta hai"""
    region_list_file = "guests_manager/region_based/regions.json"
    
    if os.path.exists(region_list_file):
        with open(region_list_file, 'r') as f:
            regions = json.load(f)
    else:
        regions = {}
    
    regions[region] = {
        "count": count,
        "file": f"{region}_guests.json"
    }
    
    with open(region_list_file, 'w') as f:
        json.dump(regions, f, indent=2)
    
    print(f"📋 Updated region list: {region} ({count} accounts)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_region_guests.py <input_file> <region>")
        print("\nExamples:")
        print("  python convert_region_guests.py BD_ACC.json BD")
        print("  python convert_region_guests.py IND_ACC.json IND")
        print("  python convert_region_guests.py BR_ACC.json BR")
        sys.exit(1)
    
    input_file = sys.argv[1]
    region = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    convert_region_guests(input_file, region)
