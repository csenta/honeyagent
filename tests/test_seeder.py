import json
import os
import tempfile
import unittest
from honeyagent.core.generator import HoneytokenGenerator
from honeyagent.core.models import TokenType
from honeyagent.engine.seeder import RAGSeeder


class TestRAGSeeder(unittest.TestCase):
    def setUp(self):
        self.gen = HoneytokenGenerator(hmac_secret="test_seeder_secret")

    def test_seed_markdown_file(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".md") as f:
            f.write("# Internal Developer Documentation\n\nWelcome to engineering docs.")
            md_path = f.name

        try:
            token = self.gen.generate(TokenType.AWS_ACCESS_KEY, "rag:cloud_docs")
            RAGSeeder.seed_markdown_file(md_path, token)

            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn(token.value, content)
            self.assertIn("Backup & Cloud Archive Configuration", content)
        finally:
            if os.path.exists(md_path):
                os.remove(md_path)

    def test_seed_json_file(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as f:
            json.dump({"company": "Acme Corp"}, f)
            json_path = f.name

        try:
            token = self.gen.generate(TokenType.API_BEARER_TOKEN, "rag:api_spec")
            RAGSeeder.seed_json_file(json_path, token)

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            key = f"decoy_credential_{token.token_id}"
            self.assertIn(key, data)
            self.assertEqual(data[key]["value"], token.value)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)


if __name__ == "__main__":
    unittest.main()
