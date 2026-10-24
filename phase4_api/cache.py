"""In-memory recommendation response cache with TTL and capacity bounds."""

import json
import time
import hashlib
from typing import Dict, Any, Optional


class RecommendationCache:
    """
    In-memory cache keyed by hash of profile JSON (includes language),
    max 200 entries, 1-hour expiry.
    """
    def __init__(self, max_size: int = 200, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}

    def compute_key(self, profile_dict: Dict[str, Any]) -> str:
        """Hash canonical JSON of profile dictionary including language."""
        serialized = json.dumps(profile_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve entry if present and not expired."""
        entry = self._store.get(key)
        if not entry:
            return None

        # Expired check
        if time.time() - entry["timestamp"] > self.ttl:
            del self._store[key]
            return None

        return entry["data"]

    def set(self, key: str, data: Dict[str, Any]):
        """Store response data if cache conditions met."""
        now = time.time()

        # Evict expired entries
        expired_keys = [k for k, v in self._store.items() if now - v["timestamp"] > self.ttl]
        for k in expired_keys:
            del self._store[k]

        # Evict oldest entry if still exceeding max_size
        if len(self._store) >= self.max_size:
            oldest_key = min(self._store.keys(), key=lambda k: self._store[k]["timestamp"])
            del self._store[oldest_key]

        self._store[key] = {"data": data, "timestamp": now}

    def clear(self):
        """Clear all cached entries."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
