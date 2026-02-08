import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone
from bson import ObjectId
import os

# TODO: INTEGRATE SOLANA?
# Global Vars

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"]) # ?


MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["qwermapdb"]          # your database name
places_collection = db["places"]     # your collection name


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

    query = {
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius
            }
        }
    }

    if place_type:
        query["place_type"] = place_type
    if category:
        query["category"] = category
    if status:
        query["status"] = status

    cursor = places_collection.find(query).skip(offset).limit(limit)
    total = places_collection.count_documents(query)

    places = []
    for p in cursor:
        places.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "location": p["location"],
            "place_type": p["place_type"],
            "category": p["category"],
            "status": p.get("status", "pending"),
            "created_at": p.get("created_at").isoformat() if p.get("created_at") else None
        })

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

    place_doc = {
        "transaction_id": fake_tx_id,
        "name": data["name"],
        "description": data.get("description"),
        "location": data["location"],  # GeoJSON
        "place_type": data["place_type"],
        "category": data["category"],
        "era": data.get("era"),
        "address": data.get("address"),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "upvote_count": 0,
        "safety_score": 0
    }

    result = places_collection.insert_one(place_doc)
    place_id = str(result.inserted_id)

    return jsonify({
        "transaction_id": fake_tx_id,
        "place_id": place_id,
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
    



if __name__ == "__main__":
    app.run(debug=True, port=8000)
