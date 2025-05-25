from pathlib import Path
from os.path import dirname, join
import os
from redis import asyncio
from typing import Union
from app.config import Settings, load_config


def get_settings() -> Settings:
    return load_config()


async def get_redis_connection() -> asyncio.Redis:
    try:
        r = asyncio.Redis(host='164.92.93.98', port=6379,
                          decode_responses=True, db=1,
                          password="your_secure_redis_password")
    except asyncio.connection.ConnectionError as err:
        raise Exception(str(err))
    return r


BASE_DIR = Path(__file__).resolve().parent.parent.parent
