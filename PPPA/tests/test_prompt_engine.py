import unittest

from services.prompt_engine import PromptRequest, build_handoff_note, build_prompt, run_prompt_wizard


class PromptEngineTests(unittest.TestCase):
    def setUp(self):
        self.user = {
            "name": "Aarav Sharma",
            "occupation": "Product Manager",
            "location": "Bengaluru, India",
            "date_of_birth": "1996-08-11",
            "industry": "SaaS",
            "primary_use_case": "career",
            "preferred_tone": "Direct and polished",
            "goals": "Move into global product leadership roles.",
        }

    def test_build_prompt_includes_profile_and_task(self):
        prompt_request = PromptRequest.from_payload(
            {
                "task": "Write a cold outreach email for a Berlin startup recruiter.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "Recruiter",
                "desired_format": "Email draft",
                "output_length": "Short",
                "thinking_styles": "Analytical",
            }
        )

        prompt = build_prompt(self.user, prompt_request)

        self.assertIn("Occupation: Product Manager", prompt)
        self.assertIn("Location: Bengaluru, India", prompt)
        self.assertIn("Current task: Write a cold outreach email", prompt)
        self.assertIn("Desired format: Email draft", prompt)
        self.assertIn("Preferred length: Short", prompt)
        self.assertNotIn("Thinking styles:", prompt)
        self.assertNotIn("Constraints:", prompt)
        self.assertNotIn("Additional context:", prompt)

    def test_build_prompt_skips_empty_goals(self):
        user = dict(self.user)
        user["goals"] = ""
        prompt_request = PromptRequest.from_payload(
            {
                "task": "Write a cold outreach email for a Berlin startup recruiter.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "Recruiter",
                "desired_format": "Email draft",
                "output_length": "Short",
                "thinking_styles": "Analytical",
            }
        )

        prompt = build_prompt(user, prompt_request)

        self.assertNotIn("Goals:", prompt)

    def test_prompt_wizard_returns_trace_and_refined_prompt(self):
        prompt_request = PromptRequest.from_payload(
            {
                "task": "Write a cold outreach email for a Berlin startup recruiter.",
                "use_case": "career",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "Recruiter",
                "desired_format": "Email draft",
                "output_length": "Short",
                "thinking_styles": "Analytical, strategic",
            }
        )

        result = run_prompt_wizard(self.user, prompt_request)

        self.assertIn("Prompt wizard", result["trace"])
        self.assertIn("Mutate:", result["trace"])
        self.assertIn("Scoring:", result["trace"])
        self.assertIn("Critique strengths:", result["trace"])
        self.assertIn("Critique gaps:", result["trace"])
        self.assertIn("Synthesize:", result["trace"])
        self.assertIn("Current task: Write a cold outreach email", result["final_prompt"])
        self.assertGreaterEqual(result["selected_score"], 0)

    def test_handoff_note_mentions_local_inference_for_generate_mode(self):
        note = build_handoff_note("chatgpt", "generate")
        self.assertIn("OPENAI_API_KEY", note)

    def test_handoff_note_mentions_groq_api_key(self):
        note = build_handoff_note("groq", "generate")
        self.assertIn("GROQ_API_KEY", note)

    def test_ollama_prompt_mode_note_is_not_presented_as_an_error(self):
        note = build_handoff_note("ollama", "prompt")
        self.assertEqual(note, "Prompt generated successfully. No model call was made.")

    def test_prompt_request_accepts_groq_provider(self):
        prompt_request = PromptRequest.from_payload(
            {
                "task": "Draft a launch email.",
                "use_case": "business",
                "target_provider": "groq",
                "mode": "prompt",
            }
        )

        self.assertEqual(prompt_request.target_provider, "groq")


if __name__ == "__main__":
    unittest.main()
