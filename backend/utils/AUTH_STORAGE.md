# Authentication Storage Layer

## Overview

The authentication system in VulnSphere PRIME uses an abstraction layer for storing users and API keys. This allows you to easily switch between different storage backends without modifying application code.

## Architecture

### Storage Interfaces

Two abstract base classes define the storage interface:

- **`UserStorage`**: Interface for user management (get, create, update, delete, list)
- **`APIKeyStorage`**: Interface for API key management (get, create, delete, update_last_used, list)

### Available Implementations

#### 1. In-Memory Storage (Development/Testing)

- **`InMemoryUserStorage`**: Stores users in a Python dictionary
- **`InMemoryAPIKeyStorage`**: Stores API keys in a Python dictionary

**Pros:**
- Fast and simple
- No external dependencies
- Perfect for development and testing

**Cons:**
- Data lost on application restart
- Not shared across multiple instances
- Not suitable for production

#### 2. Database Storage (Production)

- **`DatabaseUserStorage`**: Stores users in PostgreSQL via SQLAlchemy
- **`DatabaseAPIKeyStorage`**: Stores API keys in PostgreSQL via SQLAlchemy

**Pros:**
- Persistent storage
- Shared across instances
- Production-ready

**Cons:**
- Requires database setup
- Requires implementing database models and migrations

## Usage

### Default Configuration (Development)

By default, the system uses in-memory storage:

```python
from backend.utils.auth import user_storage, api_key_storage

# These are InMemoryUserStorage and InMemoryAPIKeyStorage by default
user = user_storage.get_user("admin")
```

### Switching to Database Storage (Production)

To use database-backed storage, you need to:

1. **Create database models** (e.g., using SQLAlchemy ORM)
2. **Implement the database storage classes** (complete the TODOs in `DatabaseUserStorage` and `DatabaseAPIKeyStorage`)
3. **Run database migrations** to create the necessary tables
4. **Configure the storage backends** at application startup

Example configuration in `backend/main.py`:

```python
from backend.utils.auth import configure_storage
from backend.utils.auth_storage import DatabaseUserStorage, DatabaseAPIKeyStorage
from backend.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configure authentication to use database storage
configure_storage(
    user_backend=DatabaseUserStorage(SessionLocal),
    api_key_backend=DatabaseAPIKeyStorage(SessionLocal)
)
```

### Implementing Database Models

Here's an example of what the SQLAlchemy models might look like:

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
    scopes = Column(JSON, default=["read"])
    hashed_password = Column(String, nullable=False)

class APIKeyModel(Base):
    __tablename__ = "api_keys"
    
    key = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    description = Column(String, default="")
    created_at = Column(DateTime, nullable=False)
    last_used = Column(DateTime, nullable=True)
```

### Creating a Custom Storage Backend

You can create your own storage implementation for other databases (MongoDB, Redis, etc.):

```python
from backend.utils.auth_storage import UserStorage, APIKeyStorage

class RedisUserStorage(UserStorage):
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def get_user(self, username: str):
        # Implement using Redis
        pass
    
    # ... implement other methods

# Use your custom storage
from backend.utils.auth import configure_storage
configure_storage(user_backend=RedisUserStorage(redis_client))
```

## Testing

The in-memory storage implementations are perfect for testing:

```python
import pytest
from backend.utils.auth_storage import InMemoryUserStorage, InMemoryAPIKeyStorage

@pytest.fixture
def user_storage():
    return InMemoryUserStorage()

def test_create_user(user_storage):
    success = user_storage.create_user("testuser", {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": "...",
    })
    assert success
    
    user = user_storage.get_user("testuser")
    assert user["email"] == "test@example.com"
```

## Migration Path

To migrate from in-memory to database storage:

1. Set up your database and create the schema
2. Implement the database storage classes (complete the TODOs)
3. Add the configuration call to your application startup
4. Test thoroughly in a staging environment
5. Deploy to production

The abstraction layer ensures that your application code doesn't need to change - only the storage backend configuration.

## Security Considerations

- Always use environment variables for database credentials
- Use connection pooling for database storage
- Implement proper error handling in storage implementations
- Consider adding retry logic for database operations
- Use transactions where appropriate to ensure data consistency
