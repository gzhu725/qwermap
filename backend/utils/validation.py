ALLOWED_PLACE_TYPES = {"current", "historical", "all"}
ALLOWED_CATEGORIES = {
    "bar",
    "cafe",
    "library",
    "community_center",
    "bookstore",
    "park",
    "art_space",
    "other",
}
ALLOWED_STATUS = {"pending", "approved", "rejected"}

ALLOWED_MOVEMENTS = {
    "stonewall", "aids_activism", "marriage_equality", "trans_rights",
    "gay_liberation", "homophile_movement", "dont_ask_dont_tell",
    "pride", "drag_culture", "ballroom_culture", "other",
}

ALLOWED_COMMUNITY_TAGS = {
    "lesbian", "gay", "bisexual", "trans", "queer", "nonbinary",
    "intersex", "two_spirit", "bipoc_queer", "youth", "elders",
    "leather", "bear", "drag", "other",
}

ALLOWED_SITE_TYPES = {
    "bar", "nightclub", "bathhouse", "bookstore", "community_center",
    "health_clinic", "protest_site", "memorial", "residence",
    "religious_space", "cafe", "park", "art_space", "library",
    "theater", "archive", "shelter", "other",
}

ALLOWED_SIGNIFICANCE = {"local", "regional", "national", "international"}
ALLOWED_STILL_EXISTS = {"yes", "no", "partial", "unknown"}


def validate_geojson_point(location):
    if not isinstance(location, dict):
        return False, "location must be an object"
    if location.get("type") != "Point":
        return False, "location.type must be Point"
    coords = location.get("coordinates")
    if not isinstance(coords, list) or len(coords) != 2:
        return False, "location.coordinates must be [lon, lat]"
    lon, lat = coords
    try:
        lon = float(lon)
        lat = float(lat)
    except (TypeError, ValueError):
        return False, "location.coordinates must be numbers"
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return False, "location.coordinates out of range"
    return True, None


def validate_enum(value, allowed, field_name):
    if value is None:
        return True, None
    if value not in allowed:
        return False, f"{field_name} must be one of {sorted(allowed)}"
    return True, None
