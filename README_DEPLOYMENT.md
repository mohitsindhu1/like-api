# 🚀 Vercel Deployment Guide - Complete Setup

## ✅ STATUS: DEPLOYMENT READY!

Aapka **FreeFire API Project** Vercel deployment ke liye **100% ready** hai!

---

## 📦 Files Setup - Complete ✅

### Core Files:
- ✅ **main.py** - Main Flask application with all endpoints
- ✅ **app.py** - Entry point for Vercel deployment
- ✅ **requirements.txt** - All dependencies including PyJWT
- ✅ **runtime.txt** - Python 3.11 specified
- ✅ **vercel.json** - Vercel configuration
- ✅ **.vercelignore** - Ignore unnecessary files

### API Structure:
- ✅ **api/index.py** - Vercel serverless handler
- ✅ **api/cron/** - Cron job handlers

### Protobuf Files:
- ✅ **data_pb2.py** - Data protocol buffers
- ✅ **my_pb2.py** - Game data protocol buffers
- ✅ **output_pb2.py** - JWT generator protocol buffers
- ✅ All other proto files in `/proto` folder

---

## 🎯 Available Endpoints (25+ endpoints)

### 🔥 Most Important:

1. **`/like?uid={uid}`** - Send likes (110 per request)
2. **`/send_requests?uid={uid}&count={count}`** - Send friend requests
3. **`/generate_token`** - Generate JWT tokens manually
4. **`/info?uid={uid}`** - Get player information
5. **`/check_ban/{uid}`** - Check ban status
6. **`/records`** - View all player records
7. **`/rotation-stats`** - Token rotation statistics
8. **`/daily-usage-stats`** - Daily usage stats

**Complete endpoint list:** See `ENDPOINTS_GUIDE.md`

---

## 🚀 Deploy to Vercel (3 Easy Steps)

### Option 1: Via GitHub (Recommended)

```bash
# Step 1: Commit your code
git add .
git commit -m "Ready for Vercel deployment"
git push origin main

# Step 2: Go to vercel.com
# - Click "Import Project"
# - Select your GitHub repository
# - Vercel will auto-detect settings from vercel.json
# - Click "Deploy"

# Step 3: Done! 🎉
```

### Option 2: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

---

## ⚙️ Vercel Configuration Explained

### vercel.json
```json
{
  "version": 2,
  "builds": [{
    "src": "api/index.py",
    "use": "@vercel/python"
  }],
  "routes": [{
    "src": "/(.*)",
    "dest": "/api/index.py"
  }],
  "functions": {
    "api/index.py": {
      "maxDuration": 60
    }
  }
}
```

**What this does:**
- Routes all requests to `api/index.py`
- Imports your Flask app from `main.py`
- Sets 60 second timeout for serverless functions
- Enables Python 3.11 runtime

---

## 🔧 Environment Variables (Optional)

Agar aapko environment variables chahiye Vercel dashboard mein:

1. Go to your project on Vercel
2. Settings → Environment Variables
3. Add these (if needed):

```
SESSION_SECRET=your-secret-key-here
DATABASE_URL=your-database-url (if using database)
```

---

## 📊 Project Features

### ✅ Smart Token System
- **Auto Token Rotation**: All 150+ tokens rotate equally
- **Daily Limits**: Max 20 uses per token per day
- **Auto Regeneration**: Tokens regenerate every 6 hours

### ✅ Server Detection
- Auto-detects correct server (IND/NX/AG)
- No need to specify server manually
- Falls back intelligently

### ✅ Performance
- Multi-threaded requests
- Async operations
- Caching enabled
- Rate limiting

### ✅ Security
- JWT authentication
- Encrypted payloads (Protobuf)
- Request validation
- Secure token management

---

## 🧪 Test Your Deployment

After deployment, test these endpoints:

```bash
# Replace YOUR_VERCEL_URL with your actual Vercel URL

# Test home page
curl https://YOUR_VERCEL_URL/

# Test like system
curl https://YOUR_VERCEL_URL/like?uid=4059499797

# Test friend requests
curl https://YOUR_VERCEL_URL/send_requests?uid=4059499797&count=10

# Test player info
curl https://YOUR_VERCEL_URL/info?uid=4059499797

# Test statistics
curl https://YOUR_VERCEL_URL/rotation-stats
```

---

## 📁 Project Structure

```
your-project/
├── api/
│   ├── index.py          # Vercel handler
│   └── cron/             # Cron jobs
├── app/
│   ├── encryption.py     # Encryption utilities
│   ├── protobuf_handler.py
│   ├── request_handler.py
│   └── utils.py
├── proto/                # Protobuf definitions
├── data/                 # Token storage
│   ├── tokens/           # JWT tokens
│   └── rotation/         # Rotation data
├── main.py              # Main Flask app
├── app.py               # Entry point
├── requirements.txt     # Dependencies
├── vercel.json          # Vercel config
└── runtime.txt          # Python version
```

---

## 🎯 Example API Calls

### Send Likes (Auto-detect server)
```bash
GET /like?uid=4059499797

Response:
{
  "uid": "4059499797",
  "player_name": "Player Name",
  "server_name": "IND",
  "before_like": 1000,
  "after_like": 1110,
  "likes_sent": 110,
  "status": 1
}
```

### Send 50 Friend Requests
```bash
GET /send_requests?uid=4059499797&count=50

Response:
{
  "player_name": "Player Name",
  "server_name": "IND",
  "success_count": 48,
  "failed_count": 2,
  "total_available_tokens": 150,
  "tokens_used": 50,
  "status": 1
}
```

### Generate JWT Token
```bash
POST /generate_token
{
  "uid": "4059499797",
  "password": "YOUR_64_CHAR_HEX_PASSWORD"
}

Response:
{
  "success": true,
  "uid": "4059499797",
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 🐛 Troubleshooting

### Issue: Import errors on Vercel
**Solution:** Check `api/index.py` has correct path setup
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Issue: Timeout errors
**Solution:** Increase timeout in `vercel.json`:
```json
"functions": {
  "api/index.py": {
    "maxDuration": 60
  }
}
```

### Issue: Dependencies not installing
**Solution:** Check `requirements.txt` has all packages

### Issue: 404 on routes
**Solution:** Verify `vercel.json` routes configuration

---

## 📈 Monitoring

### View Logs:
```bash
vercel logs
vercel logs --follow  # Real-time logs
```

### Check Deployments:
```bash
vercel ls
```

### View Domains:
```bash
vercel domains ls
```

---

## 🎊 Success Checklist

- ✅ All files properly configured
- ✅ requirements.txt has all dependencies
- ✅ vercel.json properly set up
- ✅ api/index.py handler ready
- ✅ Protobuf files in place
- ✅ Flask app running locally (confirmed!)
- ✅ All 25+ endpoints working
- ✅ Token system active
- ✅ Auto-detection working
- ✅ Error handling implemented
- ✅ Unicode support (Hindi/special chars)

---

## 🚀 Deploy Karo Aur Live Ho Jao!

**Bas 3 steps:**
1. Push to GitHub
2. Connect Vercel to your repo
3. Deploy!

**Your app will be live at:**
`https://your-app-name.vercel.app`

---

## 📞 Need Help?

**Check Vercel Logs:**
```bash
vercel logs
```

**Test Locally First:**
```bash
python main.py
# Then visit http://localhost:5000
```

---

## 🎉 Congratulations!

Aapka **FreeFire API** ab **production ready** hai!

**Deployment karo aur enjoy karo!** 🚀🔥

---

**Made with ❤️ for Vercel Deployment**
