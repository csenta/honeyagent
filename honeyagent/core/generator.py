"""
Cryptographic Honeytoken Generator for HoneyAgent.
Synthesizes realistic, HMAC-signed decoy credentials and canary tripwires.
"""

import hashlib
import hmac
import uuid
from honeyagent.core.models import Honeytoken, TokenType


class HoneytokenGenerator:
    def __init__(self, hmac_secret: str, public_url: str = "http://localhost:8888"):
        self.secret = hmac_secret.encode("utf-8")
        self.public_url = public_url.rstrip("/")

    def _sign(self, raw_id: str) -> str:
        h = hmac.new(self.secret, raw_id.encode("utf-8"), hashlib.sha256)
        return h.hexdigest()[:12]

    def verify_token_signature(self, token_id: str) -> bool:
        """Verifies if the token_id was legitimately issued by this instance."""
        parts = token_id.split("_")
        if len(parts) < 3:
            return False
        sig = parts[-1]
        raw_id = "_".join(parts[:-1])
        expected_sig = self._sign(raw_id)
        return hmac.compare_digest(sig, expected_sig)

    def generate(
        self,
        token_type: TokenType,
        provenance_tag: str,
        description: str = "",
    ) -> Honeytoken:
        uid = uuid.uuid4().hex[:8]
        raw_id = f"ht_{token_type.value.lower()}_{uid}"
        signature = self._sign(raw_id)
        token_id = f"{raw_id}_{signature}"

        callback_url = f"{self.public_url}/beacon/{token_id}"
        value = ""
        metadata = {}

        if token_type == TokenType.AWS_ACCESS_KEY:
            # Generate realistic AWS Access Key ID: AKIA + 16 chars
            # Embed short hash so AWS STS simulator recognizes it
            short_hash = hashlib.md5(token_id.encode("utf-8")).hexdigest()[:16].upper()
            value = f"AKIA{short_hash}"
            metadata = {
                "secret_access_key": f"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY_{signature}",
                "region": "us-east-1",
            }

        elif token_type == TokenType.DATABASE_DSN:
            # Generate realistic Postgres connection string pointing to callback host
            host = self.public_url.replace("http://", "").replace("https://", "").split(":")[0]
            port = "5432"
            value = f"postgresql://app_read_{uid}:{signature}@{host}:{port}/prod_vault?sslmode=require"
            metadata = {"database": "prod_vault", "username": f"app_read_{uid}"}

        elif token_type == TokenType.API_BEARER_TOKEN:
            # Generate realistic JWT-like or bearer format
            value = f"sec_live_{token_id}"
            metadata = {"scope": "read:all,admin:users"}

        elif token_type == TokenType.CANARY_DOCUMENT:
            # HTML/Markdown tripwire document with embedded image tracker
            value = (
                f"# Confidential Enterprise Document [{provenance_tag}]\n\n"
                f"INTERNAL USE ONLY. DO NOT DISTRIBUTE.\n\n"
                f"<!-- Telemetry Beacon -->\n"
                f"![Beacon]({callback_url})\n\n"
                f"Projected Q4 EBITDA and Executive Compensation details are stored in internal secure vault."
            )
            metadata = {"beacon_format": "markdown_image"}

        return Honeytoken(
            token_id=token_id,
            token_type=token_type,
            value=value,
            provenance_tag=provenance_tag,
            callback_url=callback_url,
            description=description,
            metadata=metadata,
        )
