from flask import Flask

from routes import bp
from utils import CURRENT


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.register_blueprint(bp)
    app.config["CURRENT"] = CURRENT
    return app


app = create_app()
