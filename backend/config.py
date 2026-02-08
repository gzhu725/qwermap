import os


class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "qwermapdb")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    SOLANA_KEYPAIR_PATH = os.getenv("SOLANA_KEYPAIR_PATH")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    RATE_LIMIT_SUBMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_SUBMIT_PER_HOUR", "5"))
    RATE_LIMIT_UPVOTE_PER_HOUR = int(os.getenv("RATE_LIMIT_UPVOTE_PER_HOUR", "10"))
    RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "3600"))
