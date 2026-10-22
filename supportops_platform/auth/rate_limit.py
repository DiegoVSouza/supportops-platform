"""Atomic Redis fixed-window rate limiter shared by all API processes."""

import hashlib
from redis import Redis


class RedisRateLimiter:
    SCRIPT = """local n=redis.call('INCR',KEYS[1]);
if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end;
return n"""

    def __init__(self, url, namespace="p05:rate"):
        self.client = Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        self.namespace = namespace

    def allow(self, identity, limit):
        if limit < 1: raise ValueError("rate limit must be positive")
        key = self.namespace + ":" + hashlib.sha256(identity.encode()).hexdigest()
        return self.client.eval(self.SCRIPT, 1, key, 60) <= limit
