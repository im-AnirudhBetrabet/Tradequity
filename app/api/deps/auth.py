"""
Authentication dependencies for FastAPI routes.

This module provides JWT authentication validation using Supabase-issued
access tokens and JWKS-backed signature verification and in-memory key caching.

Design principles:
    - Signature verification via JWKS.
    - Cached JWKS retrieval for performance.
    - Strict issuer validation.
    - Audience validation.
    - Framework-native FastAPI dependencies.
    - Clear authentication failure semantics.
"""

import httpx
from typing              import Any
from datetime            import datetime, timedelta, timezone
from fastapi             import Depends, HTTPException, Security
from fastapi.security    import HTTPAuthorizationCredentials, HTTPBearer
from jose                import JWTError, jwt
from app.core.config     import settings
from app.core.exceptions import AuthenticationError

security_scheme = HTTPBearer(auto_error=True)

_JWKS_CACHE       : dict[str, Any] | None = None
_JWKS_CACHE_EXPIRY: datetime | None       = None
_JWKS_CACHE_TTL                           = timedelta(minutes=10)

class AuthenticatedUser:
    """
    Authenticated user context extracted from a validated JWT.

    Attributes:
        user_id:
            Supabase-authenticated user UUID.

        claims:
            Full validated JWT claims payload.
    """

    def __init__(self, user_id: str, claims: dict[str, Any]) -> None:
        self.user_id = user_id
        self.claims  = claims

def _jwks_cache_valid() -> bool:
    if _JWKS_CACHE is None or _JWKS_CACHE_EXPIRY is None:
        return False
    return datetime.now(timezone.utc) < _JWKS_CACHE_EXPIRY

async def fetch_jwks() -> dict[str, Any]:
    """
    Retrieve the Supabase JWKS document with TTL-based caching.

    Returns:
        dict[str, Any]:
            JWKS payload containing public signing keys.

    Raises:
        AuthenticationError:
            If the JWKS document cannot be retrieved.
    """

    global _JWKS_CACHE
    global _JWKS_CACHE_EXPIRY

    if _jwks_cache_valid():
        return _JWKS_CACHE

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.supabase_jwks_url)
            response.raise_for_status()

        _JWKS_CACHE        = response.json()
        _JWKS_CACHE_EXPIRY = datetime.now(timezone.utc) + _JWKS_CACHE_TTL

        return _JWKS_CACHE

    except Exception as exc:
        raise AuthenticationError("Unable to fetch JWKS") from exc

async def get_current_user( credentials: HTTPAuthorizationCredentials = Security(security_scheme) ) -> AuthenticatedUser:
    """
    Validate the incoming bearer token and return authenticated user contenxt.

    Args:
        credentials:
            HTTP bearer authorization credentials.

    Returns:
        AuthenticatedUser:
            Validated authenticated user context.

    Raises:
        HTTPException:
            If token validation fails.
    """
    token = credentials.credentials

    try:
        jwks = await fetch_jwks()

        claims = jwt.decode(
            token=token,
            key=jwks,
            algorithms=["RS256"],
            audience=settings.supabase_audience,
            issuer=settings.supabase_issuer
        )

        user_id = claims.get("sub")

        if not user_id:
            raise AuthenticationError("JWT subject claim is missing")

        return AuthenticatedUser(
            user_id=user_id,
            claims=claims
        )

    except (JWTError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
        ) from exc