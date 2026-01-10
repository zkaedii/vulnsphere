"""
Tests for the RateLimiter class to ensure proper cleanup of old entries
"""
import time
from datetime import datetime, timedelta
from backend.utils.auth import RateLimiter


def test_rate_limiter_basic_functionality():
    """Test basic rate limiting functionality"""
    limiter = RateLimiter(requests_per_minute=5)
    
    # Should allow 5 requests
    for i in range(5):
        assert limiter.is_allowed("user1"), f"Request {i+1} should be allowed"
    
    # 6th request should be blocked
    assert not limiter.is_allowed("user1"), "6th request should be blocked"


def test_rate_limiter_different_keys():
    """Test that different keys are tracked separately"""
    limiter = RateLimiter(requests_per_minute=3)
    
    # Each user should have their own limit
    assert limiter.is_allowed("user1")
    assert limiter.is_allowed("user2")
    assert limiter.is_allowed("user1")
    assert limiter.is_allowed("user2")
    assert limiter.is_allowed("user1")
    assert limiter.is_allowed("user2")
    
    # Both should be at limit now
    assert not limiter.is_allowed("user1")
    assert not limiter.is_allowed("user2")


def test_rate_limiter_cleanup_mechanism():
    """Test that old keys are cleaned up to prevent memory growth"""
    # Use short cleanup period for testing (1 minute)
    limiter = RateLimiter(requests_per_minute=10, cleanup_after_minutes=1)
    
    # Create entries for multiple keys
    for i in range(10):
        limiter.is_allowed(f"user{i}")
    
    # Verify all keys are tracked
    assert len(limiter.requests) == 10
    assert len(limiter.last_access) == 10
    
    # Simulate time passing by manually adjusting last_access times
    # Make some keys old (older than cleanup threshold)
    now = datetime.utcnow()
    old_time = now - timedelta(minutes=2)
    
    for i in range(5):
        limiter.last_access[f"user{i}"] = old_time
    
    # Also update last_cleanup to trigger cleanup on next call
    limiter.last_cleanup = now - timedelta(minutes=2)
    
    # Access a new key, which should trigger cleanup
    limiter.is_allowed("new_user")
    
    # Old keys should be removed (user0-user4), recent keys kept (user5-user9 + new_user)
    assert len(limiter.requests) == 6, f"Expected 6 keys, got {len(limiter.requests)}"
    assert len(limiter.last_access) == 6
    
    # Verify the correct keys remain
    for i in range(5):
        assert f"user{i}" not in limiter.requests
        assert f"user{i}" not in limiter.last_access
    
    for i in range(5, 10):
        assert f"user{i}" in limiter.requests
        assert f"user{i}" in limiter.last_access
    
    assert "new_user" in limiter.requests
    assert "new_user" in limiter.last_access


def test_rate_limiter_cleanup_timing():
    """Test that cleanup only runs periodically"""
    limiter = RateLimiter(requests_per_minute=10, cleanup_after_minutes=5)
    
    # Make an initial request
    limiter.is_allowed("user1")
    initial_cleanup_time = limiter.last_cleanup
    
    # Make another request immediately - should not trigger cleanup
    limiter.is_allowed("user2")
    assert limiter.last_cleanup == initial_cleanup_time
    
    # Simulate time passing by adjusting last_cleanup
    limiter.last_cleanup = datetime.utcnow() - timedelta(minutes=2)
    old_cleanup_time = limiter.last_cleanup
    
    # Next request should trigger cleanup
    limiter.is_allowed("user3")
    assert limiter.last_cleanup > old_cleanup_time


def test_rate_limiter_no_memory_leak():
    """Test that memory doesn't grow indefinitely with many different keys"""
    limiter = RateLimiter(requests_per_minute=100, cleanup_after_minutes=1)
    
    # Simulate many users accessing the system
    for i in range(100):
        limiter.is_allowed(f"user{i}")
    
    initial_size = len(limiter.requests)
    assert initial_size == 100
    
    # Simulate time passing
    limiter.last_cleanup = datetime.utcnow() - timedelta(minutes=2)
    
    # Make all existing keys old
    old_time = datetime.utcnow() - timedelta(minutes=2)
    for key in list(limiter.last_access.keys()):
        limiter.last_access[key] = old_time
    
    # Access new users, triggering cleanup
    for i in range(100, 110):
        limiter.is_allowed(f"user{i}")
    
    # Old keys should be cleaned up
    final_size = len(limiter.requests)
    assert final_size < initial_size + 10, f"Memory should be cleaned up, but got {final_size} keys"
    assert final_size <= 10, f"Should only have recent keys, got {final_size}"


def test_rate_limiter_last_access_tracking():
    """Test that last access time is properly updated"""
    limiter = RateLimiter(requests_per_minute=10)
    
    # First access
    limiter.is_allowed("user1")
    first_access = limiter.last_access["user1"]
    
    # Wait a tiny bit
    time.sleep(0.01)
    
    # Second access
    limiter.is_allowed("user1")
    second_access = limiter.last_access["user1"]
    
    # Last access time should be updated
    assert second_access > first_access
