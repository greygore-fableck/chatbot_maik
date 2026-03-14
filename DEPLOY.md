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
./build_rasa_model.sh
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
- The build step must create and refresh `latest.tar.gz` before the Rasa service starts.
- Set `RASA_ACTION_ENDPOINT` per environment:
  - local: `http://127.0.0.1:5056/webhook`
  - Railway Rasa service: URL of the Railway actions service, e.g. `https://<your-actions-service>/webhook`
- If you move files, update the commands above.
