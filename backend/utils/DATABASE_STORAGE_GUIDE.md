# Database Storage Implementation Guide

This guide explains how to implement database-backed storage for VulnSphere PRIME authentication.

## Overview

The authentication system uses abstract storage interfaces (`UserStorage` and `APIKeyStorage`) that allow for easy transition from in-memory storage to database-backed implementations.

## Storage Interfaces

### UserStorage

The `UserStorage` abstract base class defines the following operations:

- `get_user(username: str)` - Retrieve user data by username
- `create_user(username: str, user_data: Dict)` - Create a new user
- `update_user(username: str, user_data: Dict)` - Update existing user data
- `delete_user(username: str)` - Delete a user
- `user_exists(username: str)` - Check if a user exists

### APIKeyStorage

The `APIKeyStorage` abstract base class defines the following operations:

- `get_api_key(api_key: str)` - Retrieve API key data
- `create_api_key(api_key: str, key_data: Dict)` - Create a new API key
- `update_api_key(api_key: str, key_data: Dict)` - Update existing API key data
- `delete_api_key(api_key: str)` - Delete an API key
- `update_last_used(api_key: str, timestamp: datetime)` - Update last used timestamp

## Implementing Database Storage

### Step 1: Create Database Models

Example using SQLAlchemy:

```python
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    
    username = Column(String, primary_key=True)
    email = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    disabled = Column(Boolean, default=False)
    scopes = Column(JSON)
    hashed_password = Column(String)

class APIKeyModel(Base):
    __tablename__ = "api_keys"
    
    api_key = Column(String, primary_key=True)
    username = Column(String)
    description = Column(String)
    created_at = Column(String)
    last_used = Column(String, nullable=True)
```

### Step 2: Implement Storage Classes

```python
from backend.utils.storage import UserStorage, APIKeyStorage
from typing import Optional, Dict, Any
from datetime import datetime

class DatabaseUserStorage(UserStorage):
    """Database-backed user storage implementation"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        user = self.db.query(UserModel).filter_by(username=username).first()
        if user:
            return {
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "disabled": user.disabled,
                "scopes": user.scopes,
                "hashed_password": user.hashed_password
            }
        return None
    
    def create_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        if self.user_exists(username):
            return False
        user = UserModel(**user_data)
        self.db.add(user)
        self.db.commit()
        return True
    
    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        user = self.db.query(UserModel).filter_by(username=username).first()
        if not user:
            return False
        for key, value in user_data.items():
            setattr(user, key, value)
        self.db.commit()
        return True
    
    def delete_user(self, username: str) -> bool:
        user = self.db.query(UserModel).filter_by(username=username).first()
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True
    
    def user_exists(self, username: str) -> bool:
        return self.db.query(UserModel).filter_by(username=username).first() is not None

class DatabaseAPIKeyStorage(APIKeyStorage):
    """Database-backed API key storage implementation"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        key = self.db.query(APIKeyModel).filter_by(api_key=api_key).first()
        if key:
            return {
                "username": key.username,
                "description": key.description,
                "created_at": key.created_at,
                "last_used": key.last_used
            }
        return None
    
    def create_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        if self.get_api_key(api_key):
            return False
        key = APIKeyModel(api_key=api_key, **key_data)
        self.db.add(key)
        self.db.commit()
        return True
    
    def update_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        key = self.db.query(APIKeyModel).filter_by(api_key=api_key).first()
        if not key:
            return False
        for k, v in key_data.items():
            setattr(key, k, v)
        self.db.commit()
        return True
    
    def delete_api_key(self, api_key: str) -> bool:
        key = self.db.query(APIKeyModel).filter_by(api_key=api_key).first()
        if not key:
            return False
        self.db.delete(key)
        self.db.commit()
        return True
    
    def update_last_used(self, api_key: str, timestamp: datetime) -> bool:
        key = self.db.query(APIKeyModel).filter_by(api_key=api_key).first()
        if not key:
            return False
        key.last_used = timestamp.isoformat()
        self.db.commit()
        return True
```

### Step 3: Update auth.py

Replace the storage initialization in `backend/utils/auth.py`:

```python
# Before (in-memory):
user_storage: UserStorage = InMemoryUserStorage(initial_users)
api_key_storage: APIKeyStorage = InMemoryAPIKeyStorage()

# After (database):
from .database_storage import DatabaseUserStorage, DatabaseAPIKeyStorage
from .database import get_db_session

db_session = get_db_session()
user_storage: UserStorage = DatabaseUserStorage(db_session)
api_key_storage: APIKeyStorage = DatabaseAPIKeyStorage(db_session)
```

### Step 4: Database Migration

Create initial users in your database:

```python
# Create admin user
from backend.utils.auth import get_password_hash

admin_data = {
    "username": "admin",
    "email": "admin@vulnsphere.local",
    "full_name": "Administrator",
    "disabled": False,
    "scopes": ["read", "write", "admin"],
    "hashed_password": get_password_hash("changeme")
}
user_storage.create_user("admin", admin_data)
```

## Using Redis for API Key Storage

For high-performance API key lookups, you might want to use Redis:

```python
import redis
from backend.utils.storage import APIKeyStorage

class RedisAPIKeyStorage(APIKeyStorage):
    """Redis-backed API key storage for high performance"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        data = self.redis.hgetall(f"apikey:{api_key}")
        if data:
            return {k.decode(): v.decode() for k, v in data.items()}
        return None
    
    def create_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        key = f"apikey:{api_key}"
        if self.redis.exists(key):
            return False
        self.redis.hmset(key, key_data)
        return True
    
    # ... implement other methods
```

## Testing Your Implementation

Create tests to ensure your database implementation works correctly:

```python
import pytest
from backend.utils.auth import get_password_hash

def test_database_user_storage(db_session):
    storage = DatabaseUserStorage(db_session)
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": get_password_hash("password"),
        "scopes": ["read"]
    }
    
    # Test create
    assert storage.create_user("testuser", user_data)
    
    # Test get
    user = storage.get_user("testuser")
    assert user["username"] == "testuser"
    
    # Test update
    user_data["email"] = "newemail@example.com"
    assert storage.update_user("testuser", user_data)
    
    # Test delete
    assert storage.delete_user("testuser")
```

## Best Practices

1. **Connection Pooling**: Use connection pooling for database connections
2. **Async Support**: Consider implementing async versions for better performance
3. **Caching**: Add a caching layer (e.g., Redis) for frequently accessed data
4. **Migrations**: Use Alembic or similar tools for database migrations
5. **Indexing**: Add indexes on frequently queried columns (username, api_key)
6. **Error Handling**: Add proper error handling and logging
7. **Transactions**: Use database transactions for data consistency

## Environment Configuration

Add database configuration to your environment:

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost/vulnsphere
REDIS_URL=redis://localhost:6379/0
```

## Security Considerations

1. **Encryption at Rest**: Ensure database encryption is enabled
2. **Connection Security**: Use SSL/TLS for database connections
3. **Access Control**: Implement proper database user permissions
4. **Secrets Management**: Never hardcode credentials; use environment variables
5. **Audit Logging**: Log all authentication-related operations
