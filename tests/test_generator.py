import unittest
from honeyagent.core.generator import HoneytokenGenerator
from honeyagent.core.models import TokenType


class TestHoneytokenGenerator(unittest.TestCase):
    def setUp(self):
        self.secret = "test_secret_key_12345"
        self.gen = HoneytokenGenerator(hmac_secret=self.secret, public_url="http://localhost:8888")

    def test_signature_and_verification(self):
        token = self.gen.generate(TokenType.API_BEARER_TOKEN, "rag:test_doc")
        self.assertTrue(self.gen.verify_token_signature(token.token_id))

        # Tampered token
        tampered_id = token.token_id[:-4] + "ffff"
        self.assertFalse(self.gen.verify_token_signature(tampered_id))

    def test_aws_access_key_generation(self):
        token = self.gen.generate(TokenType.AWS_ACCESS_KEY, "rag:aws_guide")
        self.assertTrue(token.value.startswith("AKIA"))
        self.assertEqual(len(token.value), 20)
        self.assertIn("secret_access_key", token.metadata)
        self.assertEqual(token.metadata["region"], "us-east-1")
        self.assertIn("/beacon/", token.callback_url)

    def test_database_dsn_generation(self):
        token = self.gen.generate(TokenType.DATABASE_DSN, "rag:db_manual")
        self.assertTrue(token.value.startswith("postgresql://"))
        self.assertIn("@localhost:5432/prod_vault", token.value)

    def test_canary_document_generation(self):
        token = self.gen.generate(TokenType.CANARY_DOCUMENT, "doc:financials")
        self.assertIn(token.callback_url, token.value)
        self.assertIn("INTERNAL USE ONLY", token.value)


if __name__ == "__main__":
    unittest.main()
