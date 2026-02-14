from flask import Blueprint, jsonify, render_template, request
import requests

from .services.rasa_client import send_message

bp = Blueprint("routes", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify(
            {
                "response": "Bitte schick mir eine kurze Nachricht, dann helfe ich dir gern weiter 🙂",
            }
        )

    try:
        data = send_message(message)
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
