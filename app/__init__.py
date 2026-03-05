import os

from flask import Flask, redirect, request


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    enforce_https = os.getenv("ENFORCE_HTTPS", "0") == "1"
    canonical_host = os.getenv("CANONICAL_HOST", "").strip().lower()
    local_hosts = {"localhost", "127.0.0.1"}

    @app.before_request
    def redirect_to_secure_canonical_host():
        if request.path == "/health":
            return None

        host = (request.host or "").split(":", 1)[0].lower()
        if host in local_hosts:
            return None

        path_and_query = request.full_path.rstrip("?")
        forwarded_proto = (
            request.headers.get("X-Forwarded-Proto", request.scheme)
            .split(",", 1)[0]
            .strip()
            .lower()
        )

        redirect_host = canonical_host if canonical_host else request.host
        needs_https = enforce_https and forwarded_proto != "https"
        needs_canonical = canonical_host and host != canonical_host
        if needs_https or needs_canonical:
            return redirect(f"https://{redirect_host}{path_and_query}", code=301)

    from .routes import bp as routes_bp

    app.register_blueprint(routes_bp)
    return app
