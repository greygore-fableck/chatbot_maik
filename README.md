# Chatbot (Flask + Rasa)

Dieses Projekt kombiniert eine kleine Flask-Webapp (UI + API) mit einem Rasa-Backend.

## Struktur

```
chatbotFlask/
  app/                 # Flask App (UI + /webhook)
    services/          # Rasa-Client
    static/            # CSS/JS/HTML Assets
    templates/         # Jinja Templates
  rasa/                # Rasa Projekt (nlu, stories, domain, models, actions)
  scripts/             # optional: weitere Helfer
  app.py               # Flask Einstieg
  run_chatbot.sh       # Startet genau einen Service (flask|rasa|actions)
  start.sh             # Startet alle Services im Hintergrund + Health-Checks
  stop.sh              # Stoppt Services via PID-Dateien und Port-Fallback
  restart.sh           # Stop + Start in einem Befehl
  status.sh            # Zeigt PID + HTTP-Status aller Services
```

## Start
1. Stelle sicher, dass deine virtuelle Umgebung aktiv ist.
2. Starte alle Services mit einem Befehl:

```bash
./start.sh
```

Das Script startet `flask`, `rasa` und `actions` im Hintergrund, schreibt Logs nach `/tmp/chatbot-*.log` und prüft die Health-Endpoints.

Optional kannst du weiterhin einzelne Services separat starten:

```bash
# Flask
CHATBOT_SERVICE=flask ./run_chatbot.sh

# Rasa (festes Modell, kein Training beim Start)
CHATBOT_SERVICE=rasa RASA_MODEL_PATH=./rasa/models/latest.tar.gz ./run_chatbot.sh

# Actions
CHATBOT_SERVICE=actions ./run_chatbot.sh
```

## Stop

```bash
./stop.sh
```

Das Script beendet zuerst die über `start.sh` gestarteten PIDs und räumt danach ggf. noch Prozesse auf Ports `3000/5005/5056` auf.

## Restart

```bash
./restart.sh
```

`restart.sh` läuft nur erfolgreich durch, wenn danach alle 3 Services laut `status.sh` wirklich `running` und per HTTP erreichbar sind.

## Status

```bash
./status.sh
```

Exit-Code ist `0` nur wenn alle Services gesund sind, sonst `1`.

## Modell-Link setzen

```bash
# auf das neueste Modell setzen
./set_latest_model.sh

# auf ein bestimmtes Modell setzen
./set_latest_model.sh 20260305-141238-avocado-geyser.tar.gz
```

## Konfiguration (.env)

Du kannst lokale Einstellungen über `.env` setzen (siehe `.env.example`).
Für Production kannst du zusätzlich setzen:
- `ENFORCE_HTTPS=1` (erzwingt HTTPS-Redirect)
- `CANONICAL_HOST=www.maikmitai.de` (erzwingt eine eindeutige Domain)

## Hinweise

- Flask hat einen Health-Check unter `/health`.
- Rasa läuft standardmäßig auf Port 5005.
- Action Server läuft standardmäßig auf Port 5056.
- Flask läuft standardmäßig auf Port 3000.
