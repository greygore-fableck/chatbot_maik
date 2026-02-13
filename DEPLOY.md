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
rasa train --config rasa/config.yml --domain rasa/domain.yml --data rasa/data --out rasa/models
```
Start command:
```
rasa run --port $PORT --enable-api --cors "*" --model rasa/models
```

### Rasa actions
Start command:
```
rasa run actions --port $PORT
```

## Notes
- Keep Rasa config/domain/data under rasa/.
- If you move files, update the commands above.
