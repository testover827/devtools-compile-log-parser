import os
import tempfile
from src.regex_cache import RegexCache, get_compiled, cache_stats

def test_basic_compile_and_reuse():
    c = RegexCache(max_size=10)
    p1 = c.get(r"^foo")
    p2 = c.get(r"^foo")
    assert p1 is p2
    assert len(c) == 1

def test_eviction_lru():
    c = RegexCache(max_size=3)
    patterns = [f"pat{i}" for i in range(4)]
    objs = [c.get(p) for p in patterns]
    # max_size==3 so after 4 inserts, size should be 3
    assert len(c) == 3
    # the first inserted (pat0) should have been evicted
    # ensure pat0 is not in cache by requesting and checking object identity changes
    new_obj = c.get("pat0")
    assert new_obj is not objs[0]
