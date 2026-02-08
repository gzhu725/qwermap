import time
import redis


_redis_client = None


def init_redis(app):
    global _redis_client
    redis_url = app.config.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL is not configured")
    _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)


def get_redis():
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


def is_rate_limited(key, limit, window_sec):
    client = get_redis()
    now = int(time.time())
    window_key = f"rate:{key}:{now // window_sec}"
    pipeline = client.pipeline()
    pipeline.incr(window_key, 1)
    pipeline.expire(window_key, window_sec)
    count, _ = pipeline.execute()
    return count > limit


def check_and_set_dedupe(key, ttl_sec):
    client = get_redis()
    added = client.set(key, "1", nx=True, ex=ttl_sec)
    return added is None
