import unittest

from app.company_context import (
    COMPANY_INTENT_FIT,
    COMPANY_INTENT_GENERAL_WHY,
    COMPANY_INTENT_MENTION,
    COMPANY_INTENT_WHY,
    company_key_from_value,
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
        self.assert_company_context("adesso?", "adesso", COMPANY_INTENT_MENTION, "praktischem Bezug")
        self.assert_company_context("denkwerk", "denkwerk", COMPANY_INTENT_MENTION, "Nutzerführung")
        self.assert_company_context("msg", "msg", COMPANY_INTENT_MENTION, "praktischem Bezug")
        self.assert_company_context("taxy.io", "taxy.io", COMPANY_INTENT_MENTION, "digitale Produkte")
        self.assert_company_context("ARAG IT", "arag it", COMPANY_INTENT_MENTION, "praktischem Bezug")
        self.assert_company_context("ARAG", "arag it", COMPANY_INTENT_MENTION, "praktischem Bezug")

    def test_company_why_inputs(self):
        self.assert_company_context("Wieso adesso?", "adesso", COMPANY_INTENT_WHY, "nutzerorientiert")
        self.assert_company_context(
            "Was reizt Sie an adesso?",
            "adesso",
            COMPANY_INTENT_WHY,
            "digitale Projekte",
        )
        self.assert_company_context(
            "Warum denkwerk?",
            "denkwerk",
            COMPANY_INTENT_WHY,
            "digitales Produktdenken",
        )
        self.assert_company_context(
            "Weshalb denkwerk?",
            "denkwerk",
            COMPANY_INTENT_WHY,
            "digitales Produktdenken",
        )
        self.assert_company_context(
            "Was reizt Sie an denkwerk?",
            "denkwerk",
            COMPANY_INTENT_WHY,
            "kreatives Arbeiten",
        )
        self.assert_company_context(
            "Warum msg?",
            "msg",
            COMPANY_INTENT_WHY,
            "nutzerorientiertes Denken",
        )
        self.assert_company_context(
            "Was reizt Sie an msg?",
            "msg",
            COMPANY_INTENT_WHY,
            "digitale Anwendungen",
        )
        self.assert_company_context(
            "Warum taxy.io?",
            "taxy.io",
            COMPANY_INTENT_WHY,
            "nutzerorientiertes Denken",
        )
        self.assert_company_context(
            "Was reizt Sie an ARAG IT?",
            "arag it",
            COMPANY_INTENT_WHY,
            "digitale Anwendungen",
        )
        self.assert_company_context(
            "Warum ARAG?",
            "arag it",
            COMPANY_INTENT_WHY,
            "nutzerorientiertes Denken",
        )

    def test_company_fit_inputs(self):
        self.assert_company_context(
            "Was passt an Ihrem Profil zu denkwerk?",
            "denkwerk",
            COMPANY_INTENT_FIT,
            "Medieninformatik",
        )
        self.assert_company_context(
            "Was passt an Ihrem Profil zu msg?",
            "msg",
            COMPANY_INTENT_FIT,
            "Chatbot-Konzeption",
        )
        self.assert_company_context(
            "Was passt an Ihrem Profil zu taxy.io?",
            "taxy.io",
            COMPANY_INTENT_FIT,
            "Webentwicklung",
        )
        self.assert_company_context(
            "Was passt an Ihrem Profil zu ARAG IT?",
            "arag it",
            COMPANY_INTENT_FIT,
            "Gestaltung",
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
        result = resolve_company_context("Warum msg?", history=["Warum adesso?"])
        self.assertIsNotNone(result)
        self.assertEqual(result.company_key, "msg")
        self.assertEqual(result.intent, COMPANY_INTENT_WHY)

    def test_general_why_uses_last_explicit_company_from_history(self):
        result = resolve_company_context("Und warum zu uns?", history=["Warum msg?"])
        self.assertIsNotNone(result)
        self.assertEqual(result.company_key, "msg")
        self.assertEqual(result.intent, COMPANY_INTENT_WHY)
        self.assertIn("nutzerorientiertes Denken", result.text)

    def test_general_why_uses_explicit_company_hint(self):
        result = resolve_company_context("Und warum zu uns?", company_key_hint="msg")
        self.assertIsNotNone(result)
        self.assertEqual(result.company_key, "msg")
        self.assertEqual(result.intent, COMPANY_INTENT_WHY)
        self.assertIn("technische Umsetzung", result.text)

    def test_general_why_stays_general_without_company_context(self):
        result = resolve_company_context(
            "Warum gerade wir?",
            history=["Was studierst du?", "Erzähl mir mehr zur Bachelorarbeit."],
        )
        self.assertIsNotNone(result)
        self.assertIsNone(result.company_key)
        self.assertEqual(result.intent, COMPANY_INTENT_GENERAL_WHY)
        self.assertNotIn("adesso", result.text)
        self.assertNotIn("denkwerk", result.text)
        self.assertNotIn("msg", result.text)

    def test_conversation_context_uses_last_explicit_company(self):
        history = ["Warum msg?", "Und was reizt Sie an adesso?"]
        self.assertEqual(current_company_from_conversation(history), "adesso")

    def test_company_detection_helpers(self):
        self.assertEqual(current_company_from_message("Wieso adesso?"), "adesso")
        self.assertEqual(current_company_from_message("Warum denkwerk?"), "denkwerk")
        self.assertEqual(current_company_from_message("Warum msg?"), "msg")
        self.assertEqual(current_company_from_message("Warum taxy io?"), "taxy.io")
        self.assertEqual(current_company_from_message("Warum ARAG-IT?"), "arag it")
        self.assertEqual(current_company_from_message("Warum ARAG?"), "arag it")
        self.assertEqual(company_key_from_value("MSG"), "msg")
        self.assertEqual(company_key_from_value("taxy io"), "taxy.io")
        self.assertEqual(company_key_from_value("ARAG-IT"), "arag it")
        self.assertEqual(company_key_from_value("ARAG"), "arag it")
        self.assertIsNone(current_company_from_message("Warum gerade wir?"))

    def test_removed_companies_are_no_longer_detected(self):
        self.assertIsNone(current_company_from_message("deichmann?"))
        self.assertIsNone(current_company_from_message("Warum Materna?"))
        result = resolve_company_context("Warum zu uns?", history=["Warum Deichmann?"])
        self.assertIsNotNone(result)
        self.assertIsNone(result.company_key)
        self.assertEqual(result.intent, COMPANY_INTENT_GENERAL_WHY)
        self.assertNotIn("Deichmann", result.text)
        self.assertNotIn("Materna", result.text)

    def test_unrelated_input_falls_through(self):
        self.assertIsNone(resolve_company_context("Warum ein Chatbot?"))
        self.assertIsNone(resolve_company_context("Was studierst du?"))


if __name__ == "__main__":
    unittest.main()
