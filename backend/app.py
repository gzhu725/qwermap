import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from mongoengine import connect, DoesNotExist
import os

# Import your models
from models import Place, PlaceSummary, PlaceDetail, GeoJSONPoint, OnChainData

# TODO: INTEGRATE SOLANA?
# Global Vars

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"]) # ?

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "qwermapdb")

connect(db=MONGO_DB, host=MONGO_URI)


# get list of places near a location
@app.route("/places", methods=["GET"])
def get_places():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400

    radius = int(request.args.get("radius", 5000))  # meters
    place_type = request.args.get("type")
    category = request.args.get("category")
    status = request.args.get("status")
    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))

    filters = {}
    if place_type:
        filters["place_type"] = place_type
    if category:
        filters["category"] = category
    if status:
        filters["summary.status"] = status

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lon, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius,
                "spherical": True,
                "query": filters
            }
        },
        {"$skip": offset},
        {"$limit": limit}
    ]

    places_cursor = Place.objects.aggregate(*pipeline)

    places = []
    for p in places_cursor:
        places.append({
            "id": str(p.get("_id")),
            "transaction_id": p.get("summary", {}).get("transaction_id") if p.get("summary") else None,
            "name": p.get("name"),
            "location": p.get("location"),
            "place_type": p.get("place_type"),
            "category": p.get("category"),
            "status": p.get("summary", {}).get("status") if p.get("summary") else "pending",
            "created_at": p.get("summary", {}).get("created_at").isoformat() if p.get("summary") and p.get("summary").get("created_at") else None,
            "distance_meters": p.get("distance_meters")
        })

    total = Place.objects(__raw__=filters).count()

    return jsonify({
        "places": places,
        "total": total,
        "offset": offset,
        "limit": limit
    })

# submit a new place to DB
@app.route("/places", methods=["POST"])
def submit_place():
    data = request.json

    fingerprint = request.headers.get("X-Client-Fingerprint")
    if not fingerprint:
        return jsonify({
            "error": "Bad Request",
            "message": "Missing X-Client-Fingerprint header"
        }), 400

    # make sure all required params included
    required = ["name", "location", "place_type", "category"]
    for field in required:
        if field not in data:
            return jsonify({
                "error": "Bad Request",
                "message": f"Missing required field: {field}"
            }), 400
    
    # TODO: solana logic? including fake id below also how to fake 429?

    fake_tx_id = f"DEV_TX_{uuid.uuid4().hex}"

    geo_point = GeoJSONPoint(
       type=data["location"].get("type", "Point"),
        coordinates=data["location"]["coordinates"]
    )

    summary = PlaceSummary(
        id=str(uuid.uuid4()),
        transaction_id=f"DEV_TX_{uuid.uuid4().hex}",
        name=data["name"],
        location=geo_point,
        place_type=data["place_type"],
        category=data["category"],
        status="pending",
        created_at=datetime.now(timezone.utc)
    )

    detail = PlaceDetail(
        description=data.get("description"),
        era=data.get("era"),
        photos=data.get("photos"),
        address=data.get("address"),
        additional_info=data.get("additional_info"),
        indexed_at=datetime.now(timezone.utc)
    )

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
        summary=summary,
        detail=detail
    )

    place.save()

    return jsonify({
        "transaction_id": fake_tx_id,
        "place_id": str(place.id),
        "status": "pending"
    }), 201

# get place by id (transaction or regular id?)
@app.route("/places/<place_id>", methods=["GET"])
def get_place_by_id(place_id):
    place = None
    if ObjectId.is_valid(place_id):
        # get by id 
        place = places_collection.find_one({"_id": ObjectId(place_id)})
    
    # if not found, try by transaction id (associated with solana?)
    if not place:
        place = places_collection.find_one({"transaction_id": place_id})
    
    if not place:
        return jsonify({"error": "Place not found"}), 404

    place_json = {
        "id": str(place["_id"]),
        "transaction_id": place.get("transaction_id"),
        "name": place.get("name"),
        "description": place.get("description"),
        "location": place.get("location"),
        "place_type": place.get("place_type"),
        "category": place.get("category"),
        "era": place.get("era"),
        "address": place.get("address"),
        "status": place.get("status"),
        "upvote_count": place.get("upvote_count", 0),
        "safety_score": place.get("safety_score", 0),
        "created_at": place.get("created_at").isoformat() if place.get("created_at") else None
    }

    return jsonify(place_json), 200

# upvote a place
@app.route("/places/<place_id>/upvote", methods=["POST"])
def upvote_place(place_id):
    fingerprint = request.headers.get("X-Client-Fingerprint")
    if not fingerprint:
        return jsonify({"error": "Missing Fingerprint!"}), 400
    
    place = None 

    # see "find by place" 
    if ObjectId.is_valid(place_id):
        place = places_collection.find_one({"_id": ObjectId(place_id)})
    if not place:
        place = places_collection.find_one({"transaction_id": place_id})
    if not place:
        return jsonify({"error": "Place not found"}), 404
    
    # track who already upvoted
    upvoted_by = place.get("upvoted_by", [])
    if fingerprint in upvoted_by:
        return jsonify({"error": "Already upvoted"}), 409

    # increment upvote atomically and add fingerprint to list
    updated = places_collection.find_one_and_update(
        {"_id": place["_id"]},
        {
            "$inc": {"upvote_count": 1},
            "$push": {"upvoted_by": fingerprint}
        },
        return_document=True
    )

    return jsonify({
        "transaction_id": f"DEV_TX_{uuid.uuid4().hex}",  # fake Solana tx ID
        "new_upvote_count": updated["upvote_count"],
        "new_safety_score": 0.001
    }), 200
    
# get safety scores
# TODO: How to actually calculate with solana? 
@app.route("/safety-scores", methods=["GET"])
def get_safety_scores():
    pass

# TODO: get pending submissions 
@app.route("/moderation/queue", methods=["GET"])
def get_submissions():
    pass
# TODO: get pending submissions by id
@app.route("/moderation/places/<id>", methods=["GET"])
def get_submissions_by_id(id):
    pass

if __name__ == "__main__":
    app.run(debug=True, port=8000)
