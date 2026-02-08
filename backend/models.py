import uuid
from datetime import datetime
from mongoengine import (
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    StringField,
    FloatField,
    IntField,
    DateTimeField,
    ListField,
    DictField
)


# -----------------------------
# GeoJSON Point
# -----------------------------
class GeoJSONPoint(EmbeddedDocument):
    type = StringField(required=True, choices=["Point"], default="Point")
    coordinates = ListField(FloatField(), required=True, min_length=2, max_length=2)


# -----------------------------
# On-chain Solana Data
# -----------------------------
class OnChainData(EmbeddedDocument):
    account_address = StringField()
    raw_data = DictField()


# -----------------------------
# PlaceSummary (embedded for Place)
# -----------------------------
class PlaceSummary(EmbeddedDocument):
    id = StringField()  # MongoDB _id stored as string
    transaction_id = StringField(required=True, unique=True, sparse=True)
    name = StringField(required=True)
    location = EmbeddedDocumentField(GeoJSONPoint, required=True)
    place_type = StringField(required=True, choices=["current", "historical"])
    category = StringField(required=True)
    safety_score = FloatField(default=0)   # 0-100 scale
    upvote_count = IntField(default=0)
    distance_meters = FloatField(default=0) # optional for queries
    status = StringField(choices=["pending", "approved", "rejected"], default="pending")
    created_at = DateTimeField(default=datetime.utcnow)


# -----------------------------
# PlaceDetail (extends PlaceSummary)
# -----------------------------
class PlaceDetail(EmbeddedDocument):
    description = StringField()
    era = StringField()
    photos = ListField(StringField(), max_length=5)
    address = StringField()
    additional_info = DictField()
    on_chain_data = EmbeddedDocumentField(OnChainData)
    indexed_at = DateTimeField()


# -----------------------------
# Full Place Model
# -----------------------------
class Place(Document):
    # Core fields
    name = StringField(required=True, max_length=200)
    location = EmbeddedDocumentField(GeoJSONPoint, required=True)
    place_type = StringField(required=True, choices=["current", "historical"])
    category = StringField(required=True, choices=[
        "bar", "cafe", "library", "community_center", "bookstore",
        "park", "art_space", "other"
    ])
    
    # Optional/Detail fields
    description = StringField(max_length=2000)
    era = StringField()
    photos = ListField(StringField(), max_length=5)
    address = StringField()
    additional_info = DictField()
    
    # Embedded summary and detail
    summary = EmbeddedDocumentField(PlaceSummary)
    detail = EmbeddedDocumentField(PlaceDetail)
    
    meta = {
        "collection": "places",
        "indexes": [
            {"fields": ["location"], "type": "2dsphere"}  # <- THIS IS REQUIRED
        ]
    }

