import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app


OLLAMA_TEST_CASES = [
    {
        "name": "product-leadership-update",
        "profile": {
            "name": "Aarav Sharma",
            "email": "aarav.ollama1@example.com",
            "password": "super-secret",
            "occupation": "Product Manager",
            "location": "Bengaluru, India",
            "date_of_birth": "1996-08-11",
            "goals": "Move into product leadership roles and write sharper executive updates.",
        },
        "payload": {
            "task": "Draft a quarterly product update for the leadership team.",
            "use_case": "business",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Leadership team",
            "desired_format": "Executive summary",
            "output_length": "Medium",
            "thinking_styles": "Strategic, concise",
        },
        "snippets": [
            "Occupation: Product Manager",
            "Current task: Draft a quarterly product update for the leadership team.",
        ],
    },
    {
        "name": "linkedin-content-post",
        "profile": {
            "name": "Maya Johnson",
            "email": "maya.ollama2@example.com",
            "password": "super-secret",
            "occupation": "Content Strategist",
            "location": "Lagos, Nigeria",
            "date_of_birth": "1992-03-24",
            "goals": "Grow my LinkedIn audience with clear, consistent posts.",
        },
        "payload": {
            "task": "Write a LinkedIn post announcing a career pivot.",
            "use_case": "content",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "LinkedIn followers",
            "desired_format": "Social post",
            "output_length": "Short",
            "thinking_styles": "Creative, engaging",
        },
        "snippets": [
            "Occupation: Content Strategist",
            "Current task: Write a LinkedIn post announcing a career pivot.",
        ],
    },
    {
        "name": "python-api-debugging",
        "profile": {
            "name": "Luis Martinez",
            "email": "luis.ollama3@example.com",
            "password": "super-secret",
            "occupation": "Backend Engineer",
            "location": "Austin, USA",
            "date_of_birth": "1990-12-02",
            "goals": "Debug Python APIs faster and ship cleaner services.",
        },
        "payload": {
            "task": "Explain how to implement cursor pagination in a Python API.",
            "use_case": "coding",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Junior developers",
            "desired_format": "Technical explanation",
            "output_length": "Medium",
            "thinking_styles": "Precise, implementation-focused",
        },
        "snippets": [
            "Occupation: Backend Engineer",
            "Current task: Explain how to implement cursor pagination in a Python API.",
        ],
    },
    {
        "name": "study-guide",
        "profile": {
            "name": "Priya Nair",
            "email": "priya.ollama4@example.com",
            "password": "super-secret",
            "occupation": "Graduate Student",
            "location": "Toronto, Canada",
            "date_of_birth": "1998-05-17",
            "goals": "Pass the machine learning exam and make better study notes.",
        },
        "payload": {
            "task": "Create a study sheet on gradient descent and overfitting.",
            "use_case": "study",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Self-study",
            "desired_format": "Study guide",
            "output_length": "Medium",
            "thinking_styles": "Clear, patient",
        },
        "snippets": [
            "Occupation: Graduate Student",
            "Current task: Create a study sheet on gradient descent and overfitting.",
        ],
    },
    {
        "name": "travel-itinerary",
        "profile": {
            "name": "Sofia Rossi",
            "email": "sofia.ollama5@example.com",
            "password": "super-secret",
            "occupation": "Travel Planner",
            "location": "Madrid, Spain",
            "date_of_birth": "1989-09-08",
            "goals": "Plan travel itineraries and practical trip logistics.",
        },
        "payload": {
            "task": "Build a 3-day Tokyo itinerary with transit tips.",
            "use_case": "travel",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Solo traveler",
            "desired_format": "Itinerary",
            "output_length": "Medium",
            "thinking_styles": "Practical, cost-aware",
        },
        "snippets": [
            "Location: Madrid, Spain",
            "Current task: Build a 3-day Tokyo itinerary with transit tips.",
        ],
    },
    {
        "name": "investor-update",
        "profile": {
            "name": "Noah Kim",
            "email": "noah.ollama6@example.com",
            "password": "super-secret",
            "occupation": "Startup Founder",
            "location": "Singapore",
            "date_of_birth": "1991-01-30",
            "goals": "Write concise investor updates and explain revenue trends better.",
        },
        "payload": {
            "task": "Summarize monthly revenue, churn, and next steps for investors.",
            "use_case": "business",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Investors",
            "desired_format": "Investor update",
            "output_length": "Short",
            "thinking_styles": "Decision-oriented, concise",
        },
        "snippets": [
            "Occupation: Startup Founder",
            "Current task: Summarize monthly revenue, churn, and next steps for investors.",
        ],
    },
    {
        "name": "research-brief",
        "profile": {
            "name": "Elena Petrova",
            "email": "elena.ollama7@example.com",
            "password": "super-secret",
            "occupation": "Research Analyst",
            "location": "Boston, USA",
            "date_of_birth": "1994-07-19",
            "goals": "Synthesize evidence from studies and present careful findings.",
        },
        "payload": {
            "task": "Summarize the latest findings on remote work productivity.",
            "use_case": "research",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Policy team",
            "desired_format": "Research brief",
            "output_length": "Medium",
            "thinking_styles": "Evidence-aware, structured",
        },
        "snippets": [
            "Occupation: Research Analyst",
            "Current task: Summarize the latest findings on remote work productivity.",
        ],
    },
    {
        "name": "brand-bio",
        "profile": {
            "name": "Jordan Lee",
            "email": "jordan.ollama8@example.com",
            "password": "super-secret",
            "occupation": "Brand Consultant",
            "location": "Cape Town, South Africa",
            "date_of_birth": "1993-11-04",
            "goals": "Strengthen my LinkedIn brand and portfolio voice.",
        },
        "payload": {
            "task": "Rewrite my bio for a portfolio site.",
            "use_case": "personal-brand",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Hiring managers",
            "desired_format": "Bio",
            "output_length": "Short",
            "thinking_styles": "Authentic, polished",
        },
        "snippets": [
            "Occupation: Brand Consultant",
            "Current task: Rewrite my bio for a portfolio site.",
        ],
    },
    {
        "name": "general-checklist",
        "profile": {
            "name": "Hannah Brooks",
            "email": "hannah.ollama9@example.com",
            "password": "super-secret",
            "occupation": "Operations Manager",
            "location": "Chicago, USA",
            "date_of_birth": "1988-02-15",
            "goals": "Need direct practical answers for onboarding checklists and daily planning.",
        },
        "payload": {
            "task": "Create a simple onboarding checklist for a new hire.",
            "use_case": "general",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "New teammate",
            "desired_format": "Checklist",
            "output_length": "Short",
            "thinking_styles": "Structured, direct",
        },
        "snippets": [
            "Occupation: Operations Manager",
            "Current task: Create a simple onboarding checklist for a new hire.",
        ],
    },
    {
        "name": "career-outreach-email",
        "profile": {
            "name": "Imani Clarke",
            "email": "imani.ollama10@example.com",
            "password": "super-secret",
            "occupation": "Marketing Lead",
            "location": "London, UK",
            "date_of_birth": "1991-06-09",
            "goals": "Move into head of marketing roles and write stronger outreach emails.",
        },
        "payload": {
            "task": "Draft a cold outreach email for a product design partnership.",
            "use_case": "career",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Design director",
            "desired_format": "Email draft",
            "output_length": "Short",
            "thinking_styles": "Confident, persuasive",
        },
        "snippets": [
            "Occupation: Marketing Lead",
            "Current task: Draft a cold outreach email for a product design partnership.",
        ],
    },
]


class OllamaProfileScenarioTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.log_fd, self.log_path = tempfile.mkstemp()
        os.close(self.log_fd)
        self.report_path = Path(__file__).resolve().parents[1] / "instance" / "ollama_profile_runs.jsonl"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text("", encoding="utf-8")
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

    def signup(self, profile):
        return self.client.post(
            "/signup",
            data=profile,
            follow_redirects=True,
        )

    def log_case_report(self, case, response_payload, posted_payload):
        report = {
            "case": case["name"],
            "profile": {
                "name": case["profile"]["name"],
                "occupation": case["profile"]["occupation"],
                "location": case["profile"]["location"],
            },
            "task": case["payload"]["task"],
            "provider": response_payload["provider"],
            "mode": response_payload["mode"],
            "status": response_payload["status"],
            "model": response_payload["model"],
            "response_text": response_payload["response_text"],
            "handoff_note": response_payload["handoff_note"],
            "prompt_length": len(posted_payload["prompt"]),
            "prompt_excerpt": posted_payload["prompt"][:500],
        }

        with self.report_path.open("a", encoding="utf-8") as report_file:
            report_file.write(json.dumps(report, ensure_ascii=False) + "\n")

    @patch("services.llm_client.OllamaClient.post_json", return_value={"response": "Mock Ollama answer."})
    def test_ten_ollama_profile_scenarios_generate_successfully(self, mock_post_json):
        for case in OLLAMA_TEST_CASES:
            with self.subTest(case=case["name"]):
                self.signup(case["profile"])

                response = self.client.post("/api/generate", json=case["payload"])
                payload = response.get_json()

                self.assertEqual(response.status_code, 200)
                self.assertEqual(payload["status"], "generated")
                self.assertEqual(payload["provider"], "ollama")
                self.assertEqual(payload["mode"], "generate")
                self.assertEqual(payload["model"], self.app.config["OLLAMA_MODEL"])
                self.assertEqual(payload["response_text"], "Mock Ollama answer.")
                self.assertIn("local Ollama server", payload["handoff_note"])

                posted_payload = mock_post_json.call_args.args[1]
                self.log_case_report(case, payload, posted_payload)
                self.assertEqual(posted_payload["model"], self.app.config["OLLAMA_MODEL"])
                self.assertFalse(posted_payload["stream"])
                self.assertIn("Goal focus:", posted_payload["prompt"])
                self.assertIn(case["snippets"][0], posted_payload["prompt"])
                self.assertIn(case["snippets"][1], posted_payload["prompt"])


if __name__ == "__main__":
    unittest.main()
