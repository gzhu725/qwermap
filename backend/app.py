from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

# Global Vars

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"]) # ?


MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["qwermapdb"]          # your database name
collection = db["places"]     # your collection name


# get list of places near a location
@app.route("/places", methods=["GET"])
def get_places():
    # get required params
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
    except (TypeError, ValueError):
        return jsonify({"error": "Lat and lon are required and must be valid numbers"}), 400

    # get optional params
    radius = int(request.args.get("radius", 5000)) / 6378137  # convert meters to radians for $geoWithin??
    place_type = request.args.get("type", "all") # current, historical, all
    category = request.args.get("category") # enum: [bar, cafe, library, community_center, bookstore, park, art_space, other]
    status = request.args.get("status") # enum: [pending, approved, rejected]
    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))

    # build mongo query
    query = {
        "location": {
            "$geoWithin": {
                "$centerSphere": [[lon, lat], radius]
            }
        }
    }

    if place_type in ("current", "historical"):
        query["place_type"] = place_type
    if category:
        query["category"] = category
    if status:
        query["status"] = status

    # use query 
    places_cursor = places_collection.find(query).skip(offset).limit(limit).sort("created_at", ASCENDING)
    total_count = places_collection.count_documents(query)

    # create response
    places = []
    for place in places_cursor:
        places.append({
            "id": str(place["_id"]),
            "transaction_id": place.get("transaction_id"),
            "name": place.get("name"),
            "location": place.get("location"),
            "place_type": place.get("place_type"),
            "category": place.get("category"),
            "safety_score": place.get("safety_score", 0),
            "upvote_count": place.get("upvote_count", 0),
            "distance_meters": None,  # optional: can compute later
            "status": place.get("status", "pending"),
            "created_at": place.get("created_at").isoformat() if place.get("created_at") else None
        })

    return jsonify({
        "places": places,
        "total": total_count,
        "offset": offset,
        "limit": limit
    })



if __name__ == "__main__":
    app.run(debug=True, port=8000)