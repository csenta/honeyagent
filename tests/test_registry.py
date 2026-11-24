import os
import tempfile
import unittest
from honeyagent.core.generator import HoneytokenGenerator
from honeyagent.core.models import TokenType
from honeyagent.core.registry import HoneytokenRegistry


class TestHoneytokenRegistry(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.registry = HoneytokenRegistry(registry_path=self.temp_file.name)
        self.gen = HoneytokenGenerator(hmac_secret="test_secret")

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_register_and_retrieve(self):
        token = self.gen.generate(TokenType.API_BEARER_TOKEN, "rag:finance")
        self.registry.register(token)

        fetched = self.registry.get(token.token_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.token_id, token.token_id)
        self.assertEqual(fetched.value, token.value)

    def test_value_lookup(self):
        token = self.gen.generate(TokenType.AWS_ACCESS_KEY, "rag:aws")
        self.registry.register(token)

        looked_up = self.registry.lookup_value(token.value)
        self.assertIsNotNone(looked_up)
        self.assertEqual(looked_up.token_id, token.token_id)

    def test_persistence(self):
        token1 = self.gen.generate(TokenType.DATABASE_DSN, "rag:infra")
        self.registry.register(token1)

        # Reload registry from disk
        new_registry = HoneytokenRegistry(registry_path=self.temp_file.name)
        self.assertEqual(len(new_registry.list_all()), 1)
        self.assertEqual(new_registry.get(token1.token_id).value, token1.value)


if __name__ == "__main__":
    unittest.main()
