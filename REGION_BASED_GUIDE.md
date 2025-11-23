# 🌍 Region-Based Guest Account System

Different regions ke guest accounts ko alag-alag manage aur use karne ka complete guide.

---

## 📋 Overview

Ye system aapko allow karta hai:
- ✅ Multiple regions ke guest accounts maintain karna (BD, IND, BR, US, etc.)
- ✅ Region-specific accounts se likes bhejna
- ✅ Accounts ko automatically track karna (duplicates avoid)
- ✅ Targeted like campaigns chalana

---

## 🚀 Quick Start

### Step 1: Convert Your Guest Accounts

Agar aapke paas raw guest accounts hain (JSON format mein), toh unhe region-specific format mein convert karo:

```bash
python convert_region_guests.py <input_file> <region>
```

**Examples:**
```bash
# Bangladesh accounts
python convert_region_guests.py BD_ACC.json BD

# India accounts  
python convert_region_guests.py IND_ACC.json IND

# Brazil accounts
python convert_region_guests.py BR_ACC.json BR

# USA accounts
python convert_region_guests.py USA_ACC.json US
```

### Step 2: Send Region-Specific Likes

Region-specific accounts se likes bhejne ke liye:

```bash
python send_like_region.py
```

Ye aapko prompts dega:
1. **Region select karo** (BD, IND, BR, etc.)
2. **Target UID enter karo** (jisko like bhejni hai)
3. **Like count** (kitni likes)
4. **Concurrency** (kitni fast)

---

## 📊 Current Available Regions

Check karo ki kitne regions available hain:

```bash
cat guests_manager/region_based/regions.json
```

**Current Status:**
```json
{
  "BD": {
    "count": 165,
    "file": "BD_guests.json"
  },
  "IND": {
    "count": 161,
    "file": "IND_guests.json"
  }
}
```

---

## 💡 Use Cases

### 1. Region-Specific Campaign
```bash
# Sirf BD accounts se likes bhejo
python send_like_region.py
> Select region: BD
> UID: 1234567890
> Likes: 50
```

### 2. Multi-Region Strategy
```bash
# Pehle IND accounts use karo
python send_like_region.py
> Region: IND
> UID: 1234567890
> Likes: 100

# Phir BD accounts use karo
python send_like_region.py
> Region: BD
> UID: 1234567890
> Likes: 100
```

### 3. Batch Processing
```bash
# Multiple targets ko likes bhejo
for uid in 1111111111 2222222222 3333333333; do
    echo "Sending likes to $uid from BD..."
    python send_like_region.py << EOF
BD
$uid
50
20
EOF
done
```

---

## 📁 File Structure

```
guests_manager/
├── region_based/           # Region-specific directory
│   ├── regions.json       # Master region list
│   ├── BD_guests.json     # Bangladesh accounts
│   ├── IND_guests.json    # India accounts
│   ├── BR_guests.json     # Brazil accounts (when added)
│   └── US_guests.json     # USA accounts (when added)
│
├── guests_converted.json  # Old format (still works)
└── formatted_guests.json  # Old format (still works)
```

---

## 🔧 How It Works

### Convert Process:
```
Raw Guest JSON
    ↓
[Convert Script]
    ↓
Region-Specific JSON (BD/IND/BR/US)
    ↓
[Updated Master List]
```

### Like Sending Process:
```
Select Region (BD/IND/BR)
    ↓
Load Region Guests
    ↓
Filter Unused Guests (per target)
    ↓
Generate JWT for each guest
    ↓
Send Like with proper region headers
    ↓
Mark as used (permanent)
```

---

## 🌐 Supported Regions

| Region Code | Region Name | Server URL |
|------------|-------------|------------|
| **BD** | Bangladesh | `client.bd.freefiremobile.com` |
| **IND** | India | `client.ind.freefiremobile.com` |
| **BR** | Brazil | `client.us.freefiremobile.com` |
| **US** | USA | `client.us.freefiremobile.com` |
| **SAC** | South America | `client.us.freefiremobile.com` |
| **NA** | North America | `client.us.freefiremobile.com` |
| **SG** | Singapore | `client.sg.freefiremobile.com` |
| **RU** | Russia | `clientbp.ggblueshark.com` |

---

## ⚙️ Advanced Features

### 1. Check Region Stats
```bash
# Python script se
python -c "
import json
with open('guests_manager/region_based/regions.json') as f:
    regions = json.load(f)
for region, info in regions.items():
    print(f'{region}: {info[\"count\"]} accounts')
"
```

### 2. Merge Multiple Region Files
```bash
# Agar aapke paas ek hi region ke multiple files hain
python convert_region_guests.py BD_ACC_1.json BD
python convert_region_guests.py BD_ACC_2.json BD
# Automatically merge ho jayega
```

### 3. Export Unused Accounts
```python
# Find unused accounts for a target
import json

with open('usage_history/guest_usage_by_target.json') as f:
    usage = json.load(f)

with open('guests_manager/region_based/BD_guests.json') as f:
    bd_guests = json.load(f)

target_uid = "1234567890"
used = usage.get(target_uid, {}).get("used_guests", {})

unused = [g for g in bd_guests if g['uid'] not in used]
print(f"Unused BD accounts: {len(unused)}")
```

---

## 🎯 Best Practices

### 1. Region Selection
- ✅ **Use same region as target** - Better success rate
- ✅ **Mix regions** - More natural looking
- ✅ **Track per region** - Know which region works best

### 2. Rate Limiting
- ⚡ **Start slow** - 10-20 concurrent requests
- ⚡ **Monitor responses** - Check for errors
- ⚡ **Adjust speed** - Increase if stable

### 3. Account Management
- 💾 **Backup regularly** - Keep copies of guest files
- 💾 **Track usage** - Monitor which accounts used
- 💾 **Rotate regions** - Don't exhaust one region

---

## 🐛 Troubleshooting

### Error: "No region-based guests found"
**Solution:**
```bash
# Convert your accounts first
python convert_region_guests.py your_file.json BD
```

### Error: "Region BD not found"
**Solution:**
```bash
# Check available regions
cat guests_manager/region_based/regions.json

# Make sure region code is uppercase
python send_like_region.py
> Region: BD  # Not 'bd' or 'Bd'
```

### Error: "No available guests"
**Solution:**
```bash
# All accounts already used for this target
# Either:
# 1. Use different region
# 2. Add more accounts
# 3. Target different UID
```

---

## 📈 Stats & Monitoring

### Check Usage Statistics:
```bash
python -c "
import json
with open('usage_history/guest_usage_by_target.json') as f:
    usage = json.load(f)

for target, info in usage.items():
    total = info['total_likes']
    print(f'Target {target}: {total} likes sent')
"
```

### Check Region Availability:
```bash
python -c "
import json

# Load regions
with open('guests_manager/region_based/regions.json') as f:
    regions = json.load(f)

# Load usage
with open('usage_history/guest_usage_by_target.json') as f:
    usage = json.load(f)

target = input('Enter target UID: ')
used = usage.get(target, {}).get('used_guests', {})

print(f'\nAvailability for target {target}:')
for region, info in regions.items():
    with open(f'guests_manager/region_based/{region}_guests.json') as f:
        guests = json.load(f)
    unused = len([g for g in guests if g['uid'] not in used])
    print(f'  {region}: {unused}/{info[\"count\"]} available')
"
```

---

## 🔗 Related Tools

- **`convert_region_guests.py`** - Convert raw accounts to region format
- **`send_like_region.py`** - Send likes using region-specific accounts
- **`jwt_generator.py`** - Generate JWT for any account
- **`jwt_cli.py`** - CLI JWT generator for automation

---

## 📝 Notes

- ✅ **One-like-per-guest** - Ek guest ek target ko sirf ek baar like karega
- ✅ **Permanent tracking** - Usage history permanent hai
- ✅ **Region auto-detect** - JWT se region automatically detect hota hai
- ✅ **Cross-region support** - Kisi bhi region se kisi bhi region ko like bhej sakte ho

---

**Happy Liking! 🎉**
