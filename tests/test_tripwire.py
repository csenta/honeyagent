import os
import tempfile
import unittest
from fastapi.testclient import TestClient

from honeyagent.core.generator import HoneytokenGenerator
from honeyagent.core.models import TokenType
from honeyagent.core.registry import HoneytokenRegistry
from honeyagent.engine.alerts import AlertDispatcher
from honeyagent.server.listener import create_tripwire_app, TRANSPARENT_GIF


class TestTripwireListener(unittest.TestCase):
    def setUp(self):
        self.reg_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.reg_file.close()
        self.log_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.log_file.close()

        self.generator = HoneytokenGenerator(hmac_secret="tripwire_secret")
        self.registry = HoneytokenRegistry(registry_path=self.reg_file.name)
        self.dispatcher = AlertDispatcher(incident_log_path=self.log_file.name)

        self.app = create_tripwire_app(
            registry=self.registry,
            generator=self.generator,
            dispatcher=self.dispatcher,
        )
        self.client = TestClient(self.app)

    def tearDown(self):
        for path in (self.reg_file.name, self.log_file.name):
            if os.path.exists(path):
                os.remove(path)

    def test_health_check(self):
        resp = self.client.get("/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "listening")

    def test_canary_image_beacon(self):
        token = self.generator.generate(TokenType.CANARY_DOCUMENT, "rag:executive_brief")
        self.registry.register(token)

        resp = self.client.get(f"/beacon/{token.token_id}", headers={"user-agent": "ExfiltrationBot/1.0"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "image/gif")
        self.assertEqual(resp.content, TRANSPARENT_GIF)

        # Verify incident logged
        with open(self.log_file.name, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertIn(token.token_id, lines[0])
        self.assertIn("ExfiltrationBot", lines[0])

    def test_bearer_token_probe(self):
        token = self.generator.generate(TokenType.API_BEARER_TOKEN, "rag:vault_docs")
        self.registry.register(token)

        resp = self.client.get("/api/v1/user", headers={"authorization": f"Bearer {token.value}"})
        self.assertEqual(resp.status_code, 401)

        with open(self.log_file.name, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertIn(token.token_id, lines[0])

    def test_aws_sts_probe(self):
        token = self.generator.generate(TokenType.AWS_ACCESS_KEY, "rag:infra_code")
        self.registry.register(token)

        body = f"Action=GetCallerIdentity&AWSAccessKeyId={token.value}"
        resp = self.client.post("/aws-sts", content=body, headers={"content-type": "application/x-www-form-urlencoded"})
        self.assertEqual(resp.status_code, 403)
        self.assertIn("InvalidClientTokenId", resp.text)

        with open(self.log_file.name, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertIn(token.token_id, lines[0])


if __name__ == "__main__":
    unittest.main()
