import unittest

from services.prompt_engine import (
    PromptRequest,
    build_goal_redirect_text,
    build_handoff_note,
    build_prompt,
    evaluate_goal_alignment,
    run_prompt_wizard,
)


class PromptEngineTests(unittest.TestCase):
    def setUp(self):
        self.user = {
            "name": "Aarav Sharma",
            "occupation": "Product Manager",
            "location": "Bengaluru, India",
            "date_of_birth": "1996-08-11",
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
        self.assertIn("Goals: Move into global product leadership roles.", prompt)
        self.assertIn("Goal focus:", prompt)
        self.assertIn("If the request drifts outside those Goals", prompt)
        self.assertIn("Current task: Write a cold outreach email", prompt)
        self.assertIn("Desired format: Email draft", prompt)
        self.assertIn("Preferred length: Short", prompt)
        self.assertNotIn("Industry:", prompt)
        self.assertNotIn("Primary use case:", prompt)
        self.assertNotIn("Preferred tone:", prompt)
        self.assertNotIn("Thinking styles:", prompt)
        self.assertNotIn("Constraints:", prompt)
        self.assertNotIn("Additional context:", prompt)
        self.assertNotIn("Stored profile focus:", prompt)

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
        self.assertNotIn("Goal focus:", prompt)

    def test_build_prompt_keeps_user_goals_for_unrelated_tasks(self):
        user = dict(self.user)
        user["goals"] = "Give details of zodiac sign."
        prompt_request = PromptRequest.from_payload(
            {
                "task": "Need details of banana.",
                "use_case": "general",
                "target_provider": "chatgpt",
                "mode": "prompt",
                "audience": "General audience",
                "desired_format": "Concise answer",
                "output_length": "Medium",
                "thinking_styles": "Analytical",
            }
        )

        prompt = build_prompt(user, prompt_request)

        self.assertIn('Goals: Give details of zodiac sign.', prompt)
        self.assertIn("Goal focus:", prompt)
        self.assertIn("If the request drifts outside those Goals", prompt)
        self.assertIn("Current task: Need details of banana.", prompt)
        self.assertIn("Desired format: Concise answer", prompt)

    def test_goal_alignment_redirect_text_mentions_goal_and_task(self):
        user = dict(self.user)
        user["goals"] = "Give details of zodiac sign."
        prompt_request = PromptRequest.from_payload(
            {
                "task": "Need details on chair.",
                "use_case": "general",
                "target_provider": "chatgpt",
                "mode": "generate",
                "audience": "General audience",
                "desired_format": "Concise answer",
                "output_length": "Medium",
                "thinking_styles": "Analytical",
            }
        )

        goal_alignment = evaluate_goal_alignment(user, prompt_request)
        redirect_text = build_goal_redirect_text(goal_alignment)

        self.assertTrue(goal_alignment["has_goals"])
        self.assertFalse(goal_alignment["is_relevant"])
        self.assertEqual(goal_alignment["goal_text"], "Give details of zodiac sign.")
        self.assertEqual(goal_alignment["task_text"], "Need details on chair.")
        self.assertIn("What I can do is help with your goal: Give details of zodiac sign.", redirect_text)
        self.assertIn("Briefly, this goal is about zodiac signs", redirect_text)
        self.assertIn("Need details on chair.", redirect_text)

    def test_goal_alignment_accepts_plural_and_singular_goal_matches(self):
        user = dict(self.user)
        user["goals"] = "Plan travel itineraries and practical trip logistics."
        prompt_request = PromptRequest.from_payload(
            {
                "task": "Build a 3-day Tokyo itinerary with transit tips.",
                "use_case": "travel",
                "target_provider": "ollama",
                "mode": "generate",
                "audience": "Solo traveler",
                "desired_format": "Itinerary",
                "output_length": "Medium",
                "thinking_styles": "Practical, cost-aware",
            }
        )

        goal_alignment = evaluate_goal_alignment(user, prompt_request)

        self.assertTrue(goal_alignment["has_goals"])
        self.assertTrue(goal_alignment["is_relevant"])
        self.assertIn("itinerary", goal_alignment["task_terms"])
        self.assertIn("itinerary", goal_alignment["goal_terms"])

    def test_goal_alignment_accepts_zodiac_sign_tasks(self):
        user = dict(self.user)
        user["goals"] = "Give details on zodiac sign only."
        prompt_request = PromptRequest.from_payload(
            {
                "task": "cancer",
                "use_case": "general",
                "target_provider": "chatgpt",
                "mode": "generate",
                "audience": "General audience",
                "desired_format": "Concise answer",
                "output_length": "Medium",
                "thinking_styles": "Analytical",
            }
        )

        goal_alignment = evaluate_goal_alignment(user, prompt_request)

        self.assertTrue(goal_alignment["has_goals"])
        self.assertTrue(goal_alignment["is_relevant"])
        self.assertIn("zodiac", goal_alignment["goal_terms"])
        self.assertIn("cancer", goal_alignment["task_terms"])
        self.assertIn("cancer", goal_alignment["matched_terms"])

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

        self.assertIn("task_input", result)
        self.assertIn("prompt_initialization", result)
        self.assertIn("critique_and_evaluation", result)
        self.assertIn("task_aware_scoring", result)
        self.assertIn("prompt_refinement", result)
        self.assertIn("Prompt flow", result["trace"])
        self.assertIn("Task Input:", result["trace"])
        self.assertIn("Prompt Initialization:", result["trace"])
        self.assertIn("Critique & Evaluation:", result["trace"])
        self.assertIn("Task-Aware Scoring:", result["trace"])
        self.assertIn("Prompt Refinement:", result["trace"])
        self.assertIn("Optimized Prompt:", result["trace"])
        self.assertIn("Goal focus:", result["final_prompt"])
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
