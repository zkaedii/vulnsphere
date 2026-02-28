"""
JWT Authentication for VulnSphere PRIME API

Provides:
- JWT token generation and validation
- Password hashing with bcrypt
- User authentication middleware
- API key support for programmatic access
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

from .storage import UserStorage, APIKeyStorage, InMemoryUserStorage, InMemoryAPIKeyStorage

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    logger.error("JWT_SECRET environment variable is not set. JWT authentication cannot function without a stable secret key.")
    raise RuntimeError("JWT_SECRET environment variable must be set for JWT authentication.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
API_KEY_HEADER = "X-API-Key"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


# Models
class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Decoded token data"""
    username: Optional[str] = None
    scopes: list[str] = []
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: list[str] = ["read"]


class UserInDB(User):
    """User with hashed password"""
    hashed_password: str


# In-memory user store (replace with database in production)
# Storage interfaces allow easy transition to database-backed implementations
# To use a database, implement UserStorage and APIKeyStorage interfaces
# and inject them here instead of the in-memory versions
initial_users = {
    "admin": {
        "username": "admin",
        "email": "admin@vulnsphere.local",
        "full_name": "Administrator",
        "disabled": False,
        "scopes": ["read", "write", "admin"],
        "hashed_password": pwd_context.hash("changeme")  # Change in production!
    }
}

# Initialize storage backends (can be swapped with database implementations)
user_storage: UserStorage = InMemoryUserStorage(initial_users)
api_key_storage: APIKeyStorage = InMemoryAPIKeyStorage()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from storage"""
    user_dict = user_storage.get_user(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_api_key(username: str, description: str = "") -> str:
    """Create API key for programmatic access"""
    api_key = secrets.token_urlsafe(32)
    key_data = {
        "username": username,
        "description": description,
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None
    }
    api_key_storage.create_api_key(api_key, key_data)
    return api_key


def verify_api_key(api_key: str) -> Optional[str]:
    """Verify API key and return associated username"""
    key_data = api_key_storage.get_api_key(api_key)
    if key_data:
        api_key_storage.update_last_used(api_key, datetime.utcnow())
        return key_data["username"]
    return None


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    """
    Get current authenticated user from JWT token or API key.

    Supports both OAuth2 bearer tokens and API keys.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try API key first
    if api_key:
        username = verify_api_key(api_key)
        if username:
            user = get_user(username)
            if user:
                return User(**user.dict())

    # Try JWT token
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception

    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception

    return User(**user.dict())


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active (non-disabled) user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_scope(required_scope: str):
    """
    Dependency to require specific scope.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_scope("admin"))])
        async def admin_endpoint():
            ...
    """
    async def scope_checker(current_user: User = Depends(get_current_active_user)):
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required"
            )
        return current_user
    return scope_checker


# Optional: Rate limiting support
class RateLimiter:
    """Simple in-memory rate limiter with automatic cleanup of old entries"""

    def __init__(self, requests_per_minute: int = 60, cleanup_after_minutes: int = 5):
        self.requests_per_minute = requests_per_minute
        self.cleanup_after_minutes = cleanup_after_minutes
        self.requests: Dict[str, list] = {}
        self.last_access: Dict[str, datetime] = {}
        self.last_cleanup = datetime.utcnow()

    def _cleanup_old_keys(self):
        """Remove keys that haven't been accessed recently"""
        now = datetime.utcnow()
        cleanup_threshold = now - timedelta(minutes=self.cleanup_after_minutes)
        
        # Find keys to remove
        keys_to_remove = [
            key for key, last_time in self.last_access.items()
            if last_time < cleanup_threshold
        ]
        
        # Remove old keys
        for key in keys_to_remove:
            self.requests.pop(key, None)
            self.last_access.pop(key, None)
        
        self.last_cleanup = now

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Periodically cleanup old keys (every minute)
        if now - self.last_cleanup > timedelta(minutes=1):
            self._cleanup_old_keys()

        if key not in self.requests:
            self.requests[key] = []

        # Update last access time
        self.last_access[key] = now

        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > minute_ago
        ]

        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False

        # Record request
        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter(requests_per_minute=100)


async def rate_limit_check(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Check rate limit for current user"""
    if not rate_limiter.is_allowed(current_user.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return current_user
