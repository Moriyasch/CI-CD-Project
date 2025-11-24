from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# ------------------------------------------------------------------------------
# Flask app configuration
# ------------------------------------------------------------------------------

app = Flask(__name__)

# SQLite database file in the current folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "cards.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ------------------------------------------------------------------------------
# Database models
# ------------------------------------------------------------------------------

class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cards = db.relationship("Card", backref="topic", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False)

    card_type = db.Column(db.String(50), nullable=False)  # e.g. 'flashcard', 'summary'
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "card_type": self.card_type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# ------------------------------------------------------------------------------
# Dummy content generator (placeholder instead of OpenAI)
# ------------------------------------------------------------------------------

def generate_dummy_content(topic: str, card_type: str) -> str:
    """
    Simple placeholder generator for different card types.
    Later we will replace this with a real OpenAI call.
    """
    if card_type == "flashcard":
        return f"Q: What is {topic}?\nA: This is a simple explanation of {topic}."
    elif card_type == "summary":
        return f"Summary for {topic}: this is a short high-level summary."
    elif card_type == "quiz":
        return f"Quiz question about {topic}: write one key concept related to it."
    elif card_type == "task":
        return f"Task for {topic}: perform a small exercise that uses this topic in practice."
    elif card_type == "usecase":
        return f"Use case for {topic}: describe when and why you would use {topic}."
    elif card_type == "mindmap":
        return f"Mindmap structure for {topic}: main idea -> subtopic A, subtopic B, subtopic C."
    else:
        return f"Generic content for {topic} (type: {card_type})."

# ------------------------------------------------------------------------------
# Simple health endpoint
# ------------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# ------------------------------------------------------------------------------
# Topics endpoints
# ------------------------------------------------------------------------------

@app.route("/topics", methods=["GET"])
def list_topics():
    topics = Topic.query.all()
    data = [t.to_dict() for t in topics]
    return jsonify(data), 200

@app.route("/topics", methods=["POST"])
def create_topic():
    """
    Create a new topic and generate cards in the requested formats.
    Expected JSON body:
    {
        "topic": "Docker volumes",
        "formats": ["flashcard", "summary", "quiz"]
    }
    """
    data = request.get_json()

    if not data or "topic" not in data:
        return jsonify({"error": "Missing 'topic' in request body"}), 400

    topic_name = data["topic"].strip()
    formats = data.get("formats", [])

    if not topic_name:
        return jsonify({"error": "Topic name cannot be empty"}), 400

    if not isinstance(formats, list) or not formats:
        return jsonify({"error": "Formats must be a non-empty list"}), 400

    # Check if topic already exists
    existing = Topic.query.filter_by(name=topic_name).first()
    if existing:
        return jsonify({"error": "Topic already exists"}), 409

    # Create the topic
    new_topic = Topic(name=topic_name)
    db.session.add(new_topic)
    db.session.flush()  # so new_topic.id is available

    created_cards = []

    for card_type in formats:
        content = generate_dummy_content(topic_name, card_type)
        card = Card(
            topic_id=new_topic.id,
            card_type=card_type,
            content=content,
        )
        db.session.add(card)
        created_cards.append(card)

    db.session.commit()

    response = {
        "topic": new_topic.to_dict(),
        "cards": [c.to_dict() for c in created_cards],
    }
    return jsonify(response), 201


# ------------------------------------------------------------------------------
# App entrypoint
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Create the SQLite tables if they don't exist yet
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
