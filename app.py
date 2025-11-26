from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# --------------------------------------------------------------------------
# Flask app configuration
# --------------------------------------------------------------------------

app = Flask(__name__)

# SQLite database file in the current folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "cards.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

VALID_CARD_TYPES = {"flashcard", "summary", "quiz", "task", "usecase", "mindmap"}

# --------------------------------------------------------------------------
# Database models
# --------------------------------------------------------------------------

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

# --------------------------------------------------------------------------
# Dummy content generator (placeholder instead of OpenAI)
# --------------------------------------------------------------------------

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

# --------------------------------------------------------------------------
# Simple health endpoint
# --------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# --------------------------------------------------------------------------
# Topics endpoints
# --------------------------------------------------------------------------

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

    # validate requested card types
    for f in formats:
        if f not in VALID_CARD_TYPES:
            return jsonify({
                "error": f"Invalid card_type in formats: '{f}'",
                "allowed_types": list(VALID_CARD_TYPES),
            }), 400

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

@app.route("/topics/<int:topic_id>/cards", methods=["GET"])
def list_topic_cards(topic_id: int):
    """
    Return all cards for a given topic.
    Optional query param:
    ?type=flashcard / summary / quiz / task / usecase / mindmap
    """
    # קודם בודקים שהנושא קיים
    topic = Topic.query.get(topic_id)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # אפשרות לפילטר לפי card_type
    card_type = request.args.get("type")

    if card_type:
        cards = Card.query.filter_by(topic_id=topic_id, card_type=card_type).all()
    else:
        cards = Card.query.filter_by(topic_id=topic_id).all()

    data = [c.to_dict() for c in cards]
    return jsonify(data), 200

@app.route("/topics/<int:topic_id>/cards", methods=["GET"])
def get_topic_cards(topic_id):
    """
    Get all cards for a specific topic.
    Optional: ?type=summary to filter by card_type.
    """
    topic = Topic.query.get(topic_id)
    if topic is None:
        return jsonify({"error": "Topic not found"}), 404

    card_type = request.args.get("type")

    query = Card.query.filter_by(topic_id=topic_id)

    if card_type:
        if card_type not in VALID_CARD_TYPES:
            return jsonify({
                "error": "Invalid card_type",
                "allowed_types": list(VALID_CARD_TYPES),
            }), 400
        query = query.filter_by(card_type=card_type)

    cards = query.all()
    return jsonify([c.to_dict() for c in cards]), 200

# --------------------------------------------------------------------------
# Cards endpoints (global)
# --------------------------------------------------------------------------

@app.route("/cards", methods=["GET"])
def get_cards():
    """
    Get all cards globally.
    Optional: ?type=summary to filter by card_type.
    """
    card_type = request.args.get("type")

    query = Card.query
    if card_type:
        if card_type not in VALID_CARD_TYPES:
            return jsonify({
                "error": "Invalid card_type",
                "allowed_types": list(VALID_CARD_TYPES),
            }), 400
        query = query.filter_by(card_type=card_type)

    cards = query.all()
    return jsonify([c.to_dict() for c in cards]), 200


@app.route("/cards/<int:card_id>", methods=["PUT"])
def update_card(card_id):
    """
    Update an existing card (card_type and/or content).
    """
    card = Card.query.get(card_id)
    if card is None:
        return jsonify({"error": "Card not found"}), 404

    data = request.get_json(silent=True) or {}

    new_card_type = data.get("card_type")
    new_content = data.get("content")

    if new_card_type is not None:
        if new_card_type not in VALID_CARD_TYPES:
            return jsonify({
                "error": "Invalid card_type",
                "allowed_types": list(VALID_CARD_TYPES),
            }), 400
        card.card_type = new_card_type

    if new_content is not None:
        card.content = new_content

    db.session.commit()

    return jsonify(card.to_dict()), 200


@app.route("/cards/<int:card_id>", methods=["DELETE"])
def delete_card(card_id):
    """
    Delete a card by ID.
    """
    card = Card.query.get(card_id)
    if card is None:
        return jsonify({"error": "Card not found"}), 404

    db.session.delete(card)
    db.session.commit()

    return jsonify({"status": "deleted", "id": card_id}), 200

# --------------------------------------------------------------------------
# App entrypoint
# --------------------------------------------------------------------------

if __name__ == "__main__":
    # Create the SQLite tables if they don't exist yet
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
