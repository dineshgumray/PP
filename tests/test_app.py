import sqlite3
import os
import tempfile
import unittest
from unittest.mock import patch

from app import create_app


class PromptPilotAppTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.log_fd, self.log_path = tempfile.mkstemp()
        os.close(self.log_fd)
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE": self.db_path,
                "LOG_FILE": self.log_path,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        os.unlink(self.log_path)

    def read_log(self):
        with open(self.log_path, "r", encoding="utf-8") as log_file:
            return log_file.read()

    def signup(self):
        return self.client.post(
            "/signup",
            data={
                "name": "Aarav Sharma",
                "email": "aarav@example.com",
                "password": "super-secret",
                "occupation": "Product Manager",
                "location": "Bengaluru, India",
                "date_of_birth": "1996-08-11",
                "goals": "Prepare product management interview plans, networking emails, market updates, business updates, and concise policy memos.",
            },
            follow_redirects=True,
        )

    def test_signup_page_hides_profile_metadata_fields(self):
        response = self.client.get("/signup")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Goals (optional)", response.data)
        self.assertNotIn(b"Industry", response.data)
        self.assertNotIn(b"Primary use case", response.data)
        self.assertNotIn(b"Preferred tone", response.data)
        self.assertNotIn(b"Create your AI profile once.", response.data)

    def test_login_page_has_no_heading_section(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Login to PromptPilot", response.data)
        self.assertNotIn(b"Return to your workspace", response.data)

    def test_landing_page_uses_neutral_copy(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Stop repeating your background every time you ask for help.", response.data)
        self.assertIn(b"hand that prompt off for generation or return the final answer in the app.", response.data)
        self.assertIn(b"Use the optimized prompt anywhere, or generate the final answer in the app.", response.data)
        self.assertNotIn(b"LLM", response.data)
        self.assertNotIn(b"locally", response.data)
        self.assertNotIn(b"Groq", response.data)
        self.assertNotIn(b"Ollama", response.data)

    def test_signup_redirects_to_dashboard(self):
        response = self.signup()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My profile", response.data)
        self.assertIn(b"History", response.data)
        self.assertIn(b"More", response.data)
        self.assertIn(b"Copy prompt", response.data)
        self.assertIn(b"Copy output", response.data)
        self.assertIn(b"Submit", response.data)
        self.assertIn(b"Delete profile", response.data)
        self.assertIn(b"brand/logo.png", response.data)
        self.assertIn(b"Goals (optional)", response.data)
        self.assertIn(b'id="dob-toggle"', response.data)
        self.assertIn(b'type="checkbox"', response.data)
        self.assertIn(b'aria-label="Toggle date of birth visibility"', response.data)
        self.assertNotIn(b"Show date of birth", response.data)
        self.assertNotIn(b"Hide date of birth", response.data)
        self.assertIn(b'id="dob-field"', response.data)
        self.assertNotIn(b"data-dob-toggle", response.data)
        self.assertNotIn(b"data-dob-field", response.data)
        self.assertIn(b'id="provider-field">', response.data)
        self.assertIn(b"generate-only is-hidden", response.data)
        self.assertIn(b"prompt-mode", response.data)
        self.assertNotIn(b"Generate the right prompt once", response.data)
        self.assertNotIn(b"Primary use case", response.data)
        self.assertNotIn(b"Industry", response.data)
        self.assertNotIn(b"Preferred tone", response.data)
        self.assertNotIn(b"Thinking styles", response.data)
        self.assertNotIn(b'id="result-title"', response.data)
        self.assertNotIn(b'id="handoff-note"', response.data)
        self.assertNotIn(b"Optimized prompt will appear here", response.data)
        self.assertNotIn(b"PromptPilot will merge your saved profile", response.data)
        self.assertNotIn(b"Idle", response.data)

    def test_signup_allows_missing_goals(self):
        response = self.client.post(
            "/signup",
            data={
                "name": "Aarav Sharma",
                "email": "aarav.no-goals@example.com",
                "password": "super-secret",
                "occupation": "Product Manager",
                "location": "Bengaluru, India",
                "date_of_birth": "1996-08-11",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT goals FROM users WHERE email = ?",
                ("aarav.no-goals@example.com",),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(user["goals"], "")

    def test_signup_uses_remaining_profile_columns(self):
        response = self.client.post(
            "/signup",
            data={
                "name": "Aarav Sharma",
                "email": "aarav.defaults@example.com",
                "password": "super-secret",
                "occupation": "Product Manager",
                "location": "Bengaluru, India",
                "date_of_birth": "1996-08-11",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
            self.assertNotIn("industry", columns)
            self.assertNotIn("primary_use_case", columns)
            self.assertNotIn("preferred_tone", columns)
            user = conn.execute(
                "SELECT name, occupation, location, date_of_birth, goals FROM users WHERE email = ?",
                ("aarav.defaults@example.com",),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(user["name"], "Aarav Sharma")
        self.assertEqual(user["occupation"], "Product Manager")
        self.assertEqual(user["location"], "Bengaluru, India")
        self.assertEqual(user["date_of_birth"], "1996-08-11")
        self.assertEqual(user["goals"], "")

    def test_legacy_users_table_is_migrated(self):
        legacy_db_fd, legacy_db_path = tempfile.mkstemp()
        legacy_log_fd, legacy_log_path = tempfile.mkstemp()
        os.close(legacy_db_fd)
        os.close(legacy_log_fd)

        try:
            conn = sqlite3.connect(legacy_db_path)
            try:
                conn.executescript(
                    """
                    PRAGMA foreign_keys = OFF;
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        name TEXT NOT NULL,
                        occupation TEXT NOT NULL,
                        location TEXT NOT NULL,
                        date_of_birth TEXT NOT NULL,
                        industry TEXT,
                        primary_use_case TEXT NOT NULL,
                        preferred_tone TEXT NOT NULL,
                        goals TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE generations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        provider TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        use_case TEXT NOT NULL,
                        task TEXT NOT NULL,
                        optimized_prompt TEXT NOT NULL,
                        response_text TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users_legacy(id) ON DELETE CASCADE
                    );
                    INSERT INTO users (
                        email,
                        password_hash,
                        name,
                        occupation,
                        location,
                        date_of_birth,
                        industry,
                        primary_use_case,
                        preferred_tone,
                        goals
                    )
                    VALUES (
                        'legacy@example.com',
                        'hash',
                        'Legacy User',
                        'Builder',
                        'Delhi, India',
                        '1990-01-01',
                        'SaaS',
                        'career',
                        'Direct and polished',
                        'Build stuff'
                    );
                    INSERT INTO generations (
                        user_id,
                        provider,
                        mode,
                        use_case,
                        task,
                        optimized_prompt,
                        response_text,
                        status
                    )
                    VALUES (
                        1,
                        'groq',
                        'prompt',
                        'career',
                        'Legacy task',
                        'Legacy prompt',
                        NULL,
                        'prompt_ready'
                    );
                    """
                )
                conn.commit()
            finally:
                conn.close()

            app = create_app(
                {
                    "TESTING": True,
                    "SECRET_KEY": "test-secret",
                    "DATABASE": legacy_db_path,
                    "LOG_FILE": legacy_log_path,
                }
            )

            client = app.test_client()
            with client.session_transaction() as session:
                session["user_id"] = 1

            response = client.post(
                "/api/generate",
                json={
                    "task": "Write a product update.",
                    "use_case": "business",
                    "target_provider": "chatgpt",
                    "mode": "prompt",
                    "audience": "Leadership team",
                },
            )

            self.assertEqual(response.status_code, 200)

            conn = sqlite3.connect(legacy_db_path)
            try:
                conn.row_factory = sqlite3.Row
                columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
                self.assertNotIn("industry", columns)
                self.assertNotIn("primary_use_case", columns)
                self.assertNotIn("preferred_tone", columns)
                fk_parent = conn.execute("PRAGMA foreign_key_list(generations)").fetchone()["table"]
                self.assertEqual(fk_parent, "users")
                user = conn.execute(
                    "SELECT name, occupation, location, date_of_birth, goals FROM users WHERE email = ?",
                    ("legacy@example.com",),
                ).fetchone()
                generation_count = conn.execute("SELECT COUNT(*) FROM generations").fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(user["name"], "Legacy User")
            self.assertEqual(user["occupation"], "Builder")
            self.assertEqual(user["location"], "Delhi, India")
            self.assertEqual(user["date_of_birth"], "1990-01-01")
            self.assertEqual(user["goals"], "Build stuff")
            self.assertEqual(generation_count, 2)
        finally:
            os.unlink(legacy_db_path)
            os.unlink(legacy_log_path)

    def test_generate_prompt_returns_json(self):
        self.signup()
        response = self.client.post(
            "/api/generate",
            json={
                "task": "Create a 5-point interview prep plan for PM roles.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "Self",
                "thinking_styles": "Analytical, strategic",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "prompt_ready")
        self.assertIn("Goal focus:", payload["optimized_prompt"])
        self.assertIn("Create a 5-point interview prep plan", payload["optimized_prompt"])
        self.assertNotIn("wizard_trace", payload)
        self.assertNotIn("wizard_selected_variant", payload)
        self.assertNotIn("wizard_selected_score", payload)
        log_text = self.read_log()
        self.assertIn("Prompt flow run", log_text)
        self.assertIn("Task Input:", log_text)
        self.assertIn("Prompt Initialization:", log_text)
        self.assertIn("Critique & Evaluation:", log_text)
        self.assertIn("Task-Aware Scoring:", log_text)
        self.assertIn("Prompt Refinement:", log_text)
        self.assertIn("Optimized Prompt:", log_text)

    @patch("services.llm_client.OpenAIClient.generate", return_value="This should not be used.")
    def test_generate_redirects_tasks_outside_goals(self, mock_generate):
        self.signup()
        self.client.post(
            "/profile",
            data={
                "name": "Aarav Sharma",
                "occupation": "Product Manager",
                "location": "Bengaluru, India",
                "date_of_birth": "1996-08-11",
                "goals": "Give details of zodiac sign.",
            },
            follow_redirects=True,
        )

        response = self.client.post(
            "/api/generate",
            json={
                "task": "Need details on chair.",
                "use_case": "general",
                "target_provider": "chatgpt",
                "mode": "generate",
                "audience": "General audience",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "goal_redirect")
        self.assertIn("Goal focus:", payload["optimized_prompt"])
        self.assertIn("Give details of zodiac sign.", payload["optimized_prompt"])
        self.assertIn("Need details on chair.", payload["optimized_prompt"])
        self.assertIn("What I can do is help with your goal: Give details of zodiac sign.", payload["response_text"])
        self.assertIn("Briefly, this goal is about zodiac signs", payload["response_text"])
        self.assertIn("Need details on chair.", payload["response_text"])
        self.assertEqual(payload["response_text"], payload["handoff_note"])
        mock_generate.assert_not_called()

    @patch("services.llm_client.OpenAIClient.generate", return_value="Cancer is a water sign.")
    def test_generate_accepts_zodiac_sign_tasks_when_goal_mentions_zodiac(self, mock_generate):
        self.signup()
        self.client.post(
            "/profile",
            data={
                "name": "Aarav Sharma",
                "occupation": "Product Manager",
                "location": "Bengaluru, India",
                "date_of_birth": "1996-08-11",
                "goals": "Give details on zodiac sign only.",
            },
            follow_redirects=True,
        )
        self.app.config["OPENAI_API_KEY"] = "test-openai-key"

        response = self.client.post(
            "/api/generate",
            json={
                "task": "cancer",
                "use_case": "general",
                "target_provider": "chatgpt",
                "mode": "generate",
                "audience": "General audience",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(payload["response_text"], "Cancer is a water sign.")
        self.assertIn("Generate mode can call OpenAI directly when OPENAI_API_KEY is configured.", payload["handoff_note"])
        mock_generate.assert_called_once()

    def test_clear_history_empties_saved_generations(self):
        self.signup()
        self.client.post(
            "/api/generate",
            json={
                "task": "Create a 5-point interview prep plan for PM roles.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "Self",
            },
        )

        before_clear = self.client.get("/dashboard")
        self.assertIn(b"Clear history", before_clear.data)
        self.assertIn(b"Copy task", before_clear.data)

        response = self.client.post("/history/clear", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No history found.", response.data)

    def test_history_fragment_refreshes_after_generate(self):
        self.signup()

        before = self.client.get("/api/history")
        self.assertEqual(before.status_code, 200)
        before_payload = before.get_json()
        self.assertEqual(before_payload["count"], 0)
        self.assertIn("No history found.", before_payload["html"])

        self.client.post(
            "/api/generate",
            json={
                "task": "Write a concise follow-up email.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "Recruiter",
            },
        )

        after = self.client.get("/api/history")
        self.assertEqual(after.status_code, 200)
        after_payload = after.get_json()
        self.assertEqual(after_payload["count"], 1)
        self.assertIn("Write a concise follow-up email.", after_payload["html"])
        self.assertIn("Prompt | Career", after_payload["html"])
        self.assertIn("Copy task", after_payload["html"])
        self.assertIn("Clear history", after_payload["html"])

    def test_update_profile_updates_visible_fields(self):
        self.signup()
        response = self.client.post(
            "/profile",
            data={
                "name": "Aarav Sharma",
                "occupation": "Senior Product Manager",
                "location": "Berlin, Germany",
                "date_of_birth": "1996-08-11",
                "goals": "Move into global product leadership roles.",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT name, occupation, location, date_of_birth, goals FROM users WHERE email = ?",
                ("aarav@example.com",),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(user["name"], "Aarav Sharma")
        self.assertEqual(user["occupation"], "Senior Product Manager")
        self.assertEqual(user["location"], "Berlin, Germany")
        self.assertEqual(user["date_of_birth"], "1996-08-11")
        self.assertEqual(user["goals"], "Move into global product leadership roles.")

    def test_delete_profile_removes_user_and_history(self):
        self.signup()
        self.client.post(
            "/api/generate",
            json={
                "task": "Create a 5-point interview prep plan for PM roles.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "Self",
            },
        )

        response = self.client.post("/profile/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Start with your profile", response.data)

        conn = sqlite3.connect(self.db_path)
        try:
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            generation_count = conn.execute("SELECT COUNT(*) FROM generations").fetchone()[0]
        finally:
            conn.close()

        self.assertEqual(user_count, 0)
        self.assertEqual(generation_count, 0)

    def test_dev_auth_mode_skips_password_verification(self):
        self.signup()
        self.app.config["DEV_AUTH_MODE"] = True
        self.client.post("/logout", follow_redirects=True)

        response = self.client.post(
            "/login",
            data={
                "email": "aarav@example.com",
                "password": "wrong-password",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My profile", response.data)

    @patch("services.llm_client.OpenAIClient.generate", return_value="A generated response from OpenAI.")
    def test_generate_with_openai_returns_generated_status(self, _mock_generate):
        self.signup()
        self.app.config["OPENAI_API_KEY"] = "test-openai-key"

        response = self.client.post(
            "/api/generate",
            json={
                "task": "Draft a short SaaS networking email.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "generate",
                "audience": "Recruiter",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(payload["response_text"], "A generated response from OpenAI.")
        self.assertEqual(payload["model"], self.app.config["OPENAI_MODEL"])

    @patch("services.llm_client.GroqClient.generate", return_value="A generated response from Groq.")
    def test_generate_with_groq_returns_generated_status(self, _mock_generate):
        self.signup()
        self.app.config["GROQ_API_KEY"] = "test-groq-key"

        response = self.client.post(
            "/api/generate",
            json={
                "task": "Draft a short SaaS networking email.",
                "use_case": "career",
                "target_provider": "groq",
                "mode": "generate",
                "audience": "Recruiter",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(payload["response_text"], "A generated response from Groq.")
        self.assertEqual(payload["model"], self.app.config["GROQ_MODEL"])

    def test_generate_with_missing_openai_key_returns_provider_error(self):
        self.signup()
        self.app.config["OPENAI_API_KEY"] = ""

        response = self.client.post(
            "/api/generate",
            json={
                "task": "Draft a short SaaS networking email.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "generate",
                "audience": "Recruiter",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "provider_error")
        self.assertIn("OPENAI_API_KEY", payload["handoff_note"])

    @patch("services.llm_client.GeminiClient.generate", return_value="A generated response from Gemini.")
    def test_generate_with_gemini_returns_generated_status(self, _mock_generate):
        self.signup()
        self.app.config["GEMINI_API_KEY"] = "test-gemini-key"

        response = self.client.post(
            "/api/generate",
            json={
                "task": "Summarize a market update.",
                "use_case": "business",
                "target_provider": "gemini",
                "mode": "generate",
                "audience": "Founder",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(payload["response_text"], "A generated response from Gemini.")
        self.assertEqual(payload["model"], self.app.config["GEMINI_MODEL"])

    @patch("services.llm_client.AnthropicClient.generate", return_value="A generated response from Claude.")
    def test_generate_with_claude_returns_generated_status(self, _mock_generate):
        self.signup()
        self.app.config["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        response = self.client.post(
            "/api/generate",
            json={
                "task": "Draft a concise policy memo.",
                "use_case": "research",
                "target_provider": "claude",
                "mode": "generate",
                "audience": "Analyst",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(payload["response_text"], "A generated response from Claude.")
        self.assertEqual(payload["model"], self.app.config["ANTHROPIC_MODEL"])


if __name__ == "__main__":
    unittest.main()
