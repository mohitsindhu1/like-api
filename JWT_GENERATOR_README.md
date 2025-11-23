# 🔐 FreeFire JWT Generator

Guest account ke UID aur Password se JWT token generate karne ke liye standalone tools.

## 📋 Features

- ✅ **Standalone** - Independent scripts, koi dependency nahi
- ✅ **Secure** - AES-CBC encryption with protobuf
- ✅ **Fast** - Async/await for speed
- ✅ **Two Versions** - Interactive aur CLI dono

---

## 🚀 Usage

### Option 1: Interactive Version (User-Friendly)

```bash
python jwt_generator.py
```

**Kya hota hai:**
1. UID input karo
2. Password input karo
3. JWT token mil jayega with region aur server URL

**Output Example:**
```
============================================================
        🔐 FreeFire JWT Generator
============================================================

📱 Guest UID enter karo: 1234567890
🔑 Guest Password enter karo: abc123def456

[1/3] Access Token obtain kar rahe hain...
   ✓ Access Token: xyzabc123...
   ✓ Open ID: 9876543210

[2/3] Protobuf request bana rahe hain...
   ✓ Protobuf serialized: 89 bytes
   ✓ AES-CBC encrypted: 96 bytes

[3/3] JWT generate kar rahe hain...
   ✓ JWT Token successfully generated!

============================================================
        ✅ JWT SUCCESSFULLY GENERATED!
============================================================

🎫 JWT Token:
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

🌍 Region: IND
🖥️  Server URL: https://client.ind.freefiremobile.com

============================================================

📄 JSON Format:
{
  "jwt_token": "eyJhbGc...",
  "region": "IND",
  "server_url": "https://client.ind.freefiremobile.com",
  "uid": "1234567890"
}
```

---

### Option 2: CLI Version (For Scripts/Automation)

```bash
python jwt_cli.py <UID> <PASSWORD>
```

**Examples:**
```bash
# Basic usage
python jwt_cli.py 1234567890 abc123def456789

# Save to file
python jwt_cli.py 1234567890 abc123def456789 > jwt_output.json

# Use in bash script
JWT=$(python jwt_cli.py 1234567890 abc123def456789 | jq -r '.jwt_token')
echo "JWT Token: $JWT"
```

**Success Output:**
```json
{
  "success": true,
  "jwt_token": "eyJhbGciOiJIUzI1NiIs...",
  "region": "IND",
  "server_url": "https://client.ind.freefiremobile.com",
  "uid": "1234567890"
}
```

**Error Output:**
```json
{
  "success": false,
  "error": "Failed to obtain access token"
}
```

---

## 🔧 How It Works

### Process Flow:

```
UID + Password
    ↓
[1] OAuth Request → Access Token + Open ID
    ↓
[2] Protobuf Encoding → LoginReq message
    ↓
[3] AES-CBC Encryption → Encrypted payload
    ↓
[4] MajorLogin API → JWT Token + Region + Server URL
```

### Technical Details:

1. **Access Token** 
   - Endpoint: `https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant`
   - Method: POST (form-data)
   - Returns: `access_token` aur `open_id`

2. **Protobuf Encoding**
   - Message: `LoginReq`
   - Fields: open_id, open_id_type, login_token, orign_platform_type
   - Serialization: Binary protobuf

3. **AES-CBC Encryption**
   - Algorithm: AES-256-CBC
   - Key: Base64 decoded constant
   - IV: Base64 decoded constant
   - Padding: PKCS7

4. **JWT Generation**
   - Endpoint: `https://loginbp.ggblueshark.com/MajorLogin`
   - Method: POST (binary data)
   - Headers: Unity version, Release version, User-Agent
   - Returns: JWT token, region, server URL

---

## 📦 Dependencies

```bash
pip install httpx protobuf pycryptodome
```

Or use the requirements:
```bash
pip install -r requirements.txt
```

---

## 🎯 Use Cases

### 1. Manual Testing
```bash
python jwt_generator.py
```

### 2. Automation Scripts
```bash
#!/bin/bash
UID="1234567890"
PASS="abc123def456"

RESULT=$(python jwt_cli.py $UID $PASS)
JWT=$(echo $RESULT | jq -r '.jwt_token')

echo "JWT: $JWT"
```

### 3. Batch Processing
```bash
# Multiple accounts ka JWT generate karo
while read uid pass; do
    python jwt_cli.py "$uid" "$pass" >> all_jwts.json
done < accounts.txt
```

### 4. Python Integration
```python
import subprocess
import json

def get_jwt(uid, password):
    result = subprocess.run(
        ['python', 'jwt_cli.py', uid, password],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

jwt_data = get_jwt('1234567890', 'abc123def456')
print(f"JWT: {jwt_data['jwt_token']}")
```

---

## 🛡️ Security Notes

- ⚠️ **Password Safety**: Guest passwords ko safely store karo
- ⚠️ **JWT Expiry**: JWT tokens expire hote hain, regenerate karo jab zarurat ho
- ⚠️ **Rate Limiting**: Too many requests se avoid karo
- ⚠️ **Encryption Keys**: MAIN_KEY aur MAIN_IV hardcoded hain (game ke liye fixed)

---

## 🐛 Troubleshooting

### Error: "Failed to obtain access token"
- Check UID aur password correct hai
- Internet connection verify karo
- Server down to nahi hai

### Error: "Failed to generate JWT"
- Access token valid hai
- Protobuf libraries properly installed hain
- Network connectivity stable hai

### Error: Import errors
```bash
pip install --upgrade httpx protobuf pycryptodome
```

---

## 📝 Notes

- Guest accounts ke liye specifically designed hai
- Garena Free Fire API ke sath kaam karta hai
- Production-ready code with error handling
- Region detection automatic hai (IND, BR, US, etc.)

---

## 🔗 Related Files

- `get_jwt.py` - Original JWT implementation
- `send_like.py` - Like sender jo JWT use karta hai
- `ff_proto/freefire_pb2.py` - Protobuf definitions

---

**Made with ❤️ for FreeFire automation**
