from __future__ import annotations

import os
from typing import Any, Dict, List

import requests


RASA_WEBHOOK_URL = os.getenv(
    "RASA_URL", "http://localhost:5005/webhooks/rest/webhook"
)


def send_message(message: str, sender: str = "web-user") -> List[Dict[str, Any]]:
    response = requests.post(
        RASA_WEBHOOK_URL,
        json={"sender": sender, "message": message},
        timeout=8,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        return data
    return []
