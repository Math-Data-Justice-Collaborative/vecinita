"""
Rate Limiter Backends: Abstract base and implementations (in-memory + optional Redis).

This module provides pluggable rate limiter backends:
- InMemoryRateLimiter: Works out-of-box, single-instance only
- RedisRateLimiter: Distributed-ready, optional (if Redis available)

Auto-detection: On import, tries to connect to Redis. Falls back to in-memory if unavailable.
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class RateLimiterBackend(ABC):
    """Abstract base class for rate limiter implementations."""
    
    @abstractmethod
    async def check_and_update(
        self,
        api_key: str,
        endpoint: str,
        endpoint_limits: Dict[str, int],
    ) -> Tuple[bool, Optional[str]]:
        """
        Check rate limits and update counters.
        
        Args:
            api_key: Client API key
            endpoint: Request endpoint (e.g., "/api/v1/ask")
            endpoint_limits: {"requests_per_hour": int, "tokens_per_day": int}
            
        Returns:
            (allowed: bool, reason: str|None)
            - (True, None): Request allowed
            - (False, "reason"): Request denied with reason
        """
        pass
    
    @abstractmethod
    async def get_status(self, api_key: str) -> Dict:
        """Get current rate limit status for an API key."""
        pass


class InMemoryRateLimiter(RateLimiterBackend):
    """Single-instance rate limiter using in-memory dictionaries."""
    
    def __init__(self):
        """Initialize in-memory rate limit state."""
        self.state: Dict[str, Dict] = {}
        logger.info("Rate limiter: Using in-memory backend (single instance only)")
    
    async def check_and_update(
        self,
        api_key: str,
        endpoint: str,
        endpoint_limits: Dict[str, int],
    ) -> Tuple[bool, Optional[str]]:
        """Check rate limits in memory."""
        now = datetime.now()
        
        # Initialize state for this API key if needed
        if api_key not in self.state:
            self.state[api_key] = {
                'tokens': 0,
                'token_reset': now + timedelta(days=1),
                'endpoints': {},
            }
        
        state = self.state[api_key]
        
        # Check daily token limit
        if now >= state['token_reset']:
            state['tokens'] = 0
            state['token_reset'] = now + timedelta(days=1)
        
        if state['tokens'] >= endpoint_limits.get('tokens_per_day', 10000):
            return False, f"Daily token limit exceeded ({state['tokens']} used)"
        
        # Check hourly request limit for this endpoint
        if endpoint not in state['endpoints']:
            state['endpoints'][endpoint] = {
                'requests': 0,
                'reset': now + timedelta(hours=1),
            }
        
        ep_state = state['endpoints'][endpoint]
        if now >= ep_state['reset']:
            ep_state['requests'] = 0
            ep_state['reset'] = now + timedelta(hours=1)
        
        if ep_state['requests'] >= endpoint_limits.get('requests_per_hour', 100):
            return False, f"Hourly request limit exceeded for {endpoint}"
        
        # Update counters
        state['tokens'] += 100  # Example: 100 tokens per request
        ep_state['requests'] += 1
        
        logger.debug(
            f"Rate limit OK: {api_key[:10]}... | "
            f"{ep_state['requests']}/{endpoint_limits.get('requests_per_hour', 100)} req/hr | "
            f"{state['tokens']}/{endpoint_limits.get('tokens_per_day', 10000)} tokens/day"
        )
        
        return True, None
    
    async def get_status(self, api_key: str) -> Dict:
        """Get rate limit status for API key."""
        if api_key not in self.state:
            return {'status': 'no_usage'}
        
        state = self.state[api_key]
        return {
            'status': 'active',
            'tokens_used': state['tokens'],
            'endpoint_requests': {
                ep: ep_state['requests']
                for ep, ep_state in state['endpoints'].items()
            }
        }


class RedisRateLimiter(RateLimiterBackend):
    """Distributed rate limiter using Redis backend."""
    
    def __init__(self, redis_url: str):
        """Initialize Redis rate limiter."""
        try:
            import redis
            self.redis_client = redis.from_url(redis_url)
            # Test connection
            self.redis_client.ping()
            logger.info("Rate limiter: Using Redis backend (distributed)")
        except Exception as e:
            logger.error(f"Failed to initialize Redis rate limiter: {e}")
            raise
    
    async def check_and_update(
        self,
        api_key: str,
        endpoint: str,
        endpoint_limits: Dict[str, int],
    ) -> Tuple[bool, Optional[str]]:
        """Check rate limits in Redis."""
        try:
            # Token key: api_key:tokens (unix timestamp of reset)
            token_key = f"rl:tokens:{api_key}"
            token_count_key = f"rl:tokens_count:{api_key}"
            
            now_ts = datetime.now().timestamp()
            
            # Check daily token limit
            reset_ts = self.redis_client.get(token_key)
            if reset_ts and float(reset_ts) <= now_ts:
                self.redis_client.delete(token_count_key)
                reset_ts = None
            
            if not reset_ts:
                tomorrow_ts = int((datetime.now() + timedelta(days=1)).timestamp())
                self.redis_client.set(token_key, tomorrow_ts, ex=86400)
            
            tokens_used = int(self.redis_client.incr(token_count_key) or 0)
            if tokens_used > endpoint_limits.get('tokens_per_day', 10000):
                return False, f"Daily token limit exceeded ({tokens_used} used)"
            
            # Check hourly request limit
            ep_key = f"rl:requests:{api_key}:{endpoint}"
            ep_count = int(self.redis_client.incr(ep_key) or 0)
            
            if ep_count == 1:
                # First request this hour
                self.redis_client.expire(ep_key, 3600)
            
            if ep_count > endpoint_limits.get('requests_per_hour', 100):
                return False, f"Hourly request limit exceeded for {endpoint}"
            
            logger.debug(
                f"Rate limit OK (Redis): {api_key[:10]}... | "
                f"{ep_count}/{endpoint_limits.get('requests_per_hour', 100)} req/hr"
            )
            
            return True, None
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open if Redis is down (assume limits OK)
            logger.warning("Redis rate limiter unavailable; allowing request (fail-open)")
            return True, None
    
    async def get_status(self, api_key: str) -> Dict:
        """Get rate limit status from Redis."""
        try:
            token_count_key = f"rl:tokens_count:{api_key}"
            tokens_used = int(self.redis_client.get(token_count_key) or 0)
            
            # Scan for endpoint requests
            ep_pattern = f"rl:requests:{api_key}:*"
            ep_requests = {}
            for key in self.redis_client.scan_iter(match=ep_pattern):
                ep = key.decode().split(':')[-1]
                count = int(self.redis_client.get(key) or 0)
                ep_requests[ep] = count
            
            return {
                'status': 'active',
                'tokens_used': tokens_used,
                'endpoint_requests': ep_requests,
                'backend': 'redis'
            }
        except Exception as e:
            logger.error(f"Failed to get Redis status: {e}")
            return {'status': 'error', 'backend': 'redis'}


def create_rate_limiter() -> RateLimiterBackend:
    """
    Factory: Auto-detect and create appropriate rate limiter.
    
    Priority:
    1. If REDIS_URL env var set and Redis available: RedisRateLimiter
    2. Otherwise: InMemoryRateLimiter (with warning if multi-instance detected)
    
    Returns:
        RateLimiterBackend instance
    """
    redis_url = os.getenv("REDIS_URL")
    
    if redis_url:
        try:
            limiter = RedisRateLimiter(redis_url)
            return limiter
        except Exception as e:
            logger.warning(
                f"Redis rate limiter failed to initialize: {e}\n"
                f"Falling back to in-memory rate limiter (single-instance only).  "
                f"For distributed deployments, verify REDIS_URL is correct."
            )
    
    # Default to in-memory
    limiter = InMemoryRateLimiter()
    
    # Warn if this looks like a multi-instance deployment
    if os.getenv("DEPLOYMENT_INSTANCE_COUNT") or os.getenv("KUBERNETES_SERVICE_HOST"):
        logger.warning(
            "⚠️  Multi-instance deployment detected but using in-memory rate limiter.\n"
            "    Rate limits will not be shared across instances.\n"
            "    Set REDIS_URL environment variable to enable distributed rate limiting."
        )
    
    return limiter
