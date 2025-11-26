
# app/routes/cards.py

from flask import Blueprint, jsonify, request
from ..models import Card
from ..constants import VALID_CARD_TYPES
from .. import db

cards_bp = Blueprint("cards", __name__)


@cards_bp.route("/cards", methods=["GET"])
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


@cards_bp.route("/cards/<int:card_id>", methods=["PUT"])
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


@cards_bp.route("/cards/<int:card_id>", methods=["DELETE"])
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
