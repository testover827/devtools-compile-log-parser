"""
LRU RegexCache for compiled regular expressions.
Configurable via environment variable DEVTOOLS_REGEX_CACHE_SIZE (default 5000).
Provides thread-safe access and LRU eviction using collections.OrderedDict.
"""
from collections import OrderedDict
import os
import re
import threading
from typing import Pattern

DEFAULT_MAX_SIZE = 5000

def _get_max_size() -> int:
    try:
        val = int(os.environ.get("DEVTOOLS_REGEX_CACHE_SIZE", "{}"))
    except Exception:
        val = DEFAULT_MAX_SIZE
    return max(1, val)


class RegexCache:
    """A simple thread-safe LRU cache for compiled regex patterns."""

    def __init__(self, max_size: int = None):
        self.max_size = _get_max_size() if max_size is None else int(max_size)
        self._lock = threading.RLock()
        self._cache = OrderedDict()  # pattern_str -> re.Pattern

    def get(self, pattern: str, flags: int = 0) -> Pattern:
        """Return a compiled re.Pattern for the given pattern and flags.

        The cache key is the tuple (pattern, flags) serialized as a string to
        avoid collisions between same pattern with different flags.
        """
        key = f"{flags}:{pattern}"
        with self._lock:
            if key in self._cache:
                # move to end = most recently used
                self._cache.move_to_end(key)
                return self._cache[key]
            # compile, insert
            compiled = re.compile(pattern, flags)
            self._cache[key] = compiled
            # enforce size
            while len(self._cache) > self.max_size:
                # pop least-recently-used
                self._cache.popitem(last=False)
            return compiled

    def clear(self):
        with self._lock:
            self._cache.clear()

    def __len__(self):
        with self._lock:
            return len(self._cache)


# module-level default cache
_default_cache = RegexCache()


def get_compiled(pattern: str, flags: int = 0) -> Pattern:
    """Convenience wrapper using the module-level cache."""
    return _default_cache.get(pattern, flags)


def cache_stats():
    with _default_cache._lock:
        return {"size": len(_default_cache._cache), "max_size": _default_cache.max_size}
