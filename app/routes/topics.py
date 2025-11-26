
# app/routes/topics.py

from flask import Blueprint, jsonify, request
from ..models import Topic, Card
from ..services.content_generator import generate_dummy_content
from ..constants import VALID_CARD_TYPES
from .. import db

topics_bp = Blueprint("topics", __name__)


@topics_bp.route("/topics", methods=["GET"])
def list_topics():
    topics = Topic.query.all()
    data = [t.to_dict() for t in topics]
    return jsonify(data), 200


@topics_bp.route("/topics", methods=["POST"])
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


@topics_bp.route("/topics/<int:topic_id>/cards", methods=["GET"])
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
