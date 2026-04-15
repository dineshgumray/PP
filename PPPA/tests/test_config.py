import os
import tempfile
import unittest
from pathlib import Path

from app import load_dotenv_file


class DotenvLoadingTests(unittest.TestCase):
    def test_load_dotenv_file_sets_values_without_overwriting_existing_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env"
            dotenv_path.write_text(
                "OPENAI_MODEL=gpt-4.1-mini\nGEMINI_MODEL=gemini-2.5-pro\nSECRET_KEY=from-file\n",
                encoding="utf-8",
            )

            original_secret = os.environ.get("SECRET_KEY")
            original_openai_model = os.environ.get("OPENAI_MODEL")
            original_gemini_model = os.environ.get("GEMINI_MODEL")
            os.environ["SECRET_KEY"] = "from-env"
            os.environ.pop("OPENAI_MODEL", None)
            os.environ.pop("GEMINI_MODEL", None)

            try:
                load_dotenv_file(dotenv_path)
                self.assertEqual(os.environ["SECRET_KEY"], "from-env")
                self.assertEqual(os.environ["OPENAI_MODEL"], "gpt-4.1-mini")
                self.assertEqual(os.environ["GEMINI_MODEL"], "gemini-2.5-pro")
            finally:
                if original_secret is None:
                    os.environ.pop("SECRET_KEY", None)
                else:
                    os.environ["SECRET_KEY"] = original_secret

                if original_openai_model is None:
                    os.environ.pop("OPENAI_MODEL", None)
                else:
                    os.environ["OPENAI_MODEL"] = original_openai_model

                if original_gemini_model is None:
                    os.environ.pop("GEMINI_MODEL", None)
                else:
                    os.environ["GEMINI_MODEL"] = original_gemini_model


if __name__ == "__main__":
    unittest.main()
