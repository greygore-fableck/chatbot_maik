import os

from app import create_app

app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "3000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, port=port)
