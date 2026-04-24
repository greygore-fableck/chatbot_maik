import unittest

from app.company_context import (
    COMPANY_INTENT_GENERAL_WHY,
    COMPANY_INTENT_MENTION,
    COMPANY_INTENT_WHY,
    current_company_from_conversation,
    current_company_from_message,
    resolve_company_context,
)


class CompanyContextTests(unittest.TestCase):
    def assert_company_context(self, message, company, intent, expected_text):
        result = resolve_company_context(message)
        self.assertIsNotNone(result)
        self.assertEqual(result.company_key, company)
        self.assertEqual(result.intent, intent)
        self.assertIn(expected_text, result.text)

    def test_company_name_only_inputs(self):
        self.assert_company_context("Deichmann", "deichmann", COMPANY_INTENT_MENTION, "Nutzerführung")
        self.assert_company_context("adesso?", "adesso", COMPANY_INTENT_MENTION, "praktischem Bezug")
        self.assert_company_context("Materna", "materna", COMPANY_INTENT_MENTION, "Konzeption")

    def test_company_why_inputs(self):
        self.assert_company_context("Warum Deichmann?", "deichmann", COMPANY_INTENT_WHY, "Chatbot-Konzeption")
        self.assert_company_context("Wieso adesso?", "adesso", COMPANY_INTENT_WHY, "nutzerorientierte")
        self.assert_company_context(
            "Was passt an Ihrem Profil zu Deichmann?",
            "deichmann",
            COMPANY_INTENT_WHY,
            "Medieninformatik",
        )
        self.assert_company_context(
            "Was reizt Sie an adesso?",
            "adesso",
            COMPANY_INTENT_WHY,
            "digitale Projekte",
        )
        self.assert_company_context(
            "Warum Materna?",
            "materna",
            COMPANY_INTENT_WHY,
            "dialogischen Systemen",
        )

    def test_general_why_company_inputs(self):
        self.assert_company_context(
            "Warum möchten Sie zu uns?",
            None,
            COMPANY_INTENT_GENERAL_WHY,
            "Praxisphase",
        )
        self.assert_company_context(
            "Weshalb bewerben Sie sich bei uns?",
            None,
            COMPANY_INTENT_GENERAL_WHY,
            "Bachelorarbeit",
        )
        self.assert_company_context(
            "Wieso passt Ihr Thema zu uns?",
            None,
            COMPANY_INTENT_GENERAL_WHY,
            "realen digitalen Aufgaben",
        )

    def test_current_message_company_overrides_history(self):
        result = resolve_company_context("Warum Materna?", history=["Warum Deichmann?"])
        self.assertIsNotNone(result)
        self.assertEqual(result.company_key, "materna")
        self.assertEqual(result.intent, COMPANY_INTENT_WHY)

    def test_general_why_uses_last_explicit_company_from_history(self):
        result = resolve_company_context("Und warum zu uns?", history=["Warum Deichmann?"])
        self.assertIsNotNone(result)
        self.assertEqual(result.company_key, "deichmann")
        self.assertEqual(result.intent, COMPANY_INTENT_WHY)
        self.assertIn("Nutzerführung", result.text)

    def test_general_why_stays_general_without_company_context(self):
        result = resolve_company_context(
            "Warum gerade wir?",
            history=["Was studierst du?", "Erzähl mir mehr zur Bachelorarbeit."],
        )
        self.assertIsNotNone(result)
        self.assertIsNone(result.company_key)
        self.assertEqual(result.intent, COMPANY_INTENT_GENERAL_WHY)
        self.assertNotIn("Deichmann", result.text)
        self.assertNotIn("adesso", result.text)

    def test_conversation_context_uses_last_explicit_company(self):
        history = ["Warum Deichmann?", "Und was reizt Sie an adesso?"]
        self.assertEqual(current_company_from_conversation(history), "adesso")

    def test_company_detection_helpers(self):
        self.assertEqual(current_company_from_message("deichmann?"), "deichmann")
        self.assertEqual(current_company_from_message("Wieso adesso?"), "adesso")
        self.assertEqual(current_company_from_message("Warum Materna?"), "materna")
        self.assertIsNone(current_company_from_message("Warum gerade wir?"))

    def test_unrelated_input_falls_through(self):
        self.assertIsNone(resolve_company_context("Warum ein Chatbot?"))
        self.assertIsNone(resolve_company_context("Was studierst du?"))


if __name__ == "__main__":
    unittest.main()
