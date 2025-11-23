#!/usr/bin/env python3
"""
FreeFire Like API Test Client
Simple script to test the API endpoints
"""

import requests
import json
import sys
from typing import Optional

# API Configuration
API_URL = "http://0.0.0.0:5000"
API_KEY = "default_dev_key_12345"  # Change this if you set custom key

def make_request(method: str, endpoint: str, data: Optional[dict] = None):
    """Make API request with proper headers"""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"❌ Unsupported method: {method}")
            return None
        
        return response
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: API server is not running!")
        print("   Start server with: python -m uvicorn src.like_api:app --host 0.0.0.0 --port 5000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Request Error: {str(e)}")
        return None


def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*70)
    print("🏥 Testing Health Check Endpoint")
    print("="*70)
    
    response = make_request("GET", "/health")
    
    if response and response.status_code == 200:
        print("✅ Health Check Passed")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Health Check Failed: {response.status_code if response else 'No Response'}")


def test_get_regions():
    """Test get regions endpoint"""
    print("\n" + "="*70)
    print("📍 Testing Get Regions Endpoint")
    print("="*70)
    
    response = make_request("GET", "/api/regions")
    
    if response and response.status_code == 200:
        print("✅ Get Regions Passed")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        print("\n📊 Available Regions:")
        for region, info in data.get("regions", {}).items():
            print(f"   • {region}: {info['count']} accounts")
    else:
        print(f"❌ Get Regions Failed: {response.status_code if response else 'No Response'}")
        if response:
            print(response.json())


def test_send_likes(uid: int, region: str, count: int = 10):
    """Test send likes endpoint"""
    print("\n" + "="*70)
    print(f"💝 Testing Send Likes Endpoint")
    print("="*70)
    print(f"📱 Target UID: {uid}")
    print(f"🌍 Region: {region}")
    print(f"🔢 Likes to send: {count}")
    
    payload = {
        "uid": uid,
        "region": region,
        "count": count
    }
    
    response = make_request("POST", "/api/send-likes", payload)
    
    if response and response.status_code == 200:
        print("\n✅ Send Likes Passed")
        data = response.json()
        
        # Show profile info
        if data.get("profile"):
            profile = data["profile"]
            print(f"\n👤 Profile Information:")
            print(f"   • UID: {profile.get('uid')}")
            print(f"   • Nickname: {profile.get('nickname', 'N/A')}")
            print(f"   • Current Likes: {profile.get('likes', 'N/A')}")
        
        # Show results
        if data.get("results"):
            results = data["results"]
            print(f"\n📊 Results:")
            print(f"   • Requested: {results.get('requested_likes')}")
            print(f"   • Successful: {results.get('successful_likes')}")
            print(f"   • Failed: {results.get('failed_likes')}")
            print(f"   • Accounts Used: {results.get('accounts_used')}")
            print(f"   • Timestamp: {results.get('timestamp')}")
        
        print(f"\n✅ {data.get('message')}")
    else:
        print(f"\n❌ Send Likes Failed: {response.status_code if response else 'No Response'}")
        if response:
            print(json.dumps(response.json(), indent=2))


def test_invalid_api_key():
    """Test with invalid API key"""
    print("\n" + "="*70)
    print("🔒 Testing Invalid API Key")
    print("="*70)
    
    global API_KEY
    original_key = API_KEY
    API_KEY = "invalid_key_12345"
    
    response = make_request("GET", "/api/regions")
    
    if response and response.status_code == 403:
        print("✅ Invalid API Key Test Passed (Correctly Rejected)")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Invalid API Key Test Failed: {response.status_code if response else 'No Response'}")
    
    # Restore original key
    API_KEY = original_key


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("        🚀 FreeFire Like API Test Suite")
    print("="*70)
    print(f"🔗 API URL: {API_URL}")
    print(f"🔑 API Key: {API_KEY}")
    
    # Test 1: Health Check
    test_health_check()
    
    # Test 2: Get Regions
    test_get_regions()
    
    # Test 3: Invalid API Key
    test_invalid_api_key()
    
    # Test 4: Send Likes (Small test with 10 likes)
    # Change these values to test with your own UID and region
    test_uid = 111119900  # Replace with actual UID
    test_region = "IND"   # Replace with available region (BD, IND, BR, US, SG)
    test_count = 10       # Small number for testing
    
    print("\n" + "="*70)
    print("⚠️  INTERACTIVE TEST MODE")
    print("="*70)
    
    user_input = input("\n🤔 Do you want to test sending likes? (yes/no): ").strip().lower()
    
    if user_input in ['yes', 'y']:
        custom_uid = input(f"📱 Enter UID (default: {test_uid}): ").strip()
        custom_region = input(f"🌍 Enter Region (default: {test_region}): ").strip().upper()
        custom_count = input(f"🔢 Enter count (default: {test_count}): ").strip()
        
        if custom_uid:
            test_uid = int(custom_uid)
        if custom_region:
            test_region = custom_region
        if custom_count:
            test_count = int(custom_count)
        
        test_send_likes(test_uid, test_region, test_count)
    else:
        print("\n⏭️  Skipping send likes test")
    
    print("\n" + "="*70)
    print("✅ All Tests Completed!")
    print("="*70)
    print("\n📚 Full API Docs: http://0.0.0.0:5000/docs")
    print("📖 Documentation: API_DOCUMENTATION.md")
    print("\n")


if __name__ == "__main__":
    main()
