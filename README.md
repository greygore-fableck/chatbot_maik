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
  run_chatbot.sh        # Startet Rasa + Actions + Flask
  start.sh              # Startet run_chatbot.sh via nohup
  stop.sh               # Stoppt Ports 3000/5005/5056
```

## Start

1. Stelle sicher, dass deine virtuelle Umgebung aktiv ist.
2. Starte alles:

```bash
./start.sh
```

3. Öffne:

- http://localhost:3000

## Stop

```bash
./stop.sh
```

## Konfiguration (.env)

Du kannst lokale Einstellungen über `.env` setzen (siehe `.env.example`).

## Hinweise

- Rasa läuft standardmäßig auf Port 5005.
- Action Server läuft auf Port 5056.
- Flask läuft auf Port 3000.
