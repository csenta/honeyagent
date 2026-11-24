"""
Persistent Honeytoken Registry and Provenance Ledger.
"""

import json
import os
from honeyagent.core.models import Honeytoken, TokenType


class HoneytokenRegistry:
    def __init__(self, registry_path: str = "honeyagent_registry.json"):
        self.registry_path = registry_path
        self.tokens: dict[str, Honeytoken] = {}
        self.value_index: dict[str, str] = {}  # token_value -> token_id
        self.load()

    def load(self):
        if not os.path.isfile(self.registry_path):
            return
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("tokens", []):
                t = Honeytoken(
                    token_id=item["token_id"],
                    token_type=TokenType(item["token_type"]),
                    value=item["value"],
                    provenance_tag=item["provenance_tag"],
                    callback_url=item["callback_url"],
                    created_at=item["created_at"],
                    description=item.get("description", ""),
                    metadata=item.get("metadata", {}),
                )
                self.tokens[t.token_id] = t
                self.value_index[t.value] = t.token_id
        except Exception:
            pass

    def save(self):
        data = {
            "tokens": [
                {
                    "token_id": t.token_id,
                    "token_type": t.token_type.value,
                    "value": t.value,
                    "provenance_tag": t.provenance_tag,
                    "callback_url": t.callback_url,
                    "created_at": t.created_at,
                    "description": t.description,
                    "metadata": t.metadata,
                }
                for t in self.tokens.values()
            ]
        }
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register(self, token: Honeytoken):
        self.tokens[token.token_id] = token
        self.value_index[token.value] = token.token_id
        self.save()

    def get(self, token_id: str) -> Honeytoken | None:
        return self.tokens.get(token_id)

    def lookup_value(self, value: str) -> Honeytoken | None:
        tid = self.value_index.get(value)
        return self.tokens.get(tid) if tid else None

    def list_all(self) -> list[Honeytoken]:
        return list(self.tokens.values())
