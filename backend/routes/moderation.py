from bson import ObjectId
from flask import Blueprint, request, jsonify

from models import Place
from utils.errors import error_response


bp = Blueprint("moderation", __name__)


@bp.get("/moderation/queue")
def get_queue():
    limit = int(request.args.get("limit", 20))
    places = Place.objects(status="pending").order_by("-created_at").limit(limit)
    payload = []
    for place in places:
        payload.append(
            {
                "id": str(place.id),
                "transaction_id": place.transaction_id,
                "name": place.name,
                "location": {
                    "type": place.location.type,
                    "coordinates": place.location.coordinates,
                },
                "place_type": place.place_type,
                "category": place.category,
                "safety_score": place.safety_score,
                "upvote_count": place.upvote_count,
                "status": place.status,
                "created_at": place.created_at.isoformat()
                if place.created_at
                else None,
                "description": place.description,
                "era": place.era,
                "photos": place.photos,
                "address": place.address,
                "additional_info": place.additional_info,
                "on_chain_data": {
                    "account_address": place.on_chain_data.account_address
                    if place.on_chain_data
                    else None,
                    "raw_data": place.on_chain_data.raw_data
                    if place.on_chain_data
                    else None,
                },
                "indexed_at": place.indexed_at.isoformat()
                if place.indexed_at
                else None,
            }
        )
    return jsonify(payload)


@bp.patch("/moderation/places/<place_id>")
def moderate_place(place_id):
    data = request.json or {}
    status = data.get("status")
    reason = data.get("reason")
    if status not in ("approved", "rejected"):
        return error_response(
            "status must be approved or rejected",
            code="INVALID_STATUS",
        )

    place = None
    if ObjectId.is_valid(place_id):
        place = Place.objects(id=place_id).first()
    if not place:
        place = Place.objects(transaction_id=place_id).first()
    if not place:
        return error_response(
            "Place with given ID does not exist",
            error="Not Found",
            code="PLACE_NOT_FOUND",
            status=404,
        )

    place.status = status
    if reason:
        place.additional_info = place.additional_info or {}
        place.additional_info["moderation_reason"] = reason
    place.save()

    return jsonify(
        {
            "id": str(place.id),
            "transaction_id": place.transaction_id,
            "name": place.name,
            "location": {
                "type": place.location.type,
                "coordinates": place.location.coordinates,
            },
            "place_type": place.place_type,
            "category": place.category,
            "safety_score": place.safety_score,
            "upvote_count": place.upvote_count,
            "status": place.status,
            "created_at": place.created_at.isoformat() if place.created_at else None,
            "description": place.description,
            "era": place.era,
            "photos": place.photos,
            "address": place.address,
            "additional_info": place.additional_info,
            "on_chain_data": {
                "account_address": place.on_chain_data.account_address
                if place.on_chain_data
                else None,
                "raw_data": place.on_chain_data.raw_data if place.on_chain_data else None,
            },
            "indexed_at": place.indexed_at.isoformat() if place.indexed_at else None,
        }
    )
