# 🚀 Vercel Serverless Deployment Guide

## Overview
Yeh guide aapko batayega ki apne Free Fire Token Generator API ko Vercel par **completely serverless** kaise deploy karein.

## ✅ Kya Configure Ho Gaya

### 1. **Serverless Architecture**
- ✅ Background scheduler ko disable kar diya gaya (serverless me nahi chalta)
- ✅ Vercel Cron Jobs configured for automatic token generation (har 6 ghante)
- ✅ On-demand token generation endpoint available
- ✅ Stateless API endpoints (pure serverless)

### 2. **Files Configure Ho Gayi**
- ✅ `vercel.json` - Deployment configuration
- ✅ `api/index.py` - Main serverless handler
- ✅ `api/cron/generate-tokens.py` - Cron job for scheduled token generation
- ✅ `.vercelignore` - Unnecessary files ko exclude karta hai

### 3. **Vercel Cron Jobs**
Token generation automatic hoti rahegi har 6 ghante:
```json
"crons": [
  {
    "path": "/api/cron/generate-tokens",
    "schedule": "0 */6 * * *"
  }
]
```

## 📋 Deployment Steps

### Step 1: Vercel Account Setup
1. [Vercel.com](https://vercel.com) par account banayein (GitHub se login karein)
2. "Add New Project" click karein
3. Apni GitHub repository select karein

### Step 2: Project Configuration
Vercel automatically detect kar lega:
- **Framework Preset**: Other
- **Build Command**: (leave empty)
- **Output Directory**: (leave empty)
- **Install Command**: `pip install -r requirements.txt`

### Step 3: Environment Variables (Optional)
Agar aapko koi secrets chahiye:
1. Project Settings → Environment Variables
2. Add karein:
   - `SESSION_SECRET` - Flask session key
   - `CRON_SECRET` - Cron job security (optional)
   - `DISCORD_WEBHOOK_URL` - Discord notifications (optional)

### Step 4: Deploy!
1. "Deploy" button click karein
2. 2-3 minutes me deploy ho jayega
3. Aapko public URL milega: `https://your-project.vercel.app`

## 🔄 Token Generation Options

### Option 1: Automatic (Vercel Cron) ✅ Recommended
Vercel automatically har 6 ghante tokens generate karega.
- **No manual work needed**
- **Free tier me available** (12 cron jobs per day)
- **URL**: `https://your-project.vercel.app/api/cron/generate-tokens`

### Option 2: Manual On-Demand
Jab chahein manually generate karein:
```bash
curl https://your-project.vercel.app/api/generate-tokens
```

### Option 3: External Cron Service
Agar aap external service use karna chahte ho:
- [cron-job.org](https://cron-job.org)
- [EasyCron](https://www.easycron.com)
- GitHub Actions

Setup:
1. Service me account banayein
2. Cron job create karein
3. URL set karein: `https://your-project.vercel.app/api/cron/generate-tokens`
4. Schedule: Every 6 hours

## 📊 Monitoring

### Check Token Generation Status
```
GET https://your-project.vercel.app/api/token-generator-status
```

### View Generated Tokens
```
GET https://your-project.vercel.app/tokens
```

### Manual Token Generation
```
GET https://your-project.vercel.app/api/generate-tokens
```

## 🎯 API Endpoints (Serverless Ready)

Saare endpoints serverless me perfect kaam karenge:

### Player Endpoints
- `GET /like?uid={UID}&server_name={SERVER}` - Send likes
- `GET /send_requests?uid={UID}&server_name={SERVER}` - Send friend requests
- `GET /visit/{SERVER}/{UID}` - Send profile visits

### Information Endpoints
- `GET /info?uid={UID}` - Player info
- `GET /check_ban?uid={UID}` - Ban check
- `GET /genpro?uid={UID}` - Generate profile

### System Endpoints
- `GET /tokens` - View all tokens
- `GET /records` - Player records
- `GET /api/token-generator-status` - Generator status
- `GET /api/generate-tokens` - Manual token generation

## ⚙️ Important Notes

### Serverless Limitations
1. **No Background Tasks**: Background scheduler nahi chal sakta
   - Solution: Vercel Cron Jobs use karein ✅

2. **60 Second Timeout**: Har function max 60 seconds tak chal sakta
   - Token generation optimized hai (parallel processing)

3. **Stateless**: Har request independent hai
   - Tokens JSON files me save hote hain ✅

### Data Persistence
- **Tokens**: `data/tokens/` folder me save
- **Accounts**: `*_ACC.json` files (encrypted)
- **Records**: Internal storage (JSON)

### Security Best Practices
1. `.gitignore` me sensitive files add karein:
   ```
   config.json
   *_ACC.json
   data/tokens/
   ```

2. Environment variables use karein secrets ke liye

3. Vercel automatically HTTPS provide karta hai

## 🆘 Troubleshooting

### Problem: Tokens generate nahi ho rahe
**Solution**: 
1. Vercel Cron logs check karein
2. Manual generation try karein: `/api/generate-tokens`
3. Token files (`data/tokens/`) deploy me include hain ya nahi check karein

### Problem: API slow response
**Solution**:
1. Vercel free tier pe cold start hota hai (first request slow)
2. Pro plan upgrade karein for instant responses

### Problem: Deployment fail
**Solution**:
1. `requirements.txt` me saare dependencies hain ya nahi check karein
2. Python version compatible hai (3.11) verify karein
3. Vercel logs dekh kar errors identify karein

## 📈 Scaling

### Free Tier Limits
- 100 GB bandwidth/month
- 100 hours execution time/month
- 12 cron jobs/day

### Upgrade Options
- **Pro Plan** ($20/month): Unlimited bandwidth, better performance
- **Enterprise**: Custom limits aur dedicated support

## 🎉 Success!

Deployment successful hai agar:
- ✅ Homepage pe API documentation dikhe
- ✅ `/like` endpoint se likes send ho jaayein
- ✅ `/tokens` endpoint tokens dikha raha ho
- ✅ Vercel Cron har 6 ghante tokens generate kar raha ho

## 🔗 Useful Links

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Cron Jobs](https://vercel.com/docs/cron-jobs)
- [Python on Vercel](https://vercel.com/docs/functions/serverless-functions/runtimes/python)

---

**Happy Deploying! 🚀**

Koi problem ho toh Vercel logs check karein ya support se contact karein.
