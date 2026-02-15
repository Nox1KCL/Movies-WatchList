import redis.asyncio as redis
from typing import Optional

redis_client: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    """Dependency для отримання Redis клієнта."""
    global redis_client
    
    if redis_client is None:
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True  # Автоматично декодує bytes → str
        )
    
    return redis_client

async def close_redis():
    """Закрити з'єднання при зупинці сервера."""
    global redis_client
    if redis_client:
        await redis_client.close()
