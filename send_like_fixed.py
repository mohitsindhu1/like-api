#!/usr/bin/env python3
"""
Fixed Like Sender with Proper Region Support and Auto-Detection
"""

import httpx
import asyncio
import binascii
import json
import os
import time
from get_jwt import create_jwt
from encrypt_like_body import create_like_payload
from count_likes import detect_uid_region, GetAccountInformation

# Paths
usage_dir = "usage_history"
usage_file = os.path.join(usage_dir, "guest_usage_by_target.json")
region_dir = "guests_manager/region_based"

os.makedirs(usage_dir, exist_ok=True)

# Load usage file
if os.path.exists(usage_file):
    with open(usage_file, "r") as f:
        usage_by_target = json.load(f)
else:
    usage_by_target = {}

def ensure_target(target_uid: str):
    if target_uid not in usage_by_target:
        usage_by_target[target_uid] = {"used_guests": {}, "total_likes": 0}

def guest_used_for_target(target_uid: str, guest_uid: str) -> bool:
    ensure_target(target_uid)
    return guest_uid in usage_by_target[target_uid]["used_guests"]

def mark_used(target_uid: str, guest_uid: str, ts_ms: int):
    ensure_target(target_uid)
    usage_by_target[target_uid]["used_guests"][guest_uid] = ts_ms
    usage_by_target[target_uid]["total_likes"] = len(usage_by_target[target_uid]["used_guests"])

def save_usage():
    with open(usage_file, "w") as f:
        json.dump(usage_by_target, f, indent=2)

def get_available_regions():
    """Available regions list"""
    region_file = os.path.join(region_dir, "regions.json")
    if os.path.exists(region_file):
        with open(region_file, 'r') as f:
            return json.load(f)
    return {}

def load_region_guests(region: str):
    """Load specific region guests"""
    guest_file = os.path.join(region_dir, f"{region.upper()}_guests.json")
    if os.path.exists(guest_file):
        with open(guest_file, 'r') as f:
            return json.load(f)
    return []

def get_base_url(region: str) -> str:
    """Get server URL based on region"""
    region = region.upper()
    if region == "IND":
        return "https://client.ind.freefiremobile.com"
    elif region in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com"
    elif region == "BD":
        return "https://client.bd.freefiremobile.com"
    elif region == "SG":
        return "https://client.sg.freefiremobile.com"
    else:
        return "https://clientbp.ggblueshark.com"

async def like_with_guest(guest: dict, target_uid: str, semaphore) -> bool:
    guest_uid = str(guest["uid"])
    guest_pass = guest["password"]
    guest_region = guest.get("region", "IND")
    now_ms = int(time.time() * 1000)
    
    if guest_used_for_target(target_uid, guest_uid):
        return False
    
    async with semaphore:
        try:
            # Get JWT
            jwt, jwt_region, server_url_from_jwt = await create_jwt(guest_uid, guest_pass)
            
            # Use guest's region for correct server
            if server_url_from_jwt and server_url_from_jwt != "0":
                base_url = server_url_from_jwt.rstrip('/')
            else:
                base_url = get_base_url(guest_region)
            
            # Build payload with guest's region
            payload = create_like_payload(target_uid, jwt_region)
            if isinstance(payload, str):
                payload = binascii.unhexlify(payload)
            
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; Pixel 8 Build/UP1A.231005.007)",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/octet-stream",
                "Expect": "100-continue",
                "Authorization": f"Bearer {jwt}",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB51",
            }
            
            async with httpx.AsyncClient() as client:
                url = f"{base_url}/LikeProfile"
                response = await client.post(url, data=payload, headers=headers, timeout=30)
                response.raise_for_status()
            
            print(f"[{guest_uid}] ✅ Like sent! Region: {guest_region} | Status: {response.status_code}")
            mark_used(target_uid, guest_uid, now_ms)
            return True
            
        except httpx.HTTPStatusError as err:
            print(f"[{guest_uid}] ❌ HTTP {err.response.status_code}: {err.response.text[:100]}")
            return False
        except Exception as e:
            print(f"[{guest_uid}] ❌ Error: {str(e)[:100]}")
            return False

async def main():
    print("=" * 70)
    print("        🎯 FreeFire Like Sender (Fixed)")
    print("=" * 70)
    
    # Show available regions
    regions = get_available_regions()
    if not regions:
        print("\n⚠️  No region-based guests found!")
        print("Using default guests from guests_manager/guests_converted.json")
        print("\nTo use region-based system, run:")
        print("  python convert_region_guests.py <file> <region>")
        return
    
    print("\n📍 Available Regions:")
    for region, info in sorted(regions.items()):
        print(f"   • {region}: {info['count']} accounts")
    
    # User inputs
    print("\n" + "=" * 70)
    uid_to_like = input("📱 Target UID to like: ").strip()
    
    if not uid_to_like:
        print("❌ UID cannot be empty!")
        return
    
    selected_region = input("\n🌍 Select region (press Enter to auto-detect): ").strip().upper()
    
    if not selected_region or selected_region == "":
        print(f"\n🔍 Auto-detecting region for UID {uid_to_like}...")
        try:
            selected_region = await detect_uid_region(uid_to_like)
            if selected_region is None:
                print(f"❌ Could not auto-detect region for UID {uid_to_like}")
                selected_region = input("\n🌍 Please enter region manually (BD/IND/BR/US): ").strip().upper()
            else:
                print(f"✅ Detected region: {selected_region}")
        except Exception as e:
            print(f"❌ Auto-detection failed: {e}")
            selected_region = input("\n🌍 Please enter region manually (BD/IND/BR/US): ").strip().upper()
    
    if selected_region not in regions:
        print(f"\n❌ Region '{selected_region}' not available!")
        print(f"Available: {', '.join(regions.keys())}")
        return
    
    # Load region-specific guests
    guests = load_region_guests(selected_region)
    
    if not guests:
        print(f"❌ No guests found for region {selected_region}!")
        return
    
    print(f"\n✅ Loaded {len(guests)} {selected_region} guest accounts")
    
    # Filter unused guests
    ensure_target(uid_to_like)
    available_guests = [g for g in guests if not guest_used_for_target(uid_to_like, str(g["uid"]))]
    
    if not available_guests:
        print(f"\n❌ No unused {selected_region} guests available for UID {uid_to_like}")
        print(f"Total likes already sent: {usage_by_target[uid_to_like]['total_likes']}")
        save_usage()
        return
    
    print(f"💡 {len(available_guests)} unused {selected_region} guests available")
    
    # Get like count
    max_available = len(available_guests)
    likes_input = input(f"\n💝 How many likes to send? (max {max_available}): ").strip()
    requested_likes = int(likes_input) if likes_input else max_available
    requested_likes = min(requested_likes, max_available)
    
    # Get concurrency
    conc_input = input("⚡ Requests per second? (default 10): ").strip()
    MAX_CONCURRENT = int(conc_input) if conc_input else 10
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    print(f"\n🚀 Sending {requested_likes} likes from {selected_region} accounts...")
    print(f"⚙️  Concurrency: {MAX_CONCURRENT} req/sec")
    print("=" * 70 + "\n")
    
    # Create tasks
    tasks = []
    for guest in available_guests[:requested_likes]:
        tasks.append(like_with_guest(guest, uid_to_like, semaphore))
    
    # Execute with progress
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions
    success_count = sum(1 for r in results if r is True)
    error_count = sum(1 for r in results if isinstance(r, Exception))
    
    # Save usage
    save_usage()
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Completed!")
    print(f"   Success: {success_count}/{requested_likes}")
    if error_count > 0:
        print(f"   Errors: {error_count}")
    print(f"   Total likes on UID {uid_to_like}: {usage_by_target[uid_to_like]['total_likes']}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
        save_usage()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        save_usage()
