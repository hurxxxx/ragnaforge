"""Authentication utilities for API routes."""

from fastapi import HTTPException, status, Header
from typing import Optional
from config import settings
from utils.openai_errors import authentication_error


async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """Verify API key from Authorization header - OpenAI API compatible."""
    if not authorization:
        raise authentication_error("You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY)")

    if not authorization.startswith("Bearer "):
        raise authentication_error("Invalid authorization header format. Expected 'Bearer <api_key>'")

    token = authorization[7:]  # Remove "Bearer " prefix

    if not token:
        raise authentication_error("API key cannot be empty")

    if settings.api_key and token != settings.api_key:
        raise authentication_error("Incorrect API key provided")

    return token
