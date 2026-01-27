"""
Tests for core utilities.
"""
import pytest
from django.core.cache import cache
from apps.core.utils import cache_key, get_or_set_cache, generate_random_string


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_generate_random_string(self):
        """Test random string generation."""
        result = generate_random_string(10)
        assert len(result) == 10
        assert result.isalnum()
        
        # Test different lengths
        assert len(generate_random_string(5)) == 5
        assert len(generate_random_string(20)) == 20
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        key = cache_key('user', 123)
        assert key == 'user:123'
        
        key = cache_key('post', user_id=456, post_id=789)
        assert 'post:' in key
        assert 'post_id_789' in key
        assert 'user_id_456' in key
    
    @pytest.mark.django_db
    def test_get_or_set_cache(self):
        """Test get or set cache functionality."""
        cache.clear()
        
        call_count = 0
        
        def expensive_operation():
            nonlocal call_count
            call_count += 1
            return 'result'
        
        # First call should execute function
        result1 = get_or_set_cache('test_key', expensive_operation, timeout=60)
        assert result1 == 'result'
        assert call_count == 1
        
        # Second call should get from cache
        result2 = get_or_set_cache('test_key', expensive_operation, timeout=60)
        assert result2 == 'result'
        assert call_count == 1  # Function not called again
