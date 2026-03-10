from flask import Blueprint, jsonify, render_template, request
import requests

from .services.rasa_client import send_message

bp = Blueprint("routes", __name__)
MATCH_EXACT = "exact"
MATCH_CONTAINS = "contains"
DEFAULT_FALLBACK_TEXT = (
    "Ich bin mir gerade nicht ganz sicher, wie ich das einordnen soll. "
    "Ich kann dir aber direkt beim Projekt, bei meinem Hintergrund oder bei der Praxisphase weiterhelfen."
)
DEFAULT_FALLBACK_BUTTONS = [
    {"title": "Zeig mir das Projekt 🤖💬", "payload": "/project_chatbot"},
    {"title": "Erzähl mir was über dich", "payload": "/origin_overview"},
    {"title": "Mehr zur Praxisphase", "payload": "/praxisphase_info"},
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
            "ciao",
            "bis bald",
            "mach's gut",
            "machs gut",
            "auf wiedersehen",
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
            "wer bistn du",
            "mit wem spreche ich",
            "was bist du",
            "bist du ein bot",
        },
    },
    # General capability and topic entry points.
    {
        "payload": "/smalltalk_what_can_you_do",
        "match": MATCH_CONTAINS,
        "aliases": {
            "was kannst du",
            "wobei kannst du helfen",
            "wie kannst du mir helfen",
            "wofuer bist du da",
            "wofür bist du da",
            "was machst du",
        },
    },
    {
        "payload": "/project_chatbot",
        "match": MATCH_CONTAINS,
        "aliases": {
            "erzähl mir was über das projekt",
            "erzähl mir vom projekt",
            "zeig mir das projekt",
            "was ist mit deinem projekt",
            "projekt",
            "chatbot",
            "website",
            "bachelorarbeit",
        },
    },
    # Contact should stay below broader topic routing.
    {
        "payload": "/contact_email",
        "match": MATCH_CONTAINS,
        "aliases": {
            "kontakt",
            "mail",
            "email",
            "e-mail",
            "erreichbar",
            "wie kann ich dich erreichen",
            "ich suche kontakt",
        },
    },
]


def build_default_fallback_response():
    return {
        "response": DEFAULT_FALLBACK_TEXT,
        "messages": [
            {
                "text": DEFAULT_FALLBACK_TEXT,
                "buttons": DEFAULT_FALLBACK_BUTTONS,
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
