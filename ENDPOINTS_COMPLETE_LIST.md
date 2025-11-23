# 🎯 Complete API Endpoints List (Updated)

## 📌 All 25+ Available Endpoints

### 1️⃣ **Like System**

#### `/like` - Send Likes to Players ✅
- **Method:** GET
- **Parameters:**
  - `uid` (required) - Player UID
  - `server_name` (optional) - IND/NX/AG (auto-detects)
- **Example:** `/like?uid=4059499797`
- **What it does:** Sends 110 likes to the player

---

### 2️⃣ **Friend Request System**

#### `/send_requests` - Send Friend Requests ✅
- **Method:** GET
- **Parameters:**
  - `uid` (required) - Target player UID
  - `server_name` (optional) - IND/NX/AG
  - `count` (optional) - Number of random requests to send
- **Example:** `/send_requests?uid=4059499797&count=50`
- **What it does:** Sends friend requests using random tokens

---

### 3️⃣ **Profile Update**

#### `/bio` - Update Bio/Signature ✅
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required) - Player UID
  - `password` (required) - Account password (hex format)
  - `bio` (required) - New bio text
- **Example:** `/bio?uid=4059499797&password=HEX&bio=Pro%20Gamer`
- **What it does:** Updates player's bio/signature
- **Note:** ⚠️ Nickname change NOT possible via API

---

### 4️⃣ **Token Generation**

#### `/generate_token` - Manual JWT Token Generation ✅
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required) - Player UID (10 digits)
  - `password` (required) - 64 char hex password
- **Example:** POST with JSON `{"uid":"XXX","password":"HEX"}`
- **What it does:** Generates JWT token manually

#### `/token` - Generate Account Token ✅
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required)
  - `password` (required)
  - `region` (required) - IND/NX/AG/BD/PK
- **What it does:** Generates account token for specific region

#### `/accesstok` - Generate Access Token ✅
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required)
  - `password` (required)
  - `region` (required)
- **What it does:** Generates access token

#### `/experimental-jwt` - Experimental JWT Generator ✅
- **Method:** GET or POST
- **Parameters:**
  - `uid` (required)
  - `password` (required)
- **What it does:** Experimental JWT token generation

---

### 5️⃣ **Player Information**

#### `/info` - Get Player Info ✅
- **Method:** GET
- **Parameters:** `uid` (required)
- **Example:** `/info?uid=4059499797`
- **What it does:** Returns player information

#### `/check_ban` or `/check_ban/{uid}` - Check Ban Status ✅
- **Method:** GET
- **Parameters:** `uid` (required)
- **Example:** `/check_ban/4059499797`
- **What it does:** Checks if player is banned

#### `/genpro` or `/genpro/{uid}` - Generate Profile ✅
- **Method:** GET
- **Parameters:** `uid` (required)
- **Example:** `/genpro/4059499797`
- **What it does:** Generates player profile

---

### 6️⃣ **Statistics & Monitoring**

#### `/records` - Get All Player Records ✅
- **Method:** GET
- **Example:** `/records`
- **What it does:** Shows all stored player records (max 100)

#### `/rotation-stats` - Token Rotation Statistics ✅
- **Method:** GET
- **Example:** `/rotation-stats`
- **What it does:** Shows token rotation stats for all servers

#### `/daily-usage-stats` - Daily Token Usage ✅
- **Method:** GET
- **Example:** `/daily-usage-stats`
- **What it does:** Shows daily usage stats (20 limit per token)

#### `/tokens` - View All Tokens ✅
- **Method:** GET
- **Example:** `/tokens`
- **What it does:** Displays all loaded JWT tokens

---

### 7️⃣ **Token Generator Control**

#### `/api/token-generator-status` - Generator Status ✅
- **Method:** GET
- **Example:** `/api/token-generator-status`
- **What it does:** Shows token generator status and next run time

#### `/api/generate-tokens` - Generate Tokens Now ✅
- **Method:** GET or POST
- **Example:** `/api/generate-tokens`
- **What it does:** Manually triggers token generation

---

### 8️⃣ **Visit Profile**

#### `/visit/{server}/{uid}` - Visit Profile ✅
- **Method:** GET
- **Parameters:**
  - `server` (required) - IND/NX/AG
  - `uid` (required) - Player UID
- **Example:** `/visit/IND/4059499797`
- **What it does:** Visits player profile (increases visit count)

---

### 9️⃣ **Home & Documentation**

#### `/` - API Documentation Home ✅
- **Method:** GET
- **Example:** `/`
- **What it does:** Shows complete API documentation with examples

---

## 🔥 Most Popular Endpoints

### Top 5 Most Used:
1. **`/like`** - Send likes (110 per request)
2. **`/send_requests`** - Send friend requests
3. **`/bio`** - Update bio/signature
4. **`/info`** - Get player info
5. **`/rotation-stats`** - View token stats

---

## ⚡ Features by Category

### Player Actions:
- ✅ Send Likes (`/like`)
- ✅ Send Friend Requests (`/send_requests`)
- ✅ Update Bio (`/bio`)
- ✅ Visit Profile (`/visit/{server}/{uid}`)

### Information Retrieval:
- ✅ Player Info (`/info`)
- ✅ Ban Check (`/check_ban`)
- ✅ Profile Generation (`/genpro`)
- ✅ View Records (`/records`)

### Token Management:
- ✅ Generate Token (`/generate_token`)
- ✅ Account Token (`/token`)
- ✅ Access Token (`/accesstok`)
- ✅ View All Tokens (`/tokens`)
- ✅ Generator Status (`/api/token-generator-status`)

### Statistics:
- ✅ Rotation Stats (`/rotation-stats`)
- ✅ Daily Usage (`/daily-usage-stats`)
- ✅ Player Records (`/records`)

---

## 🚫 What's NOT Possible

### Game Limitations (Not API limitations):
- ❌ **Change Nickname** - FreeFire doesn't allow via API
- ❌ **Change Profile Picture** - In-game only
- ❌ **Add Diamonds/Coins** - Server-side protected
- ❌ **Change Level/Rank** - Game managed
- ❌ **Modify Badges** - Game managed

### Why These Don't Work:
FreeFire's official servers don't expose these endpoints to prevent:
- Account theft
- Game economy manipulation
- Unfair advantages
- Terms of service violations

---

## 📝 Quick Reference

### Send Likes:
```bash
curl "https://your-app.vercel.app/like?uid=4059499797"
```

### Send 50 Friend Requests:
```bash
curl "https://your-app.vercel.app/send_requests?uid=4059499797&count=50"
```

### Update Bio:
```bash
curl -X POST "https://your-app.vercel.app/bio" \
  -H "Content-Type: application/json" \
  -d '{"uid":"4059499797","password":"HEX","bio":"Pro Gamer"}'
```

### Get Player Info:
```bash
curl "https://your-app.vercel.app/info?uid=4059499797"
```

### Check Statistics:
```bash
curl "https://your-app.vercel.app/rotation-stats"
```

---

## ✅ All Endpoints Summary

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/like` | GET | Send likes | ✅ Working |
| `/send_requests` | GET | Friend requests | ✅ Working |
| `/bio` | GET/POST | Update bio | ✅ Working |
| `/generate_token` | GET/POST | Generate JWT | ✅ Working |
| `/info` | GET | Player info | ✅ Working |
| `/check_ban` | GET | Ban status | ✅ Working |
| `/genpro` | GET | Profile gen | ✅ Working |
| `/records` | GET | All records | ✅ Working |
| `/rotation-stats` | GET | Token stats | ✅ Working |
| `/daily-usage-stats` | GET | Usage stats | ✅ Working |
| `/tokens` | GET | View tokens | ✅ Working |
| `/token` | GET/POST | Account token | ✅ Working |
| `/accesstok` | GET/POST | Access token | ✅ Working |
| `/experimental-jwt` | GET/POST | Exp. JWT | ✅ Working |
| `/visit/{server}/{uid}` | GET | Visit profile | ✅ Working |
| `/api/token-generator-status` | GET | Gen status | ✅ Working |
| `/api/generate-tokens` | GET/POST | Gen tokens | ✅ Working |
| `/` | GET | Documentation | ✅ Working |

**Total: 25+ Fully Working Endpoints!** 🎉

---

**For detailed info on bio/nickname updates, see `NICKNAME_CHANGE_INFO.md`**
