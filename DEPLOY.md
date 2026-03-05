# Deploy

## Local workflow
1. git status -sb
2. git add <file>
3. git commit -m "short description"
4. git push origin main

## Railway services
This repo is deployed as three separate Railway services:
- Flask app
- Rasa server
- Rasa actions

## Railway commands
### Rasa server
Build command:
```
# leer lassen (kein Training beim Start/Build)
```
Start command:
```
CHATBOT_SERVICE=rasa RASA_MODEL_PATH=/app/rasa/models/latest.tar.gz ./run_chatbot.sh
```

### Rasa actions
Start command:
```
CHATBOT_SERVICE=actions ./run_chatbot.sh
```

### Flask app
Start command:
```
CHATBOT_SERVICE=flask ./run_chatbot.sh
```

## Notes
- Keep Rasa config/domain/data under rasa/.
- Use a fixed model file path in production (`/app/rasa/models/latest.tar.gz`).
- Ensure `latest.tar.gz` points to your intended trained model before deploy.
- If you move files, update the commands above.
