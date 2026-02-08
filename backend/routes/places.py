from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, request, jsonify, current_app

from models import Place, GeoJSONPoint, OnChainData
from services.rate_limit import is_rate_limited
from services.solana_service import SolanaService, hash_payload
from utils.errors import error_response
from utils.validation import (
    validate_geojson_point,
    validate_enum,
    ALLOWED_PLACE_TYPES,
    ALLOWED_CATEGORIES,
    ALLOWED_STATUS,
    ALLOWED_STILL_EXISTS,
)


bp = Blueprint("places", __name__)


def place_summary_from_doc(doc, distance_meters=None):
    return {
        "id": str(doc.id),
        "transaction_id": doc.transaction_id,
        "name": doc.name,
        "location": {
            "type": doc.location.type,
            "coordinates": doc.location.coordinates,
        },
        "place_type": doc.place_type,
        "category": doc.category,
        "safety_score": doc.safety_score,
        "upvote_count": doc.upvote_count,
        "distance_meters": distance_meters,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "movements": doc.movements or [],
        "significance": doc.significance,
        "still_exists": doc.still_exists,
    }


def place_detail_from_doc(doc):
    payload = place_summary_from_doc(doc, distance_meters=None)
    payload.update(
        {
            "description": doc.description,
            "era": doc.era,
            "photos": doc.photos,
            "address": doc.address,
            "additional_info": doc.additional_info,
            "on_chain_data": {
                "account_address": doc.on_chain_data.account_address
                if doc.on_chain_data
                else None,
                "raw_data": doc.on_chain_data.raw_data if doc.on_chain_data else None,
            },
            "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
            "events": [
                {
                    "title": e.title,
                    "date": e.date,
                    "description": e.description,
                    "source_url": e.source_url,
                }
                for e in (doc.events or [])
            ],
            "related_figures": [
                {
                    "name": f.name,
                    "role": f.role,
                    "description": f.description,
                }
                for f in (doc.related_figures or [])
            ],
            "community_tags": doc.community_tags or [],
            "site_types": doc.site_types or [],
            "year_opened": doc.year_opened,
            "year_closed": doc.year_closed,
        }
    )
    return payload


@bp.get("/places")
def get_places():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return error_response("lat and lon required", code="INVALID_COORDS")

    radius = int(request.args.get("radius", 50000))
    place_type = request.args.get("type", "all")
    category = request.args.get("category")
    status = request.args.get("status")
    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))

    ok, msg = validate_enum(place_type, ALLOWED_PLACE_TYPES, "type")
    if not ok:
        return error_response(msg, code="INVALID_TYPE")
    ok, msg = validate_enum(category, ALLOWED_CATEGORIES, "category")
    if not ok:
        return error_response(msg, code="INVALID_CATEGORY")
    ok, msg = validate_enum(status, ALLOWED_STATUS, "status")
    if not ok:
        return error_response(msg, code="INVALID_STATUS")

    query = {}
    if place_type and place_type != "all":
        query["place_type"] = place_type
    if category:
        query["category"] = category
    if status:
        query["status"] = status

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lon, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius,
                "spherical": True,
                "query": query,
            }
        },
        {"$skip": offset},
        {"$limit": limit},
    ]

    places_cursor = Place.objects.aggregate(*pipeline)
    places = []
    for p in places_cursor:
        places.append(
            {
                "id": str(p.get("_id")),
                "transaction_id": p.get("transaction_id"),
                "name": p.get("name"),
                "location": p.get("location"),
                "place_type": p.get("place_type"),
                "category": p.get("category"),
                "safety_score": p.get("safety_score", 0),
                "upvote_count": p.get("upvote_count", 0),
                "distance_meters": p.get("distance_meters"),
                "status": p.get("status", "pending"),
                "created_at": p.get("created_at").isoformat()
                if p.get("created_at")
                else None,
                "movements": p.get("movements", []),
                "significance": p.get("significance"),
                "still_exists": p.get("still_exists"),
            }
        )

    total = Place.objects(__raw__=query).count()

    return jsonify(
        {
            "places": places,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    )


@bp.post("/places")
def submit_place():
    data = request.json or {}
    fingerprint = request.headers.get("X-Client-Fingerprint")
    if not fingerprint:
        return error_response(
            "Missing X-Client-Fingerprint header",
            code="MISSING_FINGERPRINT",
        )

    if is_rate_limited(
        f"submit:{fingerprint}",
        current_app.config["RATE_LIMIT_SUBMIT_PER_HOUR"],
        current_app.config["RATE_LIMIT_WINDOW_SEC"],
    ):
        return error_response(
            "Maximum submissions per hour exceeded",
            error="Rate Limited",
            code="RATE_LIMIT_EXCEEDED",
            status=429,
        )

    required = ["name", "location", "place_type", "category"]
    for field in required:
        if field not in data:
            return error_response(
                f"Missing required field: {field}",
                code="MISSING_FIELD",
            )

    ok, msg = validate_geojson_point(data.get("location"))
    if not ok:
        return error_response(msg, code="INVALID_COORDS")
    ok, msg = validate_enum(data.get("place_type"), {"current", "historical"}, "place_type")
    if not ok:
        return error_response(msg, code="INVALID_TYPE")
    ok, msg = validate_enum(data.get("category"), ALLOWED_CATEGORIES, "category")
    if not ok:
        return error_response(msg, code="INVALID_CATEGORY")
    ok, msg = validate_enum(data.get("still_exists"), ALLOWED_STILL_EXISTS, "still_exists")
    if not ok:
        return error_response(msg, code="INVALID_STILL_EXISTS")

    geo_point = GeoJSONPoint(
        type="Point",
        coordinates=data["location"]["coordinates"],
    )

    solana = SolanaService(
        current_app.config["SOLANA_RPC_URL"],
        current_app.config["SOLANA_KEYPAIR_PATH"],
    )
    memo_hash = hash_payload(
        "submit",
        fingerprint,
        data["name"],
        geo_point.coordinates[1],
        geo_point.coordinates[0],
        int(datetime.now(timezone.utc).timestamp()),
    )
    tx_id = solana.send_memo(memo_hash)

    # Parse optional integer fields safely
    year_opened = data.get("year_opened")
    if year_opened is not None:
        try:
            year_opened = int(year_opened)
        except (TypeError, ValueError):
            year_opened = None
    year_closed = data.get("year_closed")
    if year_closed is not None:
        try:
            year_closed = int(year_closed)
        except (TypeError, ValueError):
            year_closed = None

    place = Place(
        name=data["name"],
        location=geo_point,
        place_type=data["place_type"],
        category=data["category"],
        description=data.get("description"),
        era=data.get("era"),
        photos=data.get("photos"),
        address=data.get("address"),
        additional_info=data.get("additional_info"),
        year_opened=year_opened,
        year_closed=year_closed,
        still_exists=data.get("still_exists"),
        transaction_id=tx_id,
        status="approved",
        created_at=datetime.now(timezone.utc),
        indexed_at=datetime.now(timezone.utc),
        on_chain_data=OnChainData(
            account_address=None,
            raw_data={"memo": memo_hash, "signature": tx_id},
        ),
    )
    place.save()

    return (
        jsonify(
            {
                "transaction_id": tx_id,
                "place_id": str(place.id),
                "status": place.status,
            }
        ),
        201,
    )


@bp.get("/places/<place_id>")
def get_place_by_id(place_id):
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

    return jsonify(place_detail_from_doc(place))
