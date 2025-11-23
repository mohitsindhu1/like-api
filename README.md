# FreeFire Guest generator, Like & API Toolkit
---
## Disclaimer & Responsible Use

**Important — read before using this repository.**

This project is provided **solely for research, defensive testing, educational and interoperability purposes**. By using the code in this repository you agree to all of the following:

- **Lawful, authorized use only.** You must have explicit authorization from the owner of any systems, accounts, or services you interact with. Do **not** use this software to access, modify, or automate accounts, services, or data that you do not own or do not have written permission to test.

- **Respect third-party terms and local law.** Many online services explicitly prohibit automated account creation, automated interactions, or reverse engineering in their Terms of Service. You are responsible for ensuring your use complies with all applicable laws and the terms of any service you interact with.

- **No endorsement of malicious activity.** The author(s) and contributors do **not** condone, support, or assist fraud, harassment, spam, unauthorized account access, or any other malicious behavior. Use of this code to perform such activities is strictly prohibited.

- **No warranty — use at your own risk.** This software is provided **as-is**, with no warranties of any kind (express or implied). The author(s) expressly disclaim all liability for damages or losses resulting from the use, misuse, or inability to use this code.

- **Operational safety and limits.** If you use automation against live services, tune concurrency and rate limits responsibly. Excessive or careless automated requests can harm services, trigger blocks, or expose you to legal risk.

- **Data handling & privacy.** Any account data, tokens, or personally identifiable information captured or stored using the tools in this repository must be handled in accordance with applicable privacy laws. Do not retain or publish data that you are not authorized to store.

- **Responsible disclosure.** If you discover a security vulnerability in third-party software while using this project, follow responsible disclosure best practices: do not exploit the issue, and report it privately to the affected vendor or maintainer.

### Removal or modification of this disclaimer
If you are a repository maintainer or developer and wish to remove or modify this disclaimer, **contact the repository owner first** at **kaifcodec@gmail.com** to request permission and discuss legal/ethical considerations. Changes to the disclaimer should not be used to enable or excuse unlawful or unauthorized activity.

---

If you are unsure whether a planned use is permitted, **stop and seek explicit legal or organizational authorization** before proceeding.
---

Automates creating and capturing **Free Fire guest accounts** via **Frida**, formats and manages them, obtains **JWTs**, and sends encrypted like requests to a target UID with **concurrency controls** and **one-like-per-guest-per-target guarantees**.

---

## ⚡ Features
- Capture guest **uid/password/token** from the Android app via **Frida hooks** and persist on-device with de-duplication.
- **Auto-loop** guest creation by restarting after successful registration to mass-generate accounts.
- Convert captured guests into structured **JSONs**, skipping duplicates and invalid entries.
- Authenticate guests to obtain a **JWT** using **AES-CBC–wrapped protobuf requests**.
- Build protobuf **LikeProfile payloads**, **AES-CBC encrypt** them, and send **concurrent likes** with usage tracking.

---

## Repository structure
- **dev/frida_injections**: Frida scripts for capture and auto-restart flows.
- **ff_proto**: Protobufs used by authentication and like payload builders.
- **guests_manager**: Tools and data for formatting and storing captured guests.
- **Python clients**: JWT acquisition, like payload encryption, and like sender.
- **index.js**: Il2Cpp/Frida helpers used by injection scripts.

---

## Prerequisites
- **Android device** with **Frida server** or **Frida Gadget**, reachable via USB or TCP.
- **Python 3.10+** with `httpx`, `pycryptodome`, `protobuf` installed.
- **Protobuf modules compiled** and present under `ff_proto` (`FreeFire_pb2.py`, `like_pb2.py`).

### Install:
    pip install httpx pycryptodome protobuf
    or 
    pip install -r requirements.txt
### Usage (For sending likes)
    python3 send_like.py
---

## 👤 Guest account creation workflow
- Attach `capture_and_save_guest.js` while launching the game to hook SharedPreferences and relevant classes, collecting uid/password/token.
- The script reads an existing `guest_accounts.json` in the app’s external media directory, appends unique entries, and writes atomically.
- Load `restart_after_register.js` to detect registration completion and trigger a timed restart for continuous guest generation.
- Load `index.js` or no hooking will work.

### Launch options:
- **Interactive**: `python3 dev/frida_injections/frida_manager.py` (choose USB/TCP and scripts).
- Then use image clicker to click on respective positions one after another and the script will work on its own save guest data in the apps permissible dir inside `Android/data/com.dts.freefiremax/`
- **Manual**: `frida -U -n Gadget -l dev/frida_injections/capture_and_save_guest.js -l dev/frida_injections/restart_after_register.js -l dev/frida_injections/index.js`.

### Notes:
- `frida_manager.py` validates connectivity, restarts sessions, and manages default script lists; adjust `PROCESS_NAME`/`DEFAULT_JS_SCRIPTS` as needed.

## Convert and deduplicate guests
- Run: `python3 guests_manager/save_guest.py` to merge new captures into repo JSONs.
- Outputs: `formatted_guests.json` map and `guests_converted.json` flat array used by automation.
- Behavior: skips duplicates, ignores `unknown_*` placeholders, preserves numbering, and reports counts.

---


## Builds encrypted Like payload
- **Function**: `create_like_payload(uid_to_like, region) -> bytes (application/octet-stream)`
- **Internals**: constructs `like_pb2.like`, serializes, applies PKCS7 padding, AES-CBC encrypts the serialized bytes with `MAIN_KEY` / `MAIN_IV`, and returns the encrypted payload ready for POST.

---

## ⚡Send likes (concurrent, safe)

### Option 1: Simple API Endpoint (Recommended) ⭐
Sabse simple tarika - sirf URL call karo:

```bash
# Simple GET request
curl "http://localhost:5000/like?uid=123456&server=IND&api=your_key&count=50"

# Response
{
  "success": true,
  "uid": 123456,
  "server": "IND",
  "sent": 50,
  "requested": 50,
  "profile": {
    "username": "PlayerName",
    "current_likes": 1500
  }
}
```

**Parameters:**
- `uid`: Target UID jisko likes bhejna hai
- `server`: Region (IND, BD, BR, US, SG)
- `api`: Your API key
- `count`: Number of likes (optional, default 101)

### Option 2: Advanced API Endpoint
For detailed profile info and batch operations:

```bash
curl -X POST "http://localhost:5000/api/send-likes" \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"uid": 123456, "region": "IND", "count": 50}'
```

### Option 3: Command Line Script
- Run: `python3 send_like.py`, then provide target UID, desired like count, and max concurrency.
- **Behavior**:  
  - Loads guests from `guests_converted.json`  
  - Obtains JWT and region per guest (via the JWT flow) if not cached  
  - Builds an encrypted Like payload using `create_like_payload`  
  - Posts the encrypted payload to the LikeProfile endpoint with required headers and auth  
  - Retries transient errors and respects per-request backoff / RPS limits
- **Guarantee**: one-like-per-guest-per-target enforced via `usage_history/guest_usage_by_target.json`.
- Concurrency controls and RPS limiting are applied to reduce throttling and detect rate limits early.

---

## 🪛Configuration tips
- If using Gadget, keep `PROCESS_NAME="Gadget"`; otherwise set the app process name in `frida_manager.py`.
- Tune concurrency and RPS to avoid throttling and fit within daily per-target limits.
- Prefer the `server_url` returned by the JWT flow when endpoints are region-scoped.

---

## Data files
- `guests_manager/formatted_guests.json`: human-readable map of captured guests.
- `guests_manager/guests_converted.json`: automation-ready array used by the sender.
- `usage_history/guest_usage_by_target.json`: tracks which guest has liked which target to enforce one-like-per-guest-per-target.

---
## 🌲Project tree
```bash
freefire-like-and-guest-api/
├── LICENSE
├── README.md
├── dev
│   ├── frida_injections
│   │   ├── capture_and_save_guest.js
│   │   ├── frida_manager.py
│   │   ├── index.js
│   │   ├── not_imp
│   │   │   ├── class.js
│   │   │   ├── class_new.js
│   │   │   ├── decode_MajorRegister.py
│   │   │   ├── decoder.py
│   │   │   ├── decoder_rw_pb.py
│   │   │   ├── decrypt_like_body.py
│   │   │   ├── dummy.py
│   │   │   ├── encode.py
│   │   │   ├── encode_MajorRegister.py
│   │   │   ├── find_blob.js
│   │   │   ├── frida_manger.py
│   │   │   ├── log_class.js
│   │   │   ├── main.py
│   │   │   ├── native_ssl_bypass.js
│   │   │   ├── nativelog.js
│   │   │   ├── nativelog_new.js
│   │   │   ├── platform_info_constructor.js
│   │   │   ├── protobufwalker.py
│   │   │   ├── rawhex.hex
│   │   │   ├── register.py
│   │   │   ├── req_body_likeprofile.py
│   │   │   └── requst_body.hex
│   │   └── restart_after_register.js
│   └── not_imp
│       ├── decoder.py
│       ├── like.py
│       ├── main.py
│       ├── proto_brute
│       │   ├── PlatformRegisterReq.proto
│       │   ├── PlatformRegisterReq_pb2.py
│       │   ├── PlatformRegisterReq_template.proto
│       │   ├── main.py
│       │   ├── proto_trials
│       │   │   ├── PlatformRegisterReq.proto
│       │   │   └── PlatformRegisterReq_pb2.py
│       │   └── rawhex.hex
│       └── rawhex.hex
├── encrypt_like_body.py
├── ff_proto
│   ├── account_show_pb2.py
│   ├── core_pb2.py
│   ├── count_likes_pb2.py
│   ├── freefire_pb2.py
│   ├── register_req.proto
│   ├── register_req_pb2.py
│   └── send_like_pb2.py
├── get_jwt.py
├── guests_manager
│   ├── count_guest.py
│   ├── formatted_guests.json
│   ├── guests_converted.json
│   ├── rm_duplicates.py
│   ├── save_guest.py
│   └── unreg_guests
│       ├── formatted_guests.json.lock
│       └── guests_converted_unregisterd.json
├── requirements.txt
└── send_like.py
└── usage_history

```

- 💎 Inside the `dev/not_imp` & `dev/frida_injections/not_imp/` there are my all works, the scripts, methods i used to create this repository. It's more than a diamond if you can understand what those things are for.
