"""
Authentication Storage Abstraction Layer

Provides abstract interfaces and implementations for user and API key storage.
This allows switching between in-memory storage (for development) and
database-backed storage (for production) without changing application code.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class UserStorage(ABC):
    """Abstract interface for user storage"""

    @abstractmethod
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username. Returns user dict or None if not found."""
        pass

    @abstractmethod
    def create_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Create a new user. Returns True on success, False if user exists."""
        pass

    @abstractmethod
    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Update existing user. Returns True on success, False if not found."""
        pass

    @abstractmethod
    def delete_user(self, username: str) -> bool:
        """Delete a user. Returns True on success, False if not found."""
        pass

    @abstractmethod
    def list_users(self) -> list[str]:
        """List all usernames."""
        pass


class APIKeyStorage(ABC):
    """Abstract interface for API key storage"""

    @abstractmethod
    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key metadata. Returns dict or None if not found."""
        pass

    @abstractmethod
    def create_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        """Store a new API key. Returns True on success, False if key exists."""
        pass

    @abstractmethod
    def delete_api_key(self, api_key: str) -> bool:
        """Delete an API key. Returns True on success, False if not found."""
        pass

    @abstractmethod
    def update_last_used(self, api_key: str, timestamp: str) -> bool:
        """Update the last_used timestamp for an API key."""
        pass

    @abstractmethod
    def list_keys_for_user(self, username: str) -> list[str]:
        """List all API keys for a given username."""
        pass


class InMemoryUserStorage(UserStorage):
    """In-memory implementation of UserStorage (for development/testing)"""

    def __init__(self, initial_data: Optional[Dict[str, Dict[str, Any]]] = None):
        self._users: Dict[str, Dict[str, Any]] = initial_data or {}

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        return self._users.get(username)

    def create_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        if username in self._users:
            return False
        self._users[username] = user_data
        return True

    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        if username not in self._users:
            return False
        self._users[username] = user_data
        return True

    def delete_user(self, username: str) -> bool:
        if username not in self._users:
            return False
        del self._users[username]
        return True

    def list_users(self) -> list[str]:
        return list(self._users.keys())


class InMemoryAPIKeyStorage(APIKeyStorage):
    """In-memory implementation of APIKeyStorage (for development/testing)"""

    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}

    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        return self._keys.get(api_key)

    def create_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        if api_key in self._keys:
            return False
        self._keys[api_key] = key_data
        return True

    def delete_api_key(self, api_key: str) -> bool:
        if api_key not in self._keys:
            return False
        del self._keys[api_key]
        return True

    def update_last_used(self, api_key: str, timestamp: str) -> bool:
        if api_key not in self._keys:
            return False
        self._keys[api_key]["last_used"] = timestamp
        return True

    def list_keys_for_user(self, username: str) -> list[str]:
        return [
            key for key, data in self._keys.items()
            if data.get("username") == username
        ]


class DatabaseUserStorage(UserStorage):
    """
    Database-backed implementation of UserStorage using SQLAlchemy.
    
    This implementation provides persistent storage for production use.
    """

    def __init__(self, db_session_factory):
        """
        Initialize with a SQLAlchemy session factory.
        
        Args:
            db_session_factory: A callable that returns a database session
        """
        self.db_session_factory = db_session_factory
        logger.info("Initialized DatabaseUserStorage")

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user from database"""
        # TODO: Implement database query
        # Example:
        # with self.db_session_factory() as session:
        #     user = session.query(UserModel).filter_by(username=username).first()
        #     if user:
        #         return user.to_dict()
        # return None
        raise NotImplementedError("Database storage requires database models and migrations")

    def create_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Create user in database"""
        raise NotImplementedError("Database storage requires database models and migrations")

    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Update user in database"""
        raise NotImplementedError("Database storage requires database models and migrations")

    def delete_user(self, username: str) -> bool:
        """Delete user from database"""
        raise NotImplementedError("Database storage requires database models and migrations")

    def list_users(self) -> list[str]:
        """List all usernames from database"""
        raise NotImplementedError("Database storage requires database models and migrations")


class DatabaseAPIKeyStorage(APIKeyStorage):
    """
    Database-backed implementation of APIKeyStorage using SQLAlchemy.
    
    This implementation provides persistent storage for production use.
    """

    def __init__(self, db_session_factory):
        """
        Initialize with a SQLAlchemy session factory.
        
        Args:
            db_session_factory: A callable that returns a database session
        """
        self.db_session_factory = db_session_factory
        logger.info("Initialized DatabaseAPIKeyStorage")

    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key from database"""
        raise NotImplementedError("Database storage requires database models and migrations")

    def create_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        """Store API key in database"""
        raise NotImplementedError("Database storage requires database models and migrations")

    def delete_api_key(self, api_key: str) -> bool:
        """Delete API key from database"""
        raise NotImplementedError("Database storage requires database models and migrations")

    def update_last_used(self, api_key: str, timestamp: str) -> bool:
        """Update last_used timestamp in database"""
        raise NotImplementedError("Database storage requires database models and migrations")

    def list_keys_for_user(self, username: str) -> list[str]:
        """List all API keys for user from database"""
        raise NotImplementedError("Database storage requires database models and migrations")
