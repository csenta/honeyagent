"""
Intrusion Alert Dispatcher for HoneyAgent.
Records tripwire activations to JSONL and dispatches webhooks to SIEM/Slack.
"""

import json
from honeyagent.core.models import TripwireIncident


class AlertDispatcher:
    def __init__(self, incident_log_path: str = "honeyagent_incidents.jsonl", webhook_url: str = ""):
        self.incident_log_path = incident_log_path
        self.webhook_url = webhook_url

    def dispatch(self, incident: TripwireIncident):
        # 1. Print High-Visibility Security Alarm
        print("\n" + "=" * 70)
        print("🚨 [HONEYAGENT INTRUSION ALARM] HONEYTOKEN ACTIVATED!")
        print(f"   Token ID:        {incident.token_id}")
        print(f"   Token Type:      {incident.token_type}")
        print(f"   Provenance:      {incident.provenance_tag}")
        print(f"   Attacker IP:     {incident.attacker_ip}")
        print(f"   User Agent:      {incident.user_agent}")
        print(f"   Request:         {incident.request_method} {incident.request_path}")
        print(f"   Timestamp:       {incident.timestamp}")
        print("=" * 70 + "\n")

        # 2. Append to JSONL Audit Log
        record = {
            "incident_id": incident.incident_id,
            "token_id": incident.token_id,
            "token_type": incident.token_type,
            "provenance_tag": incident.provenance_tag,
            "attacker_ip": incident.attacker_ip,
            "user_agent": incident.user_agent,
            "request_method": incident.request_method,
            "request_path": incident.request_path,
            "timestamp": incident.timestamp,
            "headers": incident.headers,
        }

        try:
            with open(self.incident_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

        # 3. Optional Webhook Delivery (Non-blocking attempt)
        if self.webhook_url:
            import urllib.request
            try:
                payload = json.dumps({"text": f"🚨 HoneyAgent Alert: Token {incident.token_id} triggered from {incident.attacker_ip}!"}).encode()
                req = urllib.request.Request(self.webhook_url, data=payload, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass
