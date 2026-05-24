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

import jwt
from typing              import Any
from uuid                import UUID
from fastapi             import HTTPException, Security
from fastapi.security    import HTTPAuthorizationCredentials, HTTPBearer
from jwt                 import PyJWTError, PyJWKClient
from app.core.config     import settings
from app.core.exceptions import AuthenticationError

security_scheme = HTTPBearer(auto_error=True)

class AuthenticatedUser:
    """
    Authenticated user context extracted from a validated JWT.

    Attributes:
        user_id:
            Supabase-authenticated user UUID.

        claims:
            Full validated JWT claims payload.
    """

    def __init__(self, user_id: UUID, claims: dict[str, Any]) -> None:
        self.user_id = user_id
        self.claims  = claims

async def get_current_user( credentials: HTTPAuthorizationCredentials = Security(security_scheme) ) -> AuthenticatedUser:
    """
    Validate the incoming bearer token and return authenticated user context.

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
        jwk_client = PyJWKClient(settings.supabase_jwks_url)

        signing_key = jwk_client.get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "HS256", "ES256"],
            audience=settings.supabase_audience,
            issuer=settings.supabase_issuer,
        )

        subject = claims.get("sub")

        if not subject:
            raise AuthenticationError(
                "JWT subject claim is missing"
            )

        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise AuthenticationError(
                "JWT subject claim is not a valid UUID"
            ) from exc

        return AuthenticatedUser(
            user_id=user_id,
            claims=claims,
        )

    except (PyJWTError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(exc)}",
        ) from exc