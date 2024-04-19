
# Core Flask imports
from flask import Flask

from app import routes
# Third-party imports
from scripts.Database import db

# App imports

db_manager = db


def create_app():
    app = Flask(__name__)

    db_manager.connect()

    app.register_blueprint(routes.bp)

    return app
