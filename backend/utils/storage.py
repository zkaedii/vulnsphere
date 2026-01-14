"""
Storage abstractions for VulnSphere PRIME authentication

Provides abstract base classes for user and API key storage,
allowing for easy transition from in-memory to database implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class UserStorage(ABC):
    """Abstract base class for user storage operations"""

    @abstractmethod
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user data by username.
        
        Args:
            username: The username to look up
            
        Returns:
            Dictionary containing user data if found, None otherwise
        """
        pass

    @abstractmethod
    def create_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """
        Create a new user.
        
        Args:
            username: The username for the new user
            user_data: Dictionary containing user information
            
        Returns:
            True if user was created successfully, False otherwise
        """
        pass

    @abstractmethod
    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """
        Update existing user data.
        
        Args:
            username: The username to update
            user_data: Dictionary containing updated user information
            
        Returns:
            True if user was updated successfully, False otherwise
        """
        pass

    @abstractmethod
    def delete_user(self, username: str) -> bool:
        """
        Delete a user.
        
        Args:
            username: The username to delete
            
        Returns:
            True if user was deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists.
        
        Args:
            username: The username to check
            
        Returns:
            True if user exists, False otherwise
        """
        pass


class APIKeyStorage(ABC):
    """Abstract base class for API key storage operations"""

    @abstractmethod
    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve API key data.
        
        Args:
            api_key: The API key to look up
            
        Returns:
            Dictionary containing API key data if found, None otherwise
        """
        pass

    @abstractmethod
    def create_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        """
        Create a new API key.
        
        Args:
            api_key: The API key string
            key_data: Dictionary containing API key metadata
            
        Returns:
            True if key was created successfully, False otherwise
        """
        pass

    @abstractmethod
    def update_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        """
        Update existing API key data.
        
        Args:
            api_key: The API key to update
            key_data: Dictionary containing updated API key information
            
        Returns:
            True if key was updated successfully, False otherwise
        """
        pass

    @abstractmethod
    def delete_api_key(self, api_key: str) -> bool:
        """
        Delete an API key.
        
        Args:
            api_key: The API key to delete
            
        Returns:
            True if key was deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def update_last_used(self, api_key: str, timestamp: datetime) -> bool:
        """
        Update the last used timestamp for an API key.
        
        Args:
            api_key: The API key to update
            timestamp: The timestamp when the key was last used
            
        Returns:
            True if timestamp was updated successfully, False otherwise
        """
        pass


class InMemoryUserStorage(UserStorage):
    """In-memory implementation of user storage (for development/testing)"""

    def __init__(self, initial_users: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize in-memory user storage.
        
        Args:
            initial_users: Optional dictionary of initial users
        """
        self._users: Dict[str, Dict[str, Any]] = initial_users or {}

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user data by username"""
        return self._users.get(username)

    def create_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Create a new user"""
        if username in self._users:
            return False
        self._users[username] = user_data
        return True

    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Update existing user data"""
        if username not in self._users:
            return False
        self._users[username] = user_data
        return True

    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        if username not in self._users:
            return False
        del self._users[username]
        return True

    def user_exists(self, username: str) -> bool:
        """Check if a user exists"""
        return username in self._users


class InMemoryAPIKeyStorage(APIKeyStorage):
    """In-memory implementation of API key storage (for development/testing)"""

    def __init__(self):
        """Initialize in-memory API key storage"""
        self._keys: Dict[str, Dict[str, Any]] = {}

    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve API key data"""
        return self._keys.get(api_key)

    def create_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        """Create a new API key"""
        if api_key in self._keys:
            return False
        self._keys[api_key] = key_data
        return True

    def update_api_key(self, api_key: str, key_data: Dict[str, Any]) -> bool:
        """Update existing API key data"""
        if api_key not in self._keys:
            return False
        self._keys[api_key] = key_data
        return True

    def delete_api_key(self, api_key: str) -> bool:
        """Delete an API key"""
        if api_key not in self._keys:
            return False
        del self._keys[api_key]
        return True

    def update_last_used(self, api_key: str, timestamp: datetime) -> bool:
        """Update the last used timestamp for an API key"""
        if api_key not in self._keys:
            return False
        self._keys[api_key]["last_used"] = timestamp.isoformat()
        return True
