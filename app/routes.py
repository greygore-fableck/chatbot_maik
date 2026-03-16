from flask import Blueprint, jsonify, render_template, request, send_from_directory
from datetime import datetime
from pathlib import Path
import json
import random
import re
import requests

from .services.rasa_client import send_message

bp = Blueprint("routes", __name__)
MATCH_EXACT = "exact"
MATCH_CONTAINS = "contains"
BOOK_RECOMMENDATION_PROMPT_PAYLOAD = "__book_recommendation_prompt__"
BOOK_RECOMMENDATION_LIST_PAYLOAD = "__book_recommendation_list__"
MAX_BOOK_RECOMMENDATION_LENGTH = 20
BOOK_RECOMMENDATIONS_PATH = Path(__file__).resolve().parent / "data" / "book_recommendations.json"
DEFAULT_FALLBACK_TEXTS = [
    "Ich bin mir gerade nicht ganz sicher, was du genau meinst. Vielleicht hilft dir einer dieser Einstiege:",
    "Das ist für mich nicht ganz eindeutig. Wie wäre es damit?",
    "Ich bin mir nicht ganz sicher, worauf du hinauswillst. Wenn du magst, steigen wir direkt bei einem der Kernthemen ein.",
    "Moment ... wolltest du vielleicht darauf hinaus?",
    "Sekunde. Vielleicht ist einer dieser Wege gerade einfacher.",
]
DEFAULT_FALLBACK_BUTTON_SETS = [
    [
        {"title": "Zeig mir das Projekt 🤖💬", "payload": "/project_chatbot"},
        {"title": "Frag mich was ...", "payload": "/show_playground_questions"},
    ],
    [
        {"title": "Projektidee", "payload": "/project_goal"},
        {"title": "Technische Umsetzung", "payload": "/tech_impl"},
        {"title": "Etwas anderes anzeigen", "payload": "/show_playground_questions"},
    ],
    [
        {"title": "Projektidee", "payload": "/project_goal"},
        {"title": "Werdegang", "payload": "/werdegang_overview"},
        {"title": "Warum ein Chatbot?", "payload": "/project_why_chatbot"},
        {"title": "Frag mich was ...", "payload": "/show_playground_questions"},
    ],
    [
        {"title": "Warum ein Chatbot?", "payload": "/project_why_chatbot"},
        {"title": "Praxisphase", "payload": "/praxisphase_info"},
        {"title": "Nicht ganz? Dann vielleicht das:", "payload": "/show_playground_questions"},
    ],
    [
        {"title": "Kaffee oder Tee?", "payload": "/playground_coffee_tea"},
        {"title": "Bist du eher kreativ oder strukturiert?", "payload": "/playground_structure_creativity"},
        {"title": "Frühaufsteher oder Nachteule?", "payload": "/playground_early_bird"},
    ],
]
# Order matters: more specific rewrites should stay above broader topic matches.
NORMALIZATION_RULES = [
    # Exact command-style shortcuts.
    {
        "payload": "/greet",
        "match": MATCH_EXACT,
        "aliases": {
            "hi",
            "hallo",
            "hey",
            "na",
            "na?",
            "na du",
            "hey na",
            "moin",
            "servus",
            "hallochen",
            "hallöchen",
            "guten tag",
        },
    },
    {
        "payload": "/goodbye",
        "match": MATCH_EXACT,
        "aliases": {
            "tschüss",
            "tschuess",
            "tschau",
            "tschau",
            "bye",
            "ciao",
            "bis bald",
            "bis dann",
            "man sieht sich",
            "mach's gut",
            "machs gut",
            "auf wiedersehen",
        },
    },
    {
        "payload": "/affirm",
        "match": MATCH_EXACT,
        "aliases": {
            "ja",
            "jo",
            "jup",
            "jawohl",
            "yes",
        },
    },
    {
        "payload": "/deny",
        "match": MATCH_EXACT,
        "aliases": {
            "nee",
            "nö",
            "noe",
            "nope",
        },
    },
    {
        "payload": "/thanks",
        "match": MATCH_EXACT,
        "aliases": {
            "thx",
            "merci",
            "danke schön",
            "danke schoen",
        },
    },
    {
        "payload": BOOK_RECOMMENDATION_PROMPT_PAYLOAD,
        "match": MATCH_EXACT,
        "aliases": {
            "buchempfehlung",
            "buch empfehlung",
            "buchtipp",
            "buchtipps",
            "buch tipp",
            "lesetipp",
            "lesetipps",
        },
    },
    {
        "payload": BOOK_RECOMMENDATION_LIST_PAYLOAD,
        "match": MATCH_EXACT,
        "aliases": {
            "bisherige empfehlungen",
            "empfehlungen",
            "buchliste",
            "leseliste",
        },
    },
    {
        "payload": "/person_age",
        "match": MATCH_EXACT,
        "aliases": {
            "wie alt bist du",
            "wie alt bist du denn",
            "wie alt ist maik",
            "dein alter",
            "alter",
        },
    },
    {
        "payload": "/english_fallback",
        "match": MATCH_EXACT,
        "aliases": {
            "mach mal auf englisch",
            "bitte auf englisch",
            "auf englisch bitte",
            "antwort auf englisch",
        },
    },
    # Person-related shortcuts.
    {
        "payload": "/origin_overview",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wer ist maik",
            "erzähl mir etwas über maik",
            "erzähl mir was über maik",
            "was kannst du mir über maik sagen",
            "sag mir was über maik",
            "mehr über maik",
            "über maik",
        },
    },
    {
        "payload": "/smalltalk_who_are_you",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was machst du",
            "wer bist du",
            "wer genau bist du",
            "wer bistn du",
            "mit wem spreche ich",
            "was bist du",
            "bist du maik",
            "bist du der chatbot",
            "bist du ein bot",
        },
    },
    {
        "payload": "/smalltalk_how_are_you",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wie geht's",
            "wie gehts",
            "wie geht es dir",
            "alles gut",
            "wie läuft's",
            "wie laeuft's",
            "wie läufts",
            "wie laeufts",
            "na alles klar",
            "na wie gehts",
            "was geht",
        },
    },
    {
        "payload": "/smalltalk_day",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wie läuft dein tag",
            "hast du einen guten tag",
            "hast du heute einen guten tag",
            "guten tag gehabt",
            "läuft dein tag gut",
            "wie ist dein tag",
            "na alles gut heute",
            "wie läufts heute",
        },
    },
    {
        "payload": "/project_improve",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was kannst du noch verbessern",
            "was könntest du noch verbessern",
            "was würdest du noch verbessern",
        },
    },
    # General capability and topic entry points.
    {
        "payload": "/study_details",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was studierst du",
            "was studierst du genau",
            "welchen studiengang studierst du",
            "was ist dein studiengang",
        },
    },
    {
        "payload": "/tech_skills",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was kannst du technisch",
            "was hast du technisch umgesetzt",
            "was ist dein technischer schwerpunkt",
            "welche technischen skills hast du",
        },
    },
    {
        "payload": "/programming_languages",
        "match": MATCH_CONTAINS,
        "aliases": {
            "welche programmiersprachen kannst du",
            "welche programmiersprache kannst du",
            "welche sprachen kannst du",
            "mit welchen sprachen arbeitest du",
        },
    },
    {
        "payload": "/tech_impl",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wie funktioniert der bot",
            "wie funktioniert dein bot",
            "wie laeuft der bot technisch",
            "wie läuft der bot technisch",
            "wie arbeitet der bot",
        },
    },
    {
        "payload": "/praxisphase_why_company",
        "match": MATCH_CONTAINS,
        "aliases": {
            "warum diese bewerbung",
            "warum bewirbst du dich hier",
            "warum diese praxisphase",
            "warum diese stelle",
        },
    },
    {
        "payload": "/smalltalk_what_can_you_do",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was kannst du",
            "was kann ich hier machen",
            "wobei kannst du helfen",
            "wobei hilfst du mir",
            "wie kannst du mir helfen",
            "wofuer bist du da",
            "wofür bist du da",
            "wofuer bist du gedacht",
            "wofür bist du gedacht",
        },
    },
    {
        "payload": "/smalltalk_time_meta",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wie spät ist es",
            "wie spaet ist es",
            "arbeitest du nachts",
            "bist du nachts da",
            "schläfst du eigentlich nie",
            "schlaefst du eigentlich nie",
        },
    },
    {
        "payload": "/smalltalk_why_so",
        "match": MATCH_CONTAINS,
        "aliases": {
            "warum so",
            "wieso so",
            "warum eigentlich so",
            "wieso eigentlich so",
            "warum diese antwort",
        },
    },
    {
        "payload": "/current_status",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was machst du beruflich",
            "beruflich",
            "was arbeitest du beruflich",
            "was machst du gerade",
            "was machst du aktuell",
            "was ist gerade dein fokus",
            "was ist dein aktueller status",
            "woran arbeitest du gerade",
            "was ist bei dir gerade los",
        },
    },
    {
        "payload": "/experience_summary",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was bringst du mit",
            "was bringst du konkret mit",
            "was bringst du fachlich mit",
            "was kannst du fachlich",
            "was kannst du schon",
            "was kann maik",
            "was kann maik eigentlich",
            "was kann maik fachlich",
            "warum sollte man mit dir sprechen",
            "warum bist du interessant",
        },
    },
    {
        "payload": "/projects_experience",
        "match": MATCH_CONTAINS,
        "aliases": {
            "hast du praktische erfahrung",
            "hast du schon praktische erfahrung",
            "wie viel praktische erfahrung hast du",
            "welche projekte hast du gemacht",
            "woran hast du gearbeitet",
        },
    },
    {
        "payload": "/strengths_tasks",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was machst du am liebsten",
            "worin bist du gut",
            "welche aufgaben liegen dir",
            "welche aufgaben liegen dir?",
            "welche aufgaben magst du",
            "was sind deine stärken",
            "was sind deine fachlichen stärken",
            "was kannst du richtig gut",
        },
    },
    {
        "payload": "/person_collab",
        "match": MATCH_CONTAINS,
        "aliases": {
            "warum passt du in ein team",
            "was macht dich angenehm in der zusammenarbeit",
            "wie arbeitest du mit anderen",
        },
    },
    {
        "payload": "/person_future_vision",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wo siehst du dich in 1 jahr",
            "wo siehst du dich in 3 jahren",
            "wo siehst du dich in 5 jahren",
            "wo willst du in ein paar jahren stehen",
            "wie sieht deine zukunft aus",
            "wo willst du langfristig hin",
        },
    },
    {
        "payload": "/smalltalk_humor",
        "match": MATCH_EXACT,
        "aliases": {
            "haha",
            "lol",
            "witzig",
        },
    },
    {
        "payload": "/playground_coffee_tea",
        "match": MATCH_EXACT,
        "aliases": {
            "kaffee oder tee",
            "lieber kaffee oder tee",
            "bist du team kaffee oder tee",
        },
    },
    {
        "payload": "/smalltalk_coffee",
        "match": MATCH_CONTAINS,
        "aliases": {
            "kaffee",
            "brauchst du kaffee",
            "willst du kaffee",
            "ohne kaffee läuft nichts",
            "erstmal kaffee",
            "zeit für kaffee",
            "noch einen kaffee",
        },
    },
    {
        "payload": "/project_why_chatbot",
        "match": MATCH_CONTAINS,
        "aliases": {
            "warum gerade ein chatbot",
            "warum ein chatbot",
            "warum chatbot",
            "warum dialog statt navigation",
            "warum keine navigation",
            "warum keine menüs",
        },
    },
    {
        "payload": "/project_chatbot",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was ist dein aktuelles projekt",
            "was ist gerade dein projekt",
            "an welchem projekt arbeitest du",
            "woran arbeitest du gerade für ein projekt",
            "ist das hier dein aktuelles projekt",
            "erzähl mir was über das projekt",
            "erzähl mir vom projekt",
            "zeig mir das projekt",
            "was ist mit deinem projekt",
            "chatbot",
            "website",
            "bachelorarbeit",
        },
    },
    {
        "payload": "/praxisphase_info",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was suchst du",
            "was suchst du gerade",
            "was suchst du eigentlich",
            "was suchst du im moment",
            "wonach suchst du",
            "wonach suchst du gerade",
            "was willst du",
            "was willst du gerade",
            "was willst du aktuell",
            "was ist dir gerade wichtig",
        },
    },
    {
        "payload": "/application_details",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wonach suchst du konkret",
            "was suchst du ganz konkret",
            "welche rolle passt zu dir",
            "was erwartest du dir von einer praxisphase",
            "was erwartest du von einer praxisphase",
        },
    },
    {
        "payload": "/person_motivation",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was motiviert dich",
        },
    },
    {
        "payload": "/person_development",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was möchtest du fachlich noch vertiefen",
        },
    },
    {
        "payload": "/person_outside_work",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was machst du gern außerhalb der arbeit",
            "was machst du gern ausserhalb der arbeit",
            "was machst du außerhalb der arbeit",
            "was machst du ausserhalb der arbeit",
        },
    },
    {
        "payload": "/person_records_followup",
        "match": MATCH_CONTAINS,
        "aliases": {
            "wie viele schallplatten hast du",
            "wie viele platten hast du",
            "welche schallplatte war deine letzte",
            "welche platte war deine letzte",
            "was war dein letzter vinyl kauf",
            "hast du eine lieblingsplatte",
            "schallplatte",
            "platten",
            "vinyl",
        },
    },
    {
        "payload": "/playground_structure_creativity",
        "match": MATCH_CONTAINS,
        "aliases": {
            "bist du eher kreativ oder strukturiert",
            "kreativ oder strukturiert",
        },
    },
    {
        "payload": "/playground_early_bird",
        "match": MATCH_CONTAINS,
        "aliases": {
            "frühaufsteher oder nachteule",
            "bist du eher frühaufsteher oder nachteule",
        },
    },
    {
        "payload": "/project_menu_meta",
        "match": MATCH_CONTAINS,
        "aliases": {
            "gibt es hier kein menü",
            "gibt's hier kein menü",
            "gibt es hier kein menu",
            "gibt's hier kein menu",
            "warum gibt es kein menü",
            "warum gibt es kein menu",
            "wo ist das menü",
            "ist das keine klassische website",
            "warum keine klassische website",
        },
    },
    {
        "payload": "/project_goal",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was ist dein ziel mit dem projekt",
            "was ist dein ziel mit diesem projekt",
            "welches ziel verfolgst du mit dem projekt",
            "was willst du mit diesem projekt erreichen",
        },
    },
    {
        "payload": "/project_business_use",
        "match": MATCH_CONTAINS,
        "aliases": {
            "einsatz im unternehmen",
            "nutzen im unternehmen",
            "für unternehmen",
            "in firmen einsetzen",
            "im arbeitsalltag helfen",
        },
    },
    {
        "payload": "/person_development",
        "match": MATCH_CONTAINS,
        "aliases": {
            "fachliche entwicklung",
            "wie entwickelst du dich weiter",
            "was lernst du gerade",
            "welche themen willst du vertiefen",
            "worin willst du besser werden",
        },
    },
    # Contact should stay below broader topic routing.
    {
        "payload": "/contact_email",
        "match": MATCH_CONTAINS,
        "aliases": {
            "kontakt",
            "kontakt?",
            "mail",
            "email",
            "e-mail",
            "erreichbar",
            "wie kann ich dich erreichen",
            "wie erreiche ich dich",
            "ich suche kontakt",
        },
    },
    {
        "payload": "/links_portfolio",
        "match": MATCH_CONTAINS,
        "aliases": {
            "kann ich deinen lebenslauf sehen",
            "hast du unterlagen",
            "hast du bewerbungsunterlagen",
            "gibt es weitere unterlagen",
        },
    },
]


def build_default_fallback_response():
    text = random.choice(DEFAULT_FALLBACK_TEXTS)
    buttons = random.choice(DEFAULT_FALLBACK_BUTTON_SETS)
    return {
        "response": text,
        "messages": [
            {
                "text": text,
                "buttons": buttons,
            }
        ],
    }


def build_person_name_opinion_response(message: str):
    cleaned = (message or "").strip()
    patterns = [
        r"was h[äa]ltst du von\s+([A-Za-zÄÖÜäöüß-]+)\??",
        r"was ist mit\s+([A-Za-zÄÖÜäöüß-]+)\??",
        r"wie findest du\s+([A-Za-zÄÖÜäöüß-]+)\??",
    ]
    name = None
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            name = match.group(1)
            break

    if not name:
        return None

    normalized = re.sub(r"[^A-Za-zÄÖÜäöüß-]", "", name).lower()
    known_names = {"sanja", "axel", "rita", "roland", "sarah"}

    if normalized in known_names:
        text = f"{name}: Super Mensch, aber lass uns doch lieber wieder über das Projekt sprechen :)"
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

    return {
        "response": text,
        "messages": [
            {
                "text": text,
                "buttons": buttons,
            }
        ],
    }


def matches_alias(cleaned: str, aliases: set[str], match_mode: str) -> bool:
    if match_mode == MATCH_EXACT:
        return cleaned in aliases
    return any(alias in cleaned for alias in aliases)


def normalize_user_message(message: str) -> str:
    cleaned = message.strip().strip(".,!?;:").casefold()
    for rule in NORMALIZATION_RULES:
        if matches_alias(cleaned, rule["aliases"], rule["match"]):
            return rule["payload"]
    return message


def load_book_recommendations() -> list[dict]:
    try:
        if not BOOK_RECOMMENDATIONS_PATH.exists():
            return []
        data = json.loads(BOOK_RECOMMENDATIONS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict) and isinstance(item.get("text"), str)]
    except (OSError, json.JSONDecodeError):
        return []
    return []


def save_book_recommendations(items: list[dict]) -> None:
    BOOK_RECOMMENDATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOOK_RECOMMENDATIONS_PATH.write_text(
        json.dumps(items[:12], ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def clean_book_recommendation(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def build_book_recommendation_prompt_response() -> dict:
    text = "Hast du eine Empfehlung für meinen SuB?"
    return {
        "response": text,
        "messages": [
            {
                "text": text,
                "buttons": [
                    {"title": "Bisherige Empfehlungen", "payload": BOOK_RECOMMENDATION_LIST_PAYLOAD},
                    {"title": "Frag mich was ...", "payload": "/show_playground_questions"},
                ],
                "custom": {
                    "book_recommendation_input": {
                        "placeholder": "Titel oder Autor",
                        "submit_label": "Empfehlen",
                        "max_length": MAX_BOOK_RECOMMENDATION_LENGTH,
                    }
                },
            }
        ],
    }


def build_book_recommendation_list_response() -> dict:
    items = load_book_recommendations()
    text = "Hier liegen die bisherigen Empfehlungen."
    return {
        "response": text,
        "messages": [
            {
                "text": text,
                "buttons": [
                    {"title": "Noch eine Empfehlung", "payload": BOOK_RECOMMENDATION_PROMPT_PAYLOAD},
                    {"title": "Frag mich was ...", "payload": "/show_playground_questions"},
                ],
                "custom": {
                    "book_recommendation_list": {
                        "title": "Bisherige Empfehlungen",
                        "items": [item["text"] for item in items[:8]],
                        "empty_text": "Noch nichts eingetragen. Du könntest das ändern.",
                    }
                },
            }
        ],
    }


def build_book_recommendation_saved_response(recommendation: str, duplicate: bool = False) -> dict:
    text = (
        "Steht schon auf der Liste."
        if duplicate
        else "Kommt auf die Liste. Mein SuB bedankt sich vorsichtig."
    )
    items = load_book_recommendations()
    return {
        "response": text,
        "messages": [
            {
                "text": text,
                "buttons": [
                    {"title": "Bisherige Empfehlungen", "payload": BOOK_RECOMMENDATION_LIST_PAYLOAD},
                    {"title": "Frag mich was ...", "payload": "/show_playground_questions"},
                ],
                "custom": {
                    "book_recommendation_list": {
                        "title": "Bisherige Empfehlungen",
                        "items": [item["text"] for item in items[:8]],
                        "empty_text": "Noch nichts eingetragen. Du könntest das ändern.",
                    }
                },
            }
        ],
    }


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/favicon.ico")
def favicon():
    response = send_from_directory(
        bp.root_path + "/static",
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@bp.route("/book-recommendations", methods=["POST"])
def book_recommendations():
    payload = request.get_json(silent=True) or {}
    recommendation = clean_book_recommendation(payload.get("recommendation") or "")
    if not recommendation:
        return jsonify({"error": "Bitte gib eine kurze Empfehlung ein."}), 400
    if len(recommendation) > MAX_BOOK_RECOMMENDATION_LENGTH:
        return jsonify({"error": "Bitte maximal 20 Zeichen verwenden."}), 400

    items = load_book_recommendations()
    normalized = recommendation.casefold()
    duplicate = any(item.get("text", "").casefold() == normalized for item in items)
    if not duplicate:
        items.insert(
            0,
            {
                "text": recommendation,
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            },
        )
        save_book_recommendations(items)

    return jsonify(build_book_recommendation_saved_response(recommendation, duplicate=duplicate))


@bp.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    sender = (payload.get("sender") or "web-user").strip() or "web-user"
    if not message:
        return jsonify(
            {
                "response": "Bitte schick mir eine kurze Nachricht, dann helfe ich dir gern weiter 🙂",
            }
        )

    direct_person_name_opinion = build_person_name_opinion_response(message)
    if direct_person_name_opinion is not None:
        return jsonify(direct_person_name_opinion)

    normalized_message = normalize_user_message(message)
    if normalized_message == BOOK_RECOMMENDATION_PROMPT_PAYLOAD:
        return jsonify(build_book_recommendation_prompt_response())
    if normalized_message == BOOK_RECOMMENDATION_LIST_PAYLOAD:
        return jsonify(build_book_recommendation_list_response())

    try:
        data = send_message(normalized_message, sender=sender)
    except requests.RequestException:
        return jsonify(
            {
                "response": "Der Bot ist gerade kurz nicht erreichbar. Versuch es bitte in 10–20 Sekunden nochmal.",
            }
        )

    if not data:
        return jsonify(build_default_fallback_response())

    messages = []
    for item in data:
        text = item.get("text", "") or ""
        buttons = item.get("buttons") or []
        custom = item.get("custom") or {}
        if text or buttons or custom:
            message = {"text": text, "buttons": buttons}
            if custom:
                message["custom"] = custom
            messages.append(message)

    combined = " ".join(item.get("text", "") for item in data if item.get("text"))
    if not messages:
        if combined:
            return jsonify({"response": combined})
        return jsonify(build_default_fallback_response())

    return jsonify({"response": combined, "messages": messages})
