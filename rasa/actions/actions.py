import logging
import re
from typing import Any, Dict, List, Optional, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)


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


class ActionSmartGreet(Action):
    def name(self) -> Text:
        return "action_smart_greet"

    def _has_meaningful_history(self, tracker: Tracker) -> bool:
        # Ignore session/bootstrap events and check whether the conversation
        # already had at least one actual user turn before this greeting.
        user_event_count = 0
        for event in tracker.events:
            if event.get("event") != "user":
                continue

            user_event_count += 1
            if user_event_count >= 2:
                return True

        return False

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        response_name = (
            "utter_re_greet"
            if self._has_meaningful_history(tracker)
            else "utter_greet"
        )
        dispatcher.utter_message(response=response_name)
        return []


class ActionSmartFallback(Action):
    ROUTES = [
        {
            "response": "utter_project_chatbot",
            "keywords": {
                "projekt": 3,
                "chatbot": 3,
                "website": 2,
                "webseite": 2,
                "bachelorarbeit": 2,
                "idee": 1,
            },
        },
        {
            "response": "utter_origin_overview",
            "keywords": {
                "ueber mich": 3,
                "über mich": 3,
                "hintergrund": 2,
                "motivation": 2,
                "wer bist du": 3,
                "wer ist maik": 3,
                "ueber maik": 2,
                "über maik": 2,
                "maik": 1,
            },
        },
        {
            "response": "utter_praxisphase_info",
            "keywords": {
                "praxisphase": 3,
                "praktikum": 3,
                "praxis": 2,
                "stelle": 2,
            },
        },
        {
            "response": "utter_praxisphase_why_company",
            "keywords": {
                "bei uns": 3,
                "zu uns": 3,
                "unser unternehmen": 4,
                "unsere firma": 4,
                "unser team": 4,
                "warum wir": 4,
                "warum genau wir": 5,
                "ausgerechnet diese firma": 5,
                "ausgerechnet hier": 4,
            },
        },
        {
            "response": "utter_person_sports",
            "keywords": {
                "verein": 3,
                "lieblingsverein": 3,
                "club": 2,
                "lieblingsclub": 3,
                "fussball": 3,
                "fußball": 3,
                "fan": 2,
                "rwe": 3,
                "rot weiss essen": 4,
                "rot-weiss essen": 4,
            },
        },
        {
            "response": "utter_person_unwind",
            "keywords": {
                "abschalten": 4,
                "ausgleich": 3,
                "freizeit": 3,
                "runterkommen": 4,
                "entspannen": 3,
                "entspannst": 3,
            },
        },
    ]

    def name(self) -> Text:
        return "action_smart_fallback"

    def _normalize_text(self, text: Text) -> Text:
        normalized = (text or "").strip().lower()
        return normalized.replace("ß", "ss")

    def _resolve_response(self, text: Text) -> Dict[Text, Any]:
        normalized = self._normalize_text(text)
        best_match: Optional[Dict[Text, Any]] = None

        for route in self.ROUTES:
            matches = [
                keyword
                for keyword in route["keywords"]
                if keyword in normalized
            ]
            if not matches:
                continue

            score = sum(route["keywords"][keyword] for keyword in matches)
            candidate = {
                "response": route["response"],
                "score": score,
                "matches": matches,
            }
            if best_match is None or candidate["score"] > best_match["score"]:
                best_match = candidate

        if best_match is not None:
            return best_match

        return {
            "response": "utter_fallback",
            "score": 0,
            "matches": [],
        }

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Score keyword groups and route to the closest known topic.
        latest_text = tracker.latest_message.get("text") or ""
        route = self._resolve_response(latest_text)
        logger.info(
            "smart_fallback text=%r response=%s score=%s matches=%s",
            latest_text,
            route["response"],
            route["score"],
            route["matches"],
        )
        dispatcher.utter_message(response=route["response"])
        return []
