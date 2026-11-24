# HoneyAgent API Specification

HoneyAgent provides both an internal Python API and an external HTTP Callback / Tripwire API.

---

## 1. HTTP Tripwire API

### `GET /status`
Health check and active token summary.
- **Response**: `200 OK`
```json
{
  "service": "HoneyAgent Tripwire Listener",
  "active_tokens": 12,
  "status": "listening"
}
```

### `GET /beacon/{token_id}`
Image tracker endpoint triggered when a canary document is opened, rendered, or scraped.
- **Parameters**: `token_id` (HMAC-signed token ID)
- **Response**: `200 OK` (1x1 Transparent GIF `image/gif`)
- **Side Effect**: Emits intrusion incident alert, logs IP, user-agent, and provenance tag.

### `ANY /api/v1/auth`, `ANY /api/v1/user`
Trap for unauthorized usage of decoy API Bearer tokens.
- **Headers**: `Authorization: Bearer sec_live_ht_...`
- **Response**: `401 Unauthorized`
```json
{
  "error": "Invalid or revoked credentials"
}
```

### `ANY /aws-sts`
Trap for decoy AWS Access Keys (`AKIA...`).
- **Body / Header**: Contains `AWSAccessKeyId=AKIA...`
- **Response**: `403 Forbidden` (`InvalidClientTokenId` XML format)

---

## 2. Python Core API

```python
from honeyagent.core.generator import HoneytokenGenerator
from honeyagent.core.models import TokenType
from honeyagent.core.registry import HoneytokenRegistry

generator = HoneytokenGenerator(hmac_secret="production_key", public_url="https://honey.example.com")
registry = HoneytokenRegistry("registry.json")

# Generate token
token = generator.generate(
    token_type=TokenType.AWS_ACCESS_KEY,
    provenance_tag="rag:q3_earnings",
)
registry.register(token)

print(token.value)
# => AKIA...
```
