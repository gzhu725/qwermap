from flask import Blueprint, request, jsonify
from models import Place
from utils.errors import error_response


bp = Blueprint("safety", __name__)


def compute_region_score(place_count, total_upvotes):
    return min(100.0, (place_count * 5.0) + (total_upvotes * 2.0))


@bp.get("/safety-scores/heatmap")
def get_safety_heatmap():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return error_response("lat and lon required", code="INVALID_COORDS")

    radius = int(request.args.get("radius", 50000))

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lon, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius,
                "spherical": True,
                "query": {"status": "approved"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "lon": {"$arrayElemAt": ["$location.coordinates", 0]},
                "lat": {"$arrayElemAt": ["$location.coordinates", 1]},
                "safety_score": 1,
            }
        },
    ]

    results = list(Place.objects.aggregate(*pipeline))
    heatmap = [[r["lon"], r["lat"], r.get("safety_score", 0)] for r in results]
    return jsonify(heatmap)


@bp.get("/safety-scores")
def get_safety_scores():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return error_response("lat and lon required", code="INVALID_COORDS")

    radius = int(request.args.get("radius", 50000))

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lon, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius,
                "spherical": True,
            }
        },
        {
            "$group": {
                "_id": None,
                "place_count": {"$sum": 1},
                "total_upvotes": {"$sum": "$upvote_count"},
            }
        },
    ]

    result = list(Place.objects.aggregate(*pipeline))
    if not result:
        place_count = 0
        total_upvotes = 0
    else:
        place_count = result[0].get("place_count", 0)
        total_upvotes = result[0].get("total_upvotes", 0)

    return jsonify(
        {
            "location": {"lat": lat, "lon": lon},
            "radius_meters": radius,
            "safety_score": compute_region_score(place_count, total_upvotes),
            "place_count": place_count,
            "total_upvotes": total_upvotes,
        }
    )
