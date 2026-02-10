from typing import Any, Dict, List, Optional, Text
import re

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionPersonNameOpinion(Action):
    def name(self) -> Text:
        return "action_person_name_opinion"

    def _extract_name(self, tracker: Tracker) -> Optional[str]:
        entities = tracker.latest_message.get("entities", []) or []
        for entity in entities:
            if entity.get("entity") in {"person_name", "name"}:
                value = entity.get("value")
                if isinstance(value, str) and value.strip():
                    return value.strip()

        text = tracker.latest_message.get("text") or ""
        match = re.search(r"(?:von|über|zu)\s+([A-Za-zÄÖÜäöüß-]+)", text)
        if match:
            return match.group(1)

        tokens = re.findall(r"[A-Za-zÄÖÜäöüß-]+", text)
        if tokens:
            return tokens[-1]
        return None

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        name = self._extract_name(tracker)
        normalized = re.sub(r"[^A-Za-zÄÖÜäöüß-]", "", name or "").lower()
        known_names = {"sanja", "axel", "rita", "roland", "sarah"}

        if normalized in known_names:
            label = name or "Der Name"
            text = f"{label}: Super Mensch, aber lass uns doch lieber wieder über das Projekt sprechen :)"
            buttons = [
                {"title": "Zeig mir das Projekt 🤖💬", "payload": "/project_chatbot"},
                {"title": "Erzähl mir was zur Praxisphase", "payload": "/praxisphase_info"},
            ]
        else:
            text = (
                "Der Name sagt mir jetzt gerade nichts, aber vielleicht kann sich das ja noch ändern. "
                "Schreib mir doch einfach eine Mail."
            )
            buttons = [
                {"title": "Kontakt per Mail ✉️", "payload": "/contact_email"},
                {"title": "Zeig mir das Projekt 🤖💬", "payload": "/project_chatbot"},
            ]

        dispatcher.utter_message(text=text, buttons=buttons)
        return []
