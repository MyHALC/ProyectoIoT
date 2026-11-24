import os
from pathlib import Path

from dotenv import load_dotenv
from redis import Redis


load_dotenv(
    Path(__file__).resolve().parents[2] / ".env"
)


redis_client = Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,
    protocol=2,
    socket_connect_timeout=3
)
