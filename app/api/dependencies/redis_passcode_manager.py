import time
from typing import Union

import redis
from redis.connection import ConnectionError
from redis import asyncio
from typing import Optional
from redis import asyncio

import redis.asyncio as redis_asyncio
from datetime import timedelta


class RedisPasscodeManager:
    def __init__(self, redis_client: redis_asyncio.Redis):
        self.redis = redis_client
        self.expiry_time = 300  # 5 minutes

    async def get_user_id_by_passcode(self, passcode: str) -> Optional[int]:
        """Get user ID by passcode"""
        try:
            user_id = await self.redis.get(str(passcode))
            return int(user_id) if user_id else None
        except (ValueError, TypeError):
            return None

    async def cleanup_user_passcode(self, user_id: int):
        """Clean up user's passcode after successful login"""
        try:
            # Get the passcode associated with this user
            passcode = await self.redis.get(str(user_id))
            if passcode:
                # Delete both mappings
                pipe = self.redis.pipeline()
                await pipe.delete(str(user_id))
                await pipe.delete(passcode.decode())
                await pipe.execute()
        except Exception as e:
            print(f"Error cleaning up passcode: {e}")

    async def is_passcode_valid(self, passcode: str) -> bool:
        """Check if passcode exists and is valid"""
        return await self.redis.exists(str(passcode))


async def get_redis_connection() -> Union[asyncio.Redis, None]:
    try:
        r = asyncio.Redis(host='localhost', port=6379, decode_responses=True, db=1,
                          password="your_secure_redis_password")
    except asyncio.connection.ConnectionError as err:
        return None
    return r



