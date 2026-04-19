import unittest

from app.company_context import (
    COMPANY_INTENT_GENERAL_WHY,
    COMPANY_INTENT_MENTION,
    COMPANY_INTENT_WHY,
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

    def test_unrelated_input_falls_through(self):
        self.assertIsNone(resolve_company_context("Warum ein Chatbot?"))
        self.assertIsNone(resolve_company_context("Was studierst du?"))


if __name__ == "__main__":
    unittest.main()
