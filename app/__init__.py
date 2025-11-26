# app/__init__.py

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# אובייקט DB גלובלי
db = SQLAlchemy()


def create_app():
    """
    יוצרת את אפליקציית Flask, מגדירה קונפיגורציה,
    מחברת את ה-DB, רושמת Blueprints, ויוצרת טבלאות.
    """
    app = Flask(__name__)

    # SQLite database file in the project folder (one level up from this file)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    db_path = os.path.join(base_dir, "cards.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # לחבר את db לאפליקציה
    db.init_app(app)

    # לייבא מודלים כדי ש-SQLAlchemy יכיר את הטבלאות
    from . import models  # noqa: F401

    # לייבא ולרשום Blueprints
    from .routes.topics import topics_bp
    from .routes.cards import cards_bp

    app.register_blueprint(topics_bp)
    app.register_blueprint(cards_bp)

    # ----- health endpoint -----
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    # ליצור את הטבלאות אם לא קיימות
    with app.app_context():
        db.create_all()

    # הדפסה לעזרת דיבאג - לראות אילו ראוטים רשומים
    print("ROUTES:", app.url_map)

    return app
