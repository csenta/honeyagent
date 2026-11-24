"""
Data models and token definitions for HoneyAgent.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TokenType(str, Enum):
    AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
    DATABASE_DSN = "DATABASE_DSN"
    API_BEARER_TOKEN = "API_BEARER_TOKEN"
    CANARY_DOCUMENT = "CANARY_DOCUMENT"


@dataclass
class Honeytoken:
    token_id: str
    token_type: TokenType
    value: str
    provenance_tag: str  # e.g., "rag:finance_q3_report", "doc:executive_salaries"
    callback_url: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TripwireIncident:
    incident_id: str
    token_id: str
    token_type: str
    provenance_tag: str
    attacker_ip: str
    user_agent: str
    request_method: str
    request_path: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    headers: dict[str, str] = field(default_factory=dict)
