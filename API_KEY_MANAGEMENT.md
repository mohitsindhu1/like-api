# 🔐 Multi-API Key Management System

## Overview

Secure API key management system with **IP-based location locking**. Har API key first use pe ek specific location se lock ho jati hai aur sirf wahi location se use ho sakti hai.

## 🎯 Key Features

✅ **Multiple API Keys**: Unlimited API keys create kar sakte ho  
✅ **Location Locking**: First use pe IP address se automatically lock ho jati hai  
✅ **Security**: Different location se use karne pe reject ho jati hai  
✅ **Management**: Create, activate, deactivate, reset - full control  
✅ **Tracking**: Usage count aur last used tracking  
✅ **Persistent Storage**: JSON file mein secure storage  

---

## 📋 API Key Lifecycle

### 1. **Creation** (Unlocked State)
```
API Key Created
├── Status: Active
├── Location: Not Locked
└── Ready for first use
```

### 2. **First Use** (Auto-Lock)
```
First Request Received
├── IP Address: Captured & Hashed
├── User Agent: Captured
└── Status: Locked to Location
```

### 3. **Subsequent Uses** (Validation)
```
Each Request
├── Check: IP matches locked IP? ✓
├── Check: User Agent matches? ✓
└── Access: Granted or Denied
```

---

## 🛠️ Management Methods

### Method 1: CLI Tool (Recommended)

**Start Admin Tool:**
```bash
python src/api_admin.py
```

**Menu Options:**
```
1. Create new API key
2. List all API keys
3. Show key info
4. Activate API key
5. Deactivate API key
6. Reset location lock
7. Delete API key
8. Exit
```

### Method 2: API Endpoints (Advanced)

**Admin Password Required:** Set via `FF_ADMIN_PASSWORD` environment variable

**Security Notice:**
⚠️ **CRITICAL**: Admin password MUST be set via environment variable for production use!

```bash
# Set admin password
export FF_ADMIN_PASSWORD="your_secure_password_here"
```

#### Create New Key
```bash
# First set your admin password
export FF_ADMIN_PASSWORD="your_secure_password"

# Then create key
curl -X POST "http://0.0.0.0:5000/api/admin/create-key?key_name=Production" \
  -H "X-Admin-Password: your_secure_password"
```

**Response:**
```json
{
  "success": true,
  "api_key": "ff_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "name": "Production",
  "message": "API key created successfully. Save it securely!",
  "note": "This key will be locked to the IP address on first use."
}
```

#### List All Keys
```bash
curl -X GET "http://0.0.0.0:5000/api/admin/list-keys" \
  -H "X-Admin-Password: your_secure_password"
```

**Response:**
```json
{
  "keys": {
    "***xxxxxxxx": {
      "name": "Production",
      "created_at": "2025-10-11T09:00:00.000000",
      "is_locked": true,
      "usage_count": 150,
      "is_active": true,
      "last_used": "2025-10-11T12:30:00.000000"
    }
  }
}
```

---

## 📝 Usage Examples

### Example 1: Create and Use Key

```bash
# Step 1: Create API key
python src/api_admin.py
# Select: 1 (Create new API key)
# Enter name: "MyApp"
# Copy the generated key: ff_abc123...

# Step 2: First use (gets locked to your IP)
curl -X POST "http://0.0.0.0:5000/api/send-likes" \
  -H "X-API-Key: ff_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"uid": 111119900, "region": "IND", "count": 50}'

# Response: "API key locked to your location"
```

### Example 2: Check Key Status

```bash
python src/api_admin.py
# Select: 2 (List all API keys)
```

**Output:**
```
Key: ***abc123
  Name: MyApp
  Status: 🟢 Active
  Lock: 🔒 Locked
  Created: 2025-10-11T09:00:00.000000
  Usage: 42 times
  Last Used: 2025-10-11T12:00:00.000000
```

### Example 3: Reset Location Lock

```bash
python src/api_admin.py
# Select: 6 (Reset location lock)
# Enter API key: ff_abc123...
# Confirm: yes

# Now key can be used from new location
```

---

## 🔒 Security Features

### 1. IP-Based Locking
- IP address ko SHA-256 hash karke store kiya jata hai
- Original IP kabhi store nahi hoti (privacy)
- Different IP se access attempt automatically reject

### 2. User Agent Validation
- Browser/Device fingerprinting
- Same device se hi access allowed
- Extra security layer

### 3. Activation Control
- Keys ko activate/deactivate kar sakte ho
- Deactivated keys use nahi ho sakti

### 4. Admin Password Protection
- Admin endpoints password-protected
- Unauthorized access prevented

---

## 🔄 Common Operations

### Create New Key
```bash
python src/api_admin.py
# Option: 1
# Name: "Development"
# Copy key and save securely
```

### Deactivate Compromised Key
```bash
python src/api_admin.py
# Option: 5
# Enter key to deactivate
```

### Reactivate Key
```bash
python src/api_admin.py
# Option: 4
# Enter key to activate
```

### Change Location (Reset Lock)
```bash
python src/api_admin.py
# Option: 6
# Enter key to reset lock
# Key will lock to next IP that uses it
```

### Delete Old Key
```bash
python src/api_admin.py
# Option: 7
# Enter key to delete
# Confirm: yes
```

---

## 📊 Storage Format

**File:** `api_keys_storage.json`

```json
{
  "ff_abc123...": {
    "name": "Production",
    "created_at": "2025-10-11T09:00:00.000000",
    "locked_ip": "a1b2c3d4e5f6...",
    "locked_user_agent": "Mozilla/5.0...",
    "first_used_at": "2025-10-11T09:05:00.000000",
    "last_used_at": "2025-10-11T12:30:00.000000",
    "usage_count": 150,
    "is_active": true
  }
}
```

⚠️ **Important:** `api_keys_storage.json` automatically `.gitignore` mein add hai

---

## ⚠️ Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `API key missing` | Header mein key nahi bheji | `X-API-Key` header add karo |
| `Invalid API key` | Key exist nahi karti | Valid key use karo |
| `API key is deactivated` | Key disable kar di gayi hai | Admin se activate karwao |
| `API key is locked to a different location` | Different IP se access try ki | Same location se use karo ya reset lock |
| `API key is locked to a different device` | Different device se access | Same device se use karo |

---

## 🎯 Best Practices

### 1. Key Naming
- Descriptive names use karo: "Production", "Development", "TestServer"
- Purpose yaad rakhne mein help milti hai

### 2. Security
- Generated keys turant save karo
- `.env` file ya secure storage mein rakhao
- Public repositories mein mat daalo

### 3. Location Changes
- Reset lock sirf zaroorat padne pe karo
- Security risk ko samjho

### 4. Regular Cleanup
- Unused keys delete karo
- Old/expired keys deactivate karo

### 5. Monitoring
- Usage count regularly check karo
- Suspicious activity detect karo

---

## 🚨 Troubleshooting

### Problem: Key not working from same location
**Solution:** User agent changed ho sakta hai (browser update). Reset lock karo.

### Problem: Lost API key
**Solution:** Admin tool se list dekho, last 8 characters se identify karo.

### Problem: Need to use from multiple locations
**Solution:** Har location ke liye alag key create karo.

### Problem: Key accidentally deleted
**Solution:** Backup nahi hai. New key create karo.

---

## 📱 Integration Example

### Python Client
```python
import requests

API_KEY = "ff_your_api_key_here"
API_URL = "http://0.0.0.0:5000"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(
    f"{API_URL}/api/send-likes",
    headers=headers,
    json={
        "uid": 111119900,
        "region": "IND",
        "count": 50
    }
)

print(response.json())
```

### Node.js Client
```javascript
const axios = require('axios');

const API_KEY = 'ff_your_api_key_here';
const API_URL = 'http://0.0.0.0:5000';

axios.post(`${API_URL}/api/send-likes`, {
  uid: 111119900,
  region: 'IND',
  count: 50
}, {
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
}).then(response => {
  console.log(response.data);
});
```

---

## 🔐 Admin Password

**Setup (REQUIRED for production):**

```bash
# Method 1: Environment Variable (Recommended)
export FF_ADMIN_PASSWORD="your_secure_password_here"

# Method 2: .env file
echo "FF_ADMIN_PASSWORD=your_secure_password" >> .env
```

**Security Best Practices:**
- ✅ Use strong password (min 16 characters)
- ✅ Include uppercase, lowercase, numbers, special chars
- ✅ Never commit password to git
- ✅ Change regularly
- ❌ Don't use default password in production

---

## 📚 Quick Reference

| Command | Purpose |
|---------|---------|
| `python src/api_admin.py` | Admin CLI tool start |
| `Option 1` | New key create |
| `Option 2` | All keys list |
| `Option 5` | Key deactivate |
| `Option 6` | Location lock reset |
| `Option 7` | Key delete |

---

**Developed with 🔒 for secure API access**
