from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, request, jsonify, current_app

from models import Place, OnChainData
from services.rate_limit import is_rate_limited, check_and_set_dedupe
from services.solana_service import SolanaService, hash_payload
from utils.errors import error_response


bp = Blueprint("interactions", __name__)


def compute_place_safety_score(upvote_count):
    return min(100.0, float(upvote_count) * 2.0)


@bp.post("/places/<place_id>/upvote")
def upvote_place(place_id):
    fingerprint = request.headers.get("X-Client-Fingerprint")
    if not fingerprint:
        return error_response(
            "Missing X-Client-Fingerprint header",
            code="MISSING_FINGERPRINT",
        )

    if is_rate_limited(
        f"upvote:{fingerprint}",
        current_app.config["RATE_LIMIT_UPVOTE_PER_HOUR"],
        current_app.config["RATE_LIMIT_WINDOW_SEC"],
    ):
        return error_response(
            "Maximum upvotes per hour exceeded",
            error="Rate Limited",
            code="RATE_LIMIT_EXCEEDED",
            status=429,
        )

    dedupe_key = f"upvote:{place_id}:{fingerprint}"
    already = check_and_set_dedupe(
        dedupe_key, current_app.config["RATE_LIMIT_WINDOW_SEC"]
    )
    if already:
        return error_response(
            "Already upvoted from this fingerprint",
            error="Conflict",
            code="ALREADY_UPVOTED",
            status=409,
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

    solana = SolanaService(
        current_app.config["SOLANA_RPC_URL"],
        current_app.config["SOLANA_KEYPAIR_PATH"],
    )
    memo_hash = hash_payload(
        "upvote",
        fingerprint,
        str(place.id),
        int(datetime.now(timezone.utc).timestamp()),
    )
    tx_id = solana.send_memo(memo_hash)

    place.update(
        inc__upvote_count=1,
        set__indexed_at=datetime.now(timezone.utc),
    )
    place.reload()
    new_safety_score = compute_place_safety_score(place.upvote_count)
    place.update(set__safety_score=new_safety_score)
    place.reload()

    place.on_chain_data = place.on_chain_data or OnChainData()
    place.on_chain_data.raw_data = place.on_chain_data.raw_data or {}
    place.on_chain_data.raw_data.update({"last_upvote_tx": tx_id})
    place.save()

    return jsonify(
        {
            "transaction_id": tx_id,
            "new_upvote_count": place.upvote_count,
            "new_safety_score": place.safety_score,
        }
    )
