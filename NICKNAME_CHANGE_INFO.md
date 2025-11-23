# 📝 Nickname & Bio Update Guide

## ⚠️ Important Information

### Nickname Change Limitation
**FreeFire does NOT allow nickname changes via API.** This is a game limitation, not an API limitation.

**Why?**
- FreeFire's official servers do not expose a nickname change endpoint
- Nickname changes require in-game currency (diamonds) or nickname change cards
- This is done to prevent abuse and maintain game integrity

**Alternative:**
- You can only change nickname through the game itself
- Go to Settings → Account → Change Nickname (requires diamonds/card)

---

## ✅ What You CAN Do Via API

### 1. Update Bio/Signature ✅

**Endpoint:** `/bio`  
**Method:** GET or POST  
**Status:** ✅ Working & Available

**Parameters:**
- `uid` (required) - Player UID (10 digits)
- `password` (required) - Account password (64 character hex format)
- `bio` (required) - New bio/signature text

**Example Usage:**

#### GET Request:
```bash
curl "https://your-app.vercel.app/bio?uid=4059499797&password=YOUR_HEX_PASSWORD&bio=Pro%20Gamer%20%F0%9F%94%A5"
```

#### POST Request:
```bash
curl -X POST "https://your-app.vercel.app/bio" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "4059499797",
    "password": "90692811391BDC1BCAB416B78DB4293300A797E38CA8A3FD4526E538FECFAC39",
    "bio": "Pro Gamer 🔥"
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Bio updated successfully!",
  "data": {
    "uid": "4059499797",
    "nickname": "Current Nickname",
    "region": "IND",
    "new_bio": "Pro Gamer 🔥"
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Failed to get access token/open_id",
  "message": "Please check your UID and password"
}
```

---

## 🔐 How to Get Password (Hex Format)

The password parameter requires your account password in **64 character hexadecimal format**.

**This is NOT your regular password!**

To get this:
1. You need to capture it from the game's login request
2. Or use packet sniffing tools (advanced users only)
3. This is for security purposes

**Note:** Never share your password hex with anyone!

---

## 📊 What Bio Update Does

When you update bio via `/bio` endpoint:

1. ✅ Changes your profile signature/bio text
2. ✅ Visible to all players who view your profile
3. ✅ Supports Unicode (Hindi, emojis, special characters)
4. ✅ Updates instantly
5. ❌ Does NOT change your nickname
6. ❌ Does NOT change your profile picture

---

## 🎯 Other Profile Features

### What You CAN Do:
- ✅ Update bio/signature (`/bio`)
- ✅ View player info (`/info?uid=XXX`)
- ✅ Check ban status (`/check_ban/XXX`)
- ✅ Send likes (`/like?uid=XXX`)
- ✅ Send friend requests (`/send_requests?uid=XXX`)
- ✅ Generate JWT tokens (`/generate_token`)

### What You CANNOT Do (API Limitations):
- ❌ Change nickname directly
- ❌ Change profile picture
- ❌ Change level/rank
- ❌ Change badges
- ❌ Add diamonds/coins

---

## 💡 Pro Tips

### Bio/Signature Tips:
1. **Unicode Support:** You can use any language - Hindi, Arabic, Chinese, emojis, etc.
   ```
   /bio?uid=XXX&password=XXX&bio=प्रो%20गेमर%20🔥
   ```

2. **Special Characters:** Symbols and emojis work perfectly
   ```
   /bio?uid=XXX&password=XXX&bio=⚡%20LEGEND%20⚡
   ```

3. **Length Limit:** Keep bio under 50-60 characters for best display

4. **URL Encoding:** Use `%20` for spaces in GET requests

---

## 🔧 Technical Details

### How Bio Update Works:

1. **Step 1:** Generate Access Token
   - Uses UID + Password
   - Calls FreeFire authentication API

2. **Step 2:** Create JWT Token
   - Converts access token to JWT
   - Auto-detects region (IND/NX/AG)

3. **Step 3:** Encrypt Bio
   - Uses Protobuf encryption
   - Encrypts bio text securely

4. **Step 4:** Send Update Request
   - POSTs to `/UpdateSocialBasicInfo` endpoint
   - Uses Bearer token authentication

5. **Step 5:** Verify Success
   - Checks response status
   - Returns updated profile info

---

## 🚨 Common Errors

### Error: "Failed to get access token/open_id"
**Cause:** Wrong UID or password  
**Solution:** Verify your UID and password hex are correct

### Error: "API returned status 401"
**Cause:** Invalid authentication  
**Solution:** Password might have changed, get fresh password hex

### Error: "Request timeout"
**Cause:** Server is slow or down  
**Solution:** Try again after a few seconds

### Error: "Password parameter is required"
**Cause:** Missing password in request  
**Solution:** Include password parameter in hex format

---

## 📱 Example Integration

### JavaScript/Fetch:
```javascript
const updateBio = async (uid, password, bio) => {
  const response = await fetch('https://your-app.vercel.app/bio', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ uid, password, bio })
  });
  
  const result = await response.json();
  console.log(result);
};

// Usage
updateBio('4059499797', 'YOUR_HEX_PASSWORD', 'Pro Gamer 🔥');
```

### Python/Requests:
```python
import requests

def update_bio(uid, password, bio):
    response = requests.post(
        'https://your-app.vercel.app/bio',
        json={
            'uid': uid,
            'password': password,
            'bio': bio
        }
    )
    return response.json()

# Usage
result = update_bio('4059499797', 'YOUR_HEX_PASSWORD', 'Pro Gamer 🔥')
print(result)
```

---

## ✅ Summary

| Feature | Available via API | Method |
|---------|------------------|--------|
| **Change Nickname** | ❌ No | In-game only |
| **Update Bio/Signature** | ✅ Yes | `/bio` endpoint |
| **View Profile** | ✅ Yes | `/info` endpoint |
| **Send Likes** | ✅ Yes | `/like` endpoint |
| **Friend Requests** | ✅ Yes | `/send_requests` |

---

## 🎯 Next Steps

1. **Test Bio Update:**
   ```bash
   curl "https://your-app.vercel.app/bio?uid=YOUR_UID&password=YOUR_HEX&bio=Test"
   ```

2. **Check Result:**
   - Login to FreeFire
   - View your profile
   - Bio should be updated!

3. **Integrate in Your App:**
   - Use the examples above
   - Handle errors properly
   - Add proper validation

---

**Remember:** Nickname changes are NOT possible via API. Only bio/signature updates are supported! ⚠️
