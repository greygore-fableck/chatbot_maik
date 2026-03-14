from flask import Blueprint, jsonify, render_template, request, send_from_directory
import random
import requests

from .services.rasa_client import send_message

bp = Blueprint("routes", __name__)
MATCH_EXACT = "exact"
MATCH_CONTAINS = "contains"
DEFAULT_FALLBACK_TEXTS = [
    (
        "Ich bin mir gerade nicht ganz sicher, wie ich das einordnen soll. "
        "Ich kann dir aber direkt weiterhelfen."
    ),
    (
        "Das war fuer mich gerade nicht ganz eindeutig. "
        "Wir koennen aber direkt weitermachen."
    ),
    (
        "Darauf habe ich gerade keine wirklich gute Antwort. "
        "Ich kann dir aber sofort etwas Passendes zeigen."
    ),
    (
        "Mhh. Ich bin gerade nicht ganz sicher, was du meinst. "
        "Wir finden aber direkt einen Einstieg."
    ),
    (
        "Puh, da weiss ich gerade nicht genau, worauf du hinauswillst. "
        "Ich kann dir aber direkt etwas zeigen."
    ),
    "Da muss wohl noch ein wenig Gehirnschmalz fliessen. Vielleicht ist hier etwas fuer dich dabei.",
    "Da darf ich wohl noch etwas nachschaerfen. Vielleicht passt einer der Einstiege.",
    "Das habe ich gerade noch nicht sauber drauf. Vielleicht ist das hier spannend.",
    "Hier fehlt mir gerade noch die passende Antwort. Vielleicht hilft dir das hier weiter.",
    "Nicht ganz eindeutig gerade. Vielleicht ist das hier spannend.",
    "Da bin ich gerade nicht sicher. Vielleicht passt einer der Einstiege.",
    "Ich hab's gerade nicht ganz. Vielleicht ist hier etwas fuer dich dabei.",
]
DEFAULT_FALLBACK_BUTTON_SETS = [
    [
        {"title": "Zeig mir das Projekt 🤖💬", "payload": "/project_chatbot"},
        {"title": "Erzähl mir was über dich", "payload": "/origin_overview"},
        {"title": "Mehr zur Praxisphase", "payload": "/praxisphase_info"},
    ],
    [
        {"title": "Zum Projekt", "payload": "/project_chatbot"},
        {"title": "Über dich", "payload": "/origin_overview"},
        {"title": "Zur Praxisphase", "payload": "/praxisphase_info"},
    ],
    [
        {"title": "Projekt zeigen", "payload": "/project_chatbot"},
        {"title": "Hintergrund", "payload": "/origin_overview"},
        {"title": "Praxisphase", "payload": "/praxisphase_info"},
    ],
    [
        {"title": "Erzähl mir was über dich", "payload": "/origin_overview"},
        {"title": "Zeig mir das Projekt", "payload": "/project_chatbot"},
        {"title": "Praxisphase", "payload": "/praxisphase_info"},
    ],
    [
        {"title": "Zeig mir das Projekt", "payload": "/project_chatbot"},
        {"title": "Erzähl mir was über dich", "payload": "/origin_overview"},
    ],
    [
        {"title": "Erzähl mir was über dich", "payload": "/origin_overview"},
        {"title": "Praxisphase", "payload": "/praxisphase_info"},
    ],
    [
        {"title": "Zeig mir das Projekt", "payload": "/project_chatbot"},
        {"title": "Praxisphase", "payload": "/praxisphase_info"},
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
        "payload": "/current_status",
        "match": MATCH_CONTAINS,
        "aliases": {
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
        },
    },
    {
        "payload": "/project_why_chatbot",
        "match": MATCH_CONTAINS,
        "aliases": {
            "warum ein chatbot",
            "warum chatbot",
            "warum dialog statt navigation",
            "warum keine navigation",
            "warum keine menüs",
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


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/favicon.ico")
def favicon():
    return send_from_directory(bp.root_path + "/static", "favicon.ico")


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


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

    try:
        data = send_message(normalize_user_message(message), sender=sender)
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
