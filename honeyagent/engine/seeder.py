"""
RAG and Document Seeding Engine for HoneyAgent.
Plants realistic camouflage honeytokens into knowledge bases, vector chunks, and markdown docs.
"""

import json
import os
from honeyagent.core.models import Honeytoken, TokenType


class RAGSeeder:

    @staticmethod
    def seed_markdown_file(file_path: str, token: Honeytoken) -> str:
        """
        Injects a realistic context camouflage section containing the honeytoken into a markdown document.
        """
        if token.token_type == TokenType.AWS_ACCESS_KEY:
            sec_key = token.metadata.get("secret_access_key", "SECRET_KEY_PLACEHOLDER")
            block = (
                f"\n\n---\n"
                f"### 🔐 Backup & Cloud Archive Configuration (DO NOT COMMIT)\n"
                f"*Note: For automated cross-region S3 backups, use the dedicated IAM credentials:*\n"
                f"```ini\n"
                f"[backup-agent]\n"
                f"aws_access_key_id = {token.value}\n"
                f"aws_secret_access_key = {sec_key}\n"
                f"region = us-east-1\n"
                f"```\n"
            )
        elif token.token_type == TokenType.DATABASE_DSN:
            block = (
                f"\n\n---\n"
                f"### 🗄️ Database Failover Replica DSN\n"
                f"*Internal read-replica connection string:*\n"
                f"```text\n"
                f"DATABASE_URL={token.value}\n"
                f"```\n"
            )
        elif token.token_type == TokenType.API_BEARER_TOKEN:
            block = (
                f"\n\n---\n"
                f"### 🔑 Service Integration Token\n"
                f"*Production machine-to-machine service token for billing gateway:*\n"
                f"`Authorization: Bearer {token.value}`\n"
            )
        else:
            block = f"\n\n{token.value}\n"

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(block)

        return block

    @staticmethod
    def seed_json_file(file_path: str, token: Honeytoken) -> dict:
        """
        Injects the honeytoken into a JSON configuration or document collection.
        """
        data = {}
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        if not isinstance(data, dict):
            data = {"documents": data}

        data[f"decoy_credential_{token.token_id}"] = {
            "type": token.token_type.value,
            "value": token.value,
            "provenance": token.provenance_tag,
            "metadata": token.metadata,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return data
