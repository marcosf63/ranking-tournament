
"""
Sistema de cache com Redis para otimização de performance
"""
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import logging
import hashlib
import uuid

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from .config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Serviço de cache com Redis (fallback para memória)"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.default_ttl = 300  # 5 minutos
        self._initialize_redis()
    
    def _initialize_redis(self):
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not found, using memory cache fallback.")
            return
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            logger.info("Redis cache connection configured.")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using memory cache fallback.")
            self.redis_client = None

    def _generate_key(self, key: str, prefix: str = "ranking_cache") -> str:
        return f"{prefix}:{key}"

    def _serialize(self, value: Any) -> str:
        return json.dumps(value, default=str)

    def _deserialize(self, value: str) -> Any:
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        serialized_value = self._serialize(value)

        if self.redis_client:
            await self.redis_client.setex(cache_key, ttl, serialized_value)
        else:
            self.memory_cache[cache_key] = {
                'value': serialized_value,
                'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
            }

    async def get(self, key: str) -> Optional[Any]:
        cache_key = self._generate_key(key)
        if self.redis_client:
            value = await self.redis_client.get(cache_key)
            return self._deserialize(value) if value else None
        else:
            item = self.memory_cache.get(cache_key)
            if item and item['expires_at'] > datetime.utcnow():
                return self._deserialize(item['value'])
            elif item:
                del self.memory_cache[cache_key]
        return None

    async def delete(self, key: str):
        cache_key = self._generate_key(key)
        if self.redis_client:
            await self.redis_client.delete(cache_key)
        elif cache_key in self.memory_cache:
            del self.memory_cache[cache_key]

    async def add_to_blacklist(self, jti: str, ttl: int):
        """Adiciona um JTI de token à blacklist com um TTL."""
        key = self._generate_key(jti, prefix="blacklist")
        await self.set(key, "blacklisted", ttl=ttl)

    async def is_in_blacklist(self, jti: str) -> bool:
        """Verifica se um JTI de token está na blacklist."""
        key = self._generate_key(jti, prefix="blacklist")
        return await self.get(key) is not None


class RankingCacheManager:
    def __init__(self, cache: CacheService):
        self.cache = cache

    async def get_general_ranking(self, page: int, size: int) -> Optional[Dict]:
        key = f"general_ranking:{page}:{size}"
        return await self.cache.get(key)

    async def set_general_ranking(self, data: Dict, page: int, size: int, ttl: int = 300):
        key = f"general_ranking:{page}:{size}"
        await self.cache.set(key, data, ttl)

    async def get_tournament_ranking(self, tournament_id: int, page: int, size: int) -> Optional[Dict]:
        key = f"tournament_ranking:{tournament_id}:{page}:{size}"
        return await self.cache.get(key)

    async def set_tournament_ranking(self, tournament_id: int, data: Dict, page: int, size: int, ttl: int = 600):
        key = f"tournament_ranking:{tournament_id}:{page}:{size}"
        await self.cache.set(key, data, ttl)

    async def get_player_stats(self, player_id: int) -> Optional[Dict]:
        key = f"player_stats:{player_id}"
        return await self.cache.get(key)

    async def set_player_stats(self, player_id: int, data: Dict, ttl: int = 300):
        key = f"player_stats:{player_id}"
        await self.cache.set(key, data, ttl)

    async def invalidate_all_rankings(self):
        # Esta é uma operação complexa e cara, especialmente sem Redis.
        # Para simplificar, a invalidação pode ser feita pela expiração natural (TTL baixo)
        # ou por uma estratégia mais direcionada ao atualizar dados.
        logger.warning("invalidate_all_rankings is a complex operation and should be used with care.")


cache_service = CacheService()
RankingCache = RankingCacheManager(cache_service)
