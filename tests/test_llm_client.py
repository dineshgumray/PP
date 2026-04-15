import unittest
from unittest.mock import patch

from services.llm_client import (
    GroqClient,
    LLMClientError,
    extract_anthropic_text,
    extract_gemini_text,
    extract_openai_text,
)


class LLMClientParsingTests(unittest.TestCase):
    def test_extract_openai_text(self):
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "First line."},
                        {"type": "output_text", "text": "Second line."},
                    ],
                }
            ]
        }

        self.assertEqual(extract_openai_text(payload), "First line.\nSecond line.")

    def test_extract_openai_text_supports_output_text(self):
        payload = {"output_text": "Groq answer."}

        self.assertEqual(extract_openai_text(payload), "Groq answer.")

    def test_extract_gemini_text(self):
        payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Gemini answer."},
                        ]
                    }
                }
            ]
        }

        self.assertEqual(extract_gemini_text(payload), "Gemini answer.")

    def test_extract_anthropic_text(self):
        payload = {
            "content": [
                {"type": "text", "text": "Claude answer."},
            ]
        }

        self.assertEqual(extract_anthropic_text(payload), "Claude answer.")

    @patch("services.llm_client.GroqClient.post_json", return_value={"output_text": "Groq answer."})
    def test_groq_client_generate_returns_text(self, _mock_post_json):
        client = GroqClient(
            api_key="test-groq-key",
            base_url="https://api.groq.com/openai/v1",
            default_model="llama-3.3-70b-versatile",
        )

        self.assertEqual(client.generate("Say hello."), "Groq answer.")

    def test_groq_client_generate_requires_api_key(self):
        client = GroqClient(
            api_key="",
            base_url="https://api.groq.com/openai/v1",
            default_model="llama-3.3-70b-versatile",
        )

        with self.assertRaises(LLMClientError) as exc:
            client.generate("Say hello.")

        self.assertIn("GROQ_API_KEY", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
