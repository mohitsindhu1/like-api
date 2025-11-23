# FreeFire Like API Documentation

## 🚀 Overview

API jo FreeFire profiles ko automatically likes bhejta hai. Secure authentication ke saath complete API system.

## 🔑 Authentication

API ko use karne ke liye **API Key** zaroori hai. Header mein `X-API-Key` bhejni hogi.

### API Key Setup

1. Environment variable set karo:
```bash
export FF_API_KEY="your_secret_key_here"
```

2. Ya `.env` file mein add karo:
```
FF_API_KEY=your_secret_key_here
```

**Default API Key (Development):** `default_dev_key_12345`

⚠️ **Production mein apni unique key use karo!**

## 📡 API Endpoints

### 1. Simple Like Endpoint (Recommended) ⭐
**GET** `/like`

Sabse simple tarika likes bhejne ka - sirf URL mein parameters pass karo!

**Query Parameters:**
- `uid` (required): Target UID jisko likes bhejna hai
- `server` (required): Server region - IND, BD, BR, US, SG
- `api` (required): Aapki API key
- `count` (optional): Kitne likes bhejna hai (default: 101, max: 101)

**Example URL:**
```
/like?uid=123456&server=IND&api=your_key&count=50
```

**Response (Success):**
```json
{
  "success": true,
  "uid": 123456,
  "region": "IND",
  "profile": {
    "player_nickname": "PlayerName",
    "likes_before": 1450,
    "likes_after": 1500,
    "likes_difference": 50
  },
  "results": {
    "requested_likes": 50,
    "successful_accounts": 50,
    "actual_likes_sent": 50,
    "status": 1
  },
  "summary": "✅ PlayerName: 1450 → 1500 (+50 likes) in IND"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Error message yaha aayega"
}
```

---

### 2. Root Endpoint
**GET** `/`

API info aur available endpoints dikhata hai.

**Response:**
```json
{
  "service": "FreeFire Like API",
  "status": "running",
  "version": "1.0.0",
  "endpoints": {
    "simple_like": "/like?uid=&server=&api= (GET) - Simple endpoint",
    "send_likes": "/api/send-likes (POST) - Advanced endpoint",
    "check_uid": "/check-uid?uid=&api= (GET) - Check UID across all regions",
    "health": "/health (GET)"
  },
  "examples": {
    "send_like": "/like?uid=123456&server=IND&api=your_key&count=50",
    "check_uid": "/check-uid?uid=123456&api=your_key"
  }
}
```

---

### 3. Health Check
**GET** `/health`

Server health status check karta hai.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-11T09:22:00.000Z"
}
```

---

### 4. Send Likes (Advanced Endpoint)
**POST** `/api/send-likes`

Target UID ko likes bhejta hai with full profile information.

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "uid": 111119900,
  "region": "IND",
  "count": 101
}
```

**Parameters:**
- `uid` (required): Target UID jisko likes bhejna hai
- `region` (required): Server region - IND, BD, BR, US, SG
- `count` (optional): Kitne likes bhejna hai (default: 101, max: 101)

**Response (Success):**
```json
{
  "success": true,
  "uid": 111119900,
  "region": "IND",
  "profile": {
    "player_nickname": "PlayerName",
    "likes_before": 1400,
    "likes_after": 1500,
    "likes_difference": 100
  },
  "results": {
    "requested_likes": 101,
    "successful_accounts": 101,
    "failed_accounts": 0,
    "actual_likes_sent": 100,
    "status": 1,
    "timestamp": "2025-10-11T09:22:00.000Z"
  },
  "summary": "✅ PlayerName: 1400 → 1500 (+100 likes) in IND"
}
```

**Response (Error - Invalid API Key):**
```json
{
  "detail": "Invalid API key. Access denied."
}
```

**Response (Error - No Guests Available):**
```json
{
  "detail": "No unused IND guests available for UID 111119900"
}
```

---

### 5. Get Available Regions
**GET** `/api/regions`

Available regions aur unke account counts dikhata hai.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "regions": {
    "BD": {
      "count": 165,
      "file": "guests_manager/region_based/BD_guests.json"
    },
    "IND": {
      "count": 161,
      "file": "guests_manager/region_based/IND_guests.json"
    }
  },
  "total_regions": 2
}
```

---

### 6. Get User Info (Simple) ⭐
**GET** `/info`

Ek UID ka information fetch karta hai - sabhi regions mein check karta hai.

**Query Parameters:**
- `uid` (required): Target UID jisko check karna hai
- `api` (required): Aapki API key

**Example URL:**
```
/info?uid=2926998273&api=your_key
```

**Response (Success):**
```json
{
  "success": true,
  "uid": 2926998273,
  "found_in_regions": ["IND", "BR", "SG"],
  "total_regions_found": 3,
  "regions_data": {
    "IND": {
      "found": true,
      "player_nickname": "PlayerName",
      "likes": 1500,
      "level": 65,
      "uid": 2926998273
    },
    "BR": {
      "found": true,
      "player_nickname": "PlayerName",
      "likes": 200,
      "level": 65,
      "uid": 2926998273
    }
  }
}
```

**Features:**
- ✅ Simple endpoint - bas `info?uid=&api=` use karo
- ✅ Sabhi 12 regions mein automatically check karta hai
- ✅ Har region ka complete profile dikhata hai
- ✅ Fast parallel checking

---

### 7. Check UID Across All Regions
**GET** `/check-uid`

Ek UID ko sabhi regions mein check karta hai aur complete profile information dikhata hai.

**Query Parameters:**
- `uid` (required): Target UID jisko check karna hai
- `api` (required): Aapki API key

**Example URL:**
```
/check-uid?uid=123456&api=your_key
```

**Response (Success):**
```json
{
  "success": true,
  "uid": 123456,
  "found_in_regions": ["IND", "BR", "SG"],
  "total_regions_found": 3,
  "regions_data": {
    "IND": {
      "found": true,
      "player_nickname": "PlayerName",
      "likes": 1500,
      "level": 65,
      "uid": 123456
    },
    "BR": {
      "found": true,
      "player_nickname": "PlayerName",
      "likes": 200,
      "level": 65,
      "uid": 123456
    },
    "SG": {
      "found": true,
      "player_nickname": "PlayerName",
      "likes": 300,
      "level": 65,
      "uid": 123456
    },
    "RU": {
      "found": false,
      "error": "Player not found in this region"
    }
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Invalid API key"
}
```

**Features:**
- ✅ Ek UID ko 12 regions mein check karta hai (IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS)
- ✅ Har region ka player nickname, likes, aur level dikhata hai
- ✅ Kitne regions mein player mila, uski count dikhata hai
- ✅ Fast parallel checking - sabhi regions ek saath check hote hain

---

## 🧪 Testing Examples

### cURL Examples

**1. Send Likes:**
```bash
curl -X POST "http://0.0.0.0:5000/api/send-likes" \
  -H "X-API-Key: default_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": 111119900,
    "region": "IND",
    "count": 101
  }'
```

**2. Get Regions:**
```bash
curl -X GET "http://0.0.0.0:5000/api/regions" \
  -H "X-API-Key: default_dev_key_12345"
```

**3. Get User Info (Simple):**
```bash
curl -X GET "http://0.0.0.0:5000/info?uid=2926998273&api=default_dev_key_12345"
```

**4. Check UID Across Regions:**
```bash
curl -X GET "http://0.0.0.0:5000/check-uid?uid=123456&api=default_dev_key_12345"
```

**5. Health Check:**
```bash
curl -X GET "http://0.0.0.0:5000/health"
```

---

### Python Client Example

```python
import requests
import json

# API Configuration
API_URL = "http://0.0.0.0:5000"
API_KEY = "default_dev_key_12345"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Send Likes Request
payload = {
    "uid": 111119900,
    "region": "IND",
    "count": 101
}

response = requests.post(
    f"{API_URL}/api/send-likes",
    headers=headers,
    json=payload
)

result = response.json()
print(json.dumps(result, indent=2))

# Check profile info
if result.get("profile"):
    profile = result["profile"]
    print(f"\n✅ Player: {profile['player_nickname']}")
    print(f"💝 Likes Before: {profile['likes_before']}")
    print(f"💝 Likes After: {profile['likes_after']}")
    print(f"📊 Likes Sent: {profile['likes_difference']}")
    print(f"📝 Summary: {result['summary']}")
```

---

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_URL = 'http://0.0.0.0:5000';
const API_KEY = 'default_dev_key_12345';

async function sendLikes() {
  try {
    const response = await axios.post(
      `${API_URL}/api/send-likes`,
      {
        uid: 111119900,
        region: 'IND',
        count: 101
      },
      {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );

    console.log('✅ Success:', response.data);
    
    if (response.data.profile) {
      const profile = response.data.profile;
      console.log(`\n👤 Player: ${profile.player_nickname}`);
      console.log(`💝 Likes Before: ${profile.likes_before}`);
      console.log(`💝 Likes After: ${profile.likes_after}`);
      console.log(`📊 Likes Sent: ${profile.likes_difference}`);
    }
    
    if (response.data.summary) {
      console.log(`\n📝 ${response.data.summary}`);
    }
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
  }
}

sendLikes();
```

---

## 🔒 Security Features

1. **API Key Authentication**: Har request ke liye valid API key zaroori hai
2. **Environment Variable Storage**: API keys code mein nahi, environment variables mein store hoti hain
3. **Rate Limiting**: 10 concurrent requests per second (internal)
4. **Region Validation**: Sirf valid regions accept hoti hain
5. **Usage Tracking**: Duplicate likes prevent karne ke liye tracking system

---

## 📊 Response Fields Explained

### Profile Object
- `player_nickname`: Player ka naam/nickname
- `likes_before`: Likes bhejne se pehle kitne likes the
- `likes_after`: Likes bhejne ke baad kitne likes hain
- `likes_difference`: Actual mein kitne likes increase hue

### Results Object
- `requested_likes`: Kitne likes request kiye the
- `successful_accounts`: Kitne accounts successfully use hue
- `failed_accounts`: Kitne accounts fail hue (POST endpoint only)
- `actual_likes_sent`: Actual mein kitne likes sent hue
- `status`: Status code (1 = success, 2 = partial/failed)
- `timestamp`: Request ka time (POST endpoint only)

### Summary Field
- Human-readable summary in format: "✅ PlayerName: before → after (+difference likes) in REGION"
- Example: "✅ PlayerName: 1450 → 1500 (+50 likes) in IND"

---

## 🚨 Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success - Likes successfully sent |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - API key missing |
| 403 | Forbidden - Invalid API key |
| 404 | Not Found - No guest accounts available |
| 500 | Internal Server Error |

---

## 🎯 Features

✅ **Authentication**: API key based secure access  
✅ **Profile Fetching**: Target ka naam aur likes count fetch hota hai  
✅ **Random Account Selection**: 101 random accounts se likes bheje jaate hain  
✅ **Region Support**: Multiple regions (IND, BD, BR, US, SG)  
✅ **Usage Tracking**: Duplicate likes prevent hote hain  
✅ **Concurrent Processing**: Fast execution with async operations  
✅ **Error Handling**: Detailed error messages  
✅ **Auto-documentation**: Swagger UI available at `/docs`  

---

## 📚 Interactive API Documentation

FastAPI automatic documentation provide karta hai:

- **Swagger UI**: http://0.0.0.0:5000/docs
- **ReDoc**: http://0.0.0.0:5000/redoc

Yahan se directly API test kar sakte ho!

---

## 🔧 Configuration

**File:** `src/api_config.py`

```python
API_KEY = os.getenv("FF_API_KEY", "default_dev_key_12345")
API_HOST = "0.0.0.0"
API_PORT = 5000
MAX_LIKES_PER_REQUEST = 101
```

---

## 📝 Notes

- Default API key: `default_dev_key_12345` (development only)
- Maximum 101 likes per request
- Accounts randomly select hoti hain
- Usage history automatically save hoti hai
- Profile info fetch karne mein failure se likes sending affect nahi hoti

---

## 🎉 Quick Start

1. **Start Server:**
```bash
python -m uvicorn src.like_api:app --host 0.0.0.0 --port 5000 --reload
```

2. **Set API Key (Optional):**
```bash
export FF_API_KEY="your_secret_key"
```

3. **Test API:**
```bash
curl http://0.0.0.0:5000/health
```

4. **Send Likes:**
```bash
curl -X POST "http://0.0.0.0:5000/api/send-likes" \
  -H "X-API-Key: default_dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"uid": 111119900, "region": "IND", "count": 101}'
```

---

**Developed with ❤️ for FreeFire automation**
