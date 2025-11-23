# Visit Profile API Guide

## Overview
Yeh API Free Fire profiles ko visits bhejne ke liye hai. Har server ke liye proper tokens automatically load hote hain.

## Endpoint

### Send Profile Visits
```
GET /visit/{SERVER}/{UID}
```

#### Parameters
- `SERVER` (required): Server name - IND, AG, NX, BD, PK
- `UID` (required): Free Fire UID (User ID)

**Note:** No count parameter needed! **ALL available tokens will be used automatically** ✨

## Server Configuration

### Token Mapping (Automatic)
- **IND Server** → Uses `data/tokens/ind_tokens.json` (1209 tokens available)
- **AG Server** → Uses `data/tokens/ag_tokens.json` (1150 tokens available)
- **NX Server** → Uses `data/tokens/nx_tokens.json` (99 tokens available)
- **BD Server** → Uses `data/tokens/bd_tokens.json`
- **PK Server** → Uses `data/tokens/pk_tokens.json`

### Server URLs (Automatic)
- **IND**: `https://client.ind.freefiremobile.com/GetPlayerPersonalShow`
- **AG**: `https://clientbp.ggblueshark.com/GetPlayerPersonalShow`
- **NX**: `https://client.us.freefiremobile.com/GetPlayerPersonalShow`
- **BD**: `https://clientbp.ggblueshark.com/GetPlayerPersonalShow`
- **PK**: `https://clientbp.ggblueshark.com/GetPlayerPersonalShow`

## Examples

### 1. Send visits to IND server (uses ALL 1209 tokens)
```bash
GET https://your-domain.com/visit/IND/4240853256
```

### 2. Send visits to AG server (uses ALL 1150 tokens)
```bash
GET https://your-domain.com/visit/AG/4240977931
```

### 3. Send visits to NX server (uses ALL 99 tokens)
```bash
GET https://your-domain.com/visit/NX/4231030664
```

## Response Format

### Success Response
```json
{
  "success": true,
  "server": "IND",
  "uid": 4240853256,
  "nickname": "MOHIT-00GA1H",
  "region": "IND",
  "level": 75,
  "likes": 15000,
  "visits_sent": 1000,
  "visits_failed": 0,
  "total_attempts": 1000,
  "tokens_used": 1209
}
```

### Error Response
```json
{
  "error": "❌ No valid tokens found for XYZ server",
  "server": "XYZ",
  "uid": 123456789
}
```

## How It Works

1. **Token Selection**: System automatically selects the correct token file based on server name
2. **URL Selection**: Proper server URL is automatically chosen
3. **ALL Tokens Used**: Automatically uses ALL available tokens (1209 for IND, 1150 for AG, 99 for NX)
4. **Batch Processing**: Visits are sent in batches of 100 at a time for fast processing
5. **Async Requests**: Uses aiohttp for fast parallel requests
6. **Player Info**: First successful response extracts player information
7. **Rotation**: Tokens are rotated automatically to distribute load

## Key Features

✅ **Automatic Token Routing** - IND tokens for IND, AG tokens for AG, etc.  
✅ **ALL Tokens Used** - No count parameter needed, uses ALL available tokens automatically  
✅ **Fast Processing** - Async/await for maximum speed (100 concurrent requests)  
✅ **Player Info Extraction** - Returns nickname, level, likes, region  
✅ **Error Handling** - Graceful handling of failed requests  
✅ **Smart Batching** - Processes in batches of 100 for optimal speed  

## Technical Details

- **Protocol**: Protobuf (Protocol Buffers)
- **Encryption**: AES encryption for request payloads
- **Authentication**: Bearer token in Authorization header
- **SSL**: Disabled for compatibility (ssl=False)
- **Concurrent Limit**: Unlimited (TCPConnector limit=0)

## Notes

- Har server ke liye sahi tokens automatically use hote hain
- Token files `data/tokens/` folder mein honi chahiye
- **Jitne bhi tokens available hain, sab ke sab automatically use honge** ✨
- IND: 1209 tokens use honge, AG: 1150 tokens, NX: 99 tokens
- Player info pehli successful response se extract hoti hai
- Failed requests automatically track hote hain
- No manual count specification needed!
