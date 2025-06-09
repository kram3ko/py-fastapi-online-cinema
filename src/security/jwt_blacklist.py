import time
from typing import cast

import redis

from config import get_settings

settings = get_settings()

redis_client: redis.StrictRedis = redis.StrictRedis.from_url(
    settings.CELERY_BROKER_URL,
    decode_responses=True
)


def blacklist_token(jti: str, exp: int) -> None:
    """
    Add a token to the blacklist.

    Args:
        jti (str): JWT ID of the token
        exp (int): Expiration timestamp of the token
    """
    ttl = exp - int(time.time())  # Time to live for the token
    if ttl > 0:
        # Store token info in a hash
        token_key = f"jwt:blacklist:{jti}"
        redis_client.hset(token_key, mapping={
            "jti": jti,
            "exp": exp,
            "blacklisted_at": int(time.time()),
            "type": "refresh_token"
        })
        # Set expiration for the hash
        redis_client.expire(token_key, ttl)


def is_token_blacklisted(jti: str) -> bool:
    """
    Check if a token is blacklisted.

    Args:
        jti (str): JWT ID of the token to check

    Returns:
        bool: True if token is blacklisted, False otherwise
    """
    return redis_client.exists(f"jwt:blacklist:{jti}") == 1


def get_blacklisted_token_info(jti: str) -> dict[str, str] | None:
    """
    Get information about a blacklisted token.

    Args:
        jti (str): JWT ID of the token

    Returns:
        dict[str, str] | None: Token information if found, None otherwise
    """
    token_key = f"jwt:blacklist:{jti}"
    if redis_client.exists(token_key):
        return cast(dict[str, str], redis_client.hgetall(token_key))
    return None


def remove_from_blacklist(jti: str) -> None:
    """
    Remove a token from the blacklist.

    Args:
        jti (str): JWT ID of the token to remove
    """
    redis_client.delete(f"jwt:blacklist:{jti}")
