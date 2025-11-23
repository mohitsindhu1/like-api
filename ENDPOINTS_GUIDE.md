# 🎯 Complete API Endpoints Guide

## 📌 All Available Endpoints (Vercel Ready)

### 1️⃣ **Like System**

#### `/like` - Send Likes to Players
- **Method:** GET
- **Parameters:**
  - `uid` (required) - Player UID
  - `server_name` (optional) - IND/NX/AG (auto-detects if not provided)
- **Example:**
  ```
  /like?uid=4059499797
  /like?uid=4059499797&server_name=IND
  ```
- **Response:**
  ```json
  {
    "uid": "4059499797",
    "player_name": "PlayerName",
    "server_name": "IND",
    "before_like": 1000,
    "after_like": 1110,
    "likes_sent": 110,
    "status": 1,
    "timestamp": "2025-11-17T..."
  }
  ```

---

### 2️⃣ **Friend Requests**

#### `/send_requests` - Send Friend Requests
- **Method:** GET
- **Parameters:**
  - `uid` (required) - Target player UID
  - `server_name` (optional) - IND/NX/AG (auto-detects)
  - `count` (optional) - Number of random requests to send
- **Example:**
  ```
  /send_requests?uid=4059499797
  /send_requests?uid=4059499797&count=50
  /send_requests?uid=4059499797&server_name=NX&count=100
  ```
- **Response:**
  ```json
  {
    "player_name": "PlayerName",
    "server_name": "IND",
    "success_count": 95,
    "failed_count": 5,
    "total_available_tokens": 150,
    "tokens_used": 100,
    "status": 1,
    "timestamp": "2025-11-17T..."
  }
  ```

---

### 3️⃣ **Token Generation**

#### `/generate_token` - Manual JWT Token Generation
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required) - Player UID (10 digits)
  - `password` (required) - 64 character hex password
- **Example:**
  ```
  POST /generate_token
  {
    "uid": "4059499797",
    "password": "90692811391BDC1BCAB416B78DB4293300A797E38CA8A3FD4526E538FECFAC39"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "uid": "4059499797",
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "message": "JWT token generated successfully"
  }
  ```

---

### 4️⃣ **Player Information**

#### `/info` - Get Player Info
- **Method:** GET
- **Parameters:**
  - `uid` (required) - Player UID
- **Example:**
  ```
  /info?uid=4059499797
  ```

#### `/check_ban` - Check Ban Status
- **Method:** GET
- **Parameters:**
  - `uid` (required) - Player UID
- **Example:**
  ```
  /check_ban?uid=4059499797
  /check_ban/4059499797
  ```

#### `/genpro` - Generate Profile
- **Method:** GET
- **Parameters:**
  - `uid` (required) - Player UID
- **Example:**
  ```
  /genpro?uid=4059499797
  /genpro/4059499797
  ```

---

### 5️⃣ **Statistics & Monitoring**

#### `/records` - Get All Player Records
- **Method:** GET
- **Example:**
  ```
  /records
  ```
- **Response:**
  ```json
  {
    "total_records": 150,
    "records": [...],
    "message": "Internal storage"
  }
  ```

#### `/rotation-stats` - Token Rotation Statistics
- **Method:** GET
- **Example:**
  ```
  /rotation-stats
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "rotation_stats": {
      "IND": {...},
      "NX": {...},
      "AG": {...}
    },
    "system_info": {
      "tokens_per_request": 110,
      "rotation_enabled": true
    }
  }
  ```

#### `/daily-usage-stats` - Daily Token Usage
- **Method:** GET
- **Example:**
  ```
  /daily-usage-stats
  ```

#### `/tokens` - View All Tokens
- **Method:** GET
- **Example:**
  ```
  /tokens
  ```

---

### 6️⃣ **Token Generator Control**

#### `/api/token-generator-status` - Generator Status
- **Method:** GET
- **Example:**
  ```
  /api/token-generator-status
  ```

#### `/api/generate-tokens` - Generate Tokens Now
- **Method:** GET or POST
- **Example:**
  ```
  /api/generate-tokens
  ```

---

### 7️⃣ **Advanced Features**

#### `/bio` - Update Bio/Signature
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required)
  - `password` (required)
  - `signature` (required) - New bio text
- **Example:**
  ```
  POST /bio
  {
    "uid": "4059499797",
    "password": "YOUR_PASSWORD_HEX",
    "signature": "New Bio Text"
  }
  ```

#### `/token` - Generate Account Token
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required)
  - `password` (required)
  - `region` (required) - IND/NX/AG/BD/PK

#### `/accesstok` - Generate Access Token
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required)
  - `password` (required)
  - `region` (required)

#### `/experimental-jwt` - Experimental JWT Generator
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required)
  - `password` (required)

#### `/visit/{server}/{uid}` - Visit Profile
- **Method:** GET
- **Example:**
  ```
  /visit/IND/4059499797
  /visit/NX/4059499797
  ```

---

### 8️⃣ **Home & Info**

#### `/` - API Documentation Home
- **Method:** GET
- Shows complete API documentation with examples

---

## 🚀 Quick Start Examples

### Send Likes (Auto-detect server)
```bash
curl "https://your-app.vercel.app/like?uid=4059499797"
```

### Send 50 Friend Requests
```bash
curl "https://your-app.vercel.app/send_requests?uid=4059499797&count=50"
```

### Get Player Info
```bash
curl "https://your-app.vercel.app/info?uid=4059499797"
```

### Check Ban Status
```bash
curl "https://your-app.vercel.app/check_ban/4059499797"
```

### View Statistics
```bash
curl "https://your-app.vercel.app/rotation-stats"
curl "https://your-app.vercel.app/daily-usage-stats"
curl "https://your-app.vercel.app/records"
```

---

## ⚡ Features

- ✅ **Auto Server Detection** - Automatically finds the right server
- ✅ **Smart Token Rotation** - Equal distribution of all tokens
- ✅ **Daily Limits** - Max 20 uses per token per day
- ✅ **Unicode Support** - Full Hindi/special characters support
- ✅ **Multi-threading** - Fast concurrent requests
- ✅ **Error Handling** - Comprehensive error messages
- ✅ **Rate Limiting** - Prevents API abuse

---

## 🔒 Security

All endpoints use:
- JWT Authentication
- Encrypted payloads (Protobuf)
- Secure token management
- Request validation

---

## 📝 Notes

1. **Server Names:** IND (India), NX (North America), AG (Asia)
2. **Auto-detection:** If server not specified, API tries IND → NX → AG
3. **Count Parameter:** Randomly selects that many tokens for requests
4. **Status Codes:**
   - 1 = Success
   - 2 = Failed/Error

---

**Vercel Deployment Ready! 🎉**
