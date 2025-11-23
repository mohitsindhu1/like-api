#!/usr/bin/env python3
"""
Region-Based Like Sender
========================
Specific region ke guest accounts use karke likes bhejta hai
"""

import httpx
import asyncio
import binascii
import json
import os
import time
from get_jwt import create_jwt
from encrypt_like_body import create_like_payload

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
    """Available regions ki list return karta hai"""
    region_file = os.path.join(region_dir, "regions.json")
    if os.path.exists(region_file):
        with open(region_file, 'r') as f:
            return json.load(f)
    return {}

def load_region_guests(region: str):
    """Specific region ke guests load karta hai"""
    guest_file = os.path.join(region_dir, f"{region.upper()}_guests.json")
    if os.path.exists(guest_file):
        with open(guest_file, 'r') as f:
            return json.load(f)
    return []

def get_base_url(server_name: str) -> str:
    """Server region ke basis par base URL return karta hai"""
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com"
    elif server_name == "BD":
        return "https://client.bd.freefiremobile.com"
    elif server_name == "SG":
        return "https://client.sg.freefiremobile.com"
    else:
        return "https://clientbp.ggblueshark.com"

async def like_with_guest(guest: dict, target_uid: str, semaphore) -> bool:
    guest_uid = str(guest["uid"])
    guest_pass = guest["password"]
    now_ms = int(time.time() * 1000)
    
    if guest_used_for_target(target_uid, guest_uid):
        print(f"[{guest_uid}] Already used for target {target_uid}, skipping...")
        return False
    
    async with semaphore:
        try:
            # JWT obtain karo
            jwt, region, server_url_from_jwt = await create_jwt(guest_uid, guest_pass)
            
            # Determine base URL
            guest_region = guest.get("region", region)
            BASE_URL = get_base_url(guest_region)
            
            # Payload banao
            payload = create_like_payload(target_uid, region)
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
                url = f"{BASE_URL}/LikeProfile"
                response = await client.post(url, data=payload, headers=headers, timeout=30)
                response.raise_for_status()
            
            print(f"[{guest_uid}] ✅ Like sent to {target_uid}! Region: {guest_region} | Status: {response.status_code}")
            mark_used(target_uid, guest_uid, now_ms)
            return True
            
        except httpx.HTTPStatusError as err:
            body = err.response.text if err.response is not None else ""
            print(f"[{guest_uid}] ❌ HTTP error: {err}, Response: {body}")
        except httpx.RequestError as err:
            print(f"[{guest_uid}] ❌ Request exception: {err}")
        except Exception as e:
            print(f"[{guest_uid}] ❌ Unexpected error: {e}")
    
    return False

async def main():
    print("=" * 60)
    print("        🎯 Region-Based Like Sender")
    print("=" * 60)
    
    # Available regions dikhao
    regions = get_available_regions()
    if not regions:
        print("\n❌ No region-based guests found!")
        print("First convert your guest accounts using:")
        print("  python convert_region_guests.py <file> <region>")
        return
    
    print("\n📍 Available Regions:")
    for region, info in regions.items():
        print(f"   {region}: {info['count']} accounts")
    
    # User se input lo
    print("\n" + "=" * 60)
    selected_region = input("\n🌍 Select region for guests (e.g., BD, IND, BR): ").strip().upper()
    
    if selected_region not in regions:
        print(f"❌ Region {selected_region} not found!")
        return
    
    uid_to_like = input("📱 Enter UID to like: ").strip()
    
    # Guest accounts load karo
    guests = load_region_guests(selected_region)
    print(f"\n✅ Loaded {len(guests)} {selected_region} guest accounts")
    
    # Unused guests filter karo
    available_guests = [g for g in guests if not guest_used_for_target(uid_to_like, str(g["uid"]))]
    
    if not available_guests:
        print(f"❌ No available {selected_region} guests left for target {uid_to_like}")
        save_usage()
        return
    
    print(f"💡 {len(available_guests)} unused {selected_region} guests available")
    
    requested_likes_in = input("\n💝 How many likes to send? (default: all available): ").strip()
    requested_likes = int(requested_likes_in) if requested_likes_in else len(available_guests)
    
    max_conc_in = input("⚡ Concurrent requests per second? (default: 20): ").strip()
    MAX_CONCURRENT = int(max_conc_in) if max_conc_in else 20
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    likes_planned = min(requested_likes, len(available_guests))
    
    print(f"\n🚀 Starting to send {likes_planned} likes from {selected_region} accounts...")
    print("=" * 60 + "\n")
    
    # Tasks banao
    tasks = []
    for g in available_guests[:likes_planned]:
        tasks.append(like_with_guest(g, uid_to_like, semaphore))
    
    results = await asyncio.gather(*tasks)
    save_usage()
    
    success = sum(1 for r in results if r)
    print("\n" + "=" * 60)
    print(f"✅ Completed! Success: {success}/{likes_planned}")
    print(f"📊 Total likes on {uid_to_like}: {usage_by_target[uid_to_like]['total_likes']}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
