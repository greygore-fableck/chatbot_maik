from flask import Blueprint, jsonify, render_template, request
import requests

from .services.rasa_client import send_message

bp = Blueprint("routes", __name__)
GREET_ALIASES = {
    "hi",
    "hallo",
    "hey",
    "moin",
    "servus",
    "hallochen",
    "hallöchen",
    "guten tag",
}


def normalize_user_message(message: str) -> str:
    cleaned = message.strip().strip(".,!?;:").casefold()
    if cleaned in GREET_ALIASES:
        return "/greet"
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
        return jsonify(
            {
                "response": "Dazu habe ich gerade noch keine passende Antwort. Versuch es gern etwas anders zu formulieren.",
            }
        )

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
        return jsonify(
            {
                "response": combined
                or "Dazu habe ich gerade noch keine passende Antwort. Versuch es gern etwas anders zu formulieren.",
            }
        )

    return jsonify({"response": combined, "messages": messages})
