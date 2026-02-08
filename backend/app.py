from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from config import Config
from db import init_db
from services.rate_limit import init_redis
from utils.errors import error_response

from routes.places import bp as places_bp
from routes.interactions import bp as interactions_bp
from routes.safety import bp as safety_bp
from routes.moderation import bp as moderation_bp


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=app.config.get("CORS_ORIGINS", ["http://localhost:3000"]))

    init_db(app)
    init_redis(app)

    app.register_blueprint(places_bp, url_prefix="/v1")
    app.register_blueprint(interactions_bp, url_prefix="/v1")
    app.register_blueprint(safety_bp, url_prefix="/v1")
    app.register_blueprint(moderation_bp, url_prefix="/v1")

    register_error_handlers(app)
    return app


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_):
        return error_response(
            "Resource not found",
            error="Not Found",
            code="NOT_FOUND",
            status=404,
        )

    @app.errorhandler(RuntimeError)
    def runtime_error(err):
        return error_response(
            str(err),
            error="Internal Server Error",
            code="SERVER_ERROR",
            status=500,
        )

    @app.errorhandler(Exception)
    def unhandled_error(err):
        return error_response(
            str(err),
            error="Internal Server Error",
            code="SERVER_ERROR",
            status=500,
        )


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=8000)
