"""
Utility functions and mixins for the project.
"""
from django.core.cache import cache
from django.utils.text import slugify
import random
import string


def generate_random_string(length=10):
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def cache_key(prefix, *args, **kwargs):
    """
    Generate a cache key from prefix and arguments.
    
    Usage:
        key = cache_key('user', user_id=123)
    """
    parts = [prefix]
    parts.extend(str(arg) for arg in args)
    parts.extend(f"{k}_{v}" for k, v in sorted(kwargs.items()))
    return ':'.join(parts)


def get_or_set_cache(key, callable_func, timeout=300):
    """
    Get value from cache or set it if not exists.
    
    Args:
        key: Cache key
        callable_func: Function to call if cache miss
        timeout: Cache timeout in seconds
    
    Usage:
        data = get_or_set_cache('my_key', lambda: expensive_operation(), timeout=600)
    """
    result = cache.get(key)
    if result is None:
        result = callable_func()
        cache.set(key, result, timeout)
    return result


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    from django.db import models
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
