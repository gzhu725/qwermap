from utils.validation import validate_geojson_point, validate_enum, ALLOWED_CATEGORIES


def test_validate_geojson_point_ok():
    ok, msg = validate_geojson_point(
        {"type": "Point", "coordinates": [-118.2437, 34.0522]}
    )
    assert ok
    assert msg is None


def test_validate_geojson_point_bad():
    ok, msg = validate_geojson_point({"type": "LineString", "coordinates": [1, 2]})
    assert not ok
    assert msg


def test_validate_enum():
    ok, msg = validate_enum("bar", ALLOWED_CATEGORIES, "category")
    assert ok
    assert msg is None
